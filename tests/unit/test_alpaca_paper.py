"""Synthetic Alpaca Paper fixtures. No broker, credential, network, or order action."""

from __future__ import annotations

import ast
import copy
import subprocess
from decimal import Decimal
from pathlib import Path

from swingtrade.alpaca_paper import (
    LIVE_HOST,
    PAPER_HOST,
    HostDenial,
    PaperClassification,
    PaperEvidence,
    deny_host,
    evaluate_paper_fixtures,
)
from swingtrade.group3_auth.brokerage_read import ReadKind, parse_brokerage_fixture
from swingtrade.group3_auth.order_report import classify_report

_CLIENT = "client-synth-1"
_BROKER = "broker-synth-1"
_PARSER = "ecbf5a0d06c6db3c839407df341ee407eac05dcf"
_CLASSIFIER = "7ddf267e707d0c7aabe7106eebfc24d090ed6648"


def _order(
    status: object = "new",
    client_order_id: object = _CLIENT,
    qty: object = "10",
    **extra: object,
) -> dict[str, object]:
    body: dict[str, object] = {"status": status, "qty": qty}
    if client_order_id is not None:
        body["client_order_id"] = client_order_id
    body.update(extra)
    return body


def _flags(result: PaperEvidence | HostDenial) -> None:
    assert result.connect_allowed is False
    assert result.network_permitted is False
    assert result.submit_permitted is False
    assert result.cancel_permitted is False
    assert result.resubmit_permitted is False
    assert result.safe_to_retry is False


def _one(fixtures: object) -> PaperEvidence:
    found = evaluate_paper_fixtures(fixtures)
    assert len(found) == 1
    return found[0]


def test_valid_synthetic_observation_stays_closed() -> None:
    result = _one([_order()])
    assert result == PaperEvidence(
        PaperClassification.OBSERVED,
        "CLASSIFIED",
        client_order_id=_CLIENT,
        status="new",
        qty=Decimal("10"),
    )
    assert result.generated_client_order_id is None
    _flags(result)
    assert _CLIENT not in repr(result)
    assert "10" not in repr(result)


def test_missing_client_order_id_is_not_replaced_by_broker_id() -> None:
    result = _one([_order(client_order_id=None, id=_BROKER)])
    assert result.classification is PaperClassification.REJECTED
    assert result.reason == "MISSING_CLIENT_ORDER_ID"
    assert result.client_order_id is None
    assert result.broker_order_id == _BROKER
    assert result.generated_client_order_id is None
    _flags(result)


def test_malformed_client_order_id_is_rejected() -> None:
    for value in ("", "has space", 12, "bad\nid"):
        result = _one([_order(client_order_id=value)])
        assert result.classification is PaperClassification.REJECTED
        assert result.reason == "MALFORMED_CLIENT_ORDER_ID"
        assert result.client_order_id is None
        _flags(result)


def test_client_order_id_longer_than_128_characters_is_rejected() -> None:
    accepted = _one([_order(client_order_id="c" * 128, qty="1")])
    assert accepted.classification is PaperClassification.OBSERVED
    assert accepted.client_order_id == "c" * 128
    rejected = _one([_order(client_order_id="c" * 129)])
    assert rejected.classification is PaperClassification.REJECTED
    assert rejected.reason == "CLIENT_ORDER_ID_TOO_LONG"
    assert rejected.generated_client_order_id is None
    _flags(rejected)


def test_repeated_client_order_id_is_a_local_duplicate() -> None:
    first, second = evaluate_paper_fixtures(
        [_order(qty="2"), _order(status="filled", qty="9", filled_qty="9")]
    )
    assert first.classification is PaperClassification.OBSERVED
    assert second.classification is PaperClassification.DUPLICATE
    assert second.reason == "DUPLICATE_CLIENT_ORDER_ID"
    assert second.client_order_id == _CLIENT
    assert second.generated_client_order_id is None
    assert second.status is None
    assert second.qty is None
    assert second.submit_permitted is False
    _flags(second)


