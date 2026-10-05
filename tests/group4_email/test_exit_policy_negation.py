"""Exit-policy negation is not the positive economic value."""

from __future__ import annotations

import pytest

from swingtrade.group4_email import Disposition, SiblingCancel, parse_email
from tests.group4_email.conftest import body, plain_message
from tests.group4_email.test_attacks import _alternative

DATED = body("tday_dated.txt")
_POLICY_LINE = (
    "Whichever exit comes first closes the trade. "
    "After target or stop fill, cancel the other. "
    "Before the time exit, cancel both outstanding exits."
)
_FIRST = "Whichever exit comes first closes the trade."
_SIBLING = "After target or stop fill, cancel the other."


def _policies(first: str, sibling: str) -> str:
    return DATED.replace(_POLICY_LINE, f"{first} {sibling}".strip())


def _html(text: str) -> str:
    return "<html><body>" + text.replace("\n", "<br>\n") + "</body></html>"


def _parse(text: str, message_id: str):
    return parse_email(plain_message(text, message_id))


def test_canonical_first_exit_phrase_is_true() -> None:
    outcome = _parse(DATED, "<first-positive@example.invalid>")
    assert outcome.disposition is Disposition.ACCEPT
    assert outcome.instructions[0].first_exit_wins is True


def test_canonical_sibling_phrase_is_required() -> None:
    text = _policies(
        _FIRST,
        "Once the target or the stop fills, cancel the other one.",
    )
    outcome = _parse(text, "<sibling-positive@example.invalid>")
    assert outcome.disposition is Disposition.ACCEPT
    assert outcome.instructions[0].sibling_cancel is SiblingCancel.SIBLING_CANCEL_REQUIRED
    assert outcome.instructions[0].first_exit_wins is True


def test_cancel_both_outstanding_exits_stays_required() -> None:
    text = _policies(_FIRST, "Before the time exit, cancel both outstanding exits.")
    outcome = _parse(text, "<sibling-both@example.invalid>")
    assert outcome.disposition is Disposition.ACCEPT
    assert outcome.instructions[0].sibling_cancel is SiblingCancel.SIBLING_CANCEL_REQUIRED


def test_remaining_positive_sibling_phrase_stays_required() -> None:
    text = DATED.replace("cancel the other.", "leave sibling working.")
    outcome = _parse(text, "<sibling-remain@example.invalid>")
    assert outcome.disposition is Disposition.ACCEPT
    assert outcome.instructions[0].sibling_cancel is SiblingCancel.SIBLING_CANCEL_REQUIRED


@pytest.mark.parametrize(
    ("sentence", "message_id"),
    [
        (
            "Not whichever exit comes first closes the trade.",
            "<first-not@example.invalid>",
        ),
        (
            "do not use whichever exit comes first",
            "<first-do-not@example.invalid>",
        ),
        (
            "whichever exit comes first does not close the trade",
            "<first-does-not@example.invalid>",
        ),
        (
            "whichever exit comes first will not close the trade",
            "<first-will-not@example.invalid>",
        ),
        (
            "it is not true that whichever exit comes first closes the trade",
            "<first-not-true@example.invalid>",
        ),
    ],
)
def test_first_exit_negation_does_not_accept(sentence: str, message_id: str) -> None:
    outcome = _parse(_policies(sentence, _SIBLING), message_id)
    assert outcome.disposition is Disposition.QUARANTINE
    assert outcome.instructions == ()
    assert "CONFLICTING_ECONOMIC_INSTRUCTION" in outcome.reasons
    assert "MISSING_EXIT_POLICY" not in outcome.reasons


@pytest.mark.parametrize(
    ("sentence", "message_id"),
    [
        ("do not cancel the other", "<sib-do-not@example.invalid>"),
        ("don't cancel the other", "<sib-dont@example.invalid>"),
        ("don’t cancel the other", "<sib-curly@example.invalid>"),
        ("never cancel the other", "<sib-never@example.invalid>"),
        ("cancel the other is not required", "<sib-not-required@example.invalid>"),
        (
            "the other order should not be cancelled",
            "<sib-should-not@example.invalid>",
        ),
        (
            "the other order should not be canceled",
            "<sib-canceled@example.invalid>",
        ),
    ],
)
def test_sibling_negation_is_not_required(sentence: str, message_id: str) -> None:
    outcome = _parse(_policies(_FIRST, sentence), message_id)
    assert outcome.disposition is Disposition.QUARANTINE
    assert outcome.instructions == ()
    assert "CONFLICTING_ECONOMIC_INSTRUCTION" in outcome.reasons
    accepted = [item.sibling_cancel for item in outcome.instructions]
    assert SiblingCancel.SIBLING_CANCEL_REQUIRED not in accepted


def test_negative_only_agreement_is_not_an_accepted_trade() -> None:
    text = _policies(
        "Not whichever exit comes first closes the trade.",
        "do not cancel the other.",
    )
    outcome = parse_email(_alternative(text, _html(text), "<both-neg@example.invalid>"))
    assert outcome.disposition is Disposition.QUARANTINE
    assert outcome.instructions == ()
    assert "CONFLICTING_ECONOMIC_INSTRUCTION" in outcome.reasons
    assert outcome.disposition is not Disposition.ACCEPT


