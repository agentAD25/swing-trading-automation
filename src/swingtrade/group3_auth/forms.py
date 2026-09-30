"""Token and refresh form templates. Nothing here is posted."""

from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import quote, urlencode

from swingtrade.contracts.monitoring import MonitoringEmitter
from swingtrade.group3_auth.flow import FlowMode, parse_flow
from swingtrade.group3_auth.monitoring import emit_auth_decision
from swingtrade.group3_auth.outcomes import AuthDecision, OutcomeCode, decision
from swingtrade.group3_auth.request import _verifier_text

TOKEN_ENDPOINT = "https://signin.tradestation.com/oauth/token"
FORM_CONTENT_TYPE = "application/x-www-form-urlencoded"
_SECRET_FIELDS = frozenset(
    {"access_token", "client_secret", "code", "code_verifier", "id_token", "refresh_token"}
)


class FormTemplate:
    """urlencoded body that is not transmitted. Rendering omits values."""

    __slots__ = (
        "body",
        "connect_allowed",
        "content_type",
        "decision",
        "method",
        "parameter_names",
        "url",
    )

    def __init__(
        self,
        result: AuthDecision,
        *,
        method: str,
        url: str,
        parameter_names: tuple[str, ...],
        body: str,
    ) -> None:
        self.decision = result
        self.method = method
        self.url = url
        self.content_type = FORM_CONTENT_TYPE
        self.parameter_names = parameter_names
        self.body = body
        self.connect_allowed = False

    def __repr__(self) -> str:
        names = ",".join(self.parameter_names)
        return f"FormTemplate({self.decision.reason}, {names})"


class TokenFixture:
    """Non-secret fields copied from a response fixture."""

    __slots__ = (
        "access_present",
        "decision",
        "expires_in",
        "id_present",
        "refresh_present",
        "scope",
        "token_type",
    )

    def __init__(
        self,
        result: AuthDecision,
        *,
        expires_in: int | None,
        token_type: str | None,
        scope: str | None,
        access_present: bool,
        refresh_present: bool,
        id_present: bool,
    ) -> None:
        self.decision = result
        self.expires_in = expires_in
        self.token_type = token_type
        self.scope = scope
        self.access_present = access_present
        self.refresh_present = refresh_present
        self.id_present = id_present

    def __repr__(self) -> str:
        return "TokenFixture"


def authorization_code_form(
    *,
    flow: object,
    client_id: object,
    redirect_uri: object,
    code: object,
    client_secret: object = None,
    code_verifier: object = None,
    emitter: MonitoringEmitter | None = None,
) -> FormTemplate:
    """Standard flow includes `client_secret`. PKCE includes `code_verifier` instead."""
    mode = parse_flow(flow)
    if mode is None:
        result = _empty(decision(OutcomeCode.REJECTED, "UNKNOWN_FLOW"))
    elif mode is FlowMode.STANDARD:
        result = _standard_exchange(client_id, redirect_uri, code, client_secret, code_verifier)
    else:
        result = _pkce_exchange(client_id, redirect_uri, code, client_secret, code_verifier)
    emit_auth_decision(emitter, result.decision)
    return result


def refresh_form(
    *,
    flow: object,
    client_id: object,
    refresh_token: object,
    client_secret: object = None,
    emitter: MonitoringEmitter | None = None,
) -> FormTemplate:
    """Refresh parameter names only. No rotation interval is selected."""
    mode = parse_flow(flow)
    if mode is None:
        result = _empty(decision(OutcomeCode.REJECTED, "UNKNOWN_FLOW"))
    elif mode is FlowMode.STANDARD:
        result = _standard_refresh(client_id, refresh_token, client_secret)
    else:
        result = _pkce_refresh(client_id, refresh_token, client_secret)
    emit_auth_decision(emitter, result.decision)
    return result


def read_token_fixture(
    payload: object,
    *,
    emitter: MonitoringEmitter | None = None,
) -> TokenFixture:
    """Read documented response names from a fixture. `expires_in` is not invented."""
    result = _read_fixture(payload)
    emit_auth_decision(emitter, result.decision)
    return result


def _standard_exchange(
    client_id: object,
    redirect_uri: object,
    code: object,
    client_secret: object,
    code_verifier: object,
) -> FormTemplate:
    if code_verifier is not None:
        return _empty(decision(OutcomeCode.REJECTED, "PKCE_NOT_IN_STANDARD_FLOW"))
    fields = _required(
        client_id=client_id,
        client_secret=client_secret,
        code=code,
        redirect_uri=redirect_uri,
    )
    if isinstance(fields, AuthDecision):
        return _empty(fields)
    pairs = [
        ("grant_type", "authorization_code"),
        ("client_id", fields["client_id"]),
        ("client_secret", fields["client_secret"]),
        ("code", fields["code"]),
        ("redirect_uri", fields["redirect_uri"]),
    ]
    return _form(pairs)


