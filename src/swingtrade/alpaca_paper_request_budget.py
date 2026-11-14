"""Protected paper-account request ledger. No credential and no provider call.

The production reserve function takes no path. A missing or empty ledger does
not become a zero count. An ordinary file that the same user can rewrite is
not a tamper-proof counter; replacement of a consistent pair remains a
deployment dependency on an external monotonic authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo

from swingtrade.alpaca_paper_grant import (
    VerifiedGrant,
    authorize_production,
    program_data_directory,
)

DAILY_LIMIT = 30
_NEW_YORK = ZoneInfo("America/New_York")
_FIELDS = frozenset(
    {
        "account_id",
        "ceiling",
        "chain",
        "count",
        "day",
        "genesis",
        "grant_id",
        "last_utc",
        "ledger_id",
        "serial",
        "windows_sid",
    }
)
_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


class BudgetError(RuntimeError):
    """Reason code only."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class BoundLedger:
    """One ledger directory bound to a verified grant and paper account."""

    __slots__ = ("_directory",)

    def __init__(self, directory: Path) -> None:
        if not _safe_name(directory.name):
            raise BudgetError("LEDGER_BINDING_MISMATCH")
        self._directory = directory

    def initialize(self, grant: VerifiedGrant, now: datetime) -> None:
        """Create the ledger once. A second call does not reset the count."""
        grant.ensure()
        _require_clock(now)
        _require_window(grant, now)
        _require_directory_name(self._directory, grant)
        self._directory.mkdir(parents=True, exist_ok=True)
        _reject_substitute(self._directory)
        with _thread_lock(self._directory):
            handle = _file_lock(self._directory)
            try:
                if _json_path(self._directory).exists() or _high_path(self._directory).exists():
                    raise BudgetError("LEDGER_ALREADY_INITIALIZED")
                record = _blank(grant, now)
                _write_pair(self._directory, record, create=True)
            finally:
                _unlock(handle)

    def reserve(self, grant: VerifiedGrant, now: datetime) -> int:
        """Consume one New York-day request. Ambiguous work is not refunded."""
        grant.ensure()
        _require_clock(now)
        _require_window(grant, now)
        _require_directory_name(self._directory, grant)
        record = self._mutate(grant, now, consume=True)
        count = record["count"]
        if type(count) is not int:
            raise BudgetError("LEDGER_MALFORMED")
        return count

    def spent(self, grant: VerifiedGrant, now: datetime) -> int:
        """Read the current day's count. This does not reserve or reset."""
        grant.ensure()
        _require_clock(now)
        _require_directory_name(self._directory, grant)
        record = self._mutate(grant, now, consume=False)
        if record["day"] != _day(now):
            if _day(now) < str(record["day"]):
                raise BudgetError("CLOCK_ROLLBACK")
            return 0
        count = record["count"]
        if type(count) is not int:
            raise BudgetError("LEDGER_MALFORMED")
        return count

    def __repr__(self) -> str:
        return "BoundLedger()"

    def _mutate(self, grant: VerifiedGrant, now: datetime, *, consume: bool) -> dict[str, object]:
        if not self._directory.exists():
            raise BudgetError("LEDGER_MISSING")
        _reject_substitute(self._directory)
        with _thread_lock(self._directory):
            handle = _file_lock(self._directory)
            try:
                record = _read_pair(self._directory, grant)
                _reject_clock(record, now)
                if not consume:
                    return record
                updated = _next(record, now)
                _write_pair(self._directory, updated, create=False)
                return updated
            finally:
                _unlock(handle)


def reserve_for_production() -> int:
    """Reserve against the fixed ledger. The caller cannot choose a path."""
    grant = authorize_production()
    return _production_ledger(grant).reserve(grant, datetime.now(UTC))


def initialize_for_production() -> None:
    """Create the fixed ledger once. A missing ledger is not treated as zero later."""
    grant = authorize_production()
    _production_ledger(grant).initialize(grant, datetime.now(UTC))


def _production_ledger(grant: VerifiedGrant) -> BoundLedger:
    directory = (
        program_data_directory() / "swing-trading" / "alpaca-paper-account-read" / grant.ledger_id
    )
    return BoundLedger(directory)


def expected_genesis(grant_id: str, account_id: str, ledger_id: str) -> str:
    """Genesis bound into the signed grant. A replaced file cannot choose another."""
    material = f"{grant_id}\n{account_id}\n{ledger_id}".encode()
    return hashlib.sha256(material).hexdigest()


def posix_mode_rejected(mode: int) -> bool:
    """Group or other access is rejected on platforms that honor POSIX modes."""
    return bool(mode & 0o077)


def _blank(grant: VerifiedGrant, now: datetime) -> dict[str, object]:
    record: dict[str, object] = {
        "account_id": grant.account_id,
        "ceiling": grant.daily_ceiling,
        "count": 0,
        "day": _day(now),
        "genesis": grant.ledger_genesis,
        "grant_id": grant.grant_id,
        "last_utc": _stamp(now),
        "ledger_id": grant.ledger_id,
        "serial": 0,
        "windows_sid": grant.windows_sid,
    }
    record["chain"] = _chain(record)
    return record


