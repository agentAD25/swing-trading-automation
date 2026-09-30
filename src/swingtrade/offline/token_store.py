"""Local PostgreSQL TokenStore compare-and-swap. No broker token material and no replay."""

from __future__ import annotations

import os
import re
import threading
import types
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum

from psycopg.conninfo import conninfo_to_dict
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
from sqlalchemy.engine.create import create_engine as _sqlalchemy_create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import Executable

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


def _conninfo_supplies_dial_override(raw: str) -> bool:
    parsed: object
    try:
        parsed = conninfo_to_dict(raw)
    except Exception:
        return True
    if not isinstance(parsed, Mapping):
        return True
    return "hostaddr" in parsed or "port" in parsed or "service" in parsed


_MISSING = object()


def _keyword_present(params: Mapping[str, object], key: str) -> bool:
    if key not in params:
        return False
    value = params[key]
    return value is not None and value != ""


def _refuse_libpq_dial_environment(params: Mapping[str, object]) -> None:
    """Refuse fallbacks that can replace an unset host, hostaddr, or port.

    libpq applies a service file first, then PGHOST, PGHOSTADDR, and PGPORT,
    for any dial keyword the connection parameters left empty.
    """
    service_present = _keyword_present(params, "service") or "PGSERVICE" in os.environ
    for key, env_name in (("host", "PGHOST"), ("hostaddr", "PGHOSTADDR"), ("port", "PGPORT")):
        if _keyword_present(params, key):
            continue
        if service_present or env_name in os.environ:
            raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")


def _closure_value(creator: object, name: str) -> object:
    """Return one free variable the connector bytecode will actually read."""
    code = getattr(creator, "__code__", None)
    closure = getattr(creator, "__closure__", None)
    freevars = getattr(code, "co_freevars", None)
    if not isinstance(freevars, tuple) or closure is None or len(freevars) != len(closure):
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    found = False
    value: object = None
    for free_name, cell in zip(freevars, closure, strict=True):
        if free_name != name:
            continue
        if found:
            raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
        found = True
        value = cell.cell_contents
    if not found:
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    return value


def _passed_keywords(params: object) -> dict[str, object]:
    """Materialize ``**params`` the way the connector unpacks it.

    Keyword unpacking uses ``keys`` and item access. ``Mapping.get`` is not consulted.
    """
    if not isinstance(params, Mapping):
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    try:
        keys = list(params.keys())
    except Exception:
        keys = None
    if not isinstance(keys, list):
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    passed: dict[str, object] = {}
    for key in keys:
        if type(key) is not str:
            raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
        try:
            value = params[key]
        except Exception:
            value = _MISSING
        if value is _MISSING:
            raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
        passed[key] = value
    return passed


def _refuse_connector_dial_mismatch(engine: Engine) -> None:
    """Approve host and port from the URL, then compare the connector's real arguments."""
    authority_host = _normalize_host(engine.url.host)
    authority_port = _normalize_port(engine.url.port)
    if authority_host not in _LOCAL_HOSTS or authority_port is None:
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    if _marked_remote(authority_host):
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    creator = _pool_creator(engine)
    positional = _closure_value(creator, "cargs_tup")
    if not isinstance(positional, (list, tuple)) or len(positional) != 0:
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    passed = _passed_keywords(_closure_value(creator, "cparams"))
    if "host" not in passed or "port" not in passed:
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    effective_host = _normalize_host(passed["host"])
    effective_port = _normalize_port(passed["port"])
    if effective_host != authority_host or effective_port != authority_port:
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    if effective_host not in _LOCAL_HOSTS or _marked_remote(effective_host):
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    if "conninfo" in passed:
        conninfo = passed["conninfo"]
        if type(conninfo) is not str or _conninfo_supplies_dial_override(conninfo):
            raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    if "hostaddr" in passed and passed["hostaddr"] not in (None, ""):
        hostaddr = _normalize_host(passed["hostaddr"])
        if hostaddr != authority_host or hostaddr not in {"127.0.0.1", "::1"}:
            raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    _refuse_libpq_dial_environment(passed)


def _assert_local_postgresql(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        raise TokenStoreError("POSTGRESQL_REQUIRED")
    _refuse_connect_hooks(engine)
    _refuse_connector_dial_mismatch(engine)
    _refuse_connect_hooks(engine)


def create_fixture_schema(engine: Engine) -> None:
    """Create the local fixture table. Remote hosts are refused before connect."""
    _assert_local_postgresql(engine)
    _refuse_connector_dial_mismatch(engine)
    metadata.create_all(engine)


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
        _assert_local_postgresql(engine)
        approved = _pool_creator(engine)
        _refuse_connect_hooks(engine)
        if approved is not _pool_creator(engine) or not _is_default_creator(approved):
            raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
        self._engine = engine
        self._approved_creator = approved
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
        self._before_connect()
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        if len(rows) == 0:
            return None
        if len(rows) != 1:
            raise TokenStoreError("AUTH_UNKNOWN")
        return _redacted(_mapping(rows[0]))

    def _close_attempt(self, family_id: str, attempt_id: str) -> None:
        attempt = _opaque_id(attempt_id)
        key = (family_id, attempt)
        with self._lock:
            if key in self._closed_attempts:
                raise StaleWriterRejected("SAME_ATTEMPT_RETRY_DENIED")
            self._closed_attempts.add(key)

    def _before_connect(self) -> None:
        creator = _pool_creator(self._engine)
        if creator is not self._approved_creator or _has_do_connect_listener(self._engine):
            raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
        _assert_local_postgresql(self._engine)
        if _pool_creator(self._engine) is not self._approved_creator:
            raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
        _refuse_connector_dial_mismatch(self._engine)

    def _execute_once(
        self, family_id: str, attempt_id: str, statement: Executable
    ) -> RedactedTokenRecord:
        self._before_connect()
        self._close_attempt(family_id, attempt_id)
        failure: TokenStoreError | None = None
        try:
            with self._engine.begin() as connection:
                rows = connection.execute(statement).mappings().all()
                if len(rows) == 0:
                    raise StaleWriterRejected("STALE_WRITER")
                if len(rows) != 1:
                    raise TokenStoreError("AUTH_UNKNOWN")
                return _redacted(_mapping(rows[0]))
        except SQLAlchemyError:
            failure = TokenStoreError("AUTH_UNKNOWN")
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


def _mapping(row: object) -> Mapping[str, object]:
    items = getattr(row, "items", None)
    if not callable(items):
        raise TokenStoreError("AUTH_UNKNOWN")
    mapped: dict[str, object] = {}
    for key, value in items():
        if not isinstance(key, str):
            raise TokenStoreError("AUTH_UNKNOWN")
        mapped[str(key)] = value
    return mapped
