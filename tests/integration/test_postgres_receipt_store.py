"""Mocked PostgreSQL receipt-store tests.

These tests do not open a database socket. Synthetic PASS is not a PostgreSQL
run. Real cluster execution stays NOT RUN until a separate operational grant.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import traceback
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError

import migrations.env as env
from swingtrade.group4_email.contract import (
    EMAIL_RETENTION_POLICY,
    PARSER_VERSION,
    SCHEMA_VERSION,
    CanonicalInstructionEnvelope,
    Disposition,
    FieldEvidence,
    MessageType,
    ParseOutcome,
    ParseProvenance,
    ProviderType,
    ReasonCode,
    TradeAmendmentInstruction,
)
from swingtrade.group4_email.normalize import content_digest
from swingtrade.instruction_receipt import (
    InstructionReceipt,
    ReceiptKind,
    ReceiptStoreUnavailable,
    admit_instruction_receipt,
    project_receipt,
)
from swingtrade.postgres_receipt_store import (
    InstructionReceiptRow,
    PostgresReceiptStore,
)

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migrations" / "versions" / "0004_instruction_receipts.py"
MESSAGE_ID = "<tday@example.invalid>"
DIGEST_A = content_digest(b"synthetic-receipt-a")
DIGEST_B = content_digest(b"synthetic-receipt-b")
SECRET = "SYNTHETIC_SECRET_TOKEN_7f3a"
PROHIBITED = (
    "RAW_MIME_BODY_TOKEN",
    "EXAMPLE_QUANTITY_77",
    "PRICE_51.0000",
    "ACCT-9",
    "signals@example.invalid",
)
REAL_POSTGRESQL_EXECUTION = "NOT_RUN"
COLUMNS = (
    "receipt_key",
    "content_digest",
    "disposition",
    "message_type",
    "reasons",
    "instruction_ids",
    "message_id",
    "provider_type",
    "parser_version",
    "schema_version",
    "retention_policy",
    "provider_message_ref",
    "source_timestamp",
)


class _Result:
    def __init__(self, inserted_key: str | None, row: _StoredRow | None = None) -> None:
        self.inserted_key = inserted_key
        self._row = row

    def first(self) -> _StoredRow | None:
        if self.inserted_key is None:
            return None
        return _StoredRow({"receipt_key": self.inserted_key})

    def one(self) -> _StoredRow:
        if self._row is None:
            raise SQLAlchemyError("receipt row missing")
        return self._row


class _StoredRow:
    def __init__(self, values: dict[str, object]) -> None:
        self._mapping = values


class FakeConnection:
    """In-process stand-in for one caller-owned transaction."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[str, object]] = {}
        self.statements: list[str] = []
        self.inserts = 0
        self.selects = 0
        self.commits = 0
        self.rollbacks = 0
        self.closes = 0
        self._snapshot: dict[str, dict[str, object]] | None = None
        self._lock = threading.Lock()
        self.lose_next_insert = False
        self.fail_with: BaseException | None = None

    def begin(self) -> None:
        self._snapshot = json.loads(json.dumps(self.rows))

    def rollback(self) -> None:
        self.rollbacks += 1
        if self._snapshot is None:
            self.rows = {}
            return
        self.rows = json.loads(json.dumps(self._snapshot))

    def commit(self) -> None:
        self.commits += 1

    def close(self) -> None:
        self.closes += 1

    def reload_json(self) -> None:
        self.rows = json.loads(json.dumps(self.rows))

    def execute(self, statement: object) -> _Result:
        compiled = statement.compile(dialect=postgresql.dialect())  # type: ignore[attr-defined]
        sql = str(compiled)
        self.statements.append(sql)
        if statement.is_insert:  # type: ignore[attr-defined]
            return self._insert(sql, dict(compiled.params))
        if statement.is_select:  # type: ignore[attr-defined]
            self.selects += 1
            key = _bound_key(dict(compiled.params))
            with self._lock:
                values = self.rows.get(key)
            return _Result(None, None if values is None else _StoredRow(dict(values)))
        raise AssertionError("unexpected SQL")

    def _insert(self, sql: str, params: dict[str, object]) -> _Result:
        self.inserts += 1
        assert "ON CONFLICT" in sql.upper()
        assert "DO NOTHING" in sql.upper()
        values = {name: params[name] for name in COLUMNS}
        key = values["receipt_key"]
        assert type(key) is str
        error = self.fail_with
        self.fail_with = None
        with self._lock:
            if self.lose_next_insert:
                self.lose_next_insert = False
                self.rows[key] = values
                raise error if error is not None else psycopg.OperationalError(SECRET)
            if error is not None:
                raise error
            if key in self.rows:
                return _Result(None)
            self.rows[key] = values
            return _Result(key)


