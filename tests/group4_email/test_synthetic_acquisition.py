"""Focused tests for deterministic synthetic fixture delivery."""

from __future__ import annotations

import ast
import hashlib
from dataclasses import fields
from decimal import Decimal
from pathlib import Path

import pytest

from swingtrade.group4_email.contract import Disposition, MessageType
from swingtrade.group4_email.disposition import DispositionViewLabel, derive_disposition_view
from swingtrade.group4_email.normalize import content_digest
from swingtrade.group4_email.parse import MessageIdentityRegistry, parse_email
from swingtrade.group4_email.synthetic_acquisition import (
    SyntheticAcquisitionError,
    SyntheticDelivery,
    SyntheticFixture,
    _content_digest,
    deliver_synthetic_fixtures,
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
MODULE = Path("src/swingtrade/group4_email/synthetic_acquisition.py")
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
    "parse_email",
    "admit_instruction_receipt",
    "gmail",
    "postgresql",
)
MALFORMED = (
    b"Message-ID: <bad@example.invalid>\r\n"
    b"MIME-Version: 1.0\r\n"
    b'Content-Type: multipart/mixed; boundary="abc"\r\n'
    b"\r\n--abc\r\nContent-Type: text/plain\r\n\r\nhello\r\n"
)


def _reject(fixtures: object, code: str) -> SyntheticAcquisitionError:
    with pytest.raises(SyntheticAcquisitionError, match=f"^{code}$") as caught:
        deliver_synthetic_fixtures(fixtures)  # type: ignore[arg-type]
    assert caught.value.code == code
    assert caught.value.args == (code,)
    return caught.value


def test_single_valid_fixture() -> None:
    raw = b"From: synthetic@gmail.com\r\nMessage-ID: <x@gmail.com>\r\n\r\nhello"
    fixture = SyntheticFixture("syn-delivery-1", raw)
    (delivery,) = deliver_synthetic_fixtures((fixture,))

    assert type(delivery) is SyntheticDelivery
    assert delivery.delivery_ref == "syn-delivery-1"
    assert delivery.mime == raw
    assert delivery.mime is not raw
    assert b"gmail.com" in delivery.mime
    assert delivery.content_digest == content_digest(raw)


def test_multiple_fixtures_preserve_caller_order() -> None:
    deliveries = deliver_synthetic_fixtures(
        (
            SyntheticFixture("syn-delivery-20", b"later-number"),
            SyntheticFixture("syn-delivery-3", b"earlier-number"),
            SyntheticFixture("syn-delivery-999999", b"upper-bound"),
        )
    )

    assert [item.delivery_ref for item in deliveries] == [
        "syn-delivery-20",
        "syn-delivery-3",
        "syn-delivery-999999",
    ]
    assert [item.mime for item in deliveries] == [
        b"later-number",
        b"earlier-number",
        b"upper-bound",
    ]


def test_empty_tuple() -> None:
    assert deliver_synthetic_fixtures(()) == ()


def test_identical_mime_with_distinct_references() -> None:
    raw = b"shared-opaque-bytes"
    first, second = deliver_synthetic_fixtures(
        (
            SyntheticFixture("syn-delivery-7", raw),
            SyntheticFixture("syn-delivery-8", raw),
        )
    )

    assert first.mime == second.mime == raw
    assert first.content_digest == second.content_digest == content_digest(raw)
    assert first.delivery_ref != second.delivery_ref


def test_duplicate_reference_with_identical_mime() -> None:
    raw = b"same-bytes"
    error = _reject(
        (
            SyntheticFixture("syn-delivery-5", raw),
            SyntheticFixture("syn-delivery-5", raw),
        ),
        "DUPLICATE_DELIVERY_REF",
    )

    assert "syn-delivery-5" not in str(error)
    assert "syn-delivery-5" not in repr(error)
    assert "same-bytes" not in str(error)


