from __future__ import annotations

import builtins
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, insert, select, text

from swingtrade.domain import DomainValidationError, ExecutionMode, OrderIntent, Side
from swingtrade.idempotency import idempotency_key, input_digest
from swingtrade.persistence import (
    MAX_CANONICAL_DECIMAL_DIGIT_POSITIONS,
    DurableObservationError,
    IntentIdentityConflict,
    NonCanonicalIntentKey,
    OrderIntentRow,
    PostgresIntentRepository,
    canonical_decimal,
    canonical_dispatch_key,
    canonical_dry_run_observation,
    canonical_intent,
)

POSTGRES_URL = os.getenv("SWINGTRADE_TEST_POSTGRES_URL")
NOW = datetime(2024, 1, 1, tzinfo=UTC)
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="SWINGTRADE_TEST_POSTGRES_URL is required"
)


def make_intent(
    *,
    decision_id: str = "dec_1",
    intent_id: str = "int_1",
    mode: ExecutionMode = ExecutionMode.DRY_RUN,
    quantity: str = "2",
    side: Side = Side.BUY,
    key: str | None = None,
) -> OrderIntent:
    candidate = OrderIntent(
        intent_id=intent_id,
        run_id="run_1",
        decision_id=decision_id,
        instrument_id="ins_1",
        side=side,
        quantity=Decimal(quantity),
        mode=mode,
        idempotency_key="",
    )
    return replace(
        candidate,
        idempotency_key=canonical_dispatch_key(candidate) if key is None else key,
    )


def create(repository: PostgresIntentRepository, value: OrderIntent):
    return repository.create_or_get(value, effective_at=NOW)


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
    first = create(repository, make_intent())
    assert create(repository, make_intent(quantity="2.0")) == first
    assert create(repository, make_intent(quantity="2.00")) == first

    with pytest.raises(IntentIdentityConflict):
        create(repository, make_intent(quantity="3"))

    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1
        persisted = connection.execute(select(OrderIntentRow)).one()
        assert persisted._mapping["input_digest"] == first.input_digest


@pytest.mark.parametrize(
    ("variants", "expected"),
    [
        (("2", "2.0", "2.00"), "2"),
        (("0", "0.0", "-0.00", "0E+9"), "0"),
        (("426.59", "426.590", "42659E-2"), "426.59"),
        (("-2", "-2.0", "-2.00"), "-2"),
        (("-426.59", "-426.590", "-42659E-2"), "-426.59"),
        (("1E+2", "100", "100.0"), "100"),
        (("1E-2", "0.01", "0.010"), "0.01"),
        (("-1E+2", "-100", "-100.00"), "-100"),
        (("-1E-2", "-0.01", "-0.010"), "-0.01"),
    ],
)
def test_canonical_decimal_collapses_only_economic_scale(
    variants: tuple[str, ...], expected: str
) -> None:
    assert {canonical_decimal(value) for value in variants} == {expected}


@pytest.mark.parametrize(
    ("value", "expected_length"),
    [
        ("1E+998", 999),
        ("1E+999", 1000),
        ("1E-998", 1000),
        ("1E-999", 1001),
        ("9.99E+999", 1000),
        ("9.99E-997", 1001),
        ("-" + "9" * 999, 1000),
        ("9" * 1000, 1000),
    ],
)
def test_canonical_decimal_boundary_minus_one_and_exact(
    value: str, expected_length: int
) -> None:
    result = canonical_decimal(value)
    assert len(result) == expected_length
    assert "E" not in result
    assert len(result.replace("-", "").replace(".", "")) <= (
        MAX_CANONICAL_DECIMAL_DIGIT_POSITIONS
    )


