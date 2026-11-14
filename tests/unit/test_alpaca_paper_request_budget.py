"""Durable request-budget accounting. No credential and no provider call."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

from swingtrade.alpaca_paper_request_budget import (
    DAILY_LIMIT,
    BudgetError,
    DurableRequestBudget,
)

_EARLY = datetime(2026, 11, 14, 4, 30, tzinfo=UTC)
_LATE = datetime(2026, 11, 14, 5, 30, tzinfo=UTC)


def test_process_restart_keeps_the_same_day_count(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"
    first = DurableRequestBudget(path, lambda: _LATE)
    assert first.reserve() == 1
    second = DurableRequestBudget(path, lambda: _LATE)
    assert second.reserve() == 2
    assert second.spent() == 2


def test_new_york_day_rollover_resets_the_count(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"
    clock = {"now": _EARLY}
    ledger = DurableRequestBudget(path, lambda: clock["now"])
    assert ledger.reserve() == 1
    clock["now"] = _LATE
    assert ledger.spent() == 0
    assert ledger.reserve() == 1


def test_concurrent_reservations_stop_at_the_daily_limit(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"
    ledger = DurableRequestBudget(path, lambda: _LATE)
    with ThreadPoolExecutor(max_workers=40) as pool:
        results = list(pool.map(lambda _: _one(ledger), range(40)))
    reserved = [item for item in results if isinstance(item, int)]
    denied = [item for item in results if isinstance(item, BudgetError)]
    assert sorted(reserved) == list(range(1, DAILY_LIMIT + 1))
    assert len(denied) == 10
    assert {item.reason for item in denied} == {"BUDGET_EXHAUSTED"}
    assert ledger.spent() == DAILY_LIMIT


def test_malformed_ledger_and_naive_clock_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"
    path.write_bytes(b'{"count": true, "day": "2026-11-14"}')
    ledger = DurableRequestBudget(path, lambda: _LATE)
    with pytest.raises(BudgetError) as caught:
        ledger.reserve()
    assert caught.value.reason == "BUDGET_LEDGER_MALFORMED"
    assert b"true" in path.read_bytes()
    naive = DurableRequestBudget(tmp_path / "other.json", lambda: datetime(2026, 11, 14))
    with pytest.raises(BudgetError) as clock_error:
        naive.reserve()
    assert clock_error.value.reason == "BUDGET_CLOCK_DENIED"
    assert not (tmp_path / "other.json").exists()


def _one(ledger: DurableRequestBudget) -> int | BudgetError:
    try:
        return ledger.reserve()
    except BudgetError as error:
        return error
