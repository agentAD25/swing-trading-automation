"""Synthetic account-read attacks. No real credential or provider call."""

from __future__ import annotations

import ast
import ctypes
import hashlib
import inspect
import json
import ssl
import urllib.error
import urllib.request
from ctypes import wintypes
from pathlib import Path

import pytest

from swingtrade import alpaca_paper_account_runtime as runtime
from swingtrade.alpaca_paper_account_read import ACCOUNT_URL
from swingtrade.alpaca_paper_account_runtime import (
    AccountRuntimeError,
    CredentialRecord,
    DirectConnection,
    RedirectRefusal,
    RuntimeClassification,
    ScriptedCredentials,
    ScriptedTransport,
    account_request,
    bind_credential_api,
    build_controlled_opener,
    consume_native_credential,
    credential_field_offsets,
    load_privileged_credentials,
    observe_scripted,
    read_paper_account,
    require_verified_context,
    verified_tls_context,
)
from swingtrade.alpaca_paper_boundary import LIVE_HOST, PAPER_HOST
from swingtrade.alpaca_paper_custody import PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET
from swingtrade.alpaca_paper_grant import current_windows_sid
from swingtrade.alpaca_paper_request_budget import DAILY_LIMIT, BoundLedger
from tests.unit.test_alpaca_paper_support import ACCOUNT, LEDGER, WHEN, issue, prepare

_KEY = b"synthetic-paper-key"
_SECRET = b"synthetic-paper-secret"
_FLAGS = (
    "connect_allowed",
    "network_permitted",
    "submit_permitted",
    "cancel_permitted",
    "replace_permitted",
    "resubmit_permitted",
    "safe_to_retry",
)
_SOURCES = (
    Path(__file__).parents[2] / "src" / "swingtrade" / "alpaca_paper_account_runtime.py",
    Path(__file__).parents[2] / "src" / "swingtrade" / "alpaca_paper_request_budget.py",
    Path(__file__).parents[2] / "src" / "swingtrade" / "alpaca_paper_grant.py",
)


def test_active_account_is_observed_and_not_trade_ready(tmp_path: Path) -> None:
    decision = _read(tmp_path, _payload())
    assert decision.classification is RuntimeClassification.ACCEPTED
    assert decision.reason == "ACCOUNT_OBSERVED"
    assert decision.trade_ready is False
    _assert_flags(decision)
    assert "PAPER0001" not in repr(decision)
    assert ACCOUNT not in repr(decision)
    decision = _read(tmp_path, _payload(buying_power="1.00"), ledger_id="ready0002")
    assert decision.reason == "ACCOUNT_OBSERVED"
    decision = _read(tmp_path, _payload(trading_blocked=True), ledger_id="ready0003")
    assert decision.reason == "ACCOUNT_NOT_READY"
    assert decision.trade_ready is False
    decision = _read(tmp_path, _payload(status="REJECTED"), ledger_id="ready0004")
    assert decision.reason == "ACCOUNT_NOT_READY"


def test_binding_duplicate_and_incomplete_bodies_are_refused(tmp_path: Path) -> None:
    _runtime_deny(tmp_path, _payload(account="other-account"), "ACCOUNT_BINDING_MISMATCH")
    error = _runtime_deny(
        tmp_path,
        _duplicate_identity(),
        "DUPLICATE_FIELD",
        ledger_id="body0002",
    )
    assert "other-account" not in str(error)
    assert ACCOUNT not in str(error)
    _runtime_deny(tmp_path, b'{"status":"ACTIVE"}', "INCOMPLETE_ACCOUNT", ledger_id="body0003")


