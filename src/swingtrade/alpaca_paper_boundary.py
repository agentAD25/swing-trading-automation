"""Classify hypothetical Alpaca Paper destinations. No connection is opened.

A paper-host label is a policy observation. It does not enable a call
or an account action. Live, market-data, and broker hosts are denied.
Permission flags stay closed.
"""

from __future__ import annotations

from enum import StrEnum

PAPER_HOST = "paper-api.alpaca.markets"
LIVE_HOST = "api.alpaca.markets"
DATA_HOST = "data.alpaca.markets"
BROKER_HOST = "broker-api.alpaca.markets"
BROKER_SANDBOX_HOST = "broker-api.sandbox.alpaca.markets"

_HOST_REASONS = {
    LIVE_HOST: "LIVE_HOST_DENIED",
    DATA_HOST: "DATA_HOST_DENIED",
    BROKER_HOST: "BROKER_HOST_DENIED",
    BROKER_SANDBOX_HOST: "BROKER_SANDBOX_DENIED",
}
_EXACT_PATHS = frozenset({"/v2/account", "/v2/positions", "/v2/orders"})
_ORDER_PREFIX = "/v2/orders/"
_MAX_SEGMENT = 128


class BoundaryClassification(StrEnum):
    """Policy label. Neither value permits a call or an account action."""

    PAPER_POLICY_CANDIDATE = "PAPER_POLICY_CANDIDATE"
    DENIED = "DENIED"


class BoundaryDecision:
    """One destination classification. Every action flag stays closed."""

    __slots__ = ("classification", "reason")

    def __init__(self, classification: BoundaryClassification, reason: str) -> None:
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
        if not isinstance(other, BoundaryDecision):
            return NotImplemented
        return (self.classification, self.reason) == (other.classification, other.reason)

    def __repr__(self) -> str:
        return f"BoundaryDecision({self.classification.value}, {self.reason})"


def evaluate_paper_boundary(target: object, method: object) -> BoundaryDecision:
    """Classify one absolute destination and one method token.

    The arguments are the whole input. There is no host override, proxy,
    redirect switch, or TLS switch.
    """
    path, reason = _destination(target)
    if reason is not None or path is None:
        return BoundaryDecision(BoundaryClassification.DENIED, reason or "MALFORMED_TARGET")
    method_reason = _method_reason(method)
    if method_reason is not None:
        return BoundaryDecision(BoundaryClassification.DENIED, method_reason)
    return BoundaryDecision(BoundaryClassification.PAPER_POLICY_CANDIDATE, "CLASSIFIED")


def _destination(target: object) -> tuple[str | None, str | None]:
    if type(target) is not str or target == "" or _unsafe(target):
        return None, "MALFORMED_TARGET"
    if "%" in target:
        return None, "ENCODED_PATH_DENIED"
    scheme, separator, remainder = target.partition("://")
    if separator != "://" or remainder == "":
        return None, "MALFORMED_TARGET"
    if scheme != "https":
        return None, "SCHEME_DENIED"
    if "?" in remainder:
        return None, "QUERY_DENIED"
    if "#" in remainder:
        return None, "FRAGMENT_DENIED"
    if "@" in remainder:
        return None, "USERINFO_DENIED"
    if "://" in remainder:
        return None, "MALFORMED_TARGET"
    authority, slash, path_rest = remainder.partition("/")
    path = f"/{path_rest}" if slash else ""
    authority_reason = _authority_reason(authority)
    if authority_reason is not None:
        return None, authority_reason
    path_reason = _path_reason(path)
    if path_reason is not None:
        return None, path_reason
    return path, None


def _unsafe(target: str) -> bool:
    return any(ord(char) < 33 or ord(char) > 126 or char == "\\" for char in target)


def _authority_reason(authority: str) -> str | None:
    if authority == "":
        return "MALFORMED_TARGET"
    if authority.startswith("["):
        return "ADDRESS_LITERAL_DENIED"
    host = authority
    if ":" in authority:
        host, _, port = authority.rpartition(":")
        if host.startswith("[") or _dotted_decimal(host):
            return "ADDRESS_LITERAL_DENIED"
        if port == "" or not _digits(port):
            return "MALFORMED_TARGET"
        return "PORT_DENIED"
    if _dotted_decimal(host):
        return "ADDRESS_LITERAL_DENIED"
    if host == PAPER_HOST:
        return None
    return _HOST_REASONS.get(host, "HOST_DENIED")


def _dotted_decimal(host: str) -> bool:
    parts = host.split(".")
    return len(parts) == 4 and all(_digits(part) and part != "" for part in parts)


def _digits(value: str) -> bool:
    return all("0" <= char <= "9" for char in value)


def _path_reason(path: str) -> str | None:
    if path in _EXACT_PATHS:
        return None
    if not path.startswith(_ORDER_PREFIX):
        return "PATH_DENIED"
    segment = path[len(_ORDER_PREFIX) :]
    if _segment_ok(segment):
        return None
    return "PATH_DENIED"


def _segment_ok(segment: str) -> bool:
    if not 1 <= len(segment) <= _MAX_SEGMENT:
        return False
    if not _ascii_alnum(segment[0]):
        return False
    return all(_ascii_alnum(char) or char in "-_" for char in segment)


def _ascii_alnum(char: str) -> bool:
    return "0" <= char <= "9" or "A" <= char <= "Z" or "a" <= char <= "z"


def _method_reason(method: object) -> str | None:
    if type(method) is not str or method == "" or method != method.strip():
        return "MALFORMED_METHOD"
    if any(ord(char) < 33 or ord(char) > 126 for char in method):
        return "MALFORMED_METHOD"
    if method != "GET":
        return "METHOD_DENIED"
    return None
