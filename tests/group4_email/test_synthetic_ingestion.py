"""Focused tests for the synthetic ingestion composition."""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

import pytest

from swingtrade.group4_email.contract import Disposition, MessageType
from swingtrade.group4_email.disposition import DispositionViewLabel
from swingtrade.group4_email.parse import MessageIdentityRegistry, parse_email
from swingtrade.group4_email.synthetic_acquisition import (
    SyntheticAcquisitionError,
    SyntheticFixture,
)
from swingtrade.group4_email.synthetic_ingestion import (
    SyntheticIngestionRecord,
    SyntheticIngestionRejected,
    record_synthetic_ingestion,
)
from swingtrade.instruction_receipt import (
    InMemoryReceiptStore,
    InstructionReceipt,
    ReceiptKind,
    ReceiptStoreUnavailable,
    admit_instruction_receipt,
)
from tests.group4_email.conftest import body, plain_message

DATED = body("tday_dated.txt")
MODULE = Path("src/swingtrade/group4_email/synthetic_ingestion.py")
MALFORMED = (
    b"Message-ID: <bad@example.invalid>\r\n"
    b"MIME-Version: 1.0\r\n"
    b'Content-Type: multipart/mixed; boundary="abc"\r\n'
    b"\r\n--abc\r\nContent-Type: text/plain\r\n\r\nhello\r\n"
)
_RECORD_FIELDS = {
    "delivery_ref",
    "content_digest",
    "parser_disposition",
    "parser_message_type",
    "parser_reasons",
    "view_label",
    "receipt_kind",
    "receipt_key",
    "conflict_reason",
}
_BANNED = (
    "OrderIntent",
    "example_quantity",
    "socket",
    "ctypes",
    "CredWrite",
    "CredRead",
    "psycopg",
    "sqlalchemy",
    "alembic",
    "httpx",
    "urllib",
    "oauth",
    "sqlite",
    "subprocess",
    "smtplib",
    "imaplib",
    "BytesParser",
    "normalize_email",
    "evaluate_receipt_commit",
    "evaluate_report_sequence",
    "asdict",
    "logging",
    "postgresql",
)


class CountingStore:
    """In-memory store that records how many admissions were attempted."""

    def __init__(self) -> None:
        self.calls = 0
        self.inner = InMemoryReceiptStore()

    def compare_and_insert(
        self, key: str, receipt: InstructionReceipt
    ) -> InstructionReceipt | None:
        self.calls += 1
        return self.inner.compare_and_insert(key, receipt)


class SecondCallFails(CountingStore):
    """Fail the second admission and leave the first row in place."""

    def compare_and_insert(
        self, key: str, receipt: InstructionReceipt
    ) -> InstructionReceipt | None:
        self.calls += 1
        if self.calls == 2:
            raise RuntimeError("injected-store-failure")
        return self.inner.compare_and_insert(key, receipt)


def _trade(message_id: str = "<ingest-trade@example.invalid>") -> bytes:
    return plain_message(DATED, message_id)


def test_valid_new_trade_keeps_three_statuses_distinct() -> None:
    raw = _trade()
    store = InMemoryReceiptStore()
    (record,) = record_synthetic_ingestion(
        (SyntheticFixture("syn-delivery-1", raw),),
        store,
    )

    assert type(record) is SyntheticIngestionRecord
    assert {item.name for item in fields(record)} == _RECORD_FIELDS
    assert record.parser_disposition is Disposition.ACCEPT
    assert record.parser_message_type is MessageType.NEW_TRADE
    assert record.parser_reasons == ()
    assert record.view_label is DispositionViewLabel.RECORDED_NOT_EXECUTABLE
    assert record.receipt_kind is ReceiptKind.NEW
    assert record.conflict_reason is None
    assert record.receipt_key == "<ingest-trade@example.invalid>"
    assert record.receipt_key != record.delivery_ref
    assert record.content_digest == parse_email(raw).content_digest
    assert len(store) == 1


