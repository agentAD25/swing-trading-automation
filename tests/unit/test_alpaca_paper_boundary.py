"""Negative checks for the offline Alpaca Paper boundary classifier."""

from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path

import pytest

from swingtrade.alpaca_paper_boundary import (
    BROKER_HOST,
    BROKER_SANDBOX_HOST,
    DATA_HOST,
    LIVE_HOST,
    PAPER_HOST,
    BoundaryClassification,
    BoundaryDecision,
    evaluate_paper_boundary,
)

_ACCOUNT = "https://paper-api.alpaca.markets/v2/account"
_ORDERS = "https://paper-api.alpaca.markets/v2/orders"
_ONE_ORDER = "https://paper-api.alpaca.markets/v2/orders/ord1"
_MODULE = Path(__file__).parents[2] / "src" / "swingtrade" / "alpaca_paper_boundary.py"
_ITEM24_SOURCE = Path(__file__).parents[2] / "src" / "swingtrade" / "alpaca_paper.py"
_ITEM24_TESTS = Path(__file__).parents[2] / "tests" / "unit" / "test_alpaca_paper.py"
_SCAN_TOKENS = ("requests.", "httpx.", "socket.", "tradestation", "place_order", "cancel_order")


def _closed(decision: BoundaryDecision) -> None:
    assert decision.connect_allowed is False
    assert decision.network_permitted is False
    assert decision.submit_permitted is False
    assert decision.cancel_permitted is False
    assert decision.replace_permitted is False
    assert decision.resubmit_permitted is False
    assert decision.safe_to_retry is False


def _denied(target: object, method: object, reason: str) -> BoundaryDecision:
    decision = evaluate_paper_boundary(target, method)
    assert decision.classification is BoundaryClassification.DENIED
    assert decision.reason == reason
    _closed(decision)
    return decision


def _blob(path: Path) -> str:
    payload = path.read_bytes()
    prefix = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(prefix + payload).hexdigest()


def test_exact_paper_hostname_allows_only_the_hypothetical_read() -> None:
    decision = evaluate_paper_boundary(_ACCOUNT, "GET")
    assert decision.classification is BoundaryClassification.PAPER_POLICY_CANDIDATE
    assert decision.reason == "CLASSIFIED"
    assert PAPER_HOST == "paper-api.alpaca.markets"
    positions = evaluate_paper_boundary("https://paper-api.alpaca.markets/v2/positions", "GET")
    one = evaluate_paper_boundary(_ONE_ORDER, "GET")
    orders = evaluate_paper_boundary(_ORDERS, "GET")
    assert positions.classification is BoundaryClassification.PAPER_POLICY_CANDIDATE
    assert one.classification is BoundaryClassification.PAPER_POLICY_CANDIDATE
    assert orders.classification is BoundaryClassification.PAPER_POLICY_CANDIDATE


def test_candidate_result_stays_non_executing() -> None:
    decision = evaluate_paper_boundary(_ACCOUNT, "GET")
    _closed(decision)
    assert decision.classification is BoundaryClassification.PAPER_POLICY_CANDIDATE


def test_live_trading_host_is_denied() -> None:
    assert LIVE_HOST == "api.alpaca.markets"
    _denied("https://api.alpaca.markets/v2/account", "GET", "LIVE_HOST_DENIED")


def test_market_data_host_is_denied() -> None:
    assert DATA_HOST == "data.alpaca.markets"
    _denied("https://data.alpaca.markets/v2/account", "GET", "DATA_HOST_DENIED")


def test_broker_api_host_is_denied() -> None:
    assert BROKER_HOST == "broker-api.alpaca.markets"
    _denied("https://broker-api.alpaca.markets/v2/account", "GET", "BROKER_HOST_DENIED")


def test_broker_sandbox_host_is_denied() -> None:
    assert BROKER_SANDBOX_HOST == "broker-api.sandbox.alpaca.markets"
    _denied(
        "https://broker-api.sandbox.alpaca.markets/v2/account",
        "GET",
        "BROKER_SANDBOX_DENIED",
    )


