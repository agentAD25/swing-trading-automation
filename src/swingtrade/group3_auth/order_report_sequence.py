"""Evaluate a sequence of synthetic broker-report evidence. No order action.

The input is a project-defined list of synthetic reports. It is not a
TradeStation wire schema. Labels describe evidence quality only. They do not
choose a broker order state, a quantity, or permission to submit, cancel,
retry, or resubmit.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from enum import StrEnum
from typing import NamedTuple

from swingtrade.group3_auth.order_report import ReportEvidence, classify_report

_ALLOW = frozenset({"facts", "order_id", "sequence"})
_MALFORMED = frozenset(
    {
        "MALFORMED_REPORT",
        "UNDOCUMENTED_FIELD",
        "MALFORMED_IDENTITY",
        "MALFORMED_SEQUENCE",
    }
)
_CONFLICT = frozenset(
    {
        "CONFLICTING_IDENTITY",
        "CONTRADICTORY_EVIDENCE",
        "INCONSISTENT_EVIDENCE",
        "SAME_SEQUENCE_UNEQUAL_BODY",
    }
)
_MISSING = frozenset(
    {
        "NO_REPORTS",
        "MISSING_ORDER_ID",
        "MISSING_EVIDENCE",
        "INSUFFICIENT_EVIDENCE",
        "CANCEL_UNCONFIRMED",
        "SEQUENCE_GAP",
    }
)
_FACT_DEFECTS = frozenset(
    {
        "MISSING_EVIDENCE",
        "INSUFFICIENT_EVIDENCE",
        "CANCEL_UNCONFIRMED",
        "UNSUPPORTED_EVIDENCE",
        "CONTRADICTORY_EVIDENCE",
    }
)
_REASON_ORDER = (
    "MALFORMED_REPORT",
    "UNDOCUMENTED_FIELD",
    "MALFORMED_IDENTITY",
    "MALFORMED_SEQUENCE",
    "PARTIAL_SEQUENCE",
    "CONFLICTING_IDENTITY",
    "CONTRADICTORY_EVIDENCE",
    "INCONSISTENT_EVIDENCE",
    "SAME_SEQUENCE_UNEQUAL_BODY",
    "DUPLICATE",
    "OUT_OF_ORDER",
    "NO_REPORTS",
    "MISSING_ORDER_ID",
    "MISSING_EVIDENCE",
    "INSUFFICIENT_EVIDENCE",
    "CANCEL_UNCONFIRMED",
    "UNSUPPORTED_EVIDENCE",
    "SEQUENCE_GAP",
)


class SequenceLabel(StrEnum):
    """Evidence-quality label. This is not OutcomeCode and not ReportLabel."""

    CONSISTENT = "CONSISTENT"
    DUPLICATE = "DUPLICATE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    CONFLICT = "CONFLICT"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


class SequenceEvidence:
    """One sequence classification. Network and economic actions stay closed."""

    __slots__ = ("classification", "order_id", "reasons")

    def __init__(
        self,
        classification: SequenceLabel,
        order_id: str | None,
        reasons: tuple[str, ...],
    ) -> None:
        self.classification = classification
        self.order_id = order_id
        self.reasons = reasons

    @property
    def safe_to_retry(self) -> bool:
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
    def network_permitted(self) -> bool:
        return False

    @property
    def connect_allowed(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SequenceEvidence):
            return NotImplemented
        return (self.classification, self.order_id, self.reasons) == (
            other.classification,
            other.order_id,
            other.reasons,
        )

    def __repr__(self) -> str:
        shown = ", ".join((self.classification.value, *self.reasons))
        return f"SequenceEvidence({shown})"


class _Parsed(NamedTuple):
    identity: tuple[object, ...]
    fact_key: tuple[tuple[str, int], ...]
    evidence_reason: str
    sequence: int | None
    has_sequence: bool
    order_id: str | None


def evaluate_report_sequence(reports: object) -> SequenceEvidence:
    """Classify synthetic evidence quality. The input list is not modified."""
    if type(reports) is not list:
        return _evidence(SequenceLabel.UNKNOWN, None, ("MALFORMED_REPORT",))
    malformed: set[str] = set()
    parsed_items: list[_Parsed] = []
    for item in reports:
        defects, parsed = _inspect(item)
        malformed.update(defects)
        if not malformed and parsed is not None:
            parsed_items.append(parsed)
    if malformed:
        return _evidence(SequenceLabel.UNKNOWN, None, _reasons(malformed))
    parsed_tuple = tuple(parsed_items)
    reasons = _reasons(_defects(parsed_tuple))
    return _evidence(_primary(reasons, parsed_tuple), _shared_order_id(parsed_tuple), reasons)


def _evidence(
    classification: SequenceLabel,
    order_id: str | None,
    reasons: tuple[str, ...],
) -> SequenceEvidence:
    return SequenceEvidence(classification, order_id, reasons)


def _inspect(item: object) -> tuple[set[str], _Parsed | None]:
    if type(item) is not dict:
        return {"MALFORMED_REPORT"}, None
    found: set[str] = set()
    if not set(item).issubset(_ALLOW):
        found.add("UNDOCUMENTED_FIELD")
    if "sequence" in item and not _sequence_ok(item["sequence"]):
        found.add("MALFORMED_SEQUENCE")
    evidence = classify_report(_classifier_payload(item))
    if evidence.reason in {"MALFORMED_REPORT", "MALFORMED_IDENTITY"}:
        found.add(evidence.reason)
    if found:
        return found, None
    return set(), _parsed(item, evidence)


def _parsed(item: Mapping[str, object], evidence: ReportEvidence) -> _Parsed:
    has_sequence = "sequence" in item
    sequence = _sequence_value(item)
    fact_key = _fact_key(item.get("facts"))
    marker: tuple[object, ...] = ("present", sequence) if has_sequence else ("absent",)
    if evidence.reason == "CONFLICTING_IDENTITY":
        identity: tuple[object, ...] = (
            "conflicting",
            _conflict_ids(item.get("order_id")),
            fact_key,
            marker,
        )
        order_id = None
    elif evidence.order_id is None:
        identity = ("absent", fact_key, marker)
        order_id = None
    else:
        identity = ("id", evidence.order_id, fact_key, marker)
        order_id = evidence.order_id
    return _Parsed(identity, fact_key, evidence.reason, sequence, has_sequence, order_id)


def _defects(parsed: tuple[_Parsed, ...]) -> set[str]:
    found: set[str] = set()
    if not parsed:
        found.add("NO_REPORTS")
        return found
    if any(item.has_sequence for item in parsed) and not all(item.has_sequence for item in parsed):
        found.add("PARTIAL_SEQUENCE")
    if any(item.evidence_reason == "CONFLICTING_IDENTITY" for item in parsed):
        found.add("CONFLICTING_IDENTITY")
    validated = {item.order_id for item in parsed if item.order_id is not None}
    if len(validated) > 1:
        found.add("CONFLICTING_IDENTITY")
    if any(item.evidence_reason == "CONTRADICTORY_EVIDENCE" for item in parsed):
        found.add("CONTRADICTORY_EVIDENCE")
    by_identity: dict[str, set[tuple[tuple[str, int], ...]]] = {}
    for item in parsed:
        if item.order_id is None:
            continue
        by_identity.setdefault(item.order_id, set()).add(item.fact_key)
    if any(len(keys) > 1 for keys in by_identity.values()):
        found.add("INCONSISTENT_EVIDENCE")
    by_sequence: dict[int, set[tuple[object, ...]]] = {}
    for item in parsed:
        if not item.has_sequence or item.sequence is None:
            continue
        by_sequence.setdefault(item.sequence, set()).add(item.identity[:-1])
    if any(len(bodies) > 1 for bodies in by_sequence.values()):
        found.add("SAME_SEQUENCE_UNEQUAL_BODY")
    counts = Counter(item.identity for item in parsed)
    if any(count >= 2 for count in counts.values()):
        found.add("DUPLICATE")
    if all(item.has_sequence for item in parsed):
        numbers = [item.sequence for item in parsed if item.sequence is not None]
        if len(numbers) == len(parsed) and any(
            numbers[index] >= numbers[index + 1] for index in range(len(numbers) - 1)
        ):
            found.add("OUT_OF_ORDER")
        elif len(numbers) == len(parsed) and any(
            numbers[index + 1] - numbers[index] != 1 for index in range(len(numbers) - 1)
        ):
            found.add("SEQUENCE_GAP")
    if any(
        item.order_id is None and item.evidence_reason != "CONFLICTING_IDENTITY" for item in parsed
    ):
        found.add("MISSING_ORDER_ID")
    for item in parsed:
        if item.evidence_reason in _FACT_DEFECTS:
            found.add(item.evidence_reason)
    return found


def _primary(reasons: tuple[str, ...], parsed: tuple[_Parsed, ...]) -> SequenceLabel:
    found = set(reasons)
    if found & _MALFORMED or "PARTIAL_SEQUENCE" in found:
        return SequenceLabel.UNKNOWN
    if found & _CONFLICT:
        return SequenceLabel.CONFLICT
    if "DUPLICATE" in found:
        return SequenceLabel.DUPLICATE
    if "OUT_OF_ORDER" in found:
        return SequenceLabel.OUT_OF_ORDER
    if found & _MISSING:
        return SequenceLabel.MISSING
    if "UNSUPPORTED_EVIDENCE" in found or not _consistent(parsed):
        return SequenceLabel.UNKNOWN
    return SequenceLabel.CONSISTENT


def _consistent(parsed: tuple[_Parsed, ...]) -> bool:
    if not parsed:
        return False
    order_ids = [item.order_id for item in parsed]
    if any(order_id is None for order_id in order_ids) or len(set(order_ids)) != 1:
        return False
    if any(item.evidence_reason != "CLASSIFIED" for item in parsed):
        return False
    if len({item.fact_key for item in parsed}) != 1:
        return False
    if not any(item.has_sequence for item in parsed):
        return len(parsed) == 1
    if not all(item.has_sequence and item.sequence is not None for item in parsed):
        return False
    numbers = [item.sequence for item in parsed if item.sequence is not None]
    return all(numbers[index] + 1 == numbers[index + 1] for index in range(len(numbers) - 1))


def _shared_order_id(parsed: tuple[_Parsed, ...]) -> str | None:
    order_ids = [item.order_id for item in parsed]
    if not order_ids or any(order_id is None for order_id in order_ids):
        return None
    if len(set(order_ids)) != 1:
        return None
    return order_ids[0]


def _classifier_payload(item: Mapping[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {}
    if "facts" in item:
        payload["facts"] = item["facts"]
    if "order_id" in item:
        payload["order_id"] = item["order_id"]
    return payload


def _sequence_ok(value: object) -> bool:
    return type(value) is int and value >= 0


def _sequence_value(item: Mapping[str, object]) -> int | None:
    if "sequence" not in item:
        return None
    value = item["sequence"]
    if type(value) is int and value >= 0:
        return value
    return None


def _fact_key(raw: object) -> tuple[tuple[str, int], ...]:
    if type(raw) is not list:
        return ()
    facts: list[str] = []
    for fact in raw:
        if type(fact) is not str:
            return ()
        facts.append(fact)
    return tuple(sorted(Counter(facts).items()))


def _conflict_ids(raw: object) -> tuple[str, ...]:
    if type(raw) is not list:
        return ()
    identifiers: list[str] = []
    for item in raw:
        if type(item) is not str:
            return ()
        identifiers.append(item)
    return tuple(sorted(identifiers))


def _reasons(found: set[str]) -> tuple[str, ...]:
    return tuple(code for code in _REASON_ORDER if code in found)