def test_identical_redelivery_is_receipt_replay() -> None:
    raw = _trade("<ingest-replay@example.invalid>")
    store = InMemoryReceiptStore()
    first, second = record_synthetic_ingestion(
        (
            SyntheticFixture("syn-delivery-1", raw),
            SyntheticFixture("syn-delivery-2", raw),
        ),
        store,
    )

    assert first.delivery_ref != second.delivery_ref
    assert first.content_digest == second.content_digest
    assert second.parser_disposition is Disposition.ACCEPT
    assert second.view_label is DispositionViewLabel.RECORDED_NOT_EXECUTABLE
    assert first.receipt_kind is ReceiptKind.NEW
    assert second.receipt_kind is ReceiptKind.REPLAY
    assert second.receipt_key == first.receipt_key
    assert second.conflict_reason is None
    assert len(store) == 1


def test_changed_digest_conflicts_without_replacing_the_receipt() -> None:
    original = _trade("<ingest-conflict@example.invalid>")
    changed = plain_message(DATED + "\nUnrelated tail.\n", "<ingest-conflict@example.invalid>")
    store = InMemoryReceiptStore()
    first, second = record_synthetic_ingestion(
        (
            SyntheticFixture("syn-delivery-1", original),
            SyntheticFixture("syn-delivery-2", changed),
        ),
        store,
    )
    retained = admit_instruction_receipt(parse_email(original), store)

    assert second.parser_disposition is Disposition.QUARANTINE
    assert second.parser_message_type is MessageType.NEW_TRADE
    assert second.parser_reasons == ("CONFLICTING_DUPLICATE",)
    assert second.view_label is DispositionViewLabel.QUARANTINED
    assert second.view_label is not DispositionViewLabel.DUPLICATE
    assert second.receipt_kind is ReceiptKind.CONFLICT
    assert second.conflict_reason == "CONFLICTING_DUPLICATE"
    assert second.content_digest != first.content_digest
    assert second.receipt_key == first.receipt_key
    assert retained.kind is ReceiptKind.REPLAY
    assert retained.receipt.disposition is Disposition.ACCEPT
    assert retained.receipt.content_digest == first.content_digest
    assert retained.receipt.content_digest != second.content_digest
    assert len(store) == 1


def test_deferred_amendment() -> None:
    raw = plain_message(
        "Trade amendment: stop is now sell stop $6.00, good till cancelled.\n",
        "<ingest-amend@example.invalid>",
    )
    (record,) = record_synthetic_ingestion(
        (SyntheticFixture("syn-delivery-1", raw),),
        InMemoryReceiptStore(),
    )

    assert record.parser_disposition is Disposition.QUARANTINE
    assert record.parser_message_type is MessageType.TRADE_AMENDMENT
    assert record.parser_reasons == ("PARSER_DEFERRED",)
    assert record.view_label is DispositionViewLabel.DEFERRED
    assert record.receipt_kind is ReceiptKind.NEW
    assert record.receipt_key == "<ingest-amend@example.invalid>"


def test_deferred_exit() -> None:
    raw = plain_message(
        "Exit alert: sell at the open Mon Nov 9, 2026.\n",
        "<ingest-exit@example.invalid>",
    )
    (record,) = record_synthetic_ingestion(
        (SyntheticFixture("syn-delivery-1", raw),),
        InMemoryReceiptStore(),
    )

    assert record.parser_disposition is Disposition.QUARANTINE
    assert record.parser_message_type is MessageType.EXIT_ALERT
    assert record.parser_reasons == ("PARSER_DEFERRED",)
    assert record.view_label is DispositionViewLabel.DEFERRED
    assert record.receipt_kind is ReceiptKind.NEW


def test_deferred_cancellation() -> None:
    raw = plain_message("Trade cancel: TDAY\n", "<ingest-cancel@example.invalid>")
    (record,) = record_synthetic_ingestion(
        (SyntheticFixture("syn-delivery-1", raw),),
        InMemoryReceiptStore(),
    )

    assert record.parser_disposition is Disposition.QUARANTINE
    assert record.parser_message_type is MessageType.TRADE_CANCEL
    assert record.parser_reasons == ("CANCEL_FORMAT_UNSPECIFIED",)
    assert record.view_label is DispositionViewLabel.DEFERRED
    assert record.receipt_kind is ReceiptKind.NEW