def _bound_key(params: dict[str, object]) -> str:
    for name, value in params.items():
        if name.startswith("receipt_key") and type(value) is str:
            return value
    raise AssertionError("receipt key was not bound")


def _instruction(digest: str) -> CanonicalInstructionEnvelope:
    return CanonicalInstructionEnvelope(
        instruction_id=f"v1:email_instruction:{digest}:0",
        message_type=MessageType.NEW_TRADE,
        payload=TradeAmendmentInstruction(
            evidence=(FieldEvidence("quantity", "EXAMPLE_QUANTITY_77"),)
        ),
        evidence=(FieldEvidence("body", "RAW_MIME_BODY_TOKEN"),),
    )


def _outcome(
    *,
    digest: str = DIGEST_A,
    message_id: str | None = MESSAGE_ID,
    disposition: Disposition = Disposition.QUARANTINE,
) -> ParseOutcome:
    instructions: tuple[CanonicalInstructionEnvelope, ...] = ()
    message_type = MessageType.UNKNOWN
    reasons: tuple[str, ...] = (ReasonCode.MISSING_SIZING.value,)
    if disposition is Disposition.ACCEPT:
        instructions = (_instruction(digest),)
        message_type = MessageType.NEW_TRADE
        reasons = ()
    return ParseOutcome(
        disposition=disposition,
        message_type=message_type,
        reasons=reasons,
        instructions=instructions,
        evidence=(
            FieldEvidence("price", "PRICE_51.0000"),
            FieldEvidence("account", "ACCT-9"),
        ),
        content_digest=digest,
        message_id=message_id,
        provenance=ParseProvenance(
            retention_policy=EMAIL_RETENTION_POLICY,
            provider_type=ProviderType.FIXTURE.value,
            provider_message_ref=message_id,
            raw_sha256=digest,
            parser_version=PARSER_VERSION,
            schema_version=SCHEMA_VERSION,
            source_timestamp="2024-01-01T00:00:00Z",
        ),
    )


def _receipt(**changes: object) -> InstructionReceipt:
    return project_receipt(_outcome(**changes))  # type: ignore[arg-type]


def _store() -> tuple[FakeConnection, PostgresReceiptStore, InstructionReceipt]:
    connection = FakeConnection()
    return connection, PostgresReceiptStore(connection), _receipt()


