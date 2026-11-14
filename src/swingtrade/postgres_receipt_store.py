"""PostgreSQL instruction-receipt store.

The caller owns the connection and its transaction. This module does not open
a socket, begin a transaction, commit, roll back, retry, or close that
connection. ``None`` means this statement inserted a row inside that still-open
transaction. It is not a durable commit and it does not authorize an order.

``InstructionReceipt`` is a public value object. ``project_receipt`` is not a
required constructor, so ``compare_and_insert`` applies that function's
allowlist itself and rejects the call before SQL when the value disagrees.
Each persisted string must also fit in ``MAX_EMAIL_BYTES`` UTF-8 bytes, the
accepted raw-email ceiling. Character length is not that ceiling. Importing
this module does not contact a database. A mocked result is not a migration
and is not evidence that revision 0004 has run.
"""

from __future__ import annotations

from collections.abc import Mapping

import psycopg
from sqlalchemy import JSON, String, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from swingtrade.group4_email.contract import (
    EMAIL_RETENTION_POLICY,
    MAX_EMAIL_BYTES,
    PARSER_VERSION,
    SCHEMA_VERSION,
    Disposition,
    MessageType,
    ProviderType,
)
from swingtrade.group4_email.normalize import _FIXTURE_MESSAGE_ID
from swingtrade.instruction_receipt import (
    _REASON_VALUES,
    _TIMESTAMP,
    InstructionReceipt,
    ReceiptStoreUnavailable,
    _instruction_id_ok,
    _is_digest,
)


class ReceiptBase(DeclarativeBase):
    """Metadata for this store only. It is not the shared economic registry."""


