"""Classify one in-memory synthetic broker report. No request and no order action.

The input is a controlled fixture, not a TradeStation wire response and not an
official order schema. The label is report evidence. It is not an instruction
to submit, modify, cancel, retry, or resubmit an order.
"""

from __future__ import annotations

from enum import StrEnum

_ALLOWED = frozenset({"facts", "order_id"})
_SUPPORTED = {
    "ACKNOWLEDGED": "ACKNOWLEDGMENT",
    "PARTIALLY_FILLED": "PARTIAL_FILL",
    "FILLED": "FILL",
    "REJECTED": "REJECTION",
    "CANCELED": "CANCELLATION",
}
_INSUFFICIENT = {
    "ORDER_ID_ASSIGNED": "INSUFFICIENT_EVIDENCE",
    "CANCEL_REQUESTED": "CANCEL_UNCONFIRMED",
    "PENDING_CANCEL": "CANCEL_UNCONFIRMED",
}


class ReportLabel(StrEnum):
    """Local evidence label. This is not OutcomeCode and not an order command."""

    ACKNOWLEDGMENT = "ACKNOWLEDGMENT"
    PARTIAL_FILL = "PARTIAL_FILL"
    FILL = "FILL"
    REJECTION = "REJECTION"
    CANCELLATION = "CANCELLATION"
    UNKNOWN = "UNKNOWN"


class ReportEvidence:
    """One classification. Retry, network, and economic actions stay closed."""

    __slots__ = ("label", "order_id", "reason")

    def __init__(self, label: ReportLabel, order_id: str | None, reason: str) -> None:
        self.label = label
        self.order_id = order_id
        self.reason = reason

    @property
    def safe_to_retry(self) -> bool:
        return False

    @property
    def network_permitted(self) -> bool:
        return False

    @property
    def resubmit_permitted(self) -> bool:
        return False

    @property
    def submit_permitted(self) -> bool:
        return False

    @property
    def cancel_permitted(self) -> bool:
        return False

    @property
    def connect_allowed(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ReportEvidence):
            return NotImplemented
        return (self.label, self.order_id, self.reason) == (
            other.label,
            other.order_id,
            other.reason,
        )

    def __repr__(self) -> str:
        return f"ReportEvidence({self.label.value}, {self.reason})"


def classify_report(report: object) -> ReportEvidence:
    """Return evidence for one synthetic report. The input is not modified."""
    if type(report) is not dict:
        return _unknown("MALFORMED_REPORT")
    if not set(report).issubset(_ALLOWED):
        return _unknown("UNDOCUMENTED_FIELD")
    order_id, identity_reason = _identity(report)
    label, evidence_reason = _evidence(report)
    if identity_reason is not None:
        return _unknown(identity_reason)
    if evidence_reason is not None or label is None:
        return ReportEvidence(ReportLabel.UNKNOWN, order_id, evidence_reason or "UNKNOWN")
    return ReportEvidence(label, order_id, "CLASSIFIED")


def _unknown(reason: str) -> ReportEvidence:
    return ReportEvidence(ReportLabel.UNKNOWN, None, reason)


def _opaque(value: str) -> bool:
    """Same text bounds as the existing group3 identity check. The value is not rendered."""
    if value == "" or len(value) > 64:
        return False
    return not any(character.isspace() or ord(character) < 32 for character in value)


def _identity(report: dict[str, object]) -> tuple[str | None, str | None]:
    if "order_id" not in report:
        return None, None
    value = report["order_id"]
    if type(value) is str:
        if not _opaque(value):
            return None, "MALFORMED_IDENTITY"
        return value, None
    if type(value) is list:
        if not value or any(type(item) is not str or not _opaque(item) for item in value):
            return None, "MALFORMED_IDENTITY"
        if len(set(value)) != 1:
            return None, "CONFLICTING_IDENTITY"
        return value[0], None
    return None, "MALFORMED_IDENTITY"


def _evidence(report: dict[str, object]) -> tuple[ReportLabel | None, str | None]:
    if "facts" not in report:
        return None, "MISSING_EVIDENCE"
    raw = report["facts"]
    if type(raw) is not list:
        return None, "MALFORMED_REPORT"
    if not raw:
        return None, "MISSING_EVIDENCE"
    if any(type(item) is not str for item in raw):
        return None, "MALFORMED_REPORT"
    labels: set[ReportLabel] = set()
    insufficient: str | None = None
    unsupported = False
    for item in raw:
        mapped = _SUPPORTED.get(item)
        if mapped is not None:
            labels.add(ReportLabel(mapped))
            continue
        weak = _INSUFFICIENT.get(item)
        if weak is not None:
            insufficient = weak
            continue
        unsupported = True
    if len(labels) > 1 or (len(labels) == 1 and (insufficient is not None or unsupported)):
        return None, "CONTRADICTORY_EVIDENCE"
    if len(labels) == 1:
        return next(iter(labels)), None
    if unsupported:
        return None, "UNSUPPORTED_EVIDENCE"
    if insufficient is not None:
        return None, insufficient
    return None, "MISSING_EVIDENCE"
