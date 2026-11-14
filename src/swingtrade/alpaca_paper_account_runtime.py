"""Dormant paper account-read runtime. Importing it performs no side effect.

The ungranted entry refuses before custody, budget, or transport work.
A caller-supplied standing grant is the only way past that refusal.
Gate C2 flags on this result stay false. This module does not submit,
replace, cancel, or stream.
"""

from __future__ import annotations

import json
import ssl
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from enum import StrEnum

from swingtrade.alpaca_paper_account_read import ACCOUNT_URL, _body_reason, _request_reason
from swingtrade.alpaca_paper_custody import PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET
from swingtrade.alpaca_paper_request_budget import BudgetError, DurableRequestBudget

GRANT_NAME = "LANE1_ALPACA_STANDING_PAPER_ACCOUNT_READ_AUTHORIZED"
TIMEOUT_SECONDS = 10.0
MAX_BODY = 65536
_SAME_HOST = frozenset({"HTTP_429", "HTTP_5XX"})
_OPENER_FACTORY = Callable[[], urllib.request.OpenerDirector]
_IO_ATTEMPTS = 0


class RuntimeClassification(StrEnum):
    """Observation label. Neither value turns on a Gate C2 flag."""

    ACCEPTED = "ACCEPTED"
    DENIED = "DENIED"


class RuntimeDecision:
    """One gated observation. Every action flag stays closed."""

    __slots__ = ("classification", "reason", "retry_disposition")

    def __init__(
        self,
        classification: RuntimeClassification,
        reason: str,
        retry_disposition: str,
    ) -> None:
        self.classification = classification
        self.reason = reason
        self.retry_disposition = retry_disposition

    @property
    def connect_allowed(self) -> bool:
        return False

    @property
    def network_permitted(self) -> bool:
        return False

    @property
    def submit_permitted(self) -> bool:
        return False

    @property
    def cancel_permitted(self) -> bool:
        return False

    @property
    def replace_permitted(self) -> bool:
        return False

    @property
    def resubmit_permitted(self) -> bool:
        return False

    @property
    def safe_to_retry(self) -> bool:
        return False

    def __repr__(self) -> str:
        return (
            f"RuntimeDecision({self.classification.value}, {self.reason}, {self.retry_disposition})"
        )

    def __str__(self) -> str:
        return self.reason


class AccountRuntimeError(RuntimeError):
    """Reason code only. Secrets and response bodies are omitted."""

    def __init__(self, reason: str, retry_disposition: str = "NOT_RETRYABLE") -> None:
        self.reason = reason
        self.decision = RuntimeDecision(
            RuntimeClassification.DENIED,
            reason,
            retry_disposition,
        )
        super().__init__(reason)


class StandingGrant:
    """Explicit grant value. The inactive constructor is the production default."""

    __slots__ = ("attended", "effective", "expected_account_id", "name")

    def __init__(
        self,
        name: str,
        *,
        effective: bool,
        attended: bool,
        expected_account_id: str | None = None,
    ) -> None:
        self.name = name
        self.effective = effective
        self.attended = attended
        self.expected_account_id = expected_account_id

    def __repr__(self) -> str:
        state = "effective" if self.effective and self.attended else "inactive"
        return f"StandingGrant({state})"


class ScriptedCredentials:
    """Injected custody. Bytes are not included in text."""

    __slots__ = ("_key", "_secret")

    def __init__(self, key: bytes | None, secret: bytes | None) -> None:
        self._key = key
        self._secret = secret

    def load(self) -> tuple[bytes, bytes]:
        key = self._key
        secret = self._secret
        if key is None or secret is None or key == b"" or secret == b"":
            raise AccountRuntimeError("CREDENTIAL_UNAVAILABLE")
        return key, secret

    def __repr__(self) -> str:
        return "ScriptedCredentials()"


class WindowsPaperCredentialAdapter:
    """Paper-target adapter. Native retrieval runs only after an effective grant."""

    __slots__ = ("_grant", "_reader")

    def __init__(
        self,
        grant: StandingGrant,
        reader: Callable[[], tuple[bytes, bytes]] | None = None,
    ) -> None:
        self._grant = grant
        self._reader = reader

    def load(self) -> tuple[bytes, bytes]:
        _require_grant(self._grant)
        if self._reader is not None:
            return self._reader()
        return _cred_read_native(self._grant)

    def __repr__(self) -> str:
        return "WindowsPaperCredentialAdapter()"


