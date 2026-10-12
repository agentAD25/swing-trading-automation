"""Synthetic instruction-receipt tests. No database, broker, or mailbox access."""

from __future__ import annotations

import logging
import threading
import traceback
from dataclasses import asdict, fields
from enum import Enum

import pytest

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
    InMemoryReceiptStore,
    InstructionReceipt,
    ReceiptEvidenceRejected,
    ReceiptKind,
    ReceiptStoreUnavailable,
    admit_instruction_receipt,
)

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
ALLOWED_FIELDS = {
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
}


def _instruction(digest: str, index: int = 0) -> CanonicalInstructionEnvelope:
    return CanonicalInstructionEnvelope(
        instruction_id=f"v1:email_instruction:{digest}:{index}",
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
    message_type: MessageType = MessageType.UNKNOWN,
    reasons: tuple[str, ...] = (ReasonCode.MISSING_SIZING.value,),
    instructions: tuple[CanonicalInstructionEnvelope, ...] = (),
    evidence: tuple[FieldEvidence, ...] = (
        FieldEvidence("price", "PRICE_51.0000"),
        FieldEvidence("account", "ACCT-9"),
    ),
    source_timestamp: str | None = "2024-01-01T00:00:00Z",
    provider_message_ref: str | None | object = ...,
    raw_sha256: str | None = None,
) -> ParseOutcome:
    if disposition is Disposition.ACCEPT and not instructions:
        instructions = (_instruction(digest),)
        message_type = MessageType.NEW_TRADE
        reasons = ()
    ref = message_id if provider_message_ref is ... else provider_message_ref
    return ParseOutcome(
        disposition=disposition,
        message_type=message_type,
        reasons=reasons,
        instructions=instructions,
        evidence=evidence,
        content_digest=digest,
        message_id=message_id,
        provenance=ParseProvenance(
            retention_policy=EMAIL_RETENTION_POLICY,
            provider_type=ProviderType.FIXTURE.value,
            provider_message_ref=ref,  # type: ignore[arg-type]
            raw_sha256=digest if raw_sha256 is None else raw_sha256,
            parser_version=PARSER_VERSION,
            schema_version=SCHEMA_VERSION,
            source_timestamp=source_timestamp,
        ),
    )


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Enum):
        return [value.value]
    if isinstance(value, dict):
        found: list[str] = []
        for item in value.values():
            found.extend(_strings(item))
        return found
    if isinstance(value, tuple):
        found = []
        for item in value:
            found.extend(_strings(item))
        return found
    return []


def test_new_valid_receipt_keeps_only_allowlisted_fields() -> None:
    store = InMemoryReceiptStore()
    decision = admit_instruction_receipt(_outcome(), store)

    assert decision.kind is ReceiptKind.NEW
    assert decision.conflict_reason is None
    assert decision.receipt.receipt_key == MESSAGE_ID
    assert decision.receipt.content_digest == DIGEST_A
    assert decision.receipt.disposition is Disposition.QUARANTINE
    assert decision.receipt.provider_type == "FIXTURE"
    assert {field.name for field in fields(decision.receipt)} == ALLOWED_FIELDS
    rendered = " ".join(_strings(asdict(decision.receipt)))
    for token in PROHIBITED:
        assert token not in rendered
    assert len(store) == 1


def test_same_key_and_digest_replays_the_original_object() -> None:
    store = InMemoryReceiptStore()
    first = admit_instruction_receipt(_outcome(), store)
    second = admit_instruction_receipt(_outcome(), store)

    assert second.kind is ReceiptKind.REPLAY
    assert second.receipt is first.receipt
    assert second.receipt.disposition is Disposition.QUARANTINE
    assert "DUPLICATE" not in second.receipt.reasons
    assert len(store) == 1


def test_same_key_and_different_digest_conflicts_without_replacement() -> None:
    store = InMemoryReceiptStore()
    original = admit_instruction_receipt(
        _outcome(disposition=Disposition.ACCEPT),
        store,
    )
    conflict = admit_instruction_receipt(
        _outcome(digest=DIGEST_B, disposition=Disposition.QUARANTINE),
        store,
    )

    assert conflict.kind is ReceiptKind.CONFLICT
    assert conflict.conflict_reason == ReasonCode.CONFLICTING_DUPLICATE.value
    assert conflict.receipt is original.receipt
    assert conflict.receipt.disposition is Disposition.ACCEPT
    assert conflict.receipt.content_digest == DIGEST_A
    assert ReasonCode.CONFLICTING_DUPLICATE.value not in conflict.receipt.reasons
    assert len(store) == 1


def test_replay_after_conflict_preserves_the_original_disposition() -> None:
    store = InMemoryReceiptStore()
    original = admit_instruction_receipt(
        _outcome(disposition=Disposition.ACCEPT),
        store,
    )
    admit_instruction_receipt(_outcome(digest=DIGEST_B), store)
    replay = admit_instruction_receipt(
        _outcome(disposition=Disposition.ACCEPT),
        store,
    )

    assert replay.kind is ReceiptKind.REPLAY
    assert replay.receipt is original.receipt
    assert replay.receipt.disposition is Disposition.ACCEPT
    assert replay.receipt.message_type is MessageType.NEW_TRADE


def test_validated_message_id_is_the_receipt_key() -> None:
    decision = admit_instruction_receipt(_outcome(), InMemoryReceiptStore())

    assert decision.receipt.receipt_key == MESSAGE_ID
    assert decision.receipt.receipt_key != decision.receipt.content_digest
    assert decision.receipt.message_id == MESSAGE_ID


