from __future__ import annotations

import os
import socket
import types
from collections.abc import Iterator, Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.exc import OperationalError

from swingtrade.contracts.monitoring import MonitoringConditionCode, NullMonitoringEmitter
from swingtrade.contracts.secret_refs import DeploymentEnvironment
from swingtrade.offline.database import bind_database_reference
from swingtrade.offline.token_store import (
    CasExpectation,
    CasMutation,
    InitialTokenRecord,
    PostgresTokenStore,
    StaleWriterRejected,
    SyntheticCiphertext,
    TokenState,
    TokenStoreError,
    create_fixture_schema,
    token_families,
)
from swingtrade.persistence import Base

POSTGRES_URL = os.getenv("SWINGTRADE_TEST_POSTGRES_URL")
NOW = datetime(2024, 1, 1, tzinfo=UTC)
DEV_REFS = {"SWINGTRADE_DEV_DATABASE_URL_REF": "dev-ref"}
SIM_REFS = {"SWINGTRADE_SIM_DATABASE_URL_REF": "sim-ref"}
ORIGINAL = b"fixture:alpha"
UPDATED = b"fixture:beta"
pytestmark_postgres = pytest.mark.skipif(
    not POSTGRES_URL, reason="SWINGTRADE_TEST_POSTGRES_URL is required"
)


def _record(
    material: bytes = ORIGINAL, state: TokenState = TokenState.ACTIVE
) -> InitialTokenRecord:
    return InitialTokenRecord(
        family_id="family_1",
        owner_id="owner_a",
        state=state,
        material=SyntheticCiphertext(material),
        scope_set=("READ",),
        revocation_reason_code="",
        lease_expires_at=NOW,
        updated_at=NOW,
    )


def _expectation(**overrides: object) -> CasExpectation:
    values: dict[str, object] = {
        "family_id": "family_1",
        "version": 1,
        "fence": 1,
        "state": TokenState.ACTIVE,
        "environment": DeploymentEnvironment.DEV,
        "owner_id": "owner_a",
    }
    values.update(overrides)
    return CasExpectation(
        family_id=str(values["family_id"]),
        version=values["version"],  # type: ignore[arg-type]
        fence=values["fence"],  # type: ignore[arg-type]
        state=values["state"],  # type: ignore[arg-type]
        environment=values["environment"],  # type: ignore[arg-type]
        owner_id=str(values["owner_id"]),
    )


def _mutation(material: bytes = UPDATED, **overrides: object) -> CasMutation:
    values: dict[str, object] = {
        "fence": 2,
        "owner_id": "owner_a",
        "state": TokenState.REFRESHING,
        "material": SyntheticCiphertext(material),
        "scope_set": ("READ",),
        "revocation_reason_code": "",
        "lease_expires_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return CasMutation(
        fence=values["fence"],  # type: ignore[arg-type]
        owner_id=str(values["owner_id"]),
        state=values["state"],  # type: ignore[arg-type]
        material=values["material"],  # type: ignore[arg-type]
        scope_set=values["scope_set"],  # type: ignore[arg-type]
        revocation_reason_code=str(values["revocation_reason_code"]),
        lease_expires_at=values["lease_expires_at"],  # type: ignore[arg-type]
        updated_at=values["updated_at"],  # type: ignore[arg-type]
    )


def test_phase1_metadata_does_not_include_the_token_table() -> None:
    assert "offline_token_families" not in Base.metadata.tables
    assert set(Base.metadata.tables) == {
        "domain_events",
        "idempotency_records",
        "order_intents",
        "outbox_items",
    }


def test_broker_material_and_live_expectation_are_rejected() -> None:
    with pytest.raises(TokenStoreError, match="SYNTHETIC_FIXTURE_REQUIRED"):
        SyntheticCiphertext(b"refresh-token")
    with pytest.raises(TokenStoreError, match="LIVE_INITIALIZATION_DENIED"):
        _expectation(environment=DeploymentEnvironment.LIVE)
    with pytest.raises(TokenStoreError, match="INVALID_VERSION"):
        _expectation(version=1.0)
    with pytest.raises(TokenStoreError, match="INVALID_VERSION"):
        _expectation(version=True)


