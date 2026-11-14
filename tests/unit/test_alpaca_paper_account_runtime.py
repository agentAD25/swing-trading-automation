"""Dormant paper account-read runtime. No real credential or provider call."""

from __future__ import annotations

import ast
import io
import json
import ssl
import urllib.error
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path

import pytest

from swingtrade.alpaca_paper_account_read import (
    ACCOUNT_URL,
    AccountReadDecision,
    ReadClassification,
)
from swingtrade.alpaca_paper_account_runtime import (
    MAX_BODY,
    AccountRuntimeError,
    PaperGetTransport,
    RedirectRefusal,
    RuntimeClassification,
    ScriptedCredentials,
    ScriptedTransport,
    StandingGrant,
    WindowsPaperCredentialAdapter,
    inactive_grant,
    read_paper_account,
    require_verified_context,
    run_account_read,
    verified_tls_context,
)
from swingtrade.alpaca_paper_boundary import LIVE_HOST, PAPER_HOST, evaluate_paper_boundary
from swingtrade.alpaca_paper_custody import PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET
from swingtrade.alpaca_paper_request_budget import DAILY_LIMIT, DurableRequestBudget

_KEY = b"synthetic-paper-key"
_SECRET = b"synthetic-paper-secret"
_WHEN = datetime(2026, 11, 14, 15, 0, tzinfo=UTC)
_FLAGS = (
    "connect_allowed",
    "network_permitted",
    "submit_permitted",
    "cancel_permitted",
    "replace_permitted",
    "resubmit_permitted",
    "safe_to_retry",
)
_SOURCE = Path(__file__).parents[2] / "src" / "swingtrade" / "alpaca_paper_account_runtime.py"
_BUDGET_SOURCE = Path(__file__).parents[2] / "src" / "swingtrade" / "alpaca_paper_request_budget.py"


def _grant(account: str | None = None) -> StandingGrant:
    return StandingGrant(
        "LANE1_ALPACA_STANDING_PAPER_ACCOUNT_READ_AUTHORIZED",
        effective=True,
        attended=True,
        expected_account_id=account,
    )


def _payload(account: str = "synthetic-account") -> bytes:
    body = {
        "id": account,
        "account_number": "PAPER0001",
        "status": "ACTIVE",
        "currency": "USD",
        "trading_blocked": False,
        "account_blocked": False,
        "trade_suspended_by_user": False,
    }
    return json.dumps(body).encode("utf-8")


def _ledger(tmp_path: Path, when: datetime = _WHEN) -> DurableRequestBudget:
    return DurableRequestBudget(tmp_path / "budget.json", lambda: when)


def _denied(operation: object, reason: str) -> AccountRuntimeError:
    with pytest.raises(AccountRuntimeError) as caught:
        operation()  # type: ignore[operator]
    error = caught.value
    assert error.reason == reason
    assert str(error) == reason
    assert _SECRET.decode() not in str(error)
    assert _SECRET.decode() not in repr(error.decision)
    for name in _FLAGS:
        assert getattr(error.decision, name) is False
    return error


def test_successful_account_response_keeps_flags_closed(tmp_path: Path) -> None:
    transport = ScriptedTransport((200, _payload()))
    decision = run_account_read(
        _grant("synthetic-account"),
        ScriptedCredentials(_KEY, _SECRET),
        transport,
        _ledger(tmp_path),
    )
    assert decision.classification is RuntimeClassification.ACCEPTED
    assert decision.reason == "ACCOUNT_READ"
    assert decision.retry_disposition == "NOT_REQUIRED"
    assert decision.safe_to_retry is False
    assert transport.calls == 1
    for name in _FLAGS:
        assert getattr(decision, name) is False
    assert "synthetic-account" not in repr(decision)
    assert _SECRET.decode() not in repr(decision)


def test_invalid_fields_and_binding_mismatch_are_refused(tmp_path: Path) -> None:
    missing = _payload()
    parsed = json.loads(missing)
    del parsed["id"]
    incomplete = json.dumps(parsed).encode("utf-8")
    ledger = _ledger(tmp_path)
    transport = ScriptedTransport((200, incomplete))
    _denied(
        lambda: run_account_read(_grant(), ScriptedCredentials(_KEY, _SECRET), transport, ledger),
        "INCOMPLETE_ACCOUNT",
    )
    mismatched = ScriptedTransport((200, _payload("other-account")))
    mismatch = _denied(
        lambda: run_account_read(
            _grant("synthetic-account"),
            ScriptedCredentials(_KEY, _SECRET),
            mismatched,
            ledger,
        ),
        "ACCOUNT_BINDING_MISMATCH",
    )
    assert "other-account" not in str(mismatch)
    assert "other-account" not in repr(mismatch.decision)
    assert transport.calls == 1
    assert mismatched.calls == 1


