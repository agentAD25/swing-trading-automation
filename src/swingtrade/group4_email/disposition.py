"""Pure non-economic view of an existing parse outcome.

The view does not replace ``Disposition``. It does not construct an order,
read a mailbox, or change retention. ``DUPLICATE`` is named because item 18
reserves it for an explicit replay view. No accepted contract supplies replay
context on ``ParseOutcome``, and this function does not invent one, so it
never returns that label.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, NoReturn

from swingtrade.group4_email.contract import (
    Disposition,
    MessageType,
    ParseOutcome,
    ParseProvenance,
    ReasonCode,
)
from swingtrade.group4_email.synthetic_acquisition import SyntheticAcquisitionError
from swingtrade.instruction_receipt import (
    ReceiptEvidenceRejected,
    ReceiptKind,
    ReceiptStoreUnavailable,
)

if TYPE_CHECKING:
    from swingtrade.group4_email.synthetic_ingestion import SyntheticIngestionRecord

_DEFERRED_REASONS = frozenset(
    {
        ReasonCode.PARSER_DEFERRED.value,
        ReasonCode.CANCEL_FORMAT_UNSPECIFIED.value,
    }
)


class DispositionViewLabel(StrEnum):
    """Local view labels. These are not parser dispositions or order states."""

    RECORDED_NOT_EXECUTABLE = "RECORDED_NOT_EXECUTABLE"
    DEFERRED = "DEFERRED"
    QUARANTINED = "QUARANTINED"
    DUPLICATE = "DUPLICATE"
    REJECT = "REJECT"
    INFORMATIONAL = "INFORMATIONAL"


class DispositionViewError(Exception):
    """Fail-closed view error. The message is a stable code and nothing else."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or code == "":
            code = "fail_closed"
        super().__init__(code)
        self.code = code

    def __repr__(self) -> str:
        return f"DispositionViewError({self.code!r})"

    def __str__(self) -> str:
        return self.code


@dataclass(frozen=True)
class DispositionView:
    """Immutable reading of one outcome. It holds no order and no message body."""

    label: DispositionViewLabel
    disposition: Disposition
    message_type: MessageType
    reasons: tuple[str, ...]
    instruction_ids: tuple[str, ...]
    content_digest: str
    message_id: str | None
    provenance: ParseProvenance

    def __post_init__(self) -> None:
        if self.label is DispositionViewLabel.DUPLICATE:
            raise DispositionViewError("duplicate_unavailable")


def derive_disposition_view(outcome: ParseOutcome) -> DispositionView:
    """Derive one view. The outcome object is not modified."""

    if type(outcome) is not ParseOutcome:
        _fail("invalid_outcome")
    if outcome.network_permitted is not False:
        _fail("invariant_violation")
    disposition = outcome.disposition
    message_type = outcome.message_type
    if type(disposition) is not Disposition:
        _fail("invalid_disposition")
    if type(message_type) is not MessageType:
        _fail("invalid_message_type")
    if disposition is not Disposition.ACCEPT and outcome.instructions:
        _fail("invariant_violation")
    instruction_ids = _instruction_ids(outcome)
    label = _label(disposition, message_type, outcome.reasons, instruction_ids)
    return DispositionView(
        label=label,
        disposition=disposition,
        message_type=message_type,
        reasons=tuple(outcome.reasons),
        instruction_ids=instruction_ids,
        content_digest=outcome.content_digest,
        message_id=outcome.message_id,
        provenance=outcome.provenance,
    )


def _label(
    disposition: Disposition,
    message_type: MessageType,
    reasons: tuple[str, ...],
    instruction_ids: tuple[str, ...],
) -> DispositionViewLabel:
    if disposition is Disposition.REJECT:
        return DispositionViewLabel.REJECT
    if disposition is Disposition.QUARANTINE:
        if reasons and set(reasons) <= _DEFERRED_REASONS:
            return DispositionViewLabel.DEFERRED
        return DispositionViewLabel.QUARANTINED
    if disposition is Disposition.ACCEPT and message_type is MessageType.NEW_TRADE:
        if not instruction_ids:
            _fail("missing_envelope")
        return DispositionViewLabel.RECORDED_NOT_EXECUTABLE
    if disposition is Disposition.ACCEPT and message_type is MessageType.INFORMATIONAL:
        if instruction_ids:
            _fail("unexpected_envelope")
        return DispositionViewLabel.INFORMATIONAL
    _fail("unsupported_combination")


def _instruction_ids(outcome: ParseOutcome) -> tuple[str, ...]:
    identifiers: list[str] = []
    for instruction in outcome.instructions:
        identifier = instruction.instruction_id
        if type(identifier) is not str or identifier == "":
            _fail("invariant_violation")
        identifiers.append(identifier)
    return tuple(identifiers)


