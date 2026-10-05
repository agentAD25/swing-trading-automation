"""Regression coverage for the seven Group 4A remediation findings."""

from __future__ import annotations

import threading
from datetime import date
from decimal import Decimal
from email.message import EmailMessage

import pytest

from swingtrade.domain import Side
from swingtrade.group4_email import (
    EMAIL_RETENTION_POLICY,
    PARSER_VERSION,
    SCHEMA_VERSION,
    CanonicalInstructionEnvelope,
    Disposition,
    ExitAlertInstruction,
    MessageIdentityRegistry,
    MessageType,
    NewTradeInstruction,
    TradeAmendmentInstruction,
    TradeCancelInstruction,
    parse_email,
)
from swingtrade.group4_email import extract as extract_mod
from swingtrade.group4_email import parse as parse_mod
from tests.group4_email.conftest import MAILBOX, body, plain_message
from tests.group4_email.test_attacks import _alternative, _html_only, _minimal

DATED = body("tday_dated.txt")


def test_chart_date_does_not_bind_entry() -> None:
    text = DATED.replace(
        "Entry: Buy stop $7.23, day order. Fills only if TDAY trades up to $7.23 on "
        "Monday 2026-11-02. If not filled by Monday's close, it expires.",
        "Entry: Buy stop $7.23, day order. Historical chart marks 2024-06-03. "
        "Fills only if TDAY trades up to $7.23 on Monday.",
    )
    outcome = parse_email(plain_message(text, "<chart@example.invalid>"))
    assert outcome.disposition is Disposition.QUARANTINE
    assert outcome.instructions == ()
    assert "UNRESOLVED_REQUIRED_DATE" in outcome.reasons
    assert all("2024-06-03" not in item.source_text for item in outcome.evidence)


def test_disclaimer_date_does_not_bind_time_exit() -> None:
    text = DATED.replace("Mon Nov 9, 2026", "Monday") + "\nDisclaimer chart anchor 2024-11-04.\n"
    outcome = parse_email(plain_message(text, "<disc@example.invalid>"))
    assert outcome.disposition is Disposition.QUARANTINE
    assert outcome.instructions == ()
    assert "UNRESOLVED_REQUIRED_DATE" in outcome.reasons
    assert all("2024-11-04" not in item.source_text for item in outcome.evidence)


def test_numeric_dates_quarantine_instead_of_disappearing() -> None:
    text = """Symbol: TDAY
Entry: Buy stop $7.23, day order. Fills on 11/02/2026.
Sizing: about 5% of account. Example: $10,000 account, $500 allocation, 69 shares.
Target: sell limit $9.01, good till cancelled.
Stop: sell stop $6.54, good till cancelled. The stop is a real order.
Time exit: sell at the open 11/09/2026.
Whichever exit comes first closes the trade. After target or stop fill, cancel the other.
"""
    outcome = parse_email(plain_message(text, "<num@example.invalid>"))
    assert outcome.disposition is Disposition.QUARANTINE
    assert outcome.instructions == ()
    assert "UNSUPPORTED_DATE_FORMAT" in outcome.reasons
    cited = " ".join(item.source_text for item in outcome.evidence)
    assert "11/02/2026" in cited or "11/09/2026" in cited


def test_iso_timestamp_does_not_disappear() -> None:
    text = DATED.replace(
        "Entry: Buy stop $7.23, day order. Fills only if TDAY trades up to $7.23 on "
        "Monday 2026-11-02. If not filled by Monday's close, it expires.",
        "Entry: Buy stop $7.23, day order. Session 2026-11-02T00:30:00-04:00.",
    )
    outcome = parse_email(plain_message(text, "<ts@example.invalid>"))
    assert outcome.disposition is Disposition.QUARANTINE
    assert outcome.instructions == ()
    assert "UNSUPPORTED_DATE_FORMAT" in outcome.reasons
    assert any("2026-11-02T00:30:00-04:00" in item.source_text for item in outcome.evidence)