@pytest.mark.parametrize(
    "value",
    [
        "1E+1000",
        "1E-1000",
        "9.99E+1000",
        "9.99E-998",
        "9" * 1001,
        "1" + "0" * 1000 + "E-1000",
    ],
)
def test_canonical_decimal_boundary_plus_one_rejects_with_bounded_metadata(
    value: str,
) -> None:
    with pytest.raises(DomainValidationError) as captured:
        canonical_decimal(value)
    message = str(captured.value)
    assert len(message) < 200
    assert value not in message


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0002.000", "2"),
        ("-0002.000", "-2"),
        ("+000426.59000", "426.59"),
        ("-0", "0"),
        ("-0.000", "0"),
        ("0E+2", "0"),
        ("-0E-2", "0"),
    ],
)
def test_canonical_decimal_preserves_safe_sign_zero_and_zero_padding(
    value: str, expected: str
) -> None:
    assert canonical_decimal(value) == expected


@pytest.mark.parametrize(
    ("value", "accepted"),
    [
        ("1E+100", True),
        ("1E-100", True),
        ("1E+1000", False),
        ("1E-1000", False),
        ("1E+100000", False),
        ("1E-100000", False),
        ("1E+1000000", False),
        ("1E-1000000", False),
        ("9.99E+100", True),
        ("9.99E-100", True),
        ("9.99E+1000", False),
        ("9.99E-1000", False),
        ("-1E+1000000", False),
        ("-1E-1000000", False),
    ],
)
def test_extreme_exponent_matrix_is_bounded(value: str, accepted: bool) -> None:
    if accepted:
        assert "E" not in canonical_decimal(value)
    else:
        with pytest.raises(DomainValidationError) as captured:
            canonical_decimal(value)
        assert len(str(captured.value)) < 300
        assert value not in str(captured.value)


@pytest.mark.parametrize("value", ["NaN", "sNaN", "Infinity", "-Infinity"])
def test_nonfinite_decimal_values_fail_domain_validation(value: str) -> None:
    with pytest.raises(DomainValidationError, match="finite"):
        canonical_decimal(value)


def test_extreme_rejection_occurs_before_fixed_point_formatting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_format(value: object, format_spec: str = "") -> str:
        raise AssertionError("format must not run for rejected values")

    monkeypatch.setattr(builtins, "format", forbidden_format)
    with pytest.raises(DomainValidationError, match="resource bound"):
        canonical_decimal(Decimal("1E+1000000"))


def test_decimal_subclass_is_rejected_before_spoofed_tuple_or_format() -> None:
    class SpoofDecimal(Decimal):
        def as_tuple(self):
            return Decimal("1E+1000000").as_tuple()

        def __format__(self, format_spec: str) -> str:
            return "spoofed"

    with pytest.raises(DomainValidationError, match="exactly Decimal or str"):
        canonical_decimal(SpoofDecimal("2.00"))


