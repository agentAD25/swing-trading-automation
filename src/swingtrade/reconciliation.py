from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from swingtrade.idempotency import canonical_json

REQUIRED_CHECKS = {"LEDGER_INTEGRITY", "PROJECTION", "EXECUTION"}
INITIAL_AGGREGATE_VERSION = 1
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
_CANONICAL_UTC_MICROSECOND = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$"
)


def _canonical_instant(value: object) -> datetime | None:
    if not isinstance(value, str) or not _CANONICAL_UTC_MICROSECOND.fullmatch(value):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
    except ValueError:
        return None


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


def _valid_envelope(event: dict[str, Any]) -> bool:
    if not _ENVELOPE_FIELDS <= event.keys():
        return False
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return False
    nonempty = (
        event.get("aggregate_id"),
        event.get("aggregate_type"),
        event.get("causation_id"),
        event.get("correlation_id"),
        event.get("event_id"),
        event.get("event_type"),
        event.get("producer"),
        event.get("producer_version"),
        event.get("run_id"),
    )
    effective_at = _canonical_instant(event.get("effective_at"))
    recorded_at = _canonical_instant(event.get("recorded_at"))
    return bool(
        all(isinstance(value, str) and value for value in nonempty)
        and type(event.get("aggregate_version")) is int
        and event["aggregate_version"] > 0
        and type(event.get("schema_version")) is int
        and event["schema_version"] > 0
        and isinstance(event.get("source"), dict)
        and (
            event.get("idempotency_key") is None
            or (
                isinstance(event.get("idempotency_key"), str)
                and bool(event.get("idempotency_key"))
            )
        )
        and effective_at is not None
        and recorded_at is not None
        and recorded_at >= effective_at
    )


def _valid_completion(event: dict[str, Any]) -> bool:
    payload = event.get("payload")
    return (
        _valid_envelope(event)
        and isinstance(payload, dict)
        and _PAYLOAD_FIELDS <= payload.keys()
        and event.get("aggregate_type") == "reconciliation"
        and event.get("event_type") == "reconciliation.check_completed.v1"
    )


def _valid_stream_integrity(events: Sequence[dict[str, Any]]) -> bool:
    streams: dict[tuple[str, str], list[int]] = {}
    coordinates: dict[tuple[str, str, int], str] = {}
    for event in events:
        if not _valid_envelope(event):
            return False
        aggregate_type = event["aggregate_type"]
        aggregate_id = event["aggregate_id"]
        aggregate_version = event["aggregate_version"]
        event_id = event["event_id"]
        stream = (aggregate_type, aggregate_id)
        coordinate = (*stream, aggregate_version)
        previous_event_id = coordinates.get(coordinate)
        if previous_event_id is not None and previous_event_id != event_id:
            return False
        coordinates[coordinate] = event_id
        streams.setdefault(stream, []).append(aggregate_version)
    return all(
        versions
        == list(
            range(
                INITIAL_AGGREGATE_VERSION,
                INITIAL_AGGREGATE_VERSION + len(versions),
            )
        )
        for versions in streams.values()
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
        and event.get("run_id") == run_id
    ]
    run_events = [
        event
        for event in unique[: completion_index + 1]
        if event.get("run_id") == run_id
    ]
    versions = [event.get("aggregate_version") for event in same_aggregate]
    checked_event = checked[1] if checked is not None else None
    completion_recorded = _canonical_instant(completion.get("recorded_at"))
    checked_recorded = (
        _canonical_instant(checked_event.get("recorded_at"))
        if checked_event is not None
        else None
    )
    required_checks = payload.get("required_checks")
    exact_required_checks = (
        isinstance(required_checks, list)
        and all(isinstance(check, str) for check in required_checks)
        and set(required_checks) == REQUIRED_CHECKS
        and len(required_checks) == len(REQUIRED_CHECKS)
    )
    recorded_times = [_canonical_instant(event.get("recorded_at")) for event in run_events]
    nondecreasing_recorded_times = (
        all(value is not None for value in recorded_times)
        and all(
            left <= right
            for left, right in zip(recorded_times, recorded_times[1:], strict=False)
            if left is not None and right is not None
        )
    )
    qualifies = (
        completion.get("run_id") == run_id
        and checked is not None
        and checked[0] < completion_index
        and checked_event is not None
        and _valid_envelope(checked_event)
        and checked_event.get("run_id") == run_id
        and checked_event.get("correlation_id") == completion.get("correlation_id")
        and completion.get("causation_id") == payload.get("checked_through_event_id")
        and completion_recorded is not None
        and checked_recorded is not None
        and completion_recorded >= checked_recorded
        and all(_valid_envelope(event) for event in run_events)
        and _valid_stream_integrity(run_events)
        and nondecreasing_recorded_times
        and payload.get("result") == "PASS"
        and exact_required_checks
        and type(payload.get("open_critical_discrepancies")) is int
        and payload.get("open_critical_discrepancies") == 0
        and type(payload.get("open_high_discrepancies")) is int
        and payload.get("open_high_discrepancies") == 0
        and all(
            _valid_envelope(event)
            and event.get("run_id") == run_id
            and event.get("correlation_id") == completion.get("correlation_id")
            for event in same_aggregate
        )
        and versions == list(range(1, completion["aggregate_version"] + 1))
    )
    return "PASS" if qualifies else "UNRECONCILED"
