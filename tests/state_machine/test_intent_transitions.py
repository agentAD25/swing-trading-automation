from datetime import datetime, timezone

import pytest

from swingtrade.state_machine import (
    IntentState,
    OrderIntentStateMachine,
    TransitionConflict,
    TransitionEvidence,
)

NOW = datetime(2024, 1, 1, tzinfo=timezone.utc)


def evidence(
    version: int,
    prior: IntentState,
    next_: IntentState,
    event_id: str,
    cause: str,
) -> TransitionEvidence:
    return TransitionEvidence(
        event_id=event_id,
        aggregate_id="int_1",
        aggregate_version=version,
        prior_state=prior,
        next_state=next_,
        reason_code="TEST_REASON",
        initiating_event_id="risk_1",
        causation_id=cause,
        correlation_id="cor_1",
        effective_at=NOW,
        recorded_at=NOW,
    )


def test_complete_required_path_has_evidence() -> None:
    machine = OrderIntentStateMachine("int_1")
    chain = (
        evidence(1, IntentState.NONE, IntentState.CREATED, "evt_1", "risk_1"),
        evidence(2, IntentState.CREATED, IntentState.VALIDATED, "evt_2", "evt_1"),
        evidence(3, IntentState.VALIDATED, IntentState.DISPATCH_PENDING, "evt_3", "evt_2"),
        evidence(4, IntentState.DISPATCH_PENDING, IntentState.DISPATCHED, "evt_4", "evt_3"),
    )
    for item in chain:
        machine.apply(item)
    assert (machine.state, machine.version) == (IntentState.DISPATCHED, 4)


def test_illegal_transition_is_rejected() -> None:
    machine = OrderIntentStateMachine("int_1")
    with pytest.raises(TransitionConflict, match="illegal"):
        machine.apply(
            evidence(1, IntentState.NONE, IntentState.DISPATCHED, "evt_1", "risk_1")
        )


def test_missing_transition_evidence_is_rejected() -> None:
    with pytest.raises(TransitionConflict, match="incomplete"):
        evidence(1, IntentState.NONE, IntentState.CREATED, "", "risk_1")


def test_skipped_version_and_wrong_cause_are_rejected() -> None:
    machine = OrderIntentStateMachine("int_1")
    machine.apply(evidence(1, IntentState.NONE, IntentState.CREATED, "evt_1", "risk_1"))
    with pytest.raises(TransitionConflict, match="noncontiguous"):
        machine.apply(
            evidence(3, IntentState.CREATED, IntentState.VALIDATED, "evt_2", "evt_1")
        )
    with pytest.raises(TransitionConflict, match="cause"):
        machine.apply(
            evidence(2, IntentState.CREATED, IntentState.VALIDATED, "evt_2", "wrong")
        )
