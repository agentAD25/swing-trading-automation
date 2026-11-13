"""Fail-closed Alembic entry point for the dedicated receipt-test cluster.

The target is read only from the process environment variable
``SWINGTRADE_TEST_POSTGRES_URL``. The committed ``sqlalchemy.url`` is not a
connection target and is not a fallback. Credentials stay in memory. Rejection
messages are stable codes and never include a URL or credential.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Sequence
from logging.config import fileConfig
from typing import Final

from alembic import context
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, pool, text
from sqlalchemy.engine import URL, make_url

from swingtrade.persistence import Base

target_metadata = Base.metadata

TARGET_ENV: Final = "SWINGTRADE_TEST_POSTGRES_URL"
REQUIRED_HOST: Final = "127.0.0.1"
REQUIRED_PORT: Final = 5433
REQUIRED_DATABASE: Final = "swingtrade_receipt_test"
REQUIRED_ROLE: Final = "swingtrade_migrator"
REQUIRED_SYSTEM_IDENTIFIER: Final = 7707684291752896980
ALLOWED_DRIVER: Final = "postgresql+psycopg"
LIBPQ_DEFAULT_PORT: Final = 5432
ALLOWED_REVISIONS: Final[tuple[str, str, str]] = (
    "0001_offline_foundation",
    "0002_canonical_order_intents",
    "0003_durable_dry_run_observation",
)
IDENTITY_SQL: Final = (
    "SELECT current_user, current_database(), inet_server_addr()::text, inet_server_port()"
)
SYSTEM_IDENTIFIER_SQL: Final = "SELECT system_identifier FROM pg_control_system()"
VERSION_TABLE_SQL: Final = "SELECT to_regclass('alembic_version')"
VERSION_SQL: Final = "SELECT version_num FROM alembic_version"
_LOGGER_NAME: Final = "swingtrade.alembic_target_guard"
_CODES: Final = frozenset(
    {
        "missing_target",
        "port_5432",
        "localhost_alias",
        "non_loopback_host",
        "development_database",
        "wrong_database",
        "wrong_port",
        "unexpected_role",
        "bootstrap_superuser",
        "malformed_url",
        "unexpected_url_attribute",
        "wrong_system_identifier",
        "unsupported_revision",
        "revision_0004",
        "identity_check_failed",
        "connection_replaced",
        "wrong_credential",
        "timeout",
        "unexpected_entry_point",
        "unsafe_retry",
        "connection_failed",
        "unexpected_environment",
    }
)
_BOOTSTRAP_ROLES: Final = frozenset(
    {
        "admin",
        "azure_pg_admin",
        "azure_superuser",
        "cloudsqlsuperuser",
        "enterprisedb",
        "pgadmin",
        "pgsql",
        "postgres",
        "rds_superuser",
        "rdsadmin",
        "root",
        "sa",
        "supabase_admin",
    }
)
_LIBPQ_OVERRIDE_NAMES: Final = (
    "PGDATABASE",
    "PGHOST",
    "PGHOSTADDR",
    "PGOPTIONS",
    "PGPASSFILE",
    "PGPASSWORD",
    "PGPORT",
    "PGSERVICE",
    "PGSERVICEFILE",
    "PGUSER",
)
_LOGGED_LOGGERS: Final = (
    "",
    "alembic",
    "alembic.runtime",
    "alembic.runtime.migration",
    "sqlalchemy",
    "sqlalchemy.engine",
    "sqlalchemy.pool",
    _LOGGER_NAME,
)

_ACTIVE_SECRET: str | None = None
_ORIGINAL_HANDLE = logging.Logger.handle


class AlembicTargetRejected(RuntimeError):
    """Fail-closed refusal. ``code`` is the only message text."""

    def __init__(self, code: str) -> None:
        if code not in _CODES:
            code = "connection_failed"
        self.code = code
        super().__init__(code)


class Target:
    """Validated migration target. The password is omitted from text forms."""

    __slots__ = ("database", "host", "password", "port", "role")

    def __init__(
        self,
        *,
        host: str,
        port: int,
        database: str,
        role: str,
        password: str | None,
    ) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.role = role
        self.password = password

    def __repr__(self) -> str:
        return (
            "Target(host='127.0.0.1', port=5433, database='swingtrade_receipt_test', "
            "role='swingtrade_migrator', password='***')"
        )

    __str__ = __repr__

    def offline_url(self) -> str:
        rendered = str(
            URL.create(
                drivername=ALLOWED_DRIVER,
                username=self.role,
                host=self.host,
                port=self.port,
                database=self.database,
            )
        )
        if self.password is not None and self.password in rendered:
            _reject("connection_failed")
        return rendered

    def engine_url(self) -> URL:
        url = URL.create(
            drivername=ALLOWED_DRIVER,
            username=self.role,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )
        if url.port == LIBPQ_DEFAULT_PORT:
            _reject("port_5432")
        if (
            url.host != REQUIRED_HOST
            or url.port != REQUIRED_PORT
            or url.database != REQUIRED_DATABASE
            or url.username != REQUIRED_ROLE
            or dict(url.query)
        ):
            _reject("connection_failed")
        return url


def _reject(code: str) -> None:
    if code not in _CODES:
        code = "connection_failed"
    logging.getLogger(_LOGGER_NAME).warning("alembic target rejected: %s", code)
    raise AlembicTargetRejected(code) from None


def _call[T](fn: Callable[[], T]) -> tuple[bool, T | BaseException]:
    try:
        return True, fn()
    except AlembicTargetRejected:
        raise
    except Exception as exc:
        return False, exc


def _proxy() -> object:
    proxy = getattr(context, "_proxy", None)
    if proxy is None:
        _reject("unexpected_entry_point")
    return proxy


def _command_name(proxy: object) -> str:
    config_obj = getattr(proxy, "config", None)
    cmd_opts = getattr(config_obj, "cmd_opts", None)
    cmd = getattr(cmd_opts, "cmd", None)
    if not isinstance(cmd, tuple) or not cmd:
        _reject("unexpected_entry_point")
    name = getattr(cmd[0], "__name__", None)
    if type(name) is not str:
        _reject("unexpected_entry_point")
    return name


def _migration_name(proxy: object) -> str:
    options = getattr(proxy, "context_opts", None)
    if not isinstance(options, dict):
        _reject("unexpected_entry_point")
    name = getattr(options.get("fn"), "__name__", None)
    if type(name) is not str:
        _reject("unexpected_entry_point")
    return name


def _require_upgrade_entry() -> object:
    proxy = _proxy()
    if _command_name(proxy) != "upgrade" or _migration_name(proxy) != "upgrade":
        _reject("unexpected_entry_point")
    return proxy


def _configure_logging(proxy: object) -> None:
    config_obj = getattr(proxy, "config", None)
    path = getattr(config_obj, "config_file_name", None)
    if isinstance(path, str) and path:
        fileConfig(path)


def _target_from_environment() -> Target:
    if TARGET_ENV not in os.environ:
        _reject("missing_target")
    raw = os.environ[TARGET_ENV]
    if type(raw) is not str or raw.strip() == "":
        _reject("missing_target")
    return parse_target(raw)


def _is_0004(revision: str) -> bool:
    return revision.startswith("0004")


def parse_target(raw: str) -> Target:
    """Accept only the dedicated loopback receipt-test target."""

    if type(raw) is not str or raw.strip() == "" or any(character.isspace() for character in raw):
        _reject("malformed_url")
    ok, parsed = _call(lambda: make_url(raw))
    if not ok:
        _reject("malformed_url")
    if parsed.drivername != ALLOWED_DRIVER:
        if not str(parsed.drivername).startswith("postgresql"):
            _reject("malformed_url")
        _reject("unexpected_url_attribute")
    if dict(parsed.query) or "?" in raw or "#" in raw:
        _reject("unexpected_url_attribute")
    host = parsed.host
    username = parsed.username
    database = parsed.database
    if type(host) is not str or host == "" or type(username) is not str or username == "":
        _reject("malformed_url")
    if type(database) is not str or database == "":
        _reject("malformed_url")
    if any(character in database for character in "/?#\\"):
        _reject("unexpected_url_attribute")
    if host.casefold() == "localhost":
        _reject("localhost_alias")
    if host != REQUIRED_HOST:
        _reject("non_loopback_host")
    port = parsed.port
    if port is None or port == LIBPQ_DEFAULT_PORT:
        _reject("port_5432")
    if type(port) is not int or port != REQUIRED_PORT:
        _reject("wrong_port")
    if database == "swingtrade":
        _reject("development_database")
    if database != REQUIRED_DATABASE:
        _reject("wrong_database")
    if username.casefold() in _BOOTSTRAP_ROLES:
        _reject("bootstrap_superuser")
    if username != REQUIRED_ROLE:
        _reject("unexpected_role")
    password = parsed.password
    if password is not None and type(password) is not str:
        _reject("unexpected_url_attribute")
    return Target(
        host=host,
        port=port,
        database=database,
        role=username,
        password=password,
    )


def _refuse_libpq_overrides() -> None:
    for name in _LIBPQ_OVERRIDE_NAMES:
        if name in os.environ:
            _reject("unexpected_environment")


def _assert_revision_files(revisions: Sequence[tuple[str, str | None]]) -> None:
    if isinstance(revisions, (str, bytes)) or not isinstance(revisions, Sequence):
        _reject("unsupported_revision")
    seen: dict[str, str | None] = {}
    for item in revisions:
        if type(item) is not tuple or len(item) != 2:
            _reject("unsupported_revision")
        revision, down = item
        if type(revision) is not str or (down is not None and type(down) is not str):
            _reject("unsupported_revision")
        if _is_0004(revision) or (type(down) is str and _is_0004(down)):
            _reject("revision_0004")
        if revision in seen:
            _reject("unsupported_revision")
        seen[revision] = down
    expected = {
        ALLOWED_REVISIONS[0]: None,
        ALLOWED_REVISIONS[1]: ALLOWED_REVISIONS[0],
        ALLOWED_REVISIONS[2]: ALLOWED_REVISIONS[1],
    }
    if seen != expected:
        _reject("unsupported_revision")


def _unwrap_revision(value: object) -> object:
    if isinstance(value, tuple):
        if len(value) != 1:
            _reject("unsupported_revision")
        return value[0]
    return value


def _classify_known_revision(value: str) -> str:
    if _is_0004(value):
        _reject("revision_0004")
    if value not in ALLOWED_REVISIONS:
        _reject("unsupported_revision")
    return value


def _normalize_current(value: object) -> str | None:
    value = _unwrap_revision(value)
    if value is None:
        return None
    if type(value) is not str:
        _reject("unsupported_revision")
    if value == "":
        return None
    return _classify_known_revision(value)


def _normalize_destination(value: object) -> str:
    value = _unwrap_revision(value)
    if type(value) is not str or value == "":
        _reject("unsupported_revision")
    if _is_0004(value):
        _reject("revision_0004")
    if value in {"head", "heads"}:
        return ALLOWED_REVISIONS[-1]
    if value == "base":
        _reject("unsupported_revision")
    return _classify_known_revision(value)


def validate_revision_transition(
    current: object,
    destination: object,
    revisions: Sequence[tuple[str, str | None]],
) -> str:
    """Allow an absent revision or a prefix of the three committed revisions."""

    _assert_revision_files(revisions)
    normalized_current = _normalize_current(current)
    normalized_destination = _normalize_destination(destination)
    current_index = (
        -1 if normalized_current is None else ALLOWED_REVISIONS.index(normalized_current)
    )
    if ALLOWED_REVISIONS.index(normalized_destination) < current_index:
        _reject("unsupported_revision")
    return normalized_destination


def _revision_pairs(proxy: object) -> list[tuple[str, str | None]]:
    script = getattr(proxy, "script", None)
    if script is None or not callable(getattr(script, "walk_revisions", None)):
        config_obj = getattr(proxy, "config", None)
        ok, loaded = _call(lambda: ScriptDirectory.from_config(config_obj))
        if not ok:
            _reject("unsupported_revision")
        script = loaded
    ok, walked = _call(lambda: list(script.walk_revisions()))
    if not ok:
        text_value = _exception_text(walked)
        if "0004" in text_value:
            _reject("revision_0004")
        _reject("unsupported_revision")
    pairs: list[tuple[str, str | None]] = []
    for rev in walked:
        revision = getattr(rev, "revision", None)
        down = getattr(rev, "down_revision", None)
        if type(revision) is not str:
            _reject("unsupported_revision")
        if isinstance(down, tuple):
            if any(type(item) is str and _is_0004(item) for item in down):
                _reject("revision_0004")
            _reject("unsupported_revision")
        if down is not None and type(down) is not str:
            _reject("unsupported_revision")
        pairs.append((revision, down))
    return pairs


def _exception_text(exc: object) -> str:
    ok, text_value = _call(lambda: str(exc))
    if not ok or type(text_value) is not str:
        return ""
    return text_value


def _read_destination(proxy: object) -> object:
    ok, value = _call(lambda: proxy.get_revision_argument())
    if ok:
        return value
    if "0004" in _exception_text(value):
        _reject("revision_0004")
    _reject("unsupported_revision")
    return None


def _offline_current(proxy: object) -> object:
    getter = getattr(proxy, "get_starting_revision_argument", None)
    if not callable(getter):
        return None
    ok, value = _call(getter)
    if ok:
        return value
    text_value = _exception_text(value).lower()
    if "no starting revision" in text_value:
        return None
    if "0004" in text_value:
        _reject("revision_0004")
    _reject("unsupported_revision")
    return None


def _row(connection: object, sql: str) -> tuple[object, ...]:
    execute = getattr(connection, "execute", None)
    if not callable(execute):
        _reject("identity_check_failed")
    ok, result = _call(lambda: execute(text(sql)))
    if not ok:
        _reject("identity_check_failed")
    one = getattr(result, "one", None)
    if not callable(one):
        _reject("identity_check_failed")
    ok, row = _call(one)
    if not ok:
        _reject("identity_check_failed")
    if isinstance(row, tuple):
        return row
    ok, values = _call(lambda: tuple(row))
    if not ok:
        _reject("identity_check_failed")
    if type(values) is not tuple:
        _reject("identity_check_failed")
    return values


def _rows(connection: object, sql: str) -> list[object]:
    execute = getattr(connection, "execute", None)
    if not callable(execute):
        _reject("identity_check_failed")
    ok, result = _call(lambda: execute(text(sql)))
    if not ok:
        _reject("identity_check_failed")
    fetchall = getattr(result, "fetchall", None)
    if not callable(fetchall):
        _reject("identity_check_failed")
    ok, fetched = _call(fetchall)
    if not ok:
        _reject("identity_check_failed")
    values: list[object] = []
    try:
        items = list(fetched)
    except TypeError:
        _reject("unsupported_revision")
    for item in items:
        if isinstance(item, tuple):
            if len(item) != 1:
                _reject("unsupported_revision")
            values.append(item[0])
            continue
        ok, converted = _call(lambda item=item: tuple(item))
        if not ok or type(converted) is not tuple or len(converted) != 1:
            _reject("unsupported_revision")
        values.append(converted[0])
    return values


def _address_ok(value: object) -> bool:
    if type(value) is str:
        return value == REQUIRED_HOST or value == f"{REQUIRED_HOST}/32"
    if type(value).__name__ == "IPv4Address" and str(value) == REQUIRED_HOST:
        return True
    return False


def _verify_identity(connection: object) -> None:
    row = _row(connection, IDENTITY_SQL)
    if len(row) != 4:
        _reject("identity_check_failed")
    user, database, address, server_port = row
    if (
        user != REQUIRED_ROLE
        or database != REQUIRED_DATABASE
        or not _address_ok(address)
        or type(server_port) is not int
        or server_port != REQUIRED_PORT
    ):
        _reject("identity_check_failed")
    identifier = _row(connection, SYSTEM_IDENTIFIER_SQL)
    if len(identifier) != 1 or type(identifier[0]) is not int:
        _reject("identity_check_failed")
    if identifier[0] != REQUIRED_SYSTEM_IDENTIFIER:
        _reject("wrong_system_identifier")


def _database_revision(connection: object) -> object:
    regclass = _row(connection, VERSION_TABLE_SQL)
    if len(regclass) != 1:
        _reject("identity_check_failed")
    if regclass[0] is None:
        return None
    versions = _rows(connection, VERSION_SQL)
    if len(versions) == 0:
        return None
    if len(versions) != 1:
        _reject("unsupported_revision")
    return versions[0]


def _require_same_connection(proxy: object, connection: object) -> None:
    ok, bound = _call(lambda: proxy.get_bind())
    if not ok or bound is not connection:
        _reject("connection_replaced")


def _classify_connect_error(exc: BaseException) -> str:
    if type(exc) is TimeoutError or "timeout" in type(exc).__name__.lower():
        return "timeout"
    message = _exception_text(exc).lower()
    if "timeout" in message or "timed out" in message:
        return "timeout"
    if "authentication" in message or "password" in message or "credential" in message:
        return "wrong_credential"
    return "connection_failed"


def _connect_once(engine: object, attempts: list[int]) -> object:
    if attempts:
        _reject("unsafe_retry")
    attempts.append(1)
    connect = getattr(engine, "connect", None)
    if not callable(connect):
        _reject("connection_failed")
    ok, connection = _call(connect)
    if not ok:
        if isinstance(connection, AlembicTargetRejected):
            raise connection
        _reject(_classify_connect_error(connection))
    return connection


def _close_quietly(connection: object) -> None:
    close = getattr(connection, "close", None)
    if not callable(close):
        return
    _call(close)


class _SecretFilter(logging.Filter):
    def __init__(self, secret: str) -> None:
        super().__init__()
        self._secret = secret

    def filter(self, record: logging.LogRecord) -> bool:
        return not _record_has_secret(record, self._secret)


def _record_has_secret(record: logging.LogRecord, secret: str) -> bool:
    ok, rendered = _call(record.getMessage)
    if ok and type(rendered) is str and secret in rendered:
        return True
    args = record.args
    if isinstance(args, tuple):
        return any(type(item) is str and secret in item for item in args)
    if isinstance(args, dict):
        return any(type(item) is str and secret in item for item in args.values())
    return False


def _install_secret_filter(secret: str | None) -> list[tuple[logging.Logger, logging.Filter]]:
    global _ACTIVE_SECRET
    if secret is None or secret == "":
        return []
    _ACTIVE_SECRET = secret
    filt = _SecretFilter(secret)
    attached: list[tuple[logging.Logger, logging.Filter]] = []
    for name in _LOGGED_LOGGERS:
        logger = logging.getLogger(name)
        logger.addFilter(filt)
        attached.append((logger, filt))

    def handle(self: logging.Logger, record: logging.LogRecord) -> None:
        active = _ACTIVE_SECRET
        if active is not None and _record_has_secret(record, active):
            return
        _ORIGINAL_HANDLE(self, record)

    logging.Logger.handle = handle  # type: ignore[method-assign]
    return attached


def _remove_secret_filters(attached: list[tuple[logging.Logger, logging.Filter]]) -> None:
    global _ACTIVE_SECRET
    logging.Logger.handle = _ORIGINAL_HANDLE  # type: ignore[method-assign]
    _ACTIVE_SECRET = None
    for logger, filt in attached:
        logger.removeFilter(filt)


def _configure_and_run(proxy: object, connection: object) -> None:
    proxy.configure(connection=connection, target_metadata=target_metadata)
    _require_same_connection(proxy, connection)
    with proxy.begin_transaction():
        _require_same_connection(proxy, connection)
        proxy.run_migrations()


def run_migrations_offline() -> None:
    proxy = _require_upgrade_entry()
    if not proxy.is_offline_mode():
        _reject("unexpected_entry_point")
    target = _target_from_environment()
    filters = _install_secret_filter(target.password)
    try:
        _refuse_libpq_overrides()
        destination = validate_revision_transition(
            _offline_current(proxy),
            _read_destination(proxy),
            _revision_pairs(proxy),
        )
        if destination not in ALLOWED_REVISIONS:
            _reject("unsupported_revision")
        proxy.configure(
            url=target.offline_url(),
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        with proxy.begin_transaction():
            proxy.run_migrations()
    finally:
        _remove_secret_filters(filters)


def run_migrations_online() -> None:
    proxy = _require_upgrade_entry()
    if proxy.is_offline_mode():
        _reject("unexpected_entry_point")
    target = _target_from_environment()
    filters = _install_secret_filter(target.password)
    connection: object | None = None
    try:
        _refuse_libpq_overrides()
        pairs = _revision_pairs(proxy)
        destination = _read_destination(proxy)
        validate_revision_transition(None, destination, pairs)
        engine = create_engine(
            target.engine_url(),
            poolclass=pool.NullPool,
            echo=False,
            hide_parameters=True,
            connect_args={"connect_timeout": 5},
        )
        connection = _connect_once(engine, [])
        _verify_identity(connection)
        current = _database_revision(connection)
        resolved = validate_revision_transition(current, destination, pairs)
        if resolved not in ALLOWED_REVISIONS:
            _reject("unsupported_revision")
        _configure_and_run(proxy, connection)
    finally:
        if connection is not None:
            _close_quietly(connection)
        _remove_secret_filters(filters)


def invoke_alembic_environment() -> None:
    proxy = _require_upgrade_entry()
    _configure_logging(proxy)
    if proxy.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


if getattr(context, "_proxy", None) is not None:
    invoke_alembic_environment()
