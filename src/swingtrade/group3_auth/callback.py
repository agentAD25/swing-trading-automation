"""Classify a callback query. The authorization code is not retained."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime
from urllib.parse import parse_qsl, urlsplit

from swingtrade.contracts.monitoring import MonitoringEmitter
from swingtrade.group3_auth.monitoring import emit_auth_decision
from swingtrade.group3_auth.outcomes import AuthDecision, OutcomeCode, decision
from swingtrade.group3_auth.state import StateIssuer
from swingtrade.offline.hosts import live_authority_prohibited

_MAX_CALLBACK = 4096
_IGNORED = frozenset({"error_description"})
_HOST = re.compile(
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+"
)
_CONTRACT_KINDS = frozenset({"CODE", "ACCESS_DENIED"})


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
    allowed_callbacks: Iterable[str],
    emitter: MonitoringEmitter | None = None,
) -> CallbackClassification:
    """Classify an allowlisted callback. Hostile authorities do not consume state."""
    allowed = _allowlist(allowed_callbacks)
    if isinstance(allowed, AuthDecision):
        result = CallbackClassification(allowed, code_present=False)
    elif not isinstance(issuer, StateIssuer):
        result = CallbackClassification(
            decision(OutcomeCode.REJECTED, "MALFORMED_CALLBACK"),
            code_present=False,
        )
    else:
        result = _classify(issuer, raw, now=now, allowed=allowed)
    emit_auth_decision(emitter, result.decision)
    return result


def _classify(
    issuer: StateIssuer,
    raw: object,
    *,
    now: datetime,
    allowed: frozenset[str],
) -> CallbackClassification:
    if type(raw) is not str or raw == "" or len(raw) > _MAX_CALLBACK:
        return _closed(decision(OutcomeCode.REJECTED, "MALFORMED_CALLBACK"))
    if live_authority_prohibited(raw):
        return _closed(decision(OutcomeCode.REJECTED, "LIVE_HOST_PROHIBITED"))
    if any(character.isspace() for character in raw) or "\\" in raw:
        return _closed(decision(OutcomeCode.REJECTED, "MALFORMED_CALLBACK"))
    located = _callback_base(raw)
    if located is None:
        reason = "MALFORMED_CALLBACK" if "://" not in raw else "CALLBACK_AUTHORITY_REJECTED"
        return _closed(decision(OutcomeCode.REJECTED, reason))
    base, query = located
    if base not in allowed:
        return _closed(decision(OutcomeCode.REJECTED, "CALLBACK_AUTHORITY_REJECTED"))
    parsed = _parse_query(query)
    if isinstance(parsed, AuthDecision):
        return _closed(parsed)
    state, kind = parsed
    bound = issuer.validate(state, now=now)
    if bound.code is not OutcomeCode.CLASSIFIED:
        return _closed(bound)
    if kind not in _CONTRACT_KINDS:
        return _closed(decision(OutcomeCode.UNKNOWN, "UNKNOWN"))
    consumed = issuer.consume(state, now=now)
    if consumed.code is not OutcomeCode.CLASSIFIED:
        return _closed(consumed)
    if kind == "CODE":
        return CallbackClassification(
            decision(OutcomeCode.CLASSIFIED, "AUTHORIZATION_CODE"),
            code_present=True,
        )
    return CallbackClassification(
        decision(OutcomeCode.CLASSIFIED, "ACCESS_DENIED"),
        code_present=False,
    )


def _closed(result: AuthDecision) -> CallbackClassification:
    return CallbackClassification(result, code_present=False)


def _allowlist(values: object) -> frozenset[str] | AuthDecision:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        return decision(OutcomeCode.REJECTED, "MALFORMED_CALLBACK")
    chosen: list[str] = []
    for item in values:
        if type(item) is not str or not _canonical_redirect(item) or item in chosen:
            return decision(OutcomeCode.REJECTED, "MALFORMED_CALLBACK")
        chosen.append(item)
    return frozenset(chosen)


def _canonical_redirect(value: str) -> bool:
    located = _callback_base(value)
    return located is not None and located[1] == ""


def _callback_base(raw: str) -> tuple[str, str] | None:
    """Exact https origin and path. Noncanonical forms are not rewritten."""
    if not raw.startswith("https://"):
        return None
    try:
        parts = urlsplit(raw)
    except ValueError:
        return None
    if (
        parts.scheme != "https"
        or parts.fragment != ""
        or parts.username is not None
        or parts.password is not None
        or parts.port is not None
    ):
        return None
    netloc = parts.netloc
    path = parts.path
    if (
        "%" in netloc
        or "%" in path
        or "@" in netloc
        or netloc != netloc.lower()
        or netloc.endswith(".")
        or ".." in netloc
        or _HOST.fullmatch(netloc) is None
        or not path.startswith("/")
        or "//" in path
    ):
        return None
    if any(segment in {"", ".", ".."} for segment in path.split("/")[1:]):
        return None
    base = f"https://{netloc}{path}"
    query = parts.query
    expected = base if query == "" else f"{base}?{query}"
    if raw != expected:
        return None
    return base, query


def _parse_query(query: str) -> AuthDecision | tuple[str, str]:
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
