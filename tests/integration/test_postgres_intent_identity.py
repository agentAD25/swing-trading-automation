from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select, text

from swingtrade.domain import ExecutionMode, OrderIntent, Side
from swingtrade.persistence import (
    IntentIdentityConflict,
    OrderIntentRow,
    PostgresIntentRepository,
)

POSTGRES_URL = os.getenv("SWINGTRADE_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="SWINGTRADE_TEST_POSTGRES_URL is required"
)


def make_intent(*, quantity: str = "2", key: str = "v1:dispatch:int_1:" + "a" * 64) -> OrderIntent:
    return OrderIntent(
        intent_id="int_1",
        run_id="run_1",
        decision_id="dec_1",
        instrument_id="ins_1",
        side=Side.BUY,
        quantity=Decimal(quantity),
        mode=ExecutionMode.DRY_RUN,
        idempotency_key=key,
    )


@pytest.fixture
def engine():
    assert POSTGRES_URL is not None
    value = create_engine(POSTGRES_URL, pool_size=12, max_overflow=4)
    with value.begin() as connection:
        version = connection.execute(text("SHOW server_version")).scalar_one()
        assert version
        connection.execute(text("TRUNCATE TABLE order_intents"))
    yield value
    value.dispose()


def test_same_canonical_intent_converges_and_conflict_rolls_back(engine) -> None:
    repository = PostgresIntentRepository(engine)
    first = repository.create_or_get(make_intent())
    assert repository.create_or_get(make_intent()) == first

    with pytest.raises(IntentIdentityConflict):
        repository.create_or_get(make_intent(quantity="3"))

    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1
        persisted = connection.execute(select(OrderIntentRow)).scalar_one()
        assert persisted.input_digest == first.input_digest


def test_concurrent_creators_produce_one_durable_identity(engine) -> None:
    repository = PostgresIntentRepository(engine)
    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(lambda _: repository.create_or_get(make_intent()), range(24)))
    assert len(set(results)) == 1
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1


def test_persistence_survives_pool_disposal_and_reconnect(engine) -> None:
    expected = PostgresIntentRepository(engine).create_or_get(make_intent())
    url = engine.url
    engine.dispose()
    reconnected = create_engine(url)
    try:
        assert PostgresIntentRepository(reconnected).create_or_get(make_intent()) == expected
    finally:
        reconnected.dispose()