def test_non_fixture_message_id_is_quarantined() -> None:
    raw = plain_message(DATED, "<user@gmail.com>")
    (record,) = record_synthetic_ingestion(
        (SyntheticFixture("syn-delivery-1", raw),),
        InMemoryReceiptStore(),
    )

    assert record.parser_disposition is Disposition.QUARANTINE
    assert record.parser_message_type is MessageType.NEW_TRADE
    assert record.parser_reasons == ("NON_FIXTURE_MESSAGE_ID",)
    assert record.view_label is DispositionViewLabel.QUARANTINED
    assert record.receipt_kind is ReceiptKind.NEW
    assert record.receipt_key == record.content_digest
    assert record.receipt_key != "syn-delivery-1"


def test_malformed_mime_rejects_and_receipt_is_new() -> None:
    (record,) = record_synthetic_ingestion(
        (SyntheticFixture("syn-delivery-1", MALFORMED),),
        InMemoryReceiptStore(),
    )

    assert record.parser_disposition is Disposition.REJECT
    assert record.parser_message_type is MessageType.UNKNOWN
    assert record.parser_reasons == ("MALFORMED_MIME",)
    assert record.view_label is DispositionViewLabel.REJECT
    assert record.receipt_kind is ReceiptKind.NEW
    assert record.receipt_key == record.content_digest
    assert record.view_label is not DispositionViewLabel.RECORDED_NOT_EXECUTABLE


def test_empty_tuple_does_not_touch_the_store() -> None:
    store = CountingStore()
    assert record_synthetic_ingestion((), store) == ()
    assert store.calls == 0


def test_wrong_fixture_input_preserves_the_acquisition_error() -> None:
    store = CountingStore()
    with pytest.raises(SyntheticAcquisitionError, match="^INVALID_FIXTURE$") as caught:
        record_synthetic_ingestion([SyntheticFixture("syn-delivery-1", b"a")], store)

    assert type(caught.value) is SyntheticAcquisitionError
    assert caught.value.code == "INVALID_FIXTURE"
    assert store.calls == 0


def test_invalid_later_reference_fails_before_store_access() -> None:
    store = CountingStore()
    registry = MessageIdentityRegistry()
    fixtures = (
        SyntheticFixture("syn-delivery-1", b"kept"),
        SyntheticFixture("syn-delivery-0", b"later-invalid"),
    )

    with pytest.raises(SyntheticAcquisitionError, match="^INVALID_DELIVERY_REF$"):
        record_synthetic_ingestion(fixtures, store, registry)

    assert store.calls == 0
    assert len(registry) == 0


def test_duplicate_reference_fails_before_store_access() -> None:
    store = CountingStore()
    fixtures = (
        SyntheticFixture("syn-delivery-1", b"one"),
        SyntheticFixture("syn-delivery-1", b"two"),
    )

    with pytest.raises(SyntheticAcquisitionError, match="^DUPLICATE_DELIVERY_REF$"):
        record_synthetic_ingestion(fixtures, store)

    assert store.calls == 0


def test_second_item_store_failure_keeps_the_first_receipt_and_stops() -> None:
    first_raw = _trade("<ingest-p1@example.invalid>")
    second_raw = _trade("<ingest-p2@example.invalid>")
    third_raw = _trade("<ingest-p3@example.invalid>")
    registry = MessageIdentityRegistry()
    store = SecondCallFails()
    fixtures = (
        SyntheticFixture("syn-delivery-1", first_raw),
        SyntheticFixture("syn-delivery-2", second_raw),
        SyntheticFixture("syn-delivery-3", third_raw),
    )

    with pytest.raises(ReceiptStoreUnavailable, match="^RECEIPT_STORE_UNAVAILABLE$") as caught:
        record_synthetic_ingestion(fixtures, store, registry)

    assert store.calls == 2
    assert len(store.inner) == 1
    assert len(registry) == 2
    retained = admit_instruction_receipt(parse_email(first_raw), store.inner)
    assert retained.kind is ReceiptKind.REPLAY
    assert str(caught.value) == "RECEIPT_STORE_UNAVAILABLE"
    assert "injected-store-failure" not in str(caught.value)
    assert "injected-store-failure" not in repr(caught.value)
    assert caught.value.args == ("RECEIPT_STORE_UNAVAILABLE",)
    again = parse_email(second_raw, registry)
    assert again.disposition is Disposition.ACCEPT
    assert len(registry) == 2
    third = admit_instruction_receipt(parse_email(third_raw), store.inner)
    assert third.kind is ReceiptKind.NEW


