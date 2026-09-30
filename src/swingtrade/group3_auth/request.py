"""Assemble an authorization URL. The documented audience is copied, not chosen."""

from __future__ import annotations

import base64
import hashlib
from datetime import datetime
from urllib.parse import quote, urlencode

from swingtrade.contracts.monitoring import MonitoringEmitter
from swingtrade.group3_auth.flow import FlowMode, parse_flow
from swingtrade.group3_auth.monitoring import emit_auth_decision
from swingtrade.group3_auth.outcomes import AuthDecision, AuthModelError, OutcomeCode, decision
from swingtrade.group3_auth.state import StateIssuer

AUTHORIZE_ENDPOINT = "https://signin.tradestation.com/authorize"
DOCUMENTED_AUDIENCE = "https://api.tradestation.com"


class AuthorizationAssembly:
    """Query string for a request that is not sent."""

    __slots__ = ("decision", "parameter_names", "url")

    def __init__(
        self,
        result: AuthDecision,
        url: str | None,
        parameter_names: tuple[str, ...],
    ) -> None:
        self.decision = result
        self.url = url
        self.parameter_names = parameter_names

    def __repr__(self) -> str:
        return "AuthorizationAssembly"


def _text(value: object) -> str | None:
    if type(value) is not str or value == "":
        return None
    if any(character.isspace() or ord(character) < 32 for character in value):
        return None
    return value


def s256_challenge(verifier: str) -> str:
    """S256 challenge. The verifier is not retained."""
    if _verifier_text(verifier) is None:
        raise AuthModelError("PKCE_VERIFIER_REJECTED")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _verifier_text(value: object) -> str | None:
    if type(value) is not str or not 43 <= len(value) <= 128:
        return None
    if any(ord(character) < 33 or ord(character) > 126 for character in value):
        return None
    return value


def assemble_authorization_request(
    *,
    flow: object,
    client_id: object,
    redirect_uri: object,
    scope: object,
    issuer: StateIssuer,
    issued_at: datetime,
    expires_at: datetime,
    prompt: object = None,
    code_verifier: object = None,
    emitter: MonitoringEmitter | None = None,
) -> AuthorizationAssembly:
    """Build one authorize URL. Scope, client, and redirect are explicit inputs."""
    result, url, names = _assemble(
        flow=flow,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        issuer=issuer,
        issued_at=issued_at,
        expires_at=expires_at,
        prompt=prompt,
        code_verifier=code_verifier,
    )
    emit_auth_decision(emitter, result)
    return AuthorizationAssembly(result, url, names)


def _assemble(
    *,
    flow: object,
    client_id: object,
    redirect_uri: object,
    scope: object,
    issuer: StateIssuer,
    issued_at: datetime,
    expires_at: datetime,
    prompt: object,
    code_verifier: object,
) -> tuple[AuthDecision, str | None, tuple[str, ...]]:
    mode = parse_flow(flow)
    if mode is None:
        return decision(OutcomeCode.REJECTED, "UNKNOWN_FLOW"), None, ()
    if not isinstance(issuer, StateIssuer):
        return decision(OutcomeCode.REJECTED, "MISSING_STATE"), None, ()
    client = _text(client_id)
    redirect = _text(redirect_uri)
    scope_text = _scope(scope)
    if client is None or redirect is None or scope_text is None:
        return decision(OutcomeCode.REJECTED, "MISSING_INPUT"), None, ()
    prompt_text = _prompt(prompt)
    if prompt is not None and prompt_text is None:
        return decision(OutcomeCode.UNKNOWN, "UNKNOWN_PROMPT"), None, ()
    challenge = _challenge(mode, code_verifier)
    if isinstance(challenge, AuthDecision):
        return challenge, None, ()
    try:
        issued = issuer.issue(issued_at=issued_at, expires_at=expires_at)
    except AuthModelError as exc:
        return decision(OutcomeCode.REJECTED, exc.reason), None, ()
    pairs: list[tuple[str, str]] = [
        ("response_type", "code"),
        ("client_id", client),
        ("redirect_uri", redirect),
        ("audience", DOCUMENTED_AUDIENCE),
        ("scope", scope_text),
        ("state", issued.value),
    ]
    if prompt_text is not None:
        pairs.append(("prompt", prompt_text))
    if challenge is not None:
        pairs.append(("code_challenge", challenge))
        pairs.append(("code_challenge_method", "S256"))
    query = urlencode(pairs, quote_via=quote)
    return (
        decision(OutcomeCode.ASSEMBLED, "AUTHORIZATION_REQUEST"),
        f"{AUTHORIZE_ENDPOINT}?{query}",
        tuple(name for name, _value in pairs),
    )


def _scope(value: object) -> str | None:
    """Keep the caller-supplied scope text. Do not insert or remove a scope."""
    if type(value) is not str or value == "":
        return None
    if any(ord(character) < 32 for character in value):
        return None
    if value != value.strip() or "  " in value:
        return None
    return value


def _prompt(value: object) -> str | None:
    if value is None:
        return None
    if value == "login":
        return "login"
    return None


def _challenge(mode: FlowMode, verifier: object) -> str | None | AuthDecision:
    if mode is FlowMode.STANDARD:
        if verifier is not None:
            return decision(OutcomeCode.REJECTED, "PKCE_NOT_IN_STANDARD_FLOW")
        return None
    checked = _verifier_text(verifier)
    if checked is None:
        return decision(OutcomeCode.REJECTED, "PKCE_VERIFIER_REJECTED")
    try:
        return s256_challenge(checked)
    except AuthModelError:
        return decision(OutcomeCode.REJECTED, "PKCE_VERIFIER_REJECTED")