class ScriptedTransport:
    """Injected exchange. Credential bytes are not retained."""

    __slots__ = ("_fault", "_redirected", "_result", "calls")

    def __init__(
        self,
        result: tuple[int, bytes] | None = None,
        *,
        fault: str | None = None,
        redirected: bool = False,
    ) -> None:
        self._result = result
        self._fault = fault
        self._redirected = redirected
        self.calls = 0

    def exchange(
        self,
        method: str,
        url: str,
        material: tuple[bytes, bytes],
    ) -> tuple[int, bytes, bool]:
        del method, url, material
        self.calls += 1
        if self._fault == "tls":
            raise ssl.SSLError("TLS_FAILED")
        if self._fault == "timeout":
            raise TimeoutError("TIMEOUT")
        if self._fault == "exception":
            raise urllib.error.URLError("TRANSPORT_EXCEPTION")
        if self._result is None:
            raise AccountRuntimeError("AMBIGUOUS_RESPONSE")
        status, body = self._result
        return status, body, self._redirected

    def __repr__(self) -> str:
        return f"ScriptedTransport(calls={self.calls})"


class PaperGetTransport:
    """GET transport. The default opener stays unbuilt until a grant passes."""

    __slots__ = ("_factory", "_grant")

    def __init__(
        self,
        grant: StandingGrant,
        opener_factory: _OPENER_FACTORY | None = None,
    ) -> None:
        self._grant = grant
        self._factory = opener_factory

    def exchange(
        self,
        method: str,
        url: str,
        material: tuple[bytes, bytes],
    ) -> tuple[int, bytes, bool]:
        _require_grant(self._grant)
        denied = _request_reason(method, url)
        if denied is not None:
            raise AccountRuntimeError(denied)
        try:
            if self._factory is not None:
                return _exchange_with_factory(self._factory, method, url, material)
            return _open_granted(self._grant, method, url, material)
        except AccountRuntimeError:
            raise
        except TimeoutError:
            raise AccountRuntimeError("TIMEOUT") from None
        except ssl.SSLError:
            raise AccountRuntimeError("TLS_FAILED") from None

    def __repr__(self) -> str:
        return "PaperGetTransport()"


def inactive_grant() -> StandingGrant:
    """The production default. It cannot pass the standing-grant check."""
    return StandingGrant(GRANT_NAME, effective=False, attended=False)


def read_paper_account() -> RuntimeDecision:
    """Ungranted entry. It does not load custody, reserve budget, or connect."""
    _require_grant(inactive_grant())
    raise AccountRuntimeError("GRANT_INACTIVE")


def run_account_read(
    grant: StandingGrant,
    credentials: object,
    transport: object,
    ledger: DurableRequestBudget,
    *,
    method: str = "GET",
    url: str = ACCOUNT_URL,
) -> RuntimeDecision:
    """Read one scripted or injected account response after the grant check."""
    _require_grant(grant)
    _require_binding_shape(grant.expected_account_id)
    denied = _request_reason(method, url)
    if denied is not None:
        raise AccountRuntimeError(denied)
    material = _load_material(credentials)
    _reserve(ledger)
    try:
        status, body, redirected = _exchange(transport, method, url, material)
    except AccountRuntimeError:
        raise
    except TimeoutError:
        raise AccountRuntimeError("TIMEOUT") from None
    except ssl.SSLError:
        raise AccountRuntimeError("TLS_FAILED") from None
    except urllib.error.URLError:
        raise AccountRuntimeError("TRANSPORT_EXCEPTION") from None
    return _interpret(status, body, redirected, grant.expected_account_id)


def verified_tls_context() -> ssl.SSLContext:
    """Default certificate and hostname verification. This does not connect."""
    context = ssl.create_default_context()
    require_verified_context(context)
    return context


def require_verified_context(context: ssl.SSLContext) -> None:
    """Refuse a context that does not verify the certificate and hostname."""
    if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
        raise AccountRuntimeError("TLS_POLICY_DENIED")


