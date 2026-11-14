"""Durable paper-account request budget. No credential and no provider call.

The ledger stores a New York calendar day and a count. It does not store a
key, a secret, or an account body. Creating this object does not write.
"""

from __future__ import annotations

import json
import sys
import threading
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DAILY_LIMIT = 30
_NEW_YORK = ZoneInfo("America/New_York")
_FIELDS = frozenset({"count", "day"})


class BudgetError(RuntimeError):
    """Reason code only."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class DurableRequestBudget:
    """One shared ledger. Reservations survive a new instance on the same path."""

    __slots__ = ("_clock", "_path", "_thread")

    def __init__(self, path: Path, clock: Callable[[], datetime]) -> None:
        self._path = path
        self._clock = clock
        self._thread = threading.Lock()

    def reserve(self) -> int:
        """Consume one request for the current New York day, or fail closed."""
        day = _day(self._clock())
        self._path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self._path.with_name(self._path.name + ".lock")
        with self._thread:
            if not lock_path.exists() or lock_path.stat().st_size == 0:
                lock_path.write_bytes(b"\0")
            handle = lock_path.open("r+b")
            try:
                _exclusive(handle)
                count = _stored_count(self._path, day)
                if count >= DAILY_LIMIT:
                    raise BudgetError("BUDGET_EXHAUSTED")
                updated = count + 1
                _write_count(self._path, day, updated)
                return updated
            finally:
                _release(handle)
                handle.close()

    def spent(self) -> int:
        """Current count for the clock's New York day. This does not reserve."""
        day = _day(self._clock())
        if not self._path.exists():
            return 0
        return _stored_count(self._path, day)

    def __repr__(self) -> str:
        return "DurableRequestBudget()"


def _day(moment: datetime) -> str:
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise BudgetError("BUDGET_CLOCK_DENIED")
    return moment.astimezone(_NEW_YORK).date().isoformat()


def _stored_count(path: Path, day: str) -> int:
    if not path.exists():
        return 0
    raw = path.read_bytes()
    if raw.strip() == b"":
        return 0
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise BudgetError("BUDGET_LEDGER_MALFORMED") from None
    if type(parsed) is not dict or set(parsed) != _FIELDS or type(parsed["day"]) is not str:
        raise BudgetError("BUDGET_LEDGER_MALFORMED")
    if parsed["day"] != day:
        return 0
    count = parsed["count"]
    if type(count) is not int or isinstance(count, bool) or count < 0 or count > DAILY_LIMIT:
        raise BudgetError("BUDGET_LEDGER_MALFORMED")
    return count


def _write_count(path: Path, day: str, count: int) -> None:
    payload = json.dumps({"count": count, "day": day}, separators=(",", ":"), sort_keys=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload.encode("utf-8"))
    temporary.replace(path)


def _exclusive(handle: object) -> None:
    fileno = handle.fileno()  # type: ignore[attr-defined]
    if sys.platform == "win32":
        import msvcrt

        handle.seek(0)  # type: ignore[attr-defined]
        msvcrt.locking(fileno, msvcrt.LK_LOCK, 1)
        return
    import fcntl

    fcntl.flock(fileno, fcntl.LOCK_EX)


def _release(handle: object) -> None:
    fileno = handle.fileno()  # type: ignore[attr-defined]
    if sys.platform == "win32":
        import msvcrt

        handle.seek(0)  # type: ignore[attr-defined]
        msvcrt.locking(fileno, msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(fileno, fcntl.LOCK_UN)
