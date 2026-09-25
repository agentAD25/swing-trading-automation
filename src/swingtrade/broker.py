from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Protocol

from swingtrade.domain import ExecutionMode, OrderIntent, OrderObservation
from swingtrade.idempotency import InMemoryIdempotencyStore
from swingtrade.safety import DispatchAuthorization, authorize_dispatch


class BrokerAdapter(Protocol):
    """Broker-neutral normalized execution boundary."""

    def dispatch(
        self, intent: OrderIntent, authorization: DispatchAuthorization
    ) -> OrderObservation: ...


class DryRunAdapter:
    """Local deterministic adapter with no transport or broker client."""

    def __init__(
        self,
        *,
        build_id: str,
        environment: str,
        clock: datetime,
        store: InMemoryIdempotencyStore | None = None,
    ) -> None:
        self._build_id = build_id
        self._environment = environment
        self._clock = clock
        self._store = store or InMemoryIdempotencyStore()

    def dispatch(
        self, intent: OrderIntent, authorization: DispatchAuthorization
    ) -> OrderObservation:
        authorize_dispatch(
            intent,
            authorization,
            build_id=self._build_id,
            environment=self._environment,
            now=self._clock,
        )
        if intent.mode is not ExecutionMode.DRY_RUN:
            raise AssertionError("unreachable non-DRY_RUN dispatch")
        business_input = {
            "decision_id": intent.decision_id,
            "intent_id": intent.intent_id,
            "mode": intent.mode.value,
            "quantity": str(intent.quantity),
            "side": intent.side.value,
        }
        return self._store.execute(
            intent.idempotency_key,
            business_input,
            lambda: OrderObservation(
                order_id=f"dry_{intent.intent_id}",
                intent_id=intent.intent_id,
                state="PENDING",
                requested_quantity=intent.quantity,
                cumulative_quantity=Decimal("0"),
                effective_at=self._clock,
            ),
        )
