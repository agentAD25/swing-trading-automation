"""Offline tests for the local OAuth profile-probe shapes."""

from __future__ import annotations

import ast
import hashlib
import hmac
import inspect
import os
import socket
import webbrowser
from collections.abc import Mapping
from pathlib import Path

import pytest

from swingtrade.group4_email.local_oauth_probe import (
    AuthorizationRequest,
    DesktopClientConfig,
    LocalOAuthProbeEvidence,
    LocalOAuthProbeRejected,
    ProfileRequest,
    TokenRequest,
    build_authorization_request,
    build_profile_request,
    build_token_request,
    loopback_redirect,
    new_oauth_state,
    new_pkce_verifier,
    orchestrate_profile_probe,
    pkce_s256_challenge,
    run_attended_profile_probe,
    validate_callback,
    validate_desktop_client,
    validate_profile_response,
    validate_redirect_uri,
    validate_token_response,
)

MODULE = Path("src/swingtrade/group4_email/local_oauth_probe.py")
METADATA = "https://www.googleapis.com/auth/gmail.metadata"
AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
PROFILE_ENDPOINT = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
RFC_VERIFIER = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
RFC_CHALLENGE = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
EMAIL = "shape-check@example.invalid"
ACCESS_TOKEN = "synthetic-access-token"
REFRESH_TOKEN = "synthetic-refresh-token"
PROFILE_BODY_SECRET = "raw-profile-body-secret"
CLIENT_ID = "synthetic-desktop-client"
_PROTECTED = {
    "src/swingtrade/gmail_credential/__init__.py": ("0e8eed5244e6966740f5b0d9af877f8193a6f2b1"),
    "src/swingtrade/gmail_credential/adapter.py": ("984b7781d88f28b4fd2888ba3f8a9e12475448c0"),
    "src/swingtrade/gmail_credential/errors.py": ("32a446eb059635bcd2f44db34f6ac1385ef4df85"),
    "src/swingtrade/gmail_credential/identity.py": ("30c7dd8056e195dc98d02dfc1057662c170f0811"),
    "src/swingtrade/gmail_credential/mock_port.py": ("9a76189be5cdc7cb9e4652e276f58ec86abfcd74"),
    "src/swingtrade/gmail_credential/secret.py": ("0acc491ee29e1133f73e451636da9d9747726230"),
    "src/swingtrade/group4_email/__init__.py": ("44d73a8b92f05fbf941eb6c6b1383e52a2913104"),
    "src/swingtrade/group4_email/synthetic_acquisition.py": (
        "6fd37978a839b5b4d5e4ce046d4feeba067764b6"
    ),
    "src/swingtrade/group4_email/parse.py": ("4119ffe03758380e0a284cc3514721201fac34c9"),
    "src/swingtrade/group4_email/synthetic_ingestion.py": (
        "73165d7ccaecc94dd930943f820436af3940168b"
    ),
}


