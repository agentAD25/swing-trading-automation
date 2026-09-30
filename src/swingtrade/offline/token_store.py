"""Local PostgreSQL TokenStore compare-and-swap. No broker token material and no replay."""

from __future__ import annotations

import os
import re
import threading
import types
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import cast

import psycopg
from psycopg.rows import dict_row
from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    Engine,
    Integer,
    LargeBinary,
    MetaData,
    String,
    Table,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql.psycopg import PGDialect_psycopg
from sqlalchemy.engine.create import create_engine as _sqlalchemy_create_engine
from sqlalchemy.engine.interfaces import DBAPIModule
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import CreateTable
from sqlalchemy.sql.elements import ClauseElement

from swingtrade.contracts.monitoring import MonitoringEmitter, db_unavailable
from swingtrade.contracts.secret_refs import DeploymentEnvironment
from swingtrade.domain import utc_instant
from swingtrade.offline.database import DatabaseBinding, require_local_database_connection

_FIXTURE_PREFIX = b"fixture:"
_OPAQUE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_LABEL = re.compile(r"^[A-Z0-9_]{1,32}$")
_REASON = re.compile(r"^[A-Z0-9_]{0,64}$")
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_BLOCKED_HOST_MARKERS = ("tradestation", "supabase", "amazonaws", "neon.tech")
_MATERIAL_CONSTRAINT = (
    "octet_length(refresh_ciphertext) = 0 OR "
    "substring(refresh_ciphertext from 1 for 8) = '\\x666978747572653a'::bytea"
)

