"""Parse documented v3 read fixtures. No request is sent and no account id is rendered."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from enum import StrEnum

from swingtrade.group3_auth.outcomes import AuthDecision, OutcomeCode, decision

# Property names are the OpenAPI 3.0.3 components embedded in the public
# TradeStation specification page, accessed 2026-10-08:
# https://api.tradestation.com/docs/specification/
# Account identifiers from that page's examples are not copied here.

_STR = "str"
_BOOL = "bool"
_INT = "int"


class ReadKind(StrEnum):
    ACCOUNTS = "ACCOUNTS"
    BALANCES = "BALANCES"
    POSITIONS = "POSITIONS"
    ORDERS = "ORDERS"


class ReadObservation:
    """Non-secret read classification. Account ids are digests only."""

    __slots__ = (
        "account_digests",
        "connect_allowed",
        "decision",
        "error_count",
        "kind",
        "network_permitted",
        "record_count",
    )

    def __init__(
        self,
        result: AuthDecision,
        *,
        kind: ReadKind | None,
        record_count: int,
        error_count: int,
        account_digests: tuple[str, ...],
    ) -> None:
        self.decision = result
        self.kind = kind
        self.record_count = record_count
        self.error_count = error_count
        self.account_digests = account_digests
        self.connect_allowed = False
        self.network_permitted = False

    def __repr__(self) -> str:
        return f"ReadObservation({self.decision.reason})"


def parse_brokerage_fixture(
    kind: object,
    body: object,
    *,
    status: object,
    timeout: bool = False,
) -> ReadObservation:
    """Classify one in-memory fixture. HTTP success does not erase an Errors array."""
    read_kind = _kind(kind)
    if read_kind is None:
        return _empty(decision(OutcomeCode.REJECTED, "UNKNOWN_READ"))
    if timeout:
        return _empty(decision(OutcomeCode.REJECTED, "NETWORK_TIMEOUT"), read_kind)
    if type(status) is not int:
        return _empty(decision(OutcomeCode.REJECTED, "MALFORMED_STATUS"), read_kind)
    http = _http(status)
    if http is not None:
        return _empty(http, read_kind)
    if not isinstance(body, Mapping) or type(body) is not dict:
        return _empty(decision(OutcomeCode.REJECTED, "MALFORMED_RESPONSE"), read_kind)
    return _parse_ok(read_kind, body)


def _parse_ok(kind: ReadKind, body: dict[str, object]) -> ReadObservation:
    schema = _ROOTS[kind]
    reason = _check(body, schema)
    if reason is not None:
        return _empty(decision(OutcomeCode.REJECTED, reason), kind)
    collection_name, error_name, identity_name = _COLLECTIONS[kind]
    if collection_name not in body:
        return _empty(decision(OutcomeCode.REJECTED, "MALFORMED_RESPONSE"), kind)
    records = body[collection_name]
    errors = body.get(error_name, [])
    if type(records) is not list or type(errors) is not list:
        return _empty(decision(OutcomeCode.REJECTED, "MALFORMED_RESPONSE"), kind)
    digests: list[str] = []
    seen: dict[str, str] = {}
    for record in records:
        if type(record) is not dict:
            return _empty(decision(OutcomeCode.REJECTED, "MALFORMED_RESPONSE"), kind)
        identity = record.get(identity_name)
        if type(identity) is not str:
            return _empty(decision(OutcomeCode.REJECTED, "MALFORMED_IDENTITY"), kind)
        digest = _digest(identity)
        signature = _signature(record)
        previous = seen.get(digest)
        if previous is not None and previous != signature:
            return _empty(decision(OutcomeCode.REJECTED, "CONFLICTING_RESPONSE"), kind)
        if previous is not None:
            return _empty(decision(OutcomeCode.REJECTED, "CONFLICTING_RESPONSE"), kind)
        seen[digest] = signature
        digests.append(digest)
    if errors:
        return ReadObservation(
            decision(OutcomeCode.UNKNOWN, "PARTIAL_RESPONSE"),
            kind=kind,
            record_count=len(records),
            error_count=len(errors),
            account_digests=tuple(digests),
        )
    if not records:
        return ReadObservation(
            decision(OutcomeCode.CLASSIFIED, "EMPTY_COLLECTION"),
            kind=kind,
            record_count=0,
            error_count=0,
            account_digests=(),
        )
    reason_name = "MULTIPLE_RECORDS" if len(records) > 1 else "READ_FIXTURE"
    return ReadObservation(
        decision(OutcomeCode.CLASSIFIED, reason_name),
        kind=kind,
        record_count=len(records),
        error_count=0,
        account_digests=tuple(digests),
    )


def _check(value: object, schema: object) -> str | None:
    if schema == _STR:
        return None if type(value) is str else "MALFORMED_RESPONSE"
    if schema == _BOOL:
        return None if type(value) is bool else "MALFORMED_RESPONSE"
    if schema == _INT:
        if type(value) is int and not isinstance(value, bool):
            return None
        return "MALFORMED_RESPONSE"
    if type(schema) is tuple and schema[0] == "list":
        if type(value) is not list:
            return "MALFORMED_RESPONSE"
        for item in value:
            reason = _check(item, schema[1])
            if reason is not None:
                return reason
        return None
    if type(schema) is not dict:
        return "MALFORMED_RESPONSE"
    if type(value) is not dict:
        return "MALFORMED_RESPONSE"
    allowed = set(schema)
    if not set(value).issubset(allowed):
        return "UNDOCUMENTED_FIELD"
    for key, item in value.items():
        if key == "AccountID" and (type(item) is not str or not _account_text(item)):
            return "MALFORMED_ACCOUNT"
        reason = _check(item, schema[key])
        if reason is not None:
            return reason
    return None


def _account_text(value: str) -> bool:
    if value == "" or len(value) > 64:
        return False
    return not any(character.isspace() or ord(character) < 32 for character in value)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _signature(record: Mapping[str, object]) -> str:
    parts = [f"{key}={record[key]!s}" for key in sorted(record) if key != "AccountID"]
    return "|".join(parts)


def _http(status: int) -> AuthDecision | None:
    if status == 200:
        return None
    if status == 401:
        return decision(OutcomeCode.REJECTED, "HTTP_401")
    if status == 403:
        return decision(OutcomeCode.REJECTED, "HTTP_403")
    if status == 429:
        return decision(OutcomeCode.REJECTED, "HTTP_429")
    if 500 <= status <= 599:
        return decision(OutcomeCode.REJECTED, "HTTP_5XX")
    return decision(OutcomeCode.REJECTED, "HTTP_UNEXPECTED")


def _kind(value: object) -> ReadKind | None:
    if type(value) is ReadKind:
        return value
    return None


def _empty(result: AuthDecision, kind: ReadKind | None = None) -> ReadObservation:
    return ReadObservation(
        result,
        kind=kind,
        record_count=0,
        error_count=0,
        account_digests=(),
    )


_ACCOUNT_DETAIL = {
    "DayTradingQualified": _BOOL,
    "EnrolledInRegTProgram": _BOOL,
    "IsStockLocateEligible": _BOOL,
    "OptionApprovalLevel": _INT,
    "PatternDayTrader": _BOOL,
    "RequiresBuyingPowerWarning": _BOOL,
}
_ACCOUNT = {
    "AccountDetail": _ACCOUNT_DETAIL,
    "AccountID": _STR,
    "AccountType": _STR,
    "Alias": _STR,
    "AltID": _STR,
    "Currency": _STR,
    "Status": _STR,
}
_BALANCE_DETAIL = {
    "CostOfPositions": _STR,
    "DayTradeExcess": _STR,
    "DayTradeMargin": _STR,
    "DayTradeOpenOrderMargin": _STR,
    "DayTrades": _STR,
    "InitialMargin": _STR,
    "MaintenanceMargin": _STR,
    "MaintenanceRate": _STR,
    "MarginRequirement": _STR,
    "OpenOrderMargin": _STR,
    "OptionBuyingPower": _STR,
    "OptionsMarketValue": _STR,
    "OvernightBuyingPower": _STR,
    "RealizedProfitLoss": _STR,
    "RequiredMargin": _STR,
    "SecurityOnDeposit": _STR,
    "TodayRealTimeTradeEquity": _STR,
    "TradeEquity": _STR,
    "UnrealizedProfitLoss": _STR,
    "UnsettledFunds": _STR,
}
_CURRENCY_DETAIL = {
    "AccountConversionRate": _STR,
    "AccountMarginRequirement": _STR,
    "CashBalance": _STR,
    "Commission": _STR,
    "Currency": _STR,
    "InitialMargin": _STR,
    "MaintenanceMargin": _STR,
    "RealizedProfitLoss": _STR,
    "UnrealizedProfitLoss": _STR,
}
_BALANCE = {
    "AccountID": _STR,
    "AccountType": _STR,
    "BalanceDetail": _BALANCE_DETAIL,
    "BuyingPower": _STR,
    "CashBalance": _STR,
    "Commission": _STR,
    "CurrencyDetails": ("list", _CURRENCY_DETAIL),
    "Equity": _STR,
    "MarketValue": _STR,
    "TodaysProfitLoss": _STR,
    "UnclearedDeposit": _STR,
}
_ERROR = {"AccountID": _STR, "Error": _STR, "Message": _STR}
_POSITION = {
    "AccountID": _STR,
    "Ask": _STR,
    "AssetType": _STR,
    "AveragePrice": _STR,
    "Bid": _STR,
    "ConversionRate": _STR,
    "DayTradeRequirement": _STR,
    "ExpirationDate": _STR,
    "InitialRequirement": _STR,
    "Last": _STR,
    "LongShort": _STR,
    "MaintenanceMargin": _STR,
    "MarkToMarketPrice": _STR,
    "MarketValue": _STR,
    "PositionID": _STR,
    "Quantity": _STR,
    "Symbol": _STR,
    "Timestamp": _STR,
    "TodaysProfitLoss": _STR,
    "TotalCost": _STR,
    "UnrealizedProfitLoss": _STR,
    "UnrealizedProfitLossPercent": _STR,
    "UnrealizedProfitLossQty": _STR,
}
_LEG = {
    "AssetType": _STR,
    "BuyOrSell": _STR,
    "ExecQuantity": _STR,
    "ExecutionPrice": _STR,
    "ExpirationDate": _STR,
    "OpenOrClose": _STR,
    "OptionType": _STR,
    "QuantityOrdered": _STR,
    "QuantityRemaining": _STR,
    "StrikePrice": _STR,
    "Symbol": _STR,
    "Underlying": _STR,
}
_RELATIONSHIP = {"OrderID": _STR, "Relationship": _STR}
_RULE = {
    "LogicOperator": _STR,
    "Predicate": _STR,
    "Price": _STR,
    "RuleType": _STR,
    "Symbol": _STR,
    "TriggerKey": _STR,
}
_ORDER = {
    "AccountID": _STR,
    "AdvancedOptions": _STR,
    "ClosedDateTime": _STR,
    "CommissionFee": _STR,
    "ConditionalOrders": ("list", _RELATIONSHIP),
    "ConversionRate": _STR,
    "Currency": _STR,
    "Duration": _STR,
    "FilledPrice": _STR,
    "GoodTillDate": _STR,
    "GroupName": _STR,
    "Legs": ("list", _LEG),
    "LimitPrice": _STR,
    "MarketActivationRules": _RULE,
    "OpenedDateTime": _STR,
    "OrderID": _STR,
    "OrderType": _STR,
    "PriceUsedForBuyingPower": _STR,
    "RejectReason": _STR,
    "Routing": _STR,
    "ShowOnlyQuantity": _STR,
    "Status": _STR,
    "StatusDescription": _STR,
    "StopPrice": _STR,
    "TimeActivationRules": {"TimeUtc": _STR},
    "TrailingStop": {"Amount": _STR, "Percent": _STR},
    "UnbundledRouteFee": _STR,
}
# Spread is a documented optional object whose nested types are not pinned
# in this parser. Its presence fails closed as UNDOCUMENTED_FIELD.
_ROOTS: dict[ReadKind, dict[str, object]] = {
    ReadKind.ACCOUNTS: {"Accounts": ("list", _ACCOUNT)},
    ReadKind.BALANCES: {"Balances": ("list", _BALANCE), "Errors": ("list", _ERROR)},
    ReadKind.POSITIONS: {"Positions": ("list", _POSITION), "Errors": ("list", _ERROR)},
    ReadKind.ORDERS: {
        "Orders": ("list", _ORDER),
        "Errors": ("list", _ERROR),
        "NextToken": _STR,
    },
}
_COLLECTIONS = {
    ReadKind.ACCOUNTS: ("Accounts", "Errors", "AccountID"),
    ReadKind.BALANCES: ("Balances", "Errors", "AccountID"),
    ReadKind.POSITIONS: ("Positions", "Errors", "PositionID"),
    ReadKind.ORDERS: ("Orders", "Errors", "OrderID"),
}