def test_client_id_stays_distinct_from_broker_order_id() -> None:
    result = _one([_order(id=_BROKER)])
    assert result.classification is PaperClassification.OBSERVED
    assert result.client_order_id == _CLIENT
    assert result.broker_order_id == _BROKER
    assert result.client_order_id != result.broker_order_id
    assert _CLIENT not in repr(result)
    assert _BROKER not in repr(result)
    _flags(result)


def test_partial_fill_preserves_decimal_filled_and_remaining() -> None:
    result = _one(
        [
            _order(
                status="partially_filled",
                qty="10.00",
                filled_qty="3.50",
                remaining_qty="6.50",
            )
        ]
    )
    assert result.classification is PaperClassification.OBSERVED
    assert result.status == "partially_filled"
    assert result.qty == Decimal("10.00")
    assert result.filled_qty == Decimal("3.50")
    assert result.remaining_qty == Decimal("6.50")
    assert result.qty is not None and result.qty.as_tuple().exponent == -2
    assert result.filled_qty is not None and result.filled_qty.as_tuple().exponent == -2
    _flags(result)


def test_decimal_text_is_not_parsed_through_float() -> None:
    result = _one([_order(qty="1.2300")])
    assert result.qty == Decimal("1.2300")
    assert result.qty is not None and result.qty.as_tuple().exponent == -4
    floated = _one([_order(qty=1.1)])
    assert floated.reason == "MALFORMED_QUANTITY"


def test_filled_quantity_above_requested_quantity_fails_closed() -> None:
    result = _one([_order(status="filled", qty="10", filled_qty="10.01", remaining_qty="0")])
    assert result.classification is PaperClassification.REJECTED
    assert result.reason == "FILLED_EXCEEDS_QTY"
    _flags(result)


def test_negative_quantity_fails_closed() -> None:
    result = _one([_order(qty="-1")])
    assert result.reason == "NEGATIVE_QUANTITY"
    assert result.classification is PaperClassification.REJECTED
    _flags(result)


def test_invalid_remaining_quantity_fails_closed() -> None:
    result = _one([_order(remaining_qty="not-a-number")])
    assert result.reason == "INVALID_REMAINING"
    assert result.classification is PaperClassification.REJECTED
    _flags(result)


def test_inconsistent_filled_and_remaining_quantities_fail_closed() -> None:
    result = _one(
        [_order(status="partially_filled", qty="10", filled_qty="4", remaining_qty="5")]
    )
    assert result.reason == "INCONSISTENT_QUANTITY"
    assert result.classification is PaperClassification.REJECTED
    _flags(result)


def test_terminal_statuses_are_observations_not_commands() -> None:
    cases = (
        ("filled", {"filled_qty": "10", "remaining_qty": "0"}),
        ("canceled", {"filled_qty": "0", "remaining_qty": "10"}),
        ("rejected", {"filled_qty": "0", "remaining_qty": "10"}),
        ("expired", {"filled_qty": "0", "remaining_qty": "10"}),
    )
    for status, quantities in cases:
        result = _one([_order(status=status, **quantities)])
        assert result.classification is PaperClassification.OBSERVED
        assert result.status == status
        assert result.reason == "CLASSIFIED"
        assert result.generated_client_order_id is None
        _flags(result)


def test_unknown_submission_requires_reconcile_and_mints_no_id() -> None:
    original = "client-unknown-1"
    result = _one([_order(status="submission_unknown", client_order_id=original, qty="4")])
    assert result.classification is PaperClassification.RECONCILE_BEFORE_RESUBMIT
    assert result.reason == "RECONCILE_BEFORE_RESUBMIT"
    assert result.client_order_id == original
    assert result.generated_client_order_id is None
    assert result.safe_to_retry is False
    assert result.resubmit_permitted is False
    assert result.status == "submission_unknown"
    _flags(result)
    again = evaluate_paper_fixtures(
        [
            _order(status="submission_unknown", client_order_id=original, qty="4"),
            _order(status="filled", client_order_id=original, qty="4", filled_qty="4"),
        ]
    )
    assert again[1].classification is PaperClassification.DUPLICATE
    assert again[1].client_order_id == original
    assert again[1].generated_client_order_id is None