def test_http_redirect_tls_timeout_and_ambiguous_results(tmp_path: Path) -> None:
    cases = (
        ((401, b"{}"), "HTTP_401", "NOT_RETRYABLE"),
        ((403, b"{}"), "HTTP_403", "NOT_RETRYABLE"),
        ((429, b"{}"), "HTTP_429", "SAME_HOST_ELIGIBLE"),
        ((503, b"{}"), "HTTP_5XX", "SAME_HOST_ELIGIBLE"),
        ((302, b"{}"), "REDIRECT_DENIED", "NOT_RETRYABLE"),
    )
    for index, (result, reason, disposition) in enumerate(cases, start=1):
        transport = ScriptedTransport(result, redirected=result[0] == 302)
        error = _fail(tmp_path, transport, f"http{index:04d}", reason)
        assert error.decision.retry_disposition == disposition
        assert error.decision.safe_to_retry is False
        assert transport.calls == 1
    timeout = ScriptedTransport(fault="timeout")
    _fail(tmp_path, timeout, "timeout01", "TIMEOUT")
    assert timeout.calls == 1
    tls = ScriptedTransport(fault="tls")
    _fail(tmp_path, tls, "tls00001", "TLS_FAILED")
    lost = ScriptedTransport(fault="exception")
    _fail(tmp_path, lost, "lost0001", "TRANSPORT_EXCEPTION")
    assert lost.calls == 1
    ambiguous = ScriptedTransport()
    _fail(tmp_path, ambiguous, "ambig001", "AMBIGUOUS_RESPONSE")
    assert ambiguous.calls == 1
    grant = issue(ledger_id="ambig001")
    ledger = BoundLedger(tmp_path / "ambig001")
    assert ledger.spent(grant, WHEN) == 1
    again = ScriptedTransport()
    _fail(tmp_path, again, "ambig001", "AMBIGUOUS_RESPONSE", initialize=False)
    assert again.calls == 1
    assert ledger.spent(grant, WHEN) == 2


def test_wrong_host_and_forbidden_routes_do_not_reserve(tmp_path: Path) -> None:
    routes = (
        (f"https://{LIVE_HOST}/v2/account", "LIVE_HOST_DENIED"),
        (f"https://{PAPER_HOST}/v2/orders", "ORDER_ROUTE_DENIED"),
        (f"https://{PAPER_HOST}/v2/positions", "POSITION_ROUTE_DENIED"),
        (f"https://{PAPER_HOST}/v2/events", "STREAM_ROUTE_DENIED"),
    )
    for index, (url, reason) in enumerate(routes, start=1):
        name = f"route{index:04d}"
        transport = ScriptedTransport((_ok_body(),))
        grant, _ledger = prepare(tmp_path / name, ledger_id=name)
        with pytest.raises(AccountRuntimeError) as caught:
            observe_scripted(
                grant,
                ScriptedCredentials(_KEY, _SECRET),
                transport,
                BoundLedger(tmp_path / name),
                WHEN,
                url=url,
            )
        assert caught.value.reason == reason
        assert transport.calls == 0
        assert BoundLedger(tmp_path / name).spent(grant, WHEN) == 0


def test_budget_exhaustion_does_not_exchange(tmp_path: Path) -> None:
    grant, ledger = prepare(tmp_path / LEDGER)
    for _ in range(DAILY_LIMIT):
        ledger.reserve(grant, WHEN)
    transport = ScriptedTransport((_ok_status(), _payload()))
    with pytest.raises(AccountRuntimeError) as caught:
        observe_scripted(
            grant,
            ScriptedCredentials(_KEY, _SECRET),
            transport,
            ledger,
            WHEN,
        )
    assert caught.value.reason == "BUDGET_EXHAUSTED"
    assert transport.calls == 0


def test_missing_credentials_do_not_reserve_or_exchange(tmp_path: Path) -> None:
    grant, ledger = prepare(tmp_path / LEDGER)
    transport = ScriptedTransport((_ok_status(), _payload()))
    with pytest.raises(AccountRuntimeError) as caught:
        observe_scripted(grant, ScriptedCredentials(None, None), transport, ledger, WHEN)
    assert caught.value.reason == "CREDENTIAL_UNAVAILABLE"
    assert transport.calls == 0
    assert ledger.spent(grant, WHEN) == 0


