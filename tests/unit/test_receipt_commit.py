"""Synthetic receipt-commit decision tests. No database, broker, or mailbox access."""

from __future__ import annotations

import ast
import copy
import inspect
import logging
import traceback
from dataclasses import fields

import pytest

from swingtrade.group4_email.normalize import _FIXTURE_MESSAGE_ID, content_digest
from swingtrade.instruction_receipt import InMemoryReceiptStore
from swingtrade.receipt_commit import (
    _MESSAGE_ID,
    CommitClassification,
    CommitEvidence,
    ReceiptCommitRejected,
    evaluate_receipt_commit,
)

MESSAGE_ID = "<tday@example.invalid>"
OTHER_MESSAGE_ID = "<other@example.invalid>"
DIGEST_A = content_digest(b"synthetic-receipt-a")
DIGEST_B = content_digest(b"synthetic-receipt-b")
SECRET = "SYNTHETIC_SECRET_TOKEN_7f3a"
PROHIBITED = (
    "RAW_MIME_BODY_TOKEN",
    "EXAMPLE_QUANTITY_77",
    "PRICE_51.0000",
    "ACCT-9",
    "signals@example.invalid",
    "OrderIntent",
)
_SUCCESS = frozenset(
    {
        CommitClassification.INSERTED,
        CommitClassification.COMMITTED,
        CommitClassification.REPLAY,
    }
)


def _event(
    kind: str,
    *,
    receipt_key: str = MESSAGE_ID,
    digest: str = DIGEST_A,
    detail: str | None = None,
) -> dict[str, str]:
    event = {"event": kind, "receipt_key": receipt_key, "content_digest": digest}
    if detail is not None:
        event["detail"] = detail
    return event


def _evaluate(*kinds: str, detail: str | None = None) -> CommitEvidence:
    return evaluate_receipt_commit([_event(kind, detail=detail) for kind in kinds])


def test_message_id_pattern_matches_accepted_fixture_rule() -> None:
    assert _MESSAGE_ID.pattern == _FIXTURE_MESSAGE_ID.pattern
    assert _DIGEST_ACCEPTED(DIGEST_A)
    assert len(DIGEST_A) == len(content_digest(b""))


def _DIGEST_ACCEPTED(value: str) -> bool:
    return len(value) == len(content_digest(b"")) and all(
        character in "0123456789abcdef" for character in value
    )


def test_insert_and_commit_acknowledgment_is_committed() -> None:
    evidence = _evaluate("insert_ok", "commit_confirmed")

    assert evidence.classification is CommitClassification.COMMITTED
    assert evidence.reasons == (CommitClassification.COMMITTED,)
    assert CommitClassification.REPLAY not in evidence.reasons
    assert CommitClassification.INSERTED not in evidence.reasons
    assert evidence.receipt_key == MESSAGE_ID
    assert evidence.content_digest == DIGEST_A


def test_commit_acknowledgment_alone_is_committed() -> None:
    evidence = _evaluate("commit_confirmed")

    assert evidence.classification is CommitClassification.COMMITTED
    assert evidence.content_digest == DIGEST_A


def test_insert_without_commit_acknowledgment_is_not_committed() -> None:
    evidence = _evaluate("insert_ok")

    assert evidence.classification is CommitClassification.INSERTED
    assert evidence.reasons == (CommitClassification.INSERTED,)
    assert CommitClassification.COMMITTED not in evidence.reasons


def test_insert_returning_empty_is_a_known_non_commit() -> None:
    evidence = _evaluate("insert_returning_empty")

    assert evidence.classification is CommitClassification.EMPTY_RETURNING
    assert _SUCCESS.isdisjoint(evidence.reasons)


