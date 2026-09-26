import copy

import pytest

from swingtrade.reconciliation import (
    INITIAL_AGGREGATE_VERSION,
    REQUIRED_CHECKS,
    derive_reconciliation_result,
)


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
            "aggregate_id": "ord_1",
            "aggregate_type": "order",
            "aggregate_version": 1,
            "causation_id": "cmd_1",
            "correlation_id": "cor_1",
            "effective_at": "2024-01-01T00:00:00.000000Z",
            "event_id": "evt_1",
            "event_type": "fill.recorded.v1",
            "idempotency_key": None,
            "payload": {},
            "producer": "dry_run",
            "producer_version": "1",
            "recorded_at": "2024-01-01T00:00:00.000000Z",
            "run_id": "run_1",
            "schema_version": 1,
            "source": {"kind": "local"},
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


def stream_event(
    event_id: str,
    aggregate_type: str,
    aggregate_id: str,
    aggregate_version: int,
    *,
    run_id: str = "run_1",
) -> dict[str, object]:
    event = copy.deepcopy(completion()[0])
    event.update(
        {
            "aggregate_id": aggregate_id,
            "aggregate_type": aggregate_type,
            "aggregate_version": aggregate_version,
            "event_id": event_id,
            "run_id": run_id,
        }
    )
    return event


def test_complete_evidence_can_prove_pass() -> None:
    assert derive_reconciliation_result(completion(), "evt_2", "run_1") == "PASS"


def test_interleaved_streams_partition_and_start_at_accepted_initial_version() -> None:
    assert INITIAL_AGGREGATE_VERSION == 1
    checked, completed = completion()
    events = [
        checked,
        stream_event("evt_pos_1", "position", "pos_1", 1),
        stream_event("evt_ord_2", "order", "ord_1", 2),
        stream_event(
            "evt_foreign", "position", "pos_foreign", 1, run_id="run_other"
        ),
        stream_event("evt_pos_2", "position", "pos_1", 2),
        completed,
    ]
    assert derive_reconciliation_result(events, "evt_2", "run_1") == "PASS"


def invalid_stream_case(case: str) -> list[dict[str, object]]:
    checked, completed = completion()
    if case == "start_below":
        checked["aggregate_version"] = 0
        return [checked, completed]
    if case == "start_above":
        checked["aggregate_version"] = 2
        return [checked, completed]
    if case == "middle_gap":
        return [checked, stream_event("evt_ord_3", "order", "ord_1", 3), completed]
    if case == "duplicate_different_event_id":
        return [checked, stream_event("evt_ord_dup", "order", "ord_1", 1), completed]
    if case == "conflicting_global_event_id":
        conflict = stream_event("evt_1", "position", "pos_other", 1)
        return [checked, conflict, completed]
    if case == "decreasing":
        return [
            checked,
            stream_event("evt_ord_3", "order", "ord_1", 3),
            stream_event("evt_ord_2", "order", "ord_1", 2),
            completed,
        ]
    if case == "cross_run":
        checked["run_id"] = "run_other"
        return [checked, completed]
    if case == "cross_run_coordinate":
        return [
            checked,
            stream_event(
                "evt_cross_run", "order", "ord_1", 1, run_id="run_other"
            ),
            completed,
        ]
    if case == "cross_aggregate":
        completed["aggregate_version"] = 2
        return [
            checked,
            stream_event("evt_rec_other", "reconciliation", "rec_other", 1),
            completed,
        ]
    if case == "one_valid_one_invalid":
        return [
            checked,
            stream_event("evt_valid", "position", "pos_valid", 1),
            stream_event("evt_invalid", "trade", "trade_invalid", 2),
            completed,
        ]
    raise AssertionError(f"unknown case: {case}")


@pytest.mark.parametrize(
    "case",
    [
        "start_below",
        "start_above",
        "middle_gap",
        "duplicate_different_event_id",
        "conflicting_global_event_id",
        "decreasing",
        "cross_run",
        "cross_run_coordinate",
        "cross_aggregate",
        "one_valid_one_invalid",
    ],
)
def test_ledger_integrity_stream_matrix_fails_closed(case: str) -> None:
    assert (
        derive_reconciliation_result(invalid_stream_case(case), "evt_2", "run_1")
        == "UNRECONCILED"
    )


