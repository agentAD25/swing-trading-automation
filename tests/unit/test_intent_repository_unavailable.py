"""Synthetic driver-failure tests for the intent repository. No database is opened."""

from __future__ import annotations

import io
import logging
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import psycopg
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from swingtrade.broker import DryRunAdapter
from swingtrade.domain import ExecutionMode, OrderIntent, Side
from swingtrade.idempotency import input_digest
from swingtrade.persistence import (
    DurableObservationError,
    IntentIdentityConflict,
    IntentRepositoryUnavailable,
    NonCanonicalIntentKey,
    PersistedIntent,
    PostgresIntentRepository,
    canonical_dispatch_key,
    canonical_dry_run_observation,
    canonical_intent,
)
from swingtrade.safety import AuthorizationDenied, DispatchAuthorization

NOW = datetime(2024, 1, 1, tzinfo=UTC)
SECRET = "SYNTHETIC_SECRET_TOKEN_7f3a"
USER = "synth_lane4_user"
DRIVER_TEXT = (
    f"connection failed: postgresql://{USER}:{SECRET}@synthetic-db-host.invalid:5432/synthdb_lane4"
)


def _intent(*, quantity: str = "2", key: str | None = None) -> OrderIntent:
    candidate = OrderIntent(
        intent_id="int_1",
        run_id="run_1",
        decision_id="dec_1",
        instrument_id="ins_1",
        side=Side.BUY,
        quantity=Decimal(quantity),
        mode=ExecutionMode.DRY_RUN,
        idempotency_key="pending",
    )
    resolved = canonical_dispatch_key(candidate) if key is None else key
    return replace(candidate, idempotency_key=resolved)


