"""Canonical trade-instruction contract. No broker action and no retention choice."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from swingtrade.domain import Side

# Future mailbox reference is this environment name only. It is never read here.
SIGNAL_MAILBOX = "SIGNAL_MAILBOX"
FIXTURE_SIGNAL_MAILBOX = "signals@example.invalid"

TRADE_AMENDMENT_PARSER = "DEFERRED_FIXTURE_REQUIRED"
EXIT_ALERT_PARSER = "DEFERRED_FIXTURE_REQUIRED"
QUANTITY_ROUNDING_POLICY = "UNRESOLVED"
EMAIL_RETENTION_POLICY = "UNRESOLVED"
TIMEZONE_ASSUMPTION = "UNSTATED"
CALENDAR_ASSUMPTION = "UNRESOLVED"
MAX_EMAIL_BYTES = 65536
MAX_EVIDENCE_CHARS = 240

RESOLUTION_EXPLICIT = "EXPLICIT_CIVIL_DATE"
RESOLUTION_UNRESOLVED = "UNRESOLVED_PARTIAL_DATE"
RESOLUTION_CONFLICT = "DATE_CONFLICT"
RESOLUTION_ABSENT = "NO_DATE_EXPRESSION"
RESOLUTION_MALFORMED = "MALFORMED_DATE"


class MessageType(StrEnum):
    NEW_TRADE = "NEW_TRADE"
    TRADE_AMENDMENT = "TRADE_AMENDMENT"
    EXIT_ALERT = "EXIT_ALERT"
    TRADE_CANCEL = "TRADE_CANCEL"
    INFORMATIONAL = "INFORMATIONAL"
    UNKNOWN = "UNKNOWN"


class Disposition(StrEnum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    QUARANTINE = "QUARANTINE"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    UNKNOWN = "UNKNOWN"


class TimeInForce(StrEnum):
    DAY = "DAY"
    GTC = "GTC"
    UNKNOWN = "UNKNOWN"


class TriggerBasis(StrEnum):
    BROKER_PRICE_ORDER = "BROKER_PRICE_ORDER"
    DAILY_CLOSE_TRIGGER = "DAILY_CLOSE_TRIGGER"
    NEXT_OPEN_TRIGGER = "NEXT_OPEN_TRIGGER"
    CALENDAR_TRIGGER = "CALENDAR_TRIGGER"
    OTHER_EXPLICIT = "OTHER_EXPLICIT"
    UNKNOWN = "UNKNOWN"


class Direction(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


class SessionEvent(StrEnum):
    REGULAR_SESSION_OPEN = "REGULAR_SESSION_OPEN"


class SiblingCancel(StrEnum):
    SIBLING_CANCEL_REQUIRED = "SIBLING_CANCEL_REQUIRED"


class ReasonCode(StrEnum):
    INVALID_INPUT = "INVALID_INPUT"
    EMPTY_INPUT = "EMPTY_INPUT"
    OVERSIZED_INPUT = "OVERSIZED_INPUT"
    MALFORMED_MIME = "MALFORMED_MIME"
    UNSUPPORTED_CHARSET = "UNSUPPORTED_CHARSET"
    UNDECODABLE_BODY = "UNDECODABLE_BODY"
    NO_TEXT_BODY = "NO_TEXT_BODY"
    MISSING_MESSAGE_ID = "MISSING_MESSAGE_ID"
    NON_FIXTURE_MESSAGE_ID = "NON_FIXTURE_MESSAGE_ID"
    POLICY_INSTRUCTION_IGNORED = "POLICY_INSTRUCTION_IGNORED"
    PARSER_DEFERRED = "PARSER_DEFERRED"
    CANCEL_FORMAT_UNSPECIFIED = "CANCEL_FORMAT_UNSPECIFIED"
    HTML_PLAIN_CONFLICT = "HTML_PLAIN_CONFLICT"
    CONFLICTING_ECONOMIC_INSTRUCTION = "CONFLICTING_ECONOMIC_INSTRUCTION"
    CONFLICTING_DUPLICATE = "CONFLICTING_DUPLICATE"
    DATE_CONFLICT = "DATE_CONFLICT"
    UNRESOLVED_REQUIRED_DATE = "UNRESOLVED_REQUIRED_DATE"
    MALFORMED_DATE = "MALFORMED_DATE"
    MALFORMED_CURRENCY = "MALFORMED_CURRENCY"
    UNICODE_LOOKALIKE = "UNICODE_LOOKALIKE"
    INVALID_SYMBOL = "INVALID_SYMBOL"
    MISSING_ENTRY = "MISSING_ENTRY"
    MISSING_TARGET = "MISSING_TARGET"
    MISSING_STOP = "MISSING_STOP"
    MISSING_SIZING = "MISSING_SIZING"
    MISSING_TIF = "MISSING_TIF"
    MISSING_EXIT_POLICY = "MISSING_EXIT_POLICY"
    UNKNOWN_ORDER_TYPE = "UNKNOWN_ORDER_TYPE"
    INCOMPLETE_STOP_LIMIT = "INCOMPLETE_STOP_LIMIT"
    INCOMPLETE_TRADE = "INCOMPLETE_TRADE"
    UNSPECIFIED_TIME_EXIT = "UNSPECIFIED_TIME_EXIT"
    OVERSIZED_FIELD = "OVERSIZED_FIELD"


@dataclass(frozen=True)
class FieldEvidence:
    """Exact economic citation. This is not a retained raw message."""

    field: str
    source_text: str


@dataclass(frozen=True)
class PriceOrder:
    side: Side
    order_type: OrderType
    price: Decimal | None
    limit_price: Decimal | None
    time_in_force: TimeInForce
    trigger_basis: TriggerBasis
    session_date: date | None
    session_source_date: str
    date_resolution_rule: str
    timezone_assumption: str
    calendar_assumption: str
    evidence: tuple[FieldEvidence, ...]


@dataclass(frozen=True)
class Sizing:
    method: str
    percent_equity: Decimal
    example_account_equity: Decimal | None
    example_allocation: Decimal | None
    example_quantity: Decimal | None
    quantity_rounding_policy: str
    evidence: tuple[FieldEvidence, ...]


@dataclass(frozen=True)
class TimeExit:
    side: Side
    session_event: SessionEvent
    source_date: str
    resolved_date: date | None
    resolution_rule: str
    timezone_assumption: str
    calendar_assumption: str
    evidence: tuple[FieldEvidence, ...]


@dataclass(frozen=True)
class TradeInstruction:
    instruction_id: str
    message_type: MessageType
    symbol: str
    company_name: str | None
    strategy_label: str | None
    direction: Direction
    entry: PriceOrder
    sizing: Sizing
    target: PriceOrder
    protective_stop: PriceOrder
    time_exit: TimeExit | None
    first_exit_wins: bool
    sibling_cancel: SiblingCancel
    evidence: tuple[FieldEvidence, ...]


@dataclass(frozen=True)
class ParseOutcome:
    disposition: Disposition
    message_type: MessageType
    reasons: tuple[str, ...]
    instructions: tuple[TradeInstruction, ...]
    evidence: tuple[FieldEvidence, ...]
    content_digest: str
    message_id: str | None
    ignored_remote_references: int = 0
    ignored_attachment_count: int = 0
    network_permitted: bool = False

    def __post_init__(self) -> None:
        if self.network_permitted:
            raise RuntimeError("network is not permitted")
        if self.disposition is not Disposition.ACCEPT and self.instructions:
            raise RuntimeError("only an accepted message may carry instructions")
