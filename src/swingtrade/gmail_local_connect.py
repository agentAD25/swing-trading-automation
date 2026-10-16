"""Attended Windows-local Gmail profile command.

Offline tests exercise injected boundaries and never call
``run_local_windows_profile_proof``. ``GMAIL_OAUTH_PROFILE_SHAPE_PASS`` is an
in-process shape result. The real-connectivity token is printed only by the
Windows command after that shape result.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping
from typing import Protocol

from swingtrade.group4_email.local_oauth_probe import (
    AuthorizationRequest,
    DesktopClientConfig,
    LocalOAuthProbeEvidence,
    LocalOAuthProbeRejected,
    ProbeBrowser,
    ProbeClock,
    ProbeHttp,
    orchestrate_profile_probe,
    validate_desktop_client,
)

_METADATA_SCOPE = "https://www.googleapis.com/auth/gmail.metadata"
_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
_PROFILE_ENDPOINT = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
_MAX_CALLBACK_WAIT = 120
_HTTP_TIMEOUT = 30
_MAX_CLIENT_BYTES = 8192
_SHAPE_PASS = "GMAIL_OAUTH_PROFILE_SHAPE_PASS"
_REAL_PASS = "GMAIL_GATE_C_REAL_CONNECTIVITY_PASS"
_REAL_BLOCKED = "GMAIL_GATE_C_REAL_CONNECTIVITY_BLOCKED"
_CUSTODY_KEYS = frozenset({"access_token", "refresh_token", "id_token", "private_key", "token"})
_OFFLINE_KEYS = frozenset({"access_type", "prompt"})


class ClosingListener(Protocol):
    """Loopback boundary that can be closed after the probe."""

    def bind(self) -> int:
        """Bind one loopback listener and return its port."""

    def wait(self, timeout_seconds: int) -> tuple[tuple[str, str], ...] | None:
        """Return one callback or None when the wait expires."""

    def close(self) -> None:
        """Release the listener."""


class _ClockSource(Protocol):
    def __call__(self) -> float:
        """Return a monotonic timestamp."""


class _BrowserModule(Protocol):
    def open(self, url: str) -> bool:
        """Open one local system browser."""


class _Exchange(Protocol):
    def __call__(
        self,
        method: str,
        endpoint: str,
        body: bytes,
        timeout_seconds: int,
        access_token: str | None,
    ) -> tuple[int, dict[str, object]]:
        """Perform one bounded HTTP exchange."""


class _Connection(Protocol):
    def recv(self, bufsize: int) -> bytes:
        """Read one chunk."""

    def sendall(self, data: bytes) -> None:
        """Write one response."""

    def close(self) -> None:
        """Close the accepted connection."""


class _BoundSocket(Protocol):
    def bind(self, address: tuple[str, int]) -> None:
        """Bind the socket."""

    def listen(self, backlog: int) -> None:
        """Accept one queued connection."""

    def getsockname(self) -> tuple[str, int]:
        """Return the bound address."""

    def settimeout(self, value: float | None) -> None:
        """Set the accept timeout."""

    def accept(self) -> tuple[_Connection, tuple[object, ...]]:
        """Accept one connection."""

    def close(self) -> None:
        """Close the listener."""


def desktop_client_from_document(document: object) -> DesktopClientConfig:
    """Build a Desktop config. Secret custody fields are rejected."""

    if type(document) is not dict or set(document) != {"installed"}:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED")
    installed = document["installed"]
    if type(installed) is not dict:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED")
    if "network_permitted" in installed:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_LIVE_UNAUTHORIZED")
    if _CUSTODY_KEYS.intersection(installed):
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED")
    if _OFFLINE_KEYS.intersection(installed):
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_SCOPE_REJECTED")
    if "client_secret" in installed and type(installed.get("client_secret")) is not str:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED")
    if "scopes" in installed and not _scope_declaration(installed.get("scopes")):
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_SCOPE_REJECTED")
    _reject_redirects(installed.get("redirect_uris"))
    _reject_declared_endpoint(installed, "auth_uri", _AUTH_ENDPOINT)
    _reject_declared_endpoint(installed, "token_uri", _TOKEN_ENDPOINT)
    client_id = installed.get("client_id")
    client = DesktopClientConfig(
        client_type="installed",
        redirect_host="127.0.0.1",
        redirect_path="/",
        scopes=(_METADATA_SCOPE,),
        network_permitted=False,
        client_id=client_id if type(client_id) is str else "",
    )
    validate_desktop_client(client)
    return client


def desktop_client_from_json_text(text: str) -> DesktopClientConfig:
    """Parse one in-memory Desktop client document."""

    if type(text) is not str or text.strip() == "" or len(text) > _MAX_CLIENT_BYTES:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED")
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED") from None
    return desktop_client_from_document(document)


def run_offline_profile_shape(
    client: DesktopClientConfig,
    http: ProbeHttp,
    listener: ClosingListener,
    clock: ProbeClock,
    browser: ProbeBrowser,
) -> LocalOAuthProbeEvidence:
    """Run the certified orchestrator and always close the listener.

    This wrapper does not print a real-connectivity result.
    """

    try:
        return orchestrate_profile_probe(client, http, listener, clock, browser)
    finally:
        listener.close()


class MonotonicClock:
    """Clock boundary. The Windows command supplies ``time.monotonic``."""

    def __init__(self, now: _ClockSource) -> None:
        self._now = now

    def monotonic(self) -> float:
        value = self._now()
        if type(value) not in {int, float}:
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_CALLBACK_REJECTED")
        return float(value)


class CommandBrowser:
    """System-browser boundary. The launcher is injected."""

    def __init__(self, browser: _BrowserModule) -> None:
        self._browser = browser

    def __repr__(self) -> str:
        return "CommandBrowser"

    def open(self, request: AuthorizationRequest) -> None:
        if request.endpoint != _AUTH_ENDPOINT:
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_ENDPOINT_REJECTED")
        keys = {key for key, _ in request.parameters}
        if _OFFLINE_KEYS.intersection(keys) or "client_secret" in keys:
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_SCOPE_REJECTED")
        from urllib.parse import urlencode

        target = request.endpoint + "?" + urlencode(request.parameters)
        if self._browser.open(target) is False:
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_CALLBACK_REJECTED")


class ProfileTransport:
    """One token POST and one profile GET. The access token is not retained."""

    def __init__(self, exchange: _Exchange) -> None:
        self._exchange = exchange
        self._access: list[str] = []
        self._posts = 0
        self._profiles = 0

    def __repr__(self) -> str:
        return "ProfileTransport"

    def post_form(self, endpoint: str, form: Mapping[str, str]) -> Mapping[str, object]:
        if self._posts or endpoint != _TOKEN_ENDPOINT:
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_ENDPOINT_REJECTED")
        if "client_secret" in form or "refresh_token" in form or "access_type" in form:
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED")
        self._posts += 1
        from urllib.parse import urlencode

        encoded = urlencode(list(form.items())).encode("ascii")
        status, body = self._call("POST", endpoint, encoded, None, "GMAIL_OAUTH_TOKEN_REJECTED")
        access_token = body.get("access_token")
        if status == 200 and type(access_token) is str and access_token != "":
            self._access = [access_token]
        retained = {key: value for key, value in body.items() if key != "refresh_token"}
        return {"status": status, "body": retained}

    def get_profile(self, endpoint: str, body: bytes) -> Mapping[str, object]:
        access_token = self._access[0] if self._access else None
        self._access = []
        if self._profiles or endpoint != _PROFILE_ENDPOINT or body != b"":
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_ENDPOINT_REJECTED")
        self._profiles += 1
        if type(access_token) is not str or access_token == "":
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED")
        status, payload = self._call(
            "GET",
            endpoint,
            b"",
            access_token,
            "GMAIL_OAUTH_PROFILE_REJECTED",
        )
        return {"status": status, "body": payload}

    def _call(
        self,
        method: str,
        endpoint: str,
        body: bytes,
        access_token: str | None,
        code: str,
    ) -> tuple[int, dict[str, object]]:
        try:
            status, payload = self._exchange(method, endpoint, body, _HTTP_TIMEOUT, access_token)
        except LocalOAuthProbeRejected:
            raise
        except Exception:
            raise LocalOAuthProbeRejected(code) from None
        if type(status) is not int or type(payload) is not dict:
            raise LocalOAuthProbeRejected(code)
        self._access = [] if method == "GET" else self._access
        return status, dict(payload)


class LoopbackListener:
    """One ``127.0.0.1`` listener on an operating-system-assigned port."""

    def __init__(self, open_socket: Callable[[], _BoundSocket]) -> None:
        self._open_socket = open_socket
        self._sock: _BoundSocket | None = None

    def __repr__(self) -> str:
        return "LoopbackListener"

    def bind(self) -> int:
        if self._sock is not None:
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED")
        sock = self._open_socket()
        try:
            sock.bind(("127.0.0.1", 0))
            sock.listen(1)
            address = sock.getsockname()
        except LocalOAuthProbeRejected:
            sock.close()
            raise
        except Exception:
            sock.close()
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED") from None
        if address[0] != "127.0.0.1" or type(address[1]) is not int:
            sock.close()
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED")
        self._sock = sock
        return address[1]

    def wait(self, timeout_seconds: int) -> tuple[tuple[str, str], ...] | None:
        if type(timeout_seconds) is not int or timeout_seconds < 1:
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_CALLBACK_REJECTED")
        sock = self._sock
        if sock is None:
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED")
        limit = _MAX_CALLBACK_WAIT if timeout_seconds > _MAX_CALLBACK_WAIT else timeout_seconds
        sock.settimeout(float(limit))
        try:
            connection, address = sock.accept()
        except TimeoutError:
            return None
        except LocalOAuthProbeRejected:
            raise
        except Exception:
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_CALLBACK_REJECTED") from None
        try:
            if not address or address[0] != "127.0.0.1":
                raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED")
            pairs = _pairs_from_request(_read_request(connection))
            connection.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            return pairs
        finally:
            connection.close()

    def close(self) -> None:
        sock = self._sock
        self._sock = None
        if sock is None:
            return
        try:
            sock.close()
        except OSError:
            return


def _path_argument(argv: list[str]) -> str:
    if len(argv) != 2 or type(argv[1]) is not str or argv[1] == "":
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED")
    return argv[1]


def _load_client_path(path: str) -> DesktopClientConfig:
    if type(path) is not str or path == "" or "\x00" in path:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED")
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read(_MAX_CLIENT_BYTES + 1)
    except OSError:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_TOKEN_REJECTED") from None
    return desktop_client_from_json_text(text)


def run_local_windows_profile_proof(client_json_path: str) -> str:
    """Run one attended local proof. Non-Windows refuses before any socket."""

    if sys.platform != "win32":
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_LIVE_UNAUTHORIZED")
    client = _load_client_path(client_json_path)
    import socket
    import time
    import webbrowser
    from urllib import error as urllib_error
    from urllib import request as urllib_request

    def exchange(
        method: str,
        endpoint: str,
        body: bytes,
        timeout_seconds: int,
        access_token: str | None,
    ) -> tuple[int, dict[str, object]]:
        class _NoRedirect(urllib_request.HTTPRedirectHandler):
            def redirect_request(
                self,
                req: object,
                fp: object,
                code: int,
                msg: str,
                headers: object,
                newurl: str,
            ) -> None:
                raise LocalOAuthProbeRejected("GMAIL_OAUTH_ENDPOINT_REJECTED")

        opener = urllib_request.build_opener(urllib_request.ProxyHandler({}), _NoRedirect)
        data = None if method == "GET" else body
        request = urllib_request.Request(endpoint, data=data, method=method)
        if access_token is not None:
            request.add_header("Authorization", "Bearer " + access_token)
        code = "GMAIL_OAUTH_TOKEN_REJECTED" if method == "POST" else "GMAIL_OAUTH_PROFILE_REJECTED"
        try:
            with opener.open(request, timeout=timeout_seconds) as response:
                status = response.status
                raw = response.read(65536)
        except urllib_error.HTTPError as error:
            status = error.code
            raw = error.read(65536)
        except LocalOAuthProbeRejected:
            raise
        except Exception:
            raise LocalOAuthProbeRejected(code) from None
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            raise LocalOAuthProbeRejected(code) from None
        if type(parsed) is not dict or type(status) is not int:
            raise LocalOAuthProbeRejected(code)
        return status, dict(parsed)

    def open_socket() -> _BoundSocket:
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    listener = LoopbackListener(open_socket)
    try:
        evidence = run_offline_profile_shape(
            client,
            ProfileTransport(exchange),
            listener,
            MonotonicClock(time.monotonic),
            CommandBrowser(webbrowser),
        )
    except LocalOAuthProbeRejected as rejected:
        print(rejected.code)
        return rejected.code
    if evidence.profile_result != _SHAPE_PASS or evidence.content_retained is not False:
        print(_REAL_BLOCKED)
        return _REAL_BLOCKED
    print(_REAL_PASS)
    return _REAL_PASS


def _scope_declaration(value: object) -> bool:
    if value == _METADATA_SCOPE or value == (_METADATA_SCOPE,):
        return True
    return type(value) is list and value == [_METADATA_SCOPE]


def _reject_redirects(value: object) -> None:
    if value is None:
        return
    if type(value) is not list or any(not _declared_loopback(item) for item in value):
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED")


def _declared_loopback(item: object) -> bool:
    return type(item) is str and _loopback(item)


def _loopback(uri: str) -> bool:
    if uri in {"http://127.0.0.1", "http://127.0.0.1/"}:
        return True
    prefix = "http://127.0.0.1:"
    if not uri.startswith(prefix):
        return False
    rest = uri[len(prefix) :]
    if rest.endswith("/"):
        rest = rest[:-1]
    if not rest.isdigit() or rest.startswith("0"):
        return False
    port = int(rest)
    return 1 <= port <= 65535


def _reject_declared_endpoint(installed: Mapping[str, object], key: str, expected: str) -> None:
    if key in installed and installed[key] != expected:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_ENDPOINT_REJECTED")


def _read_request(connection: _Connection) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while total < 8192:
        piece = connection.recv(8192 - total)
        if piece == b"":
            break
        chunks.append(piece)
        total += len(piece)
        if b"\r\n\r\n" in b"".join(chunks):
            break
    return b"".join(chunks)


def _pairs_from_request(raw: bytes) -> tuple[tuple[str, str], ...]:
    from urllib.parse import parse_qsl, urlsplit

    try:
        line = raw.split(b"\r\n", 1)[0].decode("ascii")
        parts = line.split(" ")
        if len(parts) != 3 or parts[0] != "GET":
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_CALLBACK_REJECTED")
        split = urlsplit(parts[1])
        if split.scheme or split.netloc or split.path != "/":
            raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED")
        parsed = parse_qsl(split.query, keep_blank_values=True, strict_parsing=True)
    except LocalOAuthProbeRejected:
        raise
    except Exception:
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_CALLBACK_REJECTED") from None
    return tuple((key, value) for key, value in parsed)


if __name__ == "__main__":
    try:
        run_local_windows_profile_proof(_path_argument(sys.argv))
    except KeyboardInterrupt:
        print(_REAL_BLOCKED)
        raise
    except LocalOAuthProbeRejected as rejected:
        print(rejected.code)
