from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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
