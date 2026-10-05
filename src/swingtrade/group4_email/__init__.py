"""Offline email signal contract. Stops at a canonical trade instruction."""

from swingtrade.group4_email.contract import (
    CALENDAR_ASSUMPTION,
    EMAIL_RETENTION_POLICY,
    EXIT_ALERT_PARSER,
    FIXTURE_SIGNAL_MAILBOX,
    QUANTITY_ROUNDING_POLICY,
    SIGNAL_MAILBOX,
    TIMEZONE_ASSUMPTION,
    TRADE_AMENDMENT_PARSER,
    Direction,
    Disposition,
    MessageType,
    OrderType,
    ParseOutcome,
    SessionEvent,
    SiblingCancel,
    TimeInForce,
    TradeInstruction,
    TriggerBasis,
)
from swingtrade.group4_email.extract import economic_decimal
from swingtrade.group4_email.parse import MessageIdentityRegistry, parse_email

__all__ = [
    "CALENDAR_ASSUMPTION",
    "EMAIL_RETENTION_POLICY",
    "EXIT_ALERT_PARSER",
    "FIXTURE_SIGNAL_MAILBOX",
    "QUANTITY_ROUNDING_POLICY",
    "SIGNAL_MAILBOX",
    "TIMEZONE_ASSUMPTION",
    "TRADE_AMENDMENT_PARSER",
    "Direction",
    "Disposition",
    "MessageIdentityRegistry",
    "MessageType",
    "OrderType",
    "ParseOutcome",
    "SessionEvent",
    "SiblingCancel",
    "TimeInForce",
    "TradeInstruction",
    "TriggerBasis",
    "economic_decimal",
    "parse_email",
]
