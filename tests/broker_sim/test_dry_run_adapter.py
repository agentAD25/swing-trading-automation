from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from swingtrade.broker import DryRunAdapter
from swingtrade.domain import ExecutionMode, OrderIntent, Side
from swingtrade.idempotency import idempotency_key
from swingtrade.safety import AuthorizationDenied, DispatchAuthorization

NOW = datetime(2024, 1, 1, tzinfo=timezone.utc)
INPUT = {
    "decision_id": "dec_1",
    "intent_id": "int_1",
    "mode": "DRY_RUN",
    "quantity": "2",
    "side": "BUY",
}


def intent() -> OrderIntent:
    return OrderIntent(
        "int_1",
        "run_1",
        "dec_1",
        "ins_1",
        Side.BUY,
        Decimal("2"),
        ExecutionMode.DRY_RUN,
        idempotency_key("dispatch", "int_1", INPUT),
    )


def grant(**overrides: object) -> DispatchAuthorization:
    values = {
        "run_id": "run_1",
        "intent_id": "int_1",
        "mode": ExecutionMode.DRY_RUN,
        "build_id": "build_1",
        "environment": "local",
        "expires_at": NOW + timedelta(minutes=1),
    }
    values.update(overrides)
    return DispatchAuthorization(**values)  # type: ignore[arg-type]


def test_dry_run_dispatch_is_local_and_idempotent() -> None:
    adapter = DryRunAdapter(build_id="build_1", environment="local", clock=NOW)
    first = adapter.dispatch(intent(), grant())
    second = adapter.dispatch(intent(), grant())
    assert first is second
    assert first.order_id == "dry_int_1"
    assert not hasattr(adapter, "submit")


@pytest.mark.parametrize(
    "override",
    [
        {"intent_id": "int_other"},
        {"build_id": "build_other"},
        {"environment": "production"},
        {"expires_at": NOW - timedelta(seconds=1)},
        {"replay": True},
        {"reporting": True},
    ],
)
def test_authorization_mismatch_produces_no_effect(override: dict[str, object]) -> None:
    adapter = DryRunAdapter(build_id="build_1", environment="local", clock=NOW)
    with pytest.raises(AuthorizationDenied):
        adapter.dispatch(intent(), grant(**override))
