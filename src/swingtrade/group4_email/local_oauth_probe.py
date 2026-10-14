"""Offline Desktop OAuth profile-probe shapes.

Gate B validates synthetic requests and responses. It does not open a
socket, a browser, a credential store, or a provider connection.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

_METADATA_SCOPE = "https://www.googleapis.com/auth/gmail.metadata"
_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
_PROFILE_ENDPOINT = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
_PROFILE_METHOD = "GET"
_MAX_CALLBACK_WAIT = 120
_VERIFIER_PATTERN = re.compile(r"^[A-Za-z0-9\-._~]{43,128}$")
_UNRESERVED = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
_CALLBACK_PASS = "CALLBACK_SHAPE_PASS"
_SCOPE_PASS = "SCOPE_EXACT"
_TOKEN_PASS = "TOKEN_SHAPE_PASS"
_PROFILE_PASS = "GMAIL_OAUTH_PROFILE_SHAPE_PASS"
_CODES = frozenset(
    {
        "GMAIL_OAUTH_STATE_REJECTED",
        "GMAIL_OAUTH_PKCE_REJECTED",
        "GMAIL_OAUTH_CALLBACK_REJECTED",
        "GMAIL_OAUTH_REDIRECT_REJECTED",
        "GMAIL_OAUTH_SCOPE_REJECTED",
        "GMAIL_OAUTH_TOKEN_REJECTED",
        "GMAIL_OAUTH_PROFILE_REJECTED",
        "GMAIL_OAUTH_ENDPOINT_REJECTED",
        "GMAIL_OAUTH_LIVE_UNAUTHORIZED",
    }
)
_TOKEN_FORM_KEYS = ("grant_type", "code", "code_verifier", "client_id", "redirect_uri")
_AUTH_PARAMETER_KEYS = (
    "response_type",
    "client_id",
    "redirect_uri",
    "scope",
    "code_challenge",
    "code_challenge_method",
    "state",
)


class LocalOAuthProbeRejected(Exception):
    """Fail-closed probe error. Public text is the stable code only."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or code not in _CODES:
            code = "fail_closed"
        super().__init__(code)
        self.code = code

    def __repr__(self) -> str:
        return self.code

    def __str__(self) -> str:
        return self.code


@dataclass(frozen=True)
class LocalOAuthProbeEvidence:
    """Non-identifying offline shape result. Provider values are absent."""

    callback_result: str
    scope_result: str
    token_exchange_result: str
    profile_result: str
    content_retained: bool

    def __post_init__(self) -> None:
        if (
            self.callback_result != _CALLBACK_PASS
            or self.scope_result != _SCOPE_PASS
            or self.token_exchange_result != _TOKEN_PASS
            or self.profile_result != _PROFILE_PASS
            or self.content_retained is not False
        ):
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_PROFILE_REJECTED")


@dataclass(frozen=True)
class DesktopClientConfig:
    """Synthetic Desktop client fields. This object is not a downloaded file."""

    client_type: str
    redirect_host: str
    redirect_path: str
    scopes: tuple[str, ...]
    network_permitted: bool
    client_id: str = field(repr=False)
    redirect_port: int | None = None


@dataclass(frozen=True)
class AuthorizationRequest:
    """Allowlisted authorization shape. Parameters stay out of ordinary repr."""

    endpoint: str
    parameters: tuple[tuple[str, str], ...] = field(repr=False)


@dataclass(frozen=True)
class TokenRequest:
    """Allowlisted token form. The form stays out of ordinary repr."""

    endpoint: str
    form: tuple[tuple[str, str], ...] = field(repr=False)


@dataclass(frozen=True)
class ProfileRequest:
    """The one allowlisted profile read. The body is empty."""

    method: str
    url: str
    body: bytes


class ProbeHttp(Protocol):
    """Synthetic transport. This module does not construct a live client."""

    def post_form(self, endpoint: str, form: Mapping[str, str]) -> Mapping[str, object]:
        """Return a synthetic token response."""

    def get_profile(self, endpoint: str, body: bytes) -> Mapping[str, object]:
        """Return a synthetic profile response."""


class ProbeListener(Protocol):
    """Synthetic loopback boundary. This module does not bind a socket."""

    def bind(self) -> int:
        """Return the port chosen for this attempt."""

    def wait(self, timeout_seconds: int) -> tuple[tuple[str, str], ...] | None:
        """Return callback pairs, or None when the wait expires."""


class ProbeClock(Protocol):
    """Synthetic clock. A negative test can move it past the callback limit."""

    def monotonic(self) -> float:
        """Return seconds from an arbitrary origin."""


class ProbeBrowser(Protocol):
    """Synthetic launcher. This module does not open a browser."""

    def open(self, request: AuthorizationRequest) -> None:
        """Observe one allowlisted authorization request."""