def _next(record: dict[str, object], now: datetime) -> dict[str, object]:
    today = _day(now)
    stored_day = record["day"]
    count = record["count"]
    serial = record["serial"]
    ceiling = record["ceiling"]
    if type(stored_day) is not str or type(count) is not int or type(serial) is not int:
        raise BudgetError("LEDGER_MALFORMED")
    if type(ceiling) is not int or ceiling != DAILY_LIMIT:
        raise BudgetError("LEDGER_MALFORMED")
    if today < stored_day:
        raise BudgetError("CLOCK_ROLLBACK")
    updated_count = count + 1 if today == stored_day else 1
    if updated_count > DAILY_LIMIT:
        raise BudgetError("BUDGET_EXHAUSTED")
    successor: dict[str, object] = dict(record)
    successor["count"] = updated_count
    successor["day"] = today
    successor["last_utc"] = _stamp(now)
    successor["serial"] = serial + 1
    successor["chain"] = _chain(successor)
    return successor


def _read_pair(directory: Path, grant: VerifiedGrant) -> dict[str, object]:
    body_path = _json_path(directory)
    high_path = _high_path(directory)
    if not body_path.exists():
        raise BudgetError("LEDGER_MISSING")
    if not high_path.exists():
        raise BudgetError("LEDGER_REPLACED")
    _reject_substitute(body_path)
    _reject_substitute(high_path)
    _reject_permissions(body_path)
    _reject_permissions(high_path)
    raw = _read_bytes(body_path)
    if raw.strip() == b"":
        raise BudgetError("LEDGER_MALFORMED")
    try:
        parsed = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeError, json.JSONDecodeError, BudgetError):
        raise BudgetError("LEDGER_MALFORMED") from None
    if type(parsed) is not dict or set(parsed) != _FIELDS:
        raise BudgetError("LEDGER_MALFORMED")
    if _chain(parsed) != parsed["chain"]:
        raise BudgetError("LEDGER_MALFORMED")
    _require_binding(parsed, grant)
    high = _read_bytes(high_path)
    if high != f"{parsed['serial']}\n{parsed['chain']}\n".encode():
        raise BudgetError("LEDGER_REPLACED")
    return parsed


def _require_binding(record: dict[str, object], grant: VerifiedGrant) -> None:
    if (
        record["account_id"] != grant.account_id
        or record["grant_id"] != grant.grant_id
        or record["ledger_id"] != grant.ledger_id
        or record["windows_sid"] != grant.windows_sid
        or record["ceiling"] != grant.daily_ceiling
        or record["genesis"] != grant.ledger_genesis
        or record["genesis"] != expected_genesis(grant.grant_id, grant.account_id, grant.ledger_id)
    ):
        raise BudgetError("LEDGER_BINDING_MISMATCH")
    count = record["count"]
    serial = record["serial"]
    day = record["day"]
    if (
        type(count) is not int
        or isinstance(count, bool)
        or count < 0
        or count > DAILY_LIMIT
        or type(serial) is not int
        or isinstance(serial, bool)
        or serial < 0
        or type(day) is not str
        or len(day) != 10
    ):
        raise BudgetError("LEDGER_MALFORMED")
    moment = _parse_stamp(record["last_utc"])
    if _day(moment) != day:
        raise BudgetError("LEDGER_MALFORMED")


def _write_pair(directory: Path, record: dict[str, object], *, create: bool) -> None:
    payload = json.dumps(record, separators=(",", ":"), sort_keys=True).encode("utf-8")
    high = f"{record['serial']}\n{record['chain']}\n".encode()
    writer = _create_new if create else _atomic_write
    writer(_json_path(directory), payload)
    writer(_high_path(directory), high)


def _binary_create_flags() -> int:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if sys.platform == "win32":
        return flags | os.O_BINARY
    return flags


def _create_new(path: Path, payload: bytes) -> None:
    try:
        descriptor = os.open(path, _binary_create_flags(), 0o600)
    except FileExistsError:
        raise BudgetError("LEDGER_ALREADY_INITIALIZED") from None
    except OSError:
        raise BudgetError("LEDGER_PERMISSION_DENIED") from None
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    except OSError:
        raise BudgetError("LEDGER_PERMISSION_DENIED") from None
    finally:
        os.close(descriptor)
    try:
        os.chmod(path, 0o600)
    except OSError:
        raise BudgetError("LEDGER_PERMISSION_DENIED") from None


def _atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists() or temporary.is_symlink():
        raise BudgetError("LEDGER_SUBSTITUTED")
    try:
        descriptor = os.open(temporary, _binary_create_flags(), 0o600)
    except OSError:
        raise BudgetError("LEDGER_PERMISSION_DENIED") from None
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    except OSError:
        raise BudgetError("LEDGER_PERMISSION_DENIED") from None
    finally:
        os.close(descriptor)
    try:
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except OSError:
        raise BudgetError("LEDGER_PERMISSION_DENIED") from None


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    found: dict[str, object] = {}
    for key, value in pairs:
        if key in found:
            raise BudgetError("LEDGER_MALFORMED")
        found[key] = value
    return found