def test_record_is_frozen_and_caller_fixtures_stay_unchanged() -> None:
    raw = b"stable-opaque-bytes"
    fixture = SyntheticFixture("syn-delivery-4", raw)
    fixtures = (fixture,)
    before = (fixture.delivery_ref, fixture.mime, id(fixture), id(fixtures))
    (record,) = record_synthetic_ingestion(fixtures, InMemoryReceiptStore())

    assert (fixture.delivery_ref, fixture.mime, id(fixture), id(fixtures)) == before
    assert fixture.mime is raw
    with pytest.raises(AttributeError):
        record.delivery_ref = "syn-delivery-5"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        record.receipt_key = "changed"  # type: ignore[misc]


def test_repr_and_str_omit_receipt_key_and_mime() -> None:
    message_id = "<repr-secret@example.invalid>"
    raw = plain_message("SYNTHETIC-MIME-TOKEN\n" + DATED, message_id)
    (record,) = record_synthetic_ingestion(
        (SyntheticFixture("syn-delivery-8", raw),),
        InMemoryReceiptStore(),
    )
    rendered = f"{record} {record!r}"

    assert record.receipt_key == message_id
    assert message_id not in rendered
    assert "SYNTHETIC-MIME-TOKEN" not in rendered
    assert "repr-secret" not in rendered
    assert b"SYNTHETIC-MIME-TOKEN" not in rendered.encode()


def test_reversed_caller_order_is_preserved() -> None:
    trade = _trade("<ingest-order-a@example.invalid>")
    notice = plain_message(
        "14 more swing orders remain behind the member notice.\n",
        "<ingest-order-b@example.invalid>",
    )
    forward = record_synthetic_ingestion(
        (
            SyntheticFixture("syn-delivery-2", trade),
            SyntheticFixture("syn-delivery-1", notice),
        ),
        InMemoryReceiptStore(),
    )
    reverse = record_synthetic_ingestion(
        (
            SyntheticFixture("syn-delivery-1", notice),
            SyntheticFixture("syn-delivery-2", trade),
        ),
        InMemoryReceiptStore(),
    )

    assert [item.delivery_ref for item in forward] == ["syn-delivery-2", "syn-delivery-1"]
    assert [item.parser_message_type for item in forward] == [
        MessageType.NEW_TRADE,
        MessageType.INFORMATIONAL,
    ]
    assert [item.delivery_ref for item in reverse] == ["syn-delivery-1", "syn-delivery-2"]
    assert [item.parser_message_type for item in reverse] == [
        MessageType.INFORMATIONAL,
        MessageType.NEW_TRADE,
    ]
    assert forward[0].view_label is DispositionViewLabel.RECORDED_NOT_EXECUTABLE
    assert forward[1].view_label is DispositionViewLabel.INFORMATIONAL


def test_new_store_after_simulated_restart_admits_new() -> None:
    raw = _trade("<ingest-restart@example.invalid>")
    fixtures = (SyntheticFixture("syn-delivery-1", raw),)
    original_store = InMemoryReceiptStore()
    restarted_store = InMemoryReceiptStore()
    first = record_synthetic_ingestion(fixtures, original_store)
    second = record_synthetic_ingestion(fixtures, restarted_store)
    replay = record_synthetic_ingestion(fixtures, original_store)

    assert first[0].receipt_kind is ReceiptKind.NEW
    assert second[0].receipt_kind is ReceiptKind.NEW
    assert replay[0].receipt_kind is ReceiptKind.REPLAY
    assert len(original_store) == 1
    assert len(restarted_store) == 1