def new_oauth_state() -> str:
    """Return one fresh cryptographic state value."""

    return secrets.token_urlsafe(32)


def new_pkce_verifier() -> str:
    """Return one fresh PKCE verifier in the RFC 7636 unreserved alphabet."""

    return "".join(secrets.choice(_UNRESERVED) for _ in range(64))


def pkce_s256_challenge(verifier: str, method: str = "S256") -> str:
    """Return the unpadded S256 challenge for one valid verifier."""

    if method != "S256":
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_PKCE_REJECTED")
    if type(verifier) is not str or _VERIFIER_PATTERN.fullmatch(verifier) is None:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_PKCE_REJECTED")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return _base64url(digest)


def loopback_redirect(port: int) -> str:
    """Build the one accepted loopback redirect for an OS-assigned port."""

    _require_port(port)
    return f"http://127.0.0.1:{port}/"


def validate_redirect_uri(uri: object, port: int) -> None:
    """Accept only the exact loopback redirect for this port."""

    if type(uri) is not str or uri != loopback_redirect(port):
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED")


def validate_callback(pairs: object, expected_state: str) -> str:
    """Return one authorization code after an exact state match.

    The code is for the in-process token form. It is not copied into evidence.
    """

    if type(expected_state) is not str or expected_state == "":
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_STATE_REJECTED")
    if type(pairs) is not tuple:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_CALLBACK_REJECTED")
    parsed: list[tuple[str, str]] = []
    for item in pairs:
        if (
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not str
        ):
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_CALLBACK_REJECTED")
        parsed.append((item[0], item[1]))
    keys = [key for key, _ in parsed]
    if any(key not in {"code", "state"} for key in keys):
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_CALLBACK_REJECTED")
    states = [value for key, value in parsed if key == "state"]
    codes = [value for key, value in parsed if key == "code"]
    if len(states) != 1:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_STATE_REJECTED")
    if not hmac.compare_digest(expected_state, states[0]):
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_STATE_REJECTED")
    if len(codes) != 1 or codes[0] == "":
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_CALLBACK_REJECTED")
    return codes[0]


def validate_desktop_client(client: object) -> None:
    """Reject a synthetic client that is not a loopback Desktop configuration."""

    if type(client) is not DesktopClientConfig:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED")
    if client.network_permitted is not False:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_LIVE_UNAUTHORIZED")
    if (
        client.client_type != "installed"
        or type(client.client_id) is not str
        or client.client_id == ""
    ):
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED")
    if client.redirect_host != "127.0.0.1" or client.redirect_path != "/":
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED")
    if client.redirect_port is not None:
        _require_port(client.redirect_port)
    _require_scope(client.scopes)


def build_authorization_request(
    *,
    client_id: str,
    redirect_uri: str,
    state: str,
    code_challenge: str,
) -> AuthorizationRequest:
    """Build the authorization shape. Offline access is not requested."""

    parameters = (
        ("response_type", "code"),
        ("client_id", client_id),
        ("redirect_uri", redirect_uri),
        ("scope", _METADATA_SCOPE),
        ("code_challenge", code_challenge),
        ("code_challenge_method", "S256"),
        ("state", state),
    )
    _require_pairs(parameters, _AUTH_PARAMETER_KEYS, "GMAIL_OAUTH_SCOPE_REJECTED")
    if any(key in {"access_type", "prompt", "include_granted_scopes"} for key, _ in parameters):
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_SCOPE_REJECTED")
    return AuthorizationRequest(endpoint=_AUTH_ENDPOINT, parameters=parameters)


def build_token_request(
    *,
    code: str,
    code_verifier: str,
    client_id: str,
    redirect_uri: str,
) -> TokenRequest:
    """Build the token form. Client secrets and refresh grants are omitted."""

    form = (
        ("grant_type", "authorization_code"),
        ("code", code),
        ("code_verifier", code_verifier),
        ("client_id", client_id),
        ("redirect_uri", redirect_uri),
    )
    _require_pairs(form, _TOKEN_FORM_KEYS, "GMAIL_OAUTH_TOKEN_REJECTED")
    return TokenRequest(endpoint=_TOKEN_ENDPOINT, form=form)


def validate_token_response(response: object) -> None:
    """Check one synthetic token response and retain none of its secrets."""

    status, body = _response_parts(response, "GMAIL_OAUTH_TOKEN_REJECTED")
    if status != 200:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED")
    scope = body.get("scope")
    if scope != _METADATA_SCOPE:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_SCOPE_REJECTED")
    access_token = body.get("access_token")
    if type(access_token) is not str or access_token == "":
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED")


