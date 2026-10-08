"""Fail-closed broker destination policy. Naming a host does not open a socket."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from urllib.parse import urlsplit

from swingtrade.contracts.monitoring import MonitoringEmitter
from swingtrade.group3_auth.monitoring import emit_auth_decision
from swingtrade.group3_auth.outcomes import AuthDecision, OutcomeCode, decision
from swingtrade.offline.hosts import live_authority_prohibited

_SIM_HOST = "sim-api.tradestation.com"
_AUTH_HOST = "signin.tradestation.com"
_SIM_PREFIX = "https://sim-api.tradestation.com/v3"
_AUTH_URLS = frozenset(
    {
        "https://signin.tradestation.com/authorize",
        "https://signin.tradestation.com/oauth/token",
    }
)
_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_HOST_MARKERS = ("HOST", "URL", "BASE", "PROXY", "DNS")
_MAX_INPUT = 2048


class ExecutionPosture(StrEnum):
    """The only posture this boundary can boot. SIM and LIVE are not members."""

    DRY_RUN = "DRY_RUN"


class EndpointClass(StrEnum):
    AUTH = "AUTH"
    BROKERAGE_SIM = "BROKERAGE_SIM"
    BROKERAGE_LIVE = "BROKERAGE_LIVE"
    UNKNOWN = "UNKNOWN"


class BoundaryError(RuntimeError):
    """Reason code only. URLs and header values are not part of the message."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class DestinationVerdict:
    """A denied destination. Connection and order placement stay false."""

    __slots__ = (
        "connect_allowed",
        "decision",
        "endpoint_class",
        "network_permitted",
        "order_placement_permitted",
    )

    def __init__(self, result: AuthDecision, endpoint_class: EndpointClass) -> None:
        self.decision = result
        self.endpoint_class = endpoint_class
        self.connect_allowed = False
        self.network_permitted = False
        self.order_placement_permitted = False

    def __repr__(self) -> str:
        return f"DestinationVerdict({self.decision.reason})"


class DryRunContext:
    """Boot identity. Network, credentials, SIM connect, and LIVE stay off."""

    __slots__ = (
        "broker_credentials_allowed",
        "live_enabled",
        "network_allowed",
        "posture",
        "sim_connect_allowed",
    )

    def __init__(self, posture: ExecutionPosture) -> None:
        if posture is not ExecutionPosture.DRY_RUN:
            raise BoundaryError("POSTURE_DENIED")
        self.posture = posture
        self.network_allowed = False
        self.broker_credentials_allowed = False
        self.live_enabled = False
        self.sim_connect_allowed = False

    def __repr__(self) -> str:
        return "DryRunContext(DRY_RUN)"


def parse_posture(value: object) -> ExecutionPosture:
    """Accept only the DRY_RUN enum or that exact string. Anything else fails."""
    if value is ExecutionPosture.DRY_RUN:
        return ExecutionPosture.DRY_RUN
    if type(value) is str and value == "DRY_RUN":
        return ExecutionPosture.DRY_RUN
    if value is None or value == "":
        raise BoundaryError("MISSING_POSTURE")
    raise BoundaryError("POSTURE_DENIED")


def boot_dry_run(value: object) -> DryRunContext:
    """Start or recover. Missing, SIM, LIVE, and ambiguous identities fail closed."""
    return DryRunContext(parse_posture(value))


def evaluate_destination(
    posture: object,
    candidate: object,
    *,
    method: object = "GET",
    redirect_to: object = None,
    header_host: object = None,
    configured_host: object = None,
    emitter: MonitoringEmitter | None = None,
) -> DestinationVerdict:
    """Classify one destination and deny the network. Overrides are not applied."""
    result = _evaluate(
        posture,
        candidate,
        method=method,
        redirect_to=redirect_to,
        header_host=header_host,
        configured_host=configured_host,
    )
    emit_auth_decision(emitter, result.decision)
    return result