class RedirectRefusal(urllib.request.HTTPRedirectHandler):
    """Redirects are closed for the paper account endpoint."""

    def redirect_request(
        self,
        req: object,
        fp: object,
        code: object,
        msg: object,
        headers: object,
        newurl: object,
    ) -> None:
        del req, fp, code, msg, headers, newurl
        raise AccountRuntimeError("REDIRECT_DENIED")


def _require_grant(grant: object) -> StandingGrant:
    if type(grant) is not StandingGrant:
        raise AccountRuntimeError("GRANT_INACTIVE")
    if grant.name != GRANT_NAME or grant.effective is not True or grant.attended is not True:
        raise AccountRuntimeError("GRANT_INACTIVE")
    return grant


def _require_binding_shape(expected: object) -> None:
    if expected is None:
        return
    if type(expected) is not str or expected == "" or expected != expected.strip():
        raise AccountRuntimeError("MALFORMED_BINDING")


def _load_material(credentials: object) -> tuple[bytes, bytes]:
    load = getattr(credentials, "load", None)
    if not callable(load):
        raise AccountRuntimeError("CREDENTIAL_UNAVAILABLE")
    loaded = load()
    if (
        type(loaded) is not tuple
        or len(loaded) != 2
        or type(loaded[0]) is not bytes
        or type(loaded[1]) is not bytes
    ):
        raise AccountRuntimeError("CREDENTIAL_UNAVAILABLE")
    _printable(loaded[0])
    _printable(loaded[1])
    return loaded


def _printable(value: bytes) -> None:
    if value == b"" or any(byte < 33 or byte > 126 for byte in value):
        raise AccountRuntimeError("MALFORMED_MATERIAL")


def _reserve(ledger: DurableRequestBudget) -> None:
    try:
        ledger.reserve()
    except BudgetError as error:
        raise AccountRuntimeError(error.reason) from None


def _exchange(
    transport: object,
    method: str,
    url: str,
    material: tuple[bytes, bytes],
) -> tuple[int, bytes, bool]:
    exchange = getattr(transport, "exchange", None)
    if not callable(exchange):
        raise AccountRuntimeError("TRANSPORT_DENIED")
    outcome = exchange(method, url, material)
    if (
        type(outcome) is not tuple
        or len(outcome) != 3
        or type(outcome[0]) is not int
        or type(outcome[1]) is not bytes
        or type(outcome[2]) is not bool
    ):
        raise AccountRuntimeError("AMBIGUOUS_RESPONSE")
    return outcome


def _interpret(
    status: int,
    body: bytes,
    redirected: bool,
    expected_account_id: str | None,
) -> RuntimeDecision:
    if redirected or 300 <= status < 400:
        raise AccountRuntimeError("REDIRECT_DENIED")
    reason = _status_reason(status)
    if reason is not None:
        disposition = "SAME_HOST_ELIGIBLE" if reason in _SAME_HOST else "NOT_RETRYABLE"
        raise AccountRuntimeError(reason, disposition)
    if len(body) > MAX_BODY:
        raise AccountRuntimeError("RESPONSE_TOO_LARGE")
    parsed = _parsed_body(body)
    if expected_account_id is not None and parsed.get("id") != expected_account_id:
        raise AccountRuntimeError("ACCOUNT_BINDING_MISMATCH")
    return RuntimeDecision(RuntimeClassification.ACCEPTED, "ACCOUNT_READ", "NOT_REQUIRED")


def _status_reason(status: int) -> str | None:
    if status == 200:
        return None
    if status == 401:
        return "HTTP_401"
    if status == 403:
        return "HTTP_403"
    if status == 429:
        return "HTTP_429"
    if 500 <= status <= 599:
        return "HTTP_5XX"
    return "HTTP_STATUS_DENIED"


def _parsed_body(body: bytes) -> dict[str, object]:
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise AccountRuntimeError("MALFORMED_BODY") from None
    reason = _body_reason(parsed)
    if reason is not None:
        raise AccountRuntimeError(reason)
    if type(parsed) is not dict:
        raise AccountRuntimeError("MALFORMED_BODY")
    return parsed


