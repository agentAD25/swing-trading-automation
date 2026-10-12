"""Offline synthetic receipt-commit decision model.

This module folds allowlisted event observations into one ``CommitEvidence``
value. It is not a database adapter. A result is not evidence of PostgreSQL
durability, isolation, or cross-process atomicity.

``INSERTED``, ``COMMITTED``, and ``REPLAY`` are local labels. They are not
``ReceiptKind``. An authoritative read reports the row that the injected
evidence says is present. It does not prove which attempt inserted that row.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import NamedTuple

from swingtrade.group4_email.normalize import content_digest

_MESSAGE_ID = re.compile(r"^<[^<>\s@]+@example\.invalid>$")
_DIGEST = re.compile(rf"^[0-9a-f]{{{len(content_digest(b''))}}}$")
_ALLOWED_KEYS = frozenset({"event", "receipt_key", "content_digest", "detail"})
_IDENTITY_EVENTS = frozenset(
    {
        "insert_ok",
        "commit_confirmed",
        "insert_returning_empty",
        "authoritative_read",
        "lost_ack",
        "missing_row",
    }
)
_STORAGE_EVENTS = frozenset(
    {
        "timeout",
        "serialization_uncertain",
        "read_only",
        "unavailable",
    }
)
_EVENTS = _IDENTITY_EVENTS | _STORAGE_EVENTS


class CommitClassification(StrEnum):
    """Local synthetic label. This is not a parser disposition or an order state."""

    UNAVAILABLE = "UNAVAILABLE"
    READ_ONLY = "READ_ONLY"
    TIMEOUT = "TIMEOUT"
    SERIALIZATION_UNCERTAIN = "SERIALIZATION_UNCERTAIN"
    CONFLICT = "CONFLICT"
    MISSING_ROW = "MISSING_ROW"
    AUTHORITATIVE_READ = "AUTHORITATIVE_READ"
    LOST_ACK = "LOST_ACK"
    REPLAY = "REPLAY"
    EMPTY_RETURNING = "EMPTY_RETURNING"
    COMMITTED = "COMMITTED"
    INSERTED = "INSERTED"


class ReceiptCommitRejected(Exception):
    """The event list is not allowlisted synthetic evidence."""

    def __init__(self) -> None:
        super().__init__("RECEIPT_COMMIT_INVALID")


@dataclass(frozen=True)
class CommitEvidence:
    """Folded synthetic evidence. ``detail`` is never stored."""

    classification: CommitClassification
    reasons: tuple[CommitClassification, ...]
    receipt_key: str | None
    content_digest: str | None

    def __post_init__(self) -> None:
        if (self.receipt_key is None) != (self.content_digest is None):
            raise ReceiptCommitRejected()
        if not self.reasons or self.reasons[0] is not self.classification:
            raise ReceiptCommitRejected()


class _Event(NamedTuple):
    kind: str
    receipt_key: str | None
    content_digest: str | None


@dataclass
class _Facts:
    receipt_key: str | None = None
    content_digest: str | None = None
    conflict: bool = False
    unavailable: bool = False
    read_only: bool = False
    timeout: bool = False
    serialization_uncertain: bool = False
    insert_ok: int = 0
    commit_confirmed: int = 0
    authoritative_read: int = 0
    insert_returning_empty: bool = False
    lost_ack: bool = False
    missing_after_lost_ack: bool = False
    read_after_lost_ack: bool = False


def evaluate_receipt_commit(events: object) -> CommitEvidence:
    """Fold synthetic events in caller order. Does not retry or write storage."""
    facts = _facts(_parse(events))
    reasons = _reasons(facts)
    if not reasons:
        raise ReceiptCommitRejected()
    return CommitEvidence(
        classification=reasons[0],
        reasons=reasons,
        receipt_key=facts.receipt_key,
        content_digest=facts.content_digest,
    )


def _parse(events: object) -> tuple[_Event, ...]:
    if not isinstance(events, list) or type(events) is not list or len(events) == 0:
        raise ReceiptCommitRejected()
    parsed: list[_Event] = []
    for item in events:
        parsed.append(_event(item))
    return tuple(parsed)


def _event(item: object) -> _Event:
    if not isinstance(item, dict) or type(item) is not dict:
        raise ReceiptCommitRejected()
    if not set(item).issubset(_ALLOWED_KEYS) or "event" not in item:
        raise ReceiptCommitRejected()
    kind = item["event"]
    if type(kind) is not str or kind not in _EVENTS:
        raise ReceiptCommitRejected()
    has_key = "receipt_key" in item
    has_digest = "content_digest" in item
    if kind in _IDENTITY_EVENTS and not (has_key and has_digest):
        raise ReceiptCommitRejected()
    if kind in _STORAGE_EVENTS and has_key != has_digest:
        raise ReceiptCommitRejected()
    if not has_key:
        return _Event(kind, None, None)
    receipt_key = item["receipt_key"]
    digest = item["content_digest"]
    if type(receipt_key) is not str or type(digest) is not str:
        raise ReceiptCommitRejected()
    _require_identity(receipt_key, digest)
    return _Event(kind, receipt_key, digest)


def _require_identity(receipt_key: str, digest: str) -> None:
    if _DIGEST.fullmatch(digest) is None:
        raise ReceiptCommitRejected()
    if _DIGEST.fullmatch(receipt_key) is not None:
        if receipt_key != digest:
            raise ReceiptCommitRejected()
        return
    if _MESSAGE_ID.fullmatch(receipt_key) is None:
        raise ReceiptCommitRejected()


def _facts(events: tuple[_Event, ...]) -> _Facts:
    facts = _Facts()
    for event in events:
        _observe(facts, event)
    return facts


def _observe(facts: _Facts, event: _Event) -> None:
    if event.kind == "unavailable":
        facts.unavailable = True
    elif event.kind == "read_only":
        facts.read_only = True
    elif event.kind == "timeout":
        facts.timeout = True
    elif event.kind == "serialization_uncertain":
        facts.serialization_uncertain = True
    if event.receipt_key is None:
        return
    _track_identity(facts, event.receipt_key, event.content_digest)
    matches_first = event.content_digest == facts.content_digest
    if event.kind == "lost_ack":
        facts.lost_ack = True
    if event.kind == "missing_row" and facts.lost_ack:
        facts.missing_after_lost_ack = True
    if event.kind == "authoritative_read" and facts.lost_ack and matches_first:
        facts.read_after_lost_ack = True
    if event.kind == "insert_returning_empty":
        facts.insert_returning_empty = True
    if not matches_first:
        return
    if event.kind == "insert_ok":
        facts.insert_ok += 1
    elif event.kind == "commit_confirmed":
        facts.commit_confirmed += 1
    elif event.kind == "authoritative_read":
        facts.authoritative_read += 1


def _track_identity(facts: _Facts, receipt_key: str, digest: str | None) -> None:
    if digest is None:
        raise ReceiptCommitRejected()
    if facts.receipt_key is None:
        facts.receipt_key = receipt_key
        facts.content_digest = digest
        return
    if receipt_key != facts.receipt_key:
        raise ReceiptCommitRejected()
    if digest != facts.content_digest:
        facts.conflict = True


def _reasons(facts: _Facts) -> tuple[CommitClassification, ...]:
    recognized: list[CommitClassification] = []
    if facts.unavailable:
        recognized.append(CommitClassification.UNAVAILABLE)
    if facts.read_only:
        recognized.append(CommitClassification.READ_ONLY)
    if facts.timeout:
        recognized.append(CommitClassification.TIMEOUT)
    if facts.serialization_uncertain:
        recognized.append(CommitClassification.SERIALIZATION_UNCERTAIN)
    if facts.conflict:
        recognized.append(CommitClassification.CONFLICT)
    if facts.lost_ack and facts.missing_after_lost_ack and not facts.read_after_lost_ack:
        recognized.append(CommitClassification.MISSING_ROW)
    if facts.lost_ack and facts.read_after_lost_ack:
        recognized.append(CommitClassification.AUTHORITATIVE_READ)
    if facts.lost_ack and not facts.missing_after_lost_ack and not facts.read_after_lost_ack:
        recognized.append(CommitClassification.LOST_ACK)
    if _establishing_read(facts):
        recognized.append(CommitClassification.AUTHORITATIVE_READ)
    if facts.insert_returning_empty and not _confirmed_row(facts):
        recognized.append(CommitClassification.EMPTY_RETURNING)
    if not recognized:
        success = _success(facts)
        if success is not None:
            recognized.append(success)
    return tuple(recognized)


def _establishing_read(facts: _Facts) -> bool:
    return (
        not facts.lost_ack
        and facts.authoritative_read == 1
        and facts.insert_ok == 0
        and facts.commit_confirmed == 0
    )


def _confirmed_row(facts: _Facts) -> bool:
    return facts.commit_confirmed > 0 or facts.authoritative_read > 0


def _replay(facts: _Facts) -> bool:
    """Repeated observation of the first digest.

    One ``insert_ok`` plus one ``commit_confirmed`` is the acknowledgment of
    that insert, so rule 12 classifies it as ``COMMITTED`` rather than as a
    second sighting. Any other repeated observation is ``REPLAY`` when no
    ``lost_ack`` applies.
    """
    if facts.lost_ack:
        return False
    observations = facts.insert_ok + facts.commit_confirmed + facts.authoritative_read
    confirmation = (
        facts.insert_ok == 1 and facts.commit_confirmed == 1 and facts.authoritative_read == 0
    )
    return observations > 1 and not confirmation


def _success(facts: _Facts) -> CommitClassification | None:
    if _replay(facts):
        return CommitClassification.REPLAY
    if facts.commit_confirmed > 0:
        return CommitClassification.COMMITTED
    if facts.insert_ok > 0:
        return CommitClassification.INSERTED
    return None
