from __future__ import annotations

import builtins
from decimal import Decimal

import pytest

from swingtrade.contracts.dto import (
    DtoQuarantineReason,
    OrderStatusCode,
    parse_account,
    parse_balance,
    parse_broker_error_envelope,
    parse_entitlement_metadata,
    parse_order,
    parse_rate_limit_metadata,
    quarantine_digest,
)
from swingtrade.domain import DomainValidationError
from swingtrade.persistence import canonical_decimal


def test_account_quarantines_unknown_fields() -> None:
    result = parse_account(
        {
            "AccountID": "SYNTH-001",
            "AccountType": "Cash",
            "Status": "Active",
            "Currency": "USD",
            "Unexpected": "value",
        }
    )
    assert result.value is not None
    assert result.value.account_id == "SYNTH-001"
    assert len(result.quarantine) == 1
    assert result.quarantine[0].reason is DtoQuarantineReason.UNKNOWN_FIELD


def test_balance_canonicalizes_scientific_notation() -> None:
    payload = {
        "AccountID": "SYNTH-001",
        "CashBalance": "1E-2",
        "Equity": "100.00",
        "BuyingPower": "50",
        "MarketValue": "100.00",
    }
    result = parse_balance(payload)
    assert result.value is not None
    assert result.value.cash_balance == canonical_decimal("0.01")


@pytest.mark.parametrize(
    "value",
    [
        "1E+1000",
        "9" * 1001,
        "NaN",
        "Infinity",
    ],
)
def test_balance_rejects_extreme_or_nonfinite_decimal(value: str) -> None:
    payload = {
        "AccountID": "SYNTH-001",
        "CashBalance": value,
        "Equity": "1",
        "BuyingPower": "1",
        "MarketValue": "1",
    }
    result = parse_balance(payload)
    assert result.value is None
    assert result.quarantine


def test_balance_rejects_bool_and_float_confusion() -> None:
    for bad in (True, 1.25):
        payload = {
            "AccountID": "SYNTH-001",
            "CashBalance": bad,
            "Equity": "1",
            "BuyingPower": "1",
            "MarketValue": "1",
        }
        result = parse_balance(payload)
        assert result.value is None
        assert any(entry.reason is DtoQuarantineReason.INVALID_TYPE for entry in result.quarantine)


def test_order_unknown_status_maps_to_unknown_with_quarantine() -> None:
    result = parse_order(
        {
            "OrderID": "ORD-1",
            "Status": "ZZZ",
            "StatusDescription": "Unknown",
            "OrderQty": "10",
            "FilledQty": "0",
            "QuantityRemaining": "10",
        }
    )
    assert result.value is not None
    assert result.value.status is OrderStatusCode.UNKNOWN
    assert any(entry.reason is DtoQuarantineReason.UNKNOWN_ENUM for entry in result.quarantine)


def test_order_documented_status_codes_are_known() -> None:
    for code in ("ACK", "OPN", "FLL"):
        result = parse_order(
            {
                "OrderID": "ORD-1",
                "Status": code,
                "StatusDescription": "ok",
                "OrderQty": "1",
                "FilledQty": "0",
                "QuantityRemaining": "1",
            }
        )
        assert result.value is not None
        assert result.value.status is OrderStatusCode(code)
        assert not any(
            entry.reason is DtoQuarantineReason.UNKNOWN_ENUM for entry in result.quarantine
        )


@pytest.mark.parametrize(
    ("opened", "quarantined"),
    [
        ("2026-01-15T12:34:56.123456Z", False),
        ("2026-01-15T12:34:56Z", True),
        ("2026-01-15T12:34:56.123456+00:00", True),
    ],
)
def test_order_instant_canonicalization(opened: str, quarantined: bool) -> None:
    result = parse_order(
        {
            "OrderID": "ORD-1",
            "Status": "ACK",
            "StatusDescription": "ok",
            "OrderQty": "1",
            "FilledQty": "0",
            "QuantityRemaining": "1",
            "OpenedDateTime": opened,
        }
    )
    assert result.value is not None
    if quarantined:
        assert any(
            entry.reason is DtoQuarantineReason.INVALID_INSTANT for entry in result.quarantine
        )
    else:
        assert result.value.opened_at == opened


def test_extreme_decimal_rejects_before_format(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_format(value: object, format_spec: str = "") -> str:
        raise AssertionError("format must not run for rejected values")

    monkeypatch.setattr(builtins, "format", forbidden_format)
    with pytest.raises(DomainValidationError, match="resource bound"):
        canonical_decimal(Decimal("1E+1000000"))


def test_rate_limit_metadata_parses_documented_headers() -> None:
    result = parse_rate_limit_metadata(
        {
            "X-RateLimit-Limit": "320",
            "X-RateLimit-Remaining": "10",
            "X-RateLimit-Reset": "42",
            "X-Concurrency-Limit": "2",
            "X-Concurrency-Remaining": "1",
        }
    )
    assert result.value is not None
    assert result.value.rate_limit_limit == 320
    assert result.value.concurrency_remaining == 1


def test_entitlement_metadata_accepts_documented_flags() -> None:
    result = parse_entitlement_metadata(
        {
            "IsDelayed": True,
            "IsHardToBorrow": False,
            "OptionApprovalLevel": 3,
            "IsStockLocateEligible": True,
        }
    )
    assert result.value is not None
    assert result.value.is_delayed is True
    assert result.value.option_approval_level == 3


def test_broker_error_envelope_parses_errors_array() -> None:
    result = parse_broker_error_envelope(
        {"Errors": [{"Error": "NotFound", "Message": "missing resource"}]}
    )
    assert result.value is not None
    assert result.value.errors[0].error_code == "NotFound"
    assert len(result.value.envelope_digest) == 64


def test_quarantine_digest_is_stable() -> None:
    assert quarantine_digest({"a": 1}) == quarantine_digest({"a": 1})
    assert quarantine_digest({"a": 1}) != quarantine_digest({"a": 2})