def _fail(code: str) -> NoReturn:
    raise DispositionViewError(code)


class RecoveryDecision(StrEnum):
    """In-memory recovery label. It is not an order and not a durable commit."""

    TERMINAL_REJECT = "TERMINAL_REJECT"
    QUARANTINE = "QUARANTINE"
    REPLAY_OBSERVED = "REPLAY_OBSERVED"
    CONFLICT_REVIEW = "CONFLICT_REVIEW"
    DEFERRED_REVIEW = "DEFERRED_REVIEW"
    OPERATOR_HALT = "OPERATOR_HALT"
    PROCESSED_SYNTHETIC = "PROCESSED_SYNTHETIC"


_REASON_VALUES = frozenset(code.value for code in ReasonCode)
_VIEW_FAILURES = frozenset(
    {
        "duplicate_unavailable",
        "invalid_outcome",
        "invariant_violation",
        "invalid_disposition",
        "invalid_message_type",
        "missing_envelope",
        "unexpected_envelope",
        "unsupported_combination",
        "fail_closed",
    }
)
_ACQUISITION_CODES = frozenset(
    {"INVALID_FIXTURE", "INVALID_DELIVERY_REF", "DUPLICATE_DELIVERY_REF"}
)
_PROCESSED_VIEWS = frozenset(
    {
        DispositionViewLabel.RECORDED_NOT_EXECUTABLE,
        DispositionViewLabel.INFORMATIONAL,
    }
)
_REVIEW_DECISIONS = frozenset(
    {
        RecoveryDecision.QUARANTINE,
        RecoveryDecision.CONFLICT_REVIEW,
        RecoveryDecision.DEFERRED_REVIEW,
        RecoveryDecision.OPERATOR_HALT,
    }
)
_DURABLE_UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class OfflineRecoveryEvidence:
    """Sanitized offline recovery reading. It carries no message body."""

    stage: str
    processing_result: str
    recovery: RecoveryDecision
    operator_review: bool
    reason: str
    durable_state: str
    economic_dispatch: bool
    delivery_ref: str | None = None
    content_digest: str | None = None
    parser_disposition: str | None = None
    view_label: str | None = None
    receipt_kind: str | None = None

    def __post_init__(self) -> None:
        if self.durable_state != _DURABLE_UNAVAILABLE or self.economic_dispatch is not False:
            raise DispositionViewError("invariant_violation")
        if type(self.recovery) is not RecoveryDecision or type(self.operator_review) is not bool:
            raise DispositionViewError("invariant_violation")
        if self.recovery in _REVIEW_DECISIONS and self.operator_review is not True:
            raise DispositionViewError("invariant_violation")
        if self.recovery not in _REVIEW_DECISIONS and self.operator_review is not False:
            raise DispositionViewError("invariant_violation")
        if self.recovery is RecoveryDecision.PROCESSED_SYNTHETIC and self.reason not in {
            DispositionViewLabel.RECORDED_NOT_EXECUTABLE.value,
            DispositionViewLabel.INFORMATIONAL.value,
        }:
            raise DispositionViewError("invariant_violation")


def classify_synthetic_record(record: object) -> OfflineRecoveryEvidence:
    """Map one completed in-memory record to a fail-closed recovery decision."""

    from swingtrade.group4_email.synthetic_ingestion import SyntheticIngestionRecord

    if type(record) is not SyntheticIngestionRecord:
        return _halt("UNKNOWN_PROCESSING_RESULT")
    if (
        type(record.receipt_kind) is not ReceiptKind
        or type(record.view_label) is not DispositionViewLabel
        or type(record.parser_disposition) is not Disposition
        or type(record.parser_reasons) is not tuple
    ):
        return _halt("UNKNOWN_PROCESSING_RESULT", record)
    if record.receipt_kind is ReceiptKind.CONFLICT:
        reason = record.conflict_reason
        if reason != ReasonCode.CONFLICTING_DUPLICATE.value:
            return _halt("UNKNOWN_PROCESSING_RESULT", record)
        return _from_record(record, RecoveryDecision.CONFLICT_REVIEW, reason, "receipt")
    if record.receipt_kind is ReceiptKind.REPLAY:
        if record.conflict_reason is not None:
            return _halt("UNKNOWN_PROCESSING_RESULT", record)
        return _from_record(record, RecoveryDecision.REPLAY_OBSERVED, "REPLAY", "receipt")
    if record.receipt_kind is not ReceiptKind.NEW or record.conflict_reason is not None:
        return _halt("UNKNOWN_PROCESSING_RESULT", record)
    reason = _primary_reason(record)
    if reason is None:
        return _halt("UNKNOWN_PROCESSING_RESULT", record)
    if record.view_label is DispositionViewLabel.REJECT:
        if record.parser_disposition is not Disposition.REJECT:
            return _halt("UNKNOWN_PROCESSING_RESULT", record)
        return _from_record(record, RecoveryDecision.TERMINAL_REJECT, reason, "parse")
    if record.view_label is DispositionViewLabel.DEFERRED:
        return _from_record(record, RecoveryDecision.DEFERRED_REVIEW, reason, "disposition")
    if record.view_label is DispositionViewLabel.QUARANTINED:
        return _from_record(record, RecoveryDecision.QUARANTINE, reason, "disposition")
    if record.view_label in _PROCESSED_VIEWS:
        if record.parser_disposition is not Disposition.ACCEPT or record.parser_reasons != ():
            return _halt("UNKNOWN_PROCESSING_RESULT", record)
        return _from_record(
            record,
            RecoveryDecision.PROCESSED_SYNTHETIC,
            record.view_label.value,
            "receipt",
        )
    return _halt("UNKNOWN_PROCESSING_RESULT", record)


