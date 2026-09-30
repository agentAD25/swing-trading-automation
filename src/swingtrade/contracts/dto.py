from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from swingtrade.domain import DomainValidationError, decimal_value
from swingtrade.idempotency import input_digest
from swingtrade.persistence import canonical_decimal

_CANONICAL_UTC_MICROSECOND = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$"
)

# Documented TradeStation v3 read-model field names (BROKER_CONTRACT.md, P2_BROKER_RESEARCH.md).
_ACCOUNT_FIELDS = frozenset({"AccountID", "AccountType", "Status", "Currency"})
_BALANCE_FIELDS = frozenset(
    {"AccountID", "CashBalance", "Equity", "BuyingPower", "MarketValue"}
)
_POSITION_FIELDS = frozenset(
    {"AccountID", "Symbol", "Quantity", "AveragePrice", "Last", "MarketValue"}
)
_ORDER_FIELDS = frozenset(
    {
        "OrderID",
        "Status",
        "StatusDescription",
        "OrderQty",
        "FilledQty",
        "QuantityRemaining",
        "OpenedDateTime",
        "ClosedDateTime",
        "LimitPrice",
        "StopPrice",
        "Route",
    }
)
_ENTITLEMENT_FIELDS = frozenset(
    {
        "IsDelayed",
        "IsHardToBorrow",
        "OptionApprovalLevel",
        "IsStockLocateEligible",
    }
)
_RATE_LIMIT_HEADER_NAMES = frozenset(
    {
        "x-ratelimit-limit",
        "x-ratelimit-remaining",
        "x-ratelimit-reset",
        "x-concurrency-limit",
        "x-concurrency-remaining",
    }
)
_ERROR_ITEM_FIELDS = frozenset({"Error", "Message"})


class DtoQuarantineReason(StrEnum):
    UNKNOWN_FIELD = "UNKNOWN_FIELD"
    INVALID_TYPE = "INVALID_TYPE"
    INVALID_DECIMAL = "INVALID_DECIMAL"
    INVALID_INSTANT = "INVALID_INSTANT"
    UNKNOWN_ENUM = "UNKNOWN_ENUM"
    NONFINITE_DECIMAL = "NONFINITE_DECIMAL"
    MALFORMED_OBJECT = "MALFORMED_OBJECT"


class OrderStatusCode(StrEnum):
    """Documented example codes only; all others map to UNKNOWN."""

    ACK = "ACK"
    OPN = "OPN"
    FLL = "FLL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DtoQuarantineEntry:
    field_path: str
    reason: DtoQuarantineReason
    raw_digest: str


@dataclass(frozen=True)
class ParseResult[T]:
    value: T | None
    quarantine: tuple[DtoQuarantineEntry, ...]

    @property
    def trusted(self) -> bool:
        return self.value is not None and not self.quarantine


def quarantine_digest(raw: object) -> str:
    return input_digest(raw)


def _digest_raw(raw: object) -> str:
    return input_digest(raw)


def _quarantine(
    path: str, reason: DtoQuarantineReason, raw: object
) -> DtoQuarantineEntry:
    return DtoQuarantineEntry(field_path=path, reason=reason, raw_digest=_digest_raw(raw))


def _unknown_keys(
    raw: Mapping[str, Any], allowed: frozenset[str], prefix: str
) -> tuple[DtoQuarantineEntry, ...]:
    entries: list[DtoQuarantineEntry] = []
    for key in raw:
        if key not in allowed:
            entries.append(
                _quarantine(f"{prefix}.{key}", DtoQuarantineReason.UNKNOWN_FIELD, raw[key])
            )
    return tuple(entries)


def _parse_decimal(path: str, raw: object) -> tuple[str | None, DtoQuarantineEntry | None]:
    if isinstance(raw, bool):
        return None, _quarantine(path, DtoQuarantineReason.INVALID_TYPE, raw)
    if isinstance(raw, (int, float)):
        return None, _quarantine(path, DtoQuarantineReason.INVALID_TYPE, raw)
    if not isinstance(raw, (str, Decimal)):
        return None, _quarantine(path, DtoQuarantineReason.INVALID_TYPE, raw)
    try:
        return canonical_decimal(decimal_value(raw)), None
    except DomainValidationError as error:
        reason = (
            DtoQuarantineReason.NONFINITE_DECIMAL
            if "finite" in str(error)
            else DtoQuarantineReason.INVALID_DECIMAL
        )
        return None, _quarantine(path, reason, raw)