def test_arbitrary_hostname_is_denied() -> None:
    _denied("https://example.com/v2/account", "GET", "HOST_DENIED")
    _denied("https://localhost/v2/account", "GET", "HOST_DENIED")
    _denied("https://paper-api.alpaca.markets.evil.example/v2/account", "GET", "HOST_DENIED")


def test_lookalike_domain_is_denied() -> None:
    _denied("https://paper-api.alpaca.market/v2/account", "GET", "HOST_DENIED")
    _denied("https://notpaper-api.alpaca.markets/v2/account", "GET", "HOST_DENIED")
    _denied("https://paper-api.alpaca.markets./v2/account", "GET", "HOST_DENIED")
    _denied("https://foo.paper-api.alpaca.markets/v2/account", "GET", "HOST_DENIED")


def test_http_scheme_is_denied() -> None:
    _denied("http://paper-api.alpaca.markets/v2/account", "GET", "SCHEME_DENIED")
    _denied("HTTPS://paper-api.alpaca.markets/v2/account", "GET", "SCHEME_DENIED")


def test_ip_literal_is_denied() -> None:
    _denied("https://127.0.0.1/v2/account", "GET", "ADDRESS_LITERAL_DENIED")
    _denied("https://10.1.2.3/v2/account", "GET", "ADDRESS_LITERAL_DENIED")
    _denied("https://[::1]/v2/account", "GET", "ADDRESS_LITERAL_DENIED")


def test_userinfo_is_denied() -> None:
    _denied(
        "https://user:secret@paper-api.alpaca.markets/v2/account",
        "GET",
        "USERINFO_DENIED",
    )
    _denied(
        "https://paper-api.alpaca.markets@evil.example/v2/account",
        "GET",
        "USERINFO_DENIED",
    )


def test_non_default_port_is_denied() -> None:
    _denied("https://paper-api.alpaca.markets:444/v2/account", "GET", "PORT_DENIED")
    _denied("https://paper-api.alpaca.markets:443/v2/account", "GET", "PORT_DENIED")
    _denied("https://api.alpaca.markets:443/v2/account", "GET", "PORT_DENIED")


def test_malformed_url_is_denied() -> None:
    for target in ("", "paper-api.alpaca.markets/v2/account", "https://", "https:///v2/account"):
        _denied(target, "GET", "MALFORMED_TARGET")
    _denied(None, "GET", "MALFORMED_TARGET")
    _denied(_ACCOUNT + " ", "GET", "MALFORMED_TARGET")
    _denied("https://paper-api.alpaca.markets/v2/account#frag", "GET", "FRAGMENT_DENIED")


def test_query_manipulation_is_denied() -> None:
    _denied(_ACCOUNT + "?next=https://api.alpaca.markets", "GET", "QUERY_DENIED")
    _denied(_ACCOUNT + "?", "GET", "QUERY_DENIED")


def test_redirect_target_is_denied() -> None:
    parameters = inspect.signature(evaluate_paper_boundary).parameters
    assert "follow_redirects" not in parameters
    assert "allow_redirects" not in parameters
    _denied("https://attacker.example/v2/account", "GET", "HOST_DENIED")
    pair = ("https://paper-api.alpaca.markets/v2/account", "https://attacker.example")
    _denied(pair, "GET", "MALFORMED_TARGET")


def test_proxy_or_endpoint_override_is_rejected() -> None:
    signature = inspect.signature(evaluate_paper_boundary)
    assert tuple(signature.parameters) == ("target", "method")
    assert "proxy" not in signature.parameters
    assert "base_url" not in signature.parameters
    for parameter in signature.parameters.values():
        assert parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        assert parameter.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        evaluate_paper_boundary(_ACCOUNT, "GET", proxy="http://127.0.0.1:9")  # type: ignore[call-arg]


def test_tls_disable_configuration_is_rejected() -> None:
    signature = inspect.signature(evaluate_paper_boundary)
    assert "verify" not in signature.parameters
    assert "tls_verify" not in signature.parameters
    with pytest.raises(TypeError):
        evaluate_paper_boundary(_ACCOUNT, "GET", verify=False)  # type: ignore[call-arg]


def test_post_is_denied() -> None:
    _denied(_ACCOUNT, "POST", "METHOD_DENIED")


def test_put_is_denied() -> None:
    _denied(_ACCOUNT, "PUT", "METHOD_DENIED")


