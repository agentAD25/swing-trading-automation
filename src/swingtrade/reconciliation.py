from __future__ import annotations

from collections.abc import Sequence
from typing import Any

REQUIRED_CHECKS = {"LEDGER_INTEGRITY", "PROJECTION", "EXECUTION"}


def derive_reconciliation_result(
    events: Sequence[dict[str, Any]], source_high_water_mark: str, run_id: str
) -> str:
    by_id = {event.get("event_id"): (index, event) for index, event in enumerate(events)}
    item = by_id.get(source_high_water_mark)
    if item is None:
        return "UNRECONCILED"
    completion_index, completion = item
    if completion.get("event_type") != "reconciliation.check_completed.v1":
        return "UNRECONCILED"
    payload = completion.get("payload", {})
    checked = by_id.get(payload.get("checked_through_event_id"))
    qualifies = (
        completion.get("run_id") == run_id
        and checked is not None
        and checked[0] < completion_index
        and completion.get("causation_id") == payload.get("checked_through_event_id")
        and payload.get("result") == "PASS"
        and set(payload.get("required_checks", [])) == REQUIRED_CHECKS
        and payload.get("open_critical_discrepancies") == 0
        and payload.get("open_high_discrepancies") == 0
    )
    return "PASS" if qualifies else "UNRECONCILED"
