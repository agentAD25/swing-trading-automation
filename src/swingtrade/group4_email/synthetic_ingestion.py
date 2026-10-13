"""Compose accepted synthetic acquisition, parse, view, and receipt steps.

The composition is sequential. It does not parse MIME itself, open a mailbox,
or create an order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from swingtrade.group4_email.contract import Disposition, MessageType
from swingtrade.group4_email.disposition import DispositionViewLabel, derive_disposition_view
from swingtrade.group4_email.parse import MessageIdentityRegistry, parse_email
from swingtrade.group4_email.synthetic_acquisition import (
    SyntheticFixture,
    deliver_synthetic_fixtures,
)
from swingtrade.instruction_receipt import ReceiptKind, ReceiptStore, admit_instruction_receipt


class SyntheticIngestionRejected(Exception):
    """Fail-closed ingestion error. The message is a stable code and nothing else."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or code == "":
            code = "fail_closed"
        super().__init__(code)
        self.code = code

    def __repr__(self) -> str:
        return f"SyntheticIngestionRejected({self.code!r})"

    def __str__(self) -> str:
        return self.code


@dataclass(frozen=True)
class SyntheticIngestionRecord:
    """One non-economic reading. Ordinary repr omits the receipt key."""

    delivery_ref: str
    content_digest: str
    parser_disposition: Disposition
    parser_message_type: MessageType
    parser_reasons: tuple[str, ...]
    view_label: DispositionViewLabel
    receipt_kind: ReceiptKind
    receipt_key: str = field(repr=False)
    conflict_reason: str | None


def record_synthetic_ingestion(
    fixtures: object,
    store: ReceiptStore,
    registry: MessageIdentityRegistry | None = None,
) -> tuple[SyntheticIngestionRecord, ...]:
    """Record one immutable result per validated delivery, in caller order.

    A later failure leaves earlier receipt admissions and registry updates in
    place and returns no tuple.
    """

    if registry is not None and type(registry) is not MessageIdentityRegistry:
        raise SyntheticIngestionRejected("INGESTION_INVALID")
    deliveries = deliver_synthetic_fixtures(cast(tuple[SyntheticFixture, ...], fixtures))
    active_registry = MessageIdentityRegistry() if registry is None else registry
    records: list[SyntheticIngestionRecord] = []
    for delivery in deliveries:
        outcome = parse_email(delivery.mime, active_registry)
        view = derive_disposition_view(outcome)
        decision = admit_instruction_receipt(outcome, store)
        records.append(
            SyntheticIngestionRecord(
                delivery_ref=delivery.delivery_ref,
                content_digest=delivery.content_digest,
                parser_disposition=outcome.disposition,
                parser_message_type=outcome.message_type,
                parser_reasons=tuple(outcome.reasons),
                view_label=view.label,
                receipt_kind=decision.kind,
                receipt_key=decision.receipt.receipt_key,
                conflict_reason=decision.conflict_reason,
            )
        )
    return tuple(records)
