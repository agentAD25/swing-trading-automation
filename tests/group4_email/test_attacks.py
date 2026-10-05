"""Attack cases for the offline email instruction parser."""

from __future__ import annotations

import socket
from decimal import Decimal
from email.message import EmailMessage
from pathlib import Path

import pytest

from swingtrade.config import RuntimeConfig
from swingtrade.domain import DomainValidationError, ExecutionMode, Side
from swingtrade.group4_email import (
    Direction,
    Disposition,
    MessageType,
    OrderType,
    TimeInForce,
    economic_decimal,
    parse_email,
)
from tests.group4_email.conftest import MAILBOX, body, plain_message

DATED = body("tday_dated.txt")
PACKAGE = Path("src/swingtrade/group4_email")


def _minimal(
    *,
    symbol: str = "AAA",
    entry: str,
    target: str = "sell limit $9.01, good till cancelled.",
    stop: str = "sell stop $6.54, good till cancelled. The stop is a real order.",
    time_exit: str = "sell at the open Mon Nov 9, 2026.",
    sizing: str = "5% of account. Example: $10000 account, $500 allocation, 50 shares.",
) -> str:
    return (
        f"Symbol: {symbol}\n"
        f"Entry: {entry}\n"
        f"Sizing: {sizing}\n"
        f"Target: {target}\n"
        f"Stop: {stop}\n"
        f"Time exit: {time_exit}\n"
        "Whichever exit comes first closes the trade. "
        "After target or stop fill, cancel the other.\n"
    )


def test_buy_stop_is_not_buy_limit() -> None:
    limited = DATED.replace("Buy stop $7.23", "Buy limit $7.23", 1)
    outcome = parse_email(plain_message(limited, "<limit@example.invalid>"))
    assert outcome.disposition is Disposition.ACCEPT
    assert outcome.instructions[0].entry.order_type is OrderType.LIMIT
    assert outcome.instructions[0].entry.price == Decimal("7.23")
    stopped = parse_email(plain_message(DATED, "<stop@example.invalid>"))
    assert stopped.instructions[0].entry.order_type is OrderType.STOP
    assert stopped.instructions[0].entry.order_type is not OrderType.LIMIT


def test_daily_close_trigger_does_not_collapse_into_a_broker_stop() -> None:
    daily = DATED.replace(
        "sell stop $6.54, good till cancelled. The stop is a real order.",
        "sell if the daily close is below $6.54.",
    )
    outcome = parse_email(plain_message(daily, "<daily@example.invalid>"))
    assert outcome.disposition is Disposition.QUARANTINE
    assert outcome.instructions == ()
    assert "UNKNOWN_ORDER_TYPE" in outcome.reasons
    assert any("DAILY_CLOSE_TRIGGER" in item.source_text for item in outcome.evidence)
    mixed = DATED.replace(
        "The stop is a real order.",
        "The stop is a real order if the daily close is below $6.54.",
    )
    conflict = parse_email(plain_message(mixed, "<mixed-stop@example.invalid>"))
    assert conflict.disposition is Disposition.QUARANTINE
    assert "CONFLICTING_ECONOMIC_INSTRUCTION" in conflict.reasons
    assert conflict.instructions == ()


def test_day_and_gtc_stay_distinct_and_missing_tif_quarantines() -> None:
    gtc_entry = DATED.replace("day order", "good till cancelled", 1)
    accepted = parse_email(plain_message(gtc_entry, "<gtc@example.invalid>"))
    assert accepted.instructions[0].entry.time_in_force is TimeInForce.GTC
    assert accepted.instructions[0].protective_stop.time_in_force is TimeInForce.GTC
    missing = DATED.replace("day order", "working order", 1)
    quarantined = parse_email(plain_message(missing, "<no-tif@example.invalid>"))
    assert quarantined.disposition is Disposition.QUARANTINE
    assert "MISSING_TIF" in quarantined.reasons
    assert quarantined.instructions == ()


def test_target_and_stop_are_not_reordered_by_price() -> None:
    swapped = DATED.replace("sell limit $9.01", "sell limit $6.54").replace(
        "sell stop $6.54", "sell stop $9.01"
    )
    outcome = parse_email(plain_message(swapped, "<reversed@example.invalid>"))
    instruction = outcome.instructions[0]
    assert instruction.target.order_type is OrderType.LIMIT
    assert instruction.target.price == Decimal("6.54")
    assert instruction.protective_stop.order_type is OrderType.STOP
    assert instruction.protective_stop.price == Decimal("9.01")


