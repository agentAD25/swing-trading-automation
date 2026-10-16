"""Offline tests for the attended Windows Gmail profile command."""

from __future__ import annotations

import ast
import hashlib
import importlib
import socket
from collections.abc import Mapping
from pathlib import Path
from urllib import request as urllib_request

import pytest

import swingtrade.gmail_local_connect as connect
from swingtrade.gmail_local_connect import (
    LocalOAuthProbeEvidence,
    LocalOAuthProbeRejected,
    LoopbackListener,
    ProfileTransport,
    desktop_client_from_document,
    desktop_client_from_json_text,
    run_offline_profile_shape,
)
from swingtrade.group4_email.local_oauth_probe import (
    DesktopClientConfig,
    build_profile_request,
    pkce_s256_challenge,
    run_attended_profile_probe,
)

METADATA = "https://www.googleapis.com/auth/gmail.metadata"
AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
PROFILE = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
CLIENT_ID = "synthetic-desktop-client"
EMAIL = "shape-check@example.invalid"
ACCESS = "synthetic-access-token"
REFRESH = "synthetic-refresh-token"
SECRET = "synthetic-client-secret-value"
MODULE = Path("src/swingtrade/gmail_local_connect.py")
_BLOBS = {
    "src/swingtrade/group4_email/local_oauth_probe.py": (
        "777db628ebe0f55aa529b26c9ad5692799121090"
    ),
    "tests/group4_email/test_local_oauth_probe.py": ("86d99b6269d1c14238c5b240b7998428a206d59f"),
    "tests/group4_email/test_attacks.py": "14b911ba29f16161f179c272c2e2f5e1be50922e",
}


class Boundary:
    """Injected clock, listener, browser, and HTTP boundary."""

    def __init__(self) -> None:
        self.port = 43123
        self.closed = 0
        self.binds = 0
        self.waits: list[int] = []
        self.opens: list[object] = []
        self.posts: list[tuple[str, dict[str, str]]] = []
        self.gets: list[tuple[str, bytes]] = []
        self.mode = "ok"
        self.token_status = 200
        self.token_body: dict[str, object] = {
            "access_token": ACCESS,
            "refresh_token": REFRESH,
            "scope": METADATA,
            "token_type": "Bearer",
        }
        self.profile_body: dict[str, object] = {
            "emailAddress": EMAIL,
            "messagesTotal": 3,
            "threadsTotal": 2,
            "historyId": "history-shape",
        }

    def bind(self) -> int:
        self.binds += 1
        if self.mode == "bind-fail":
            raise RuntimeError("listener")
        return self.port

    def close(self) -> None:
        self.closed += 1

    def wait(self, timeout_seconds: int) -> tuple[tuple[str, str], ...] | None:
        self.waits.append(timeout_seconds)
        if self.mode == "timeout":
            return None
        if self.mode == "cancel":
            raise KeyboardInterrupt
        if self.mode == "listener-fail":
            raise RuntimeError("listener")
        state = dict(self.opens[-1].parameters)["state"]  # type: ignore[attr-defined]
        if self.mode == "mismatch":
            return (("state", "other-state"), ("code", "synthetic-code"))
        if self.mode == "missing-state":
            return (("code", "synthetic-code"),)
        if self.mode == "duplicate-state":
            return (("state", state), ("state", state), ("code", "synthetic-code"))
        if self.mode == "missing-code":
            return (("state", state),)
        if self.mode == "duplicate-code":
            return (("state", state), ("code", "one"), ("code", "two"))
        if self.mode == "oauth-error":
            return (("error", "access_denied"), ("state", state))
        return (("state", state), ("code", "synthetic-code"))

    def monotonic(self) -> float:
        return 0.0

    def open(self, request: object) -> None:
        self.opens.append(request)
        if self.mode == "browser":
            raise RuntimeError("browser")

    def post_form(self, endpoint: str, form: Mapping[str, str]) -> Mapping[str, object]:
        self.posts.append((endpoint, dict(form)))
        return {"status": self.token_status, "body": self.token_body}

    def get_profile(self, endpoint: str, body: bytes) -> Mapping[str, object]:
        self.gets.append((endpoint, body))
        return {"status": 200, "body": self.profile_body}


