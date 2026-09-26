from __future__ import annotations

from datetime import datetime
from typing import Protocol

from swingtrade.domain import ExecutionMode, OrderIntent, OrderObservation
from swingtrade.persistence import (
    PostgresIntentRepository,
    materialize_dry_run_observation,
)
from swingtrade.safety import DispatchAuthorization, authorize_dispatch


class BrokerAdapter(Protocol):
    """Broker-neutral normalized execution boundary."""

    def dispatch(
        self, intent: OrderIntent, authorization: DispatchAuthorization
    ) -> OrderObservation: ...


class DurableRepositoryRequired(RuntimeError):
    """Authoritative dispatch requires the PostgreSQL intent repository."""


class DryRunAdapter:
    """Local deterministic adapter with no transport or broker client."""

    def __init__(
        self,
        *,
        build_id: str,
        environment: str,
        clock: datetime,
        repository: PostgresIntentRepository,
    ) -> None:
        if not isinstance(repository, PostgresIntentRepository):
            raise DurableRepositoryRequired(
                "DRY_RUN dispatch requires a PostgresIntentRepository"
            )
        self._build_id = build_id
        self._environment = environment
        self._clock = clock
        self._repository = repository

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
        persisted = self._repository.create_or_get(
            intent, effective_at=self._clock
        )
        return materialize_dry_run_observation(persisted)
