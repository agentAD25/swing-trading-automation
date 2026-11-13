"""Synthetic Alembic target-guard tests. They do not open a database socket.

A mocked pass is not a migration pass.
"""

from __future__ import annotations

import logging
import os
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace

import pytest

import migrations.env as env

ROOT = Path(__file__).resolve().parents[2]
SECRET = "unit-test-secret-value"
VALID_PAIRS = [
    ("0003_durable_dry_run_observation", "0002_canonical_order_intents"),
    ("0002_canonical_order_intents", "0001_offline_foundation"),
    ("0001_offline_foundation", None),
]
HEAD = env.ALLOWED_REVISIONS[-1]


class _Revision:
    def __init__(self, revision: str, down_revision: str | None) -> None:
        self.revision = revision
        self.down_revision = down_revision


class _Script:
    def __init__(self, pairs: list[tuple[str, str | None]]) -> None:
        self._pairs = pairs

    def walk_revisions(self) -> list[_Revision]:
        return [_Revision(revision, down) for revision, down in self._pairs]


class _Config:
    def __init__(self, command: str) -> None:
        self.cmd_opts = SimpleNamespace(cmd=(_named(command), [], {}))
        self.config_file_name = None
        self.fallback_calls = 0

    def get_main_option(self, name: str, default: str | None = None) -> str:
        self.fallback_calls += 1
        raise AssertionError("committed URL fallback")

    def get_section(self, name: str, default: object = None) -> dict[str, str]:
        self.fallback_calls += 1
        raise AssertionError("committed URL fallback")


class _Row:
    def __init__(
        self,
        row: tuple[object, ...] | None,
        rows: list[tuple[object, ...]] | None = None,
    ) -> None:
        self._row = row
        self._rows = rows if rows is not None else ([] if row is None else [row])

    def one(self) -> tuple[object, ...]:
        if self._row is None:
            raise AssertionError("no row")
        return self._row

    def fetchall(self) -> list[tuple[object, ...]]:
        return list(self._rows)


class _Connection:
    def __init__(
        self,
        *,
        identity: tuple[object, object, object, object],
        system_id: object,
        version_table: object,
        versions: list[object],
        fail_sql: str | None = None,
    ) -> None:
        self.identity = identity
        self.system_id = system_id
        self.version_table = version_table
        self.versions = versions
        self.fail_sql = fail_sql
        self.statements: list[str] = []
        self.closed = False

    def execute(self, statement: object, *args: object, **kwargs: object) -> _Row:
        sql = str(statement)
        self.statements.append(sql)
        if self.fail_sql is not None and self.fail_sql in sql:
            raise RuntimeError("identity proof unavailable")
        if "pg_control_system" in sql:
            return _Row((self.system_id,))
        if "to_regclass" in sql:
            return _Row((self.version_table,))
        if "version_num" in sql:
            return _Row(None, [(item,) for item in self.versions])
        if "current_user" in sql:
            return _Row(self.identity)
        raise AssertionError("unexpected SQL")

    def close(self) -> None:
        self.closed = True


class _Transaction:
    def __enter__(self) -> _Transaction:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        return False


class _Proxy:
    def __init__(
        self,
        *,
        command: str,
        migration: str,
        offline: bool,
        destination: object,
        starting: object,
        script: _Script,
        state: dict[str, object],
    ) -> None:
        self.config = _Config(command)
        self.context_opts = {
            "fn": _named(migration),
            "as_sql": offline,
            "starting_rev": starting,
            "destination_rev": destination,
        }
        self.script = script
        self._offline = offline
        self._destination = destination
        self._starting = starting
        self._state = state

    def is_offline_mode(self) -> bool:
        return self._offline

    def get_revision_argument(self) -> object:
        return self._destination

    def get_starting_revision_argument(self) -> object:
        return self._starting

    def configure(self, *args: object, **kwargs: object) -> None:
        configured = self._state["configured"]
        assert isinstance(configured, list)
        configured.append(kwargs)

    def begin_transaction(self) -> _Transaction:
        return _Transaction()

    def run_migrations(self, **kwargs: object) -> None:
        count = self._state["migrations"]
        assert isinstance(count, int)
        self._state["migrations"] = count + 1

    def get_bind(self) -> object:
        if self._state["bind"] is not None:
            return self._state["bind"]
        configured = self._state["configured"]
        assert isinstance(configured, list)
        if not configured:
            raise AssertionError("no bind")
        latest = configured[-1]
        assert isinstance(latest, dict)
        return latest.get("connection")


