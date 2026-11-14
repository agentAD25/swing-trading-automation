"""Gated paper account-read runtime. Importing it performs no side effect.

Production entry points take no grant, path, key, clock, or transport.
A caller-built boolean object cannot unlock Windows credentials or HTTPS.
Gate C2 flags on every result stay false. This module does not submit,
replace, cancel, or stream.
"""

from __future__ import annotations

import ctypes
import json
import ssl
import sys
import urllib.error
import urllib.request
from ctypes import wintypes
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, cast

from swingtrade.alpaca_paper_account_read import ACCOUNT_URL, _body_reason, _request_reason
from swingtrade.alpaca_paper_custody import PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET
from swingtrade.alpaca_paper_grant import GrantError, VerifiedGrant, authorize_production
from swingtrade.alpaca_paper_request_budget import BoundLedger, BudgetError, reserve_for_production

TIMEOUT_SECONDS = 10.0
MAX_BODY = 65536
MAX_SECRET_BYTES = 1024
PRIVILEGED_IO_ATTEMPTS = 0
_SAME_HOST = frozenset({"HTTP_429", "HTTP_5XX"})
_PAPER_TARGETS = (PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET)


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

    @property
    def trade_ready(self) -> bool:
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


class ScriptedCredentials:
    """Synthetic custody. It cannot read Windows Credential Manager."""

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


class ScriptedTransport:
    """Synthetic exchange. It does not open a connection."""

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


class DirectConnection(urllib.request.ProxyHandler):
    """Proxy slot held empty. Process proxy settings are not consulted."""

    def __init__(self) -> None:
        urllib.request.ProxyHandler.__init__(self, {})

    def https_open(self, request: object) -> None:
        del request
        return None


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


class CredentialRecord(ctypes.Structure):
    """Natural x64 layout of Windows CREDENTIALW."""

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


class NativeCredentialReader(Protocol):
    """Fake or native reader. The production path does not accept a caller reader."""

    def read(self, target: str, credential_type: int) -> tuple[bool, int, bytes | None]:
        """Return one credential blob. A false result means nothing was allocated."""

    def release(self) -> None:
        """Release one successful allocation."""


def read_paper_account() -> RuntimeDecision:
    """Privileged account read. The caller cannot supply a grant or a transport."""
    grant = _authorized_grant()
    reserve_for_production()
    material = _cred_read_native()
    status, body, redirected = _open_network(material)
    return _interpret(status, body, redirected, grant.account_id)


def load_privileged_credentials() -> tuple[bytes, bytes]:
    """Privileged custody read. A caller-selected reader is not accepted."""
    _authorized_grant()
    return _cred_read_native()


def observe_scripted(
    grant: VerifiedGrant,
    credentials: ScriptedCredentials,
    transport: ScriptedTransport,
    ledger: BoundLedger,
    now: datetime,
    *,
    method: str = "GET",
    url: str = ACCOUNT_URL,
) -> RuntimeDecision:
    """Synthetic observation. This path cannot construct the production opener."""
    if type(grant) is not VerifiedGrant:
        raise AccountRuntimeError("GRANT_UNVERIFIED")
    grant.ensure()
    if type(credentials) is not ScriptedCredentials or type(transport) is not ScriptedTransport:
        raise AccountRuntimeError("SYNTHETIC_BOUNDARY_REQUIRED")
    if type(ledger) is not BoundLedger:
        raise AccountRuntimeError("SYNTHETIC_BOUNDARY_REQUIRED")
    denied = _request_reason(method, url)
    if denied is not None:
        raise AccountRuntimeError(denied)
    material = _load_scripted(credentials)
    _reserve(ledger, grant, now)
    try:
        status, body, redirected = transport.exchange(method, url, material)
    except AccountRuntimeError:
        raise
    except TimeoutError:
        raise AccountRuntimeError("TIMEOUT") from None
    except ssl.SSLError:
        raise AccountRuntimeError("TLS_FAILED") from None
    except urllib.error.URLError:
        raise AccountRuntimeError("TRANSPORT_EXCEPTION") from None
    return _interpret(status, body, redirected, grant.account_id)


def build_controlled_opener() -> urllib.request.OpenerDirector:
    """HTTPS opener with an empty proxy map and no redirect follower."""
    opener = urllib.request.OpenerDirector()
    opener.add_handler(DirectConnection())
    opener.add_handler(urllib.request.HTTPSHandler(context=verified_tls_context()))
    opener.add_handler(RedirectRefusal())
    opener.add_handler(urllib.request.HTTPErrorProcessor())
    return opener


def verified_tls_context() -> ssl.SSLContext:
    """Default certificate and hostname verification. This does not connect."""
    context = ssl.create_default_context()
    require_verified_context(context)
    return context


def require_verified_context(context: ssl.SSLContext) -> None:
    """Refuse a context that does not verify the certificate and hostname."""
    if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
        raise AccountRuntimeError("TLS_POLICY_DENIED")


def bind_credential_api(library: Any) -> None:
    """Set CredReadW and CredFree prototypes. This does not call either function."""
    library.CredReadW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.POINTER(CredentialRecord)),
    )
    library.CredReadW.restype = wintypes.BOOL
    library.CredFree.argtypes = (ctypes.c_void_p,)
    library.CredFree.restype = None


def credential_field_offsets() -> dict[str, int]:
    """Byte offsets of the local CREDENTIALW definition."""
    return {
        name: getattr(CredentialRecord, name).offset for name, _ctype in CredentialRecord._fields_
    }


