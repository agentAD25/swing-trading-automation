from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from swingtrade.domain import ExecutionMode, OrderIntent, utc_instant


class AuthorizationDenied(RuntimeError):
    """Dispatch was denied without producing an effect."""


@dataclass(frozen=True)
class DispatchAuthorization:
    run_id: str
    intent_id: str
    mode: ExecutionMode
    build_id: str
    environment: str
    expires_at: datetime
    replay: bool = False
    reporting: bool = False

    def __post_init__(self) -> None:
        utc_instant(self.expires_at)


def authorize_dispatch(
    intent: OrderIntent,
    authorization: DispatchAuthorization,
    *,
    build_id: str,
    environment: str,
    now: datetime,
) -> None:
    utc_instant(now)
    exact_identity = (
        authorization.run_id == intent.run_id
        and authorization.intent_id == intent.intent_id
        and authorization.mode is intent.mode
        and authorization.build_id == build_id
        and authorization.environment == environment
    )
    if (
        intent.mode is not ExecutionMode.DRY_RUN
        or not exact_identity
        or authorization.expires_at < now
        or authorization.replay
        or authorization.reporting
    ):
        raise AuthorizationDenied("dispatch authorization denied")