def test_duplicate_reference_with_different_mime() -> None:
    error = _reject(
        (
            SyntheticFixture("syn-delivery-6", b"one-body"),
            SyntheticFixture("syn-delivery-6", b"other-body"),
        ),
        "DUPLICATE_DELIVERY_REF",
    )

    assert "one-body" not in str(error)
    assert "other-body" not in str(error)


def test_empty_reference() -> None:
    error = _reject((SyntheticFixture("", b"opaque"),), "INVALID_DELIVERY_REF")
    assert str(error) == "INVALID_DELIVERY_REF"


@pytest.mark.parametrize(
    "reference",
    [
        "syn-delivery-",
        "syn-delivery-0",
        "syn-delivery-01",
        "syn-delivery-1000000",
        "syn-delivery-1 ",
        "SYN-delivery-1",
        "signals@example.invalid",
        "<tday@example.invalid>",
        "v1:email_instruction:abc:0",
        "syn-delivery-\uff11",
    ],
)
def test_invalid_reference_grammar(reference: str) -> None:
    error = _reject((SyntheticFixture(reference, b"opaque"),), "INVALID_DELIVERY_REF")
    assert reference not in str(error)
    assert reference not in repr(error)


@pytest.mark.parametrize("reference", [None, 1, b"syn-delivery-1", ("syn-delivery-1",)])
def test_non_string_reference(reference: object) -> None:
    error = _reject(
        (SyntheticFixture(reference, b"opaque"),),  # type: ignore[arg-type]
        "INVALID_DELIVERY_REF",
    )
    assert repr(reference) not in str(error)


@pytest.mark.parametrize(
    "value",
    [
        None,
        [],
        [SyntheticFixture("syn-delivery-1", b"a")],
        SyntheticFixture("syn-delivery-1", b"a"),
        iter(()),
    ],
)
def test_non_tuple_input(value: object) -> None:
    _reject(value, "INVALID_FIXTURE")


def test_non_fixture_tuple_member() -> None:
    payload = b"opaque"
    _reject(("syn-delivery-1", payload), "INVALID_FIXTURE")
    _reject((payload,), "INVALID_FIXTURE")


@pytest.mark.parametrize("mime", ["opaque", bytearray(b"opaque"), None, 1, memoryview(b"opaque")])
def test_non_bytes_mime(mime: object) -> None:
    error = _reject(
        (SyntheticFixture("syn-delivery-1", mime),),  # type: ignore[arg-type]
        "INVALID_FIXTURE",
    )
    assert "opaque" not in str(error)


