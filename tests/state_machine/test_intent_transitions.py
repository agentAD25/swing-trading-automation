from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from swingtrade.state_machine import (
    IntentState,
    OrderIntentStateMachine,
    TransitionConflict,
    TransitionEvidence,
)

NOW = datetime(2024, 1, 1, tzinfo=UTC)


def evidence(
    version: int,
    prior: IntentState,
    next_: IntentState,
    event_id: str,
    cause: str,
    *,
    effective_at: datetime = NOW,
    recorded_at: datetime = NOW,
) -> TransitionEvidence:
    event_types = {
        (IntentState.NONE, IntentState.CREATED): "order_intent.created.v1",
        (IntentState.CREATED, IntentState.VALIDATED): "order_intent.validated.v1",
        (IntentState.VALIDATED, IntentState.DISPATCH_PENDING):
            "order_intent.dispatch_requested.v1",
        (IntentState.DISPATCH_PENDING, IntentState.DISPATCHED): "order_intent.dispatched.v1",
    }
    return TransitionEvidence(
        event_id=event_id,
        event_type=event_types.get((prior, next_), "order_intent.invalid.v1"),
        aggregate_id="int_1",
        aggregate_version=version,
        prior_state=prior,
        next_state=next_,
        reason_code="TEST_REASON",
        initiating_event_id="risk_1",
        causation_id=cause,
        correlation_id="cor_1",
        effective_at=effective_at,
        recorded_at=recorded_at,
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


def test_equal_and_rapid_distinct_times_are_preserved() -> None:
    machine = OrderIntentStateMachine("int_1")
    first = evidence(1, IntentState.NONE, IntentState.CREATED, "evt_1", "risk_1")
    rapid = evidence(
        2,
        IntentState.CREATED,
        IntentState.VALIDATED,
        "evt_2",
        "evt_1",
        effective_at=NOW,
        recorded_at=NOW + timedelta(microseconds=1),
    )
    machine.apply(first)
    machine.apply(rapid)
    assert machine.last_effective_at == NOW
    assert machine.last_recorded_at == NOW + timedelta(microseconds=1)


@pytest.mark.parametrize("field", ["effective_at", "recorded_at"])
def test_backward_event_time_is_rejected(field: str) -> None:
    machine = OrderIntentStateMachine("int_1")
    first = evidence(
        1,
        IntentState.NONE,
        IntentState.CREATED,
        "evt_1",
        "risk_1",
        effective_at=NOW + timedelta(seconds=1),
        recorded_at=NOW + timedelta(seconds=1),
    )
    machine.apply(first)
    second = evidence(
        2,
        IntentState.CREATED,
        IntentState.VALIDATED,
        "evt_2",
        "evt_1",
        effective_at=NOW + timedelta(seconds=2),
        recorded_at=NOW + timedelta(seconds=2),
    )
    with pytest.raises(TransitionConflict, match="time moved backward"):
        machine.apply(replace(second, **{field: NOW}))


def test_exact_event_type_and_replay_semantics() -> None:
    machine = OrderIntentStateMachine("int_1")
    created = evidence(1, IntentState.NONE, IntentState.CREATED, "evt_1", "risk_1")
    assert machine.apply(created) is IntentState.CREATED
    assert machine.apply(created) is IntentState.CREATED
    with pytest.raises(TransitionConflict, match="contradictory"):
        machine.apply(replace(created, reason_code="DIFFERENT"))
    validated = evidence(2, IntentState.CREATED, IntentState.VALIDATED, "evt_2", "evt_1")
    with pytest.raises(TransitionConflict, match="event type"):
        machine.apply(replace(validated, event_type="order_intent.dispatched.v1"))