class InstructionReceiptRow(ReceiptBase):
    """Allowlisted receipt columns. Raw message bodies are not represented."""

    __tablename__ = "instruction_receipts"

    receipt_key: Mapped[str] = mapped_column(String, primary_key=True)
    content_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    disposition: Mapped[str] = mapped_column(String, nullable=False)
    message_type: Mapped[str] = mapped_column(String, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    instruction_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    message_id: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_type: Mapped[str] = mapped_column(String, nullable=False)
    parser_version: Mapped[str] = mapped_column(String, nullable=False)
    schema_version: Mapped[str] = mapped_column(String, nullable=False)
    retention_policy: Mapped[str] = mapped_column(String, nullable=False)
    provider_message_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    source_timestamp: Mapped[str | None] = mapped_column(String, nullable=True)


class PostgresReceiptStore:
    """First-writer receipt identity on a caller-owned PostgreSQL transaction."""

    def __init__(self, connection: object) -> None:
        self._connection = connection

    def compare_and_insert(
        self, key: str, receipt: InstructionReceipt
    ) -> InstructionReceipt | None:
        """Insert only when ``key`` is absent. Never replace an existing row."""

        if not _acceptable(key, receipt):
            raise ReceiptStoreUnavailable()
        try:
            stored = self._compare(receipt)
        except ReceiptStoreUnavailable:
            raise
        except (psycopg.Error, SQLAlchemyError):
            stored = None
            rejected = True
        else:
            rejected = False
        if rejected:
            raise ReceiptStoreUnavailable()
        return stored

    def _compare(self, receipt: InstructionReceipt) -> InstructionReceipt | None:
        inserted = insert(InstructionReceiptRow).values(**_values(receipt))
        statement = inserted.on_conflict_do_nothing(
            index_elements=[InstructionReceiptRow.receipt_key]
        ).returning(InstructionReceiptRow.receipt_key)
        result = _execute(self._connection, statement)
        if _first(result) is not None:
            return None
        existing = _execute(
            self._connection,
            select(InstructionReceiptRow).where(
                InstructionReceiptRow.receipt_key == receipt.receipt_key
            ),
        )
        return _receipt_from_row(_one(existing))


def _acceptable(key: object, receipt: object) -> bool:
    if type(key) is not str or not _fits(key) or type(receipt) is not InstructionReceipt:
        return False
    if receipt.receipt_key != key:
        return False
    if type(receipt.disposition) is not Disposition:
        return False
    if type(receipt.message_type) is not MessageType:
        return False
    return _matches_projection(receipt)


def _matches_projection(receipt: InstructionReceipt) -> bool:
    """Same allowlist as ``project_receipt``, applied at the persistence boundary."""

    digest = receipt.content_digest
    if not _is_digest(digest):
        return False
    message_id = receipt.message_id
    if message_id is None:
        if receipt.receipt_key != digest or receipt.provider_message_ref is not None:
            return False
    elif (
        type(message_id) is not str
        or not _fits(message_id)
        or _FIXTURE_MESSAGE_ID.fullmatch(message_id) is None
        or receipt.receipt_key != message_id
        or receipt.provider_message_ref != message_id
    ):
        return False
    if (
        receipt.provider_type != ProviderType.FIXTURE.value
        or receipt.parser_version != PARSER_VERSION
        or receipt.schema_version != SCHEMA_VERSION
        or receipt.retention_policy != EMAIL_RETENTION_POLICY
    ):
        return False
    timestamp = receipt.source_timestamp
    if timestamp is not None and (
        type(timestamp) is not str
        or not _fits(timestamp)
        or _TIMESTAMP.fullmatch(timestamp) is None
    ):
        return False
    reasons = receipt.reasons
    instruction_ids = receipt.instruction_ids
    if type(reasons) is not tuple or type(instruction_ids) is not tuple:
        return False
    if any(type(reason) is not str or reason not in _REASON_VALUES for reason in reasons):
        return False
    if len(instruction_ids) != len(set(instruction_ids)):
        return False
    if any(type(identifier) is not str or not _fits(identifier) for identifier in instruction_ids):
        return False
    return all(
        _instruction_id_ok(identifier, digest, message_id) for identifier in instruction_ids
    )


def _fits(value: str) -> bool:
    """Bound one persisted string by the raw email's UTF-8 byte ceiling."""

    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return len(encoded) <= MAX_EMAIL_BYTES


def _values(receipt: InstructionReceipt) -> dict[str, object]:
    return {
        "receipt_key": receipt.receipt_key,
        "content_digest": receipt.content_digest,
        "disposition": receipt.disposition.value,
        "message_type": receipt.message_type.value,
        "reasons": list(receipt.reasons),
        "instruction_ids": list(receipt.instruction_ids),
        "message_id": receipt.message_id,
        "provider_type": receipt.provider_type,
        "parser_version": receipt.parser_version,
        "schema_version": receipt.schema_version,
        "retention_policy": receipt.retention_policy,
        "provider_message_ref": receipt.provider_message_ref,
        "source_timestamp": receipt.source_timestamp,
    }


def _execute(connection: object, statement: object) -> object:
    execute = getattr(connection, "execute", None)
    if not callable(execute):
        raise ReceiptStoreUnavailable()
    return execute(statement)


def _first(result: object) -> object:
    first = getattr(result, "first", None)
    if not callable(first):
        raise ReceiptStoreUnavailable()
    return first()


def _one(result: object) -> object:
    one = getattr(result, "one", None)
    if not callable(one):
        raise ReceiptStoreUnavailable()
    return one()


def _receipt_from_row(row: object) -> InstructionReceipt:
    mapping = getattr(row, "_mapping", None)
    if not isinstance(mapping, Mapping):
        raise ReceiptStoreUnavailable()
    try:
        reasons = _stored_texts(mapping["reasons"])
        instruction_ids = _stored_texts(mapping["instruction_ids"])
        receipt = InstructionReceipt(
            receipt_key=_stored_text(mapping["receipt_key"]),
            content_digest=_stored_text(mapping["content_digest"]),
            disposition=Disposition(_stored_text(mapping["disposition"])),
            message_type=MessageType(_stored_text(mapping["message_type"])),
            reasons=reasons,
            instruction_ids=instruction_ids,
            message_id=_stored_optional(mapping["message_id"]),
            provider_type=_stored_text(mapping["provider_type"]),
            parser_version=_stored_text(mapping["parser_version"]),
            schema_version=_stored_text(mapping["schema_version"]),
            retention_policy=_stored_text(mapping["retention_policy"]),
            provider_message_ref=_stored_optional(mapping["provider_message_ref"]),
            source_timestamp=_stored_optional(mapping["source_timestamp"]),
        )
    except (KeyError, TypeError, ValueError):
        raise ReceiptStoreUnavailable() from None
    if not _acceptable(receipt.receipt_key, receipt):
        raise ReceiptStoreUnavailable()
    return receipt


def _stored_text(value: object) -> str:
    if type(value) is not str or value == "":
        raise ReceiptStoreUnavailable()
    return value


def _stored_optional(value: object) -> str | None:
    if value is None:
        return None
    return _stored_text(value)


def _stored_texts(value: object) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise ReceiptStoreUnavailable()
    return tuple(value)
