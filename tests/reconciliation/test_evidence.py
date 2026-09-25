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
        {"event_id": "evt_1", "event_type": "fill.recorded.v1", "run_id": "run_1"},
        {
            "event_id": "evt_2",
            "event_type": "reconciliation.check_completed.v1",
            "run_id": "run_1",
            "causation_id": "evt_1",
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
