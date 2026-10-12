"""Synthetic tests for the non-economic disposition view."""

from __future__ import annotations

import ast
from dataclasses import fields, replace
from pathlib import Path

from swingtrade.group4_email.contract import Disposition, MessageType, ParseOutcome
from swingtrade.group4_email.disposition import (
    DispositionViewError,
    DispositionViewLabel,
    derive_disposition_view,
)
from swingtrade.group4_email.parse import MessageIdentityRegistry, parse_email
from tests.group4_email.conftest import body, plain_message

DATED = body("tday_dated.txt")
MODULE = Path("src/swingtrade/group4_email/disposition.py")
_BANNED = (
    "OrderIntent",
    "authorize_dispatch",
    "DryRunAdapter",
    "example_quantity",
    "socket",
    "ctypes",
    "advapi32",
    "psycopg",
    "sqlalchemy",
    "httpx",
    "urllib",
)


def _trade() -> ParseOutcome:
    return parse_email(plain_message(DATED, "<view-trade@example.invalid>"))


def _info() -> ParseOutcome:
    return parse_email(
        plain_message(
            "14 more swing orders remain behind the member notice.\n",
            "<view-info@example.invalid>",
        )
    )


def _code(outcome: ParseOutcome) -> str:
    try:
        derive_disposition_view(outcome)
    except DispositionViewError as error:
        return error.code
    raise AssertionError("expected fail closed")


def _snapshot(outcome: ParseOutcome) -> tuple[object, ...]:
    return (
        outcome.disposition,
        outcome.message_type,
        outcome.reasons,
        outcome.instructions,
        outcome.evidence,
        outcome.content_digest,
        outcome.message_id,
        outcome.provenance,
        outcome.ignored_remote_references,
        outcome.ignored_attachment_count,
        outcome.network_permitted,
    )


def test_recorded_new_trade_is_not_executable() -> None:
    outcome = _trade()
    view = derive_disposition_view(outcome)
    assert view.label is DispositionViewLabel.RECORDED_NOT_EXECUTABLE
    assert view.instruction_ids == (outcome.instructions[0].instruction_id,)
    assert view.label.name != "EXECUTABLE"
    assert "OrderIntent" not in repr(view)


def test_informational_accept_has_no_envelope() -> None:
    outcome = _info()
    view = derive_disposition_view(outcome)
    assert outcome.disposition is Disposition.ACCEPT
    assert outcome.message_type is MessageType.INFORMATIONAL
    assert outcome.instructions == ()
    assert view.label is DispositionViewLabel.INFORMATIONAL
    assert view.instruction_ids == ()


def test_malformed_mime_stays_rejected() -> None:
    raw = (
        b"Message-ID: <bad@example.invalid>\r\n"
        b"MIME-Version: 1.0\r\n"
        b'Content-Type: multipart/mixed; boundary="abc"\r\n'
        b"\r\n--abc\r\nContent-Type: text/plain\r\n\r\nhello\r\n"
    )
    outcome = parse_email(raw)
    view = derive_disposition_view(outcome)
    assert outcome.disposition is Disposition.REJECT
    assert view.label is DispositionViewLabel.REJECT
    assert view.reasons == ("MALFORMED_MIME",)


def test_deferred_amendment_exit_and_cancel() -> None:
    amendment = parse_email(
        plain_message(
            "Trade amendment: stop is now sell stop $6.00, good till cancelled.\n",
            "<view-amend@example.invalid>",
        )
    )
    exit_alert = parse_email(
        plain_message(
            "Exit alert: sell at the open Mon Nov 9, 2026.\n",
            "<view-exit@example.invalid>",
        )
    )
    cancel = parse_email(
        plain_message("Trade cancel: TDAY\n", "<view-cancel@example.invalid>")
    )
    assert derive_disposition_view(amendment).label is DispositionViewLabel.DEFERRED
    assert derive_disposition_view(exit_alert).label is DispositionViewLabel.DEFERRED
    assert amendment.reasons == ("PARSER_DEFERRED",)
    assert exit_alert.reasons == ("PARSER_DEFERRED",)
    assert "CANCEL_FORMAT_UNSPECIFIED" in cancel.reasons
    assert derive_disposition_view(cancel).label is DispositionViewLabel.DEFERRED


