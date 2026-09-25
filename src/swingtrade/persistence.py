from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import JSON, Engine, Integer, String, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from swingtrade.domain import OrderIntent
from swingtrade.idempotency import canonical_json, input_digest


class Base(DeclarativeBase):
    pass


class DomainEventRow(Base):
    __tablename__ = "domain_events"
    __table_args__ = (
        UniqueConstraint("aggregate_type", "aggregate_id", "aggregate_version"),
    )

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    aggregate_type: Mapped[str] = mapped_column(String, nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String, nullable=False)
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    canonical_event: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class IdempotencyRow(Base):
    __tablename__ = "idempotency_records"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    input_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class OutboxRow(Base):
    __tablename__ = "outbox_items"

    intent_id: Mapped[str] = mapped_column(String, primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)


class OrderIntentRow(Base):
    __tablename__ = "order_intents"

    idempotency_key: Mapped[str] = mapped_column(String, primary_key=True)
    intent_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    input_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_intent: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class IntentIdentityConflict(RuntimeError):
    """A durable intent identity was reused for different canonical content."""


@dataclass(frozen=True)
class PersistedIntent:
    idempotency_key: str
    intent_id: str
    input_digest: str
    canonical_intent: dict[str, Any]


def canonical_intent(intent: OrderIntent) -> dict[str, Any]:
    payload = asdict(intent)
    payload["side"] = intent.side.value
    payload["quantity"] = str(intent.quantity)
    payload["mode"] = intent.mode.value
    # Round-trip through canonical JSON to guarantee JSON-native immutable values.
    decoded = json.loads(canonical_json(payload))
    if not isinstance(decoded, dict):
        raise TypeError("canonical intent must be an object")
    return decoded


class PostgresIntentRepository:
    """Atomic canonical intent identity backed by PostgreSQL unique constraints."""

    def __init__(self, engine: Engine) -> None:
        if engine.dialect.name != "postgresql":
            raise ValueError("PostgresIntentRepository requires PostgreSQL")
        self._engine = engine

    def create_or_get(self, intent: OrderIntent) -> PersistedIntent:
        payload = canonical_intent(intent)
        digest = input_digest(payload)
        values = {
            "idempotency_key": intent.idempotency_key,
            "intent_id": intent.intent_id,
            "input_digest": digest,
            "canonical_intent": payload,
        }
        with self._engine.begin() as connection:
            connection.execute(insert(OrderIntentRow).values(**values).on_conflict_do_nothing())
            row = connection.execute(
                select(OrderIntentRow).where(
                    OrderIntentRow.idempotency_key == intent.idempotency_key
                )
            ).scalar_one_or_none()
            if row is None:
                row = connection.execute(
                    select(OrderIntentRow).where(OrderIntentRow.intent_id == intent.intent_id)
                ).scalar_one()
            persisted = PersistedIntent(
                row.idempotency_key,
                row.intent_id,
                row.input_digest,
                row.canonical_intent,
            )
            if persisted != PersistedIntent(
                intent.idempotency_key, intent.intent_id, digest, payload
            ):
                raise IntentIdentityConflict(
                    "idempotency key or intent id reused with different canonical intent"
                )
            return persisted