def _canonical_instant_string(
    path: str, raw: object
) -> tuple[str | None, DtoQuarantineEntry | None]:
    if not isinstance(raw, str):
        return None, _quarantine(path, DtoQuarantineReason.INVALID_TYPE, raw)
    if not _CANONICAL_UTC_MICROSECOND.fullmatch(raw):
        return None, _quarantine(path, DtoQuarantineReason.INVALID_INSTANT, raw)
    try:
        parsed = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
    except ValueError:
        return None, _quarantine(path, DtoQuarantineReason.INVALID_INSTANT, raw)
    canonical = parsed.isoformat(timespec="microseconds").replace("+00:00", "Z")
    if canonical != raw:
        return None, _quarantine(path, DtoQuarantineReason.INVALID_INSTANT, raw)
    return canonical, None


def _parse_order_status(
    path: str, raw: object
) -> tuple[OrderStatusCode, DtoQuarantineEntry | None]:
    if not isinstance(raw, str):
        return OrderStatusCode.UNKNOWN, _quarantine(path, DtoQuarantineReason.INVALID_TYPE, raw)
    try:
        return OrderStatusCode(raw), None
    except ValueError:
        return (
            OrderStatusCode.UNKNOWN,
            _quarantine(path, DtoQuarantineReason.UNKNOWN_ENUM, raw),
        )


def _require_string(path: str, raw: object) -> tuple[str | None, DtoQuarantineEntry | None]:
    if not isinstance(raw, str) or not raw:
        return None, _quarantine(path, DtoQuarantineReason.INVALID_TYPE, raw)
    return raw, None


@dataclass(frozen=True)
class AccountDto:
    account_id: str
    account_type: str
    status: str
    currency: str


@dataclass(frozen=True)
class BalanceDto:
    account_id: str
    cash_balance: str
    equity: str
    buying_power: str
    market_value: str


@dataclass(frozen=True)
class PositionDto:
    account_id: str
    symbol: str
    quantity: str
    average_price: str
    last_price: str
    market_value: str


@dataclass(frozen=True)
class OrderDto:
    order_id: str
    status: OrderStatusCode
    status_description: str
    order_qty: str
    filled_qty: str
    quantity_remaining: str
    opened_at: str | None
    closed_at: str | None
    limit_price: str | None
    stop_price: str | None
    route: str | None


@dataclass(frozen=True)
class EntitlementMetadata:
    is_delayed: bool | None
    is_hard_to_borrow: bool | None
    option_approval_level: int | None
    is_stock_locate_eligible: bool | None


@dataclass(frozen=True)
class RateLimitMetadata:
    rate_limit_limit: int | None
    rate_limit_remaining: int | None
    rate_limit_reset_seconds: int | None
    concurrency_limit: int | None
    concurrency_remaining: int | None


@dataclass(frozen=True)
class BrokerErrorItem:
    error_code: str
    message: str


@dataclass(frozen=True)
class BrokerErrorEnvelope:
    errors: tuple[BrokerErrorItem, ...]
    envelope_digest: str


def parse_account(raw: object) -> ParseResult[AccountDto]:
    if not isinstance(raw, Mapping):
        return ParseResult(
            None,
            (_quarantine("$", DtoQuarantineReason.MALFORMED_OBJECT, raw),),
        )
    mapping = dict(raw)
    quarantine = list(_unknown_keys(mapping, _ACCOUNT_FIELDS, "$"))
    account_id, err = _require_string("$.AccountID", mapping.get("AccountID"))
    if err:
        quarantine.append(err)
    account_type, err = _require_string("$.AccountType", mapping.get("AccountType"))
    if err:
        quarantine.append(err)
    status, err = _require_string("$.Status", mapping.get("Status"))
    if err:
        quarantine.append(err)
    currency, err = _require_string("$.Currency", mapping.get("Currency"))
    if err:
        quarantine.append(err)
    if account_id is None or account_type is None or status is None or currency is None:
        return ParseResult(None, tuple(quarantine))
    return ParseResult(
        AccountDto(
            account_id=account_id,
            account_type=account_type,
            status=status,
            currency=currency,
        ),
        tuple(quarantine),
    )