def test_default_registry_lasts_one_call() -> None:
    original = _trade("<ingest-life@example.invalid>")
    changed = plain_message(DATED + "\nUnrelated tail.\n", "<ingest-life@example.invalid>")
    store = InMemoryReceiptStore()
    first = record_synthetic_ingestion((SyntheticFixture("syn-delivery-1", original),), store)
    second = record_synthetic_ingestion((SyntheticFixture("syn-delivery-2", changed),), store)

    assert first[0].parser_disposition is Disposition.ACCEPT
    assert second[0].parser_disposition is Disposition.ACCEPT
    assert second[0].parser_reasons == ()
    assert second[0].receipt_kind is ReceiptKind.CONFLICT
    assert second[0].content_digest != first[0].content_digest


def test_injected_registry_is_reused_across_calls() -> None:
    original = _trade("<ingest-shared@example.invalid>")
    changed = plain_message(DATED + "\nUnrelated tail.\n", "<ingest-shared@example.invalid>")
    registry = MessageIdentityRegistry()
    first_store = InMemoryReceiptStore()
    second_store = InMemoryReceiptStore()
    first = record_synthetic_ingestion(
        (SyntheticFixture("syn-delivery-1", original),),
        first_store,
        registry,
    )
    second = record_synthetic_ingestion(
        (SyntheticFixture("syn-delivery-2", changed),),
        second_store,
        registry,
    )

    assert len(registry) == 1
    assert second[0].parser_disposition is Disposition.QUARANTINE
    assert second[0].parser_reasons == ("CONFLICTING_DUPLICATE",)
    assert second[0].view_label is DispositionViewLabel.QUARANTINED
    assert second[0].receipt_kind is ReceiptKind.NEW
    assert second[0].content_digest != first[0].content_digest
    assert len(second_store) == 1


def test_invalid_registry_fails_before_acquisition_or_store_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def forbidden(fixtures: object) -> tuple[object, ...]:
        nonlocal calls
        calls += 1
        return ()

    monkeypatch.setattr(
        "swingtrade.group4_email.synthetic_ingestion.deliver_synthetic_fixtures",
        forbidden,
    )
    store = CountingStore()

    class Loud:
        def __repr__(self) -> str:
            return "LOUD-REGISTRY-SECRET"

    with pytest.raises(SyntheticIngestionRejected, match="^INGESTION_INVALID$") as caught:
        record_synthetic_ingestion((), store, Loud())  # type: ignore[arg-type]

    assert calls == 0
    assert store.calls == 0
    assert caught.value.code == "INGESTION_INVALID"
    assert "LOUD-REGISTRY-SECRET" not in f"{caught.value} {caught.value!r} {caught.value.args}"

    class Child(MessageIdentityRegistry):
        pass

    with pytest.raises(SyntheticIngestionRejected, match="^INGESTION_INVALID$"):
        record_synthetic_ingestion((), store, Child())
    assert calls == 0
    assert store.calls == 0


def test_module_has_no_forbidden_imports_or_economic_logic() -> None:
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: list[tuple[str | None, tuple[str, ...]]] = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            imported.append((node.module, tuple(alias.name for alias in node.names)))
        elif isinstance(node, ast.Import):
            imported.append((None, tuple(alias.name for alias in node.names)))

    assert imported == [
        ("__future__", ("annotations",)),
        ("dataclasses", ("dataclass", "field")),
        ("typing", ("cast",)),
        ("swingtrade.group4_email.contract", ("Disposition", "MessageType")),
        (
            "swingtrade.group4_email.disposition",
            ("DispositionViewLabel", "derive_disposition_view"),
        ),
        ("swingtrade.group4_email.parse", ("MessageIdentityRegistry", "parse_email")),
        (
            "swingtrade.group4_email.synthetic_acquisition",
            ("SyntheticFixture", "deliver_synthetic_fixtures"),
        ),
        (
            "swingtrade.instruction_receipt",
            ("ReceiptKind", "ReceiptStore", "admit_instruction_receipt"),
        ),
    ]
    lowered = source.lower()
    for token in _BANNED:
        assert token.lower() not in lowered
    names = set(record_synthetic_ingestion.__code__.co_names)
    for token in ("open", "print", "socket", "system"):
        assert token not in names