def _chain(record: dict[str, object]) -> str:
    body = {key: value for key, value in record.items() if key != "chain"}
    raw = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _reject_clock(record: dict[str, object], now: datetime) -> None:
    stored = _parse_stamp(record["last_utc"])
    if now < stored or _day(now) < str(record["day"]):
        raise BudgetError("CLOCK_ROLLBACK")


def _require_window(grant: VerifiedGrant, now: datetime) -> None:
    if now < grant.activated_at:
        raise BudgetError("GRANT_NOT_ACTIVE")
    if now >= grant.expires_at:
        raise BudgetError("GRANT_EXPIRED")


def _require_clock(now: datetime) -> None:
    if now.tzinfo is None or now.utcoffset() is None:
        raise BudgetError("BUDGET_CLOCK_DENIED")


def _require_directory_name(directory: Path, grant: VerifiedGrant) -> None:
    if directory.name != grant.ledger_id:
        raise BudgetError("LEDGER_BINDING_MISMATCH")


def _safe_name(name: str) -> bool:
    return name.isascii() and name.isalnum() and 1 <= len(name) <= 64


def _day(moment: datetime) -> str:
    return moment.astimezone(_NEW_YORK).date().isoformat()


def _stamp(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _parse_stamp(value: object) -> datetime:
    if type(value) is not str or not value.endswith("Z"):
        raise BudgetError("LEDGER_MALFORMED")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
    except ValueError:
        raise BudgetError("LEDGER_MALFORMED") from None


def _json_path(directory: Path) -> Path:
    return directory / "ledger.json"


def _high_path(directory: Path) -> Path:
    return directory / "ledger.high"


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError:
        raise BudgetError("LEDGER_PERMISSION_DENIED") from None


def _reject_permissions(path: Path) -> None:
    try:
        writable = os.access(path, os.W_OK)
        mode = path.stat().st_mode
    except OSError:
        raise BudgetError("LEDGER_PERMISSION_DENIED") from None
    if not writable:
        raise BudgetError("LEDGER_PERMISSION_DENIED")
    if sys.platform != "win32" and posix_mode_rejected(mode):
        raise BudgetError("LEDGER_PERMISSION_DENIED")


def _reject_substitute(path: Path) -> None:
    junction = getattr(path, "is_junction", None)
    if path.is_symlink() or (callable(junction) and junction()):
        raise BudgetError("LEDGER_SUBSTITUTED")
    if sys.platform != "win32":
        return
    import ctypes
    from ctypes import wintypes

    kernel = cast(Any, ctypes).WinDLL("kernel32")
    kernel.GetFileAttributesW.argtypes = (wintypes.LPCWSTR,)
    kernel.GetFileAttributesW.restype = wintypes.DWORD
    attributes = int(kernel.GetFileAttributesW(os.fspath(path)))
    if attributes == 0xFFFFFFFF or attributes & 0x400:
        raise BudgetError("LEDGER_SUBSTITUTED")


def _thread_lock(directory: Path) -> threading.Lock:
    key = str(directory)
    with _LOCKS_GUARD:
        lock = _LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _LOCKS[key] = lock
        return lock


def _file_lock(directory: Path) -> object:
    path = directory / "ledger.lock"
    if path.is_symlink():
        raise BudgetError("LEDGER_SUBSTITUTED")
    if not path.exists():
        try:
            descriptor = os.open(path, _binary_create_flags(), 0o600)
        except FileExistsError:
            descriptor = -1
        except OSError:
            raise BudgetError("LEDGER_PERMISSION_DENIED") from None
        else:
            try:
                os.write(descriptor, b"\0")
            except OSError:
                raise BudgetError("LEDGER_PERMISSION_DENIED") from None
            finally:
                os.close(descriptor)
    try:
        handle = path.open("r+b")
    except OSError:
        raise BudgetError("LEDGER_PERMISSION_DENIED") from None
    _exclusive(handle)
    return handle


def _exclusive(handle: object) -> None:
    fileno = handle.fileno()  # type: ignore[attr-defined]
    if sys.platform == "win32":
        import msvcrt

        handle.seek(0)  # type: ignore[attr-defined]
        msvcrt.locking(fileno, msvcrt.LK_LOCK, 1)
        return
    import fcntl

    fcntl.flock(fileno, fcntl.LOCK_EX)


def _unlock(handle: object) -> None:
    fileno = handle.fileno()  # type: ignore[attr-defined]
    try:
        if sys.platform == "win32":
            import msvcrt

            handle.seek(0)  # type: ignore[attr-defined]
            msvcrt.locking(fileno, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(fileno, fcntl.LOCK_UN)
    finally:
        handle.close()  # type: ignore[attr-defined]