def consume_native_credential(reader: NativeCredentialReader, target: str) -> bytes:
    """Copy one mocked or native blob. Live targets are rejected before the read."""
    if target not in _PAPER_TARGETS:
        raise AccountRuntimeError("LIVE_TARGET_DENIED")
    found, size, blob = reader.read(target, 1)
    try:
        if not found or blob is None:
            raise AccountRuntimeError("CREDENTIAL_UNAVAILABLE")
        if size <= 0 or size > MAX_SECRET_BYTES or size != len(blob):
            raise AccountRuntimeError("MALFORMED_MATERIAL")
        copied = bytes(blob)
        _printable(copied)
        return copied
    finally:
        if found:
            reader.release()


def account_request(method: str, url: str, material: tuple[bytes, bytes]) -> urllib.request.Request:
    """Build the account GET. This function does not open the request."""
    if method != "GET" or url != ACCOUNT_URL:
        raise AccountRuntimeError("ENDPOINT_DENIED")
    request = urllib.request.Request(url, method=method)
    key, secret = material
    request.add_header("APCA-API-KEY-ID", key.decode("ascii"))
    request.add_header("APCA-API-SECRET-KEY", secret.decode("ascii"))
    return request


def _authorized_grant() -> VerifiedGrant:
    try:
        return authorize_production()
    except GrantError as error:
        raise AccountRuntimeError(error.reason) from None


def _load_scripted(credentials: ScriptedCredentials) -> tuple[bytes, bytes]:
    loaded = credentials.load()
    _printable(loaded[0])
    _printable(loaded[1])
    return loaded


def _printable(value: bytes) -> None:
    if value == b"" or any(byte < 33 or byte > 126 for byte in value):
        raise AccountRuntimeError("MALFORMED_MATERIAL")


def _reserve(ledger: BoundLedger, grant: VerifiedGrant, now: datetime) -> None:
    try:
        ledger.reserve(grant, now)
    except BudgetError as error:
        raise AccountRuntimeError(error.reason) from None


def _interpret(
    status: int,
    body: bytes,
    redirected: bool,
    expected_account_id: str,
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
    if parsed.get("id") != expected_account_id:
        raise AccountRuntimeError("ACCOUNT_BINDING_MISMATCH")
    observed = _account_reason(parsed)
    return RuntimeDecision(RuntimeClassification.ACCEPTED, observed, "NOT_REQUIRED")


def _account_reason(body: dict[str, object]) -> str:
    blocked = (
        body.get("status") != "ACTIVE"
        or body.get("trading_blocked") is not False
        or body.get("account_blocked") is not False
        or body.get("trade_suspended_by_user") is not False
    )
    if blocked:
        return "ACCOUNT_NOT_READY"
    return "ACCOUNT_OBSERVED"


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
        parsed = json.loads(body.decode("utf-8"), object_pairs_hook=_pairs)
    except AccountRuntimeError:
        raise
    except (UnicodeError, json.JSONDecodeError):
        raise AccountRuntimeError("MALFORMED_BODY") from None
    reason = _body_reason(parsed)
    if reason is not None:
        raise AccountRuntimeError(reason)
    if type(parsed) is not dict:
        raise AccountRuntimeError("MALFORMED_BODY")
    return parsed


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    found: dict[str, object] = {}
    for key, value in pairs:
        if key in found:
            raise AccountRuntimeError("DUPLICATE_FIELD")
        found[key] = value
    return found


def _cred_read_native() -> tuple[bytes, bytes]:
    _authorized_grant()
    if sys.platform != "win32":
        raise AccountRuntimeError("RUNTIME_PLATFORM_DENIED")
    global PRIVILEGED_IO_ATTEMPTS
    PRIVILEGED_IO_ATTEMPTS += 1
    library = _load_library()
    key = _read_target(library, PAPER_KEY_ID_TARGET)
    secret = _read_target(library, PAPER_SECRET_TARGET)
    return key, secret


def _load_library() -> Any:
    library = cast(Any, ctypes).WinDLL("advapi32")
    bind_credential_api(library)
    return library


def _read_target(library: Any, target: str) -> bytes:
    if target not in _PAPER_TARGETS:
        raise AccountRuntimeError("LIVE_TARGET_DENIED")
    pointer = ctypes.POINTER(CredentialRecord)()
    found = library.CredReadW(target, 1, 0, ctypes.byref(pointer))
    if not found or not pointer:
        raise AccountRuntimeError("CREDENTIAL_UNAVAILABLE")
    try:
        record = pointer.contents
        size = int(record.CredentialBlobSize)
        blob = record.CredentialBlob
        if size <= 0 or size > MAX_SECRET_BYTES or not blob:
            raise AccountRuntimeError("MALFORMED_MATERIAL")
        copied = ctypes.string_at(blob, size)
        _printable(copied)
        return copied
    finally:
        library.CredFree(pointer)


def _open_network(material: tuple[bytes, bytes]) -> tuple[int, bytes, bool]:
    _authorized_grant()
    if sys.platform != "win32":
        raise AccountRuntimeError("RUNTIME_PLATFORM_DENIED")
    global PRIVILEGED_IO_ATTEMPTS
    PRIVILEGED_IO_ATTEMPTS += 1
    request = account_request("GET", ACCOUNT_URL, material)
    opener = build_controlled_opener()
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
        return int(error.code), payload, False
    except urllib.error.URLError as error:
        reason = error.reason
        if isinstance(reason, TimeoutError):
            raise AccountRuntimeError("TIMEOUT") from None
        if isinstance(reason, ssl.SSLError):
            raise AccountRuntimeError("TLS_FAILED") from None
        raise AccountRuntimeError("TRANSPORT_EXCEPTION") from None
    with response:
        payload = response.read(MAX_BODY + 1)
        status = int(response.status)
    if len(payload) > MAX_BODY:
        raise AccountRuntimeError("RESPONSE_TOO_LARGE")
    return status, payload, False