def test_unknown_commit_failure_event_is_rejected(caplog: pytest.LogCaptureFixture) -> None:
    secret = SECRET

    def _rejected() -> list[dict[str, str]]:
        return [_event("commit_failed", detail=secret)]

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(ReceiptCommitRejected, match="^RECEIPT_COMMIT_INVALID$") as caught:
            evaluate_receipt_commit(_rejected())

    rendered = "".join(traceback.format_exception(caught.value))
    assert caught.value.args == ("RECEIPT_COMMIT_INVALID",)
    assert secret not in str(caught.value)
    assert secret not in repr(caught.value)
    assert secret not in rendered
    assert secret not in caplog.text


def test_lost_ack_without_follow_up_stays_unresolved() -> None:
    evidence = _evaluate("insert_ok", "lost_ack")

    assert evidence.classification is CommitClassification.LOST_ACK
    assert evidence.reasons == (CommitClassification.LOST_ACK,)
    assert _SUCCESS.isdisjoint(evidence.reasons)
    assert CommitClassification.MISSING_ROW not in evidence.reasons
    assert evidence.content_digest == DIGEST_A


def test_lost_ack_then_same_digest_read_is_authoritative_read() -> None:
    evidence = _evaluate("insert_ok", "lost_ack", "authoritative_read")

    assert type(evidence) is CommitEvidence
    assert evidence.classification is CommitClassification.AUTHORITATIVE_READ
    assert evidence.reasons == (CommitClassification.AUTHORITATIVE_READ,)
    assert CommitClassification.INSERTED not in evidence.reasons
    assert CommitClassification.COMMITTED not in evidence.reasons
    assert CommitClassification.REPLAY not in evidence.reasons
    assert evidence.receipt_key == MESSAGE_ID
    assert evidence.content_digest == DIGEST_A


def test_read_before_lost_ack_does_not_prove_the_attempt_committed() -> None:
    evidence = _evaluate("authoritative_read", "lost_ack")

    assert evidence.classification is CommitClassification.LOST_ACK
    assert _SUCCESS.isdisjoint(evidence.reasons)


def test_conflict_preserves_the_first_digest() -> None:
    evidence = evaluate_receipt_commit(
        [
            _event("insert_ok", digest=DIGEST_A),
            _event("commit_confirmed", digest=DIGEST_A),
            _event("authoritative_read", digest=DIGEST_B),
        ]
    )

    assert evidence.classification is CommitClassification.CONFLICT
    assert evidence.reasons[0] is CommitClassification.CONFLICT
    assert evidence.receipt_key == MESSAGE_ID
    assert evidence.content_digest == DIGEST_A
    assert evidence.content_digest != DIGEST_B
    assert _SUCCESS.isdisjoint(evidence.reasons)


def test_repeated_insert_outranks_an_unconfirmed_empty_return() -> None:
    evidence = _evaluate("insert_ok", "insert_ok", "insert_returning_empty")

    assert evidence.classification is CommitClassification.REPLAY
    assert evidence.reasons == (
        CommitClassification.REPLAY,
        CommitClassification.EMPTY_RETURNING,
    )
    assert CommitClassification.INSERTED not in evidence.reasons
    assert CommitClassification.COMMITTED not in evidence.reasons
    assert evidence.content_digest == DIGEST_A


def test_same_digest_twice_is_replay_of_the_first_writer() -> None:
    evidence = _evaluate("insert_ok", "insert_ok")

    assert evidence.classification is CommitClassification.REPLAY
    assert evidence.reasons == (CommitClassification.REPLAY,)
    assert evidence.content_digest == DIGEST_A
    assert CommitClassification.INSERTED not in evidence.reasons


def test_one_authoritative_read_establishes_the_existing_row() -> None:
    evidence = _evaluate("authoritative_read")

    assert evidence.classification is CommitClassification.AUTHORITATIVE_READ
    assert evidence.receipt_key == MESSAGE_ID
    assert evidence.content_digest == DIGEST_A
    assert _SUCCESS.isdisjoint(evidence.reasons)