class Boundary:
    """Synthetic clock, listener, browser, and HTTP boundary."""

    def __init__(self) -> None:
        self.port = 43123
        self.binds = 0
        self.waits: list[int] = []
        self.opens: list[AuthorizationRequest] = []
        self.posts: list[tuple[str, dict[str, str]]] = []
        self.gets: list[tuple[str, bytes]] = []
        self.query_mode = "match"
        self.elapsed = 0.0
        self._now = 0.0
        self.token: dict[str, object] = {
            "status": 200,
            "body": {
                "access_token": ACCESS_TOKEN,
                "refresh_token": REFRESH_TOKEN,
                "scope": METADATA,
                "token_type": "Bearer",
            },
        }
        self.profile: dict[str, object] = {
            "status": 200,
            "body": {
                "emailAddress": EMAIL,
                "messagesTotal": 3,
                "threadsTotal": 2,
                "historyId": "history-shape",
            },
        }

    def bind(self) -> int:
        self.binds += 1
        return self.port

    def wait(self, timeout_seconds: int) -> tuple[tuple[str, str], ...] | None:
        self.waits.append(timeout_seconds)
        if self.query_mode == "timeout":
            return None
        state = dict(self.opens[-1].parameters)["state"]
        if self.query_mode == "mismatch":
            return (("state", "not-the-attempt-state"), ("code", "synthetic-code"))
        if self.query_mode == "missing_state":
            return (("code", "synthetic-code"),)
        if self.query_mode == "duplicate_state":
            return (("state", state), ("state", state), ("code", "synthetic-code"))
        if self.query_mode == "missing_code":
            return (("state", state),)
        if self.query_mode == "duplicate_code":
            return (("state", state), ("code", "one-code"), ("code", "other-code"))
        if self.query_mode == "oauth_error":
            return (("error", "access_denied"), ("state", state))
        return (("state", state), ("code", "synthetic-code"))

    def monotonic(self) -> float:
        self._now += self.elapsed
        return self._now

    def open(self, request: AuthorizationRequest) -> None:
        self.opens.append(request)

    def post_form(self, endpoint: str, form: Mapping[str, str]) -> Mapping[str, object]:
        self.posts.append((endpoint, dict(form)))
        return self.token

    def get_profile(self, endpoint: str, body: bytes) -> Mapping[str, object]:
        self.gets.append((endpoint, body))
        return self.profile


def _client(**overrides: object) -> DesktopClientConfig:
    values: dict[str, object] = {
        "client_type": "installed",
        "redirect_host": "127.0.0.1",
        "redirect_path": "/",
        "scopes": (METADATA,),
        "network_permitted": False,
        "redirect_port": None,
        "client_id": CLIENT_ID,
    }
    values.update(overrides)
    return DesktopClientConfig(**values)  # type: ignore[arg-type]


def _probe(boundary: Boundary, **overrides: object) -> LocalOAuthProbeEvidence:
    return orchestrate_profile_probe(
        _client(**overrides),
        boundary,
        boundary,
        boundary,
        boundary,
    )


def _reject(callback: object) -> LocalOAuthProbeRejected:
    with pytest.raises(LocalOAuthProbeRejected) as caught:
        callback()  # type: ignore[operator]
    return caught.value


def _blob(path: str) -> str:
    raw = Path(path).read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def test_live_entry_refuses_immediately() -> None:
    signature = inspect.signature(run_attended_profile_probe)
    error = _reject(run_attended_profile_probe)

    assert signature.parameters == {}
    assert error.code == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"
    assert str(error) == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"
    assert repr(error) == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"


