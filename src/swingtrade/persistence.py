from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, DecimalException
from typing import Any

from sqlalchemy import JSON, Engine, Integer, String, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from swingtrade.domain import (
    DomainValidationError,
    OrderIntent,
    OrderObservation,
    decimal_value,
    utc_instant,
)
from swingtrade.idempotency import idempotency_key, input_digest


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
    canonical_observation: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class IntentIdentityConflict(RuntimeError):
    """A durable intent identity was reused for different canonical content."""


class NonCanonicalIntentKey(RuntimeError):
    """An intent supplied or stored a key not derived from its canonical input."""


class DurableObservationError(RuntimeError):
    """A durable DRY_RUN observation is missing or noncanonical."""


@dataclass(frozen=True)
class PersistedIntent:
    idempotency_key: str
    intent_id: str
    input_digest: str
    canonical_intent: dict[str, Any]
    canonical_observation: dict[str, Any]


def canonical_decimal(value: Decimal | str) -> str:
    """Serialize a finite base-10 value without scale or exponent aliases."""
    number = decimal_value(value)
    if number == 0:
        return "0"
    fixed = format(number, "f")
    return fixed.rstrip("0").rstrip(".") if "." in fixed else fixed


def canonical_economic_intent(intent: OrderIntent) -> dict[str, str]:
    """Return the sole canonical economic input for DRY_RUN dispatch."""
    return {
        "decision_id": intent.decision_id,
        "intent_id": intent.intent_id,
        "mode": intent.mode.value,
        "quantity": canonical_decimal(intent.quantity),
        "side": intent.side.value,
    }


def dispatch_business_input(intent: OrderIntent) -> dict[str, str]:
    return canonical_economic_intent(intent)


def canonical_dispatch_key(intent: OrderIntent) -> str:
    return idempotency_key("dispatch", intent.intent_id, canonical_economic_intent(intent))


def _stored_dispatch_key(payload: object) -> str:
    if not isinstance(payload, dict):
        raise NonCanonicalIntentKey("stored canonical intent is not an object")
    required = ("decision_id", "intent_id", "mode", "quantity", "side")
    if any(not isinstance(payload.get(field), str) for field in required):
        raise NonCanonicalIntentKey("stored canonical intent lacks dispatch key input")
    intent_id = payload["intent_id"]
    business_input = {field: payload[field] for field in required}
    try:
        canonical_quantity = canonical_decimal(business_input["quantity"])
    except DomainValidationError as error:
        raise NonCanonicalIntentKey(
            "stored canonical intent has an invalid decimal quantity"
        ) from error
    if business_input["quantity"] != canonical_quantity:
        raise NonCanonicalIntentKey(
            "stored canonical intent uses a stale noncanonical decimal"
        )
    business_input["quantity"] = canonical_quantity
    return idempotency_key("dispatch", intent_id, business_input)


def _canonical_utc_instant(value: datetime) -> str:
    utc_instant(value)
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _canonical_dry_run_observation(
    intent: OrderIntent,
    effective_at: datetime,
    economic: dict[str, str],
) -> dict[str, str]:
    return {
        "cumulative_quantity": "0",
        "effective_at": _canonical_utc_instant(effective_at),
        "intent_id": intent.intent_id,
        "order_id": f"dry_{intent.intent_id}",
        "requested_quantity": economic["quantity"],
        "state": "PENDING",
    }


def canonical_dry_run_observation(
    intent: OrderIntent, effective_at: datetime
) -> dict[str, str]:
    economic = canonical_economic_intent(intent)
    return _canonical_dry_run_observation(intent, effective_at, economic)