def parse_balance(raw: object) -> ParseResult[BalanceDto]:
    if not isinstance(raw, Mapping):
        return ParseResult(
            None,
            (_quarantine("$", DtoQuarantineReason.MALFORMED_OBJECT, raw),),
        )
    mapping = dict(raw)
    quarantine = list(_unknown_keys(mapping, _BALANCE_FIELDS, "$"))
    account_id, err = _require_string("$.AccountID", mapping.get("AccountID"))
    if err:
        quarantine.append(err)
    cash, err = _parse_decimal("$.CashBalance", mapping.get("CashBalance"))
    if err:
        quarantine.append(err)
    equity, err = _parse_decimal("$.Equity", mapping.get("Equity"))
    if err:
        quarantine.append(err)
    buying_power, err = _parse_decimal("$.BuyingPower", mapping.get("BuyingPower"))
    if err:
        quarantine.append(err)
    market_value, err = _parse_decimal("$.MarketValue", mapping.get("MarketValue"))
    if err:
        quarantine.append(err)
    if None in (account_id, cash, equity, buying_power, market_value):
        return ParseResult(None, tuple(quarantine))
    assert account_id is not None
    assert cash is not None
    assert equity is not None
    assert buying_power is not None
    assert market_value is not None
    return ParseResult(
        BalanceDto(
            account_id=account_id,
            cash_balance=cash,
            equity=equity,
            buying_power=buying_power,
            market_value=market_value,
        ),
        tuple(quarantine),
    )


def parse_position(raw: object) -> ParseResult[PositionDto]:
    if not isinstance(raw, Mapping):
        return ParseResult(
            None,
            (_quarantine("$", DtoQuarantineReason.MALFORMED_OBJECT, raw),),
        )
    mapping = dict(raw)
    quarantine = list(_unknown_keys(mapping, _POSITION_FIELDS, "$"))
    account_id, err = _require_string("$.AccountID", mapping.get("AccountID"))
    if err:
        quarantine.append(err)
    symbol, err = _require_string("$.Symbol", mapping.get("Symbol"))
    if err:
        quarantine.append(err)
    quantity, err = _parse_decimal("$.Quantity", mapping.get("Quantity"))
    if err:
        quarantine.append(err)
    average_price, err = _parse_decimal("$.AveragePrice", mapping.get("AveragePrice"))
    if err:
        quarantine.append(err)
    last_price, err = _parse_decimal("$.Last", mapping.get("Last"))
    if err:
        quarantine.append(err)
    market_value, err = _parse_decimal("$.MarketValue", mapping.get("MarketValue"))
    if err:
        quarantine.append(err)
    if None in (account_id, symbol, quantity, average_price, last_price, market_value):
        return ParseResult(None, tuple(quarantine))
    assert account_id is not None
    assert symbol is not None
    assert quantity is not None
    assert average_price is not None
    assert last_price is not None
    assert market_value is not None
    return ParseResult(
        PositionDto(
            account_id=account_id,
            symbol=symbol,
            quantity=quantity,
            average_price=average_price,
            last_price=last_price,
            market_value=market_value,
        ),
        tuple(quarantine),
    )


