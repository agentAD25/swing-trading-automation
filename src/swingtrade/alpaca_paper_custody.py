"""Offline synthetic mock for two Alpaca paper targets.

A stored value is not permission to connect or to trade. The mock keeps
synthetic bytes in memory and exposes only reason codes in text.
"""

from __future__ import annotations

from enum import StrEnum

from swingtrade.alpaca_paper_boundary import (
    BROKER_HOST,
    BROKER_SANDBOX_HOST,
    DATA_HOST,
    LIVE_HOST,
    PAPER_HOST,
)

PAPER_KEY_ID_TARGET = "swing-trading/lane2/alpaca/paper/key-id"
PAPER_SECRET_TARGET = "swing-trading/lane2/alpaca/paper/secret"
AUTHX_HOST = "authx.alpaca.markets"
AUTHX_SANDBOX_HOST = "authx.sandbox.alpaca.markets"
DATA_SANDBOX_HOST = "data.sandbox.alpaca.markets"

_TARGETS = frozenset({PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET})
_LIVE_TARGET_PREFIX = "swing-trading/lane2/alpaca/live/"
_DENIED_HOSTS = frozenset(
    {
        LIVE_HOST,
        DATA_HOST,
        BROKER_HOST,
        BROKER_SANDBOX_HOST,
        AUTHX_HOST,
        AUTHX_SANDBOX_HOST,
        DATA_SANDBOX_HOST,
    }
)
_FAULTS = frozenset({"ambiguous", "inconsistent", "incomplete", "malformed"})
_FAULT_REASONS = {
    "ambiguous": "AMBIGUOUS_MOCK",
    "inconsistent": "INCONSISTENT_MOCK",
    "incomplete": "INCOMPLETE_MOCK",
    "malformed": "MALFORMED_MOCK",
}


class CustodyClassification(StrEnum):
    """Policy label. Neither value permits a call or an account action."""

    ACCEPTED = "ACCEPTED"
    DENIED = "DENIED"


class CustodyDecision:
    """One mock operation. Every action flag stays closed."""

    __slots__ = ("classification", "reason")

    def __init__(self, classification: CustodyClassification, reason: str) -> None:
        self.classification = classification
        self.reason = reason

    @property
    def connect_allowed(self) -> bool:
        return False

    @property
    def network_permitted(self) -> bool:
        return False

    @property
    def submit_permitted(self) -> bool:
        return False

    @property
    def cancel_permitted(self) -> bool:
        return False

    @property
    def replace_permitted(self) -> bool:
        return False

    @property
    def resubmit_permitted(self) -> bool:
        return False

    @property
    def safe_to_retry(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CustodyDecision):
            return NotImplemented
        return (self.classification, self.reason) == (other.classification, other.reason)

    def __repr__(self) -> str:
        return f"CustodyDecision({self.classification.value}, {self.reason})"

    def __str__(self) -> str:
        return self.reason