class _Sock:
    def __init__(self, host: str = "127.0.0.1", port: int = 54321) -> None:
        self.host = host
        self.port = port
        self.bound: tuple[str, int] | None = None
        self.listening = 0
        self.timeout: float | None = None
        self.closed = False
        self.accept_result: tuple[object, tuple[object, ...]] | None = None
        self.accept_error: BaseException | None = None

    def bind(self, address: tuple[str, int]) -> None:
        self.bound = address

    def listen(self, backlog: int) -> None:
        self.listening = backlog

    def getsockname(self) -> tuple[str, int]:
        return (self.host, self.port)

    def settimeout(self, value: float | None) -> None:
        self.timeout = value

    def accept(self) -> tuple[object, tuple[object, ...]]:
        if self.accept_error is not None:
            raise self.accept_error
        assert self.accept_result is not None
        return self.accept_result

    def close(self) -> None:
        self.closed = True


class _Conn:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.sent = b""
        self.closed = False

    def recv(self, bufsize: int) -> bytes:
        piece = self.payload[:bufsize]
        self.payload = self.payload[bufsize:]
        return piece

    def sendall(self, data: bytes) -> None:
        self.sent += data

    def close(self) -> None:
        self.closed = True


def _client(**installed: object) -> DesktopClientConfig:
    body: dict[str, object] = {"client_id": CLIENT_ID}
    body.update(installed)
    return desktop_client_from_document({"installed": body})


def _run(boundary: Boundary | None = None, **installed: object) -> LocalOAuthProbeEvidence:
    probe = boundary or Boundary()
    return run_offline_profile_shape(_client(**installed), probe, probe, probe, probe)


def _reject(callback: object) -> LocalOAuthProbeRejected:
    with pytest.raises(LocalOAuthProbeRejected) as caught:
        callback()  # type: ignore[operator]
    return caught.value


def _blob(path: str) -> str:
    raw = Path(path).read_bytes()
    prefix = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(prefix + raw).hexdigest()


def _executable(nodes: list[ast.stmt]) -> list[ast.stmt]:
    return [node for node in nodes if not isinstance(node, ast.Expr)]


def test_import_and_discovery_are_inert(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket")

    monkeypatch.setattr(socket, "socket", boom)
    monkeypatch.setattr(urllib_request, "urlopen", boom)
    reloaded = importlib.reload(connect)

    assert reloaded.run_local_windows_profile_proof is not None


def test_suite_does_not_call_the_live_command() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(node.func, ast.Name) else getattr(func, "attr", "")
            assert name != "run_local_windows_profile_proof"


def test_non_windows_refusal_precedes_socket_import() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_local_windows_profile_proof"
    )
    body = _executable(function.body)
    imported = {
        alias.name for node in tree.body if isinstance(node, ast.Import) for alias in node.names
    }
    imported_from = {node.module for node in tree.body if isinstance(node, ast.ImportFrom)}

    assert isinstance(body[0], ast.If)
    assert any(isinstance(node, ast.Raise) for node in ast.walk(body[0]))
    assert all(not isinstance(node, (ast.Import, ast.ImportFrom)) for node in body[0].body)
    assert any(isinstance(node, ast.Import) for node in body[1:])
    assert "socket" not in imported
    assert "webbrowser" not in imported
    assert imported_from.isdisjoint({"socket", "webbrowser", "urllib.request", "urllib.error"})


def test_explicit_attended_invocation_is_under_main() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    guards = [
        node
        for node in tree.body
        if isinstance(node, ast.If) and ast.dump(node.test).find("__main__") >= 0
    ]
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_local_windows_profile_proof"
    ]

    assert len(guards) == 1
    assert len(calls) == 1
    assert calls[0] in list(ast.walk(guards[0]))
    missing = _reject(lambda: connect._path_argument(["prog"]))
    assert missing.code == "GMAIL_OAUTH_TOKEN_REJECTED"


def test_invalid_or_missing_client_configuration() -> None:
    missing = _reject(lambda: desktop_client_from_document({}))
    web = _reject(lambda: desktop_client_from_document({"web": {"client_id": CLIENT_ID}}))
    broken = _reject(lambda: desktop_client_from_json_text("{"))
    empty = _reject(lambda: desktop_client_from_json_text(""))
    custody = _reject(
        lambda: desktop_client_from_document(
            {"installed": {"client_id": CLIENT_ID, "refresh_token": SECRET}}
        )
    )

    assert missing.code == "GMAIL_OAUTH_TOKEN_REJECTED"
    assert web.code == "GMAIL_OAUTH_TOKEN_REJECTED"
    assert broken.code == "GMAIL_OAUTH_TOKEN_REJECTED"
    assert empty.code == "GMAIL_OAUTH_TOKEN_REJECTED"
    assert custody.code == "GMAIL_OAUTH_TOKEN_REJECTED"
    assert SECRET not in f"{custody} {custody!r}"