def _pkce_exchange(
    client_id: object,
    redirect_uri: object,
    code: object,
    client_secret: object,
    code_verifier: object,
) -> FormTemplate:
    if client_secret is not None:
        return _empty(decision(OutcomeCode.REJECTED, "CLIENT_SECRET_NOT_IN_PKCE"))
    verifier = _verifier(code_verifier)
    if verifier is None:
        return _empty(decision(OutcomeCode.REJECTED, "PKCE_VERIFIER_REJECTED"))
    fields = _required(client_id=client_id, code=code, redirect_uri=redirect_uri)
    if isinstance(fields, AuthDecision):
        return _empty(fields)
    pairs = [
        ("grant_type", "authorization_code"),
        ("client_id", fields["client_id"]),
        ("code", fields["code"]),
        ("redirect_uri", fields["redirect_uri"]),
        ("code_verifier", verifier),
    ]
    return _form(pairs)


def _standard_refresh(
    client_id: object,
    refresh_token: object,
    client_secret: object,
) -> FormTemplate:
    fields = _required(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
    )
    if isinstance(fields, AuthDecision):
        return _empty(fields)
    pairs = [
        ("grant_type", "refresh_token"),
        ("client_id", fields["client_id"]),
        ("client_secret", fields["client_secret"]),
        ("refresh_token", fields["refresh_token"]),
    ]
    return _form(pairs)


def _pkce_refresh(
    client_id: object,
    refresh_token: object,
    client_secret: object,
) -> FormTemplate:
    if client_secret is not None:
        return _empty(decision(OutcomeCode.REJECTED, "CLIENT_SECRET_NOT_IN_PKCE"))
    fields = _required(client_id=client_id, refresh_token=refresh_token)
    if isinstance(fields, AuthDecision):
        return _empty(fields)
    pairs = [
        ("grant_type", "refresh_token"),
        ("client_id", fields["client_id"]),
        ("refresh_token", fields["refresh_token"]),
    ]
    return _form(pairs)


def _required(**values: object) -> dict[str, str] | AuthDecision:
    copied: dict[str, str] = {}
    for name, value in values.items():
        text = _single_token(value)
        if text is None:
            return decision(OutcomeCode.REJECTED, "MISSING_INPUT")
        copied[name] = text
    return copied


def _single_token(value: object) -> str | None:
    if type(value) is not str or value == "":
        return None
    if any(character.isspace() or ord(character) < 32 for character in value):
        return None
    return value


def _verifier(value: object) -> str | None:
    return _verifier_text(value)


def _form(pairs: list[tuple[str, str]]) -> FormTemplate:
    names = tuple(name for name, _value in pairs)
    if "expires_in" in names or any(name.endswith("_minutes") for name in names):
        return _empty(decision(OutcomeCode.REJECTED, "REFRESH_INTERVAL_PROHIBITED"))
    body = urlencode(pairs, quote_via=quote)
    return FormTemplate(
        decision(OutcomeCode.ASSEMBLED, "FORM_TEMPLATE"),
        method="POST",
        url=TOKEN_ENDPOINT,
        parameter_names=names,
        body=body,
    )


def _empty(result: AuthDecision) -> FormTemplate:
    return FormTemplate(
        result,
        method="POST",
        url=TOKEN_ENDPOINT,
        parameter_names=(),
        body="",
    )


def _read_fixture(payload: object) -> TokenFixture:
    if not isinstance(payload, Mapping):
        return _fixture(decision(OutcomeCode.REJECTED, "MALFORMED_RESPONSE"))
    keys: set[str] = set()
    for key in payload:
        if not isinstance(key, str):
            return _fixture(decision(OutcomeCode.REJECTED, "MALFORMED_RESPONSE"))
        keys.add(key)
    unknown = keys.difference(
        {"access_token", "refresh_token", "id_token", "token_type", "scope", "expires_in"}
    )
    if unknown:
        return _fixture(decision(OutcomeCode.UNKNOWN, "UNKNOWN"))
    if "access_token" not in payload or "expires_in" not in payload or "token_type" not in payload:
        return _fixture(decision(OutcomeCode.REJECTED, "MISSING_INPUT"))
    expires = _positive_int(payload["expires_in"])
    token_type = payload["token_type"]
    scope = payload.get("scope")
    if expires is None:
        return _fixture(decision(OutcomeCode.REJECTED, "EXPIRES_IN_REJECTED"))
    if type(token_type) is not str or token_type == "":
        return _fixture(decision(OutcomeCode.REJECTED, "MALFORMED_RESPONSE"))
    if token_type != "Bearer":
        return _fixture(decision(OutcomeCode.UNKNOWN, "UNKNOWN"))
    scope_text: str | None
    if scope is None:
        scope_text = None
    elif type(scope) is str:
        scope_text = scope
    else:
        return _fixture(decision(OutcomeCode.UNKNOWN, "UNKNOWN"))
    for name in _SECRET_FIELDS:
        if name in payload and type(payload[name]) is not str:
            return _fixture(decision(OutcomeCode.REJECTED, "MALFORMED_RESPONSE"))
    return TokenFixture(
        decision(OutcomeCode.CLASSIFIED, "TOKEN_FIXTURE"),
        expires_in=expires,
        token_type=token_type,
        scope=scope_text,
        access_present=True,
        refresh_present="refresh_token" in payload,
        id_present="id_token" in payload,
    )


def _positive_int(value: object) -> int | None:
    if isinstance(value, int) and type(value) is int and value > 0:
        return value
    return None


def _fixture(result: AuthDecision) -> TokenFixture:
    return TokenFixture(
        result,
        expires_in=None,
        token_type=None,
        scope=None,
        access_present=False,
        refresh_present=False,
        id_present=False,
    )
