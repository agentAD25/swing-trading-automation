"""Pure non-economic view of an existing parse outcome.

The view does not replace ``Disposition``. It does not construct an order,
read a mailbox, or change retention. ``DUPLICATE`` is named because item 18
reserves it for an explicit replay view. No accepted contract supplies replay
context on ``ParseOutcome``, and this function does not invent one, so it
never returns that label.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import NoReturn

from swingtrade.group4_email.contract import (
    Disposition,
    MessageType,
    ParseOutcome,
    ParseProvenance,
    ReasonCode,
)

_DEFERRED_REASONS = frozenset(
    {
        ReasonCode.PARSER_DEFERRED.value,
        ReasonCode.CANCEL_FORMAT_UNSPECIFIED.value,
    }
)


class DispositionViewLabel(StrEnum):
    """Local view labels. These are not parser dispositions or order states."""

    RECORDED_NOT_EXECUTABLE = "RECORDED_NOT_EXECUTABLE"
    DEFERRED = "DEFERRED"
    QUARANTINED = "QUARANTINED"
    DUPLICATE = "DUPLICATE"
    REJECT = "REJECT"
    INFORMATIONAL = "INFORMATIONAL"


class DispositionViewError(Exception):
    """Fail-closed view error. The message is a stable code and nothing else."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or code == "":
            code = "fail_closed"
        super().__init__(code)
        self.code = code

    def __repr__(self) -> str:
        return f"DispositionViewError({self.code!r})"

    def __str__(self) -> str:
        return self.code


@dataclass(frozen=True)
class DispositionView:
    """Immutable reading of one outcome. It holds no order and no message body."""

    label: DispositionViewLabel
    disposition: Disposition
    message_type: MessageType
    reasons: tuple[str, ...]
    instruction_ids: tuple[str, ...]
    content_digest: str
    message_id: str | None
    provenance: ParseProvenance

    def __post_init__(self) -> None:
        if self.label is DispositionViewLabel.DUPLICATE:
            raise DispositionViewError("duplicate_unavailable")


def derive_disposition_view(outcome: ParseOutcome) -> DispositionView:
    """Derive one view. The outcome object is not modified."""

    if type(outcome) is not ParseOutcome:
        _fail("invalid_outcome")
    if outcome.network_permitted is not False:
        _fail("invariant_violation")
    disposition = outcome.disposition
    message_type = outcome.message_type
    if type(disposition) is not Disposition:
        _fail("invalid_disposition")
    if type(message_type) is not MessageType:
        _fail("invalid_message_type")
    if disposition is not Disposition.ACCEPT and outcome.instructions:
        _fail("invariant_violation")
    instruction_ids = _instruction_ids(outcome)
    label = _label(disposition, message_type, outcome.reasons, instruction_ids)
    return DispositionView(
        label=label,
        disposition=disposition,
        message_type=message_type,
        reasons=tuple(outcome.reasons),
        instruction_ids=instruction_ids,
        content_digest=outcome.content_digest,
        message_id=outcome.message_id,
        provenance=outcome.provenance,
    )


def _label(
    disposition: Disposition,
    message_type: MessageType,
    reasons: tuple[str, ...],
    instruction_ids: tuple[str, ...],
) -> DispositionViewLabel:
    if disposition is Disposition.REJECT:
        return DispositionViewLabel.REJECT
    if disposition is Disposition.QUARANTINE:
        if reasons and set(reasons) <= _DEFERRED_REASONS:
            return DispositionViewLabel.DEFERRED
        return DispositionViewLabel.QUARANTINED
    if disposition is Disposition.ACCEPT and message_type is MessageType.NEW_TRADE:
        if not instruction_ids:
            _fail("missing_envelope")
        return DispositionViewLabel.RECORDED_NOT_EXECUTABLE
    if disposition is Disposition.ACCEPT and message_type is MessageType.INFORMATIONAL:
        if instruction_ids:
            _fail("unexpected_envelope")
        return DispositionViewLabel.INFORMATIONAL
    _fail("unsupported_combination")


def _instruction_ids(outcome: ParseOutcome) -> tuple[str, ...]:
    identifiers: list[str] = []
    for instruction in outcome.instructions:
        identifier = instruction.instruction_id
        if type(identifier) is not str or identifier == "":
            _fail("invariant_violation")
        identifiers.append(identifier)
    return tuple(identifiers)


def _fail(code: str) -> NoReturn:
    raise DispositionViewError(code)
