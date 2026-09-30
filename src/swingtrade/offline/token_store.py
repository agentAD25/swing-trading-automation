"""Local PostgreSQL TokenStore compare-and-swap. No broker token material and no replay."""

from __future__ import annotations

import re
import threading
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum

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


def _effective_connect_params(engine: Engine) -> Mapping[str, object]:
    """Return the parameters the pool will pass to the driver, including overrides."""
    creator = getattr(engine.pool, "_creator", None)
    closure = getattr(creator, "__closure__", None)
    candidates: list[Mapping[str, object]] = []
    if closure is not None:
        for cell in closure:
            contents = cell.cell_contents
            if isinstance(contents, Mapping):
                candidates.append(contents)
    for contents in candidates:
        if any(key in contents for key in ("host", "hostaddr", "port", "dbname")):
            return contents
    if candidates:
        return candidates[0]
    _unused, cparams = engine.dialect.create_connect_args(engine.url)
    return cparams


def _assert_local_postgresql(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        raise TokenStoreError("POSTGRESQL_REQUIRED")
    authority_host = _normalize_host(engine.url.host)
    authority_port = _normalize_port(engine.url.port)
    if authority_host not in _LOCAL_HOSTS and authority_host is not None:
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    if _marked_remote(authority_host):
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    params = _effective_connect_params(engine)
    effective_host = _normalize_host(params.get("host")) if "host" in params else None
    effective_port = _normalize_port(params.get("port")) if "port" in params else None
    if effective_host != authority_host or effective_port != authority_port:
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    if effective_host not in _LOCAL_HOSTS and effective_host is not None:
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    if _marked_remote(effective_host):
        raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")
    if "hostaddr" in params and params.get("hostaddr") not in (None, ""):
        hostaddr = _normalize_host(params.get("hostaddr"))
        if hostaddr != authority_host or hostaddr not in {"127.0.0.1", "::1"}:
            raise TokenStoreError("REMOTE_DATABASE_PROHIBITED")


def create_fixture_schema(engine: Engine) -> None:
    """Create the local fixture table. Remote hosts are refused before connect."""
    _assert_local_postgresql(engine)
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
        self._engine = engine
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

    def _execute_once(
        self, family_id: str, attempt_id: str, statement: Executable
    ) -> RedactedTokenRecord:
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