def test_patch_is_denied() -> None:
    _denied(_ACCOUNT, "PATCH", "METHOD_DENIED")


def test_delete_is_denied() -> None:
    _denied(_ACCOUNT, "DELETE", "METHOD_DENIED")


def test_order_creation_route_is_denied() -> None:
    _denied(_ORDERS, "POST", "METHOD_DENIED")
    _denied(_ORDERS + "/", "GET", "PATH_DENIED")


def test_cancellation_route_is_denied() -> None:
    _denied(_ONE_ORDER, "DELETE", "METHOD_DENIED")


def test_replacement_route_is_denied() -> None:
    _denied(_ONE_ORDER, "PATCH", "METHOD_DENIED")
    _denied(_ONE_ORDER, "PUT", "METHOD_DENIED")


def test_unknown_route_is_denied() -> None:
    _denied("https://paper-api.alpaca.markets/v2/clock", "GET", "PATH_DENIED")
    _denied("https://paper-api.alpaca.markets/v2/account/activities", "GET", "PATH_DENIED")
    _denied("https://paper-api.alpaca.markets/v2/orders/ord1/extra", "GET", "PATH_DENIED")
    _denied("https://paper-api.alpaca.markets/v2/orders/..", "GET", "PATH_DENIED")


def test_encoded_path_bypass_is_denied() -> None:
    _denied(
        "https://paper-api.alpaca.markets/v2/account/%2e%2e/v2/orders",
        "GET",
        "ENCODED_PATH_DENIED",
    )
    _denied("https://paper-api.alpaca.markets/v2/%61ccount", "GET", "ENCODED_PATH_DENIED")
    _denied(
        "https://paper-api.alpaca.markets/v2/orders/%2e%2e/account",
        "GET",
        "ENCODED_PATH_DENIED",
    )


def test_module_has_no_network_client_or_socket_import() -> None:
    source = _MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".", 1)[0])
    assert imported.isdisjoint(
        {"socket", "requests", "httpx", "urllib", "alpaca", "os", "subprocess"}
    )
    lowered = source.lower()
    for token in _SCAN_TOKENS:
        assert token not in lowered


def test_module_has_no_credential_or_environment_access() -> None:
    source = _MODULE.read_text(encoding="utf-8").lower()
    for token in ("getenv", "environ", "apca_api", "http_proxy", "https_proxy", "credential"):
        assert token not in source
    parameters = inspect.signature(evaluate_paper_boundary).parameters
    assert set(parameters).isdisjoint({"key", "secret", "token", "api_key", "api_secret"})
    with pytest.raises(TypeError):
        evaluate_paper_boundary(_ACCOUNT, "GET", token="synthetic")  # type: ignore[call-arg]


def test_module_has_no_provider_request_or_order_intent() -> None:
    source = _MODULE.read_text(encoding="utf-8").lower()
    for token in ("orderintent", "quantity", "order_class", "risk_limit", "base_url"):
        assert token not in source
    decision = evaluate_paper_boundary(_ACCOUNT, "GET")
    assert type(decision) is BoundaryDecision
    assert not hasattr(decision, "order")


def test_repeated_evaluation_is_deterministic() -> None:
    target = _ACCOUNT
    method = "GET"
    first = evaluate_paper_boundary(target, method)
    second = evaluate_paper_boundary(target, method)
    assert first == second
    assert target == _ACCOUNT
    assert method == "GET"
    denied = _denied(_ACCOUNT, "POST", "METHOD_DENIED")
    assert denied == evaluate_paper_boundary(_ACCOUNT, "POST")


def test_item24_blobs_stay_unchanged() -> None:
    assert _blob(_ITEM24_SOURCE) == "4342e4bcad80eb823aa8a377447205f43f6eda6f"
    assert _blob(_ITEM24_TESTS) == "d30bae879028b6683100d670b3a15f8f0f70a587"


def test_lowercase_method_and_blank_method_fail_closed() -> None:
    _denied(_ACCOUNT, "get", "METHOD_DENIED")
    _denied(_ACCOUNT, "", "MALFORMED_METHOD")
    _denied(_ACCOUNT, None, "MALFORMED_METHOD")
