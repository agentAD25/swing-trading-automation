"""Ledger attacks. Files are disposable and contain no credentials."""

from __future__ import annotations

import inspect
import os
import stat
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from swingtrade.alpaca_paper_grant import GrantError, authorize_production
from swingtrade.alpaca_paper_request_budget import (
    DAILY_LIMIT,
    BoundLedger,
    BudgetError,
    initialize_for_production,
    posix_mode_rejected,
    reserve_for_production,
)
from tests.unit.test_alpaca_paper_support import LEDGER, WHEN, issue, prepare

_EARLY = datetime(2026, 11, 14, 4, 30, tzinfo=UTC)
_LATE = datetime(2026, 11, 14, 5, 30, tzinfo=UTC)
_NEW_YORK = ZoneInfo("America/New_York")


def test_production_reserve_has_no_caller_path() -> None:
    assert inspect.signature(reserve_for_production).parameters == {}
    assert inspect.signature(initialize_for_production).parameters == {}
    with pytest.raises(GrantError) as caught:
        reserve_for_production()
    assert caught.value.reason == "GRANT_ANCHOR_ABSENT"
    with pytest.raises(GrantError) as provisioning:
        initialize_for_production()
    assert provisioning.value.reason == "GRANT_ANCHOR_ABSENT"
    with pytest.raises(GrantError) as inactive:
        authorize_production()
    assert inactive.value.reason == "GRANT_ANCHOR_ABSENT"


def test_restart_keeps_the_count_and_a_new_instance_cannot_reset(tmp_path: Path) -> None:
    grant, first = prepare(tmp_path / LEDGER)
    assert first.reserve(grant, WHEN) == 1
    second = BoundLedger(tmp_path / LEDGER)
    assert second.spent(grant, WHEN) == 1
    assert second.reserve(grant, WHEN) == 2


def test_alternate_missing_empty_truncated_and_replaced_ledgers_fail(tmp_path: Path) -> None:
    grant, ledger = prepare(tmp_path / LEDGER)
    assert ledger.reserve(grant, WHEN) == 1
    original = _body(tmp_path)
    alternate = BoundLedger(tmp_path / "elsewhere" / LEDGER)
    (tmp_path / "elsewhere").mkdir()
    _deny(lambda: alternate.reserve(grant, WHEN), "LEDGER_MISSING")
    assert ledger.spent(grant, WHEN) == 1
    other = issue(ledger_id="ledger0002")
    _deny(lambda: ledger.reserve(other, WHEN), "LEDGER_BINDING_MISMATCH")
    _deny(lambda: BoundLedger(tmp_path / "ledger0002").reserve(other, WHEN), "LEDGER_MISSING")
    assert _body(tmp_path) == original
    (tmp_path / LEDGER / "ledger.json").unlink()
    _deny(lambda: ledger.reserve(grant, WHEN), "LEDGER_MISSING")
    (tmp_path / LEDGER / "ledger.json").write_bytes(original)
    (tmp_path / LEDGER / "ledger.json").write_bytes(b"   ")
    _deny(lambda: ledger.reserve(grant, WHEN), "LEDGER_MALFORMED")
    (tmp_path / LEDGER / "ledger.json").write_bytes(b'{"count":')
    _deny(lambda: ledger.reserve(grant, WHEN), "LEDGER_MALFORMED")
    (tmp_path / LEDGER / "ledger.json").write_bytes(original)
    (tmp_path / LEDGER / "ledger.high").write_bytes(b"replaced\n")
    _deny(lambda: ledger.reserve(grant, WHEN), "LEDGER_REPLACED")
    assert _body(tmp_path) == original
    _deny(lambda: ledger.spent(grant, WHEN), "LEDGER_REPLACED")


def test_permissions_symlink_and_clock_rollback_do_not_rewrite(tmp_path: Path) -> None:
    grant, ledger = prepare(tmp_path / LEDGER)
    assert ledger.reserve(grant, WHEN) == 1
    original = _body(tmp_path)
    _deny(lambda: ledger.reserve(grant, _EARLY), "CLOCK_ROLLBACK")
    assert _body(tmp_path) == original
    assert posix_mode_rejected(0o666) is True
    assert posix_mode_rejected(0o600) is False
    json_path = tmp_path / LEDGER / "ledger.json"
    if sys.platform == "win32":
        os.chmod(json_path, stat.S_IREAD)
    else:
        os.chmod(json_path, 0o666)
    try:
        _deny(lambda: ledger.reserve(grant, WHEN), "LEDGER_PERMISSION_DENIED")
    finally:
        os.chmod(json_path, stat.S_IWRITE | stat.S_IREAD)
    assert _body(tmp_path) == original


def test_symlink_or_junction_replacement_is_rejected(tmp_path: Path) -> None:
    grant, ledger = prepare(tmp_path / LEDGER)
    assert ledger.reserve(grant, WHEN) == 1
    kind = _substitution(tmp_path)
    if kind is None:
        pytest.skip("symlink and junction creation are unavailable")
    if kind == "file":
        _deny(lambda: ledger.reserve(grant, WHEN), "LEDGER_SUBSTITUTED")
        return
    linked = BoundLedger(tmp_path / "linkparent" / LEDGER)
    _deny(lambda: linked.reserve(grant, WHEN), "LEDGER_SUBSTITUTED")
    assert ledger.spent(grant, WHEN) == 1