def materialize_dry_run_observation(persisted: PersistedIntent) -> OrderObservation:
    payload = persisted.canonical_observation
    required = {
        "cumulative_quantity",
        "effective_at",
        "intent_id",
        "order_id",
        "requested_quantity",
        "state",
    }
    if set(payload) != required or not all(
        isinstance(payload[field], str) for field in required
    ):
        raise DurableObservationError("durable DRY_RUN observation is not canonical")
    canonical_intent_payload = persisted.canonical_intent
    if (
        payload["order_id"] != f"dry_{persisted.intent_id}"
        or payload["intent_id"] != persisted.intent_id
        or payload["requested_quantity"] != canonical_intent_payload.get("quantity")
        or payload["state"] != "PENDING"
        or payload["cumulative_quantity"] != "0"
    ):
        raise DurableObservationError(
            "durable DRY_RUN observation conflicts with canonical intent"
        )
    try:
        effective_at = datetime.fromisoformat(payload["effective_at"].replace("Z", "+00:00"))
        if _canonical_utc_instant(effective_at) != payload["effective_at"]:
            raise ValueError("noncanonical instant")
        observation = OrderObservation(
            order_id=payload["order_id"],
            intent_id=payload["intent_id"],
            state=payload["state"],
            requested_quantity=Decimal(payload["requested_quantity"]),
            cumulative_quantity=Decimal(payload["cumulative_quantity"]),
            effective_at=effective_at,
        )
    except (TypeError, ValueError, DecimalException) as error:
        raise DurableObservationError(
            "durable DRY_RUN observation is not canonical"
        ) from error
    return observation


def _canonical_intent(
    intent: OrderIntent, economic: dict[str, str]
) -> dict[str, Any]:
    return {
        "decision_id": economic["decision_id"],
        "idempotency_key": intent.idempotency_key,
        "instrument_id": intent.instrument_id,
        "intent_id": economic["intent_id"],
        "mode": economic["mode"],
        "quantity": economic["quantity"],
        "run_id": intent.run_id,
        "side": economic["side"],
    }


def canonical_intent(intent: OrderIntent) -> dict[str, Any]:
    economic = canonical_economic_intent(intent)
    return _canonical_intent(intent, economic)


class PostgresIntentRepository:
    """Atomic canonical intent identity backed by PostgreSQL unique constraints."""

    def __init__(self, engine: Engine) -> None:
        if engine.dialect.name != "postgresql":
            raise ValueError("PostgresIntentRepository requires PostgreSQL")
        self._engine = engine

    def create_or_get(
        self, intent: OrderIntent, *, effective_at: datetime
    ) -> PersistedIntent:
        economic = canonical_economic_intent(intent)
        expected_key = idempotency_key("dispatch", intent.intent_id, economic)
        if intent.idempotency_key != expected_key:
            raise NonCanonicalIntentKey(
                "supplied intent key does not match canonical dispatch input"
            )
        payload = _canonical_intent(intent, economic)
        digest = input_digest(payload)
        observation = _canonical_dry_run_observation(intent, effective_at, economic)
        values = {
            "idempotency_key": intent.idempotency_key,
            "intent_id": intent.intent_id,
            "input_digest": digest,
            "canonical_intent": payload,
            "canonical_observation": observation,
        }
        with self._engine.begin() as connection:
            connection.execute(insert(OrderIntentRow).values(**values).on_conflict_do_nothing())
            row = connection.execute(
                select(OrderIntentRow).where(
                    OrderIntentRow.idempotency_key == intent.idempotency_key
                )
            ).one_or_none()
            if row is None:
                row = connection.execute(
                    select(OrderIntentRow).where(OrderIntentRow.intent_id == intent.intent_id)
                ).one()
            persisted = PersistedIntent(
                row._mapping["idempotency_key"],
                row._mapping["intent_id"],
                row._mapping["input_digest"],
                row._mapping["canonical_intent"],
                row._mapping["canonical_observation"],
            )
            stored_key = _stored_dispatch_key(persisted.canonical_intent)
            if (
                persisted.idempotency_key != stored_key
                or persisted.canonical_intent.get("idempotency_key") != stored_key
            ):
                raise NonCanonicalIntentKey(
                    "durable intent row contains a noncanonical dispatch key"
                )
            if not isinstance(persisted.canonical_observation, dict):
                raise DurableObservationError(
                    "durable intent row lacks a canonical DRY_RUN observation"
                )
            materialize_dry_run_observation(persisted)
            if (
                persisted.idempotency_key,
                persisted.intent_id,
                persisted.input_digest,
                persisted.canonical_intent,
            ) != (
                intent.idempotency_key,
                intent.intent_id,
                digest,
                payload,
            ):
                raise IntentIdentityConflict(
                    "idempotency key or intent id reused with different canonical intent"
                )
            return persisted
