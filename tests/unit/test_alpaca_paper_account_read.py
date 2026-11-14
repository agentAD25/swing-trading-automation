"""Offline checks for the paper account read."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

from swingtrade.alpaca_paper_account_read import (
    ACCOUNT_URL,
    AccountReadError,
    ReadClassification,
    ReadSession,
    ScriptedExchange,
    SyntheticCredentials,
    SyntheticTransport,
    perform_paper_get,
    read_account,
    retrieve_paper_credentials,
)
from swingtrade.alpaca_paper_boundary import LIVE_HOST, PAPER_HOST
from swingtrade.alpaca_paper_custody import PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET

_KEY = b"synthetic-paper-key-id"
_SECRET = b"synthetic-paper-secret"
_MODULE = Path(__file__).parents[2] / "src" / "swingtrade" / "alpaca_paper_account_read.py"
_FLAGS = (
    "connect_allowed",
    "network_permitted",
    "submit_permitted",
    "cancel_permitted",
    "replace_permitted",
    "resubmit_permitted",
    "safe_to_retry",
)
_SCAN = ("requests.", "httpx.", "socket.", "tradestation", "place_order", "cancel_order")


def _body() -> dict[str, object]:
    return {
        "id": "synthetic-account",
        "account_number": "PAPER0001",
        "status": "ACTIVE",
        "currency": "USD",
        "trading_blocked": False,
        "account_blocked": False,
        "trade_suspended_by_user": False,
        "buying_power": "0",
    }


def _papers() -> dict[str, bytes]:
    return {PAPER_KEY_ID_TARGET: _KEY, PAPER_SECRET_TARGET: _SECRET}


def _ready(
    *,
    entries: object = None,
    fault: object = None,
    exchange: ScriptedExchange | None = None,
    method: object = "GET",
    url: object = ACCOUNT_URL,
) -> tuple[ReadSession, SyntheticCredentials, SyntheticTransport]:
    credentials = SyntheticCredentials(_papers() if entries is None else entries, fault=fault)
    transport = SyntheticTransport(exchange or ScriptedExchange(body=_body()))
    return ReadSession(), credentials, transport


def _denied(operation: object, reason: str) -> AccountReadError:
    with pytest.raises(AccountReadError) as caught:
        operation()  # type: ignore[operator]
    error = caught.value
    assert error.reason == reason
    assert str(error) == reason
    assert error.decision.classification is ReadClassification.DENIED
    for name in _FLAGS:
        assert getattr(error.decision, name) is False
    return error


def test_valid_account_response_keeps_flags_closed() -> None:
    session, credentials, transport = _ready()
    decision = read_account(session, credentials, transport)
    assert decision.classification is ReadClassification.ACCEPTED
    assert decision.reason == "ACCOUNT_READ"
    assert transport.calls == 1
    for name in _FLAGS:
        assert getattr(decision, name) is False
    rendered = " ".join((repr(decision), str(decision), repr(credentials), repr(transport)))
    assert "synthetic-account" not in rendered
    assert _SECRET.decode() not in rendered


def test_http_errors_and_malformed_bodies_are_terminal() -> None:
    cases = (
        (ScriptedExchange(status=401, body=_body()), "HTTP_ERROR"),
        (ScriptedExchange(status=500, body=_body()), "HTTP_ERROR"),
        (ScriptedExchange(status=200), "MISSING_BODY"),
        (ScriptedExchange(status=200, body=None), "NULL_BODY"),
        (ScriptedExchange(status=200, body="not-json"), "MALFORMED_BODY"),
        (ScriptedExchange(status=200, body={**_body(), "extra": "x"}), "UNRECOGNIZED_FIELD"),
        (
            ScriptedExchange(status=200, body={**_body(), "status": "PAPER_ONLY"}),
            "UNSUPPORTED_STATUS",
        ),
        (
            ScriptedExchange(
                status=200, body={key: value for key, value in _body().items() if key != "id"}
            ),
            "INCOMPLETE_ACCOUNT",
        ),
        (ScriptedExchange(status=200, body={**_body(), "currency": "EUR"}), "UNSUPPORTED_CURRENCY"),
        (
            ScriptedExchange(status=200, body={**_body(), "trading_blocked": "false"}),
            "MALFORMED_PRECONDITION",
        ),
    )
    for exchange, reason in cases:
        ready = _ready(exchange=exchange)
        _denied(lambda current=ready: read_account(*current), reason)
        assert ready[2].calls == 1
        _denied(lambda current=ready: read_account(*current), "RETRY_DENIED")
        assert ready[2].calls == 1


def test_wrong_method_route_and_live_host_are_refused() -> None:
    live = f"https://{LIVE_HOST}/v2/account"
    orders = f"https://{PAPER_HOST}/v2/orders"
    ready = _ready(url=live)
    _denied(
        lambda current=ready, target=live: read_account(*current, url=target), "LIVE_HOST_DENIED"
    )
    posted = _ready(method="POST")
    _denied(lambda current=posted: read_account(*current, method="POST"), "METHOD_DENIED")
    routed = _ready(url=orders)
    _denied(
        lambda current=routed, target=orders: read_account(*current, url=target),
        "ORDER_ROUTE_DENIED",
    )
    assert ready[2].calls == 0
    assert posted[2].calls == 0


def test_custody_network_redirect_and_timeout_do_not_retry() -> None:
    missing = _ready(entries={PAPER_SECRET_TARGET: _SECRET})
    _denied(lambda current=missing: read_account(*current), "MISSING_KEY_ID")
    live = _ready(entries={"swing-trading/lane2/alpaca/live/key-id": _KEY})
    _denied(lambda current=live: read_account(*current), "LIVE_TARGET_DENIED")
    fallback = _ready(fault="env-fallback")
    _denied(lambda current=fallback: read_account(*current), "ENV_FALLBACK_DENIED")
    assert missing[2].calls == 0
    redirected = _ready(exchange=ScriptedExchange(status=302, redirected=True, body=_body()))
    _denied(lambda current=redirected: read_account(*current), "REDIRECT_DENIED")
    assert redirected[2].calls == 1
    _denied(lambda current=redirected: read_account(*current), "RETRY_DENIED")
    timed = _ready(exchange=ScriptedExchange(fault="timeout", body=_body()))
    _denied(lambda current=timed: read_account(*current), "TIMEOUT")
    failed = _ready(exchange=ScriptedExchange(fault="network", body=_body()))
    _denied(lambda current=failed: read_account(*current), "NETWORK_DENIED")
    crashed = _ready(exchange=ScriptedExchange(fault="exception", body=_body()))
    _denied(lambda current=crashed: read_account(*current), "TRANSPORT_EXCEPTION")
    assert timed[2].calls == 1
    assert crashed[2].calls == 1
    timeout = _denied(lambda current=timed: read_account(*current), "RETRY_DENIED")
    assert timeout.decision.safe_to_retry is False


def test_import_does_not_retrieve_or_request() -> None:
    module = importlib.import_module("swingtrade.alpaca_paper_account_read")
    assert module.retrieve_paper_credentials is retrieve_paper_credentials
    _denied(retrieve_paper_credentials, "RUNTIME_UNAUTHORIZED")
    _denied(perform_paper_get, "RUNTIME_UNAUTHORIZED")
    source = _MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".", 1)[0])
    assert imported == {"__future__", "enum", "swingtrade"}
    lowered = source.lower()
    for token in ("getenv", "environ", "urllib", "ctypes", "advapi32", "winreg", "logging"):
        assert token not in lowered
    for token in _SCAN:
        assert token not in lowered
    function = ast.parse(__import__("inspect").getsource(read_account)).body[0]
    assert isinstance(function, ast.FunctionDef)
    assert not any(isinstance(node, (ast.While, ast.For)) for node in ast.walk(function))