def test_unknown_broker_status_is_not_retryable() -> None:
    result = _one([_order(status="held")])
    assert result.classification is PaperClassification.REJECTED
    assert result.reason == "UNKNOWN_STATUS"
    assert result.safe_to_retry is False
    assert result.resubmit_permitted is False
    _flags(result)


def test_malformed_fixture_types_fail_closed() -> None:
    for value in (None, _order(), "fixture", 0):
        result = _one(value)
        assert result.reason == "MALFORMED_FIXTURE"
        _flags(result)
    nested = _one([[_order()]])
    assert nested.reason == "MALFORMED_FIXTURE"
    account = _one([_order(account_id="SYN-ACCOUNT")])
    assert account.reason == "UNDOCUMENTED_FIELD"
    assert "SYN-ACCOUNT" not in repr(account)


def test_paper_and_live_hosts_are_denied() -> None:
    paper = deny_host(PAPER_HOST)
    live = deny_host(LIVE_HOST)
    other = deny_host("https://paper-api.alpaca.markets/v2/orders")
    assert paper.reason == "PAPER_HOST_DENIED"
    assert live.reason == "LIVE_HOST_DENIED"
    assert other.reason == "HOST_DENIED"
    for denial in (paper, live, other):
        _flags(denial)
        assert denial.connect_allowed is False


def test_module_has_no_network_secret_or_order_intent_path() -> None:
    source = Path("src/swingtrade/alpaca_paper.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module.split(".", 1)[0])
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    forbidden = {
        "socket",
        "requests",
        "httpx",
        "urllib",
        "alpaca",
        "os",
        "subprocess",
        "sqlalchemy",
        "psycopg",
    }
    assert imported.isdisjoint(forbidden)
    assert "OrderIntent" not in names
    assert "environ" not in names
    assert "getenv" not in names
    assert "APCA-API-KEY-ID" not in source
    assert "APCA-API-SECRET-KEY" not in source
    assert "risk_limit" not in source
    assert "order_class" not in source
    assert "position_size" not in source
    for function in (evaluate_paper_fixtures, deny_host):
        parameters = function.__code__.co_varnames[: function.__code__.co_argcount]
        assert set(parameters).isdisjoint(
            {"key", "secret", "api_key", "api_secret", "base_url", "token"}
        )


def test_repeated_evaluation_does_not_mutate_or_drift() -> None:
    fixtures = [
        _order(status="partially_filled", qty="2.50", filled_qty="1.25", remaining_qty="1.25")
    ]
    snapshot = copy.deepcopy(fixtures)
    first = evaluate_paper_fixtures(fixtures)
    second = evaluate_paper_fixtures(fixtures)
    assert fixtures == snapshot
    assert first == second
    assert first[0].filled_qty == Decimal("1.25")
    assert first[0].remaining_qty == Decimal("1.25")


def test_tradestation_classifier_and_parser_blobs_stay_unchanged() -> None:
    parser = subprocess.check_output(
        ["git", "hash-object", "src/swingtrade/group3_auth/brokerage_read.py"],
        text=True,
    ).strip()
    classifier = subprocess.check_output(
        ["git", "hash-object", "src/swingtrade/group3_auth/order_report.py"],
        text=True,
    ).strip()
    assert parser == _PARSER
    assert classifier == _CLASSIFIER
    assert classify_report({"facts": ["FILLED"], "order_id": "ORD_SYN_1"}).reason == "CLASSIFIED"
    read = parse_brokerage_fixture(
        ReadKind.ORDERS,
        {"Orders": [{"AccountID": "SYN_READ_ONE", "OrderID": "ORD_SYN_1", "Status": "OPN"}]},
        status=200,
    )
    assert read.decision.reason == "READ_FIXTURE"
    assert read.network_permitted is False