def test_missing_message_id_uses_the_digest_key() -> None:
    decision = admit_instruction_receipt(
        _outcome(message_id=None, reasons=(ReasonCode.MISSING_MESSAGE_ID.value,)),
        InMemoryReceiptStore(),
    )

    assert decision.kind is ReceiptKind.NEW
    assert decision.receipt.message_id is None
    assert decision.receipt.receipt_key == DIGEST_A
    assert decision.receipt.provider_message_ref is None


def test_malformed_message_id_does_not_fall_back_to_the_digest() -> None:
    store = InMemoryReceiptStore()
    with pytest.raises(ReceiptEvidenceRejected, match="^RECEIPT_EVIDENCE_INVALID$"):
        admit_instruction_receipt(_outcome(message_id="<user@gmail.com>"), store)
    assert len(store) == 0


def test_invalid_content_digest_is_rejected() -> None:
    store = InMemoryReceiptStore()
    with pytest.raises(ReceiptEvidenceRejected, match="^RECEIPT_EVIDENCE_INVALID$"):
        admit_instruction_receipt(
            _outcome(digest=DIGEST_A.upper(), raw_sha256=DIGEST_A.upper()),
            store,
        )
    assert len(store) == 0


def test_missing_or_malformed_outcome_is_rejected() -> None:
    store = InMemoryReceiptStore()
    with pytest.raises(ReceiptEvidenceRejected, match="^RECEIPT_EVIDENCE_INVALID$"):
        admit_instruction_receipt(object(), store)  # type: ignore[arg-type]
    with pytest.raises(ReceiptEvidenceRejected, match="^RECEIPT_EVIDENCE_INVALID$"):
        admit_instruction_receipt(
            _outcome(provider_message_ref="other-ref"),
            store,
        )
    assert len(store) == 0


def test_injected_storage_failure_is_sanitized_and_not_retried(
    caplog: pytest.LogCaptureFixture,
) -> None:
    calls = 0

    class Boom:
        def compare_and_insert(
            self, key: str, receipt: InstructionReceipt
        ) -> InstructionReceipt | None:
            nonlocal calls
            calls += 1
            raise RuntimeError(
                "connection failed: postgresql://synth:"
                f"{SECRET}@synthetic-db-host.invalid:5432/synthdb"
            )

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(ReceiptStoreUnavailable) as caught:
            admit_instruction_receipt(_outcome(), Boom())

    rendered = "".join(traceback.format_exception(caught.value))
    assert caught.value.args == ("RECEIPT_STORE_UNAVAILABLE",)
    assert SECRET not in str(caught.value)
    assert SECRET not in repr(caught.value)
    assert SECRET not in rendered
    assert SECRET not in caplog.text
    assert calls == 1


def test_concurrent_same_digest_returns_one_original() -> None:
    store = InMemoryReceiptStore()
    barrier = threading.Barrier(4)
    decisions: list[object] = []
    guard = threading.Lock()

    def worker() -> None:
        barrier.wait()
        decision = admit_instruction_receipt(_outcome(), store)
        with guard:
            decisions.append(decision)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert {item.kind for item in decisions} == {ReceiptKind.NEW, ReceiptKind.REPLAY}  # type: ignore[attr-defined]
    assert len(store) == 1
    assert len({id(item.receipt) for item in decisions}) == 1  # type: ignore[attr-defined]


def test_concurrent_conflicting_digest_cannot_replace_the_first_receipt() -> None:
    store = InMemoryReceiptStore()
    barrier = threading.Barrier(2)
    decisions: list[object] = []
    guard = threading.Lock()

    def worker(digest: str, disposition: Disposition) -> None:
        barrier.wait()
        decision = admit_instruction_receipt(
            _outcome(digest=digest, disposition=disposition),
            store,
        )
        with guard:
            decisions.append(decision)

    threads = [
        threading.Thread(target=worker, args=(DIGEST_A, Disposition.ACCEPT)),
        threading.Thread(target=worker, args=(DIGEST_B, Disposition.QUARANTINE)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    kinds = {item.kind for item in decisions}  # type: ignore[attr-defined]
    assert kinds == {ReceiptKind.NEW, ReceiptKind.CONFLICT}
    assert len(store) == 1
    winner = next(item for item in decisions if item.kind is ReceiptKind.NEW)  # type: ignore[attr-defined]
    loser = next(item for item in decisions if item.kind is ReceiptKind.CONFLICT)  # type: ignore[attr-defined]
    assert loser.receipt is winner.receipt
    assert loser.conflict_reason == ReasonCode.CONFLICTING_DUPLICATE.value
    assert winner.receipt.disposition in {Disposition.ACCEPT, Disposition.QUARANTINE}


def test_receipt_does_not_construct_an_order_or_import_a_broker() -> None:
    import inspect

    import swingtrade.instruction_receipt as receipt

    source = inspect.getsource(receipt)
    for name in ("OrderIntent", "authorize_dispatch", "DryRunAdapter", "psycopg", "create_engine"):
        assert name not in source
    decision = admit_instruction_receipt(
        _outcome(disposition=Disposition.ACCEPT), InMemoryReceiptStore()
    )
    assert type(decision.receipt) is InstructionReceipt
    assert "v1:email_instruction:" in decision.receipt.instruction_ids[0]
    assert "EXAMPLE_QUANTITY_77" not in decision.receipt.instruction_ids[0]
