"""Offline contract for one future Alpaca paper account read.

No credential is loaded and no provider request is sent. A scripted
transport may run only after a separate Windows runtime grant, and only
once. The seven Gate C2 flags stay closed.
"""

from __future__ import annotations

from enum import StrEnum

from swingtrade.alpaca_paper_boundary import (
    BROKER_HOST,
    BROKER_SANDBOX_HOST,
    DATA_HOST,
    LIVE_HOST,
    PAPER_HOST,
    BoundaryClassification,
    evaluate_paper_boundary,
)
from swingtrade.alpaca_paper_custody import (
    AUTHX_HOST,
    AUTHX_SANDBOX_HOST,
    DATA_SANDBOX_HOST,
    PAPER_KEY_ID_TARGET,
    PAPER_SECRET_TARGET,
)

ACCOUNT_PATH = "/v2/account"
ACCOUNT_URL = f"https://{PAPER_HOST}{ACCOUNT_PATH}"
_LIVE_TARGET_PREFIX = "swing-trading/lane2/alpaca/live/"
_PAPER_TARGETS = (PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET)
_DENIED_HOSTS = frozenset(
    {
        DATA_HOST,
        BROKER_HOST,
        BROKER_SANDBOX_HOST,
        AUTHX_HOST,
        AUTHX_SANDBOX_HOST,
        DATA_SANDBOX_HOST,
    }
)
_ACCEPTED_BODY_STATUS = "ACTIVE"
_MISSING_BODY = object()
_FAULTS = frozenset({"ambiguous", "inconsistent", "incomplete", "malformed", "env-fallback"})
_FAULT_REASONS = {
    "ambiguous": "AMBIGUOUS_CUSTODY",
    "inconsistent": "INCONSISTENT_CUSTODY",
    "incomplete": "INCOMPLETE_CUSTODY",
    "malformed": "MALFORMED_CUSTODY",
    "env-fallback": "ENV_FALLBACK_DENIED",
}


class ProbeClassification(StrEnum):
    """Observation label. Neither value permits a provider call."""

    ACCEPTED = "ACCEPTED"
    DENIED = "DENIED"


class ProbeDecision:
    """One scripted observation. Every action flag stays closed."""

    __slots__ = ("classification", "reason")

    def __init__(self, classification: ProbeClassification, reason: str) -> None:
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
        if not isinstance(other, ProbeDecision):
            return NotImplemented
        return (self.classification, self.reason) == (other.classification, other.reason)

    def __repr__(self) -> str:
        return f"ProbeDecision({self.classification.value}, {self.reason})"

    def __str__(self) -> str:
        return self.reason


