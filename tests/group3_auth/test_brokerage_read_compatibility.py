"""Offline fixtures for the 2026-10-10 read-only parser gaps. No network."""

from __future__ import annotations

from swingtrade.group3_auth.boundary import ExecutionPosture, evaluate_destination
from swingtrade.group3_auth.brokerage_read import ReadKind, parse_brokerage_fixture
from swingtrade.group3_auth.outcomes import OutcomeCode
from swingtrade.group3_auth.scopes import validate_granted_scopes
from swingtrade.group3_auth.throttle import LoginThrottle, retry_permitted

_ACCOUNT = "SYN_READ_ONE"
_ORDER = "ORD_SYN_1"
_OTHER = "ORD_SYN_2"


def _order(**extra: object) -> dict[str, object]:
    body: dict[str, object] = {"AccountID": _ACCOUNT, "OrderID": _ORDER, "Status": "OPN"}
    body.update(extra)
    return body


def test_spread_string_is_read_only_and_wrong_types_fail() -> None:
    accepted = parse_brokerage_fixture(
        ReadKind.ORDERS,
        {"Orders": [_order(Spread="Vertical")]},
        status=200,
    )
    assert accepted.decision.reason == "READ_FIXTURE"
    assert accepted.connect_allowed is False
    assert accepted.network_permitted is False
    assert "Vertical" not in repr(accepted)
    absent = parse_brokerage_fixture(ReadKind.ORDERS, {"Orders": [_order()]}, status=200)
    assert absent.decision.reason == "READ_FIXTURE"
    blank = parse_brokerage_fixture(
        ReadKind.ORDERS,
        {"Orders": [_order(Spread=None)]},
        status=200,
    )
    assert blank.decision.reason == "READ_FIXTURE"
    for value in ({"Delta": "1"}, ["Vertical"], 1):
        rejected = parse_brokerage_fixture(
            ReadKind.ORDERS,
            {"Orders": [_order(Spread=value)]},
            status=200,
        )
        assert rejected.decision.reason == "MALFORMED_RESPONSE"
        assert rejected.decision.safe_to_retry is False


def test_null_blank_strings_are_not_quantities_and_identities_fail() -> None:
    present = parse_brokerage_fixture(
        ReadKind.BALANCES,
        {"Balances": [{"AccountID": _ACCOUNT, "CashBalance": "1.00", "Equity": "2.00"}]},
        status=200,
    )
    assert present.decision.reason == "READ_FIXTURE"
    omitted = parse_brokerage_fixture(
        ReadKind.BALANCES,
        {"Balances": [{"AccountID": _ACCOUNT, "CashBalance": "1.00"}]},
        status=200,
    )
    assert omitted.decision.reason == "READ_FIXTURE"
    alias = parse_brokerage_fixture(
        ReadKind.ACCOUNTS,
        {"Accounts": [{"AccountID": _ACCOUNT, "Alias": None, "Status": "Active"}]},
        status=200,
    )
    assert alias.decision.reason == "READ_FIXTURE"
    assert "0" not in repr(alias)
    quantity = parse_brokerage_fixture(
        ReadKind.POSITIONS,
        {"Positions": [{"PositionID": "POS_SYN_1", "AccountID": _ACCOUNT, "Quantity": None}]},
        status=200,
    )
    assert quantity.decision.reason == "NULL_ECONOMIC_FIELD"
    assert quantity.decision.safe_to_retry is False
    missing_id = parse_brokerage_fixture(
        ReadKind.ORDERS,
        {"Orders": [{"AccountID": _ACCOUNT, "Status": "OPN"}]},
        status=200,
    )
    assert missing_id.decision.reason == "MALFORMED_IDENTITY"
    null_id = parse_brokerage_fixture(
        ReadKind.ORDERS,
        {"Orders": [{"AccountID": None, "OrderID": _ORDER}]},
        status=200,
    )
    assert null_id.decision.reason == "MALFORMED_ACCOUNT"
    wrong = parse_brokerage_fixture(
        ReadKind.ORDERS,
        {"Orders": [_order(LimitPrice=1)]},
        status=200,
    )
    assert wrong.decision.reason == "MALFORMED_RESPONSE"
    conflict = parse_brokerage_fixture(
        ReadKind.ORDERS,
        {
            "Orders": [
                _order(Status="OPN"),
                {"AccountID": _ACCOUNT, "OrderID": _ORDER, "Status": "FLL"},
            ]
        },
        status=200,
    )
    assert conflict.decision.reason == "CONFLICTING_RESPONSE"


