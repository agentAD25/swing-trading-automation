"""Bounded RFC Message-ID classification. Receipt keys stay fixture-only."""

from __future__ import annotations

from swingtrade.group4_email.normalize import (
    _FIXTURE_MESSAGE_ID,
    classify_message_id,
    message_id_classification,
    recognized_message_id,
)
from swingtrade.group4_email.parse import parse_email
from tests.group4_email.conftest import body, plain_message


def test_fixture_identity_remains_distinct_from_a_recognized_header() -> None:
    fixture = "<pilot-success@example.invalid>"
    recognized = "<abc123+tag@mail.example.com>"

    assert classify_message_id(fixture) == "FIXTURE"
    assert classify_message_id(recognized) == "RECOGNIZED"
    assert recognized_message_id(recognized) == recognized
    assert _FIXTURE_MESSAGE_ID.fullmatch(recognized) is None


def test_missing_malformed_and_adversarial_ids_are_not_retained() -> None:
    injected = "<abc123@mail.example.com>\r\nBcc: person@mail.example.com"
    huge = "<" + ("a" * 300) + "@mail.example.com>"

    assert classify_message_id(None) == "MISSING"
    assert classify_message_id("   ") == "MISSING"
    assert classify_message_id("<missing-at.example.com>") == "MALFORMED"
    assert classify_message_id("<a@b>") == "MALFORMED"
    assert classify_message_id(injected) == "MALFORMED"
    assert classify_message_id(huge) == "MALFORMED"
    assert recognized_message_id(injected) is None
    assert recognized_message_id(123) is None


def test_recognized_header_does_not_become_an_economic_message_id() -> None:
    raw = plain_message(body("tday_dated.txt"), "<abc123+tag@mail.example.com>")
    kind, token = message_id_classification(raw)
    outcome = parse_email(raw)

    assert kind == "RECOGNIZED"
    assert token == "<abc123+tag@mail.example.com>"
    assert outcome.message_id is None
    assert outcome.disposition.value == "QUARANTINE"
    assert "NON_FIXTURE_MESSAGE_ID" in outcome.reasons
    assert outcome.instructions == ()
    assert token not in repr(outcome)
    assert outcome.provenance.provider_message_ref is None