class ProbeError(RuntimeError):
    """Reason code only. Synthetic bytes are not part of the message."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        self.decision = ProbeDecision(ProbeClassification.DENIED, reason)
        super().__init__(reason)


class RuntimeAuthorization:
    """Injected stand-in for a later exact-source runtime decision.

    A Windows value still does not open a credential store or a provider
    connection. Any other platform is closed.
    """

    __slots__ = ("platform",)

    def __init__(self, platform: str) -> None:
        self.platform = platform

    def __repr__(self) -> str:
        return f"RuntimeAuthorization({self.platform})"

    def __str__(self) -> str:
        return repr(self)


class SyntheticCustody:
    """Scripted custody evidence. Bytes stay inside this object."""

    __slots__ = ("_denial", "_entries")

    def __init__(
        self,
        entries: object = None,
        *,
        host: object = None,
        hosts: object = None,
        fault: object = None,
    ) -> None:
        self._entries: dict[str, bytes] = {}
        self._denial = _custody_denial(entries, host, hosts, fault)
        if self._denial is not None or not isinstance(entries, dict):
            return
        self._entries = {
            name: value
            for name, value in entries.items()
            if isinstance(name, str) and isinstance(value, bytes)
        }

    def __repr__(self) -> str:
        if self._denial is not None:
            return f"SyntheticCustody({self._denial})"
        names = ",".join(sorted(self._entries))
        return f"SyntheticCustody({names})"

    def __str__(self) -> str:
        return repr(self)


class ScriptedOutcome:
    """One scripted account result. The body is never rendered."""

    __slots__ = ("_body", "fault", "redirected", "status")

    def __init__(
        self,
        *,
        status: object = 200,
        redirected: object = False,
        fault: object = None,
        body: object = _MISSING_BODY,
    ) -> None:
        self.status = status
        self.redirected = redirected
        self.fault = fault
        self._body = body

    def __repr__(self) -> str:
        return "ScriptedOutcome()"

    def __str__(self) -> str:
        return "ScriptedOutcome()"


class SyntheticTransport:
    """In-process script. ``exchange`` does not leave the interpreter."""

    __slots__ = ("_outcome", "calls")

    def __init__(self, outcome: object) -> None:
        if type(outcome) is not ScriptedOutcome:
            raise ProbeError("MALFORMED_TRANSPORT")
        self._outcome = outcome
        self.calls = 0

    def exchange(self) -> ScriptedOutcome:
        self.calls += 1
        if self._outcome.fault == "exception":
            raise RuntimeError("TRANSPORT_EXCEPTION")
        return self._outcome

    def __repr__(self) -> str:
        return f"SyntheticTransport(calls={self.calls})"

    def __str__(self) -> str:
        return repr(self)


class ProbeSession:
    """One future account read. A second attempt is closed."""

    __slots__ = ("_exchanged",)

    def __init__(self) -> None:
        self._exchanged = False

    def __repr__(self) -> str:
        return f"ProbeSession(exchanged={self._exchanged})"


def read_account(
    session: object,
    custody: object,
    transport: object,
    runtime: object,
    *,
    method: object = "GET",
    url: object = ACCOUNT_URL,
) -> ProbeDecision:
    """Observe one scripted paper account read, or fail closed.

    The arguments are the whole input. There is no host override, secret
    fallback, redirect, or second exchange.
    """
    current = _require_session(session)
    if current._exchanged:
        raise ProbeError("MULTIPLE_GET_DENIED")
    request_reason = _request_reason(method, url)
    if request_reason is not None:
        raise ProbeError(request_reason)
    _require_runtime(runtime)
    _require_custody(custody)
    scripted = _require_transport(transport)
    current._exchanged = True
    try:
        outcome = scripted.exchange()
    except RuntimeError:
        raise ProbeError("TRANSPORT_EXCEPTION") from None
    return _interpret(outcome)


def _require_session(session: object) -> ProbeSession:
    if type(session) is not ProbeSession:
        raise ProbeError("MALFORMED_SESSION")
    return session


def _request_reason(method: object, url: object) -> str | None:
    decision = evaluate_paper_boundary(url, method)
    if decision.classification is not BoundaryClassification.PAPER_POLICY_CANDIDATE:
        if decision.reason == "PATH_DENIED" and isinstance(url, str):
            special = _special_path(url)
            if special is not None:
                return special
        return decision.reason
    if not isinstance(url, str):
        return "MALFORMED_TARGET"
    if _path(url) == ACCOUNT_PATH:
        return None
    return _special_path(url) or "PATH_DENIED"


def _special_path(url: str) -> str | None:
    folded = url.casefold()
    if "stream" in folded or "/events" in folded:
        return "STREAM_ROUTE_DENIED"
    if "/v2/orders" in folded:
        return "ORDER_ROUTE_DENIED"
    if "/v2/positions" in folded:
        return "POSITION_ROUTE_DENIED"
    return None


def _path(url: str) -> str:
    remainder = url.split("://", 1)[1]
    slash = remainder.find("/")
    if slash < 0:
        return ""
    return remainder[slash:]


def _require_runtime(runtime: object) -> None:
    if runtime is None:
        raise ProbeError("RUNTIME_UNAUTHORIZED")
    if type(runtime) is not RuntimeAuthorization:
        raise ProbeError("MALFORMED_RUNTIME")
    if type(runtime.platform) is not str or runtime.platform != "Windows":
        raise ProbeError("RUNTIME_PLATFORM_DENIED")


def _require_custody(custody: object) -> None:
    if type(custody) is not SyntheticCustody:
        raise ProbeError("MALFORMED_CUSTODY")
    if custody._denial is not None:
        raise ProbeError(custody._denial)


def _require_transport(transport: object) -> SyntheticTransport:
    if type(transport) is not SyntheticTransport:
        raise ProbeError("TRANSPORT_DENIED")
    if transport.calls != 0:
        raise ProbeError("MULTIPLE_GET_DENIED")
    return transport


def _interpret(outcome: ScriptedOutcome) -> ProbeDecision:
    fault = outcome.fault
    if fault is not None:
        if fault == "timeout":
            raise ProbeError("TIMEOUT")
        if fault == "network":
            raise ProbeError("NETWORK_DENIED")
        raise ProbeError("AMBIGUOUS_RESPONSE")
    if type(outcome.redirected) is not bool or type(outcome.status) is not int:
        raise ProbeError("AMBIGUOUS_RESPONSE")
    if outcome.redirected or 300 <= outcome.status < 400:
        raise ProbeError("REDIRECT_DENIED")
    if outcome.status == 200:
        reason = _body_reason(outcome._body)
        if reason is not None:
            raise ProbeError(reason)
        return ProbeDecision(ProbeClassification.ACCEPTED, "ACCOUNT_OBSERVED")
    raise ProbeError("UNEXPECTED_STATUS")


def _body_reason(body: object) -> str | None:
    if body is _MISSING_BODY:
        return "MISSING_BODY"
    if body is None:
        return "NULL_BODY"
    if type(body) is not dict:
        return "MALFORMED_BODY"
    if len(body) == 0:
        return "EMPTY_BODY"
    if any(type(key) is not str for key in body):
        return "MALFORMED_BODY"
    if "status" not in body:
        return "MISSING_STATUS"
    status = body["status"]
    if type(status) is not str or status == "" or status != status.strip():
        return "MALFORMED_STATUS"
    if status != _ACCEPTED_BODY_STATUS:
        return "UNSUPPORTED_STATUS"
    extras = [key for key in body if key != "status"]
    if not extras:
        return None
    for key in extras:
        value = body[key]
        if value is None or type(value) is bool or type(value) is str:
            return "CONTRADICTORY_BODY"
    return "AMBIGUOUS_RESPONSE"


def _custody_denial(
    entries: object,
    host: object,
    hosts: object,
    fault: object,
) -> str | None:
    named = _fault_name(fault)
    if named is not None:
        return _FAULT_REASONS.get(named, "MALFORMED_CUSTODY")
    if entries is None:
        return "MISSING_CUSTODY"
    if not isinstance(entries, dict):
        return "MALFORMED_CUSTODY"
    target_reason = _target_reason(entries)
    if target_reason is not None:
        return target_reason
    material_reason = _material_reason(entries)
    if material_reason is not None:
        return material_reason
    return _hosts_reason(host, hosts)


def _fault_name(fault: object) -> str | None:
    if fault is None:
        return None
    if type(fault) is str and fault in _FAULTS:
        return fault
    return "malformed"


def _target_reason(entries: dict[object, object]) -> str | None:
    names: list[str] = []
    for name in entries:
        if type(name) is not str or name == "":
            return "MALFORMED_CUSTODY"
        if name.startswith(_LIVE_TARGET_PREFIX):
            return "LIVE_TARGET_DENIED"
        if "live" in name.casefold():
            return "LIVE_NAME_DENIED"
        names.append(name)
    if len(names) != len(set(names)):
        return "AMBIGUOUS_CUSTODY"
    if any(name not in _PAPER_TARGETS for name in names):
        return "AMBIGUOUS_CUSTODY"
    if PAPER_KEY_ID_TARGET not in names:
        return "MISSING_KEY_ID"
    if PAPER_SECRET_TARGET not in names:
        return "MISSING_SECRET"
    return None


def _material_reason(entries: dict[object, object]) -> str | None:
    for name in _PAPER_TARGETS:
        value = entries[name]
        if isinstance(value, list):
            return "AMBIGUOUS_CUSTODY"
        if type(value) is not bytes:
            return "MALFORMED_MATERIAL"
        if value == b"":
            return "INCOMPLETE_MATERIAL"
        if any(byte < 33 or byte > 126 for byte in value):
            return "MALFORMED_MATERIAL"
    return None


def _hosts_reason(host: object, hosts: object) -> str | None:
    if host is not None and hosts is not None:
        return "AMBIGUOUS_CUSTODY"
    if hosts is not None:
        return _mapped_hosts(hosts)
    selected = PAPER_HOST if host is None else host
    if type(selected) is not str:
        return "MALFORMED_HOST"
    return _one_host(selected)


def _mapped_hosts(hosts: object) -> str | None:
    if not isinstance(hosts, dict):
        return "MALFORMED_HOST"
    if set(hosts) != set(_PAPER_TARGETS):
        return "AMBIGUOUS_CUSTODY"
    seen: list[str] = []
    for name in _PAPER_TARGETS:
        value = hosts[name]
        if type(value) is not str:
            return "MALFORMED_HOST"
        reason = _one_host(value)
        if reason is not None:
            return reason
        seen.append(value)
    if seen[0] != seen[1]:
        return "INCONSISTENT_CUSTODY"
    return None


def _one_host(host: str) -> str | None:
    if host == "":
        return "MALFORMED_HOST"
    if any(char == "\\" or ord(char) < 33 or ord(char) > 126 for char in host):
        return "MALFORMED_HOST"
    if "://" in host or "@" in host or "/" in host:
        return "MALFORMED_HOST"
    if host == PAPER_HOST:
        return None
    if host == LIVE_HOST:
        return "LIVE_HOST_DENIED"
    if host in _DENIED_HOSTS:
        return "HOST_DENIED"
    return "HOST_MISMATCH"
