"""In-process fake credential port. Not a Windows Credential Manager binding."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock

from swingtrade.gmail_credential.identity import CANONICAL_TARGET, CRED_TYPE_GENERIC
from swingtrade.gmail_credential.secret import SyntheticSecret, _material_of

_SESSION_FAULTS = frozenset(
    {"unsupported_os", "invalid_security_context", "no_logon_session"}
)
_CASE_VARIANT = "Swing-Trading/Lane3/Gmail/Dev/Refresh-Token"


class _Row:
    __slots__ = ("material", "persist", "spelling")

    def __init__(self, spelling: str, material: bytes, persist: int) -> None:
        self.spelling = spelling
        self.material = material
        self.persist = persist

    def __repr__(self) -> str:
        return "_Row(redacted)"


class MockCredentialPort:
    """Case-insensitive fake vault for one injected test store.

    ``CredWriteW`` would replace an existing target. :meth:`create_holding_lock`
    does not. Allocation ids stand in for a future ``CredReadW`` buffer.
    :meth:`release` drops that stand-in only. It does not certify ``CredFree``.
    The lock serializes this process. It is not cross-process atomicity.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._rows: dict[tuple[str, int], _Row] = {}
        self._live: dict[int, int] = {}
        self._next_alloc = 1
        self.session_fault: str | None = None
        self.operation_fault: str | None = None
        self.create_attempts = 0
        self.replace_attempts = 0
        self.delete_attempts = 0
        self.read_attempts = 0
        self.release_count = 0
        self.alloc_count = 0
        self.raise_after_read = False

    def __repr__(self) -> str:
        return f"MockCredentialPort(entries={len(self._rows)})"

    @contextmanager
    def hold(self) -> Iterator[None]:
        self._lock.acquire()
        try:
            yield
        finally:
            self._lock.release()

    def entry_count(self) -> int:
        with self._lock:
            return len(self._rows)

    def session_block(self) -> str | None:
        fault = self.session_fault
        if fault is None:
            return None
        if fault in _SESSION_FAULTS:
            return fault
        return "fail_closed"

    def seed_case_variant(self, secret: SyntheticSecret, persist: int) -> None:
        """Insert a non-canonical spelling at the canonical case-insensitive key."""
        if type(secret) is not SyntheticSecret:
            raise ValueError("seed requires a synthetic fixture")
        key = (CANONICAL_TARGET.casefold(), CRED_TYPE_GENERIC)
        with self._lock:
            self._rows[key] = _Row(_CASE_VARIANT, _material_of(secret), persist)

    def live_allocation_count(self) -> int:
        with self._lock:
            return len(self._live)

    def contains_holding_lock(self) -> bool:
        key = (CANONICAL_TARGET.casefold(), CRED_TYPE_GENERIC)
        return key in self._rows

    def create_holding_lock(self, material: bytes, persist: int) -> str:
        """Insert only when absent. Does not replace."""
        self.create_attempts += 1
        key = (CANONICAL_TARGET.casefold(), CRED_TYPE_GENERIC)
        if key in self._rows:
            return "collision"
        fault = self._take_operation_fault()
        if fault == "ambiguous_write":
            self._rows[key] = _Row(CANONICAL_TARGET, bytes(material), persist)
            return "ambiguous_write"
        if fault == "interrupted_write":
            return "interrupted_write"
        if fault is not None:
            return fault
        self._rows[key] = _Row(CANONICAL_TARGET, bytes(material), persist)
        return "stored"

    def replace_holding_lock(self, material: bytes, persist: int) -> str:
        """Replace only an existing row. Does not create."""
        self.replace_attempts += 1
        key = (CANONICAL_TARGET.casefold(), CRED_TYPE_GENERIC)
        if key not in self._rows:
            return "missing"
        fault = self._take_operation_fault()
        if fault == "ambiguous_write":
            self._rows[key] = _Row(CANONICAL_TARGET, bytes(material), persist)
            return "ambiguous_write"
        if fault == "interrupted_write":
            return "interrupted_write"
        if fault is not None:
            return fault
        self._rows[key] = _Row(CANONICAL_TARGET, bytes(material), persist)
        return "replaced"

    def delete_holding_lock(self) -> str:
        self.delete_attempts += 1
        key = (CANONICAL_TARGET.casefold(), CRED_TYPE_GENERIC)
        if key not in self._rows:
            return "missing"
        fault = self._take_operation_fault()
        if fault is not None:
            return fault
        del self._rows[key]
        return "deleted"

    def read_holding_lock(self) -> tuple[int, bytes] | str:
        """Return ``(allocation id, material)`` or an error code.

        The caller must :meth:`release` that id on every path. Releasing the
        id is mock cleanup only and does not certify native ``CredFree``.
        """
        self.read_attempts += 1
        fault = self._take_operation_fault()
        if fault is not None:
            return fault
        key = (CANONICAL_TARGET.casefold(), CRED_TYPE_GENERIC)
        row = self._rows.get(key)
        if row is None:
            return "missing"
        alloc_id = self._next_alloc
        self._next_alloc += 1
        self._live[alloc_id] = 1
        self.alloc_count += 1
        return (alloc_id, bytes(row.material))

    def release(self, allocation_id: int | None) -> None:
        """Drop one mock allocation id. Not a native ``CredFree`` call."""
        if allocation_id is None:
            return
        self._live.pop(allocation_id, None)
        self.release_count += 1

    def _take_operation_fault(self) -> str | None:
        fault = self.operation_fault
        self.operation_fault = None
        return fault
