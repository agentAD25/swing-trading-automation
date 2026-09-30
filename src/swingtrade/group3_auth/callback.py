"""Classify a callback query. The authorization code is not retained."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import parse_qsl, urlsplit

from swingtrade.contracts.monitoring import MonitoringEmitter
from swingtrade.group3_auth.monitoring import emit_auth_decision
from swingtrade.group3_auth.outcomes import AuthDecision, OutcomeCode, decision
from swingtrade.group3_auth.state import StateIssuer

_MAX_CALLBACK = 4096
_IGNORED = frozenset({"error_description"})


class CallbackClassification:
    """State binding result. Query values are not rendered."""

    __slots__ = ("code_present", "decision")

    def __init__(self, result: AuthDecision, *, code_present: bool) -> None:
        self.decision = result
        self.code_present = code_present

    def __repr__(self) -> str:
        return "CallbackClassification"


def classify_callback(
    issuer: StateIssuer,
    raw: object,
    *,
    now: datetime,
    emitter: MonitoringEmitter | None = None,
) -> CallbackClassification:
    """Classify `code` plus `state`, or `error=access_denied`. Mismatched state fails closed."""
    if not isinstance(issuer, StateIssuer):
        result = CallbackClassification(
            decision(OutcomeCode.REJECTED, "MALFORMED_CALLBACK"),
            code_present=False,
        )
    else:
        result = _classify(issuer, raw, now=now)
    emit_auth_decision(emitter, result.decision)
    return result


def _classify(issuer: StateIssuer, raw: object, *, now: datetime) -> CallbackClassification:
    parsed = _parse(raw)
    if isinstance(parsed, AuthDecision):
        return CallbackClassification(parsed, code_present=False)
    state, kind = parsed
    bound = issuer.consume(state, now=now)
    if bound.code is not OutcomeCode.CLASSIFIED:
        return CallbackClassification(bound, code_present=False)
    if kind == "CODE":
        return CallbackClassification(
            decision(OutcomeCode.CLASSIFIED, "AUTHORIZATION_CODE"),
            code_present=True,
        )
    if kind == "ACCESS_DENIED":
        return CallbackClassification(
            decision(OutcomeCode.CLASSIFIED, "ACCESS_DENIED"),
            code_present=False,
        )
    return CallbackClassification(decision(OutcomeCode.UNKNOWN, "UNKNOWN"), code_present=False)


def _query(raw: str) -> tuple[str | None, bool]:
    if "://" in raw:
        if "@" in raw.split("?", 1)[0]:
            return None, False
        try:
            parts = urlsplit(raw)
        except ValueError:
            return None, False
        if parts.hostname == "api.tradestation.com":
            return None, True
        if parts.scheme != "https" or parts.fragment != "":
            return None, False
        return parts.query, False
    if raw.startswith("?"):
        return raw[1:], False
    if "=" in raw:
        return raw, False
    return None, False


def _parse(raw: object) -> AuthDecision | tuple[str, str]:
    if type(raw) is not str or raw == "" or len(raw) > _MAX_CALLBACK:
        return decision(OutcomeCode.REJECTED, "MALFORMED_CALLBACK")
    if any(character.isspace() for character in raw) or "\\" in raw:
        return decision(OutcomeCode.REJECTED, "MALFORMED_CALLBACK")
    query, live = _query(raw)
    if live:
        return decision(OutcomeCode.REJECTED, "LIVE_HOST_PROHIBITED")
    if query is None:
        return decision(OutcomeCode.REJECTED, "MALFORMED_CALLBACK")
    try:
        pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        return decision(OutcomeCode.REJECTED, "MALFORMED_CALLBACK")
    seen: set[str] = set()
    state: str | None = None
    code_present = False
    error: str | None = None
    for key, value in pairs:
        if key in seen:
            return decision(OutcomeCode.REJECTED, "MALFORMED_CALLBACK")
        seen.add(key)
        if key in _IGNORED:
            continue
        if key == "state":
            state = value
            continue
        if key == "code":
            if value == "":
                return decision(OutcomeCode.REJECTED, "MALFORMED_CALLBACK")
            code_present = True
            continue
        if key == "error":
            error = value
            continue
        return decision(OutcomeCode.UNKNOWN, "UNKNOWN")
    if state is None or state == "":
        return decision(OutcomeCode.REJECTED, "MISSING_STATE")
    if code_present and error is not None:
        return state, "CONTRADICTORY"
    if code_present:
        return state, "CODE"
    if error == "access_denied":
        return state, "ACCESS_DENIED"
    if error is None:
        return decision(OutcomeCode.REJECTED, "MALFORMED_CALLBACK")
    return state, "UNKNOWN_ERROR"
