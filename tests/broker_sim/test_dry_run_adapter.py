import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select, text

from swingtrade.broker import DryRunAdapter, DurableRepositoryRequired
from swingtrade.domain import (
    DomainValidationError,
    ExecutionMode,
    OrderIntent,
    Side,
)
from swingtrade.persistence import (
    IntentIdentityConflict,
    OrderIntentRow,
    PostgresIntentRepository,
    canonical_dispatch_key,
)
from swingtrade.safety import AuthorizationDenied, DispatchAuthorization

NOW = datetime(2024, 1, 1, tzinfo=UTC)
POSTGRES_URL = os.getenv("SWINGTRADE_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="SWINGTRADE_TEST_POSTGRES_URL is required"
)


def intent(*, quantity: str = "2") -> OrderIntent:
    candidate = OrderIntent(
        "int_1",
        "run_1",
        "dec_1",
        "ins_1",
        Side.BUY,
        Decimal(quantity),
        ExecutionMode.DRY_RUN,
        "",
    )
    return replace(candidate, idempotency_key=canonical_dispatch_key(candidate))


@pytest.fixture
def engine():
    assert POSTGRES_URL is not None
    value = create_engine(POSTGRES_URL, pool_size=12, max_overflow=4)
    with value.begin() as connection:
        connection.execute(text("TRUNCATE TABLE order_intents"))
    yield value
    value.dispose()


def adapter(engine, *, clock: datetime = NOW) -> DryRunAdapter:
    return DryRunAdapter(
        build_id="build_1",
        environment="local",
        clock=clock,
        repository=PostgresIntentRepository(engine),
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


def test_dry_run_dispatch_is_local_durable_and_idempotent(engine) -> None:
    subject = adapter(engine)
    first = subject.dispatch(intent(), grant())
    second = subject.dispatch(intent(), grant())
    assert first == second
    assert first.order_id == "dry_int_1"
    assert not hasattr(subject, "submit")
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1


def test_dry_run_equivalent_decimal_scales_converge(engine) -> None:
    subject = adapter(engine)
    first = subject.dispatch(intent(quantity="2"), grant())
    assert subject.dispatch(intent(quantity="2.0"), grant()) == first
    assert subject.dispatch(intent(quantity="2.00"), grant()) == first
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1


def test_dry_run_extreme_decimal_fails_before_durable_row(engine) -> None:
    extreme = OrderIntent(
        "int_1",
        "run_1",
        "dec_1",
        "ins_1",
        Side.BUY,
        Decimal("1E+1000000"),
        ExecutionMode.DRY_RUN,
        "v1:dispatch:int_1:" + "f" * 64,
    )
    with pytest.raises(DomainValidationError, match="resource bound"):
        adapter(engine).dispatch(extreme, grant())
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 0


def test_missing_durable_repository_fails_closed() -> None:
    with pytest.raises(DurableRepositoryRequired):
        DryRunAdapter(
            build_id="build_1",
            environment="local",
            clock=NOW,
            repository=None,  # type: ignore[arg-type]
        )


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
def test_authorization_mismatch_produces_no_effect(
    engine, override: dict[str, object]
) -> None:
    subject = adapter(engine)
    with pytest.raises(AuthorizationDenied):
        subject.dispatch(intent(), grant(**override))
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 0


def test_concurrent_identical_adapter_dispatch_converges(engine) -> None:
    subject = adapter(engine)
    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(lambda _: subject.dispatch(intent(), grant()), range(24)))
    assert all(result == results[0] for result in results)
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1


def test_concurrent_conflicting_adapter_dispatch_fails_closed(engine) -> None:
    subject = adapter(engine)

    def dispatch(quantity: str):
        try:
            return subject.dispatch(intent(quantity=quantity), grant())
        except IntentIdentityConflict:
            return None

    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(dispatch, ["2", "3"] * 12))
    persisted = [result for result in results if result is not None]
    assert persisted
    assert all(result == persisted[0] for result in persisted)
    assert any(result is None for result in results)
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1


def test_adapter_reconnect_replays_durable_identity(engine) -> None:
    expected = adapter(engine).dispatch(intent(), grant())
    url = engine.url
    engine.dispose()
    reconnected = create_engine(url)
    try:
        assert (
            adapter(reconnected, clock=NOW + timedelta(days=1)).dispatch(
                intent(), grant(expires_at=NOW + timedelta(days=2))
            )
            == expected
        )
        with reconnected.connect() as connection:
            assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1
    finally:
        reconnected.dispose()


def test_denied_and_conflicting_transactions_rollback_then_retry(engine) -> None:
    subject = adapter(engine)
    with pytest.raises(AuthorizationDenied):
        subject.dispatch(intent(), grant(expires_at=NOW - timedelta(seconds=1)))
    expected = subject.dispatch(intent(), grant())
    with pytest.raises(IntentIdentityConflict):
        subject.dispatch(intent(quantity="3"), grant())
    assert subject.dispatch(intent(), grant()) == expected
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1