@pytest.mark.parametrize(
    ("url", "connect_args"),
    [
        ("postgresql+psycopg://?host=example.invalid", {}),
        ("postgresql+psycopg://127.0.0.1/swingtrade_test?host=example.invalid", {}),
        ("postgresql+psycopg://localhost/swingtrade_test?host=db.example.supabase.co", {}),
        ("postgresql+psycopg://127.0.0.1/swingtrade_test?host=api.tradestation.com", {}),
        ("postgresql+psycopg://127.0.0.1/swingtrade_test?hostaddr=93.184.216.34", {}),
        ("postgresql+psycopg://swingtrade:swingtrade@127.0.0.1:5432/swingtrade_test?port=1", {}),
        ("postgresql+psycopg://127.0.0.1/swingtrade_test", {"host": "example.invalid"}),
        ("postgresql+psycopg://127.0.0.1:5432/swingtrade_test", {"port": 1}),
        ("postgresql+psycopg://127.0.0.1/swingtrade_test", {"hostaddr": "93.184.216.34"}),
    ],
)
def test_local_authority_rejects_dial_target_overrides(
    monkeypatch: pytest.MonkeyPatch, url: str, connect_args: dict[str, object]
) -> None:
    def denied(*args: object, **kwargs: object) -> object:
        raise AssertionError("socket opened")

    monkeypatch.setattr(socket, "socket", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    engine = create_engine(url, connect_args=connect_args)
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED") as captured:
        PostgresTokenStore(engine, binding)
    rendered = str(captured.value)
    assert "example.invalid" not in rendered
    assert "supabase" not in rendered
    assert "tradestation" not in rendered
    assert "93.184.216.34" not in rendered
    assert "swingtrade" not in rendered
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        create_fixture_schema(engine)


def _deny_sockets(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []

    def denied(*args: object, **kwargs: object) -> object:
        calls.append("socket")
        raise AssertionError("socket opened")

    monkeypatch.setattr(socket, "socket", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    return calls


@pytest.mark.parametrize(
    "conninfo",
    [
        "hostaddr=127.0.0.1 port=1",
        "hostaddr='127.0.0.1' port='1'",
        "hostaddr = 127.0.0.1 port = 1",
        "port=1",
        "hostaddr=127.0.0.1",
        "HostAddr=127.0.0.1",
    ],
)
def test_conninfo_hostaddr_or_port_is_rejected(
    monkeypatch: pytest.MonkeyPatch, conninfo: str
) -> None:
    calls = _deny_sockets(monkeypatch)
    engine = create_engine(
        "postgresql+psycopg://swingtrade:swingtrade@127.0.0.1:5432/swingtrade",
        connect_args={"conninfo": conninfo},
    )
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED") as captured:
        PostgresTokenStore(engine, binding)
    rendered = str(captured.value)
    assert "hostaddr" not in rendered
    assert "127.0.0.1" not in rendered
    assert "swingtrade" not in rendered
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        create_fixture_schema(engine)
    assert calls == []


def test_conninfo_without_dial_keys_keeps_the_url_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _deny_sockets(monkeypatch)
    engine = create_engine(
        "postgresql+psycopg://swingtrade:swingtrade@127.0.0.1:5432/swingtrade",
        connect_args={"conninfo": "dbname=swingtrade"},
    )
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    PostgresTokenStore(engine, binding)
    assert calls == []


class _DivergentPort(Mapping[str, object]):
    """``.get`` and ``in`` report port 5432. Item access reports port 1."""

    _visible = {"host": "127.0.0.1", "port": 5432, "dbname": "swingtrade"}
    _stored = {"host": "127.0.0.1", "port": 1, "dbname": "swingtrade"}

    def __getitem__(self, key: str) -> object:
        return self._stored[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._stored)

    def __len__(self) -> int:
        return len(self._stored)

    def get(self, key: str, default: object = None) -> object:
        if key in self._visible:
            return self._visible[key]
        return default

    def __contains__(self, key: object) -> bool:
        return key in self._visible


def _creator_with_cparams(engine: object, params: Mapping[str, object]) -> object:
    creator = engine.pool._creator  # type: ignore[attr-defined]
    cells: list[types.CellType] = []
    pairs = zip(creator.__code__.co_freevars, creator.__closure__, strict=True)
    for name, cell in pairs:
        if name == "cparams":
            cells.append(types.CellType(params))
        else:
            cells.append(cell)
    return types.FunctionType(
        creator.__code__,
        creator.__globals__,
        "connect",
        closure=tuple(cells),
    )


def test_getitem_port_is_not_hidden_by_mapping_get(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _deny_sockets(monkeypatch)
    url = "postgresql+psycopg://swingtrade:swingtrade@127.0.0.1:5432/swingtrade"
    forged = _creator_with_cparams(create_engine(url), _DivergentPort())
    engine = create_engine(url, creator=forged)
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED") as captured:
        PostgresTokenStore(engine, binding)
    rendered = str(captured.value)
    assert "127.0.0.1" not in rendered
    assert "5432" not in rendered
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        create_fixture_schema(engine)
    assert calls == []


def test_mutated_cparams_cell_does_not_dial(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _deny_sockets(monkeypatch)
    url = "postgresql+psycopg://swingtrade:swingtrade@127.0.0.1:5432/swingtrade"
    engine = create_engine(url)
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    store = PostgresTokenStore(engine, binding)
    creator = engine.pool._creator
    replaced = False
    pairs = zip(creator.__code__.co_freevars, creator.__closure__, strict=True)
    for name, cell in pairs:
        if name == "cparams":
            cell.cell_contents = _DivergentPort()
            replaced = True
    assert replaced
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED") as captured:
        store.read_redacted("family_1")
    rendered = str(captured.value)
    assert "127.0.0.1" not in rendered
    assert "5432" not in rendered
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None
    assert calls == []


def test_missing_url_host_does_not_follow_pghost(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _deny_sockets(monkeypatch)
    monkeypatch.setenv("PGHOST", "127.0.0.1")
    monkeypatch.setenv("PGPORT", "1")
    engine = create_engine("postgresql+psycopg:///swingtrade")
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED") as captured:
        PostgresTokenStore(engine, binding)
    rendered = str(captured.value)
    assert "127.0.0.1" not in rendered
    assert "PGHOST" not in rendered
    assert "PGPORT" not in rendered
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        create_fixture_schema(engine)
    assert calls == []


def test_omitted_port_cannot_be_replaced_by_pgport(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _deny_sockets(monkeypatch)
    monkeypatch.setenv("PGPORT", "1")
    engine = create_engine("postgresql+psycopg://127.0.0.1/swingtrade")
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED") as captured:
        PostgresTokenStore(engine, binding)
    rendered = str(captured.value)
    assert "PGPORT" not in rendered
    assert "1" not in rendered
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        create_fixture_schema(engine)
    assert calls == []


def test_omitted_port_is_rejected_without_pgport(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _deny_sockets(monkeypatch)
    monkeypatch.delenv("PGPORT", raising=False)
    engine = create_engine("postgresql+psycopg://localhost/swingtrade")
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        PostgresTokenStore(engine, binding)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        create_fixture_schema(engine)
    assert calls == []


@pytest.mark.parametrize(
    ("env_name", "env_value", "allowed"),
    [
        ("PGHOST", "example.invalid", True),
        ("PGPORT", "1", True),
        ("PGHOSTADDR", "93.184.216.34", False),
    ],
)
def test_libpq_env_cannot_replace_an_explicit_dial_target(
    monkeypatch: pytest.MonkeyPatch, env_name: str, env_value: str, allowed: bool
) -> None:
    calls = _deny_sockets(monkeypatch)
    for name in ("PGHOST", "PGHOSTADDR", "PGPORT", "PGSERVICE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(env_name, env_value)
    engine = create_engine("postgresql+psycopg://127.0.0.1:5432/swingtrade")
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    if allowed:
        PostgresTokenStore(engine, binding)
    else:
        with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED") as captured:
            PostgresTokenStore(engine, binding)
        rendered = str(captured.value)
        assert env_value not in rendered
        assert env_name not in rendered
        with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
            create_fixture_schema(engine)
    assert calls == []


def test_pghostaddr_set_after_approval_does_not_connect(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _deny_sockets(monkeypatch)
    monkeypatch.delenv("PGHOSTADDR", raising=False)
    monkeypatch.delenv("PGSERVICE", raising=False)
    engine = create_engine("postgresql+psycopg://127.0.0.1:5432/swingtrade")
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    store = PostgresTokenStore(engine, binding)
    monkeypatch.setenv("PGHOSTADDR", "93.184.216.34")
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED") as captured:
        store.read_redacted("family_1")
    assert "93.184.216.34" not in str(captured.value)
    assert "PGHOSTADDR" not in str(captured.value)
    assert calls == []


def test_pgservice_cannot_supply_hostaddr(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _deny_sockets(monkeypatch)
    monkeypatch.setenv("PGSERVICE", "remote")
    engine = create_engine("postgresql+psycopg://127.0.0.1:5432/swingtrade")
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED") as captured:
        PostgresTokenStore(engine, binding)
    assert "PGSERVICE" not in str(captured.value)
    assert "remote" not in str(captured.value)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        create_fixture_schema(engine)
    assert calls == []


def test_custom_creator_is_rejected_before_it_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _deny_sockets(monkeypatch)
    ran: list[str] = []

    def exploding_creator() -> object:
        ran.append("creator")
        raise AssertionError("creator ran")

    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    url = "postgresql+psycopg://swingtrade:swingtrade@127.0.0.1:5432/swingtrade"
    engine = create_engine(url, creator=exploding_creator)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        PostgresTokenStore(engine, binding)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        create_fixture_schema(engine)

    def connect() -> None:
        ran.append("forged")
        raise RuntimeError("store path invoked spoof")

    connect.__code__ = connect.__code__.replace(co_filename="/opt/sqlalchemy/engine/create.py")
    connect.__module__ = "sqlalchemy.engine.create"
    connect.__qualname__ = "create_engine.<locals>.connect"
    forged_engine = create_engine(url, creator=connect)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        PostgresTokenStore(forged_engine, binding)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        create_fixture_schema(forged_engine)

    def _stolen() -> object:
        cargs_tup = cparams = dialect = None

        def stolen_connect() -> object:
            if False:
                return (cargs_tup, cparams, dialect)
            raise RuntimeError("stolen connector invoked")

        return stolen_connect

    stolen = _stolen()
    real_creator = create_engine(url).pool._creator
    stolen.__code__ = real_creator.__code__  # type: ignore[attr-defined]
    stolen_engine = create_engine(url, creator=stolen)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        PostgresTokenStore(stolen_engine, binding)
    assert ran == []
    assert calls == []


def test_mutated_connector_code_is_rejected_before_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _deny_sockets(monkeypatch)

    def _mutant() -> object:
        left = middle = right = None

        def connect() -> object:
            if False:
                return (left, middle, right)
            raise RuntimeError("mutated connector invoked")

        return connect

    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    url = "postgresql+psycopg://swingtrade:swingtrade@127.0.0.1:5432/swingtrade"
    engine = create_engine(url)
    store = PostgresTokenStore(engine, binding)
    engine.pool._creator.__code__ = _mutant().__code__  # type: ignore[attr-defined]  # noqa: SLF001
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        store.read_redacted("family_1")
    assert calls == []


def test_replacement_creator_and_do_connect_do_not_run(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _deny_sockets(monkeypatch)
    ran: list[str] = []
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    url = "postgresql+psycopg://swingtrade:swingtrade@127.0.0.1:5432/swingtrade"

    def replacement() -> object:
        ran.append("creator")
        raise AssertionError("creator ran")

    replacement.__module__ = "sqlalchemy.engine.create"
    replacement.__qualname__ = "create_engine.<locals>.connect"
    engine = create_engine(url)
    store = PostgresTokenStore(engine, binding)
    engine.pool._creator = replacement  # noqa: SLF001
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        store.read_redacted("family_1")
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        store.commit_initial(_record(), attempt_id="after-replace")

    def listener(
        dialect: object, conn_rec: object, cargs: object, cparams: dict[str, object]
    ) -> None:
        ran.append("listener")
        cparams["host"] = "example.invalid"
        raise AssertionError("listener ran")

    listened = create_engine(url)
    listened_store = PostgresTokenStore(listened, binding)
    event.listen(listened, "do_connect", listener)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED") as captured:
        listened_store.read_redacted("family_1")
    rendered = str(captured.value)
    assert "example.invalid" not in rendered
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        listened_store.commit_initial(_record(), attempt_id="after-listen")
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED"):
        create_fixture_schema(listened)
    assert ran == []
    assert calls == []


def test_remote_and_sim_stores_do_not_connect(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*args: object, **kwargs: object) -> object:
        raise AssertionError("socket opened")

    monkeypatch.setattr(socket, "socket", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    remote = create_engine("postgresql+psycopg://swingtrade:supersecret@example.invalid/db")
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    with pytest.raises(TokenStoreError, match="REMOTE_DATABASE_PROHIBITED") as captured:
        PostgresTokenStore(remote, binding)
    assert "supersecret" not in str(captured.value)
    assert "example.invalid" not in str(captured.value)
    local = create_engine("postgresql+psycopg://swingtrade:swingtrade@127.0.0.1/swingtrade_test")
    sim = bind_database_reference(DeploymentEnvironment.SIM, SIM_REFS)
    with pytest.raises(Exception, match="SIM_CONNECTION_PROHIBITED"):
        PostgresTokenStore(local, sim)


@pytest.fixture
def store():
    assert POSTGRES_URL is not None
    engine = create_engine(POSTGRES_URL)
    create_fixture_schema(engine)
    with engine.begin() as connection:
        version = connection.execute(text("SHOW server_version_num")).scalar_one()
        assert int(version) // 10000 == 16
        isolation = connection.execute(text("SHOW transaction_isolation")).scalar_one()
        assert isolation == "read committed"
        connection.execute(token_families.delete())
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    value = PostgresTokenStore(engine, binding)
    yield value
    engine.dispose()


def _ciphertext(engine_holder: PostgresTokenStore) -> bytes:
    with engine_holder._engine.connect() as connection:  # noqa: SLF001
        value = connection.execute(
            select(token_families.c.refresh_ciphertext).where(
                token_families.c.family_id == "family_1"
            )
        ).scalar_one()
    assert isinstance(value, bytes)
    return value


@pytestmark_postgres
def test_matching_cas_increments_version_once(store: PostgresTokenStore) -> None:
    seeded = store.commit_initial(_record(), attempt_id="seed")
    assert seeded.version == 1
    assert not hasattr(seeded, "refresh_ciphertext")
    updated = store.compare_and_swap(_expectation(), _mutation(), attempt_id="cas_ok")
    assert updated.version == 2
    assert updated.fence == 2
    assert updated.state == TokenState.REFRESHING.value
    assert updated.environment == "DEV"
    assert "owner_id" not in updated.__slots__
    assert _ciphertext(store) == UPDATED
    redacted = store.read_redacted("family_1")
    assert redacted is not None
    assert redacted.version == 2
    assert not hasattr(redacted, "refresh_ciphertext")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("version", 9),
        ("fence", 9),
        ("state", TokenState.REVOKED),
        ("environment", DeploymentEnvironment.TEST),
        ("owner_id", "owner_b"),
    ],
)
@pytestmark_postgres
def test_predicate_mismatch_updates_zero_rows(
    store: PostgresTokenStore, field: str, value: object
) -> None:
    store.commit_initial(_record(), attempt_id=f"seed_{field}")
    reason = "STALE_WRITER"
    if field == "state" and value in {
        TokenState.REVOKED,
        TokenState.REAUTH_REQUIRED,
        TokenState.AUTH_UNKNOWN,
    }:
        reason = "TERMINAL_STATE_REJECTED"
    with pytest.raises(StaleWriterRejected, match=reason) as captured:
        store.compare_and_swap(
            _expectation(**{field: value}),
            _mutation(b"fixture:gamma"),
            attempt_id=f"stale_{field}",
        )
    assert b"fixture:alpha" not in str(captured.value).encode()
    assert b"fixture:gamma" not in str(captured.value).encode()
    assert not hasattr(captured.value, "refresh_ciphertext")
    assert _ciphertext(store) == ORIGINAL
    redacted = store.read_redacted("family_1")
    assert redacted is not None
    assert redacted.version == 1


@pytestmark_postgres
def test_stale_writer_is_not_retried_in_the_same_attempt(store: PostgresTokenStore) -> None:
    store.commit_initial(_record(), attempt_id="seed")
    store.compare_and_swap(_expectation(), _mutation(), attempt_id="winner")
    updates: list[str] = []

    def collect(
        connection: object,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        if statement.lstrip().lower().startswith("update"):
            updates.append(statement)

    event.listen(store._engine, "before_cursor_execute", collect)  # noqa: SLF001
    with pytest.raises(StaleWriterRejected, match="STALE_WRITER") as captured:
        store.compare_and_swap(_expectation(), _mutation(b"fixture:gamma"), attempt_id="stale")
    assert "fixture" not in str(captured.value)
    with pytest.raises(StaleWriterRejected, match="SAME_ATTEMPT_RETRY_DENIED"):
        store.compare_and_swap(
            _expectation(version=2),
            _mutation(b"fixture:gamma"),
            attempt_id="stale",
        )
    assert len(updates) == 1
    assert _ciphertext(store) == UPDATED
    reread = store.read_redacted("family_1")
    assert reread is not None
    assert reread.version == 2


@pytestmark_postgres
def test_ambiguous_database_error_does_not_replay_or_chain_material(
    store: PostgresTokenStore,
) -> None:
    store.commit_initial(_record(), attempt_id="seed")
    emitter = NullMonitoringEmitter()
    store._emitter = emitter  # noqa: SLF001

    def fail(
        connection: object,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        if statement.lstrip().lower().startswith("update"):
            raise OperationalError(
                "update",
                {"body": ORIGINAL},
                Exception("fixture:should-not-leak"),
            )

    event.listen(store._engine, "before_cursor_execute", fail)  # noqa: SLF001
    with pytest.raises(TokenStoreError, match="AUTH_UNKNOWN") as captured:
        store.compare_and_swap(_expectation(), _mutation(), attempt_id="ambiguous")
    assert captured.value.__cause__ is None
    assert "fixture" not in str(captured.value)
    assert emitter.conditions[-1].code is MonitoringConditionCode.DB_UNAVAILABLE
    with pytest.raises(StaleWriterRejected, match="SAME_ATTEMPT_RETRY_DENIED"):
        store.compare_and_swap(_expectation(), _mutation(), attempt_id="ambiguous")
    assert _ciphertext(store) == ORIGINAL


@pytest.mark.parametrize(
    "state",
    [TokenState.REVOKED, TokenState.REAUTH_REQUIRED, TokenState.AUTH_UNKNOWN],
)
@pytestmark_postgres
def test_terminal_state_cas_does_not_replace_ciphertext(
    store: PostgresTokenStore, state: TokenState
) -> None:
    store.commit_initial(_record(state=state), attempt_id=f"seed_{state.value}")
    updates: list[str] = []

    def collect(
        connection: object,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        if statement.lstrip().lower().startswith("update"):
            updates.append(statement)

    event.listen(store._engine, "before_cursor_execute", collect)  # noqa: SLF001
    with pytest.raises(StaleWriterRejected, match="TERMINAL_STATE_REJECTED") as captured:
        store.compare_and_swap(
            _expectation(state=state),
            _mutation(b"fixture:revived", state=TokenState.ACTIVE),
            attempt_id=f"revive_{state.value}",
        )
    assert "fixture" not in str(captured.value)
    assert "revived" not in str(captured.value)
    with pytest.raises(StaleWriterRejected, match="SAME_ATTEMPT_RETRY_DENIED"):
        store.compare_and_swap(
            _expectation(state=state),
            _mutation(b"fixture:revived", state=TokenState.ACTIVE),
            attempt_id=f"revive_{state.value}",
        )
    assert updates == []
    assert _ciphertext(store) == ORIGINAL
    redacted = store.read_redacted("family_1")
    assert redacted is not None
    assert redacted.version == 1
    assert redacted.state == state.value


@pytestmark_postgres
def test_concurrent_cas_lets_exactly_one_writer_win(store: PostgresTokenStore) -> None:
    store.commit_initial(_record(), attempt_id="seed")

    def attempt(attempt_id: str) -> object:
        try:
            return store.compare_and_swap(_expectation(), _mutation(), attempt_id=attempt_id)
        except StaleWriterRejected as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, ("one", "two")))
    successes = [result for result in results if not isinstance(result, StaleWriterRejected)]
    failures = [result for result in results if isinstance(result, StaleWriterRejected)]
    assert len(successes) == 1
    assert len(failures) == 1
    assert failures[0].reason == "STALE_WRITER"
    redacted = store.read_redacted("family_1")
    assert redacted is not None
    assert redacted.version == 2
    assert _ciphertext(store) == UPDATED