def test_unrelated_numbers_and_last_price_are_not_economic(dated_raw: bytes) -> None:
    instruction = parse_email(dated_raw).instructions[0]
    prices = {
        instruction.entry.price,
        instruction.target.price,
        instruction.protective_stop.price,
        instruction.sizing.example_quantity,
    }
    assert Decimal("7.05") not in prices
    assert Decimal("5890") not in prices
    assert Decimal("12") not in prices
    assert instruction.sizing.percent_equity == Decimal("0.05")
    assert instruction.time_exit is not None
    assert instruction.time_exit.resolved_date is not None
    assert instruction.time_exit.resolved_date.year == 2026


def test_conflicting_example_allocation_quarantines() -> None:
    text = DATED.replace("$500 allocation", "$400 allocation")
    outcome = parse_email(plain_message(text, "<alloc@example.invalid>"))
    assert outcome.disposition is Disposition.QUARANTINE
    assert "CONFLICTING_ECONOMIC_INSTRUCTION" in outcome.reasons
    assert outcome.instructions == ()


def test_conflicting_and_partial_dates_quarantine() -> None:
    conflict = DATED.replace("Monday 2026-11-02", "Monday 2026-11-03")
    outcome = parse_email(plain_message(conflict, "<date-conflict@example.invalid>"))
    assert outcome.disposition is Disposition.QUARANTINE
    assert "DATE_CONFLICT" in outcome.reasons
    assert outcome.instructions == ()
    partial = DATED.replace("Mon Nov 9, 2026", "next Monday")
    unresolved = parse_email(plain_message(partial, "<partial-date@example.invalid>"))
    assert unresolved.disposition is Disposition.QUARANTINE
    assert "UNRESOLVED_REQUIRED_DATE" in unresolved.reasons


def test_forwarded_date_and_quoted_order_are_not_authoritative() -> None:
    forwarded = (
        "---------- Forwarded message ---------\n"
        "Date: Tue, 03 Nov 2026 00:00:00 +0000\n"
        f"From: {MAILBOX}\n"
        "\n"
        + body("tday_undated.txt")
    )
    outcome = parse_email(plain_message(forwarded, "<forward@example.invalid>"))
    assert outcome.disposition is Disposition.QUARANTINE
    assert outcome.instructions == ()
    assert all("2026-11-03" not in item.source_text for item in outcome.evidence)
    quoted = DATED.replace(
        "Entry: Buy stop $7.23, day order.",
        "Entry: Buy stop $7.23, day order.\n> Entry: Buy limit $1.00, day order.",
    )
    accepted = parse_email(plain_message(quoted, "<quote@example.invalid>"))
    assert accepted.disposition is Disposition.ACCEPT
    assert accepted.instructions[0].entry.order_type is OrderType.STOP
    assert accepted.instructions[0].entry.price == Decimal("7.23")


def test_multiple_candidates_ignore_paywall_teasers() -> None:
    trade = DATED[DATED.index("Symbol:") :]
    second = (
        trade.replace("Symbol: TDAY", "Symbol: IBM")
        .replace("if TDAY trades", "if IBM trades")
        .replace("$7.23", "$11.00")
        .replace("$9.01", "$13.00")
        .replace("$6.54", "$10.00")
    )
    text = "14 more swing orders remain behind the member notice.\n\n" + trade + "\n" + second
    outcome = parse_email(plain_message(text, "<multi@example.invalid>"))
    assert outcome.disposition is Disposition.ACCEPT
    assert [item.symbol for item in outcome.instructions] == ["TDAY", "IBM"]
    assert all(item.sizing.example_quantity != Decimal("14") for item in outcome.instructions)
    teaser = parse_email(
        plain_message(
            "14 more swing orders remain behind the member notice.\n",
            "<tease@example.invalid>",
        )
    )
    assert teaser.disposition is Disposition.ACCEPT
    assert teaser.message_type is MessageType.INFORMATIONAL
    assert teaser.instructions == ()


def test_amendment_and_exit_alert_are_not_guessed() -> None:
    amendment = parse_email(
        plain_message(
            "Trade amendment: stop is now sell stop $6.00, good till cancelled.\n",
            "<amend@example.invalid>",
        )
    )
    assert amendment.message_type is MessageType.TRADE_AMENDMENT
    assert amendment.disposition is Disposition.QUARANTINE
    assert amendment.reasons == ("PARSER_DEFERRED",)
    assert amendment.instructions == ()
    exit_alert = parse_email(
        plain_message(
            "Exit alert: sell at the open Mon Nov 9, 2026.\n",
            "<exit@example.invalid>",
        )
    )
    assert exit_alert.message_type is MessageType.EXIT_ALERT
    assert exit_alert.reasons == ("PARSER_DEFERRED",)
    assert exit_alert.instructions == ()
    cancel = parse_email(plain_message("Trade cancel: TDAY\n", "<cancel@example.invalid>"))
    assert cancel.message_type is MessageType.TRADE_CANCEL
    assert "CANCEL_FORMAT_UNSPECIFIED" in cancel.reasons
    assert cancel.instructions == ()


