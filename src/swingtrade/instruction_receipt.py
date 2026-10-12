"""Synthetic, non-economic instruction receipt.

This module projects an accepted ``ParseOutcome`` onto an allowlisted receipt
and admits it through an injected store. The in-memory store is process-local.
It is not PostgreSQL, not durable, and not a broker or mailbox component.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from swingtrade.group4_email.contract import (
    EMAIL_RETENTION_POLICY,
    PARSER_VERSION,
    SCHEMA_VERSION,
    CanonicalInstructionEnvelope,
    Disposition,
    MessageType,
    ParseOutcome,
    ProviderType,
    ReasonCode,
)
from swingtrade.group4_email.normalize import _FIXTURE_MESSAGE_ID, content_digest

_DIGEST_LENGTH = len(content_digest(b""))
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REASON_VALUES = frozenset(code.value for code in ReasonCode)


class ReceiptKind(StrEnum):
    """Admission result. This is not a parser disposition and not an order state."""

    NEW = "NEW"
    REPLAY = "REPLAY"
    CONFLICT = "CONFLICT"


class ReceiptEvidenceRejected(Exception):
    """The outcome cannot be projected onto the receipt allowlist."""

    def __init__(self) -> None:
        super().__init__("RECEIPT_EVIDENCE_INVALID")


class ReceiptStoreUnavailable(Exception):
    """The storage outcome is unknown. The message is a stable code."""

    def __init__(self) -> None:
        super().__init__("RECEIPT_STORE_UNAVAILABLE")


@dataclass(frozen=True)
class InstructionReceipt:
    """Allowlisted receipt. Economic payloads and message bodies are absent."""

    receipt_key: str
    content_digest: str
    disposition: Disposition
    message_type: MessageType
    reasons: tuple[str, ...]
    instruction_ids: tuple[str, ...]
    message_id: str | None
    provider_type: str
    parser_version: str
    schema_version: str
    retention_policy: str
    provider_message_ref: str | None
    source_timestamp: str | None


@dataclass(frozen=True)
class ReceiptDecision:
    """NEW stores one receipt. REPLAY and CONFLICT return that original object."""

    kind: ReceiptKind
    receipt: InstructionReceipt
    conflict_reason: str | None = None


class ReceiptStore(Protocol):
    """Compare-and-insert. Return the existing row, or None when this call inserts."""

    def compare_and_insert(
        self, key: str, receipt: InstructionReceipt
    ) -> InstructionReceipt | None:
        """Insert only when ``key`` is absent. Never replace an existing row."""


class InMemoryReceiptStore:
    """Lock-guarded synthetic map.

    Concurrent first writers for one key leave one original receipt. A later
    same-key conflict cannot replace it. This lock is not evidence of
    PostgreSQL isolation or durability.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rows: dict[str, InstructionReceipt] = {}

    def __len__(self) -> int:
        with self._lock:
            return len(self._rows)

    def compare_and_insert(
        self, key: str, receipt: InstructionReceipt
    ) -> InstructionReceipt | None:
        with self._lock:
            existing = self._rows.get(key)
            if existing is not None:
                return existing
            self._rows[key] = receipt
            return None


def admit_instruction_receipt(outcome: ParseOutcome, store: ReceiptStore) -> ReceiptDecision:
    """Admit one projected receipt. Unknown storage failures stay unavailable."""

    receipt = project_receipt(outcome)
    try:
        existing = store.compare_and_insert(receipt.receipt_key, receipt)
    except Exception:
        raise ReceiptStoreUnavailable() from None
    if existing is None:
        return ReceiptDecision(kind=ReceiptKind.NEW, receipt=receipt)
    if type(existing) is not InstructionReceipt or existing.receipt_key != receipt.receipt_key:
        raise ReceiptStoreUnavailable() from None
    if existing.content_digest == receipt.content_digest:
        return ReceiptDecision(kind=ReceiptKind.REPLAY, receipt=existing)
    return ReceiptDecision(
        kind=ReceiptKind.CONFLICT,
        receipt=existing,
        conflict_reason=ReasonCode.CONFLICTING_DUPLICATE.value,
    )


def project_receipt(outcome: ParseOutcome) -> InstructionReceipt:
    """Copy allowlisted fields. Fail closed when mandatory evidence is unusable."""

    if type(outcome) is not ParseOutcome:
        raise ReceiptEvidenceRejected()
    if (
        type(outcome.disposition) is not Disposition
        or type(outcome.message_type) is not MessageType
    ):
        raise ReceiptEvidenceRejected()
    digest = outcome.content_digest
    if not _is_digest(digest):
        raise ReceiptEvidenceRejected()
    message_id = outcome.message_id
    if message_id is not None and (
        type(message_id) is not str or _FIXTURE_MESSAGE_ID.fullmatch(message_id) is None
    ):
        raise ReceiptEvidenceRejected()
    provenance = outcome.provenance
    if (
        provenance.retention_policy != EMAIL_RETENTION_POLICY
        or provenance.provider_type != ProviderType.FIXTURE.value
        or provenance.provider_message_ref != message_id
        or provenance.raw_sha256 != digest
        or provenance.parser_version != PARSER_VERSION
        or provenance.schema_version != SCHEMA_VERSION
    ):
        raise ReceiptEvidenceRejected()
    timestamp = provenance.source_timestamp
    if timestamp is not None and (
        type(timestamp) is not str or _TIMESTAMP.fullmatch(timestamp) is None
    ):
        raise ReceiptEvidenceRejected()
    if type(outcome.reasons) is not tuple or any(
        type(reason) is not str or reason not in _REASON_VALUES for reason in outcome.reasons
    ):
        raise ReceiptEvidenceRejected()
    if type(outcome.instructions) is not tuple:
        raise ReceiptEvidenceRejected()
    instruction_ids: list[str] = []
    for instruction in outcome.instructions:
        if type(instruction) is not CanonicalInstructionEnvelope:
            raise ReceiptEvidenceRejected()
        identifier = instruction.instruction_id
        if not _instruction_id_ok(identifier, digest, message_id):
            raise ReceiptEvidenceRejected()
        instruction_ids.append(identifier)
    if len(instruction_ids) != len(set(instruction_ids)):
        raise ReceiptEvidenceRejected()
    return InstructionReceipt(
        receipt_key=message_id if message_id is not None else digest,
        content_digest=digest,
        disposition=outcome.disposition,
        message_type=outcome.message_type,
        reasons=outcome.reasons,
        instruction_ids=tuple(instruction_ids),
        message_id=message_id,
        provider_type=ProviderType.FIXTURE.value,
        parser_version=PARSER_VERSION,
        schema_version=SCHEMA_VERSION,
        retention_policy=EMAIL_RETENTION_POLICY,
        provider_message_ref=message_id,
        source_timestamp=timestamp,
    )


def _is_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _DIGEST_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def _instruction_id_ok(identifier: object, digest: str, message_id: str | None) -> bool:
    if type(identifier) is not str:
        return False
    prefix = f"v1:email_instruction:{digest}:"
    if not identifier.startswith(prefix):
        return False
    index = identifier[len(prefix) :]
    if not index.isdecimal() or (index != "0" and index.startswith("0")):
        return False
    return message_id is None or message_id not in identifier