def test_http_statuses_redirects_tls_and_timeouts(tmp_path: Path) -> None:
    cases = (
        (ScriptedTransport((401, _SECRET)), "HTTP_401", "NOT_RETRYABLE"),
        (ScriptedTransport((403, _SECRET)), "HTTP_403", "NOT_RETRYABLE"),
        (ScriptedTransport((429, _SECRET)), "HTTP_429", "SAME_HOST_ELIGIBLE"),
        (ScriptedTransport((503, _SECRET)), "HTTP_5XX", "SAME_HOST_ELIGIBLE"),
        (ScriptedTransport((200, _payload()), redirected=True), "REDIRECT_DENIED", "NOT_RETRYABLE"),
        (ScriptedTransport(fault="tls"), "TLS_FAILED", "NOT_RETRYABLE"),
        (ScriptedTransport(fault="timeout"), "TIMEOUT", "NOT_RETRYABLE"),
    )
    for transport, reason, disposition in cases:
        error = _denied(
            lambda current=transport: run_account_read(
                _grant(),
                ScriptedCredentials(_KEY, _SECRET),
                current,
                _ledger(tmp_path),
            ),
            reason,
        )
        assert error.decision.retry_disposition == disposition
        assert error.decision.safe_to_retry is False
        assert transport.calls == 1


def test_wrong_host_order_route_and_live_target_do_not_exchange(tmp_path: Path) -> None:
    transport = ScriptedTransport((200, _payload()))
    live = f"https://{LIVE_HOST}/v2/account"
    orders = f"https://{PAPER_HOST}/v2/orders"
    ledger = _ledger(tmp_path)
    _denied(
        lambda: run_account_read(
            _grant(),
            ScriptedCredentials(_KEY, _SECRET),
            transport,
            ledger,
            url=live,
        ),
        "LIVE_HOST_DENIED",
    )
    _denied(
        lambda: run_account_read(
            _grant(),
            ScriptedCredentials(_KEY, _SECRET),
            transport,
            ledger,
            url=orders,
        ),
        "ORDER_ROUTE_DENIED",
    )
    assert transport.calls == 0
    assert not (tmp_path / "budget.json").exists()
    boundary = evaluate_paper_boundary(ACCOUNT_URL, "GET")
    assert boundary.network_permitted is False
    offline = AccountReadDecision(ReadClassification.ACCEPTED, "ACCOUNT_READ")
    assert offline.connect_allowed is False
    assert offline.safe_to_retry is False