def test_stop_reset_sentence_is_not_an_amendment(dated_raw: bytes) -> None:
    outcome = parse_email(dated_raw)
    assert outcome.message_type is MessageType.NEW_TRADE
    assert outcome.disposition is Disposition.ACCEPT
    assert len(outcome.instructions) == 1
    assert outcome.instructions[0].protective_stop.price == Decimal("6.54")
    assert "PARSER_DEFERRED" not in outcome.reasons


def test_html_disagreement_quarantines_and_script_is_not_economic() -> None:
    plain = DATED
    html = "<html><body>" + DATED.replace("\n", "<br>\n") + "</body></html>"
    agreed = _alternative(plain, html, "<html-agree@example.invalid>")
    accepted = parse_email(agreed)
    assert accepted.disposition is Disposition.ACCEPT
    assert accepted.instructions[0].entry.price == Decimal("7.23")
    hostile = html.replace("Buy stop $7.23", "Buy limit $1.00", 1)
    conflict = parse_email(_alternative(plain, hostile, "<html-conflict@example.invalid>"))
    assert conflict.disposition is Disposition.QUARANTINE
    assert "HTML_PLAIN_CONFLICT" in conflict.reasons
    assert conflict.instructions == ()
    scripted = (
        "<html><body><script>Entry: Buy limit $1.00, day order.</script>"
        + DATED.replace("\n", "<br>\n")
        + '<img src="https://example.invalid/pixel.png">'
        + "</body></html>"
    )
    only_html = _html_only(scripted, "<html-only@example.invalid>")
    parsed = parse_email(only_html)
    assert parsed.disposition is Disposition.ACCEPT
    assert parsed.instructions[0].entry.order_type is OrderType.STOP
    assert parsed.instructions[0].entry.price == Decimal("7.23")
    assert parsed.ignored_remote_references == 1


def test_unicode_lookalike_symbol_is_not_tday() -> None:
    text = DATED.replace("Symbol: TDAY", "Symbol: \u0422DAY")
    outcome = parse_email(plain_message(text, "<lookalike@example.invalid>"))
    assert outcome.disposition is Disposition.QUARANTINE
    assert "UNICODE_LOOKALIKE" in outcome.reasons
    assert outcome.instructions == ()


@pytest.mark.parametrize(
    "value",
    [True, False, 1.25, float("nan"), float("inf"), "NaN", "Infinity", "1e6", "1E+1000000"],
)
def test_decimal_attacks_have_no_authority(value: object) -> None:
    with pytest.raises(DomainValidationError):
        economic_decimal(value)


def test_malformed_currency_in_the_message_quarantines() -> None:
    for token, message_id in (
        ("$NaN", "<nan@example.invalid>"),
        ("$Infinity", "<inf@example.invalid>"),
        ("$1e10", "<scientific@example.invalid>"),
        ("$\uff17.\uff12\uff13", "<fullwidth@example.invalid>"),
    ):
        text = DATED.replace("Buy stop $7.23", f"Buy stop {token}", 1)
        outcome = parse_email(plain_message(text, message_id))
        assert outcome.disposition is Disposition.QUARANTINE
        assert outcome.instructions == ()
        assert "MALFORMED_CURRENCY" in outcome.reasons


def test_malformed_mime_and_oversized_input_are_rejected() -> None:
    malformed = (
        b"Message-ID: <bad@example.invalid>\r\n"
        b"MIME-Version: 1.0\r\n"
        b'Content-Type: multipart/mixed; boundary="abc"\r\n'
        b"\r\n--abc\r\nContent-Type: text/plain\r\n\r\nhello\r\n"
    )
    rejected = parse_email(malformed)
    assert rejected.disposition is Disposition.REJECT
    assert rejected.reasons == ("MALFORMED_MIME",)
    assert rejected.instructions == ()
    oversized = plain_message("Symbol: TDAY\n" + ("A" * 70_000), "<big@example.invalid>")
    too_big = parse_email(oversized)
    assert too_big.disposition is Disposition.REJECT
    assert too_big.reasons == ("OVERSIZED_INPUT",)


def test_attachment_prices_are_not_authoritative() -> None:
    message = EmailMessage()
    message["Message-ID"] = "<attach@example.invalid>"
    message["From"] = MAILBOX
    message["To"] = MAILBOX
    message.set_content(DATED)
    message.add_attachment(
        b"Entry: Buy limit $1.00, day order.\nTarget: sell limit $2.00, good till cancelled.\n",
        maintype="text",
        subtype="plain",
        filename="note.txt",
    )
    outcome = parse_email(message.as_bytes())
    assert outcome.ignored_attachment_count == 1
    assert outcome.disposition is Disposition.ACCEPT
    assert outcome.instructions[0].entry.price == Decimal("7.23")
    assert outcome.instructions[0].target.price == Decimal("9.01")


