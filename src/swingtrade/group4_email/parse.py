"""Raw email to a canonical TradeInstruction, or to reject / quarantine."""

from __future__ import annotations

from dataclasses import replace

from swingtrade.group4_email.contract import (
    Disposition,
    FieldEvidence,
    MessageType,
    ParseOutcome,
    ReasonCode,
    TradeInstruction,
)
from swingtrade.group4_email.extract import (
    Extraction,
    assign_instruction_ids,
    extract_text,
    projection,
)
from swingtrade.group4_email.normalize import normalize_email


class MessageIdentityRegistry:
    """One result per source message id. Economics alone never collapse messages."""

    def __init__(self) -> None:
        self._records: dict[str, ParseOutcome] = {}

    def __len__(self) -> int:
        return len(self._records)

    def parse(self, raw: bytes) -> ParseOutcome:
        return self.admit(parse_email(raw))

    def admit(self, outcome: ParseOutcome) -> ParseOutcome:
        message_id = outcome.message_id
        if message_id is None:
            return outcome
        existing = self._records.get(message_id)
        if existing is None:
            self._records[message_id] = outcome
            return outcome
        if existing.content_digest == outcome.content_digest:
            return existing
        return replace(
            outcome,
            disposition=Disposition.QUARANTINE,
            reasons=(ReasonCode.CONFLICTING_DUPLICATE.value,),
            instructions=(),
            evidence=(
                FieldEvidence("message_id", message_id),
                FieldEvidence("retained_digest", existing.content_digest),
                FieldEvidence("conflicting_digest", outcome.content_digest),
            ),
        )


def parse_email(raw: object, registry: MessageIdentityRegistry | None = None) -> ParseOutcome:
    outcome = _parse_email(raw)
    if registry is None:
        return outcome
    return registry.admit(outcome)


def _parse_email(raw: object) -> ParseOutcome:
    if type(raw) is not bytes:
        return _outcome(Disposition.REJECT, MessageType.UNKNOWN, (ReasonCode.INVALID_INPUT.value,))
    normalized = normalize_email(raw)
    if normalized.reject_reason is not None:
        return _outcome(
            Disposition.REJECT,
            MessageType.UNKNOWN,
            (normalized.reject_reason,),
            digest=normalized.content_digest,
        )

    plain = extract_text(normalized.plain_text) if normalized.plain_text is not None else None
    html = extract_text(normalized.html_text) if normalized.html_text is not None else None
    chosen: Extraction | None
    if plain is not None and html is not None and projection(plain) != projection(html):
        chosen = _quarantine(plain, (ReasonCode.HTML_PLAIN_CONFLICT.value,))
    else:
        chosen = plain if plain is not None else html
    if chosen is None:
        return _outcome(
            Disposition.REJECT,
            MessageType.UNKNOWN,
            (ReasonCode.NO_TEXT_BODY.value,),
            digest=normalized.content_digest,
        )
    if normalized.message_id_reason is not None:
        chosen = _quarantine(chosen, (normalized.message_id_reason,))
    chosen = assign_instruction_ids(chosen, normalized.content_digest)
    return _outcome(
        chosen.disposition,
        chosen.message_type,
        chosen.reasons,
        chosen.instructions,
        chosen.evidence,
        digest=normalized.content_digest,
        message_id=normalized.message_id,
        remote_references=normalized.ignored_remote_references,
        attachment_count=normalized.ignored_attachment_count,
    )


def _quarantine(extraction: Extraction, extra: tuple[str, ...]) -> Extraction:
    reasons = tuple(dict.fromkeys((*extraction.reasons, *extra)))
    return replace(
        extraction,
        disposition=Disposition.QUARANTINE,
        reasons=reasons,
        instructions=(),
    )


def _outcome(
    disposition: Disposition,
    message_type: MessageType,
    reasons: tuple[str, ...],
    instructions: tuple[TradeInstruction, ...] = (),
    evidence: tuple[FieldEvidence, ...] = (),
    *,
    digest: str = "",
    message_id: str | None = None,
    remote_references: int = 0,
    attachment_count: int = 0,
) -> ParseOutcome:
    return ParseOutcome(
        disposition=disposition,
        message_type=message_type,
        reasons=reasons,
        instructions=instructions,
        evidence=evidence,
        content_digest=digest,
        message_id=message_id,
        ignored_remote_references=remote_references,
        ignored_attachment_count=attachment_count,
    )
