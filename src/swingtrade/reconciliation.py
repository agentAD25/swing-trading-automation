from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from swingtrade.idempotency import canonical_json

REQUIRED_CHECKS = {"LEDGER_INTEGRITY", "PROJECTION", "EXECUTION"}
_ENVELOPE_FIELDS = {
    "aggregate_id",
    "aggregate_type",
    "aggregate_version",
    "causation_id",
    "correlation_id",
    "effective_at",
    "event_id",
    "event_type",
    "idempotency_key",
    "payload",
    "producer",
    "producer_version",
    "recorded_at",
    "run_id",
    "schema_version",
    "source",
}
_PAYLOAD_FIELDS = {
    "checked_through_event_id",
    "open_critical_discrepancies",
    "open_high_discrepancies",
    "required_checks",
    "result",
}


def _valid_utc_microsecond(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return False
    return True


def _deduplicate(events: Sequence[dict[str, Any]]) -> list[dict[str, Any]] | None:
    unique: list[dict[str, Any]] = []
    by_id: dict[str, bytes] = {}
    for event in events:
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            return None
        encoded = canonical_json(event)
        previous = by_id.get(event_id)
        if previous is not None:
            if previous != encoded:
                return None
            continue
        by_id[event_id] = encoded
        unique.append(event)
    return unique


def _valid_completion(event: dict[str, Any]) -> bool:
    if not _ENVELOPE_FIELDS <= event.keys():
        return False
    payload = event.get("payload")
    if not isinstance(payload, dict) or not _PAYLOAD_FIELDS <= payload.keys():
        return False
    nonempty = (
        event.get("aggregate_id"),
        event.get("causation_id"),
        event.get("correlation_id"),
        event.get("event_id"),
        event.get("producer"),
        event.get("producer_version"),
        event.get("run_id"),
    )
    return (
        all(isinstance(value, str) and value for value in nonempty)
        and event.get("aggregate_type") == "reconciliation"
        and event.get("event_type") == "reconciliation.check_completed.v1"
        and isinstance(event.get("aggregate_version"), int)
        and event["aggregate_version"] > 0
        and isinstance(event.get("schema_version"), int)
        and event["schema_version"] > 0
        and isinstance(event.get("source"), dict)
        and _valid_utc_microsecond(event.get("effective_at"))
        and _valid_utc_microsecond(event.get("recorded_at"))
    )


def derive_reconciliation_result(
    events: Sequence[dict[str, Any]], source_high_water_mark: str, run_id: str
) -> str:
    unique = _deduplicate(events)
    if unique is None:
        return "UNRECONCILED"
    by_id = {event["event_id"]: (index, event) for index, event in enumerate(unique)}
    item = by_id.get(source_high_water_mark)
    if item is None:
        return "UNRECONCILED"
    completion_index, completion = item
    if not _valid_completion(completion):
        return "UNRECONCILED"
    payload = completion.get("payload", {})
    checked = by_id.get(payload.get("checked_through_event_id"))
    same_aggregate = [
        event
        for event in unique[: completion_index + 1]
        if event.get("aggregate_id") == completion["aggregate_id"]
        and event.get("aggregate_type") == "reconciliation"
    ]
    versions = [event.get("aggregate_version") for event in same_aggregate]
    qualifies = (
        completion.get("run_id") == run_id
        and checked is not None
        and checked[0] < completion_index
        and checked[1].get("run_id") == run_id
        and completion.get("causation_id") == payload.get("checked_through_event_id")
        and payload.get("result") == "PASS"
        and set(payload.get("required_checks", [])) == REQUIRED_CHECKS
        and len(payload.get("required_checks", [])) == len(REQUIRED_CHECKS)
        and payload.get("open_critical_discrepancies") == 0
        and payload.get("open_high_discrepancies") == 0
        and versions == list(range(1, completion["aggregate_version"] + 1))
    )
    return "PASS" if qualifies else "UNRECONCILED"