def _named(name: str):
    def command(_rev: object, _ctx: object) -> list[object]:
        return []

    command.__name__ = name
    return command


def _url(
    *,
    user: str = env.REQUIRED_ROLE,
    password: str = SECRET,
    host: str = env.REQUIRED_HOST,
    port: str = str(env.REQUIRED_PORT),
    database: str = env.REQUIRED_DATABASE,
    query: str = "",
    driver: str = env.ALLOWED_DRIVER,
) -> str:
    auth = user if password == "" else f"{user}:{password}"
    port_text = f":{port}" if port != "" else ""
    return f"{driver}://{auth}@{host}{port_text}/{database}{query}"


def _good_connection(**changes: object) -> _Connection:
    identity = changes.get(
        "identity",
        (env.REQUIRED_ROLE, env.REQUIRED_DATABASE, env.REQUIRED_HOST, env.REQUIRED_PORT),
    )
    assert isinstance(identity, tuple)
    versions = changes.get("versions", [])
    assert isinstance(versions, list)
    return _Connection(
        identity=identity,
        system_id=changes.get("system_id", env.REQUIRED_SYSTEM_IDENTIFIER),
        version_table=changes.get("version_table"),
        versions=versions,
        fail_sql=changes.get("fail_sql") if isinstance(changes.get("fail_sql"), str) else None,
    )


def _install(
    monkeypatch: pytest.MonkeyPatch,
    *,
    url: str | None,
    offline: bool = False,
    destination: object = HEAD,
    command: str = "upgrade",
    migration: str = "upgrade",
    pairs: list[tuple[str, str | None]] | None = None,
    starting: object = None,
    connection: _Connection | None = None,
    bind: object | None = None,
    connect_error: BaseException | None = None,
) -> dict[str, object]:
    state: dict[str, object] = {
        "urls": [],
        "kwargs": [],
        "connects": 0,
        "migrations": 0,
        "configured": [],
        "bind": bind,
        "connection": connection,
        "connect_error": connect_error,
    }
    proxy = _Proxy(
        command=command,
        migration=migration,
        offline=offline,
        destination=destination,
        starting=starting,
        script=_Script(list(VALID_PAIRS if pairs is None else pairs)),
        state=state,
    )
    monkeypatch.setattr(env.context, "_proxy", proxy, raising=False)
    if url is None:
        monkeypatch.delenv(env.TARGET_ENV, raising=False)
    else:
        monkeypatch.setenv(env.TARGET_ENV, url)

    def factory(engine_url: object, **kwargs: object) -> SimpleNamespace:
        urls = state["urls"]
        stored = state["kwargs"]
        assert isinstance(urls, list)
        assert isinstance(stored, list)
        urls.append(engine_url)
        stored.append(kwargs)

        def connect() -> object:
            state["connects"] = int(state["connects"]) + 1
            if int(state["connects"]) > 1:
                raise AssertionError("second connection")
            if state["connect_error"] is not None:
                raise state["connect_error"]
            return state["connection"]

        return SimpleNamespace(connect=connect)

    monkeypatch.setattr(env, "create_engine", factory)
    return state


def _assert_rejected(runner, code: str, state: dict[str, object]) -> env.AlembicTargetRejected:
    with pytest.raises(env.AlembicTargetRejected) as caught:
        runner()
    assert caught.value.code == code
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert SECRET not in str(caught.value)
    assert SECRET not in "".join(traceback.format_exception(caught.value))
    assert state["migrations"] == 0
    return caught.value


def _revision_bytes() -> dict[Path, bytes]:
    versions = ROOT / "migrations" / "versions"
    paths = [ROOT / "alembic.ini", ROOT / "migrations" / "env.py", *sorted(versions.glob("*.py"))]
    return {path: path.read_bytes() for path in paths}