def test_refusal_happens_before_any_provider_effect(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("provider effect")

    monkeypatch.setattr(socket, "socket", boom)
    monkeypatch.setattr(webbrowser, "open", boom)
    error = _reject(run_attended_profile_probe)

    assert error.code == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"


def test_environment_and_config_cannot_enable_live_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GMAIL_OAUTH_ENABLE_LIVE", "1")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "synthetic-client.json")
    error = _reject(run_attended_profile_probe)
    boundary = Boundary()

    assert error.code == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"
    assert os.environ["GMAIL_OAUTH_ENABLE_LIVE"] == "1"
    network = _reject(lambda: _probe(boundary, network_permitted=True))
    assert network.code == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"
    assert boundary.binds == 0
    assert boundary.posts == []


def test_no_alternate_live_entrypoint() -> None:
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    attended = next(node for node in functions if node.name == "run_attended_profile_probe")
    parameters = [
        parameter.arg for node in functions for parameter in node.args.args + node.args.kwonlyargs
    ]

    executable = [node for node in attended.body if not isinstance(node, ast.Expr)]
    imported = {
        alias.name for node in tree.body if isinstance(node, ast.Import) for alias in node.names
    }

    assert executable and isinstance(executable[0], ast.Raise)
    assert "enable_live" not in parameters
    assert {"httpx", "webbrowser", "urllib", "socket"}.isdisjoint(imported)
    assert "urlopen" not in source


def test_rfc7636_appendix_b_vector() -> None:
    challenge = pkce_s256_challenge(RFC_VERIFIER)

    assert challenge == RFC_CHALLENGE
    assert "=" not in challenge
    plain = _reject(lambda: pkce_s256_challenge(RFC_VERIFIER, method="plain"))
    assert plain.code == "GMAIL_OAUTH_PKCE_REJECTED"
    assert RFC_VERIFIER not in f"{plain} {plain!r}"


def test_state_is_fresh_per_attempt() -> None:
    first = new_oauth_state()
    second = new_oauth_state()

    assert first != second
    assert len(first) >= 43
    assert len(second) >= 43


def test_verifier_is_fresh_per_attempt() -> None:
    first = new_pkce_verifier()
    second = new_pkce_verifier()

    assert first != second
    assert pkce_s256_challenge(first) != pkce_s256_challenge(second)


def test_verifier_grammar_and_length() -> None:
    legal = "A" * 43 + "-._~"
    assert pkce_s256_challenge(legal)

    for verifier in ("A" * 42, "A" * 129, "bad verifier", "plus+sign-and-more-padding-padding-pad"):
        error = _reject(lambda verifier=verifier: pkce_s256_challenge(verifier))
        assert error.code == "GMAIL_OAUTH_PKCE_REJECTED"
        assert verifier not in str(error)


def test_s256_challenge_uses_the_verifier_digest() -> None:
    digest = hashlib.sha256(RFC_VERIFIER.encode("ascii")).digest()
    expected = pkce_s256_challenge(RFC_VERIFIER)

    assert expected == RFC_CHALLENGE
    assert len(digest) == 32


def test_challenge_has_no_base64url_padding() -> None:
    challenge = pkce_s256_challenge(new_pkce_verifier())

    assert "=" not in challenge
    assert "+" not in challenge
    assert "/" not in challenge


def test_exact_loopback_callback() -> None:
    uri = loopback_redirect(43123)

    assert uri == "http://127.0.0.1:43123/"
    validate_redirect_uri(uri, 43123)


@pytest.mark.parametrize(
    "uri",
    [
        "http://localhost:43123/",
        "http://[::1]:43123/",
        "http://0.0.0.0:43123/",
        "https://127.0.0.1:43123/",
        "http://203.0.113.10:43123/",
        "urn:ietf:wg:oauth:2.0:oob",
    ],
)
def test_non_loopback_redirect_is_rejected(uri: str) -> None:
    error = _reject(lambda: validate_redirect_uri(uri, 43123))

    assert error.code == "GMAIL_OAUTH_REDIRECT_REJECTED"
    assert uri not in str(error)


def test_port_and_path_mismatch_are_rejected() -> None:
    path_error = _reject(lambda: validate_redirect_uri("http://127.0.0.1:43123/callback", 43123))
    port_error = _reject(lambda: validate_redirect_uri("http://127.0.0.1:43124/", 43123))
    invalid_port = _reject(lambda: loopback_redirect(0))
    boolean_port = _reject(lambda: loopback_redirect(True))  # type: ignore[arg-type]

    assert path_error.code == "GMAIL_OAUTH_REDIRECT_REJECTED"
    assert port_error.code == "GMAIL_OAUTH_REDIRECT_REJECTED"
    assert invalid_port.code == "GMAIL_OAUTH_REDIRECT_REJECTED"
    assert boolean_port.code == "GMAIL_OAUTH_REDIRECT_REJECTED"


def test_missing_state_is_rejected() -> None:
    error = _reject(lambda: validate_callback((("code", "synthetic-code"),), "expected-state"))

    assert error.code == "GMAIL_OAUTH_STATE_REJECTED"
    assert "synthetic-code" not in str(error)


def test_duplicate_state_is_rejected() -> None:
    pairs = (("state", "expected-state"), ("state", "expected-state"), ("code", "synthetic-code"))
    error = _reject(lambda: validate_callback(pairs, "expected-state"))

    assert error.code == "GMAIL_OAUTH_STATE_REJECTED"
    assert "expected-state" not in str(error)


def test_state_mismatch_stops_before_token_exchange() -> None:
    boundary = Boundary()
    boundary.query_mode = "mismatch"
    error = _reject(lambda: _probe(boundary))

    assert error.code == "GMAIL_OAUTH_STATE_REJECTED"
    assert boundary.posts == []
    assert boundary.gets == []
    assert "not-the-attempt-state" not in str(error)


def test_missing_authorization_code_is_rejected() -> None:
    error = _reject(lambda: validate_callback((("state", "expected-state"),), "expected-state"))

    assert error.code == "GMAIL_OAUTH_CALLBACK_REJECTED"


def test_duplicate_authorization_code_is_rejected() -> None:
    pairs = (("state", "expected-state"), ("code", "one-code"), ("code", "other-code"))
    error = _reject(lambda: validate_callback(pairs, "expected-state"))

    assert error.code == "GMAIL_OAUTH_CALLBACK_REJECTED"
    assert "one-code" not in str(error)
    assert "other-code" not in str(error)


def test_oauth_error_callback_is_rejected() -> None:
    pairs = (("error", "access_denied"), ("state", "expected-state"))
    error = _reject(lambda: validate_callback(pairs, "expected-state"))

    assert error.code == "GMAIL_OAUTH_CALLBACK_REJECTED"
    assert "access_denied" not in f"{error} {error!r}"


def test_callback_timeout_stops_before_token_exchange() -> None:
    quiet = Boundary()
    quiet.query_mode = "timeout"
    quiet_error = _reject(lambda: _probe(quiet))
    late = Boundary()
    late.elapsed = 121.0
    late_error = _reject(lambda: _probe(late))

    assert quiet_error.code == "GMAIL_OAUTH_CALLBACK_REJECTED"
    assert late_error.code == "GMAIL_OAUTH_CALLBACK_REJECTED"
    assert quiet.waits == [120]
    assert late.waits == [120]
    assert quiet.posts == []
    assert late.posts == []


def test_authorization_scope_is_exact() -> None:
    boundary = Boundary()
    _probe(boundary)
    parameters = dict(boundary.opens[0].parameters)

    assert parameters["scope"] == METADATA
    assert boundary.opens[0].endpoint == AUTH_ENDPOINT


def test_missing_scope_is_rejected() -> None:
    boundary = Boundary()
    error = _reject(lambda: _probe(boundary, scopes=()))

    assert error.code == "GMAIL_OAUTH_SCOPE_REJECTED"
    assert boundary.binds == 0
    granted = _reject(
        lambda: validate_token_response({"status": 200, "body": {"access_token": ACCESS_TOKEN}})
    )
    assert granted.code == "GMAIL_OAUTH_SCOPE_REJECTED"
    assert ACCESS_TOKEN not in str(granted)


def test_extra_scope_is_rejected() -> None:
    boundary = Boundary()
    requested = _reject(
        lambda: _probe(
            boundary, scopes=(METADATA, "https://www.googleapis.com/auth/gmail.readonly")
        )
    )
    granted = _reject(
        lambda: validate_token_response(
            {
                "status": 200,
                "body": {
                    "access_token": ACCESS_TOKEN,
                    "scope": f"{METADATA} https://www.googleapis.com/auth/gmail.readonly",
                },
            }
        )
    )

    assert requested.code == "GMAIL_OAUTH_SCOPE_REJECTED"
    assert granted.code == "GMAIL_OAUTH_SCOPE_REJECTED"
    assert boundary.posts == []
    assert "gmail.readonly" not in str(granted)


def test_authorization_omits_access_type_and_offline_prompt() -> None:
    boundary = Boundary()
    _probe(boundary)
    keys = [key for key, _ in boundary.opens[0].parameters]

    assert "access_type" not in keys
    assert "prompt" not in keys
    assert "offline" not in keys


def test_token_form_omits_client_secret_and_refresh_token() -> None:
    boundary = Boundary()
    _probe(boundary)
    form = boundary.posts[0][1]

    assert boundary.posts[0][0] == TOKEN_ENDPOINT
    assert set(form) == {"grant_type", "code", "code_verifier", "client_id", "redirect_uri"}
    assert form["grant_type"] == "authorization_code"
    assert "client_secret" not in form
    assert "refresh_token" not in form
    assert "access_type" not in form


def test_refresh_token_is_not_retained() -> None:
    boundary = Boundary()
    evidence = _probe(boundary)
    rendered = f"{evidence} {evidence!r}"

    assert REFRESH_TOKEN not in rendered
    assert ACCESS_TOKEN not in rendered
    assert REFRESH_TOKEN not in MODULE.read_text(encoding="utf-8")


def test_profile_get_is_allowlisted() -> None:
    boundary = Boundary()
    _probe(boundary)

    assert boundary.gets == [(PROFILE_ENDPOINT, b"")]


def test_profile_request_body_is_empty() -> None:
    request = build_profile_request("GET", PROFILE_ENDPOINT)

    assert type(request) is ProfileRequest
    assert request.method == "GET"
    assert request.url == PROFILE_ENDPOINT
    assert request.body == b""


def test_other_profile_methods_and_endpoints_are_rejected() -> None:
    method_error = _reject(
        lambda: build_profile_request(
            "POST",
            PROFILE_ENDPOINT,
        )
    )
    messages = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
    endpoint_error = _reject(lambda: build_profile_request("GET", messages))

    assert method_error.code == "GMAIL_OAUTH_ENDPOINT_REJECTED"
    assert endpoint_error.code == "GMAIL_OAUTH_ENDPOINT_REJECTED"
    assert messages not in str(endpoint_error)


def test_valid_profile_shape_is_discarded() -> None:
    boundary = Boundary()
    evidence = _probe(boundary)

    assert evidence.profile_result == "GMAIL_OAUTH_PROFILE_SHAPE_PASS"
    assert evidence.content_retained is False
    assert EMAIL not in repr(evidence)
    validate_profile_response(boundary.profile)


def test_invalid_profile_shape_is_rejected() -> None:
    boolean_total = {
        "status": 200,
        "body": {
            "emailAddress": EMAIL,
            "messagesTotal": True,
            "threadsTotal": 2,
            "historyId": "history-shape",
        },
    }
    shape_error = _reject(lambda: validate_profile_response(boolean_total))
    failed = {
        "status": 403,
        "body": {"error": PROFILE_BODY_SECRET},
    }
    status_error = _reject(lambda: validate_profile_response(failed))

    assert shape_error.code == "GMAIL_OAUTH_PROFILE_REJECTED"
    assert status_error.code == "GMAIL_OAUTH_PROFILE_REJECTED"
    assert EMAIL not in str(shape_error)
    assert PROFILE_BODY_SECRET not in f"{status_error} {status_error!r}"


def test_evidence_contract_is_five_frozen_fields() -> None:
    evidence = _probe(Boundary())
    names = tuple(item.name for item in evidence.__dataclass_fields__.values())

    assert names == (
        "callback_result",
        "scope_result",
        "token_exchange_result",
        "profile_result",
        "content_retained",
    )
    assert evidence.content_retained is False
    assert evidence.profile_result == "GMAIL_OAUTH_PROFILE_SHAPE_PASS"
    assert "GMAIL_CONNECTIVITY_PASS" not in repr(evidence)
    with pytest.raises(AttributeError):
        evidence.content_retained = True  # type: ignore[misc]


def test_public_text_omits_provider_values() -> None:
    boundary = Boundary()
    evidence = _probe(boundary)
    state = dict(boundary.opens[0].parameters)["state"]
    verifier = boundary.posts[0][1]["code_verifier"]
    rendered = f"{evidence} {evidence!r} {boundary.opens[0]} {TokenRequest(TOKEN_ENDPOINT, ())}"

    assert state not in rendered
    assert verifier not in rendered
    assert EMAIL not in rendered
    assert ACCESS_TOKEN not in rendered
    assert REFRESH_TOKEN not in rendered
    assert CLIENT_ID not in repr(_client())
    assert hmac.compare_digest(verifier, verifier)


def test_module_does_not_read_credential_files_or_environment() -> None:
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = [
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    imported = {
        alias.name for node in tree.body if isinstance(node, ast.Import) for alias in node.names
    }

    assert "os.environ" not in source
    assert "getenv" not in source
    assert "pathlib" not in imported
    assert "os" not in imported
    assert "open" not in calls
    validate_desktop_client(_client())
    wrong_type = _reject(lambda: validate_desktop_client(_client(client_type="web")))
    assert wrong_type.code == "GMAIL_OAUTH_TOKEN_REJECTED"


def test_module_has_no_network_browser_or_credential_calls() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    banned = {
        "socket",
        "webbrowser",
        "httpx",
        "http",
        "urllib",
        "ctypes",
        "winreg",
        "requests",
    }
    imported = {
        alias.name.split(".", 1)[0]
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_from = {
        (node.module or "").split(".", 1)[0]
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
    }
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert banned.isdisjoint(imported)
    assert banned.isdisjoint(imported_from)
    assert {"urlopen", "CredRead", "CredWrite"}.isdisjoint(calls)


def test_module_has_no_economic_or_broker_imports() -> None:
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    allowed = {
        "base64",
        "collections.abc",
        "dataclasses",
        "hashlib",
        "hmac",
        "re",
        "secrets",
        "typing",
        "__future__",
    }
    imported = {
        alias.name for node in tree.body if isinstance(node, ast.Import) for alias in node.names
    }
    imported_from = {node.module for node in tree.body if isinstance(node, ast.ImportFrom)}

    assert "OrderIntent" not in source
    assert "record_synthetic_ingestion" not in source
    assert "parse_email" not in source
    assert "deliver_synthetic_fixtures" not in source
    assert "admit_instruction_receipt" not in source
    assert "evaluate_receipt_commit" not in source
    assert "evaluate_report_sequence" not in source
    assert imported <= allowed
    assert imported_from <= allowed
    assert not any(isinstance(node, ast.ImportFrom) and node.level for node in tree.body)


def test_protected_modules_stay_unchanged() -> None:
    package = Path("src/swingtrade/group4_email/__init__.py").read_text(encoding="utf-8")

    assert "local_oauth_probe" not in package
    for path, blob in _PROTECTED.items():
        assert _blob(path) == blob


def test_shape_pass_is_not_real_connectivity() -> None:
    evidence = _probe(Boundary())

    assert evidence.callback_result == "CALLBACK_SHAPE_PASS"
    assert evidence.scope_result == "SCOPE_EXACT"
    assert evidence.token_exchange_result == "TOKEN_SHAPE_PASS"
    assert evidence.profile_result == "GMAIL_OAUTH_PROFILE_SHAPE_PASS"
    assert evidence.profile_result != "GMAIL_CONNECTIVITY_PASS"
    assert evidence.content_retained is False


def test_authorization_and_token_builders_hide_secrets() -> None:
    authorization = build_authorization_request(
        client_id=CLIENT_ID,
        redirect_uri="http://127.0.0.1:43123/",
        state="attempt-state",
        code_challenge=RFC_CHALLENGE,
    )
    token = build_token_request(
        code="synthetic-code",
        code_verifier=RFC_VERIFIER,
        client_id=CLIENT_ID,
        redirect_uri="http://127.0.0.1:43123/",
    )

    assert isinstance(authorization, AuthorizationRequest)
    assert "attempt-state" not in repr(authorization)
    assert RFC_VERIFIER not in repr(token)
    assert "synthetic-code" not in repr(token)
    assert "client_secret" not in dict(token.form)
    assert "access_type" not in dict(authorization.parameters)
