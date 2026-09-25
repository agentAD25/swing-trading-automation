#!/usr/bin/env python3
"""Offline Phase 1 fixture contract validator using only the standard library."""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import re


ROOT = pathlib.Path(__file__).parent / "fixtures" / "wdc-reference"
TRANSITION_SEQUENCE = [
    "order_intent.created.v1",
    "order_intent.validated.v1",
    "order_intent.dispatch_requested.v1",
    "order_intent.dispatched.v1",
]
TRANSITION_TYPES = set(TRANSITION_SEQUENCE)
ENVELOPE_FIELDS = {
    "aggregate_id",
    "aggregate_version",
    "event_id",
    "effective_at",
    "recorded_at",
    "causation_id",
    "correlation_id",
}
PAYLOAD_FIELDS = {
    "prior_state",
    "next_state",
    "reason_code",
    "initiating_event_id",
}
EXPECTED_STATES = [
    ("NONE", "CREATED"),
    ("CREATED", "VALIDATED"),
    ("VALIDATED", "DISPATCH_PENDING"),
    ("DISPATCH_PENDING", "DISPATCHED"),
]


class ContractError(ValueError):
    """Fixture violates a Phase 1 contract."""


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def require_fields(value: dict, fields: set[str], location: str) -> None:
    missing = fields - value.keys()
    if missing:
        raise ContractError(f"{location}: missing {sorted(missing)}")
    empty = [field for field in fields if value[field] in (None, "")]
    if empty:
        raise ContractError(f"{location}: empty {sorted(empty)}")


def validate_transition(event: dict) -> None:
    require_fields(event, ENVELOPE_FIELDS, event.get("event_id", "<event>"))
    payload = event.get("payload")
    if not isinstance(payload, dict):
        raise ContractError(f"{event['event_id']}: payload is not an object")
    require_fields(payload, PAYLOAD_FIELDS, f"{event['event_id']}.payload")


def validate_intent(intent_events: list[dict]) -> None:
    if [event["event_type"] for event in intent_events] != TRANSITION_SEQUENCE:
        raise ContractError("intent transition event sequence is incomplete")
    initiating = intent_events[0]["causation_id"]
    correlation = intent_events[0]["correlation_id"]
    previous_event_id = None
    for index, (event, states) in enumerate(zip(intent_events, EXPECTED_STATES), 1):
        validate_transition(event)
        if event["aggregate_version"] != index:
            raise ContractError(f"{event['event_id']}: noncontiguous version")
        if (event["payload"]["prior_state"], event["payload"]["next_state"]) != states:
            raise ContractError(f"{event['event_id']}: invalid state transition")
        if event["payload"]["initiating_event_id"] != initiating:
            raise ContractError(f"{event['event_id']}: initiating cause changed")
        if event["correlation_id"] != correlation:
            raise ContractError(f"{event['event_id']}: correlation changed")
        expected_cause = initiating if previous_event_id is None else previous_event_id
        if event["causation_id"] != expected_cause:
            raise ContractError(f"{event['event_id']}: immediate cause mismatch")
        previous_event_id = event["event_id"]


def load_fixture() -> tuple[dict, dict, list[dict]]:
    scenario = json.loads((ROOT / "scenario.json").read_text())
    report = json.loads((ROOT / "expected-report.json").read_text())
    events = [
        json.loads(line)
        for line in (ROOT / "expected-events.jsonl").read_text().splitlines()
    ]
    return scenario, report, events


def validate_manifest() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    for name, expected in manifest["sha256"].items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ContractError(f"{name}: {actual} != {expected}")


def validate_idempotency(scenario: dict, events: list[dict]) -> None:
    cases = [
        ("int_wdc_entry_001", "dispatch", "entry_dispatch", "int_wdc_entry_001"),
        ("int_wdc_exit_001", "dispatch", "exit_dispatch", "int_wdc_exit_001"),
        ("rpt_wdc_ref_001", "report", "report", scenario["ids"]["run_id"]),
    ]
    for aggregate_id, operation, input_name, scope in cases:
        digest = hashlib.sha256(
            canonical(scenario["idempotency_inputs"][input_name])
        ).hexdigest()
        expected = f"v1:{operation}:{scope}:{digest}"
        keys = {
            event["idempotency_key"]
            for event in events
            if event["aggregate_id"] == aggregate_id
        }
        if keys != {expected} or not re.fullmatch(
            r"v1:[a-z_]+:[a-z0-9_]+:[0-9a-f]{64}", expected
        ):
            raise ContractError(f"{aggregate_id}: invalid idempotency key")


def validate_report(report: dict, events: list[dict]) -> None:
    body = dict(report)
    claimed = body.pop("content_digest")
    actual = hashlib.sha256(canonical(body)).hexdigest()
    report_event = events[-1]
    if actual != claimed:
        raise ContractError("report content digest mismatch")
    if report_event["payload"]["content_digest"] != claimed:
        raise ContractError("report event digest mismatch")
    if report_event["causation_id"] != report["source_high_water_mark"]:
        raise ContractError("report high-water mark mismatch")


def validate_fixture() -> tuple[dict, dict, list[dict]]:
    validate_manifest()
    scenario, report, events = load_fixture()
    for intent_id in ("int_wdc_entry_001", "int_wdc_exit_001"):
        validate_intent(
            [event for event in events if event["aggregate_id"] == intent_id]
        )
    validate_idempotency(scenario, events)
    validate_report(report, events)
    return scenario, report, events


def regression_test_required_transition_fields(events: list[dict]) -> None:
    sample = next(event for event in events if event["event_type"] in TRANSITION_TYPES)
    for field in ("prior_state", "next_state", "reason_code"):
        mutated = copy.deepcopy(sample)
        del mutated["payload"][field]
        try:
            validate_transition(mutated)
        except ContractError:
            continue
        raise AssertionError(f"omission of {field} was not rejected")


if __name__ == "__main__":
    _, _, fixture_events = validate_fixture()
    regression_test_required_transition_fields(fixture_events)
    print(
        "Phase 1 contracts: manifest, C01, C02, C03 PASS; "
        "required-field omission regression PASS"
    )