def test_plain_html_economic_disagreements_quarantine() -> None:
    cases = (
        ("Target: sell limit $9.01", "Target: buy limit $9.01", "<side@example.invalid>"),
        ("sell stop $6.54", "buy stop $6.54", "<pside@example.invalid>"),
        (
            "Target: sell limit $9.01, good till cancelled.",
            "Target: sell limit $9.01, good till cancelled. Monday 2026-12-07.",
            "<tdate@example.invalid>",
        ),
        (
            "Target: sell limit $9.01, good till cancelled.",
            "Target: sell stop limit $9.01 limit $8.50, good till cancelled.",
            "<tlim@example.invalid>",
        ),
        (
            "Stop: sell stop $6.54, good till cancelled.",
            "Stop: sell stop limit $6.54 limit $6.10, good till cancelled.",
            "<slim@example.invalid>",
        ),
    )
    for plain_token, html_token, message_id in cases:
        html = "<html><body>" + DATED.replace(plain_token, html_token).replace("\n", "<br>\n")
        html += "</body></html>"
        outcome = parse_email(_alternative(DATED, html, message_id))
        assert outcome.disposition is Disposition.QUARANTINE
        assert "HTML_PLAIN_CONFLICT" in outcome.reasons
        assert outcome.instructions == ()


def test_time_exit_side_disagreement_quarantines() -> None:
    plain = _minimal(entry="Buy stop $7.23, day order. Monday 2026-11-02.")
    html_body = _minimal(
        entry="Buy stop $7.23, day order. Monday 2026-11-02.",
        time_exit="buy at the open Mon Nov 9, 2026.",
    )
    html = "<html><body>" + html_body.replace("\n", "<br>\n") + "</body></html>"
    outcome = parse_email(_alternative(plain, html, "<txside@example.invalid>"))
    assert outcome.disposition is Disposition.QUARANTINE
    assert "HTML_PLAIN_CONFLICT" in outcome.reasons
    assert outcome.instructions == ()


def _hidden_case(marker: str) -> None:
    hidden_block = (
        f"<div {marker}>Symbol: EVIL<br>"
        "Entry: Buy limit $1.00, day order. Monday 2026-11-02.<br>"
        "Sizing: 5% of account.<br>"
        "Target: sell limit $2.00, good till cancelled.<br>"
        "Stop: sell stop $0.50, good till cancelled.<br>"
        "Time exit: sell at the open Mon Nov 9, 2026.<br>"
        "Whichever exit comes first closes the trade. "
        "After target or stop fill, cancel the other.<br>"
        + ("</div></div>" if "><" in marker else "</div>")
    )
    html = "<html><body>" + hidden_block + DATED.replace("\n", "<br>\n") + "</body></html>"
    outcome = parse_email(_html_only(html, "<hidden@example.invalid>"))
    assert outcome.disposition is Disposition.ACCEPT
    assert [item.symbol for item in outcome.instructions] == ["TDAY"]
    assert outcome.instructions[0].entry.price == Decimal("7.23")


def test_hidden_attribute_and_display_none_and_visibility() -> None:
    _hidden_case("hidden")
    _hidden_case('style="display:none"')
    _hidden_case('style="visibility: hidden"')
    _hidden_case('hidden><div style="display:none"')


def test_ambiguous_visibility_quarantines() -> None:
    html = (
        '<html><body><span style="display: mystery">Symbol: EVIL</span><br>'
        + DATED.replace("\n", "<br>\n")
        + "</body></html>"
    )
    outcome = parse_email(_html_only(html, "<ambig@example.invalid>"))
    assert outcome.disposition is Disposition.QUARANTINE
    assert outcome.reasons == ("AMBIGUOUS_VISIBILITY",)
    assert outcome.instructions == ()


def test_short_sell_at_open_quarantines_and_buy_at_open_accepts() -> None:
    common = dict(
        symbol="IBM",
        entry="Sell stop $20.00, day order. Fills on Monday 2026-11-02.",
        target="buy limit $18.00, good till cancelled.",
        stop="buy stop $21.50, good till cancelled. The stop is a real order.",
    )
    wrong = parse_email(
        plain_message(
            _minimal(**common, time_exit="sell at the open Mon Nov 9, 2026."),
            "<short-sell@example.invalid>",
        )
    )
    assert wrong.disposition is Disposition.QUARANTINE
    assert wrong.instructions == ()
    assert "CONFLICTING_ECONOMIC_INSTRUCTION" in wrong.reasons
    accepted = parse_email(
        plain_message(
            _minimal(**common, time_exit="buy at the open Mon Nov 9, 2026."),
            "<short-buy@example.invalid>",
        )
    )
    assert accepted.disposition is Disposition.ACCEPT
    instruction = accepted.instructions[0]
    assert isinstance(instruction.payload, NewTradeInstruction)
    assert instruction.payload.direction.value == "SHORT"
    assert instruction.payload.time_exit is not None
    assert instruction.payload.time_exit.side is Side.BUY
    assert instruction.payload.time_exit.resolved_date == date(2026, 11, 9)