def evaluate_environment(
    posture: object,
    candidate: object,
    environ: Mapping[str, object],
    *,
    method: object = "GET",
    emitter: MonitoringEmitter | None = None,
) -> DestinationVerdict:
    """Ignore broker host variables. A LIVE value is a safety violation."""
    if not isinstance(environ, Mapping):
        result = _verdict(decision(OutcomeCode.REJECTED, "HOST_OVERRIDE_DENIED"))
        emit_auth_decision(emitter, result.decision)
        return result
    for key, raw in environ.items():
        if type(key) is not str or not _host_key(key):
            continue
        if _contains_live(raw):
            result = _verdict(
                decision(OutcomeCode.REJECTED, "LIVE_HOST_PROHIBITED"),
                EndpointClass.BROKERAGE_LIVE,
            )
            emit_auth_decision(emitter, result.decision)
            return result
        result = _verdict(decision(OutcomeCode.REJECTED, "HOST_OVERRIDE_DENIED"))
        emit_auth_decision(emitter, result.decision)
        return result
    return evaluate_destination(posture, candidate, method=method, emitter=emitter)


def _evaluate(
    posture: object,
    candidate: object,
    *,
    method: object,
    redirect_to: object,
    header_host: object,
    configured_host: object,
) -> DestinationVerdict:
    try:
        parse_posture(posture)
    except BoundaryError as exc:
        return _verdict(decision(OutcomeCode.REJECTED, exc.reason))
    live_override = (
        _contains_live(redirect_to)
        or _contains_live(header_host)
        or _contains_live(configured_host)
    )
    if live_override:
        return _verdict(
            decision(OutcomeCode.REJECTED, "LIVE_HOST_PROHIBITED"),
            EndpointClass.BROKERAGE_LIVE,
        )
    if redirect_to is not None:
        return _verdict(decision(OutcomeCode.REJECTED, "REDIRECT_DENIED"))
    if header_host is not None or configured_host is not None:
        return _verdict(decision(OutcomeCode.REJECTED, "HOST_OVERRIDE_DENIED"))
    if type(method) is not str or method == "" or method != method.upper():
        return _verdict(decision(OutcomeCode.REJECTED, "METHOD_REJECTED"))
    if _contains_live(candidate):
        return _verdict(
            decision(OutcomeCode.REJECTED, "LIVE_HOST_PROHIBITED"),
            EndpointClass.BROKERAGE_LIVE,
        )
    classified = _classify_candidate(candidate)
    if classified is None:
        return _verdict(decision(OutcomeCode.REJECTED, "UNKNOWN_DESTINATION"))
    endpoint_class, path = classified
    if endpoint_class is EndpointClass.AUTH:
        return _verdict(
            decision(OutcomeCode.REJECTED, "AUTH_ENDPOINT_CONNECT_DENIED"),
            endpoint_class,
        )
    if _order_path(path) or method in _WRITE_METHODS:
        return _verdict(decision(OutcomeCode.REJECTED, "ORDER_PLACEMENT_DENIED"), endpoint_class)
    return _verdict(decision(OutcomeCode.REJECTED, "SIM_CONNECT_DENIED"), endpoint_class)


def _classify_candidate(candidate: object) -> tuple[EndpointClass, str] | None:
    if type(candidate) is not str or candidate == "" or len(candidate) > _MAX_INPUT:
        return None
    if any(character.isspace() or ord(character) < 32 for character in candidate):
        return None
    try:
        parts = urlsplit(candidate)
    except ValueError:
        return None
    host = parts.hostname
    if host is None or parts.username or parts.password or parts.port is not None:
        return None
    if parts.scheme != "https" or parts.fragment or "\\" in candidate:
        return None
    path = parts.path
    if ".." in path.split("/"):
        return None
    if host == _AUTH_HOST and candidate.split("?", 1)[0] in _AUTH_URLS and parts.query == "":
        return EndpointClass.AUTH, path
    if host == _SIM_HOST and candidate.split("?", 1)[0].startswith(_SIM_PREFIX):
        if path != "/v3" and not path.startswith("/v3/"):
            return None
        return EndpointClass.BROKERAGE_SIM, path
    return None


def _order_path(path: str) -> bool:
    lowered = path.lower()
    return "orderexecution" in lowered or lowered.endswith("/orderconfirm")


def _contains_live(raw: object) -> bool:
    return live_authority_prohibited(raw)


def _host_key(key: str) -> bool:
    upper = key.upper()
    return any(marker in upper for marker in _HOST_MARKERS)


def _verdict(
    result: AuthDecision,
    endpoint_class: EndpointClass = EndpointClass.UNKNOWN,
) -> DestinationVerdict:
    return DestinationVerdict(result, endpoint_class)