def test_trailing_zero_coefficient_formats_only_bounded_canonical_tuple(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_format = builtins.format
    formatted_positions: list[int] = []

    def guarded_format(value: object, format_spec: str = "") -> str:
        if isinstance(value, Decimal) and format_spec == "f":
            _, digits, exponent = value.as_tuple()
            assert isinstance(exponent, int)
            positions = (
                len(digits) + exponent
                if exponent >= 0
                else max(len(digits), 1 - exponent)
            )
            formatted_positions.append(positions)
            assert positions <= MAX_CANONICAL_DECIMAL_DIGIT_POSITIONS
        return original_format(value, format_spec)

    monkeypatch.setattr(builtins, "format", guarded_format)
    value = "1" + "0" * 999 + "E-1500"
    result = canonical_decimal(value)
    assert result == "0." + "0" * 500 + "1"
    assert len(result.replace(".", "")) == 502
    assert formatted_positions == [502]


def test_equal_scale_keys_and_payloads_match_but_nearby_value_remains_distinct() -> None:
    equivalent = [make_intent(quantity=value) for value in ("426.59", "426.590", "42659E-2")]
    assert len({canonical_dispatch_key(value) for value in equivalent}) == 1
    assert len({input_digest(canonical_intent(value)) for value in equivalent}) == 1
    assert canonical_dispatch_key(make_intent(quantity="426.5901")) != canonical_dispatch_key(
        equivalent[0]
    )


@pytest.mark.parametrize("quantity", ["1E+1000", "1E-1000", "9" * 1001])
def test_repository_rejects_extreme_decimal_before_row(engine, quantity: str) -> None:
    extreme = OrderIntent(
        intent_id="int_1",
        run_id="run_1",
        decision_id="dec_1",
        instrument_id="ins_1",
        side=Side.BUY,
        quantity=Decimal(quantity),
        mode=ExecutionMode.DRY_RUN,
        idempotency_key="v1:dispatch:int_1:" + "f" * 64,
    )
    with pytest.raises(DomainValidationError, match="resource bound"):
        create(PostgresIntentRepository(engine), extreme)
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 0


def test_legacy_scale_sensitive_supplied_key_fails_before_persistence(engine) -> None:
    value = make_intent(quantity="2.00")
    legacy_input = {
        **canonical_intent(value),
        "quantity": "2.00",
    }
    legacy_business_input = {
        field: legacy_input[field]
        for field in ("decision_id", "intent_id", "mode", "quantity", "side")
    }
    forged = replace(
        value,
        idempotency_key=idempotency_key("dispatch", value.intent_id, legacy_business_input),
    )
    with pytest.raises(NonCanonicalIntentKey):
        create(PostgresIntentRepository(engine), forged)
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 0


def test_stale_scale_sensitive_row_is_reported_without_alias_or_rewrite(engine) -> None:
    valid = make_intent(quantity="2")
    stale_payload = canonical_intent(valid)
    stale_payload["quantity"] = "2.00"
    stale_input = {
        field: stale_payload[field]
        for field in ("decision_id", "intent_id", "mode", "quantity", "side")
    }
    stale_key = idempotency_key("dispatch", valid.intent_id, stale_input)
    stale_payload["idempotency_key"] = stale_key
    stale_observation = canonical_dry_run_observation(valid, NOW)
    stale_observation["requested_quantity"] = "2.00"
    with engine.begin() as connection:
        connection.execute(
            insert(OrderIntentRow).values(
                idempotency_key=stale_key,
                intent_id=valid.intent_id,
                input_digest=input_digest(stale_payload),
                canonical_intent=stale_payload,
                canonical_observation=stale_observation,
            )
        )
    with pytest.raises(NonCanonicalIntentKey, match="stale noncanonical decimal"):
        create(PostgresIntentRepository(engine), valid)
    with engine.connect() as connection:
        row = connection.execute(select(OrderIntentRow)).one()._mapping
        assert row["idempotency_key"] == stale_key
        assert row["canonical_intent"] == stale_payload
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1


def test_forged_key_fails_before_persistence_and_changed_economic_intent_conflicts(
    engine,
) -> None:
    repository = PostgresIntentRepository(engine)
    forged = make_intent(key="v1:dispatch:int_1:" + "f" * 64)
    with pytest.raises(NonCanonicalIntentKey):
        create(repository, forged)
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 0

    create(repository, make_intent())
    with pytest.raises(IntentIdentityConflict):
        create(repository, make_intent(quantity="3"))
    with pytest.raises(NonCanonicalIntentKey):
        create(
            repository,
            make_intent(quantity="3", key=make_intent().idempotency_key)
        )
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1


@pytest.mark.parametrize(
    "changed",
    [
        {"decision_id": "dec_other"},
        {"intent_id": "int_other"},
        {"mode": ExecutionMode.SIM},
        {"quantity": "3"},
        {"side": Side.SELL},
    ],
)
def test_each_canonical_dispatch_field_rejects_a_stale_supplied_key(
    engine, changed: dict[str, object]
) -> None:
    original_key = make_intent().idempotency_key
    with pytest.raises(NonCanonicalIntentKey):
        create(
            PostgresIntentRepository(engine),
            make_intent(key=original_key, **changed),  # type: ignore[arg-type]
        )
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 0


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
        create(PostgresIntentRepository(engine), make_intent())
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1


def test_malformed_existing_canonical_payload_raises_typed_failure(engine) -> None:
    valid = make_intent()
    malformed = ["not", "an", "object"]
    with engine.begin() as connection:
        connection.execute(
            insert(OrderIntentRow).values(
                idempotency_key=valid.idempotency_key,
                intent_id=valid.intent_id,
                input_digest=input_digest(malformed),
                canonical_intent=malformed,
                canonical_observation={},
            )
        )
    with pytest.raises(NonCanonicalIntentKey):
        create(PostgresIntentRepository(engine), valid)


def test_malformed_existing_observation_raises_typed_failure(engine) -> None:
    valid = make_intent()
    payload = canonical_intent(valid)
    with engine.begin() as connection:
        connection.execute(
            insert(OrderIntentRow).values(
                idempotency_key=valid.idempotency_key,
                intent_id=valid.intent_id,
                input_digest=input_digest(payload),
                canonical_intent=payload,
                canonical_observation={},
            )
        )
    with pytest.raises(DurableObservationError):
        create(PostgresIntentRepository(engine), valid)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("cumulative_quantity", "bogus"),
        ("cumulative_quantity", "0.0"),
        ("cumulative_quantity", "-0"),
        ("cumulative_quantity", "00"),
        ("requested_quantity", "bogus"),
        ("requested_quantity", "2.0"),
        ("effective_at", "2024-01-01T00:00:00Z"),
        ("state", "FILLED"),
    ],
)
def test_noncanonical_existing_observation_values_raise_typed_failure(
    engine, field: str, value: str
) -> None:
    valid = make_intent()
    payload = canonical_intent(valid)
    observation = canonical_dry_run_observation(valid, NOW)
    observation[field] = value
    with engine.begin() as connection:
        connection.execute(
            insert(OrderIntentRow).values(
                idempotency_key=valid.idempotency_key,
                intent_id=valid.intent_id,
                input_digest=input_digest(payload),
                canonical_intent=payload,
                canonical_observation=observation,
            )
        )
    with pytest.raises(DurableObservationError):
        create(PostgresIntentRepository(engine), valid)


