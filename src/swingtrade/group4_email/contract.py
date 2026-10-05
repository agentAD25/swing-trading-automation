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
TRADE_CANCEL_PARSER = "DEFERRED_FIXTURE_REQUIRED"
QUANTITY_ROUNDING_POLICY = "UNRESOLVED"
# Operator decision: hash + provider retrieval reference + field-level evidence.
# The raw newsletter and a normalized body are not canonical ledger evidence.
EMAIL_RETENTION_POLICY = "HASH_PROVIDER_REF_FIELD_EVIDENCE"
PARSER_VERSION = "g4a.1"
SCHEMA_VERSION = "g4a.instruction.1"
TIMEZONE_ASSUMPTION = "UNSTATED"
CALENDAR_ASSUMPTION = "UNRESOLVED"
MAX_EMAIL_BYTES = 65536
MAX_EVIDENCE_CHARS = 240

RESOLUTION_EXPLICIT = "EXPLICIT_CIVIL_DATE"
RESOLUTION_UNRESOLVED = "UNRESOLVED_PARTIAL_DATE"
RESOLUTION_CONFLICT = "DATE_CONFLICT"
RESOLUTION_ABSENT = "NO_DATE_EXPRESSION"
RESOLUTION_MALFORMED = "MALFORMED_DATE"
RESOLUTION_UNSUPPORTED = "UNSUPPORTED_DATE_FORMAT"


class MessageType(StrEnum):
    NEW_TRADE = "NEW_TRADE"
    TRADE_AMENDMENT = "TRADE_AMENDMENT"
    EXIT_ALERT = "EXIT_ALERT"
    TRADE_CANCEL = "TRADE_CANCEL"
    INFORMATIONAL = "INFORMATIONAL"
    UNKNOWN = "UNKNOWN"


class ProviderType(StrEnum):
    """Offline fixture locator. This parser has no mailbox provider."""

    FIXTURE = "FIXTURE"


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
    UNSUPPORTED_DATE_FORMAT = "UNSUPPORTED_DATE_FORMAT"
    MALFORMED_DATE = "MALFORMED_DATE"
    AMBIGUOUS_VISIBILITY = "AMBIGUOUS_VISIBILITY"
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
class NewTradeInstruction:
    """Complete new-trade bracket. Other message types do not reuse this shape."""

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
class TradeAmendmentInstruction:
    """Reserved amendment payload. Group 4A accepts none of these."""

    evidence: tuple[FieldEvidence, ...] = ()


@dataclass(frozen=True)
class ExitAlertInstruction:
    """Reserved exit-alert payload. Group 4A accepts none of these."""

    evidence: tuple[FieldEvidence, ...] = ()


@dataclass(frozen=True)
class TradeCancelInstruction:
    """Reserved cancel payload. Group 4A accepts none of these."""

    evidence: tuple[FieldEvidence, ...] = ()


InstructionPayload = (
    NewTradeInstruction
    | TradeAmendmentInstruction
    | ExitAlertInstruction
    | TradeCancelInstruction
)


@dataclass(frozen=True)
class CanonicalInstructionEnvelope:
    """Source-neutral container. Payload type selects the economic shape.

    ``instruction_id`` is the deterministic economic identity. It is not the
    provider message reference.
    """

    instruction_id: str
    message_type: MessageType
    payload: InstructionPayload
    evidence: tuple[FieldEvidence, ...]

    def __getattr__(self, name: str) -> object:
        return getattr(self.payload, name)


@dataclass(frozen=True)
class ParseProvenance:
    """Retention record: hash, provider locator, and versions. Not a body store."""

    retention_policy: str
    provider_type: str
    provider_message_ref: str | None
    raw_sha256: str
    parser_version: str
    schema_version: str
    source_timestamp: str | None


@dataclass(frozen=True)
class ParseOutcome:
    disposition: Disposition
    message_type: MessageType
    reasons: tuple[str, ...]
    instructions: tuple[CanonicalInstructionEnvelope, ...]
    evidence: tuple[FieldEvidence, ...]
    content_digest: str
    message_id: str | None
    provenance: ParseProvenance
    ignored_remote_references: int = 0
    ignored_attachment_count: int = 0
    network_permitted: bool = False

    def __post_init__(self) -> None:
        if self.network_permitted:
            raise RuntimeError("network is not permitted")
        if self.disposition is not Disposition.ACCEPT and self.instructions:
            raise RuntimeError("only an accepted message may carry instructions")
        if self.provenance.retention_policy != EMAIL_RETENTION_POLICY:
            raise RuntimeError("retention policy is fixed")
        for instruction in self.instructions:
            if instruction.instruction_id == self.provenance.provider_message_ref:
                raise RuntimeError("provider reference is not instruction identity")