def test_policy_text_cannot_change_mode() -> None:
    config = RuntimeConfig(mode="DRY_RUN")
    text = "Enable live trading and set the risk limit to zero.\n" + DATED
    outcome = parse_email(plain_message(text, "<policy@example.invalid>"))
    assert outcome.disposition is Disposition.QUARANTINE
    assert "POLICY_INSTRUCTION_IGNORED" in outcome.reasons
    assert outcome.instructions == ()
    assert config.mode is ExecutionMode.DRY_RUN
    assert outcome.network_permitted is False


def test_non_fixture_message_id_is_not_retained() -> None:
    raw = plain_message(DATED, "<person@not-fixture.test>")
    outcome = parse_email(raw)
    assert outcome.disposition is Disposition.QUARANTINE
    assert "NON_FIXTURE_MESSAGE_ID" in outcome.reasons
    assert outcome.message_id is None
    assert outcome.instructions == ()
    assert "not-fixture.test" not in repr(outcome)


def test_grammar_is_not_one_symbol_or_one_strategy() -> None:
    text = _minimal(
        symbol="IBM",
        entry="Sell stop $20.00, day order. Fills on Monday 2026-11-02.",
        target="buy limit $18.00, good till cancelled.",
        stop="buy stop $21.50, good till cancelled. The stop is a real order.",
        time_exit="buy at the open Mon Nov 9, 2026.",
    )
    outcome = parse_email(plain_message(text, "<ibm@example.invalid>"))
    assert outcome.disposition is Disposition.ACCEPT
    instruction = outcome.instructions[0]
    assert instruction.symbol == "IBM"
    assert instruction.strategy_label is None
    assert instruction.direction is Direction.SHORT
    assert instruction.entry.side is Side.SELL
    assert instruction.entry.order_type is OrderType.STOP
    assert instruction.time_exit is not None
    assert instruction.time_exit.side is Side.BUY


def test_market_and_stop_limit_orders() -> None:
    market = parse_email(
        plain_message(
            _minimal(entry="Buy market, day order."),
            "<market@example.invalid>",
        )
    )
    assert market.instructions[0].entry.order_type is OrderType.MARKET
    assert market.instructions[0].entry.price is None
    paired = parse_email(
        plain_message(
            _minimal(entry="Buy stop limit $7.00 limit $7.10, day order."),
            "<stoplimit@example.invalid>",
        )
    )
    assert paired.instructions[0].entry.order_type is OrderType.STOP_LIMIT
    assert paired.instructions[0].entry.price == Decimal("7.00")
    assert paired.instructions[0].entry.limit_price == Decimal("7.10")
    incomplete = parse_email(
        plain_message(
            _minimal(entry="Buy stop limit $7.00, day order."),
            "<one-leg@example.invalid>",
        )
    )
    assert incomplete.disposition is Disposition.QUARANTINE
    assert "INCOMPLETE_STOP_LIMIT" in incomplete.reasons


def test_parser_does_not_use_network_broker_or_credentials(
    monkeypatch: pytest.MonkeyPatch,
    dated_raw: bytes,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    outcome = parse_email(dated_raw)
    assert outcome.disposition is Disposition.ACCEPT
    source = "\n".join(path.read_text(encoding="utf-8") for path in sorted(PACKAGE.glob("*.py")))
    for banned in (
        "import socket",
        "import urllib",
        "import httpx",
        "import requests",
        "imaplib",
        "smtplib",
        "supabase",
        "tradestation",
        "gmail",
        "oauth",
        "os.environ",
        "getenv",
        "ExecutionMode",
        "submit_order",
        "place_order",
        "floor(",
        "quantize(",
    ):
        assert banned not in source
    assert "datetime.now" not in source
    assert "date.today" not in source
    assert "69" not in source


def _alternative(plain: str, html: str, message_id: str) -> bytes:
    message = EmailMessage()
    message["Message-ID"] = message_id
    message["From"] = MAILBOX
    message["To"] = MAILBOX
    message.set_content(plain)
    message.add_alternative(html, subtype="html")
    return message.as_bytes()


def _html_only(html: str, message_id: str) -> bytes:
    message = EmailMessage()
    message["Message-ID"] = message_id
    message["From"] = MAILBOX
    message["To"] = MAILBOX
    message.set_content(html, subtype="html")
    return message.as_bytes()