def test_desktop_client_validation_forces_loopback_metadata() -> None:
    client = _client()
    enabled = _reject(
        lambda: desktop_client_from_document(
            {"installed": {"client_id": CLIENT_ID, "network_permitted": True}}
        )
    )

    assert client.client_type == "installed"
    assert client.network_permitted is False
    assert client.scopes == (METADATA,)
    assert client.redirect_host == "127.0.0.1"
    assert client.redirect_path == "/"
    assert enabled.code == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"
    assert SECRET not in repr(_client(client_secret=SECRET))


def test_loopback_bind_uses_an_ephemeral_port() -> None:
    sock = _Sock()
    listener = LoopbackListener(lambda: sock)
    port = listener.bind()

    assert sock.bound == ("127.0.0.1", 0)
    assert sock.listening == 1
    assert port == 54321


def test_callback_wait_is_capped_at_120_seconds() -> None:
    sock = _Sock()
    sock.accept_error = TimeoutError
    listener = LoopbackListener(lambda: sock)
    listener.bind()

    assert listener.wait(120) is None
    assert sock.timeout == 120
    assert listener.wait(180) is None
    assert sock.timeout == 120


def test_listener_closes_on_success_and_failure() -> None:
    success = Boundary()
    evidence = _run(success)
    failed = Boundary()
    failed.mode = "timeout"
    error = _reject(lambda: _run(failed))
    failed_closed = Boundary()
    failed_closed.mode = "bind-fail"
    bind_error = _reject(lambda: _run(failed_closed))

    assert evidence.content_retained is False
    assert success.closed == 1
    assert error.code == "GMAIL_OAUTH_CALLBACK_REJECTED"
    assert bind_error.code == "GMAIL_OAUTH_REDIRECT_REJECTED"
    assert failed.closed == 1
    assert failed_closed.closed == 1


def test_browser_launch_failure_closes_the_listener() -> None:
    boundary = Boundary()
    boundary.mode = "browser"
    error = _reject(lambda: _run(boundary))

    assert error.code == "GMAIL_OAUTH_CALLBACK_REJECTED"
    assert boundary.closed == 1
    assert boundary.posts == []


def test_operator_cancellation_closes_the_listener() -> None:
    boundary = Boundary()
    boundary.mode = "cancel"

    with pytest.raises(KeyboardInterrupt):
        _run(boundary)

    assert boundary.closed == 1
    assert boundary.posts == []


def test_pkce_helpers_are_reused_not_duplicated() -> None:
    boundary = Boundary()
    _run(boundary)
    verifier = boundary.posts[0][1]["code_verifier"]
    challenge = dict(boundary.opens[0].parameters)["code_challenge"]  # type: ignore[attr-defined]
    source = MODULE.read_text(encoding="utf-8")

    assert challenge == pkce_s256_challenge(verifier)
    assert "def pkce_s256_challenge" not in source
    assert "import hashlib" not in source
    assert "def new_oauth_state" not in source


def test_state_and_verifier_are_fresh() -> None:
    first = Boundary()
    second = Boundary()
    _run(first)
    _run(second)

    assert dict(first.opens[0].parameters)["state"] != dict(second.opens[0].parameters)["state"]  # type: ignore[attr-defined]
    assert first.posts[0][1]["code_verifier"] != second.posts[0][1]["code_verifier"]


@pytest.mark.parametrize(
    ("mode", "code"),
    [
        ("mismatch", "GMAIL_OAUTH_STATE_REJECTED"),
        ("missing-state", "GMAIL_OAUTH_STATE_REJECTED"),
        ("duplicate-state", "GMAIL_OAUTH_STATE_REJECTED"),
        ("missing-code", "GMAIL_OAUTH_CALLBACK_REJECTED"),
        ("duplicate-code", "GMAIL_OAUTH_CALLBACK_REJECTED"),
        ("oauth-error", "GMAIL_OAUTH_CALLBACK_REJECTED"),
    ],
)
def test_callback_failures_stop_before_token_exchange(mode: str, code: str) -> None:
    boundary = Boundary()
    boundary.mode = mode
    error = _reject(lambda: _run(boundary))

    assert error.code == code
    assert boundary.posts == []
    assert SECRET not in f"{error} {error!r}"


def test_wrong_callback_uri_is_rejected() -> None:
    localhost = _reject(lambda: _client(redirect_uris=["http://localhost/"]))
    public = _reject(lambda: _client(redirect_uris=["https://example.invalid/callback"]))
    sock = _Sock()
    listener = LoopbackListener(lambda: sock)
    listener.bind()
    connection = _Conn(b"GET /callback?code=synthetic&state=synthetic HTTP/1.1\r\n\r\n")
    sock.accept_result = (connection, ("127.0.0.1", 9))
    path_error = _reject(lambda: listener.wait(120))

    assert localhost.code == "GMAIL_OAUTH_REDIRECT_REJECTED"
    assert public.code == "GMAIL_OAUTH_REDIRECT_REJECTED"
    assert path_error.code == "GMAIL_OAUTH_REDIRECT_REJECTED"
    assert b"synthetic" not in connection.sent