def parse_order(raw: object) -> ParseResult[OrderDto]:
    if not isinstance(raw, Mapping):
        return ParseResult(
            None,
            (_quarantine("$", DtoQuarantineReason.MALFORMED_OBJECT, raw),),
        )
    mapping = dict(raw)
    quarantine = list(_unknown_keys(mapping, _ORDER_FIELDS, "$"))
    order_id, err = _require_string("$.OrderID", mapping.get("OrderID"))
    if err:
        quarantine.append(err)
    status, status_err = _parse_order_status("$.Status", mapping.get("Status"))
    if status_err:
        quarantine.append(status_err)
    status_description, err = _require_string(
        "$.StatusDescription", mapping.get("StatusDescription")
    )
    if err:
        quarantine.append(err)
    order_qty, err = _parse_decimal("$.OrderQty", mapping.get("OrderQty"))
    if err:
        quarantine.append(err)
    filled_qty, err = _parse_decimal("$.FilledQty", mapping.get("FilledQty"))
    if err:
        quarantine.append(err)
    quantity_remaining, err = _parse_decimal(
        "$.QuantityRemaining", mapping.get("QuantityRemaining")
    )
    if err:
        quarantine.append(err)
    opened_at: str | None = None
    if "OpenedDateTime" in mapping:
        opened_at, opened_err = _canonical_instant_string(
            "$.OpenedDateTime", mapping["OpenedDateTime"]
        )
        if opened_err:
            quarantine.append(opened_err)
    closed_at: str | None = None
    if "ClosedDateTime" in mapping:
        closed_at, closed_err = _canonical_instant_string(
            "$.ClosedDateTime", mapping["ClosedDateTime"]
        )
        if closed_err:
            quarantine.append(closed_err)
    limit_price: str | None = None
    if "LimitPrice" in mapping:
        limit_price, limit_err = _parse_decimal("$.LimitPrice", mapping["LimitPrice"])
        if limit_err:
            quarantine.append(limit_err)
    stop_price: str | None = None
    if "StopPrice" in mapping:
        stop_price, stop_err = _parse_decimal("$.StopPrice", mapping["StopPrice"])
        if stop_err:
            quarantine.append(stop_err)
    route: str | None = None
    if "Route" in mapping:
        route, route_err = _require_string("$.Route", mapping["Route"])
        if route_err:
            quarantine.append(route_err)
    if None in (order_id, status_description, order_qty, filled_qty, quantity_remaining):
        return ParseResult(None, tuple(quarantine))
    assert order_id is not None
    assert status_description is not None
    assert order_qty is not None
    assert filled_qty is not None
    assert quantity_remaining is not None
    return ParseResult(
        OrderDto(
            order_id=order_id,
            status=status,
            status_description=status_description,
            order_qty=order_qty,
            filled_qty=filled_qty,
            quantity_remaining=quantity_remaining,
            opened_at=opened_at,
            closed_at=closed_at,
            limit_price=limit_price,
            stop_price=stop_price,
            route=route,
        ),
        tuple(quarantine),
    )


def _parse_optional_bool(path: str, raw: object) -> tuple[bool | None, DtoQuarantineEntry | None]:
    if raw is None:
        return None, None
    if isinstance(raw, bool):
        return raw, None
    return None, _quarantine(path, DtoQuarantineReason.INVALID_TYPE, raw)


def _parse_optional_int(path: str, raw: object) -> tuple[int | None, DtoQuarantineEntry | None]:
    if raw is None:
        return None, None
    if isinstance(raw, bool):
        return None, _quarantine(path, DtoQuarantineReason.INVALID_TYPE, raw)
    if isinstance(raw, int) and not isinstance(raw, bool):
        return raw, None
    return None, _quarantine(path, DtoQuarantineReason.INVALID_TYPE, raw)


def parse_entitlement_metadata(raw: object) -> ParseResult[EntitlementMetadata]:
    if not isinstance(raw, Mapping):
        return ParseResult(
            None,
            (_quarantine("$", DtoQuarantineReason.MALFORMED_OBJECT, raw),),
        )
    mapping = dict(raw)
    quarantine = list(_unknown_keys(mapping, _ENTITLEMENT_FIELDS, "$"))
    is_delayed, err = _parse_optional_bool("$.IsDelayed", mapping.get("IsDelayed"))
    if err:
        quarantine.append(err)
    is_hard, err = _parse_optional_bool("$.IsHardToBorrow", mapping.get("IsHardToBorrow"))
    if err:
        quarantine.append(err)
    level, err = _parse_optional_int("$.OptionApprovalLevel", mapping.get("OptionApprovalLevel"))
    if err:
        quarantine.append(err)
    locate, err = _parse_optional_bool(
        "$.IsStockLocateEligible", mapping.get("IsStockLocateEligible")
    )
    if err:
        quarantine.append(err)
    return ParseResult(
        EntitlementMetadata(
            is_delayed=is_delayed,
            is_hard_to_borrow=is_hard,
            option_approval_level=level,
            is_stock_locate_eligible=locate,
        ),
        tuple(quarantine),
    )


def _parse_header_int(path: str, raw: object) -> tuple[int | None, DtoQuarantineEntry | None]:
    if raw is None:
        return None, None
    if isinstance(raw, bool):
        return None, _quarantine(path, DtoQuarantineReason.INVALID_TYPE, raw)
    if isinstance(raw, int) and not isinstance(raw, bool):
        return raw, None
    if isinstance(raw, str) and raw.isdigit():
        return int(raw), None
    return None, _quarantine(path, DtoQuarantineReason.INVALID_TYPE, raw)


