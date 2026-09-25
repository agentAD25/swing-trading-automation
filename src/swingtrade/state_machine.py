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


@dataclass(frozen=True)
class TransitionEvidence:
    event_id: str
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

    def apply(self, evidence: TransitionEvidence) -> IntentState:
        if evidence.aggregate_id != self.aggregate_id:
            raise TransitionConflict("aggregate identity changed")
        if evidence.prior_state is not self.state or evidence.next_state not in _ALLOWED.get(
            self.state, set()
        ):
            raise TransitionConflict("illegal transition")
        if evidence.aggregate_version != self.version + 1:
            raise TransitionConflict("aggregate version is noncontiguous")
        if self.initiating_event_id and evidence.initiating_event_id != self.initiating_event_id:
            raise TransitionConflict("initiating event changed")
        if self.last_event_id and evidence.causation_id != self.last_event_id:
            raise TransitionConflict("immediate cause mismatch")
        if self.state is IntentState.NONE and evidence.causation_id != evidence.initiating_event_id:
            raise TransitionConflict("created event must be caused by initiating event")
        self.state = evidence.next_state
        self.version = evidence.aggregate_version
        self.initiating_event_id = evidence.initiating_event_id
        self.last_event_id = evidence.event_id
        return self.state
