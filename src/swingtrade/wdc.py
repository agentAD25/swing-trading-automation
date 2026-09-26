from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from swingtrade.domain import Bar, decimal_value
from swingtrade.idempotency import canonical_json, idempotency_key
from swingtrade.reconciliation import derive_reconciliation_result


class FixtureError(ValueError):
    """The immutable fixture or its declared semantics are invalid."""


@dataclass(frozen=True)
class DailyCloseSignal:
    session_date: date
    prior_trading_day_high: str
    close: str
    triggered: bool


@dataclass(frozen=True)
class WdcFixture:
    scenario: dict[str, Any]
    bars: tuple[Bar, ...]
    events: tuple[dict[str, Any], ...]
    report: dict[str, Any]
    event_bytes: bytes
    report_bytes: bytes


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_wdc_fixture(root: Path) -> WdcFixture:
    manifest = json.loads((root / "manifest.json").read_bytes())
    raw = {name: (root / name).read_bytes() for name in manifest["sha256"]}
    for name, expected in manifest["sha256"].items():
        if _digest(raw[name]) != expected:
            raise FixtureError(f"{name}: manifest digest mismatch")

    scenario = json.loads(raw["scenario.json"])
    report = json.loads(raw["expected-report.json"])
    events = tuple(json.loads(line) for line in raw["expected-events.jsonl"].splitlines())
    rows = list(csv.DictReader(raw["bars.csv"].decode().splitlines()))
    bars = tuple(
        Bar(
            instrument_id=row["instrument_id"],
            symbol=row["symbol"],
            interval=row["interval"],
            session_date=date.fromisoformat(row["session_date"]),
            open=decimal_value(row["open"]),
            high=decimal_value(row["high"]),
            low=decimal_value(row["low"]),
            close=decimal_value(row["close"]),
            volume=decimal_value(row["volume"]),
            currency=row["currency"],
            source=row["source"],
            revision=int(row["revision"]),
        )
        for row in rows
    )
    _validate_fixture(scenario, bars, events, report)
    return WdcFixture(
        scenario, bars, events, report, raw["expected-events.jsonl"], raw["expected-report.json"]
    )


def _validate_fixture(
    scenario: dict[str, Any],
    bars: tuple[Bar, ...],
    events: tuple[dict[str, Any], ...],
    report: dict[str, Any],
) -> None:
    sessions = tuple(date.fromisoformat(value) for value in scenario["calendar"]["sessions"])
    _validate_calendar(bars, sessions)
    signal_index = next(
        (index for index, bar in enumerate(bars) if bar.close > bar.open),
        None,
    )
    if signal_index is None or signal_index + 3 >= len(bars):
        raise FixtureError("fixture rule cannot select entry and exit sessions")
    entry, exit_ = bars[signal_index + 1], bars[signal_index + 3]
    if (
        report["entry"]["session_date"] != entry.session_date.isoformat()
        or report["entry"]["price"] != f"{entry.open:.4f}"
        or report["exit"]["session_date"] != exit_.session_date.isoformat()
        or report["exit"]["price"] != f"{exit_.open:.4f}"
    ):
        raise FixtureError("report contradicts deterministic calendar evaluation")
    for name, operation, scope in (
        ("entry_dispatch", "dispatch", scenario["ids"]["entry_intent_id"]),
        ("exit_dispatch", "dispatch", scenario["ids"]["exit_intent_id"]),
        ("report", "report", scenario["ids"]["run_id"]),
    ):
        expected = idempotency_key(operation, scope, scenario["idempotency_inputs"][name])
        matching = {
            event["idempotency_key"]
            for event in events
            if event.get("idempotency_key") == expected
        }
        if matching != {expected}:
            raise FixtureError(f"{name}: idempotency evidence mismatch")
    body = dict(report)
    claimed_digest = body.pop("content_digest")
    if _digest(canonical_json(body)) != claimed_digest:
        raise FixtureError("report content digest mismatch")
    if (
        derive_reconciliation_result(events, report["source_high_water_mark"], report["run_id"])
        != report["reconciliation_result"]
    ):
        raise FixtureError("report reconciliation evidence mismatch")


def evaluate_daily_close_protective(
    bars: tuple[Bar, ...], calendar_sessions: tuple[date, ...]
) -> tuple[DailyCloseSignal, ...]:
    """Evaluate a protective breakout only at close against prior-session high."""
    _validate_calendar(bars, calendar_sessions)
    by_session = {bar.session_date: bar for bar in bars}
    signals = []
    for prior_session, session in zip(calendar_sessions, calendar_sessions[1:], strict=False):
        prior, current = by_session[prior_session], by_session[session]
        signals.append(
            DailyCloseSignal(
                session_date=session,
                prior_trading_day_high=str(prior.high),
                close=str(current.close),
                triggered=current.close > prior.high,
            )
        )
    return tuple(signals)


def _validate_calendar(bars: tuple[Bar, ...], calendar_sessions: tuple[date, ...]) -> None:
    actual_sessions = tuple(bar.session_date for bar in bars)
    if (
        not calendar_sessions
        or len(actual_sessions) != len(calendar_sessions)
        or len(set(actual_sessions)) != len(actual_sessions)
        or len(set(calendar_sessions)) != len(calendar_sessions)
        or tuple(sorted(calendar_sessions)) != calendar_sessions
        or actual_sessions != calendar_sessions
    ):
        raise FixtureError(
            "bars must exactly match unique ascending supplied trading-calendar sessions"
        )


evaluate_daily_close_breakout = evaluate_daily_close_protective