def test_midnight_and_dst_use_new_york_dates(tmp_path: Path) -> None:
    assert _EARLY.astimezone(_NEW_YORK).date().isoformat() == "2026-11-13"
    assert _LATE.astimezone(_NEW_YORK).date().isoformat() == "2026-11-14"
    grant = issue()
    ledger = BoundLedger(tmp_path / LEDGER)
    ledger.initialize(grant, _EARLY)
    assert ledger.reserve(grant, _EARLY) == 1
    assert ledger.reserve(grant, _LATE) == 1
    assert b'"serial":2' in _body(tmp_path)
    spring_before = datetime(2026, 3, 8, 6, 30, tzinfo=UTC)
    spring_after = datetime(2026, 3, 8, 7, 30, tzinfo=UTC)
    fall_before = datetime(2026, 11, 1, 5, 30, tzinfo=UTC)
    fall_after = datetime(2026, 11, 1, 6, 30, tzinfo=UTC)
    assert spring_before.astimezone(_NEW_YORK).date() == spring_after.astimezone(_NEW_YORK).date()
    assert fall_before.astimezone(_NEW_YORK).date() == fall_after.astimezone(_NEW_YORK).date()
    spring = BoundLedger(tmp_path / "spring0001")
    spring_grant = issue(ledger_id="spring0001")
    spring.initialize(spring_grant, spring_before)
    assert spring.reserve(spring_grant, spring_before) == 1
    assert spring.reserve(spring_grant, spring_after) == 2
    fall = BoundLedger(tmp_path / "fall0001")
    fall_grant = issue(ledger_id="fall0001")
    fall.initialize(fall_grant, fall_before)
    assert fall.reserve(fall_grant, fall_before) == 1
    assert fall.reserve(fall_grant, fall_after) == 2


def test_exhaustion_and_threads_stop_at_thirty(tmp_path: Path) -> None:
    grant, ledger = prepare(tmp_path / LEDGER)
    for expected in range(1, DAILY_LIMIT + 1):
        assert ledger.reserve(grant, WHEN) == expected
    _deny(lambda: ledger.reserve(grant, WHEN), "BUDGET_EXHAUSTED")
    fresh = prepare(tmp_path / "thread0001", ledger_id="thread0001")
    outcomes = list(ThreadPoolExecutor(max_workers=8).map(lambda _: _one(*fresh), range(40)))
    assert sorted(item for item in outcomes if type(item) is int) == list(range(1, 31))
    assert outcomes.count("BUDGET_EXHAUSTED") == 10


def test_separate_processes_share_the_ceiling(tmp_path: Path) -> None:
    directory = tmp_path / LEDGER
    prepare(directory)
    root = str(Path(__file__).parents[2])
    source = str(Path(root) / "src")
    code = (
        "import sys\n"
        "sys.path[:0] = [sys.argv[1], sys.argv[2]]\n"
        "from tests.unit.test_alpaca_paper_support import child_reserve\n"
        "child_reserve(sys.argv[3])\n"
    )

    def once() -> int:
        completed = subprocess.run(
            [sys.executable, "-c", code, root, source, str(directory)],
            check=False,
            capture_output=True,
            text=True,
            cwd=root,
        )
        assert completed.returncode == 0, completed.stderr
        return int(completed.stdout.strip())

    with ThreadPoolExecutor(max_workers=2) as pool:
        accepted = list(pool.map(lambda _: once(), (0, 1)))
    assert sum(accepted) == DAILY_LIMIT
    grant = issue()
    assert BoundLedger(directory).spent(grant, WHEN) == DAILY_LIMIT


def test_naive_clock_does_not_create_a_ledger(tmp_path: Path) -> None:
    grant = issue()
    ledger = BoundLedger(tmp_path / LEDGER)
    _deny(lambda: ledger.initialize(grant, datetime(2026, 11, 14)), "BUDGET_CLOCK_DENIED")
    assert not (tmp_path / LEDGER).exists()


def _body(tmp_path: Path) -> bytes:
    return (tmp_path / LEDGER / "ledger.json").read_bytes()


def _deny(operation: object, reason: str) -> None:
    with pytest.raises(BudgetError) as caught:
        operation()  # type: ignore[operator]
    assert caught.value.reason == reason


def _one(grant: object, ledger: BoundLedger) -> int | str:
    try:
        return ledger.reserve(grant, WHEN)  # type: ignore[arg-type]
    except BudgetError as error:
        return error.reason


def _substitution(tmp_path: Path) -> str | None:
    json_path = tmp_path / LEDGER / "ledger.json"
    copy = tmp_path / "copied.json"
    original = json_path.read_bytes()
    copy.write_bytes(original)
    json_path.unlink()
    try:
        json_path.symlink_to(copy)
    except OSError:
        json_path.write_bytes(original)
    else:
        return "file"
    parent = tmp_path / "linkparent"
    parent.mkdir()
    link = parent / LEDGER
    try:
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(tmp_path / LEDGER)],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    junction = getattr(link, "is_junction", None)
    if link.is_symlink() or (callable(junction) and junction()):
        return "junction"
    return None