class CustodyError(RuntimeError):
    """Reason code only. Synthetic bytes are not part of the message."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        self.decision = CustodyDecision(CustodyClassification.DENIED, reason)
        super().__init__(reason)


class SyntheticMock:
    """In-memory fixture. A fault or a bad entry stores nothing."""

    __slots__ = ("_ambiguous_latched", "_entries", "_fault", "_hosts")

    def __init__(self, entries: object = None, *, fault: object = None) -> None:
        self._entries: dict[str, bytes] = {}
        self._hosts: dict[str, str] = {}
        self._ambiguous_latched = False
        self._fault = _fault_name(fault)
        if self._fault is not None or entries is None:
            return
        parsed = _parse_entries(entries)
        if isinstance(parsed, str):
            self._fault = parsed
            return
        self._entries, self._hosts = parsed

    def target_names(self) -> frozenset[str]:
        """Names only. Stored bytes stay inside the mock."""
        if self._fault is not None:
            return frozenset()
        return frozenset(self._entries)

    def __repr__(self) -> str:
        if self._fault is not None:
            return f"SyntheticMock({self._fault})"
        names = ",".join(sorted(self._entries))
        return f"SyntheticMock({names})"

    def __str__(self) -> str:
        return repr(self)


def store(mock: object, target: object, material: object, host: object) -> CustodyDecision:
    """Insert one synthetic value. An existing target is rejected."""
    current, name, payload, hostname = _prepare(mock, target, material, host)
    if name in current._entries:
        raise CustodyError("TARGET_EXISTS")
    current._entries[name] = payload
    current._hosts[name] = hostname
    return _accepted("STORED")


def replace(mock: object, target: object, material: object, host: object) -> CustodyDecision:
    """Replace one present synthetic value. An absent target is rejected."""
    current, name, payload, hostname = _prepare(mock, target, material, host)
    if name not in current._entries:
        raise CustodyError("TARGET_ABSENT")
    current._entries[name] = payload
    current._hosts[name] = hostname
    return _accepted("REPLACED")


def delete(mock: object, target: object) -> CustodyDecision:
    """Remove one present synthetic value. An absent target is rejected."""
    current = _require_mock(mock)
    _require_ready(current)
    name = _require_target(target)
    if name not in current._entries:
        raise CustodyError("TARGET_ABSENT")
    del current._entries[name]
    del current._hosts[name]
    return _accepted("DELETED")


def _accepted(reason: str) -> CustodyDecision:
    return CustodyDecision(CustodyClassification.ACCEPTED, reason)


def _prepare(
    mock: object,
    target: object,
    material: object,
    host: object,
) -> tuple[SyntheticMock, str, bytes, str]:
    current = _require_mock(mock)
    _require_ready(current)
    return current, _require_target(target), _require_material(material), _require_host(host)


def _require_mock(mock: object) -> SyntheticMock:
    if mock is None:
        raise CustodyError("MISSING_MOCK")
    if type(mock) is not SyntheticMock:
        raise CustodyError("MALFORMED_MOCK")
    return mock


def _require_ready(mock: SyntheticMock) -> None:
    if mock._ambiguous_latched:
        raise CustodyError("RETRY_DENIED")
    if mock._fault == "ambiguous":
        mock._ambiguous_latched = True
        raise CustodyError("AMBIGUOUS_MOCK")
    if mock._fault is not None:
        raise CustodyError(_FAULT_REASONS.get(mock._fault, "MALFORMED_MOCK"))


def _fault_name(fault: object) -> str | None:
    if fault is None:
        return None
    if type(fault) is str and fault in _FAULTS:
        return fault
    return "malformed"


def _parse_entries(entries: object) -> str | tuple[dict[str, bytes], dict[str, str]]:
    if not isinstance(entries, dict):
        return "malformed"
    kept_material: dict[str, bytes] = {}
    kept_hosts: dict[str, str] = {}
    for key, value in entries.items():
        parsed = _parse_entry(key, value)
        if isinstance(parsed, str):
            return parsed
        name, material, host = parsed
        kept_material[name] = material
        kept_hosts[name] = host
    return kept_material, kept_hosts


def _parse_entry(key: object, value: object) -> str | tuple[str, bytes, str]:
    if type(key) is not str:
        return "malformed"
    if type(value) is list:
        return "ambiguous"
    if type(value) is not tuple or len(value) != 2:
        return "malformed"
    material, host = value
    if type(material) is bytes and type(host) is str:
        if material == b"" or host == "":
            return "incomplete"
        if key not in _TARGETS or host != PAPER_HOST:
            return "inconsistent"
        return key, material, host
    return "malformed"


def _require_target(target: object) -> str:
    if type(target) is not str:
        raise CustodyError("MALFORMED_TARGET")
    if target == "" or _unsafe(target):
        raise CustodyError("MALFORMED_TARGET")
    folded = target.casefold()
    if "live" in folded:
        if target.startswith(_LIVE_TARGET_PREFIX):
            raise CustodyError("LIVE_TARGET_DENIED")
        raise CustodyError("LIVE_NAME_DENIED")
    if target in _TARGETS:
        return target
    if folded in {name.casefold() for name in _TARGETS}:
        raise CustodyError("TARGET_CASE_DENIED")
    raise CustodyError("TARGET_DENIED")


def _require_material(material: object) -> bytes:
    if material is None or material == b"":
        raise CustodyError("INCOMPLETE_MATERIAL")
    if type(material) is not bytes:
        raise CustodyError("MALFORMED_MATERIAL")
    if any(byte < 33 or byte > 126 for byte in material):
        raise CustodyError("MALFORMED_MATERIAL")
    return material


def _require_host(host: object) -> str:
    if type(host) is not str:
        raise CustodyError("MALFORMED_HOST")
    if host == "" or _unsafe(host) or _structured(host):
        raise CustodyError("MALFORMED_HOST")
    if host == LIVE_HOST:
        raise CustodyError("LIVE_HOST_DENIED")
    if host in _DENIED_HOSTS:
        raise CustodyError("HOST_DENIED")
    if host != PAPER_HOST:
        raise CustodyError("HOST_MISMATCH")
    return host


def _structured(host: str) -> bool:
    return "://" in host or "/" in host or "@" in host or ":" in host or "\\" in host


def _unsafe(value: str) -> bool:
    return any(ord(char) < 33 or ord(char) > 126 for char in value)