def test_identical_duplicate_event_identity_is_a_valid_no_op() -> None:
    checked, completed = completion()
    assert (
        derive_reconciliation_result(
            [checked, copy.deepcopy(checked), completed], "evt_2", "run_1"
        )
        == "PASS"
    )


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


@pytest.mark.parametrize(
    ("event_index", "field", "value"),
    [
        (1, "effective_at", "2024-01-01T00:00:00.00001Z"),
        (1, "recorded_at", "2024-01-01T00:00:00.000002+00:00"),
        (1, "recorded_at", "2024-01-01T00:00:00Z"),
        (0, "recorded_at", "2023-12-31T23:59:59.999999Z"),
        (1, "recorded_at", "2023-12-31T23:59:59.999999Z"),
    ],
)
def test_noncanonical_or_backward_temporal_evidence_fails_closed(
    event_index: int, field: str, value: object
) -> None:
    events = completion()
    events[event_index][field] = value
    assert derive_reconciliation_result(events, "evt_2", "run_1") == "UNRECONCILED"


def test_late_effective_fact_does_not_override_recorded_sequence() -> None:
    events = completion()
    events[0]["effective_at"] = "2024-01-01T00:00:00.000001Z"
    events[0]["recorded_at"] = "2024-01-01T00:00:00.000001Z"
    events[1]["effective_at"] = "2024-01-01T00:00:00.000000Z"
    assert derive_reconciliation_result(events, "evt_2", "run_1") == "PASS"


def test_intervening_run_event_cannot_move_recorded_time_backward() -> None:
    events = completion()
    intervening = copy.deepcopy(events[0])
    intervening["aggregate_id"] = "ord_2"
    intervening["event_id"] = "evt_intervening"
    intervening["recorded_at"] = "2024-01-01T00:00:00.000010Z"
    events.insert(1, intervening)
    assert derive_reconciliation_result(events, "evt_2", "run_1") == "UNRECONCILED"


@pytest.mark.parametrize(
    ("event_index", "field", "value"),
    [
        (1, "correlation_id", "cor_other"),
        (1, "causation_id", "evt_other"),
        (1, "run_id", "run_other"),
        (0, "run_id", "run_other"),
        (1, "aggregate_type", "report"),
        (1, "aggregate_version", 2),
        (1, "aggregate_version", True),
        (1, "schema_version", True),
        (0, "aggregate_id", ""),
        (0, "causation_id", ""),
    ],
)
def test_wrong_correlation_causation_run_or_aggregate_fails_closed(
    event_index: int, field: str, value: object
) -> None:
    events = completion()
    events[event_index][field] = value
    assert derive_reconciliation_result(events, "evt_2", "run_1") == "UNRECONCILED"


def test_missing_or_after_checkpoint_relation_fails_closed() -> None:
    missing = completion(checked_through_event_id="evt_missing")
    assert derive_reconciliation_result(missing, "evt_2", "run_1") == "UNRECONCILED"

    after = completion()
    checked = after.pop(0)
    after.append(checked)
    assert derive_reconciliation_result(after, "evt_2", "run_1") == "UNRECONCILED"


@pytest.mark.parametrize(
    "payload_override",
    [
        {"required_checks": None},
        {"required_checks": sorted(REQUIRED_CHECKS - {"EXECUTION"})},
        {"open_critical_discrepancies": 1},
        {"open_high_discrepancies": 1},
        {"open_critical_discrepancies": False},
        {"open_high_discrepancies": 0.0},
    ],
)
def test_incomplete_checks_or_discrepancies_fail_closed(
    payload_override: dict[str, object],
) -> None:
    assert (
        derive_reconciliation_result(completion(**payload_override), "evt_2", "run_1")
        == "UNRECONCILED"
    )


def test_repeated_identical_evidence_and_derivation_are_idempotent() -> None:
    events = completion()
    events.append(copy.deepcopy(events[1]))
    first = derive_reconciliation_result(events, "evt_2", "run_1")
    second = derive_reconciliation_result(events, "evt_2", "run_1")
    assert first == second == "PASS"
