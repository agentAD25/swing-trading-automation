from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, insert, select, text

from swingtrade.domain import ExecutionMode, OrderIntent, Side
from swingtrade.persistence import (
    IntentIdentityConflict,
    NonCanonicalIntentKey,
    OrderIntentRow,
    PostgresIntentRepository,
    canonical_dispatch_key,
    canonical_intent,
)
from swingtrade.idempotency import input_digest

POSTGRES_URL = os.getenv("SWINGTRADE_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="SWINGTRADE_TEST_POSTGRES_URL is required"
)


def make_intent(*, quantity: str = "2", key: str | None = None) -> OrderIntent:
    candidate = OrderIntent(
        intent_id="int_1",
        run_id="run_1",
        decision_id="dec_1",
        instrument_id="ins_1",
        side=Side.BUY,
        quantity=Decimal(quantity),
        mode=ExecutionMode.DRY_RUN,
        idempotency_key="",
    )
    return replace(
        candidate,
        idempotency_key=canonical_dispatch_key(candidate) if key is None else key,
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
        persisted = connection.execute(select(OrderIntentRow)).one()
        assert persisted._mapping["input_digest"] == first.input_digest


def test_forged_key_fails_before_persistence_and_changed_economic_intent_conflicts(
    engine,
) -> None:
    repository = PostgresIntentRepository(engine)
    forged = make_intent(key="v1:dispatch:int_1:" + "f" * 64)
    with pytest.raises(NonCanonicalIntentKey):
        repository.create_or_get(forged)
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 0

    repository.create_or_get(make_intent())
    with pytest.raises(IntentIdentityConflict):
        repository.create_or_get(make_intent(quantity="3"))
    with pytest.raises(NonCanonicalIntentKey):
        repository.create_or_get(
            make_intent(quantity="3", key=make_intent().idempotency_key)
        )
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1


def test_existing_noncanonical_durable_row_fails_closed(engine) -> None:
    forged = make_intent(key="v1:dispatch:int_1:" + "f" * 64)
    payload = canonical_intent(forged)
    with engine.begin() as connection:
        connection.execute(
            insert(OrderIntentRow).values(
                idempotency_key=forged.idempotency_key,
                intent_id=forged.intent_id,
                input_digest=input_digest(payload),
                canonical_intent=payload,
            )
        )
    with pytest.raises(NonCanonicalIntentKey):
        PostgresIntentRepository(engine).create_or_get(make_intent())
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1


def test_concurrent_creators_produce_one_durable_identity(engine) -> None:
    repository = PostgresIntentRepository(engine)
    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(lambda _: repository.create_or_get(make_intent()), range(24)))
    assert all(result == results[0] for result in results)
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1


def test_concurrent_forged_keys_fail_without_durable_rows(engine) -> None:
    repository = PostgresIntentRepository(engine)

    def create(index: int) -> None:
        repository.create_or_get(
            make_intent(key=f"v1:dispatch:int_1:{index:064x}")
        )

    with ThreadPoolExecutor(max_workers=12) as executor:
        attempts = [executor.submit(create, index) for index in range(1, 25)]
    assert all(isinstance(attempt.exception(), NonCanonicalIntentKey) for attempt in attempts)
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 0


def test_concurrent_conflicting_creators_choose_one_identity(engine) -> None:
    repository = PostgresIntentRepository(engine)

    def create(quantity: str):
        try:
            return repository.create_or_get(make_intent(quantity=quantity))
        except IntentIdentityConflict:
            return None

    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(create, ["2", "3"] * 12))
    persisted = [result for result in results if result is not None]
    assert persisted
    assert all(result == persisted[0] for result in persisted)
    assert any(result is None for result in results)
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