metadata = MetaData()
token_families = Table(
    "offline_token_families",
    metadata,
    Column("family_id", String, primary_key=True),
    Column("environment", String, nullable=False),
    Column("version", Integer, nullable=False),
    Column("fence", Integer, nullable=False),
    Column("owner_id", String, nullable=False),
    Column("lease_expires_at", DateTime(timezone=True), nullable=True),
    Column("state", String, nullable=False),
    Column("scope_set", JSON, nullable=False),
    Column("refresh_ciphertext", LargeBinary, nullable=False),
    Column("revocation_reason_code", String, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    CheckConstraint("environment IN ('DEV', 'TEST')", name="ck_token_family_env"),
    CheckConstraint("version >= 1", name="ck_token_family_version"),
    CheckConstraint("fence >= 1", name="ck_token_family_fence"),
    CheckConstraint(
        "state IN ('ACTIVE', 'REFRESHING', 'REVOKED', 'REAUTH_REQUIRED', 'AUTH_UNKNOWN')",
        name="ck_token_family_state",
    ),
    CheckConstraint(_MATERIAL_CONSTRAINT, name="ck_token_family_material"),
)

_REDACTED_COLUMNS = (
    token_families.c.family_id,
    token_families.c.environment,
    token_families.c.version,
    token_families.c.fence,
    token_families.c.state,
    token_families.c.scope_set,
    token_families.c.revocation_reason_code,
    token_families.c.updated_at,
)


class TokenState(StrEnum):
    ACTIVE = "ACTIVE"
    REFRESHING = "REFRESHING"
    REVOKED = "REVOKED"
    REAUTH_REQUIRED = "REAUTH_REQUIRED"
    AUTH_UNKNOWN = "AUTH_UNKNOWN"


_MUTABLE_TOKEN_STATES = (TokenState.ACTIVE.value, TokenState.REFRESHING.value)
_TERMINAL_TOKEN_STATES = frozenset(
    {
        TokenState.REVOKED,
        TokenState.REAUTH_REQUIRED,
        TokenState.AUTH_UNKNOWN,
    }
)


class TokenStoreError(RuntimeError):
    """TokenStore refused a write without publishing token material."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class StaleWriterRejected(TokenStoreError):
    """The conditional update matched zero rows, or the attempt already failed."""


class SyntheticCiphertext:
    """Empty or ``fixture:`` bytes. Broker token material cannot be represented."""

    __slots__ = ("body",)

    def __init__(self, body: bytes) -> None:
        if type(body) is not bytes or len(body) > 128:
            raise TokenStoreError("SYNTHETIC_FIXTURE_REQUIRED")
        if body != b"" and not body.startswith(_FIXTURE_PREFIX):
            raise TokenStoreError("SYNTHETIC_FIXTURE_REQUIRED")
        self.body = body


class RedactedTokenRecord:
    """Non-secret metadata. Ciphertext and owner identity are not included."""

    __slots__ = (
        "environment",
        "family_id",
        "fence",
        "revocation_reason_code",
        "scope_set",
        "state",
        "updated_at",
        "version",
    )

    def __init__(
        self,
        *,
        family_id: str,
        environment: str,
        version: int,
        fence: int,
        state: str,
        scope_set: tuple[str, ...],
        revocation_reason_code: str,
        updated_at: datetime,
    ) -> None:
        self.family_id = family_id
        self.environment = environment
        self.version = version
        self.fence = fence
        self.state = state
        self.scope_set = scope_set
        self.revocation_reason_code = revocation_reason_code
        self.updated_at = updated_at


class InitialTokenRecord:
    __slots__ = (
        "family_id",
        "lease_expires_at",
        "material",
        "owner_id",
        "revocation_reason_code",
        "scope_set",
        "state",
        "updated_at",
    )

    def __init__(
        self,
        *,
        family_id: str,
        owner_id: str,
        state: TokenState,
        material: SyntheticCiphertext,
        scope_set: tuple[str, ...],
        revocation_reason_code: str,
        lease_expires_at: datetime | None,
        updated_at: datetime,
    ) -> None:
        self.family_id = _opaque_id(family_id)
        self.owner_id = _opaque_id(owner_id)
        if not isinstance(state, TokenState):
            raise TokenStoreError("INVALID_STATE")
        self.state = state
        if not isinstance(material, SyntheticCiphertext):
            raise TokenStoreError("SYNTHETIC_FIXTURE_REQUIRED")
        self.material = material
        self.scope_set = _scope_set(scope_set)
        self.revocation_reason_code = _reason(revocation_reason_code)
        self.lease_expires_at = None if lease_expires_at is None else utc_instant(lease_expires_at)
        self.updated_at = utc_instant(updated_at)


class CasExpectation:
    __slots__ = ("environment", "family_id", "fence", "owner_id", "state", "version")

    def __init__(
        self,
        *,
        family_id: str,
        version: int,
        fence: int,
        state: TokenState,
        environment: DeploymentEnvironment,
        owner_id: str,
    ) -> None:
        if environment is DeploymentEnvironment.LIVE:
            raise TokenStoreError("LIVE_INITIALIZATION_DENIED")
        self.family_id = _opaque_id(family_id)
        self.version = _positive_int(version, "INVALID_VERSION")
        self.fence = _positive_int(fence, "INVALID_FENCE")
        if not isinstance(state, TokenState):
            raise TokenStoreError("INVALID_STATE")
        self.state = state
        if not isinstance(environment, DeploymentEnvironment):
            raise TokenStoreError("UNKNOWN_ENVIRONMENT")
        self.environment = environment
        self.owner_id = _opaque_id(owner_id)


class CasMutation:
    __slots__ = (
        "fence",
        "lease_expires_at",
        "material",
        "owner_id",
        "revocation_reason_code",
        "scope_set",
        "state",
        "updated_at",
    )

    def __init__(
        self,
        *,
        fence: int,
        owner_id: str,
        state: TokenState,
        material: SyntheticCiphertext,
        scope_set: tuple[str, ...],
        revocation_reason_code: str,
        lease_expires_at: datetime | None,
        updated_at: datetime,
    ) -> None:
        self.fence = _positive_int(fence, "INVALID_FENCE")
        self.owner_id = _opaque_id(owner_id)
        if not isinstance(state, TokenState):
            raise TokenStoreError("INVALID_STATE")
        self.state = state
        if not isinstance(material, SyntheticCiphertext):
            raise TokenStoreError("SYNTHETIC_FIXTURE_REQUIRED")
        self.material = material
        self.scope_set = _scope_set(scope_set)
        self.revocation_reason_code = _reason(revocation_reason_code)
        self.lease_expires_at = None if lease_expires_at is None else utc_instant(lease_expires_at)
        self.updated_at = utc_instant(updated_at)


def _opaque_id(value: object) -> str:
    if type(value) is not str or _OPAQUE_ID.fullmatch(value) is None:
        raise TokenStoreError("INVALID_IDENTITY")
    return value


def _positive_int(value: object, reason: str) -> int:
    if type(value) is not int or value < 1:
        raise TokenStoreError(reason)
    return value


def _scope_set(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or len(value) > 16:
        raise TokenStoreError("INVALID_SCOPE")
    labels: list[str] = []
    for item in value:
        if type(item) is not str or _LABEL.fullmatch(item) is None:
            raise TokenStoreError("INVALID_SCOPE")
        labels.append(item)
    return tuple(labels)


def _reason(value: object) -> str:
    if type(value) is not str or _REASON.fullmatch(value) is None:
        raise TokenStoreError("INVALID_REASON")
    return value


def _normalize_host(host: object) -> str | None:
    if host is None or host == "":
        return None
    if type(host) is not str or "," in host:
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    return host.rstrip(".").lower()


def _normalize_port(port: object) -> int | None:
    if port is None or port == "":
        return None
    if type(port) is int:
        return port
    if type(port) is str and port.isdigit():
        return int(port)
    raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")


def _marked_remote(host: str | None) -> bool:
    return host is not None and any(marker in host for marker in _BLOCKED_HOST_MARKERS)


def _default_connector_identity() -> tuple[object, object]:
    """Identity of SQLAlchemy's compiled pool connector, not its name strings."""
    bare: object = _sqlalchemy_create_engine
    wrapped = getattr(bare, "__wrapped__", None)
    if wrapped is not None:
        bare = wrapped
    code_obj = getattr(bare, "__code__", None)
    consts = getattr(code_obj, "co_consts", ())
    matches = [
        item
        for item in consts
        if isinstance(item, types.CodeType) and item.co_name == "connect"
    ]
    globals_map = getattr(bare, "__globals__", None)
    if len(matches) != 1 or type(globals_map) is not dict:
        return None, None
    return matches[0], globals_map


_DEFAULT_CONNECT_CODE, _DEFAULT_CONNECT_GLOBALS = _default_connector_identity()


def _pool_creator(engine: Engine) -> object:
    return getattr(engine.pool, "_creator", None)


def _is_default_creator(creator: object) -> bool:
    if _DEFAULT_CONNECT_CODE is None or _DEFAULT_CONNECT_GLOBALS is None:
        return False
    return (
        getattr(creator, "__code__", None) is _DEFAULT_CONNECT_CODE
        and getattr(creator, "__globals__", None) is _DEFAULT_CONNECT_GLOBALS
    )


def _has_do_connect_listener(engine: Engine) -> bool:
    dialect = getattr(engine, "dialect", None)
    dispatch = getattr(dialect, "dispatch", None)
    hook = getattr(dispatch, "do_connect", None)
    if hook is None:
        return True
    listeners = getattr(hook, "listeners", None)
    parent = getattr(hook, "parent_listeners", None)
    if listeners is None or parent is None:
        return True
    return bool(listeners) or bool(parent)


def _refuse_connect_hooks(engine: Engine) -> None:
    if not _is_default_creator(_pool_creator(engine)) or _has_do_connect_listener(engine):
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")


_URL_DIAL_QUERY_KEYS = frozenset({"host", "hostaddr", "port", "conninfo", "service"})


def _postgresql_dialect() -> PGDialect_psycopg:
    dialect = PGDialect_psycopg(paramstyle="pyformat")  # type: ignore[no-untyped-call]
    dialect.dbapi = cast(DBAPIModule, psycopg)
    return dialect


_DIALECT = _postgresql_dialect()


class _FrozenDial:
    """Plain host and port copied from the SQLAlchemy URL. Not a connector cell."""

    __slots__ = ("database", "host", "password", "port", "username")

    def __init__(self, host: str, port: int, database: str, username: str, password: str) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password


def _refuse_libpq_environment() -> None:
    if "PGHOSTADDR" in os.environ or "PGSERVICE" in os.environ:
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")


def _freeze_dial(engine: Engine) -> _FrozenDial:
    """Copy the URL authority into str and int values. Ignore connector parameters."""
    if engine.dialect.name != "postgresql":
        raise TokenStoreError("POSTGRESQL_REQUIRED")
    _refuse_libpq_environment()
    if _URL_DIAL_QUERY_KEYS.intersection(str(key) for key in engine.url.query):
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    host = _normalize_host(engine.url.host)
    port = _normalize_port(engine.url.port)
    if host not in _LOCAL_HOSTS or port is None or _marked_remote(host):
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    database = engine.url.database
    username = engine.url.username
    password = engine.url.password
    if type(database) is not str or database == "":
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    if username is None:
        username = ""
    if type(username) is not str:
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    if password is None:
        password = ""
    if type(password) is not str:
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    return _FrozenDial(str(host), int(port), str(database), str(username), str(password))


def _dial(target: _FrozenDial) -> psycopg.Connection:
    """Open libpq with the frozen host and port. Do not use an engine creator."""
    host = target.host
    port = target.port
    database = target.database
    username = target.username
    password = target.password
    if (
        type(host) is not str
        or type(port) is not int
        or type(database) is not str
        or type(username) is not str
        or type(password) is not str
    ):
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    if host not in _LOCAL_HOSTS or _marked_remote(host):
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    _refuse_libpq_environment()
    if username == "":
        if host in {"127.0.0.1", "::1"}:
            return psycopg.connect(host=host, port=port, hostaddr=host, dbname=database)
        return psycopg.connect(host=host, port=port, dbname=database)
    if host in {"127.0.0.1", "::1"}:
        return psycopg.connect(
            host=host,
            port=port,
            hostaddr=host,
            dbname=database,
            user=username,
            password=password,
        )
    return psycopg.connect(
        host=host,
        port=port,
        dbname=database,
        user=username,
        password=password,
    )


def _bound_params(compiled: object) -> dict[str, object]:
    construct = getattr(compiled, "construct_params", None)
    processors = getattr(compiled, "_bind_processors", None)
    if not callable(construct) or not isinstance(processors, Mapping):
        raise TokenStoreError("AUTH_UNKNOWN")
    raw = construct()
    if not isinstance(raw, Mapping):
        raise TokenStoreError("AUTH_UNKNOWN")
    params = {str(key): value for key, value in raw.items()}
    for key, processor in processors.items():
        if not callable(processor) or key not in params or params[key] is None:
            continue
        params[str(key)] = processor(params[key])
    return params


def _run(connection: psycopg.Connection, statement: ClauseElement) -> list[dict[str, object]]:
    compiled = statement.compile(
        dialect=_DIALECT, compile_kwargs={"render_postcompile": True}
    )
    sql = getattr(compiled, "string", None)
    if type(sql) is not str:
        raise TokenStoreError("AUTH_UNKNOWN")
    params = _bound_params(compiled)
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(sql, params)
        if cursor.description is None:
            return []
        fetched = cursor.fetchall()
    rows: list[dict[str, object]] = []
    for row in fetched:
        items = getattr(row, "items", None)
        if not callable(items):
            raise TokenStoreError("AUTH_UNKNOWN")
        rows.append({str(key): value for key, value in items()})
    return rows


def _ensure_token_table(connection: psycopg.Connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('offline_token_families')")
        found = cursor.fetchone()
    if found is not None and found[0] is not None:
        return
    ddl = str(CreateTable(token_families).compile(dialect=_DIALECT))
    with connection.cursor() as cursor:
        cursor.execute(ddl)


def create_fixture_schema(engine: Engine) -> None:
    """Create the local fixture table. The dial uses the URL host and port only."""
    target = _freeze_dial(engine)
    _refuse_connect_hooks(engine)
    connection = _dial(target)
    try:
        _ensure_token_table(connection)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _require_str(value: object) -> str:
    if type(value) is not str:
        raise TokenStoreError("AUTH_UNKNOWN")
    return value


def _require_int(value: object) -> int:
    if type(value) is not int:
        raise TokenStoreError("AUTH_UNKNOWN")
    return value


def _require_scope(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise TokenStoreError("AUTH_UNKNOWN")
    labels: list[str] = []
    for item in value:
        if type(item) is not str:
            raise TokenStoreError("AUTH_UNKNOWN")
        labels.append(item)
    return tuple(labels)


def _require_instant(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TokenStoreError("AUTH_UNKNOWN")
    return utc_instant(value)


def _redacted(row: Mapping[str, object]) -> RedactedTokenRecord:
    return RedactedTokenRecord(
        family_id=_require_str(row["family_id"]),
        environment=_require_str(row["environment"]),
        version=_require_int(row["version"]),
        fence=_require_int(row["fence"]),
        state=_require_str(row["state"]),
        scope_set=_require_scope(row["scope_set"]),
        revocation_reason_code=_require_str(row["revocation_reason_code"]),
        updated_at=_require_instant(row["updated_at"]),
    )


class PostgresTokenStore:
    """One conditional update per attempt. Zero rows reject the stale writer."""

    def __init__(
        self,
        engine: Engine,
        binding: DatabaseBinding,
        *,
        emitter: MonitoringEmitter | None = None,
    ) -> None:
        require_local_database_connection(binding)
        approved_dial = _freeze_dial(engine)
        approved = _pool_creator(engine)
        _refuse_connect_hooks(engine)
        if approved is not _pool_creator(engine) or not _is_default_creator(approved):
            raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
        self._engine = engine
        self._approved_creator = approved
        self._host = approved_dial.host
        self._port = approved_dial.port
        self._database = approved_dial.database
        self._username = approved_dial.username
        self._password = approved_dial.password
        self._binding = binding
        self._emitter = emitter
        self._closed_attempts: set[tuple[str, str]] = set()
        self._lock = threading.Lock()

    def commit_initial(self, record: InitialTokenRecord, *, attempt_id: str) -> RedactedTokenRecord:
        if not isinstance(record, InitialTokenRecord):
            raise TokenStoreError("INVALID_RECORD")
        statement = (
            insert(token_families)
            .values(
                family_id=record.family_id,
                environment=self._binding.environment.value,
                version=1,
                fence=1,
                owner_id=record.owner_id,
                lease_expires_at=record.lease_expires_at,
                state=record.state.value,
                scope_set=list(record.scope_set),
                refresh_ciphertext=record.material.body,
                revocation_reason_code=record.revocation_reason_code,
                updated_at=record.updated_at,
            )
            .returning(*_REDACTED_COLUMNS)
        )
        return self._execute_once(record.family_id, attempt_id, statement)

    def compare_and_swap(
        self,
        expected: CasExpectation,
        mutation: CasMutation,
        *,
        attempt_id: str,
    ) -> RedactedTokenRecord:
        """Apply one predicate update. A zero-row result cannot be retried in-attempt."""
        if not isinstance(expected, CasExpectation) or not isinstance(mutation, CasMutation):
            raise TokenStoreError("INVALID_CAS")
        if expected.state in _TERMINAL_TOKEN_STATES:
            self._close_attempt(expected.family_id, attempt_id)
            raise StaleWriterRejected("TERMINAL_STATE_REJECTED")
        statement = (
            update(token_families)
            .where(
                token_families.c.family_id == expected.family_id,
                token_families.c.version == expected.version,
                token_families.c.fence == expected.fence,
                token_families.c.state == expected.state.value,
                token_families.c.state.in_(_MUTABLE_TOKEN_STATES),
                token_families.c.environment == expected.environment.value,
                token_families.c.environment == self._binding.environment.value,
                token_families.c.owner_id == expected.owner_id,
            )
            .values(
                version=expected.version + 1,
                fence=mutation.fence,
                owner_id=mutation.owner_id,
                state=mutation.state.value,
                scope_set=list(mutation.scope_set),
                refresh_ciphertext=mutation.material.body,
                revocation_reason_code=mutation.revocation_reason_code,
                lease_expires_at=mutation.lease_expires_at,
                updated_at=mutation.updated_at,
            )
            .returning(*_REDACTED_COLUMNS)
        )
        return self._execute_once(expected.family_id, attempt_id, statement)

    def read_redacted(self, family_id: str) -> RedactedTokenRecord | None:
        family = _opaque_id(family_id)
        statement = select(*_REDACTED_COLUMNS).where(token_families.c.family_id == family)
        failure: TokenStoreError | None = None
        rows: list[dict[str, object]] = []
        connection: psycopg.Connection | None = None
        try:
            connection = self._open()
            rows = _run(connection, statement)
            connection.rollback()
        except (psycopg.Error, SQLAlchemyError):
            failure = TokenStoreError("AUTH_UNKNOWN")
        finally:
            if connection is not None:
                try:
                    connection.rollback()
                except (psycopg.Error, SQLAlchemyError):
                    pass
                try:
                    connection.close()
                except (psycopg.Error, SQLAlchemyError):
                    pass
        if failure is not None:
            self._emit_unavailable()
            raise failure
        if len(rows) == 0:
            return None
        if len(rows) != 1:
            raise TokenStoreError("AUTH_UNKNOWN")
        return _redacted(rows[0])

    def _close_attempt(self, family_id: str, attempt_id: str) -> None:
        attempt = _opaque_id(attempt_id)
        key = (family_id, attempt)
        with self._lock:
            if key in self._closed_attempts:
                raise StaleWriterRejected("SAME_ATTEMPT_RETRY_DENIED")
            self._closed_attempts.add(key)

    def _before_connect(self) -> None:
        creator = _pool_creator(self._engine)
        if (
            creator is not self._approved_creator
            or not _is_default_creator(creator)
            or _has_do_connect_listener(self._engine)
        ):
            raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
        _refuse_libpq_environment()

    def _dial_approved(self) -> psycopg.Connection:
        """Dial the plain host and port copied at approval."""
        host = self._host
        port = self._port
        database = self._database
        username = self._username
        password = self._password
        if (
            type(host) is not str
            or type(port) is not int
            or type(database) is not str
            or type(username) is not str
            or type(password) is not str
        ):
            raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
        return _dial(_FrozenDial(host, port, database, username, password))

    def _open(self) -> psycopg.Connection:
        self._before_connect()
        return self._dial_approved()

    def _execute_once(
        self, family_id: str, attempt_id: str, statement: ClauseElement
    ) -> RedactedTokenRecord:
        self._before_connect()
        self._close_attempt(family_id, attempt_id)
        connection: psycopg.Connection | None = None
        committed = False
        failure: TokenStoreError | None = None
        try:
            connection = self._dial_approved()
            rows = _run(connection, statement)
            if len(rows) == 0:
                raise StaleWriterRejected("STALE_WRITER")
            if len(rows) != 1:
                raise TokenStoreError("AUTH_UNKNOWN")
            record = _redacted(rows[0])
            connection.commit()
            committed = True
            return record
        except (psycopg.Error, SQLAlchemyError):
            failure = TokenStoreError("AUTH_UNKNOWN")
        finally:
            if connection is not None and not committed:
                try:
                    connection.rollback()
                except (psycopg.Error, SQLAlchemyError):
                    pass
            if connection is not None:
                try:
                    connection.close()
                except (psycopg.Error, SQLAlchemyError):
                    pass
        if failure is not None:
            self._emit_unavailable()
            raise failure
        raise TokenStoreError("AUTH_UNKNOWN")

    def _emit_unavailable(self) -> None:
        if self._emitter is not None:
            self._emitter.emit(
                db_unavailable(
                    "token store outcome is unknown",
                    environment=self._binding.environment.value,
                )
            )
