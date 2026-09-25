from datetime import date
from pathlib import Path

import pytest

from swingtrade.domain import Bar
from swingtrade.wdc import FixtureError, evaluate_daily_close_breakout, load_wdc_fixture

FIXTURE = Path(__file__).parents[1] / "fixtures" / "wdc-reference"


def bar(session: str, high: str, close: str) -> Bar:
    return Bar(
        "ins_1",
        "WDC",
        "1d",
        date.fromisoformat(session),
        "10",
        high,
        "9",
        close,
        "100",
        "USD",
        "fixture",
        1,
    )


def test_accepted_wdc_fixture_loads_and_preserves_bytes() -> None:
    fixture = load_wdc_fixture(FIXTURE)
    assert fixture.event_bytes == (FIXTURE / "expected-events.jsonl").read_bytes()
    assert fixture.report_bytes == (FIXTURE / "expected-report.json").read_bytes()
    assert fixture.report["reconciliation_result"] == "UNRECONCILED"


def test_daily_close_only_and_rolling_prior_trading_day_high() -> None:
    bars = (
        bar("2024-01-05", "12", "11"),
        bar("2024-01-08", "13", "11.5"),  # intraday > 12, close does not trigger
        bar("2024-01-09", "14", "13.5"),  # close > rolling prior high 13
    )
    calendar = tuple(item.session_date for item in bars)
    signals = evaluate_daily_close_breakout(bars, calendar)
    assert [(item.prior_trading_day_high, item.triggered) for item in signals] == [
        ("12", False),
        ("13", True),
    ]


def test_duplicate_calendar_input_is_rejected() -> None:
    duplicate = bar("2024-01-05", "12", "11")
    with pytest.raises(FixtureError, match="one-to-one"):
        evaluate_daily_close_breakout(
            (duplicate, duplicate),
            (date(2024, 1, 5), date(2024, 1, 5)),
        )