def parse_rate_limit_metadata(headers: object) -> ParseResult[RateLimitMetadata]:
    if not isinstance(headers, Mapping):
        return ParseResult(
            None,
            (_quarantine("$", DtoQuarantineReason.MALFORMED_OBJECT, headers),),
        )
    normalized: dict[str, object] = {}
    for key, value in headers.items():
        if not isinstance(key, str):
            return ParseResult(
                None,
                (_quarantine("$", DtoQuarantineReason.MALFORMED_OBJECT, headers),),
            )
        lowered = key.lower()
        if lowered in _RATE_LIMIT_HEADER_NAMES:
            normalized[lowered] = value
        else:
            normalized.setdefault("__unknown__", {})
            if isinstance(normalized["__unknown__"], dict):
                cast_unknown = normalized["__unknown__"]
                cast_unknown[key] = value
    quarantine: list[DtoQuarantineEntry] = []
    unknown_bucket = normalized.pop("__unknown__", None)
    if isinstance(unknown_bucket, dict):
        for unknown_key, unknown_value in unknown_bucket.items():
            quarantine.append(
                _quarantine(f"$.{unknown_key}", DtoQuarantineReason.UNKNOWN_FIELD, unknown_value)
            )
    limit, err = _parse_header_int("$.X-RateLimit-Limit", normalized.get("x-ratelimit-limit"))
    if err:
        quarantine.append(err)
    remaining, err = _parse_header_int(
        "$.X-RateLimit-Remaining", normalized.get("x-ratelimit-remaining")
    )
    if err:
        quarantine.append(err)
    reset, err = _parse_header_int("$.X-RateLimit-Reset", normalized.get("x-ratelimit-reset"))
    if err:
        quarantine.append(err)
    concurrency_limit, err = _parse_header_int(
        "$.X-Concurrency-Limit", normalized.get("x-concurrency-limit")
    )
    if err:
        quarantine.append(err)
    concurrency_remaining, err = _parse_header_int(
        "$.X-Concurrency-Remaining", normalized.get("x-concurrency-remaining")
    )
    if err:
        quarantine.append(err)
    return ParseResult(
        RateLimitMetadata(
            rate_limit_limit=limit,
            rate_limit_remaining=remaining,
            rate_limit_reset_seconds=reset,
            concurrency_limit=concurrency_limit,
            concurrency_remaining=concurrency_remaining,
        ),
        tuple(quarantine),
    )


def parse_broker_error_envelope(raw: object) -> ParseResult[BrokerErrorEnvelope]:
    if not isinstance(raw, Mapping):
        return ParseResult(
            None,
            (_quarantine("$", DtoQuarantineReason.MALFORMED_OBJECT, raw),),
        )
    errors_raw = raw.get("Errors")
    if errors_raw is None:
        return ParseResult(
            None,
            (_quarantine("$.Errors", DtoQuarantineReason.MALFORMED_OBJECT, raw),),
        )
    if not isinstance(errors_raw, list):
        return ParseResult(
            None,
            (_quarantine("$.Errors", DtoQuarantineReason.INVALID_TYPE, errors_raw),),
        )
    quarantine: list[DtoQuarantineEntry] = []
    for key in raw:
        if key != "Errors":
            quarantine.append(
                _quarantine(f"$.{key}", DtoQuarantineReason.UNKNOWN_FIELD, raw[key])
            )
    items: list[BrokerErrorItem] = []
    for index, item in enumerate(errors_raw):
        if not isinstance(item, Mapping):
            quarantine.append(
                _quarantine(f"$.Errors[{index}]", DtoQuarantineReason.MALFORMED_OBJECT, item)
            )
            continue
        item_map = dict(item)
        for field in item_map:
            if field not in _ERROR_ITEM_FIELDS:
                quarantine.append(
                    _quarantine(
                        f"$.Errors[{index}].{field}",
                        DtoQuarantineReason.UNKNOWN_FIELD,
                        item_map[field],
                    )
                )
        code, code_err = _require_string(f"$.Errors[{index}].Error", item_map.get("Error"))
        if code_err:
            quarantine.append(code_err)
        message, message_err = _require_string(
            f"$.Errors[{index}].Message", item_map.get("Message")
        )
        if message_err:
            quarantine.append(message_err)
        if code is None or message is None:
            continue
        items.append(BrokerErrorItem(error_code=code, message=message))
    if not items:
        return ParseResult(None, tuple(quarantine))
    digest = input_digest(
        {
            "Errors": [
                {"Error": item.error_code, "Message": item.message} for item in items
            ]
        }
    )
    return ParseResult(
        BrokerErrorEnvelope(errors=tuple(items), envelope_digest=digest),
        tuple(quarantine),
    )