def test_later_invalid_member_rejects_the_whole_tuple(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def counting(raw: bytes) -> str:
        nonlocal calls
        calls += 1
        return content_digest(raw)

    monkeypatch.setattr(
        "swingtrade.group4_email.synthetic_acquisition._content_digest",
        counting,
    )
    first = SyntheticFixture("syn-delivery-1", b"kept")
    second = SyntheticFixture("syn-delivery-0", b"later-invalid")
    fixtures = (first, second)

    _reject(fixtures, "INVALID_DELIVERY_REF")

    assert calls == 0
    assert first.mime == b"kept"
    assert second.mime == b"later-invalid"
    _reject((first, object()), "INVALID_FIXTURE")
    assert calls == 0


def test_structure_precedes_reference_and_duplicate_codes() -> None:
    _reject(
        (
            SyntheticFixture("not-a-ref", b"a"),
            object(),
        ),
        "INVALID_FIXTURE",
    )
    _reject(
        (
            SyntheticFixture("syn-delivery-1", b"a"),
            SyntheticFixture("syn-delivery-1", b"b"),
            SyntheticFixture("nope", b"c"),
        ),
        "INVALID_DELIVERY_REF",
    )


def test_exact_mime_byte_preservation() -> None:
    raw = b"From: synthetic@gmail.com\r\n\r\n\xff\xfeopaque\x00\r\nline"
    (delivery,) = deliver_synthetic_fixtures((SyntheticFixture("syn-delivery-9", raw),))

    assert delivery.mime == raw
    assert delivery.mime is not raw
    assert b"syn-delivery-9" not in delivery.mime


def test_digest_parity_with_existing_content_digest() -> None:
    raw = b"digest-parity"
    (delivery,) = deliver_synthetic_fixtures((SyntheticFixture("syn-delivery-4", raw),))

    assert _content_digest is content_digest
    assert delivery.content_digest == content_digest(raw)
    assert delivery.content_digest == hashlib.sha256(raw).hexdigest()
    assert "sha256" not in MODULE.read_text(encoding="utf-8")


def test_repeated_invocation_is_deterministic() -> None:
    fixtures = (
        SyntheticFixture("syn-delivery-2", b"b"),
        SyntheticFixture("syn-delivery-1", b"a"),
    )
    first = deliver_synthetic_fixtures(fixtures)
    second = deliver_synthetic_fixtures(fixtures)

    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    assert first[0].mime is not second[0].mime
    assert [item.delivery_ref for item in first] == ["syn-delivery-2", "syn-delivery-1"]


def test_duplicate_reference_is_scoped_to_one_tuple() -> None:
    fixture = SyntheticFixture("syn-delivery-1", b"again")
    assert deliver_synthetic_fixtures((fixture,)) == deliver_synthetic_fixtures((fixture,))


def test_input_objects_are_not_mutated() -> None:
    raw = b"stable-bytes"
    fixture = SyntheticFixture("syn-delivery-4", raw)
    fixtures = (fixture,)
    before = (fixture.delivery_ref, fixture.mime, id(fixture), id(fixtures))

    delivered = deliver_synthetic_fixtures(fixtures)

    assert (fixture.delivery_ref, fixture.mime, id(fixture), id(fixtures)) == before
    assert fixture.mime is raw
    assert delivered[0].mime is not raw
    with pytest.raises(AttributeError):
        fixture.delivery_ref = "syn-delivery-5"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        delivered[0].mime = b"changed"  # type: ignore[misc]


def test_error_messages_are_redacted() -> None:
    reference = "mailbox-secret@example.invalid"
    raw = b"SYNTHETIC-REDACTION-TOKEN\xff\xfe"
    error = _reject((SyntheticFixture(reference, raw),), "INVALID_DELIVERY_REF")
    rendered = f"{error} {error!r} {error.args}"

    assert rendered == (
        "INVALID_DELIVERY_REF "
        "SyntheticAcquisitionError('INVALID_DELIVERY_REF') "
        "('INVALID_DELIVERY_REF',)"
    )
    assert "mailbox-secret" not in rendered
    assert "SYNTHETIC-REDACTION-TOKEN" not in rendered
    assert "example.invalid" not in rendered


def test_no_network_credential_or_database_access() -> None:
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
        (None, ("re",)),
        ("dataclasses", ("dataclass",)),
        ("swingtrade.group4_email.normalize", ("content_digest",)),
    ]
    names = set(deliver_synthetic_fixtures.__code__.co_names)
    for token in ("open", "socket", "connect", "urlopen", "system"):
        assert token not in names
    lowered = source.lower()
    for token in _BANNED:
        assert token.lower() not in lowered


def test_no_order_intent_or_quantity_promotion() -> None:
    names = {item.name for item in fields(SyntheticDelivery)}
    assert names == {"delivery_ref", "mime", "content_digest"}
    raw = plain_message(DATED, "<acq-qty@example.invalid>")
    (delivery,) = deliver_synthetic_fixtures((SyntheticFixture("syn-delivery-11", raw),))
    outcome = parse_email(delivery.mime)

    assert outcome.instructions[0].sizing.example_quantity == Decimal("69")
    assert "example_quantity" not in names
    assert outcome.network_permitted is False


