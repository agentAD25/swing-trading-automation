from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum

MAX_DECIMAL_RAW_LENGTH = 1024
MAX_DECIMAL_COEFFICIENT_DIGITS = 1000
MAX_DECIMAL_EXPONENT_DIGITS = 6
MAX_DECIMAL_EXPONENT_MAGNITUDE = 999_999
_DECIMAL_TYPE = Decimal


class DomainValidationError(ValueError):
    """A value violates a broker-neutral domain invariant."""


class ExecutionMode(StrEnum):
    DRY_RUN = "DRY_RUN"
    SIM = "SIM"
    LIVE_SHADOW = "LIVE_SHADOW"
    LIVE = "LIVE"


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


def _decimal_lexical_error(reason: str) -> DomainValidationError:
    return DomainValidationError(
        "invalid decimal input "
        f"(reason={reason}, max_raw_length={MAX_DECIMAL_RAW_LENGTH}, "
        f"max_coefficient_digits={MAX_DECIMAL_COEFFICIENT_DIGITS}, "
        f"max_exponent_digits={MAX_DECIMAL_EXPONENT_DIGITS})"
    )


def _validate_decimal_string(raw: str) -> None:
    raw_length = len(raw)
    if raw_length == 0:
        raise _decimal_lexical_error("empty")
    if raw_length > MAX_DECIMAL_RAW_LENGTH:
        raise _decimal_lexical_error("raw-length")
    unsigned = raw[1:] if raw[0] in "+-" else raw
    if unsigned.lower() in {"nan", "snan", "inf", "infinity"}:
        raise DomainValidationError("decimal must be finite")

    index = 1 if raw[0] in "+-" else 0
    coefficient_digits = 0
    seen_decimal_point = False
    while index < raw_length and raw[index] not in "eE":
        character = raw[index]
        if "0" <= character <= "9":
            coefficient_digits += 1
            if coefficient_digits > MAX_DECIMAL_COEFFICIENT_DIGITS:
                raise _decimal_lexical_error("coefficient-digits")
        elif character == "." and not seen_decimal_point:
            seen_decimal_point = True
        else:
            raise _decimal_lexical_error("syntax")
        index += 1
    if coefficient_digits == 0:
        raise _decimal_lexical_error("missing-coefficient")
    if index == raw_length:
        return

    index += 1
    if index < raw_length and raw[index] in "+-":
        index += 1
    exponent_start = index
    while index < raw_length and "0" <= raw[index] <= "9":
        index += 1
    exponent_digits = index - exponent_start
    if exponent_digits == 0 or index != raw_length:
        raise _decimal_lexical_error("exponent-syntax")
    if exponent_digits > MAX_DECIMAL_EXPONENT_DIGITS:
        raise _decimal_lexical_error("exponent-digits")
    exponent_magnitude = int(raw[exponent_start:index])
    if exponent_magnitude > MAX_DECIMAL_EXPONENT_MAGNITUDE:
        raise _decimal_lexical_error("exponent-magnitude")


def decimal_value(value: Decimal | str) -> Decimal:
    if type(value) is _DECIMAL_TYPE:
        result = value
    elif type(value) is str:
        _validate_decimal_string(value)
        try:
            result = Decimal(value)
        except Exception as error:
            raise DomainValidationError("invalid decimal input") from error
    else:
        raise DomainValidationError("decimal input type must be exactly Decimal or str")
    if not result.is_finite():
        raise DomainValidationError("decimal must be finite")
    return result


def utc_instant(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise DomainValidationError("instant must be UTC")
    return value


@dataclass(frozen=True)
class Bar:
    instrument_id: str
    symbol: str
    interval: str
    session_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    currency: str
    source: str
    revision: int

    def __post_init__(self) -> None:
        for field in ("open", "high", "low", "close", "volume"):
            object.__setattr__(self, field, decimal_value(getattr(self, field)))
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise DomainValidationError("OHLC values are inconsistent")
        if self.volume < 0 or self.revision < 1:
            raise DomainValidationError("volume and revision must be nonnegative")


@dataclass(frozen=True)
class OrderIntent:
    intent_id: str
    run_id: str
    decision_id: str
    instrument_id: str
    side: Side
    quantity: Decimal
    mode: ExecutionMode
    idempotency_key: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "quantity", decimal_value(self.quantity))
        if self.quantity <= 0:
            raise DomainValidationError("quantity must be positive")


@dataclass(frozen=True)
class OrderObservation:
    order_id: str
    intent_id: str
    state: str
    requested_quantity: Decimal
    cumulative_quantity: Decimal
    effective_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_quantity", decimal_value(self.requested_quantity))
        object.__setattr__(self, "cumulative_quantity", decimal_value(self.cumulative_quantity))
        utc_instant(self.effective_at)
        if not Decimal("0") <= self.cumulative_quantity <= self.requested_quantity:
            raise DomainValidationError("cumulative quantity is outside requested quantity")