def test_token_exchange_rejection_and_malformed_response() -> None:
    denied = Boundary()
    denied.token_status = 401
    denied_error = _reject(lambda: _run(denied))

    def malformed(
        _method: str,
        _endpoint: str,
        _body: bytes,
        timeout: int,
        _token: str | None,
    ) -> tuple[int, object]:
        assert timeout == 30
        return 200, ["not-an-object"]

    transport = ProfileTransport(malformed)  # type: ignore[arg-type]
    form = {
        "grant_type": "authorization_code",
        "code": "synthetic-code",
        "code_verifier": "a" * 43,
        "client_id": CLIENT_ID,
        "redirect_uri": "http://127.0.0.1:43123/",
    }
    malformed_error = _reject(lambda: transport.post_form(TOKEN, form))

    assert denied_error.code == "GMAIL_OAUTH_TOKEN_REJECTED"
    assert denied.gets == []
    assert malformed_error.code == "GMAIL_OAUTH_TOKEN_REJECTED"


def test_missing_and_extra_scope_are_rejected() -> None:
    missing = Boundary()
    missing.token_body = {"access_token": ACCESS, "token_type": "Bearer"}
    extra = Boundary()
    extra.token_body = {
        "access_token": ACCESS,
        "scope": METADATA + " https://www.googleapis.com/auth/gmail.readonly",
    }
    missing_error = _reject(lambda: _run(missing))
    extra_error = _reject(lambda: _run(extra))
    config_error = _reject(
        lambda: _client(scopes=["https://www.googleapis.com/auth/gmail.readonly"])
    )

    assert missing_error.code == "GMAIL_OAUTH_SCOPE_REJECTED"
    assert extra_error.code == "GMAIL_OAUTH_SCOPE_REJECTED"
    assert config_error.code == "GMAIL_OAUTH_SCOPE_REJECTED"
    assert missing.gets == []
    assert extra.gets == []


def test_refresh_token_is_not_retained() -> None:
    calls: list[tuple[str, str, int]] = []

    def exchange(
        method: str,
        endpoint: str,
        body: bytes,
        timeout: int,
        token: str | None,
    ) -> tuple[int, dict[str, object]]:
        calls.append((method, endpoint, timeout))
        if method == "POST":
            assert token is None
            assert b"client_secret" not in body
            assert b"refresh_token" not in body
            return 200, {
                "access_token": ACCESS,
                "refresh_token": REFRESH,
                "scope": METADATA,
            }
        assert token == ACCESS
        return 200, {
            "emailAddress": EMAIL,
            "messagesTotal": 3,
            "threadsTotal": 2,
            "historyId": "history-shape",
        }

    boundary = Boundary()
    transport = ProfileTransport(exchange)
    evidence = run_offline_profile_shape(_client(), transport, boundary, boundary, boundary)

    assert evidence.profile_result == "GMAIL_OAUTH_PROFILE_SHAPE_PASS"
    assert transport._access == []
    assert REFRESH not in repr(transport)
    assert REFRESH not in repr(evidence)
    assert ACCESS not in repr(evidence)
    assert calls == [("POST", TOKEN, 30), ("GET", PROFILE, 30)]


def test_no_credential_or_token_persistence() -> None:
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    opens = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open"
    ]

    assert "token.json" not in source
    assert "os.environ" not in source
    assert "getenv" not in source
    assert "CredWrite" not in source
    assert opens
    assert all(keyword.arg == "encoding" for node in opens for keyword in node.keywords)


def test_public_errors_omit_provider_material(capsys: pytest.CaptureFixture[str]) -> None:
    boundary = Boundary()
    evidence = _run(boundary)
    state = dict(boundary.opens[0].parameters)["state"]  # type: ignore[attr-defined]
    verifier = boundary.posts[0][1]["code_verifier"]
    rendered = f"{evidence} {evidence!r} {boundary.opens[0]}"

    assert state not in rendered
    assert verifier not in rendered
    assert EMAIL not in rendered
    assert ACCESS not in rendered
    assert REFRESH not in rendered
    assert "GMAIL_GATE_C_REAL_CONNECTIVITY_PASS" not in capsys.readouterr().out
    assert evidence.profile_result == "GMAIL_OAUTH_PROFILE_SHAPE_PASS"