def test_privileged_entry_has_no_side_effect(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("privileged io")

    monkeypatch.setattr(
        "swingtrade.alpaca_paper_account_runtime._cred_read_native",
        denied,
    )
    monkeypatch.setattr(
        "swingtrade.alpaca_paper_account_runtime._open_network",
        denied,
    )
    monkeypatch.setattr(
        "swingtrade.alpaca_paper_grant.current_windows_sid",
        denied,
    )
    with pytest.raises(AccountRuntimeError) as caught:
        read_paper_account()
    assert caught.value.reason == "GRANT_ANCHOR_ABSENT"
    with pytest.raises(AccountRuntimeError) as custody:
        load_privileged_credentials()
    assert custody.value.reason == "GRANT_ANCHOR_ABSENT"
    assert runtime.PRIVILEGED_IO_ATTEMPTS == 0
    assert current_windows_sid.__name__ == "current_windows_sid"


def test_opener_disables_proxy_discovery_and_redirects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def discovered() -> dict[str, str]:
        raise AssertionError("proxy discovery")

    monkeypatch.setattr(urllib.request, "getproxies", discovered)
    opener = build_controlled_opener()
    proxies = [handler for handler in opener.handlers if type(handler) is DirectConnection]
    assert len(proxies) == 1
    assert proxies[0].proxies == {}
    assert any(type(handler) is RedirectRefusal for handler in opener.handlers)
    assert not any(type(handler) is urllib.request.HTTPHandler for handler in opener.handlers)
    assert not any(type(handler) is urllib.request.FileHandler for handler in opener.handlers)
    https = next(
        handler for handler in opener.handlers if type(handler) is urllib.request.HTTPSHandler
    )
    assert https._context.verify_mode == ssl.CERT_REQUIRED  # type: ignore[attr-defined]
    assert https._context.check_hostname is True  # type: ignore[attr-defined]
    context = verified_tls_context()
    require_verified_context(context)
    context.check_hostname = False
    with pytest.raises(AccountRuntimeError) as caught:
        require_verified_context(context)
    assert caught.value.reason == "TLS_POLICY_DENIED"
    with pytest.raises(AccountRuntimeError) as redirected:
        RedirectRefusal().redirect_request(None, None, 302, None, None, "https://other")
    assert redirected.value.reason == "REDIRECT_DENIED"


def test_request_builder_does_not_open_and_hides_material() -> None:
    request = account_request("GET", ACCOUNT_URL, (_KEY, _SECRET))
    assert request.get_method() == "GET"
    assert request.full_url == ACCOUNT_URL
    header = request.get_header("Apca-api-key-id")
    assert header is not None
    assert hashlib.sha256(header.encode("ascii")).digest() == hashlib.sha256(_KEY).digest()
    with pytest.raises(AccountRuntimeError) as caught:
        account_request("POST", ACCOUNT_URL, (_KEY, _SECRET))
    assert caught.value.reason == "ENDPOINT_DENIED"
    assert _SECRET.decode("ascii") not in str(caught.value)


def test_native_credential_contract_uses_a_fake_api() -> None:
    offsets = credential_field_offsets()
    if ctypes.sizeof(ctypes.c_void_p) == 8:
        assert offsets["Flags"] == 0
        assert offsets["Type"] == 4
        assert offsets["LastWrittenLow"] == 24
        assert offsets["LastWrittenHigh"] == 28
        assert offsets["CredentialBlobSize"] == 32
        assert offsets["CredentialBlob"] == 40
        assert offsets["UserName"] == 72
        assert ctypes.sizeof(CredentialRecord) == 80

    class _Function:
        def __init__(self) -> None:
            self.argtypes: object = None
            self.restype: object = None

    class _Library:
        def __init__(self) -> None:
            self.CredReadW = _Function()
            self.CredFree = _Function()

    library = _Library()
    bind_credential_api(library)
    assert library.CredReadW.restype is wintypes.BOOL
    assert library.CredFree.restype is None
    assert len(library.CredReadW.argtypes) == 4  # type: ignore[arg-type]
    reader = _FakeCredential(True, len(_KEY), _KEY)
    assert consume_native_credential(reader, PAPER_KEY_ID_TARGET) == _KEY
    assert reader.reads == 1
    assert reader.releases == 1
    assert reader.kind == 1
    missing = _FakeCredential(False, 0, None)
    with pytest.raises(AccountRuntimeError) as absent:
        consume_native_credential(missing, PAPER_SECRET_TARGET)
    assert absent.value.reason == "CREDENTIAL_UNAVAILABLE"
    assert missing.releases == 0
    null = _FakeCredential(True, 4, None)
    with pytest.raises(AccountRuntimeError) as empty:
        consume_native_credential(null, PAPER_SECRET_TARGET)
    assert empty.value.reason == "CREDENTIAL_UNAVAILABLE"
    assert null.releases == 1
    oversized = _FakeCredential(True, 1025, b"a" * 1025)
    with pytest.raises(AccountRuntimeError) as malformed:
        consume_native_credential(oversized, PAPER_KEY_ID_TARGET)
    assert malformed.value.reason == "MALFORMED_MATERIAL"
    assert oversized.releases == 1
    live = _FakeCredential(True, 4, b"live")
    with pytest.raises(AccountRuntimeError) as denied:
        consume_native_credential(live, "swing-trading/lane2/alpaca/live/secret")
    assert denied.value.reason == "LIVE_TARGET_DENIED"
    assert live.reads == 0
    assert _SECRET.decode("ascii") not in str(malformed.value)


def test_runtime_source_has_no_forbidden_token_or_retry_loop() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in _SOURCES)
    lowered = source.lower()
    for token in ("requests.", "httpx.", "socket.", "tradestation", "place_order", "cancel_order"):
        assert token not in lowered
    assert "environ" not in lowered
    assert "build_opener" not in source
    assert "StandingGrant" not in source
    for function in (observe_scripted, read_paper_account, load_privileged_credentials):
        parsed = ast.parse(inspect.getsource(function)).body[0]
        assert isinstance(parsed, ast.FunctionDef)
        assert not any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(parsed))
    assert inspect.signature(read_paper_account).parameters == {}
    assert inspect.signature(load_privileged_credentials).parameters == {}
    assert PAPER_KEY_ID_TARGET
    assert PAPER_SECRET_TARGET