def test_deferred_labels_and_unlabeled_prose_emit_no_payload() -> None:
    samples = (
        (
            "Trade amendment: stop is now sell stop $6.00, good till cancelled.\n",
            MessageType.TRADE_AMENDMENT,
            "PARSER_DEFERRED",
        ),
        (
            "Exit alert: sell at the open Mon Nov 9, 2026.\n",
            MessageType.EXIT_ALERT,
            "PARSER_DEFERRED",
        ),
        (
            "Trade cancel: TDAY\n",
            MessageType.TRADE_CANCEL,
            "CANCEL_FORMAT_UNSPECIFIED",
        ),
        ("Please amend TDAY stop to 6.00 tonight.\n", MessageType.INFORMATIONAL, None),
        ("Exit the TDAY position at the open.\n", MessageType.INFORMATIONAL, None),
        ("Cancel the TDAY order.\n", MessageType.INFORMATIONAL, None),
    )
    for text, message_type, reason in samples:
        outcome = parse_email(plain_message(text, f"<{message_type.value}@example.invalid>"))
        assert outcome.message_type is message_type
        assert outcome.instructions == ()
        if reason is None:
            assert outcome.disposition is Disposition.ACCEPT
        else:
            assert outcome.disposition is Disposition.QUARANTINE
            assert reason in outcome.reasons


def test_reserved_payloads_do_not_require_a_new_trade_bracket() -> None:
    amendment = TradeAmendmentInstruction()
    exit_alert = ExitAlertInstruction()
    cancel = TradeCancelInstruction()
    for payload, message_type in (
        (amendment, MessageType.TRADE_AMENDMENT),
        (exit_alert, MessageType.EXIT_ALERT),
        (cancel, MessageType.TRADE_CANCEL),
    ):
        envelope = CanonicalInstructionEnvelope(
            instruction_id="v1:email_instruction:fixture:0",
            message_type=message_type,
            payload=payload,
            evidence=(),
        )
        assert envelope.payload is payload
        assert not isinstance(envelope.payload, NewTradeInstruction)
        assert not hasattr(payload, "entry")


def test_duplicated_dated_fixture_parses_two_instructions() -> None:
    text = DATED + "\n" + DATED
    outcome = parse_email(plain_message(text, "<dup@example.invalid>"))
    assert outcome.disposition is Disposition.ACCEPT
    assert [item.symbol for item in outcome.instructions] == ["TDAY", "TDAY"]
    assert [item.entry.price for item in outcome.instructions] == [Decimal("7.23"), Decimal("7.23")]
    assert [item.instruction_id.rsplit(":", 1)[-1] for item in outcome.instructions] == ["0", "1"]
    exits = [item.time_exit for item in outcome.instructions]
    assert all(item is not None and item.resolved_date == date(2026, 11, 9) for item in exits)


def test_outlook_original_message_is_not_a_second_trade() -> None:
    historical = """
-----Original Message-----
From: old@example.invalid
Sent: Monday, November 2, 2026 9:00 AM

Symbol: EVIL
Entry: Buy limit $1.00, day order. Monday 2026-11-02.
Sizing: 5% of account.
Target: sell limit $2.00, good till cancelled.
Stop: sell stop $0.50, good till cancelled.
Time exit: sell at the open Mon Nov 9, 2026.
Whichever exit comes first closes the trade. After target or stop fill, cancel the other.
"""
    outcome = parse_email(plain_message(DATED + historical, "<outlook@example.invalid>"))
    assert outcome.disposition is Disposition.ACCEPT
    assert [item.symbol for item in outcome.instructions] == ["TDAY"]
    assert outcome.instructions[0].entry.price == Decimal("7.23")


