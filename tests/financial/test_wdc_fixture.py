import hashlib
import json
import shutil
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

import swingtrade.domain as domain
from swingtrade.domain import Bar, DomainValidationError
from swingtrade.wdc import FixtureError, evaluate_daily_close_protective, load_wdc_fixture

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


@pytest.mark.parametrize(
    "raw",
    [
        "9" * 1_000_000,
        "0." + "9" * 1_000_000,
        "1e" + "9" * 1_000_000,
        "1e1000000",
        " 2",
        "2 ",
        "1_0",
        "NaN",
        "sNaN",
        "Infinity",
    ],
)
def test_wdc_decimal_attacks_never_enter_decimal_constructor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raw: str
) -> None:
    root = tmp_path / "wdc-reference"
    shutil.copytree(FIXTURE, root)
    bars_path = root / "bars.csv"
    lines = bars_path.read_text().splitlines()
    first_row = lines[1].split(",")
    first_row[4] = raw
    lines[1] = ",".join(first_row)
    bars_path.write_text("\n".join(lines) + "\n")
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["sha256"]["bars.csv"] = hashlib.sha256(bars_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))

    constructor_called = False

    def forbidden_constructor(value: object) -> Decimal:
        nonlocal constructor_called
        constructor_called = True
        raise AssertionError("Decimal constructor must not be called")

    monkeypatch.setattr(domain, "Decimal", forbidden_constructor)
    with pytest.raises(DomainValidationError):
        load_wdc_fixture(root)
    assert not constructor_called


def test_daily_close_only_and_rolling_prior_trading_day_high() -> None:
    bars = (
        bar("2024-01-05", "12", "11"),
        bar("2024-01-08", "13", "11.5"),  # intraday > 12, close does not trigger
        bar("2024-01-09", "14", "13.5"),  # close > rolling prior high 13
    )
    calendar = tuple(item.session_date for item in bars)
    signals = evaluate_daily_close_protective(bars, calendar)
    assert [(item.prior_trading_day_high, item.triggered) for item in signals] == [
        ("12", False),
        ("13", True),
    ]


def test_duplicate_calendar_input_is_rejected() -> None:
    duplicate = bar("2024-01-05", "12", "11")
    with pytest.raises(FixtureError, match="unique ascending"):
        evaluate_daily_close_protective(
            (duplicate, duplicate),
            (date(2024, 1, 5), date(2024, 1, 5)),
        )


def test_unsorted_or_cardinality_mismatched_sessions_are_rejected() -> None:
    friday = bar("2024-01-05", "12", "11")
    monday = bar("2024-01-08", "13", "12.5")
    with pytest.raises(FixtureError, match="unique ascending"):
        evaluate_daily_close_protective(
            (monday, friday), (date(2024, 1, 8), date(2024, 1, 5))
        )
    with pytest.raises(FixtureError, match="exactly match"):
        evaluate_daily_close_protective((friday,), (date(2024, 1, 5), date(2024, 1, 8)))


def test_supplied_calendar_defines_weekend_and_holiday_adjacency() -> None:
    # No weekday/holiday policy is inferred: adjacency comes only from the supplied sessions.
    bars = (
        bar("2024-01-12", "12", "11"),
        bar("2024-01-16", "13", "12.5"),
        bar("2024-01-17", "14", "13.5"),
    )
    sessions = tuple(item.session_date for item in bars)
    signals = evaluate_daily_close_protective(bars, sessions)
    assert [signal.session_date for signal in signals] == [
        date(2024, 1, 16),
        date(2024, 1, 17),
    ]
    assert [signal.prior_trading_day_high for signal in signals] == ["12", "13"]


def test_prior_next_session_and_replay_are_deterministic() -> None:
    bars = (
        bar("2024-01-05", "12", "11"),
        bar("2024-01-08", "13", "12.5"),
        bar("2024-01-09", "14", "13.5"),
    )
    sessions = tuple(item.session_date for item in bars)
    first = evaluate_daily_close_protective(bars, sessions)
    second = evaluate_daily_close_protective(bars, sessions)
    assert first == second
    assert first[1].prior_trading_day_high == str(bars[1].high)