def _engine():
    def refuse_connect(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("database connection attempted")

    return create_engine(
        f"postgresql+psycopg://{USER}:{SECRET}@127.0.0.1:9/synthdb_lane4",
        creator=refuse_connect,
    )


class _Result:
    def __init__(self, row: object) -> None:
        self._row = row

    def one_or_none(self) -> object:
        return self._row

    def one(self) -> object:
        return self._row


class _MappingRow:
    def __init__(self, persisted: PersistedIntent) -> None:
        self._mapping = {
            "idempotency_key": persisted.idempotency_key,
            "intent_id": persisted.intent_id,
            "input_digest": persisted.input_digest,
            "canonical_intent": persisted.canonical_intent,
            "canonical_observation": persisted.canonical_observation,
        }


class _Connection:
    def __init__(self, row: object, calls: list[str], *, fail: bool) -> None:
        self._row = row
        self._calls = calls
        self._fail = fail
        self._executed = 0

    def execute(self, _statement: object) -> _Result:
        self._calls.append("execute")
        self._executed += 1
        if self._fail:
            origin = psycopg.OperationalError(DRIVER_TEXT)
            raise OperationalError(DRIVER_TEXT, {}, origin)
        if self._executed == 1:
            return _Result(None)
        return _Result(self._row)


@contextmanager
def _begin(calls: list[str], *, fail_at: str, row: object = None) -> Iterator[_Connection]:
    calls.append("begin")
    if fail_at == "begin":
        raise psycopg.OperationalError(DRIVER_TEXT)
    connection = _Connection(row, calls, fail=fail_at == "execute")
    try:
        yield connection
    finally:
        if fail_at == "commit":
            calls.append("commit")
            raise psycopg.OperationalError(DRIVER_TEXT)


def _repository(calls: list[str], *, fail_at: str, row: object = None) -> PostgresIntentRepository:
    engine = _engine()

    def begin() -> Iterator[_Connection]:
        return _begin(calls, fail_at=fail_at, row=row)

    engine.begin = begin  # type: ignore[method-assign]
    return PostgresIntentRepository(engine)


def _matching_row(intent: OrderIntent) -> _MappingRow:
    payload = canonical_intent(intent)
    persisted = PersistedIntent(
        intent.idempotency_key,
        intent.intent_id,
        input_digest(payload),
        payload,
        canonical_dry_run_observation(intent, NOW),
    )
    return _MappingRow(persisted)


def _rendered(error: BaseException) -> str:
    return "".join(traceback.format_exception(type(error), error, error.__traceback__))


def _assert_sanitized(error: IntentRepositoryUnavailable) -> None:
    assert error.reason == "DATABASE_UNAVAILABLE"
    assert error.args == ("DATABASE_UNAVAILABLE",)
    assert str(error) == "DATABASE_UNAVAILABLE"
    assert SECRET not in str(error)
    assert SECRET not in repr(error)
    assert all(SECRET not in str(argument) for argument in error.args)
    assert USER not in str(error)
    assert "synthetic-db-host.invalid" not in str(error)
    assert SECRET not in _rendered(error)
    assert error.__cause__ is None
    assert error.__suppress_context__ is True


def _grant(**overrides: object) -> DispatchAuthorization:
    values: dict[str, object] = {
        "run_id": "run_1",
        "intent_id": "int_1",
        "mode": ExecutionMode.DRY_RUN,
        "build_id": "build_1",
        "environment": "local",
        "expires_at": NOW + timedelta(minutes=1),
    }
    values.update(overrides)
    return DispatchAuthorization(**values)  # type: ignore[arg-type]


def test_connection_acquisition_failure_is_sanitized() -> None:
    calls: list[str] = []
    repository = _repository(calls, fail_at="begin")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("test.intent.repository")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        repository.create_or_get(_intent(), effective_at=NOW)
    except IntentRepositoryUnavailable as error:
        _assert_sanitized(error)
        logger.exception("boundary")
    else:
        raise AssertionError("driver failure returned a row")
    finally:
        logger.removeHandler(handler)
    assert SECRET not in stream.getvalue()
    assert "DATABASE_UNAVAILABLE" in stream.getvalue()
    assert calls == ["begin"]


def test_statement_execution_failure_is_sanitized() -> None:
    calls: list[str] = []
    repository = _repository(calls, fail_at="execute")
    with pytest.raises(IntentRepositoryUnavailable) as captured:
        repository.create_or_get(_intent(), effective_at=NOW)
    _assert_sanitized(captured.value)
    assert calls == ["begin", "execute"]
    assert isinstance(captured.value.__context__, OperationalError)
    assert SECRET in str(captured.value.__context__)
    assert SECRET not in _rendered(captured.value)


def test_supplied_noncanonical_key_is_unchanged() -> None:
    calls: list[str] = []
    repository = _repository(calls, fail_at="begin")
    with pytest.raises(NonCanonicalIntentKey, match="supplied intent key does not match"):
        repository.create_or_get(_intent(key="v1:dispatch:int_1:" + "ab" * 32), effective_at=NOW)
    assert calls == []


def test_stored_noncanonical_key_is_unchanged() -> None:
    intent = _intent()
    payload = canonical_intent(intent)
    payload["quantity"] = "9"
    row = _MappingRow(
        PersistedIntent(
            intent.idempotency_key,
            intent.intent_id,
            input_digest(canonical_intent(intent)),
            payload,
            canonical_dry_run_observation(intent, NOW),
        )
    )
    calls: list[str] = []
    repository = _repository(calls, fail_at="none", row=row)
    with pytest.raises(
        NonCanonicalIntentKey,
        match="durable intent row contains a noncanonical dispatch key",
    ):
        repository.create_or_get(intent, effective_at=NOW)
    assert calls.count("begin") == 1


def test_missing_observation_is_unchanged() -> None:
    intent = _intent()
    payload = canonical_intent(intent)
    row = _MappingRow(
        PersistedIntent(
            intent.idempotency_key,
            intent.intent_id,
            input_digest(payload),
            payload,
            None,  # type: ignore[arg-type]
        )
    )
    calls: list[str] = []
    repository = _repository(calls, fail_at="none", row=row)
    with pytest.raises(DurableObservationError, match="lacks a canonical DRY_RUN observation"):
        repository.create_or_get(intent, effective_at=NOW)
    assert calls.count("begin") == 1


def test_identity_conflict_is_unchanged() -> None:
    intent = _intent()
    payload = canonical_intent(intent)
    payload["instrument_id"] = "ins_other"
    row = _MappingRow(
        PersistedIntent(
            intent.idempotency_key,
            intent.intent_id,
            input_digest(canonical_intent(intent)),
            payload,
            canonical_dry_run_observation(intent, NOW),
        )
    )
    calls: list[str] = []
    repository = _repository(calls, fail_at="none", row=row)
    with pytest.raises(IntentIdentityConflict, match="reused with different canonical intent"):
        repository.create_or_get(intent, effective_at=NOW)
    assert calls == ["begin", "execute", "execute"]


def test_successful_observation_is_unchanged() -> None:
    intent = _intent()
    calls: list[str] = []
    repository = _repository(calls, fail_at="none", row=_matching_row(intent))
    persisted = repository.create_or_get(intent, effective_at=NOW)
    assert persisted == PersistedIntent(
        intent.idempotency_key,
        intent.intent_id,
        input_digest(canonical_intent(intent)),
        canonical_intent(intent),
        canonical_dry_run_observation(intent, NOW),
    )
    adapter = DryRunAdapter(
        build_id="build_1",
        environment="local",
        clock=NOW,
        repository=repository,
    )
    observation = adapter.dispatch(intent, _grant())
    assert observation.order_id == "dry_int_1"
    assert observation.intent_id == "int_1"
    assert observation.state == "PENDING"
    assert observation.requested_quantity == Decimal("2")
    assert observation.cumulative_quantity == Decimal("0")
    assert calls.count("begin") == 2


def test_failure_does_not_retry() -> None:
    calls: list[str] = []
    repository = _repository(calls, fail_at="execute")
    with pytest.raises(IntentRepositoryUnavailable):
        repository.create_or_get(_intent(), effective_at=NOW)
    assert calls.count("begin") == 1
    assert calls.count("execute") == 1


def test_ambiguous_commit_failure_does_not_fabricate_success() -> None:
    intent = _intent()
    calls: list[str] = []
    repository = _repository(calls, fail_at="commit", row=_matching_row(intent))
    with pytest.raises(IntentRepositoryUnavailable) as captured:
        repository.create_or_get(intent, effective_at=NOW)
    _assert_sanitized(captured.value)
    assert calls.count("begin") == 1
    assert calls.count("commit") == 1
    assert calls.count("execute") == 2


def test_dispatch_propagates_sanitized_exception() -> None:
    calls: list[str] = []
    repository = _repository(calls, fail_at="begin")
    adapter = DryRunAdapter(
        build_id="build_1",
        environment="local",
        clock=NOW,
        repository=repository,
    )
    with pytest.raises(IntentRepositoryUnavailable) as captured:
        adapter.dispatch(_intent(), _grant())
    _assert_sanitized(captured.value)
    with pytest.raises(AuthorizationDenied, match="dispatch authorization denied"):
        adapter.dispatch(_intent(), _grant(reporting=True))
    assert calls == ["begin"]


def test_traceback_frame_still_reaches_the_engine_secret() -> None:
    repository = _repository([], fail_at="begin")
    with pytest.raises(IntentRepositoryUnavailable) as captured:
        repository.create_or_get(_intent(), effective_at=NOW)
    frame = captured.value.__traceback__
    password = None
    while frame is not None:
        if frame.tb_frame.f_code.co_name == "create_or_get":
            password = frame.tb_frame.f_locals["self"]._engine.url.password
        frame = frame.tb_next
    assert password == SECRET
    assert SECRET not in _rendered(captured.value)
