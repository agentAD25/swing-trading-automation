from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum


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


def decimal_value(value: Decimal | str) -> Decimal:
    if isinstance(value, float):
        raise DomainValidationError("binary floating point is prohibited")
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except Exception as error:
        raise DomainValidationError("invalid decimal") from error
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
