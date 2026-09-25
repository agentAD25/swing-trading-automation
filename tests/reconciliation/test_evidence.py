import copy

import pytest

from swingtrade.reconciliation import REQUIRED_CHECKS, derive_reconciliation_result


def completion(**payload_overrides: object) -> list[dict[str, object]]:
    payload = {
        "checked_through_event_id": "evt_1",
        "result": "PASS",
        "required_checks": sorted(REQUIRED_CHECKS),
        "open_critical_discrepancies": 0,
        "open_high_discrepancies": 0,
    }
    payload.update(payload_overrides)
    return [
        {
            "event_id": "evt_1",
            "event_type": "fill.recorded.v1",
            "run_id": "run_1",
        },
        {
            "aggregate_id": "rec_1",
            "aggregate_type": "reconciliation",
            "aggregate_version": 1,
            "causation_id": "evt_1",
            "correlation_id": "cor_1",
            "effective_at": "2024-01-01T00:00:00.000001Z",
            "event_id": "evt_2",
            "event_type": "reconciliation.check_completed.v1",
            "idempotency_key": None,
            "producer": "reconciler",
            "producer_version": "1",
            "recorded_at": "2024-01-01T00:00:00.000002Z",
            "run_id": "run_1",
            "schema_version": 1,
            "source": {"kind": "local"},
            "payload": payload,
        },
    ]


def test_complete_evidence_can_prove_pass() -> None:
    assert derive_reconciliation_result(completion(), "evt_2", "run_1") == "PASS"


def test_report_projection_cannot_manufacture_pass() -> None:
    events = [{"event_id": "evt_1", "event_type": "report.generated.v1", "run_id": "run_1"}]
    assert derive_reconciliation_result(events, "evt_1", "run_1") == "UNRECONCILED"


def test_open_or_missing_evidence_withholds_pass() -> None:
    assert (
        derive_reconciliation_result(
            completion(open_high_discrepancies=1), "evt_2", "run_1"
        )
        == "UNRECONCILED"
    )
    assert derive_reconciliation_result(completion(), "missing", "run_1") == "UNRECONCILED"


@pytest.mark.parametrize(
    ("location", "field"),
    [
        ("envelope", "aggregate_id"),
        ("envelope", "aggregate_type"),
        ("envelope", "aggregate_version"),
        ("envelope", "correlation_id"),
        ("envelope", "effective_at"),
        ("envelope", "producer"),
        ("envelope", "recorded_at"),
        ("envelope", "schema_version"),
        ("envelope", "source"),
        ("payload", "checked_through_event_id"),
        ("payload", "required_checks"),
        ("payload", "result"),
        ("payload", "open_critical_discrepancies"),
        ("payload", "open_high_discrepancies"),
    ],
)
def test_missing_contract_evidence_fails_closed(location: str, field: str) -> None:
    events = completion()
    target = events[1] if location == "envelope" else events[1]["payload"]
    assert isinstance(target, dict)
    del target[field]
    assert derive_reconciliation_result(events, "evt_2", "run_1") == "UNRECONCILED"


def test_partial_and_contradictory_evidence_never_increases_certainty() -> None:
    wrong_run = completion()
    wrong_run[0]["run_id"] = "run_other"
    assert derive_reconciliation_result(wrong_run, "evt_2", "run_1") == "UNRECONCILED"

    duplicate_checks = completion(required_checks=[*sorted(REQUIRED_CHECKS), "EXECUTION"])
    assert derive_reconciliation_result(duplicate_checks, "evt_2", "run_1") == "UNRECONCILED"

    contradiction = completion()
    changed = copy.deepcopy(contradiction[1])
    changed["payload"]["result"] = "FAIL"  # type: ignore[index]
    contradiction.append(changed)
    assert derive_reconciliation_result(contradiction, "evt_2", "run_1") == "UNRECONCILED"


def test_repeated_identical_evidence_and_derivation_are_idempotent() -> None:
    events = completion()
    events.append(copy.deepcopy(events[1]))
    first = derive_reconciliation_result(events, "evt_2", "run_1")
    second = derive_reconciliation_result(events, "evt_2", "run_1")
    assert first == second == "PASS"
