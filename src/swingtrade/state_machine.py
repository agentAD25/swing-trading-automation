from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from swingtrade.domain import utc_instant


class TransitionConflict(RuntimeError):
    """A state change is illegal or lacks durable evidence."""


class IntentState(StrEnum):
    NONE = "NONE"
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    DISPATCH_PENDING = "DISPATCH_PENDING"
    DISPATCHED = "DISPATCHED"
    BLOCKED = "BLOCKED"
    CANCELLED_BEFORE_DISPATCH = "CANCELLED_BEFORE_DISPATCH"
    OPERATOR_REVIEW = "OPERATOR_REVIEW"


_ALLOWED = {
    IntentState.NONE: {IntentState.CREATED},
    IntentState.CREATED: {
        IntentState.VALIDATED,
        IntentState.BLOCKED,
        IntentState.CANCELLED_BEFORE_DISPATCH,
        IntentState.OPERATOR_REVIEW,
    },
    IntentState.VALIDATED: {
        IntentState.DISPATCH_PENDING,
        IntentState.CANCELLED_BEFORE_DISPATCH,
        IntentState.OPERATOR_REVIEW,
    },
    IntentState.DISPATCH_PENDING: {IntentState.DISPATCHED, IntentState.OPERATOR_REVIEW},
}
_EVENT_TRANSITIONS = {
    (IntentState.NONE, IntentState.CREATED): "order_intent.created.v1",
    (IntentState.CREATED, IntentState.VALIDATED): "order_intent.validated.v1",
    (IntentState.VALIDATED, IntentState.DISPATCH_PENDING):
        "order_intent.dispatch_requested.v1",
    (IntentState.DISPATCH_PENDING, IntentState.DISPATCHED): "order_intent.dispatched.v1",
}


@dataclass(frozen=True)
class TransitionEvidence:
    event_id: str
    event_type: str
    aggregate_id: str
    aggregate_version: int
    prior_state: IntentState
    next_state: IntentState
    reason_code: str
    initiating_event_id: str
    causation_id: str
    correlation_id: str
    effective_at: datetime
    recorded_at: datetime

    def __post_init__(self) -> None:
        required = (
            self.event_id,
            self.event_type,
            self.aggregate_id,
            self.reason_code,
            self.initiating_event_id,
            self.causation_id,
            self.correlation_id,
        )
        if not all(required) or self.aggregate_version < 1:
            raise TransitionConflict("transition evidence is incomplete")
        utc_instant(self.effective_at)
        utc_instant(self.recorded_at)


class OrderIntentStateMachine:
    def __init__(self, aggregate_id: str) -> None:
        self.aggregate_id = aggregate_id
        self.state = IntentState.NONE
        self.version = 0
        self.initiating_event_id: str | None = None
        self.last_event_id: str | None = None
        self.last_effective_at: datetime | None = None
        self.last_recorded_at: datetime | None = None
        self.applied_events: dict[str, TransitionEvidence] = {}

    def apply(self, evidence: TransitionEvidence) -> IntentState:
        previous = self.applied_events.get(evidence.event_id)
        if previous is not None:
            if previous != evidence:
                raise TransitionConflict("event identity reused with contradictory evidence")
            return self.state
        if evidence.aggregate_id != self.aggregate_id:
            raise TransitionConflict("aggregate identity changed")
        if evidence.prior_state is not self.state or evidence.next_state not in _ALLOWED.get(
            self.state, set()
        ):
            raise TransitionConflict("illegal transition")
        if evidence.aggregate_version != self.version + 1:
            raise TransitionConflict("aggregate version is noncontiguous")
        expected_event_type = _EVENT_TRANSITIONS.get(
            (evidence.prior_state, evidence.next_state)
        )
        if expected_event_type is not None and evidence.event_type != expected_event_type:
            raise TransitionConflict("event type contradicts transition")
        if self.initiating_event_id and evidence.initiating_event_id != self.initiating_event_id:
            raise TransitionConflict("initiating event changed")
        if self.last_event_id and evidence.causation_id != self.last_event_id:
            raise TransitionConflict("immediate cause mismatch")
        if self.state is IntentState.NONE and evidence.causation_id != evidence.initiating_event_id:
            raise TransitionConflict("created event must be caused by initiating event")
        if self.last_effective_at and evidence.effective_at < self.last_effective_at:
            raise TransitionConflict("effective time moved backward")
        if self.last_recorded_at and evidence.recorded_at < self.last_recorded_at:
            raise TransitionConflict("recorded time moved backward")
        self.state = evidence.next_state
        self.version = evidence.aggregate_version
        self.initiating_event_id = evidence.initiating_event_id
        self.last_event_id = evidence.event_id
        self.last_effective_at = evidence.effective_at
        self.last_recorded_at = evidence.recorded_at
        self.applied_events[evidence.event_id] = evidence
        return self.state