def test_budget_exhaustion_does_not_exchange(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    for _ in range(DAILY_LIMIT):
        ledger.reserve()
    transport = ScriptedTransport((200, _payload()))
    _denied(
        lambda: run_account_read(_grant(), ScriptedCredentials(_KEY, _SECRET), transport, ledger),
        "BUDGET_EXHAUSTED",
    )
    assert transport.calls == 0
    assert ledger.spent() == DAILY_LIMIT


def test_credential_and_runtime_refusal_have_no_side_effect(tmp_path: Path) -> None:
    calls = {"n": 0}

    class _Tracking:
        def load(self) -> tuple[bytes, bytes]:
            calls["n"] += 1
            return _KEY, _SECRET

        def exchange(
            self,
            method: str,
            url: str,
            material: tuple[bytes, bytes],
        ) -> tuple[int, bytes, bool]:
            del method, url, material
            calls["n"] += 1
            return 200, _payload(), False

    tracker = _Tracking()
    ledger = _ledger(tmp_path)
    _denied(lambda: run_account_read(inactive_grant(), tracker, tracker, ledger), "GRANT_INACTIVE")
    _denied(read_paper_account, "GRANT_INACTIVE")
    unavailable = ScriptedTransport((200, _payload()))
    _denied(
        lambda: run_account_read(
            _grant(),
            ScriptedCredentials(None, None),
            unavailable,
            ledger,
        ),
        "CREDENTIAL_UNAVAILABLE",
    )
    assert calls["n"] == 0
    assert unavailable.calls == 0
    assert not (tmp_path / "budget.json").exists()


def test_native_paths_stay_closed_without_a_grant(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = __import__(
        "swingtrade.alpaca_paper_account_runtime",
        fromlist=["alpaca_paper_account_runtime"],
    )
    assert runtime._IO_ATTEMPTS == 0

    def _boom(*args: object, **kwargs: object) -> tuple[int, bytes, bool]:
        del args, kwargs
        raise AssertionError("native opener called")

    monkeypatch.setattr(runtime, "_default_opener", _boom)
    monkeypatch.setattr(runtime, "_cred_read_target", _boom)
    _denied(
        lambda: PaperGetTransport(inactive_grant()).exchange("GET", ACCOUNT_URL, (_KEY, _SECRET)),
        "GRANT_INACTIVE",
    )
    reader_calls = {"n": 0}

    def _reader() -> tuple[bytes, bytes]:
        reader_calls["n"] += 1
        return _KEY, _SECRET

    _denied(
        lambda: WindowsPaperCredentialAdapter(inactive_grant(), _reader).load(), "GRANT_INACTIVE"
    )
    assert reader_calls["n"] == 0
    loaded = WindowsPaperCredentialAdapter(_grant(), _reader).load()
    assert loaded == (_KEY, _SECRET)
    assert reader_calls["n"] == 1
    assert runtime._IO_ATTEMPTS == 0
    refusal = RedirectRefusal()
    _denied(
        lambda: refusal.redirect_request(None, None, 302, "", EmailMessage(), "https://x"),
        "REDIRECT_DENIED",
    )
    context = verified_tls_context()
    assert context.check_hostname is True
    assert context.verify_mode == ssl.CERT_REQUIRED
    weakened = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    weakened.check_hostname = False
    weakened.verify_mode = ssl.CERT_NONE
    _denied(lambda: require_verified_context(weakened), "TLS_POLICY_DENIED")


def test_injected_opener_reads_only_the_account_endpoint() -> None:
    seen: dict[str, object] = {}

    class _Response:
        status = 200

        def read(self, limit: int) -> bytes:
            assert limit == MAX_BODY + 1
            return _payload()

        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *args: object) -> bool:
            del args
            return False

    class _Opener:
        def open(self, request: urllib.request.Request, timeout: float) -> _Response:
            seen["url"] = request.full_url
            seen["method"] = request.get_method()
            seen["timeout"] = timeout
            seen["key"] = request.get_header("Apca-api-key-id")
            return _Response()

    transport = PaperGetTransport(_grant(), opener_factory=lambda: _Opener())  # type: ignore[arg-type]
    status, body, redirected = transport.exchange("GET", ACCOUNT_URL, (_KEY, _SECRET))
    assert status == 200
    assert redirected is False
    assert body == _payload()
    assert seen == {
        "url": ACCOUNT_URL,
        "method": "GET",
        "timeout": 10.0,
        "key": _KEY.decode(),
    }

    class _Denied:
        def open(self, request: urllib.request.Request, timeout: float) -> object:
            del request, timeout
            raise urllib.error.HTTPError(
                ACCOUNT_URL,
                401,
                "denied",
                EmailMessage(),
                io.BytesIO(_SECRET),
            )

    denied = PaperGetTransport(_grant(), opener_factory=lambda: _Denied())  # type: ignore[arg-type]
    code, payload, followed = denied.exchange("GET", ACCOUNT_URL, (_KEY, _SECRET))
    assert code == 401
    assert followed is False
    assert payload == _SECRET


def test_runtime_source_has_no_forbidden_token_or_retry_loop() -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    budget = _BUDGET_SOURCE.read_text(encoding="utf-8")
    lowered = (source + budget).lower()
    for token in ("requests.", "httpx.", "socket.", "tradestation", "place_order", "cancel_order"):
        assert token not in lowered
    assert "environ" not in lowered
    assert PAPER_KEY_ID_TARGET
    assert PAPER_SECRET_TARGET
    function = ast.parse(__import__("inspect").getsource(run_account_read)).body[0]
    assert isinstance(function, ast.FunctionDef)
    assert not any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(function))