def test_composition_new_trade_is_recorded_and_receipt_is_new() -> None:
    raw = plain_message(DATED, "<acq-trade@example.invalid>")
    (delivery,) = deliver_synthetic_fixtures((SyntheticFixture("syn-delivery-21", raw),))
    outcome = parse_email(delivery.mime)
    view = derive_disposition_view(outcome)
    decision = admit_instruction_receipt(outcome, InMemoryReceiptStore())

    assert outcome.message_type is MessageType.NEW_TRADE
    assert outcome.disposition is Disposition.ACCEPT
    assert view.label is DispositionViewLabel.RECORDED_NOT_EXECUTABLE
    assert view.label is not DispositionViewLabel.DUPLICATE
    assert decision.kind is ReceiptKind.NEW
    assert decision.receipt.receipt_key == "<acq-trade@example.invalid>"
    assert decision.receipt.receipt_key != delivery.delivery_ref
    assert decision.receipt.content_digest == delivery.content_digest
    assert decision.receipt.provider_message_ref == outcome.message_id


def test_composition_identical_redelivery_is_receipt_replay() -> None:
    raw = plain_message(DATED, "<acq-replay@example.invalid>")
    (first,) = deliver_synthetic_fixtures((SyntheticFixture("syn-delivery-22", raw),))
    (second,) = deliver_synthetic_fixtures((SyntheticFixture("syn-delivery-23", raw),))
    store = InMemoryReceiptStore()
    original = parse_email(first.mime)
    replayed = parse_email(second.mime)
    first_decision = admit_instruction_receipt(original, store)
    second_decision = admit_instruction_receipt(replayed, store)

    assert first.content_digest == second.content_digest
    assert first.delivery_ref != second.delivery_ref
    assert derive_disposition_view(original).label is DispositionViewLabel.RECORDED_NOT_EXECUTABLE
    assert derive_disposition_view(replayed).label is DispositionViewLabel.RECORDED_NOT_EXECUTABLE
    assert first_decision.kind is ReceiptKind.NEW
    assert second_decision.kind is ReceiptKind.REPLAY
    assert second_decision.receipt is first_decision.receipt
    assert "DUPLICATE" not in second_decision.receipt.reasons
    assert len(store) == 1


def test_composition_changed_digest_conflicts_without_replacing_the_receipt() -> None:
    registry = MessageIdentityRegistry()
    original_raw = plain_message(DATED, "<acq-conflict@example.invalid>")
    changed_raw = plain_message(DATED + "\nUnrelated tail.\n", "<acq-conflict@example.invalid>")
    first, second = deliver_synthetic_fixtures(
        (
            SyntheticFixture("syn-delivery-30", original_raw),
            SyntheticFixture("syn-delivery-31", changed_raw),
        )
    )
    original = registry.parse(first.mime)
    conflict = registry.parse(second.mime)
    store = InMemoryReceiptStore()
    admitted = admit_instruction_receipt(original, store)
    decision = admit_instruction_receipt(conflict, store)

    assert derive_disposition_view(original).label is DispositionViewLabel.RECORDED_NOT_EXECUTABLE
    assert conflict.reasons == ("CONFLICTING_DUPLICATE",)
    assert derive_disposition_view(conflict).label is DispositionViewLabel.QUARANTINED
    assert derive_disposition_view(conflict).label is not DispositionViewLabel.DUPLICATE
    assert admitted.kind is ReceiptKind.NEW
    assert decision.kind is ReceiptKind.CONFLICT
    assert decision.conflict_reason == "CONFLICTING_DUPLICATE"
    assert decision.receipt is admitted.receipt
    assert decision.receipt.content_digest == first.content_digest
    assert decision.receipt.content_digest != second.content_digest
    assert decision.receipt.receipt_key != second.delivery_ref
    assert len(store) == 1


