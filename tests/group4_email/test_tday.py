"""TDAY new-trade contract. Dates resolve only from explicit civil dates."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from swingtrade.domain import Side
from swingtrade.group4_email import (
    CALENDAR_ASSUMPTION,
    EMAIL_RETENTION_POLICY,
    EXIT_ALERT_PARSER,
    QUANTITY_ROUNDING_POLICY,
    SIGNAL_MAILBOX,
    TIMEZONE_ASSUMPTION,
    TRADE_AMENDMENT_PARSER,
    Direction,
    Disposition,
    MessageIdentityRegistry,
    MessageType,
    OrderType,
    SessionEvent,
    SiblingCancel,
    TimeInForce,
    TriggerBasis,
    parse_email,
)


def test_signal_mailbox_is_a_name_and_retention_is_unresolved() -> None:
    assert SIGNAL_MAILBOX == "SIGNAL_MAILBOX"
    assert EMAIL_RETENTION_POLICY == "HASH_PROVIDER_REF_FIELD_EVIDENCE"
    assert TRADE_AMENDMENT_PARSER == "DEFERRED_FIXTURE_REQUIRED"
    assert EXIT_ALERT_PARSER == "DEFERRED_FIXTURE_REQUIRED"
    assert QUANTITY_ROUNDING_POLICY == "UNRESOLVED"


def test_dated_tday_accepts_the_canonical_instruction(dated_raw: bytes) -> None:
    outcome = parse_email(dated_raw)
    assert outcome.disposition is Disposition.ACCEPT
    assert outcome.message_type is MessageType.NEW_TRADE
    assert outcome.network_permitted is False
    assert outcome.reasons == ()
    assert len(outcome.instructions) == 1
    instruction = outcome.instructions[0]
    assert instruction.symbol == "TDAY"
    assert instruction.company_name == "USA TODAY"
    assert instruction.strategy_label == "Bull-Flag Momentum"
    assert instruction.direction is Direction.LONG
    assert instruction.message_type is MessageType.NEW_TRADE
    assert instruction.entry.side is Side.BUY
    assert instruction.entry.order_type is OrderType.STOP
    assert instruction.entry.price == Decimal("7.23")
    assert instruction.entry.time_in_force is TimeInForce.DAY
    assert instruction.entry.trigger_basis is TriggerBasis.BROKER_PRICE_ORDER
    assert instruction.entry.session_date == date(2026, 11, 2)
    assert instruction.entry.date_resolution_rule == "EXPLICIT_CIVIL_DATE"
    assert instruction.entry.timezone_assumption == TIMEZONE_ASSUMPTION
    assert instruction.entry.calendar_assumption == CALENDAR_ASSUMPTION
    assert instruction.sizing.method == "PERCENT_EQUITY"
    assert instruction.sizing.percent_equity == Decimal("0.05")
    assert instruction.sizing.example_account_equity == Decimal("10000")
    assert instruction.sizing.example_allocation == Decimal("500")
    assert instruction.sizing.example_quantity == Decimal("69")
    assert instruction.sizing.quantity_rounding_policy == "UNRESOLVED"
    assert instruction.target.side is Side.SELL
    assert instruction.target.order_type is OrderType.LIMIT
    assert instruction.target.price == Decimal("9.01")
    assert instruction.target.time_in_force is TimeInForce.GTC
    assert instruction.protective_stop.side is Side.SELL
    assert instruction.protective_stop.order_type is OrderType.STOP
    assert instruction.protective_stop.price == Decimal("6.54")
    assert instruction.protective_stop.time_in_force is TimeInForce.GTC
    assert instruction.protective_stop.trigger_basis is TriggerBasis.BROKER_PRICE_ORDER
    assert instruction.time_exit is not None
    assert instruction.time_exit.side is Side.SELL
    assert instruction.time_exit.session_event is SessionEvent.REGULAR_SESSION_OPEN
    assert instruction.time_exit.resolved_date == date(2026, 11, 9)
    assert instruction.time_exit.source_date == "Mon Nov 9, 2026"
    assert instruction.first_exit_wins is True
    assert instruction.sibling_cancel is SiblingCancel.SIBLING_CANCEL_REQUIRED
    cited = {item.field: item.source_text for item in instruction.evidence}
    assert cited["entry.price"] == "7.23"
    assert cited["protective_stop.trigger_basis"] == "BROKER_PRICE_ORDER"
    assert "7.05" not in cited.values()
    assert all("2024" not in item.source_text for item in instruction.evidence)


def test_undated_tday_quarantines_unresolved_dates(undated_raw: bytes) -> None:
    outcome = parse_email(undated_raw)
    assert outcome.disposition is Disposition.QUARANTINE
    assert outcome.message_type is MessageType.NEW_TRADE
    assert outcome.instructions == ()
    assert "UNRESOLVED_REQUIRED_DATE" in outcome.reasons
    fields = {item.field for item in outcome.evidence}
    assert "entry.session_date" in fields
    assert "time_exit.session_date" in fields
    assert all(item.source_text != "2024" for item in outcome.evidence)


def test_same_message_twice_is_one_instruction(dated_raw: bytes) -> None:
    registry = MessageIdentityRegistry()
    first = registry.parse(dated_raw)
    second = registry.parse(dated_raw)
    assert first is second
    assert len(registry) == 1
    assert len(first.instructions) == 1


def test_distinct_message_ids_do_not_collapse_matching_economics(dated_raw: bytes) -> None:
    registry = MessageIdentityRegistry()
    first = registry.parse(dated_raw)
    other = dated_raw.replace(
        b"<tday-dated@example.invalid>",
        b"<tday-copy@example.invalid>",
    )
    second = registry.parse(other)
    assert len(registry) == 2
    assert first.instructions[0].instruction_id != second.instructions[0].instruction_id
    assert first.instructions[0].entry.price == second.instructions[0].entry.price


def test_changed_content_under_one_message_id_does_not_collapse(dated_raw: bytes) -> None:
    registry = MessageIdentityRegistry()
    original = registry.parse(dated_raw)
    changed = dated_raw.replace(b"$7.23", b"$7.50")
    conflict = registry.parse(changed)
    assert conflict.disposition is Disposition.QUARANTINE
    assert conflict.reasons == ("CONFLICTING_DUPLICATE",)
    assert conflict.instructions == ()
    replay = registry.parse(dated_raw)
    assert replay is original
    assert len(registry) == 1
    assert original.instructions[0].entry.price == Decimal("7.23")
