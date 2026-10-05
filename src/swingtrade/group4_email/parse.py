"""Raw email to a canonical instruction envelope, or to reject / quarantine."""

from __future__ import annotations

import threading
from dataclasses import replace

from swingtrade.group4_email.contract import (
    EMAIL_RETENTION_POLICY,
    PARSER_VERSION,
    SCHEMA_VERSION,
    CanonicalInstructionEnvelope,
    Disposition,
    FieldEvidence,
    MessageType,
    ParseOutcome,
    ParseProvenance,
    ProviderType,
    ReasonCode,
)
from swingtrade.group4_email.extract import (
    Extraction,
    assign_instruction_ids,
    extract_text,
    projection,
)
from swingtrade.group4_email.normalize import NormalizedEmail, content_digest, normalize_email


class _Poison:
    """Two distinct bodies contended for one unseen source identity."""


class MessageIdentityRegistry:
    """One admitted outcome per source message id.

    Economics alone never collapse messages. If two different bodies overlap
    before either commit for an unseen id, both fail closed and neither is
    stored as accepted.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: dict[str, ParseOutcome | _Poison] = {}
        self._open: dict[str, set[str]] = {}
        self._open_count: dict[str, int] = {}

    def __len__(self) -> int:
        with self._lock:
            return sum(isinstance(value, ParseOutcome) for value in self._records.values())

    def parse(self, raw: bytes) -> ParseOutcome:
        if type(raw) is not bytes:
            return _parse_email(raw)
        digest = content_digest(raw)
        normalized = normalize_email(raw)
        message_id = normalized.message_id
        if message_id is None:
            return _from_normalized(normalized)
        self._enter(message_id, digest)
        try:
            outcome = _from_normalized(normalized)
        except BaseException:
            self._leave(message_id)
            raise
        return self._commit(message_id, digest, outcome)

    def admit(self, outcome: ParseOutcome) -> ParseOutcome:
        message_id = outcome.message_id
        if message_id is None:
            return outcome
        with self._lock:
            return self._store(message_id, outcome.content_digest, outcome, overlap=False)

    def _enter(self, message_id: str, digest: str) -> None:
        with self._lock:
            self._open.setdefault(message_id, set()).add(digest)
            self._open_count[message_id] = self._open_count.get(message_id, 0) + 1

    def _leave(self, message_id: str) -> None:
        with self._lock:
            remaining = self._open_count.get(message_id, 0) - 1
            if remaining <= 0:
                self._open.pop(message_id, None)
                self._open_count.pop(message_id, None)
            else:
                self._open_count[message_id] = remaining

    def _commit(self, message_id: str, digest: str, outcome: ParseOutcome) -> ParseOutcome:
        with self._lock:
            cohort = set(self._open.get(message_id, set()))
            remaining = self._open_count.get(message_id, 1) - 1
            if remaining <= 0:
                self._open.pop(message_id, None)
                self._open_count.pop(message_id, None)
            else:
                self._open_count[message_id] = remaining
            return self._store(message_id, digest, outcome, overlap=len(cohort) > 1)

    def _store(
        self,
        message_id: str,
        digest: str,
        outcome: ParseOutcome,
        *,
        overlap: bool,
    ) -> ParseOutcome:
        existing = self._records.get(message_id)
        if overlap or isinstance(existing, _Poison):
            self._records[message_id] = _Poison()
            return _conflict(outcome, message_id, digest, existing)
        if isinstance(existing, ParseOutcome):
            if existing.content_digest == digest:
                return existing
            return _conflict(outcome, message_id, digest, existing)
        self._records[message_id] = outcome
        return outcome


def parse_email(raw: object, registry: MessageIdentityRegistry | None = None) -> ParseOutcome:
    if registry is not None and type(raw) is bytes:
        return registry.parse(raw)
    return _parse_email(raw)


def _parse_email(raw: object) -> ParseOutcome:
    if type(raw) is not bytes:
        return _outcome(Disposition.REJECT, MessageType.UNKNOWN, (ReasonCode.INVALID_INPUT.value,))
    return _from_normalized(normalize_email(raw))


def _from_normalized(normalized: NormalizedEmail) -> ParseOutcome:
    digest = normalized.content_digest
    message_id = normalized.message_id
    timestamp = normalized.source_timestamp
    if normalized.visibility_failure is not None:
        return _outcome(
            Disposition.QUARANTINE,
            MessageType.UNKNOWN,
            (normalized.visibility_failure,),
            digest=digest,
            message_id=message_id,
            source_timestamp=timestamp,
        )
    if normalized.reject_reason is not None:
        return _outcome(
            Disposition.REJECT,
            MessageType.UNKNOWN,
            (normalized.reject_reason,),
            digest=digest,
            source_timestamp=timestamp,
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
            digest=digest,
            source_timestamp=timestamp,
        )
    if normalized.message_id_reason is not None:
        chosen = _quarantine(chosen, (normalized.message_id_reason,))
    envelopes: tuple[CanonicalInstructionEnvelope, ...] = ()
    if chosen.disposition is Disposition.ACCEPT:
        envelopes = assign_instruction_ids(chosen, digest)
    return _outcome(
        chosen.disposition,
        chosen.message_type,
        chosen.reasons,
        envelopes,
        chosen.evidence,
        digest=digest,
        message_id=message_id,
        source_timestamp=timestamp,
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


def _conflict(
    outcome: ParseOutcome,
    message_id: str,
    digest: str,
    existing: ParseOutcome | _Poison | None,
) -> ParseOutcome:
    retained = existing.content_digest if isinstance(existing, ParseOutcome) else ""
    return replace(
        outcome,
        disposition=Disposition.QUARANTINE,
        reasons=(ReasonCode.CONFLICTING_DUPLICATE.value,),
        instructions=(),
        evidence=(
            FieldEvidence("message_id", message_id),
            FieldEvidence("retained_digest", retained),
            FieldEvidence("conflicting_digest", digest),
        ),
    )


def _provenance(
    digest: str,
    message_id: str | None,
    source_timestamp: str | None,
) -> ParseProvenance:
    return ParseProvenance(
        retention_policy=EMAIL_RETENTION_POLICY,
        provider_type=ProviderType.FIXTURE.value,
        provider_message_ref=message_id,
        raw_sha256=digest,
        parser_version=PARSER_VERSION,
        schema_version=SCHEMA_VERSION,
        source_timestamp=source_timestamp,
    )


def _outcome(
    disposition: Disposition,
    message_type: MessageType,
    reasons: tuple[str, ...],
    instructions: tuple[CanonicalInstructionEnvelope, ...] = (),
    evidence: tuple[FieldEvidence, ...] = (),
    *,
    digest: str = "",
    message_id: str | None = None,
    source_timestamp: str | None = None,
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
        provenance=_provenance(digest, message_id, source_timestamp),
        ignored_remote_references=remote_references,
        ignored_attachment_count=attachment_count,
    )