def classify_ingestion_stop(error: object) -> OfflineRecoveryEvidence:
    """Classify a stop. Unknown exceptions do not become success or leak text."""

    from swingtrade.group4_email.synthetic_ingestion import SyntheticIngestionRejected

    if type(error) is SyntheticAcquisitionError and error.code in _ACQUISITION_CODES:
        return _stop("acquisition", RecoveryDecision.TERMINAL_REJECT, error.code)
    if type(error) is ReceiptStoreUnavailable:
        return _stop("receipt", RecoveryDecision.OPERATOR_HALT, "RECEIPT_STORE_UNAVAILABLE")
    if type(error) is ReceiptEvidenceRejected:
        return _stop("receipt", RecoveryDecision.OPERATOR_HALT, "RECEIPT_EVIDENCE_INVALID")
    if type(error) is SyntheticIngestionRejected and error.code == "INGESTION_INVALID":
        return _stop("recovery", RecoveryDecision.OPERATOR_HALT, "INGESTION_INVALID")
    if type(error) is DispositionViewError and error.code in _VIEW_FAILURES:
        return _stop("disposition", RecoveryDecision.OPERATOR_HALT, error.code.upper())
    return _stop("recovery", RecoveryDecision.OPERATOR_HALT, "UNKNOWN_PROCESSING_RESULT")


def _primary_reason(record: SyntheticIngestionRecord) -> str | None:
    if record.view_label in _PROCESSED_VIEWS:
        return record.view_label.value
    if not record.parser_reasons:
        if record.view_label is DispositionViewLabel.REJECT:
            return record.view_label.value
        return None
    reason = record.parser_reasons[0]
    if reason not in _REASON_VALUES:
        return None
    return reason


def _from_record(
    record: SyntheticIngestionRecord,
    recovery: RecoveryDecision,
    reason: str,
    stage: str,
) -> OfflineRecoveryEvidence:
    return OfflineRecoveryEvidence(
        stage=stage,
        processing_result=f"{record.view_label.value}:{record.receipt_kind.value}",
        recovery=recovery,
        operator_review=recovery in _REVIEW_DECISIONS,
        reason=reason,
        durable_state=_DURABLE_UNAVAILABLE,
        economic_dispatch=False,
        delivery_ref=record.delivery_ref,
        content_digest=record.content_digest,
        parser_disposition=record.parser_disposition.value,
        view_label=record.view_label.value,
        receipt_kind=record.receipt_kind.value,
    )


def _halt(
    reason: str,
    record: SyntheticIngestionRecord | None = None,
) -> OfflineRecoveryEvidence:
    return OfflineRecoveryEvidence(
        stage="recovery",
        processing_result="STOPPED",
        recovery=RecoveryDecision.OPERATOR_HALT,
        operator_review=True,
        reason=reason,
        durable_state=_DURABLE_UNAVAILABLE,
        economic_dispatch=False,
        delivery_ref=None if record is None else record.delivery_ref,
        content_digest=None if record is None else record.content_digest,
        parser_disposition=None if record is None else record.parser_disposition.value,
        view_label=None if record is None else record.view_label.value,
        receipt_kind=None if record is None else record.receipt_kind.value,
    )


def _stop(stage: str, recovery: RecoveryDecision, reason: str) -> OfflineRecoveryEvidence:
    return OfflineRecoveryEvidence(
        stage=stage,
        processing_result="STOPPED",
        recovery=recovery,
        operator_review=recovery in _REVIEW_DECISIONS,
        reason=reason,
        durable_state=_DURABLE_UNAVAILABLE,
        economic_dispatch=False,
    )