def test_conflicting_duplicate_stays_quarantined() -> None:
    registry = MessageIdentityRegistry()
    first = registry.parse(plain_message(DATED, "<view-conflict@example.invalid>"))
    second = registry.parse(
        plain_message(DATED + "\nUnrelated tail.\n", "<view-conflict@example.invalid>")
    )
    view = derive_disposition_view(second)
    assert first.disposition is Disposition.ACCEPT
    assert second.reasons == ("CONFLICTING_DUPLICATE",)
    assert view.label is DispositionViewLabel.QUARANTINED
    assert view.label is not DispositionViewLabel.DUPLICATE


def test_registry_replay_is_not_labeled_duplicate() -> None:
    registry = MessageIdentityRegistry()
    raw = plain_message(DATED, "<view-replay@example.invalid>")
    first = registry.parse(raw)
    replay = registry.parse(raw)
    assert derive_disposition_view(first) == derive_disposition_view(replay)
    assert derive_disposition_view(replay).label is not DispositionViewLabel.DUPLICATE
    fresh = parse_email(raw)
    assert derive_disposition_view(fresh).label is DispositionViewLabel.RECORDED_NOT_EXECUTABLE


def test_equal_outcomes_are_not_inferred_duplicates() -> None:
    outcome = _trade()
    again = replace(outcome)
    assert derive_disposition_view(outcome).label is DispositionViewLabel.RECORDED_NOT_EXECUTABLE
    assert derive_disposition_view(again).label is DispositionViewLabel.RECORDED_NOT_EXECUTABLE


def test_unknown_disposition_fails_closed() -> None:
    outcome = _info()
    object.__setattr__(outcome, "disposition", "NOPE")
    assert _code(outcome) == "invalid_disposition"
    assert "NOPE" not in DispositionViewError("invalid_disposition").__str__()


def test_unsupported_message_type_fails_closed() -> None:
    outcome = replace(_info(), message_type=MessageType.TRADE_AMENDMENT)
    assert outcome.disposition is Disposition.ACCEPT
    assert _code(outcome) == "unsupported_combination"


def test_new_trade_without_envelope_fails_closed() -> None:
    outcome = replace(_trade(), instructions=())
    assert _code(outcome) == "missing_envelope"


def test_informational_with_envelope_fails_closed() -> None:
    trade = _trade()
    outcome = replace(_info(), instructions=trade.instructions)
    assert _code(outcome) == "unexpected_envelope"


def test_identical_inputs_yield_identical_views() -> None:
    outcome = _trade()
    assert derive_disposition_view(outcome) == derive_disposition_view(outcome)


def test_instruction_ids_and_provenance_are_unchanged() -> None:
    outcome = _trade()
    before_ids = tuple(item.instruction_id for item in outcome.instructions)
    before_provenance = outcome.provenance
    view = derive_disposition_view(outcome)
    assert view.instruction_ids == before_ids
    assert view.provenance is before_provenance
    assert view.provenance.retention_policy == "HASH_PROVIDER_REF_FIELD_EVIDENCE"
    assert view.content_digest == outcome.content_digest
    assert view.message_id == outcome.message_id


def test_outcome_and_envelopes_are_not_mutated() -> None:
    outcome = _trade()
    before = _snapshot(outcome)
    instruction = outcome.instructions[0]
    payload = instruction.payload
    derive_disposition_view(outcome)
    assert _snapshot(outcome) == before
    assert instruction.payload is payload


def test_view_does_not_project_quantity_or_order_intent() -> None:
    view = derive_disposition_view(_trade())
    names = {item.name for item in fields(view)}
    assert "example_quantity" not in names
    assert "payload" not in names
    assert "instructions" not in names
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = [
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    ]
    assert "OrderIntent" not in imported
    for token in _BANNED:
        assert token not in source


def test_duplicate_label_cannot_be_constructed() -> None:
    outcome = _trade()
    view = derive_disposition_view(outcome)
    try:
        object.__setattr__(view, "label", DispositionViewLabel.DUPLICATE)
        view.__post_init__()
    except DispositionViewError as error:
        assert error.code == "duplicate_unavailable"
    else:
        raise AssertionError("duplicate label accepted")


def test_module_has_no_service_boundary() -> None:
    source = MODULE.read_text(encoding="utf-8")
    for token in ("CredWriteW", "CredReadW", "gmail.googleapis.com", "postgresql"):
        assert token not in source