def _payload(account: str = ACCOUNT, **extra: object) -> bytes:
    body: dict[str, object] = {
        "id": account,
        "account_number": "PAPER0001",
        "status": "ACTIVE",
        "currency": "USD",
        "trading_blocked": False,
        "account_blocked": False,
        "trade_suspended_by_user": False,
    }
    body.update(extra)
    return json.dumps(body).encode("utf-8")


def _duplicate_identity() -> bytes:
    body = _payload().decode("utf-8")
    return body.replace('"id"', '"id":"other-account","id"', 1).encode("utf-8")


def _read(tmp_path: Path, body: bytes, ledger_id: str = "ready0001") -> object:
    grant, ledger = prepare(tmp_path / ledger_id, ledger_id=ledger_id)
    decision = observe_scripted(
        grant,
        ScriptedCredentials(_KEY, _SECRET),
        ScriptedTransport((200, body)),
        ledger,
        WHEN,
    )
    return decision


def _runtime_deny(
    tmp_path: Path, body: bytes, reason: str, ledger_id: str = "body0001"
) -> AccountRuntimeError:
    grant, ledger = prepare(tmp_path / ledger_id, ledger_id=ledger_id)
    with pytest.raises(AccountRuntimeError) as caught:
        observe_scripted(
            grant,
            ScriptedCredentials(_KEY, _SECRET),
            ScriptedTransport((200, body)),
            ledger,
            WHEN,
        )
    assert caught.value.reason == reason
    assert _SECRET.decode("ascii") not in str(caught.value)
    return caught.value


def _fail(
    tmp_path: Path,
    transport: ScriptedTransport,
    ledger_id: str,
    reason: str,
    *,
    initialize: bool = True,
) -> AccountRuntimeError:
    if initialize:
        grant, ledger = prepare(tmp_path / ledger_id, ledger_id=ledger_id)
    else:
        grant = issue(ledger_id=ledger_id)
        ledger = BoundLedger(tmp_path / ledger_id)
    with pytest.raises(AccountRuntimeError) as caught:
        observe_scripted(grant, ScriptedCredentials(_KEY, _SECRET), transport, ledger, WHEN)
    assert caught.value.reason == reason
    return caught.value


def _ok_status() -> int:
    return 200


def _ok_body() -> bytes:
    return _payload()


def _assert_flags(decision: object) -> None:
    for name in _FLAGS:
        assert getattr(decision, name) is False


class _FakeCredential:
    def __init__(self, found: bool, size: int, blob: bytes | None) -> None:
        self.found = found
        self.size = size
        self.blob = blob
        self.reads = 0
        self.releases = 0
        self.kind = 0

    def read(self, target: str, credential_type: int) -> tuple[bool, int, bytes | None]:
        del target
        self.reads += 1
        self.kind = credential_type
        return self.found, self.size, self.blob

    def release(self) -> None:
        self.releases += 1