def _exchange_with_factory(
    factory: _OPENER_FACTORY,
    method: str,
    url: str,
    material: tuple[bytes, bytes],
) -> tuple[int, bytes, bool]:
    if method != "GET" or url != ACCOUNT_URL:
        raise AccountRuntimeError("ENDPOINT_DENIED")
    opener = factory()
    return _read_opener(opener, method, url, material)


def _open_granted(
    grant: StandingGrant,
    method: str,
    url: str,
    material: tuple[bytes, bytes],
) -> tuple[int, bytes, bool]:
    _require_grant(grant)
    if sys.platform != "win32":
        raise AccountRuntimeError("RUNTIME_PLATFORM_DENIED")
    if method != "GET" or url != ACCOUNT_URL:
        raise AccountRuntimeError("ENDPOINT_DENIED")
    global _IO_ATTEMPTS
    _IO_ATTEMPTS += 1
    return _read_opener(_default_opener(), method, url, material)


def _default_opener() -> urllib.request.OpenerDirector:
    context = verified_tls_context()
    https_handler = urllib.request.HTTPSHandler(context=context)
    return urllib.request.build_opener(https_handler, RedirectRefusal)


def _read_opener(
    opener: urllib.request.OpenerDirector,
    method: str,
    url: str,
    material: tuple[bytes, bytes],
) -> tuple[int, bytes, bool]:
    request = urllib.request.Request(url, method=method)
    key, secret = material
    request.add_header("APCA-API-KEY-ID", key.decode("ascii"))
    request.add_header("APCA-API-SECRET-KEY", secret.decode("ascii"))
    try:
        response = opener.open(request, timeout=TIMEOUT_SECONDS)
    except AccountRuntimeError:
        raise
    except TimeoutError:
        raise AccountRuntimeError("TIMEOUT") from None
    except ssl.SSLError:
        raise AccountRuntimeError("TLS_FAILED") from None
    except urllib.error.HTTPError as error:
        payload = error.read(MAX_BODY + 1)
        return error.code, payload, False
    except urllib.error.URLError as error:
        reason = error.reason
        if isinstance(reason, TimeoutError):
            raise AccountRuntimeError("TIMEOUT") from None
        if isinstance(reason, ssl.SSLError):
            raise AccountRuntimeError("TLS_FAILED") from None
        raise AccountRuntimeError("TRANSPORT_EXCEPTION") from None
    with response:
        payload = response.read(MAX_BODY + 1)
        status = response.status
    if len(payload) > MAX_BODY:
        raise AccountRuntimeError("RESPONSE_TOO_LARGE")
    return status, payload, False


def _cred_read_native(grant: StandingGrant) -> tuple[bytes, bytes]:
    _require_grant(grant)
    if sys.platform != "win32":
        raise AccountRuntimeError("RUNTIME_PLATFORM_DENIED")
    global _IO_ATTEMPTS
    _IO_ATTEMPTS += 1
    key = _cred_read_target(PAPER_KEY_ID_TARGET)
    secret = _cred_read_target(PAPER_SECRET_TARGET)
    _printable(key)
    _printable(secret)
    return key, secret


def _cred_read_target(target: str) -> bytes:
    if target != PAPER_KEY_ID_TARGET and target != PAPER_SECRET_TARGET:
        raise AccountRuntimeError("LIVE_TARGET_DENIED")
    import ctypes
    from ctypes import wintypes

    class _Credential(ctypes.Structure):
        _fields_ = (
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWrittenLow", wintypes.DWORD),
            ("LastWrittenHigh", wintypes.DWORD),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_char)),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        )

    library = ctypes.WinDLL("advapi32")
    pointer = ctypes.POINTER(_Credential)()
    found = library.CredReadW(target, 1, 0, ctypes.byref(pointer))
    if not found:
        raise AccountRuntimeError("CREDENTIAL_UNAVAILABLE")
    try:
        record = pointer.contents
        size = int(record.CredentialBlobSize)
        if size <= 0 or not record.CredentialBlob:
            raise AccountRuntimeError("CREDENTIAL_UNAVAILABLE")
        return ctypes.string_at(record.CredentialBlob, size)
    finally:
        library.CredFree(pointer)