def _migration_module() -> object:
    spec = importlib.util.spec_from_file_location("receipt_migration_0004", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _named(name: str):
    def command(_revision: object, _context: object) -> list[object]:
        return []

    command.__name__ = name
    return command


@pytest.fixture(autouse=True)
def _no_database_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWINGTRADE_TEST_POSTGRES_URL", raising=False)

    def blocked(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("real database socket")

    monkeypatch.setattr(socket, "create_connection", blocked)


def test_initial_insertion_returns_none_and_keeps_the_callers_transaction() -> None:
    connection, store, receipt = _store()

    assert store.compare_and_insert(receipt.receipt_key, receipt) is None

    assert connection.inserts == 1
    assert connection.selects == 0
    assert connection.commits == 0
    assert connection.rollbacks == 0
    assert connection.closes == 0
    assert connection.rows[receipt.receipt_key]["content_digest"] == DIGEST_A


def test_same_digest_replay_returns_the_original_receipt() -> None:
    connection, store, receipt = _store()
    store.compare_and_insert(receipt.receipt_key, receipt)

    found = store.compare_and_insert(receipt.receipt_key, receipt)

    assert found == receipt
    assert connection.inserts == 2
    assert connection.selects == 1
    assert len(connection.rows) == 1
    decision = admit_instruction_receipt(_outcome(), store)
    assert decision.kind is ReceiptKind.REPLAY
    assert decision.receipt == receipt


def test_conflicting_digest_returns_the_original_without_replacement() -> None:
    connection, store, original = _store()
    store.compare_and_insert(original.receipt_key, original)
    conflict = _receipt(digest=DIGEST_B)

    found = store.compare_and_insert(conflict.receipt_key, conflict)

    assert found == original
    assert found != conflict
    assert connection.rows[original.receipt_key]["content_digest"] == DIGEST_A
    decision = admit_instruction_receipt(_outcome(digest=DIGEST_B), store)
    assert decision.kind is ReceiptKind.CONFLICT
    assert decision.receipt == original
    assert decision.receipt.content_digest == DIGEST_A


def test_concurrent_first_writer_leaves_one_row() -> None:
    connection, store, receipt = _store()
    barrier = threading.Barrier(2)
    results: list[InstructionReceipt | None] = []

    def worker() -> None:
        barrier.wait()
        results.append(store.compare_and_insert(receipt.receipt_key, receipt))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(result is None for result in results) == [False, True]
    assert len(connection.rows) == 1
    assert results[0] == results[1] or None in results


def test_concurrent_conflict_cannot_replace_the_winner() -> None:
    connection = FakeConnection()
    store = PostgresReceiptStore(connection)
    first = _receipt(digest=DIGEST_A)
    second = _receipt(digest=DIGEST_B)
    barrier = threading.Barrier(2)
    results: list[InstructionReceipt | None] = []

    def worker(receipt: InstructionReceipt) -> None:
        barrier.wait()
        results.append(store.compare_and_insert(receipt.receipt_key, receipt))

    threads = [
        threading.Thread(target=worker, args=(first,)),
        threading.Thread(target=worker, args=(second,)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    stored = connection.rows[MESSAGE_ID]["content_digest"]
    assert stored in {DIGEST_A, DIGEST_B}
    assert [stored == DIGEST_A, stored == DIGEST_B].count(True) == 1
    assert None in results
    returned = next(result for result in results if result is not None)
    assert returned.content_digest == stored
    assert list(connection.rows) == [MESSAGE_ID]


def test_caller_rollback_removes_the_uncommitted_insert() -> None:
    connection, store, receipt = _store()
    connection.begin()

    assert store.compare_and_insert(receipt.receipt_key, receipt) is None
    connection.rollback()

    assert connection.rows == {}
    assert connection.commits == 0
    assert store.compare_and_insert(receipt.receipt_key, receipt) is None


def test_lost_acknowledgement_is_redacted_and_keeps_the_written_row() -> None:
    connection, store, receipt = _store()
    connection.lose_next_insert = True
    connection.fail_with = psycopg.OperationalError(f"password={SECRET} host=203.0.113.10")

    with pytest.raises(ReceiptStoreUnavailable) as caught:
        store.compare_and_insert(receipt.receipt_key, receipt)

    rendered = "".join(traceback.format_exception(caught.value))
    assert caught.value.args == ("RECEIPT_STORE_UNAVAILABLE",)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert SECRET not in rendered
    assert "203.0.113.10" not in rendered
    assert connection.rows[receipt.receipt_key]["content_digest"] == DIGEST_A
    assert connection.commits == 0


def test_authoritative_later_read_returns_the_surviving_original() -> None:
    connection, store, receipt = _store()
    connection.lose_next_insert = True
    connection.fail_with = psycopg.OperationalError(SECRET)
    with pytest.raises(ReceiptStoreUnavailable):
        store.compare_and_insert(receipt.receipt_key, receipt)

    found = store.compare_and_insert(receipt.receipt_key, _receipt(digest=DIGEST_B))

    assert found == receipt
    assert connection.rows[receipt.receipt_key]["content_digest"] == DIGEST_A


def test_json_round_trip_preserves_the_allowlisted_receipt() -> None:
    connection, store, receipt = _store()
    accepted = _receipt(disposition=Disposition.ACCEPT)
    assert store.compare_and_insert(accepted.receipt_key, accepted) is None

    connection.reload_json()
    found = store.compare_and_insert(accepted.receipt_key, accepted)

    assert found == accepted
    assert found is not None
    assert found.instruction_ids == (f"v1:email_instruction:{DIGEST_A}:0",)
    assert found.reasons == ()
    assert found.source_timestamp == "2024-01-01T00:00:00Z"
    assert json.loads(json.dumps(connection.rows)) == connection.rows


def test_sql_errors_redact_driver_details() -> None:
    connection, store, receipt = _store()
    connection.fail_with = SQLAlchemyError(f"token={SECRET} dbname=swingtrade_receipt_test")

    with pytest.raises(ReceiptStoreUnavailable) as caught:
        store.compare_and_insert(receipt.receipt_key, receipt)

    rendered = "".join(traceback.format_exception(caught.value))
    assert SECRET not in rendered
    assert "swingtrade_receipt_test" not in rendered
    assert connection.rows == {}
    assert caught.value.__context__ is None


def test_raw_body_and_economic_fields_are_not_stored() -> None:
    connection, store, _receipt_value = _store()
    accepted = _receipt(disposition=Disposition.ACCEPT)
    store.compare_and_insert(accepted.receipt_key, accepted)
    stored = json.dumps(connection.rows)

    for token in PROHIBITED:
        assert token not in stored
    assert set(connection.rows[MESSAGE_ID]) == set(COLUMNS)
    assert "body" not in InstructionReceiptRow.__table__.columns
    assert "raw_body" not in InstructionReceiptRow.__table__.columns


def test_mismatched_key_writes_nothing() -> None:
    connection, store, receipt = _store()

    with pytest.raises(ReceiptStoreUnavailable) as caught:
        store.compare_and_insert(DIGEST_B, receipt)

    assert caught.value.args == ("RECEIPT_STORE_UNAVAILABLE",)
    assert connection.inserts == 0
    assert connection.rows == {}


def test_import_does_not_open_a_connection() -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment.pop("SWINGTRADE_TEST_POSTGRES_URL", None)
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import socket\n"
            "socket.create_connection = lambda *args, **kwargs: (_ for _ in ()).throw(\n"
            "    RuntimeError('socket')\n"
            ")\n"
            "import swingtrade.postgres_receipt_store as store\n"
            "assert not hasattr(store, 'create_engine')\n"
            "print('IMPORT_OK')\n",
        ],
        check=False,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "IMPORT_OK" in completed.stdout
    source = (ROOT / "src" / "swingtrade" / "postgres_receipt_store.py").read_text(encoding="utf-8")
    for prohibited in ("create_engine", "psycopg.connect", "urlopen", "alpaca", "broker"):
        assert prohibited not in source


def test_migration_schema_matches_the_receipt_contract() -> None:
    module = _migration_module()
    tree = ast.parse(MIGRATION.read_text(encoding="utf-8"))
    table_name, columns, digest_length = _schema(tree)

    assert module.revision == "0004_instruction_receipts"
    assert module.down_revision == "0003_durable_dry_run_observation"
    assert table_name == "instruction_receipts"
    assert columns == COLUMNS
    assert digest_length == 64
    assert set(InstructionReceiptRow.__table__.columns.keys()) == set(COLUMNS)
    assert InstructionReceiptRow.receipt_key.primary_key is True
    for token in ("body", "raw_body", "mime", "payload", "password", "secret"):
        assert token not in columns


def test_revision_ancestry_follows_0003() -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    revision = script.get_revision("0004_instruction_receipts")

    assert revision.down_revision == "0003_durable_dry_run_observation"
    chain = ["0004_instruction_receipts"]
    current = revision.down_revision
    while current is not None:
        chain.append(current)
        parent = script.get_revision(current)
        current = parent.down_revision
    assert chain == [
        "0004_instruction_receipts",
        "0003_durable_dry_run_observation",
        "0002_canonical_order_intents",
        "0001_offline_foundation",
    ]


def test_existing_guard_refuses_to_execute_revision_0004(monkeypatch: pytest.MonkeyPatch) -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    assert "0004_instruction_receipts" not in env.ALLOWED_REVISIONS
    script = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    pairs = [(item.revision, item.down_revision) for item in script.walk_revisions()]
    with pytest.raises(env.AlembicTargetRejected) as walked:
        env.validate_revision_transition(None, "head", pairs)
    assert walked.value.code == "revision_0004"

    class _Config:
        def __init__(self) -> None:
            self.cmd_opts = SimpleNamespace(cmd=(_named("upgrade"), [], {}))
            self.config_file_name = None

        def get_main_option(self, _name: str, default: str | None = None) -> str:
            raise AssertionError("committed URL fallback")

        def get_section(self, _name: str, default: object = None) -> dict[str, str]:
            raise AssertionError("committed URL fallback")

    class _Script:
        def walk_revisions(self) -> list[SimpleNamespace]:
            return [
                SimpleNamespace(
                    revision="0004_instruction_receipts",
                    down_revision="0003_durable_dry_run_observation",
                )
            ]

    class _Proxy:
        def __init__(self) -> None:
            self.config = _Config()
            self.context_opts = {"fn": _named("upgrade"), "as_sql": False}
            self.script = _Script()

        def is_offline_mode(self) -> bool:
            return False

        def get_revision_argument(self) -> str:
            return "0004_instruction_receipts"

        def configure(self, **_kwargs: object) -> None:
            raise AssertionError("migration configured")

        def run_migrations(self, **_kwargs: object) -> None:
            raise AssertionError("migration executed")

    connects = {"n": 0}

    def factory(*_args: object, **_kwargs: object) -> object:
        connects["n"] += 1
        raise AssertionError("create_engine")

    monkeypatch.setattr(env.context, "_proxy", _Proxy(), raising=False)
    monkeypatch.setenv(
        env.TARGET_ENV,
        f"postgresql+psycopg://swingtrade_migrator:{SECRET}@127.0.0.1:5433/swingtrade_receipt_test",
    )
    monkeypatch.setattr(env, "create_engine", factory)

    with pytest.raises(env.AlembicTargetRejected) as caught:
        env.run_migrations_online()

    assert caught.value.code == "revision_0004"
    assert connects["n"] == 0
    assert SECRET not in "".join(traceback.format_exception(caught.value))
    assert caught.value.__context__ is None


def test_real_postgresql_execution_is_not_run() -> None:
    assert REAL_POSTGRESQL_EXECUTION == "NOT_RUN"
    assert os.getenv("SWINGTRADE_TEST_POSTGRES_URL") is None


def _schema(tree: ast.AST) -> tuple[str, tuple[str, ...], int]:
    table_name = ""
    columns: list[str] = []
    digest_length = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _call_name(node) == "create_table":
            continue
        table_name = _constant(node.args[0])
        for argument in node.args[1:]:
            if not isinstance(argument, ast.Call):
                continue
            if _call_name(argument) == "Column":
                name = _constant(argument.args[0])
                columns.append(name)
                if name == "content_digest":
                    digest_length = _constant(argument.args[1].args[0])  # type: ignore[attr-defined]
            if _call_name(argument) == "PrimaryKeyConstraint":
                assert _constant(argument.args[0]) == "receipt_key"
    return table_name, tuple(columns), digest_length


def _call_name(node: ast.Call) -> str:
    function = node.func
    if isinstance(function, ast.Attribute):
        return function.attr
    if isinstance(function, ast.Name):
        return function.id
    return ""


def _constant(node: ast.AST) -> object:
    assert isinstance(node, ast.Constant)
    return node.value