def test_later_negation_beyond_the_prefix_radius_fails_closed() -> None:
    filler = "The broker handles the working orders. " * 8
    text = DATED.replace(
        _POLICY_LINE,
        _POLICY_LINE + " " + filler + "This does not apply.",
    )
    outcome = _parse(text, "<later-cue@example.invalid>")
    assert outcome.disposition is Disposition.QUARANTINE
    assert "CONFLICTING_ECONOMIC_INSTRUCTION" in outcome.reasons
    assert outcome.instructions == ()


def test_nearby_followup_negation_is_not_affirmation() -> None:
    first = _policies(
        "Whichever exit comes first closes the trade. This does not close the trade.",
        _SIBLING,
    )
    sibling = _policies(
        _FIRST,
        "Cancel the other. This order should not be cancelled.",
    )
    first_outcome = _parse(first, "<nearby-first@example.invalid>")
    sibling_outcome = _parse(sibling, "<nearby-sib@example.invalid>")
    for outcome in (first_outcome, sibling_outcome):
        assert outcome.disposition is Disposition.QUARANTINE
        assert "CONFLICTING_ECONOMIC_INSTRUCTION" in outcome.reasons
        assert outcome.instructions == ()


def test_first_exit_positive_and_negative_in_one_text_quarantines() -> None:
    text = _policies(
        "Whichever exit comes first closes the trade. "
        "Do not use whichever exit comes first.",
        _SIBLING,
    )
    outcome = _parse(text, "<first-mix@example.invalid>")
    assert outcome.disposition is Disposition.QUARANTINE
    assert "CONFLICTING_ECONOMIC_INSTRUCTION" in outcome.reasons
    assert outcome.instructions == ()


def test_sibling_positive_and_negative_in_one_text_quarantines() -> None:
    text = _policies(_FIRST, "Cancel the other. Do not cancel the other.")
    outcome = _parse(text, "<sib-mix@example.invalid>")
    assert outcome.disposition is Disposition.QUARANTINE
    assert "CONFLICTING_ECONOMIC_INSTRUCTION" in outcome.reasons
    assert outcome.instructions == ()


def test_same_positive_plain_and_html_accepts() -> None:
    outcome = parse_email(_alternative(DATED, _html(DATED), "<same-pos@example.invalid>"))
    assert outcome.disposition is Disposition.ACCEPT
    assert len(outcome.instructions) == 1
    assert outcome.instructions[0].first_exit_wins is True
    assert outcome.instructions[0].sibling_cancel is SiblingCancel.SIBLING_CANCEL_REQUIRED


@pytest.mark.parametrize(
    ("plain_first", "html_first", "message_id"),
    [
        (
            _FIRST,
            "Not whichever exit comes first closes the trade.",
            "<html-first-neg@example.invalid>",
        ),
        (
            "Not whichever exit comes first closes the trade.",
            _FIRST,
            "<plain-first-neg@example.invalid>",
        ),
    ],
)
def test_first_exit_cross_mime_negation_conflicts(
    plain_first: str,
    html_first: str,
    message_id: str,
) -> None:
    plain = _policies(plain_first, _SIBLING)
    html = _html(_policies(html_first, _SIBLING))
    outcome = parse_email(_alternative(plain, html, message_id))
    assert outcome.disposition is Disposition.QUARANTINE
    assert "HTML_PLAIN_CONFLICT" in outcome.reasons
    assert outcome.instructions == ()


@pytest.mark.parametrize(
    ("plain_sibling", "html_sibling", "message_id"),
    [
        (
            "cancel the other.",
            "do not cancel the other.",
            "<html-sib-neg@example.invalid>",
        ),
        (
            "do not cancel the other.",
            "cancel the other.",
            "<plain-sib-neg@example.invalid>",
        ),
    ],
)
def test_sibling_cross_mime_negation_conflicts(
    plain_sibling: str,
    html_sibling: str,
    message_id: str,
) -> None:
    plain = _policies(_FIRST, plain_sibling)
    html = _html(_policies(_FIRST, html_sibling))
    outcome = parse_email(_alternative(plain, html, message_id))
    assert outcome.disposition is Disposition.QUARANTINE
    assert "HTML_PLAIN_CONFLICT" in outcome.reasons
    assert outcome.instructions == ()


def test_absent_policy_across_mime_fails_closed() -> None:
    absent = DATED.replace(_POLICY_LINE, "Exits follow the broker orders.")
    left = parse_email(_alternative(DATED, _html(absent), "<absent-html@example.invalid>"))
    right = parse_email(_alternative(absent, _html(DATED), "<absent-plain@example.invalid>"))
    for outcome in (left, right):
        assert outcome.disposition is Disposition.QUARANTINE
        assert "HTML_PLAIN_CONFLICT" in outcome.reasons
        assert outcome.instructions == ()


def test_absence_is_not_classified_as_negation() -> None:
    text = DATED.replace(_POLICY_LINE, "Exits follow the broker orders.")
    outcome = _parse(text, "<absent-only@example.invalid>")
    assert outcome.disposition is Disposition.QUARANTINE
    assert outcome.instructions == ()
    assert "MISSING_EXIT_POLICY" in outcome.reasons
    assert "CONFLICTING_ECONOMIC_INSTRUCTION" not in outcome.reasons