def test_composition_quarantine_and_reject_keep_their_meanings() -> None:
    amendment = plain_message(
        "Trade amendment: stop is now sell stop $6.00, good till cancelled.\n",
        "<acq-amend@example.invalid>",
    )
    exit_alert = plain_message(
        "Exit alert: sell at the open Mon Nov 9, 2026.\n",
        "<acq-exit@example.invalid>",
    )
    cancel = plain_message("Trade cancel: TDAY\n", "<acq-cancel@example.invalid>")
    foreign = plain_message(DATED, "<user@gmail.com>")
    deliveries = deliver_synthetic_fixtures(
        (
            SyntheticFixture("syn-delivery-40", amendment),
            SyntheticFixture("syn-delivery-41", exit_alert),
            SyntheticFixture("syn-delivery-42", cancel),
            SyntheticFixture("syn-delivery-43", foreign),
            SyntheticFixture("syn-delivery-44", MALFORMED),
        )
    )
    parsed = [parse_email(item.mime) for item in deliveries]
    views = [derive_disposition_view(item) for item in parsed]

    assert parsed[0].reasons == ("PARSER_DEFERRED",)
    assert parsed[1].reasons == ("PARSER_DEFERRED",)
    assert "CANCEL_FORMAT_UNSPECIFIED" in parsed[2].reasons
    assert views[0].label is DispositionViewLabel.DEFERRED
    assert views[1].label is DispositionViewLabel.DEFERRED
    assert views[2].label is DispositionViewLabel.DEFERRED
    assert parsed[3].reasons == ("NON_FIXTURE_MESSAGE_ID",)
    assert parsed[3].message_id is None
    assert views[3].label is DispositionViewLabel.QUARANTINED
    assert parsed[4].disposition is Disposition.REJECT
    assert parsed[4].reasons == ("MALFORMED_MIME",)
    assert views[4].label is DispositionViewLabel.REJECT
    assert all(
        item.mime == source
        for item, source in zip(
            deliveries,
            (
                amendment,
                exit_alert,
                cancel,
                foreign,
                MALFORMED,
            ),
            strict=True,
        )
    )


def test_composition_receipt_store_failure_stays_fail_closed() -> None:
    raw = plain_message(DATED, "<acq-store@example.invalid>")
    fixture = SyntheticFixture("syn-delivery-45", raw)
    (delivery,) = deliver_synthetic_fixtures((fixture,))
    calls = 0

    class Boom:
        def compare_and_insert(
            self, key: str, receipt: InstructionReceipt
        ) -> InstructionReceipt | None:
            nonlocal calls
            calls += 1
            raise RuntimeError("injected-store-failure")

    with pytest.raises(ReceiptStoreUnavailable, match="^RECEIPT_STORE_UNAVAILABLE$") as caught:
        admit_instruction_receipt(parse_email(delivery.mime), Boom())

    assert calls == 1
    assert "injected-store-failure" not in str(caught.value)
    assert caught.value.__cause__ is None
    assert deliver_synthetic_fixtures((fixture,))[0] == delivery


def test_composition_caller_order_changes_processing_order_only() -> None:
    trade = plain_message(DATED, "<acq-order-a@example.invalid>")
    notice = plain_message(
        "14 more swing orders remain behind the member notice.\n",
        "<acq-order-b@example.invalid>",
    )
    forward = deliver_synthetic_fixtures(
        (
            SyntheticFixture("syn-delivery-50", trade),
            SyntheticFixture("syn-delivery-51", notice),
        )
    )
    reverse = deliver_synthetic_fixtures(
        (
            SyntheticFixture("syn-delivery-51", notice),
            SyntheticFixture("syn-delivery-50", trade),
        )
    )
    forward_types = [parse_email(item.mime).message_type for item in forward]
    reverse_types = [parse_email(item.mime).message_type for item in reverse]

    assert forward_types == [MessageType.NEW_TRADE, MessageType.INFORMATIONAL]
    assert reverse_types == [MessageType.INFORMATIONAL, MessageType.NEW_TRADE]
    assert {item.content_digest for item in forward} == {item.content_digest for item in reverse}
    assert [item.delivery_ref for item in forward] == ["syn-delivery-50", "syn-delivery-51"]