def test_lost_ack_followed_by_missing_row_is_not_a_commit() -> None:
    evidence = _evaluate("lost_ack", "missing_row")

    assert evidence.classification is CommitClassification.MISSING_ROW
    assert evidence.reasons == (CommitClassification.MISSING_ROW,)
    assert evidence.receipt_key == MESSAGE_ID
    assert evidence.content_digest == DIGEST_A
    assert _SUCCESS.isdisjoint(evidence.reasons)


def test_missing_row_after_a_read_is_the_later_resolution() -> None:
    evidence = _evaluate("lost_ack", "authoritative_read", "missing_row")

    assert evidence.classification is CommitClassification.MISSING_ROW
    assert evidence.reasons == (
        CommitClassification.MISSING_ROW,
        CommitClassification.AUTHORITATIVE_READ,
    )
    assert _SUCCESS.isdisjoint(evidence.reasons)
    assert evidence.content_digest == DIGEST_A


def test_later_matching_read_overrides_an_intermediate_missing_row() -> None:
    evidence = _evaluate("lost_ack", "missing_row", "authoritative_read")

    assert evidence.classification is CommitClassification.AUTHORITATIVE_READ
    assert CommitClassification.MISSING_ROW not in evidence.reasons
    assert _SUCCESS.isdisjoint(evidence.reasons)


@pytest.mark.parametrize(
    ("kind", "classification"),
    [
        ("unavailable", CommitClassification.UNAVAILABLE),
        ("read_only", CommitClassification.READ_ONLY),
        ("timeout", CommitClassification.TIMEOUT),
        ("serialization_uncertain", CommitClassification.SERIALIZATION_UNCERTAIN),
    ],
)
def test_each_storage_failure_fails_closed(kind: str, classification: CommitClassification) -> None:
    evidence = evaluate_receipt_commit([_event("commit_confirmed"), {"event": kind}])

    assert evidence.classification is classification
    assert evidence.reasons[0] is classification
    assert CommitClassification.COMMITTED not in evidence.reasons
    assert evidence.content_digest == DIGEST_A


def test_storage_failures_keep_precedence_and_every_condition() -> None:
    evidence = evaluate_receipt_commit(
        [
            {"event": "serialization_uncertain"},
            {"event": "timeout"},
            {"event": "read_only"},
            {"event": "unavailable"},
        ]
    )

    assert evidence.classification is CommitClassification.UNAVAILABLE
    assert evidence.reasons == (
        CommitClassification.UNAVAILABLE,
        CommitClassification.READ_ONLY,
        CommitClassification.TIMEOUT,
        CommitClassification.SERIALIZATION_UNCERTAIN,
    )
    assert evidence.receipt_key is None
    assert evidence.content_digest is None


@pytest.mark.parametrize(
    "events",
    [
        [],
        (),
        "insert_ok",
        [{"event": "insert_ok"}],
        [{"event": "no-such-event"}],
        [{"event": "insert_ok", "receipt_key": MESSAGE_ID}],
        [{"event": "timeout", "receipt_key": MESSAGE_ID}],
        [{"receipt_key": MESSAGE_ID, "content_digest": DIGEST_A}],
        [{"event": "insert_ok", "receipt_key": "mailbox@gmail.com", "content_digest": DIGEST_A}],
        [{"event": "insert_ok", "receipt_key": MESSAGE_ID, "content_digest": "ABCD"}],
        [{"event": "insert_ok", "receipt_key": DIGEST_A, "content_digest": DIGEST_B}],
        [
            _event("insert_ok", receipt_key=MESSAGE_ID),
            _event("insert_ok", receipt_key=OTHER_MESSAGE_ID),
        ],
        [{"event": "missing_row", "receipt_key": MESSAGE_ID, "content_digest": DIGEST_A}],
        [
            {
                "event": "insert_ok",
                "receipt_key": MESSAGE_ID,
                "content_digest": DIGEST_A,
                "body": "x",
            }
        ],
    ],
)
def test_malformed_or_mismatched_identity_is_rejected(events: object) -> None:
    with pytest.raises(ReceiptCommitRejected, match="^RECEIPT_COMMIT_INVALID$") as caught:
        evaluate_receipt_commit(events)
    assert caught.value.args == ("RECEIPT_COMMIT_INVALID",)