def test_profile_get_is_exact_and_empty() -> None:
    boundary = Boundary()
    _run(boundary)
    request = build_profile_request("GET", PROFILE)

    assert boundary.gets == [(PROFILE, b"")]
    assert request.method == "GET"
    assert request.url == PROFILE
    assert request.body == b""
    assert boundary.waits == [120]


def test_second_profile_call_and_other_endpoints_send_nothing() -> None:
    calls: list[str] = []

    def exchange(
        method: str,
        endpoint: str,
        _body: bytes,
        _timeout: int,
        _token: str | None,
    ) -> tuple[int, dict[str, object]]:
        calls.append(endpoint)
        if method == "POST":
            return 200, {"access_token": ACCESS, "scope": METADATA}
        return 200, {
            "emailAddress": EMAIL,
            "messagesTotal": 1,
            "threadsTotal": 1,
            "historyId": "history-shape",
        }

    transport = ProfileTransport(exchange)
    transport.post_form(
        TOKEN,
        {
            "grant_type": "authorization_code",
            "code": "synthetic-code",
            "code_verifier": "a" * 43,
            "client_id": CLIENT_ID,
            "redirect_uri": "http://127.0.0.1:1/",
        },
    )
    transport.get_profile(PROFILE, b"")
    second = _reject(lambda: transport.get_profile(PROFILE, b""))
    messages = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
    other = _reject(lambda: transport.get_profile(messages, b""))
    posted = _reject(lambda: transport.post_form(messages, {"grant_type": "authorization_code"}))

    assert second.code == "GMAIL_OAUTH_ENDPOINT_REJECTED"
    assert other.code == "GMAIL_OAUTH_ENDPOINT_REJECTED"
    assert posted.code == "GMAIL_OAUTH_ENDPOINT_REJECTED"
    assert calls == [TOKEN, PROFILE]


def test_profile_shape_is_checked_and_discarded() -> None:
    evidence = _run()
    invalid = Boundary()
    invalid.profile_body = {
        "emailAddress": EMAIL,
        "messagesTotal": True,
        "threadsTotal": 2,
        "historyId": "history-shape",
    }
    error = _reject(lambda: _run(invalid))

    assert evidence.profile_result == "GMAIL_OAUTH_PROFILE_SHAPE_PASS"
    assert evidence.content_retained is False
    assert set(LocalOAuthProbeEvidence.__dataclass_fields__) == {
        "callback_result",
        "scope_result",
        "token_exchange_result",
        "profile_result",
        "content_retained",
    }
    assert error.code == "GMAIL_OAUTH_PROFILE_REJECTED"
    assert EMAIL not in f"{error} {evidence!r}"


def test_synthetic_flow_does_not_contact_a_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("provider")

    monkeypatch.setattr(socket, "socket", boom)
    monkeypatch.setattr(urllib_request, "urlopen", boom)
    monkeypatch.setattr("builtins.open", boom)
    evidence = _run()

    assert evidence.profile_result == "GMAIL_OAUTH_PROFILE_SHAPE_PASS"
    assert evidence.profile_result != "GMAIL_GATE_C_REAL_CONNECTIVITY_PASS"


def test_module_has_no_database_broker_or_economic_imports() -> None:
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    allowed = {
        "json",
        "sys",
        "collections.abc",
        "typing",
        "swingtrade.group4_email.local_oauth_probe",
        "__future__",
    }
    imported = {
        alias.name for node in tree.body if isinstance(node, ast.Import) for alias in node.names
    }
    imported_from = {node.module for node in tree.body if isinstance(node, ast.ImportFrom)}

    assert "OrderIntent" not in source
    assert "tradestation" not in source.lower()
    assert "psycopg" not in source
    assert "postgres" not in source.lower()
    assert imported <= allowed
    assert imported_from <= allowed


def test_certified_gate_b_and_item_22_blobs_stay_unchanged() -> None:
    error = _reject(run_attended_profile_probe)

    assert error.code == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"
    assert str(error) == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"
    for path, blob in _BLOBS.items():
        assert _blob(path) == blob


def test_real_pass_token_is_only_loaded_by_the_windows_command() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    stack: list[str] = []
    loads: list[tuple[str, ...]] = []

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            stack.append(node.name)
            self.generic_visit(node)
            stack.pop()

        def visit_Name(self, node: ast.Name) -> None:
            if node.id == "_REAL_PASS" and isinstance(node.ctx, ast.Load):
                loads.append(tuple(stack))

    Visitor().visit(tree)

    assert set(loads) == {("run_local_windows_profile_proof",)}
    assert loads