def build_profile_request(method: str, url: str) -> ProfileRequest:
    """Accept only the metadata profile read with an empty body."""

    if method != _PROFILE_METHOD or url != _PROFILE_ENDPOINT:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_ENDPOINT_REJECTED")
    return ProfileRequest(method=_PROFILE_METHOD, url=_PROFILE_ENDPOINT, body=b"")


def validate_profile_response(response: object) -> None:
    """Check the profile shape. The values are not returned."""

    status, body = _response_parts(response, "GMAIL_OAUTH_PROFILE_REJECTED")
    if status != 200:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_PROFILE_REJECTED")
    expected = {"emailAddress", "messagesTotal", "threadsTotal", "historyId"}
    if set(body) != expected:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_PROFILE_REJECTED")
    if type(body["emailAddress"]) is not str or body["emailAddress"] == "":
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_PROFILE_REJECTED")
    if type(body["messagesTotal"]) is not int or type(body["threadsTotal"]) is not int:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_PROFILE_REJECTED")
    if type(body["historyId"]) is not str or body["historyId"] == "":
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_PROFILE_REJECTED")


def orchestrate_profile_probe(
    client: DesktopClientConfig,
    http: ProbeHttp,
    listener: ProbeListener,
    clock: ProbeClock,
    browser: ProbeBrowser,
) -> LocalOAuthProbeEvidence:
    """Run one synthetic probe through caller-supplied boundaries.

    The returned evidence does not carry callback, token, or profile content.
    """

    validate_desktop_client(client)
    verifier = new_pkce_verifier()
    state = new_oauth_state()
    challenge = pkce_s256_challenge(verifier)
    try:
        port = listener.bind()
    except LocalOAuthProbeRejected:
        raise
    except Exception:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED") from None
    if client.redirect_port is not None and client.redirect_port != port:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED")
    redirect_uri = loopback_redirect(port)
    authorization = build_authorization_request(
        client_id=client.client_id,
        redirect_uri=redirect_uri,
        state=state,
        code_challenge=challenge,
    )
    if authorization.endpoint != _AUTH_ENDPOINT:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_ENDPOINT_REJECTED")
    try:
        browser.open(authorization)
        started = clock.monotonic()
        pairs = listener.wait(_MAX_CALLBACK_WAIT)
        elapsed = clock.monotonic() - started
    except LocalOAuthProbeRejected:
        raise
    except Exception:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_CALLBACK_REJECTED") from None
    if pairs is None or type(elapsed) not in {int, float} or elapsed > _MAX_CALLBACK_WAIT:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_CALLBACK_REJECTED")
    code = validate_callback(pairs, state)
    token_request = build_token_request(
        code=code,
        code_verifier=verifier,
        client_id=client.client_id,
        redirect_uri=redirect_uri,
    )
    if token_request.endpoint != _TOKEN_ENDPOINT:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_ENDPOINT_REJECTED")
    try:
        token_response = http.post_form(token_request.endpoint, dict(token_request.form))
    except LocalOAuthProbeRejected:
        raise
    except Exception:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED") from None
    validate_token_response(token_response)
    profile_request = build_profile_request(_PROFILE_METHOD, _PROFILE_ENDPOINT)
    try:
        profile_response = http.get_profile(profile_request.url, profile_request.body)
    except LocalOAuthProbeRejected:
        raise
    except Exception:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_PROFILE_REJECTED") from None
    validate_profile_response(profile_response)
    return LocalOAuthProbeEvidence(
        callback_result=_CALLBACK_PASS,
        scope_result=_SCOPE_PASS,
        token_exchange_result=_TOKEN_PASS,
        profile_result=_PROFILE_PASS,
        content_retained=False,
    )


def run_attended_profile_probe() -> None:
    """Refuse a live attended probe. Gate C is a separate decision."""

    raise LocalOAuthProbeRejected("GMAIL_OAUTH_LIVE_UNAUTHORIZED")


def _base64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _require_port(port: object) -> None:
    if type(port) is not int or port < 1 or port > 65535:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED")


def _require_scope(scopes: object) -> None:
    if scopes != (_METADATA_SCOPE,):
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_SCOPE_REJECTED")


def _require_pairs(
    pairs: tuple[tuple[str, str], ...],
    expected_keys: tuple[str, ...],
    code: str,
) -> None:
    if tuple(key for key, _ in pairs) != expected_keys:
        raise LocalOAuthProbeRejected(code)


def _response_parts(response: object, code: str) -> tuple[int, dict[str, object]]:
    if type(response) is not dict or set(response) != {"status", "body"}:
        raise LocalOAuthProbeRejected(code)
    status = response.get("status")
    body = response.get("body")
    if type(status) is not int or type(body) is not dict:
        raise LocalOAuthProbeRejected(code)
    return status, dict(body)