def test_http_400_and_404_are_specific_and_not_retried() -> None:
    secret = "SYN_SHOULD_NOT_RENDER"
    cases = (
        (400, "HTTP_400"),
        (401, "HTTP_401"),
        (403, "HTTP_403"),
        (404, "HTTP_404"),
        (429, "HTTP_429"),
        (503, "HTTP_5XX"),
        (504, "HTTP_5XX"),
    )
    for status, reason in cases:
        observed = parse_brokerage_fixture(
            ReadKind.ACCOUNTS,
            {"Error": "Bad", "Message": secret, "AccountID": secret},
            status=status,
        )
        assert observed.decision.reason == reason
        assert observed.decision.code is OutcomeCode.REJECTED
        assert observed.decision.safe_to_retry is False
        assert observed.connect_allowed is False
        assert secret not in repr(observed)
    timeout = parse_brokerage_fixture(
        ReadKind.ACCOUNTS,
        {"not": "json"},
        status=200,
        timeout=True,
    )
    assert timeout.decision.reason == "NETWORK_TIMEOUT"
    assert timeout.decision.safe_to_retry is False
    stopped = LoginThrottle("LOGIN_PARSER").observe(status=400, headers=None)
    assert stopped.action == "CONTINUE"
    assert retry_permitted(stopped) is False


def test_order_by_id_error_keeps_opaque_order_id() -> None:
    partial = parse_brokerage_fixture(
        ReadKind.ORDERS_BY_ID,
        {
            "Orders": [_order()],
            "Errors": [
                {"AccountID": _ACCOUNT, "OrderID": _OTHER, "Error": "Error", "Message": "x"}
            ],
        },
        status=200,
    )
    assert partial.decision.reason == "PARTIAL_RESPONSE"
    assert partial.decision.safe_to_retry is False
    assert _OTHER not in repr(partial)
    assert partial.connect_allowed is False
    missing = parse_brokerage_fixture(
        ReadKind.ORDERS_BY_ID,
        {"Orders": [], "Errors": [{"AccountID": _ACCOUNT, "Error": "Error", "Message": "x"}]},
        status=200,
    )
    assert missing.decision.reason == "PARTIAL_RESPONSE"
    invalid = parse_brokerage_fixture(
        ReadKind.ORDERS_BY_ID,
        {"Orders": [], "Errors": [{"OrderID": 12, "Error": "Error", "Message": "x"}]},
        status=200,
    )
    assert invalid.decision.reason == "MALFORMED_RESPONSE"
    null_order = parse_brokerage_fixture(
        ReadKind.ORDERS_BY_ID,
        {"Orders": [], "Errors": [{"OrderID": None, "Error": "Error", "Message": "x"}]},
        status=200,
    )
    assert null_order.decision.reason == "MALFORMED_IDENTITY"
    extra = parse_brokerage_fixture(
        ReadKind.ORDERS_BY_ID,
        {"Orders": [], "Errors": [{"OrderID": _OTHER, "Strategy": "send"}]},
        status=200,
    )
    assert extra.decision.reason == "UNDOCUMENTED_FIELD"
    assert "send" not in repr(extra)
    conflict = parse_brokerage_fixture(
        ReadKind.ORDERS_BY_ID,
        {
            "Orders": [],
            "Errors": [
                {"OrderID": _OTHER, "Message": "one"},
                {"OrderID": _OTHER, "Message": "two"},
            ],
        },
        status=200,
    )
    assert conflict.decision.reason == "CONFLICTING_RESPONSE"
    listed = parse_brokerage_fixture(
        ReadKind.ORDERS,
        {
            "Orders": [],
            "Errors": [{"AccountID": _ACCOUNT, "OrderID": _OTHER, "Error": "E", "Message": "m"}],
        },
        status=200,
    )
    assert listed.decision.reason == "UNDOCUMENTED_FIELD"


def test_parser_remediation_does_not_open_a_broker_path() -> None:
    live = evaluate_destination(
        ExecutionPosture.DRY_RUN,
        "https://api.tradestation.com/v3/brokerage/accounts",
    )
    assert live.decision.reason == "LIVE_HOST_PROHIBITED"
    sim = evaluate_destination(
        ExecutionPosture.DRY_RUN,
        "https://sim-api.tradestation.com/v3/brokerage/accounts",
    )
    assert sim.decision.reason == "SIM_CONNECT_DENIED"
    assert sim.connect_allowed is False
    auth = evaluate_destination(
        ExecutionPosture.DRY_RUN,
        "https://signin.tradestation.com/oauth/token",
        method="POST",
    )
    assert auth.decision.reason == "AUTH_ENDPOINT_CONNECT_DENIED"
    redirected = evaluate_destination(
        ExecutionPosture.DRY_RUN,
        "https://sim-api.tradestation.com/v3/brokerage/accounts",
        redirect_to="https://api.tradestation.com/v3/brokerage/accounts",
    )
    assert redirected.decision.reason == "LIVE_HOST_PROHIBITED"
    scope = validate_granted_scopes("openid ReadAccount Trade")
    assert scope.decision.reason == "UNEXPECTED_SCOPE_GRANTED"
    order = evaluate_destination(
        ExecutionPosture.DRY_RUN,
        "https://sim-api.tradestation.com/v3/orderexecution/orders",
        method="POST",
    )
    assert order.decision.reason == "ORDER_PLACEMENT_DENIED"