@pytest.fixture(autouse=True)
def _no_database_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    import psycopg

    def blocked(*args: object, **kwargs: object) -> object:
        raise AssertionError("real database socket")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(psycopg, "connect", blocked)


def test_missing_target(monkeypatch: pytest.MonkeyPatch) -> None:
    for value in (None, "", "   "):
        state = _install(monkeypatch, url=None if value is None else value)
        _assert_rejected(env.run_migrations_online, "missing_target", state)
        assert state["urls"] == []


def test_port_5432(monkeypatch: pytest.MonkeyPatch) -> None:
    for sample in (_url(port="5432"), _url(port="")):
        for offline in (False, True):
            state = _install(monkeypatch, url=sample, offline=offline)
            runner = env.run_migrations_offline if offline else env.run_migrations_online
            _assert_rejected(runner, "port_5432", state)
            assert state["urls"] == []
            assert state["connects"] == 0


def test_localhost_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    for host in ("localhost", "LocalHost"):
        state = _install(monkeypatch, url=_url(host=host))
        _assert_rejected(env.run_migrations_online, "localhost_alias", state)
        assert state["connects"] == 0


def test_remote_host(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install(monkeypatch, url=_url(host="203.0.113.10"))
    _assert_rejected(env.run_migrations_online, "non_loopback_host", state)
    assert state["connects"] == 0


def test_wrong_database(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install(monkeypatch, url=_url(database="postgres"))
    _assert_rejected(env.run_migrations_online, "wrong_database", state)


def test_development_database(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install(monkeypatch, url=_url(database="swingtrade"))
    _assert_rejected(env.run_migrations_online, "development_database", state)


def test_wrong_port(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install(monkeypatch, url=_url(port="5434"))
    _assert_rejected(env.run_migrations_online, "wrong_port", state)
    assert state["connects"] == 0


def test_wrong_role(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install(monkeypatch, url=_url(user="swingtrade"))
    _assert_rejected(env.run_migrations_online, "unexpected_role", state)


def test_bootstrap_superuser_role(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install(monkeypatch, url=_url(user="postgres"))
    _assert_rejected(env.run_migrations_online, "bootstrap_superuser", state)


def test_malformed_url(monkeypatch: pytest.MonkeyPatch) -> None:
    samples = (
        "not-a-url",
        "postgresql+psycopg://",
        f"http://swingtrade_migrator:{SECRET}@127.0.0.1:5433/swingtrade_receipt_test",
        f"postgresql+psycopg://swingtrade_migrator:{SECRET}@:5433/swingtrade_receipt_test",
    )
    for sample in samples:
        state = _install(monkeypatch, url=sample)
        _assert_rejected(env.run_migrations_online, "malformed_url", state)
        assert state["urls"] == []


def test_unexpected_url_attributes(monkeypatch: pytest.MonkeyPatch) -> None:
    samples = (
        _url(query="?sslmode=disable"),
        _url(query="?host=203.0.113.10"),
        _url(query="?port=5432"),
        _url(driver="postgresql+psycopg2"),
    )
    for sample in samples:
        state = _install(monkeypatch, url=sample)
        _assert_rejected(env.run_migrations_online, "unexpected_url_attribute", state)
        assert state["connects"] == 0


def test_credential_redaction(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    target = env.parse_target(_url())
    assert target.password == SECRET
    assert SECRET not in repr(target)
    assert SECRET not in str(target)
    offline = target.offline_url()
    assert SECRET not in offline
    assert offline == (
        "postgresql+psycopg://swingtrade_migrator@127.0.0.1:5433/swingtrade_receipt_test"
    )
    caplog.set_level(logging.WARNING, logger="swingtrade.alembic_target_guard")
    state = _install(monkeypatch, url=_url(), destination="0004_blocked")
    _assert_rejected(env.run_migrations_online, "revision_0004", state)
    assert SECRET not in " ".join(caplog.messages)
    rendered = state["urls"]
    assert rendered == []


def test_default_url_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    ini = (ROOT / "alembic.ini").read_text(encoding="utf-8")
    assert "5432" not in ini
    assert "localhost" not in ini
    assert "127.0.0.1" not in ini
    assert "@" not in ini
    assert "swingtrade:" not in ini
    source = (ROOT / "migrations" / "env.py").read_text(encoding="utf-8")
    assert "engine_from_config" not in source
    assert "get_main_option" not in source
    assert "swingtrade:swingtrade" not in source
    state = _install(monkeypatch, url=None)
    proxy = env.context._proxy
    assert isinstance(proxy, _Proxy)
    with pytest.raises(env.AlembicTargetRejected) as caught:
        env.run_migrations_online()
    assert caught.value.code == "missing_target"
    assert proxy.config.fallback_calls == 0
    assert state["urls"] == []
    assert state["connects"] == 0


def test_wrong_system_identifier(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = _good_connection(system_id=1)
    state = _install(monkeypatch, url=_url(), connection=connection)
    _assert_rejected(env.run_migrations_online, "wrong_system_identifier", state)
    assert state["connects"] == 1
    assert connection.closed is True


def test_unsupported_revision(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install(monkeypatch, url=_url(), destination="9999_other")
    _assert_rejected(env.run_migrations_online, "unsupported_revision", state)
    assert state["urls"] == []
    extra = [*VALID_PAIRS, ("9999_other", HEAD)]
    state = _install(monkeypatch, url=_url(), pairs=extra)
    _assert_rejected(env.run_migrations_online, "unsupported_revision", state)
    assert state["connects"] == 0
    connection = _good_connection(version_table="alembic_version", versions=["abcd"])
    state = _install(monkeypatch, url=_url(), connection=connection)
    _assert_rejected(env.run_migrations_online, "unsupported_revision", state)
    assert state["migrations"] == 0
    assert state["connects"] == 1


def test_revision_0004(monkeypatch: pytest.MonkeyPatch) -> None:
    for destination in ("0004", "0004_not_authorized"):
        state = _install(monkeypatch, url=_url(), destination=destination)
        _assert_rejected(env.run_migrations_online, "revision_0004", state)
        assert state["urls"] == []
        assert state["connects"] == 0
    state = _install(
        monkeypatch,
        url=_url(),
        pairs=[*VALID_PAIRS, ("0004_extra", HEAD)],
    )
    _assert_rejected(env.run_migrations_online, "revision_0004", state)
    assert state["connects"] == 0
    connection = _good_connection(version_table="alembic_version", versions=["0004"])
    state = _install(monkeypatch, url=_url(), connection=connection)
    _assert_rejected(env.run_migrations_online, "revision_0004", state)
    assert state["migrations"] == 0
    assert state["connects"] == 1


def test_revision_prefix_rules() -> None:
    pairs = list(VALID_PAIRS)
    assert env.validate_revision_transition(None, "head", pairs) == HEAD
    assert env.validate_revision_transition(None, env.ALLOWED_REVISIONS[0], pairs) == (
        env.ALLOWED_REVISIONS[0]
    )
    assert env.validate_revision_transition(env.ALLOWED_REVISIONS[0], HEAD, pairs) == HEAD
    assert env.validate_revision_transition(HEAD, HEAD, pairs) == HEAD
    with pytest.raises(env.AlembicTargetRejected) as caught:
        env.validate_revision_transition(HEAD, env.ALLOWED_REVISIONS[0], pairs)
    assert caught.value.code == "unsupported_revision"


def test_repository_revision_chain() -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    pairs = [(rev.revision, rev.down_revision) for rev in script.walk_revisions()]
    assert env.validate_revision_transition(None, "head", pairs) == HEAD


def test_failed_identity_check(monkeypatch: pytest.MonkeyPatch) -> None:
    mismatch = _good_connection(
        identity=("postgres", env.REQUIRED_DATABASE, env.REQUIRED_HOST, env.REQUIRED_PORT)
    )
    state = _install(monkeypatch, url=_url(), connection=mismatch)
    _assert_rejected(env.run_migrations_online, "identity_check_failed", state)
    assert state["connects"] == 1
    assert state["migrations"] == 0
    assert mismatch.closed is True
    unavailable = _good_connection(fail_sql="pg_control_system")
    state = _install(monkeypatch, url=_url(), connection=unavailable)
    _assert_rejected(env.run_migrations_online, "identity_check_failed", state)
    assert state["connects"] == 1
    assert state["migrations"] == 0
    assert "GRANT" not in " ".join(unavailable.statements).upper()


def test_replacement_of_the_verified_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = _good_connection()
    state = _install(monkeypatch, url=_url(), connection=connection, bind=object())
    _assert_rejected(env.run_migrations_online, "connection_replaced", state)
    configured = state["configured"]
    assert isinstance(configured, list)
    assert configured[0]["connection"] is connection
    assert state["migrations"] == 0
    assert state["connects"] == 1


def test_mocked_valid_path_is_not_a_migration_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    """One mocked online pass. It does not apply a migration or run schema SQL."""

    connection = _good_connection()
    before = _revision_bytes()
    state = _install(monkeypatch, url=_url(), connection=connection)
    env.run_migrations_online()
    applied_to_database = False
    assert state["migrations"] == 1
    assert applied_to_database is False
    assert state["connects"] == 1
    assert connection.closed is True
    assert connection.statements == [
        env.IDENTITY_SQL,
        env.SYSTEM_IDENTIFIER_SQL,
        env.VERSION_TABLE_SQL,
    ]
    for sql in connection.statements:
        upper = sql.upper()
        assert "GRANT" not in upper
        assert "CREATE" not in upper
        assert "ALTER" not in upper
        assert "DROP" not in upper
        assert "INSERT" not in upper
        assert "PG_CONTROLDATA" not in upper
    urls = state["urls"]
    kwargs = state["kwargs"]
    configured = state["configured"]
    assert isinstance(urls, list)
    assert isinstance(kwargs, list)
    assert isinstance(configured, list)
    assert urls[0].port == env.REQUIRED_PORT
    assert urls[0].host == env.REQUIRED_HOST
    assert urls[0].password == SECRET
    assert SECRET not in str(urls[0])
    assert SECRET not in repr(urls[0])
    assert kwargs[0]["poolclass"].__name__ == "NullPool"
    assert kwargs[0]["echo"] is False
    assert kwargs[0]["connect_args"] == {"connect_timeout": 5}
    assert configured[0]["connection"] is connection
    proxy = env.context._proxy
    assert isinstance(proxy, _Proxy)
    assert proxy.config.fallback_calls == 0
    assert _revision_bytes() == before


def test_no_real_sql(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = _good_connection()
    state = _install(monkeypatch, url=_url(), connection=connection, offline=True)
    env.run_migrations_offline()
    assert state["migrations"] == 1
    assert state["connects"] == 0
    assert state["urls"] == []
    assert connection.statements == []
    probes = " ".join(
        (env.IDENTITY_SQL, env.SYSTEM_IDENTIFIER_SQL, env.VERSION_TABLE_SQL, env.VERSION_SQL)
    ).upper()
    assert "GRANT" not in probes
    assert "CREATE" not in probes
    assert "ALTER" not in probes
    assert "DROP" not in probes
    assert "INSERT" not in probes
    assert "PG_CONTROLDATA" not in probes


def test_no_secret_in_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    error = RuntimeError(f"password authentication failed: {SECRET}")
    state = _install(monkeypatch, url=_url(), connection=_good_connection(), connect_error=error)
    rejected = _assert_rejected(env.run_migrations_online, "wrong_credential", state)
    assert rejected.__context__ is None
    assert state["connects"] == 1
    assert len(state["urls"]) == 1
    assert SECRET not in str(state["urls"][0])


def test_no_protected_environment_modification(monkeypatch: pytest.MonkeyPatch) -> None:
    before_files = _revision_bytes()
    before_names = sorted(path.name for path in (ROOT / "migrations" / "versions").glob("*.py"))
    state = _install(monkeypatch, url=_url(), destination="0004")
    before_env = dict(os.environ)
    before_path = list(sys.path)
    before_handle = logging.Logger.handle
    before_filters = {
        name: list(logging.getLogger(name).filters)
        for name in ("", "sqlalchemy", "sqlalchemy.engine", "swingtrade.alembic_target_guard")
    }
    _assert_rejected(env.run_migrations_online, "revision_0004", state)
    assert dict(os.environ) == before_env
    assert list(sys.path) == before_path
    assert logging.Logger.handle is before_handle
    assert before_filters == {
        name: list(logging.getLogger(name).filters)
        for name in before_filters
    }
    assert _revision_bytes() == before_files
    assert sorted(path.name for path in (ROOT / "migrations" / "versions").glob("*.py")) == (
        before_names
    )
    assert state["connects"] == 0


def test_offline_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install(monkeypatch, url=_url(), offline=True, starting=None)
    env.run_migrations_offline()
    applied_to_database = False
    assert applied_to_database is False
    assert state["migrations"] == 1
    assert state["connects"] == 0
    assert state["urls"] == []
    configured = state["configured"]
    assert isinstance(configured, list)
    rendered = configured[0]["url"]
    assert isinstance(rendered, str)
    assert SECRET not in rendered
    assert rendered == (
        "postgresql+psycopg://swingtrade_migrator@127.0.0.1:5433/swingtrade_receipt_test"
    )
    proxy = env.context._proxy
    assert isinstance(proxy, _Proxy)
    assert proxy.config.fallback_calls == 0


def test_wrong_credential(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install(
        monkeypatch,
        url=_url(),
        connect_error=RuntimeError(f"authentication failed for credential {SECRET}"),
    )
    _assert_rejected(env.run_migrations_online, "wrong_credential", state)
    assert state["connects"] == 1
    assert SECRET not in str(state["urls"][0])


def test_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install(
        monkeypatch,
        url=_url(),
        connect_error=TimeoutError(f"timed out waiting for {SECRET}"),
    )
    _assert_rejected(env.run_migrations_online, "timeout", state)
    assert state["connects"] == 1
    assert state["urls"][0].port == env.REQUIRED_PORT
    assert "5432" not in str(state["urls"][0])


def test_unexpected_entry_point(monkeypatch: pytest.MonkeyPatch) -> None:
    cases = (
        ("revision", "revision"),
        ("stamp", "do_stamp"),
        ("downgrade", "downgrade"),
        ("current", "display_version"),
    )
    for command, migration in cases:
        state = _install(monkeypatch, url=_url(), command=command, migration=migration)
        _assert_rejected(env.run_migrations_online, "unexpected_entry_point", state)
        assert state["urls"] == []
        assert state["connects"] == 0
    monkeypatch.setattr(env.context, "_proxy", None, raising=False)
    monkeypatch.setenv(env.TARGET_ENV, _url())
    with pytest.raises(env.AlembicTargetRejected) as caught:
        env.invoke_alembic_environment()
    assert caught.value.code == "unexpected_entry_point"
    assert SECRET not in str(caught.value)
    assert caught.value.__context__ is None


def test_unsafe_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install(
        monkeypatch,
        url=_url(),
        connect_error=ConnectionError("connection refused"),
    )
    _assert_rejected(env.run_migrations_online, "connection_failed", state)
    assert state["connects"] == 1
    assert state["urls"][0].port == env.REQUIRED_PORT
    assert state["urls"][0].host == env.REQUIRED_HOST
    assert "5432" not in str(state["urls"][0])
    attempts: list[int] = []
    calls = {"n": 0}

    def connect() -> object:
        calls["n"] += 1
        return object()

    env._connect_once(SimpleNamespace(connect=connect), attempts)
    with pytest.raises(env.AlembicTargetRejected) as caught:
        env._connect_once(SimpleNamespace(connect=connect), attempts)
    assert caught.value.code == "unsafe_retry"
    assert calls["n"] == 1


def test_libpq_environment_cannot_retarget(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install(monkeypatch, url=_url())
    monkeypatch.setenv("PGPORT", "5432")
    monkeypatch.setenv("PGHOST", "localhost")
    _assert_rejected(env.run_migrations_online, "unexpected_environment", state)
    assert state["urls"] == []
    assert state["connects"] == 0
