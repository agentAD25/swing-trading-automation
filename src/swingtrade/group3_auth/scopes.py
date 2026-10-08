"""Initial read-only scope contract. Requested scope is not treated as granted."""

from __future__ import annotations

from swingtrade.contracts.monitoring import MonitoringEmitter
from swingtrade.group3_auth.monitoring import emit_auth_decision
from swingtrade.group3_auth.outcomes import AuthDecision, OutcomeCode, decision

INITIAL_READ_ONLY_SCOPES = frozenset({"openid", "ReadAccount"})
_ELEVATED = frozenset({"Trade", "MarketData", "Matrix", "OptionSpreads", "offline_access"})


class ScopeVerdict:
    """Fail-closed scope classification. No authorization request is sent."""

    __slots__ = ("connect_allowed", "decision", "network_permitted")

    def __init__(self, result: AuthDecision) -> None:
        self.decision = result
        self.connect_allowed = False
        self.network_permitted = False

    def __repr__(self) -> str:
        return f"ScopeVerdict({self.decision.reason})"


def requested_scope_text() -> str:
    """Stable request text for the initial profile. No other scope is added."""
    return "openid ReadAccount"


def validate_requested_scopes(
    scopes: object,
    *,
    emitter: MonitoringEmitter | None = None,
) -> ScopeVerdict:
    """Require exactly openid and ReadAccount. Do not add offline_access."""
    result = _requested(scopes)
    emit_auth_decision(emitter, result.decision)
    return result


def validate_granted_scopes(
    scopes: object,
    *,
    emitter: MonitoringEmitter | None = None,
) -> ScopeVerdict:
    """Deny a missing read scope and any unexpected elevated scope."""
    result = _granted(scopes)
    emit_auth_decision(emitter, result.decision)
    return result


def _requested(scopes: object) -> ScopeVerdict:
    parsed = _parse(scopes)
    if isinstance(parsed, AuthDecision):
        return ScopeVerdict(parsed)
    if parsed != INITIAL_READ_ONLY_SCOPES:
        return ScopeVerdict(decision(OutcomeCode.REJECTED, "REQUESTED_SCOPE_REJECTED"))
    return ScopeVerdict(decision(OutcomeCode.CLASSIFIED, "REQUESTED_SCOPE_ACCEPTED"))


def _granted(scopes: object) -> ScopeVerdict:
    parsed = _parse(scopes)
    if isinstance(parsed, AuthDecision):
        return ScopeVerdict(parsed)
    if "ReadAccount" not in parsed or "openid" not in parsed:
        return ScopeVerdict(decision(OutcomeCode.REJECTED, "MISSING_READ_SCOPE"))
    if parsed & _ELEVATED:
        return ScopeVerdict(decision(OutcomeCode.REJECTED, "UNEXPECTED_SCOPE_GRANTED"))
    if parsed != INITIAL_READ_ONLY_SCOPES:
        return ScopeVerdict(decision(OutcomeCode.REJECTED, "UNEXPECTED_SCOPE_GRANTED"))
    return ScopeVerdict(decision(OutcomeCode.CLASSIFIED, "GRANTED_SCOPE_ACCEPTED"))


def _parse(scopes: object) -> frozenset[str] | AuthDecision:
    if type(scopes) is str:
        if scopes != scopes.strip() or "  " in scopes or scopes == "":
            return decision(OutcomeCode.REJECTED, "MALFORMED_SCOPE")
        parts = scopes.split(" ")
    elif type(scopes) is frozenset or type(scopes) is set or type(scopes) is tuple:
        parts = list(scopes)
    else:
        return decision(OutcomeCode.REJECTED, "MALFORMED_SCOPE")
    copied: list[str] = []
    for part in parts:
        if type(part) is not str or part == "" or any(character.isspace() for character in part):
            return decision(OutcomeCode.REJECTED, "MALFORMED_SCOPE")
        copied.append(part)
    if len(copied) != len(set(copied)):
        return decision(OutcomeCode.REJECTED, "MALFORMED_SCOPE")
    return frozenset(copied)