def test_secret_detail_is_absent_from_a_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret = SECRET

    def _poison() -> list[dict[str, str]]:
        return [{"event": "unavailable", "detail": secret, "password": secret}]

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(ReceiptCommitRejected) as caught:
            evaluate_receipt_commit(_poison())

    rendered = "".join(traceback.format_exception(caught.value))
    assert str(caught.value) == "RECEIPT_COMMIT_INVALID"
    assert secret not in str(caught.value)
    assert secret not in repr(caught.value)
    assert secret not in rendered
    assert secret not in caplog.text


def test_secret_detail_is_discarded_from_successful_evidence() -> None:
    secret = SECRET
    events = [_event("commit_confirmed", detail=secret)]
    before = copy.deepcopy(events)

    evidence = evaluate_receipt_commit(events)

    assert events == before
    assert evidence.classification is CommitClassification.COMMITTED
    assert secret not in repr(evidence)
    assert secret not in str(evidence)
    for name in fields(evidence):
        assert secret not in name.name


def test_identical_evidence_is_deterministic_and_detail_is_ignored() -> None:
    first = evaluate_receipt_commit([_event("commit_confirmed", detail="one")])
    second = evaluate_receipt_commit([_event("commit_confirmed", detail="two")])
    third = _evaluate("commit_confirmed")

    assert first == second == third
    assert first.classification is CommitClassification.COMMITTED


def test_contradictory_insert_and_empty_returning_is_not_a_commit() -> None:
    evidence = _evaluate("insert_ok", "insert_returning_empty")

    assert evidence.classification is CommitClassification.EMPTY_RETURNING
    assert _SUCCESS.isdisjoint(evidence.reasons)
    assert evidence.content_digest == DIGEST_A


def test_no_retry_memory_fallback_or_economic_type() -> None:
    store = InMemoryReceiptStore()
    events = [_event("lost_ack")]
    before = copy.deepcopy(events)

    evidence = evaluate_receipt_commit(events)

    assert events == before
    assert len(store) == 0
    assert evidence.classification is CommitClassification.LOST_ACK
    assert "OrderIntent" not in dir(evidence)
    source = inspect.getsource(evaluate_receipt_commit)
    module_source = inspect.getsource(inspect.getmodule(evaluate_receipt_commit))
    tree = ast.parse(module_source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert imported <= {"__future__", "re", "dataclasses", "enum", "typing", "swingtrade"}
    for banned in ("sqlalchemy", "psycopg", "socket", "alembic", "OrderIntent"):
        assert banned not in source
        assert banned not in module_source


def test_evidence_fields_exclude_prohibited_payloads() -> None:
    evidence = _evaluate("commit_confirmed")
    names = {field.name for field in fields(evidence)}

    assert names == {"classification", "reasons", "receipt_key", "content_digest"}
    rendered = repr(evidence)
    for token in PROHIBITED:
        assert token not in rendered


def test_digest_key_matches_its_digest() -> None:
    evidence = evaluate_receipt_commit(
        [
            {
                "event": "commit_confirmed",
                "receipt_key": DIGEST_A,
                "content_digest": DIGEST_A,
            }
        ]
    )

    assert evidence.classification is CommitClassification.COMMITTED
    assert evidence.receipt_key == DIGEST_A
    assert evidence.content_digest == DIGEST_A


def test_caller_order_keeps_the_first_digest_on_replay() -> None:
    evidence = evaluate_receipt_commit(
        [
            _event("authoritative_read", digest=DIGEST_A),
            _event("authoritative_read", digest=DIGEST_A),
        ]
    )

    assert evidence.classification is CommitClassification.REPLAY
    assert evidence.content_digest == DIGEST_A