def test_concurrent_creators_produce_one_durable_identity(engine) -> None:
    repository = PostgresIntentRepository(engine)
    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(lambda _: create(repository, make_intent()), range(24)))
    assert all(result == results[0] for result in results)
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1


def test_concurrent_equivalent_scales_converge_to_one_durable_identity(engine) -> None:
    repository = PostgresIntentRepository(engine)
    quantities = ["2", "2.0", "2.00"] * 8
    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(
            executor.map(
                lambda quantity: create(repository, make_intent(quantity=quantity)),
                quantities,
            )
        )
    assert all(result == results[0] for result in results)
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OrderIntentRow)) == 1
        row = connection.execute(select(OrderIntentRow)).one()._mapping
        assert row["canonical_intent"]["quantity"] == "2"


def test_concurrent_forged_keys_fail_without_durable_rows(engine) -> None:
    repository = PostgresIntentRepository(engine)

    def create(index: int) -> None:
        repository.create_or_get(
            make_intent(key=f"v1:dispatch:int_1:{index:064x}"),
            effective_at=NOW,
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
            return repository.create_or_get(
                make_intent(quantity=quantity), effective_at=NOW
            )
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
    expected = create(PostgresIntentRepository(engine), make_intent())
    url = engine.url
    engine.dispose()
    reconnected = create_engine(url)
    try:
        assert (
            PostgresIntentRepository(reconnected).create_or_get(
                make_intent(quantity="2.00"), effective_at=NOW + timedelta(days=1)
            )
            == expected
        )
    finally:
        reconnected.dispose()