def test_retention_record_is_hash_locator_and_field_evidence(dated_raw: bytes) -> None:
    tracked = "Tracking https://example.invalid/pixel?id=1 unsubscribe here.\n" + DATED
    raw = plain_message(tracked, "<tday-dated@example.invalid>")
    outcome = parse_email(raw)
    assert EMAIL_RETENTION_POLICY == "HASH_PROVIDER_REF_FIELD_EVIDENCE"
    provenance = outcome.provenance
    assert provenance.retention_policy == EMAIL_RETENTION_POLICY
    assert provenance.provider_type == "FIXTURE"
    assert provenance.provider_message_ref == "<tday-dated@example.invalid>"
    assert provenance.raw_sha256 == outcome.content_digest
    assert len(provenance.raw_sha256) == 64
    assert provenance.parser_version == PARSER_VERSION
    assert provenance.schema_version == SCHEMA_VERSION
    instruction = outcome.instructions[0]
    assert isinstance(instruction.payload, NewTradeInstruction)
    assert instruction.instruction_id != provenance.provider_message_ref
    assert provenance.provider_message_ref not in instruction.instruction_id
    assert instruction.evidence
    blob = " ".join(item.source_text for item in instruction.evidence)
    assert "https://example.invalid" not in blob
    assert "unsubscribe" not in blob
    assert "Last price" not in blob
    assert not hasattr(outcome, "raw_body")
    assert dated_raw not in outcome.__dict__.values()


def test_source_timestamp_is_provenance_only() -> None:
    message = EmailMessage()
    message["Message-ID"] = "<stamp@example.invalid>"
    message["From"] = MAILBOX
    message["To"] = MAILBOX
    message["Date"] = "Mon, 01 Nov 2026 00:30:00 -0400"
    message["Subject"] = "Published Monday 2026-10-26"
    message.set_content(DATED)
    outcome = parse_email(message.as_bytes())
    assert outcome.disposition is Disposition.ACCEPT
    assert outcome.instructions[0].entry.session_date == date(2026, 11, 2)
    assert outcome.instructions[0].time_exit is not None
    assert outcome.instructions[0].time_exit.resolved_date == date(2026, 11, 9)
    assert outcome.provenance.source_timestamp == "2026-11-01T04:30:00Z"
    assert outcome.provenance.provider_message_ref == "<stamp@example.invalid>"


def test_concurrent_distinct_bodies_admit_neither(
    monkeypatch: pytest.MonkeyPatch,
    dated_raw: bytes,
) -> None:
    real = extract_mod.extract_text

    def gated(text: str) -> object:
        gate.wait()
        return real(text)

    for _ in range(12):
        gate = threading.Barrier(2)
        monkeypatch.setattr(parse_mod, "extract_text", gated)
        registry = MessageIdentityRegistry()
        other = dated_raw.replace(b"$9.01", b"$8.00")
        results: list[object] = []

        def run(
            raw: bytes,
            registry: MessageIdentityRegistry = registry,
            found: list[object] = results,
        ) -> None:
            found.append(registry.parse(raw))

        threads = [
            threading.Thread(target=run, args=(dated_raw,)),
            threading.Thread(target=run, args=(other,)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        monkeypatch.setattr(parse_mod, "extract_text", real)
        assert len(results) == 2
        for item in results:
            assert item.disposition is Disposition.QUARANTINE  # type: ignore[attr-defined]
            assert item.reasons == ("CONFLICTING_DUPLICATE",)  # type: ignore[attr-defined]
            assert item.instructions == ()  # type: ignore[attr-defined]
        assert len(registry) == 0
        replay = registry.parse(dated_raw)
        assert replay.disposition is Disposition.QUARANTINE
        assert replay.instructions == ()


def test_concurrent_identical_bodies_reuse_one_outcome(
    monkeypatch: pytest.MonkeyPatch,
    dated_raw: bytes,
) -> None:
    real = extract_mod.extract_text
    gate = threading.Barrier(2)

    def gated(text: str) -> object:
        gate.wait()
        return real(text)

    monkeypatch.setattr(parse_mod, "extract_text", gated)
    registry = MessageIdentityRegistry()
    results: list[object] = []

    def run() -> None:
        results.append(registry.parse(dated_raw))

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert results[0] is results[1]
    assert results[0].disposition is Disposition.ACCEPT  # type: ignore[attr-defined]
    assert len(registry) == 1
    assert results[0].instructions[0].entry.price == Decimal("7.23")  # type: ignore[attr-defined]
