"""Injected-transport Gmail read-only acquisition.

The transport is supplied by the caller. This module does not open a socket,
read a credential, send mail, or submit an order. Message bytes are parsed
and then dropped. Evidence keeps hashes, dispositions, and identities.
"""

from __future__ import annotations

import base64
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from swingtrade.group4_email.contract import EMAIL_RETENTION_POLICY
from swingtrade.group4_email.parse import MessageIdentityRegistry, parse_email

READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
DURABLE_STATE = "UNAVAILABLE"
MAX_LIST_RESULTS = 10
_API = "https://gmail.googleapis.com/gmail/v1/users/me/"
_PROFILE = _API + "profile"
_LABELS = _API + "labels"
_MESSAGES = _API + "messages"
_SELECTOR = re.compile(r"^(from|label):[A-Za-z0-9][A-Za-z0-9._+@-]{0,63}$")
_MESSAGE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_HEADER_NAME = re.compile(r"^[A-Za-z0-9-]{1,64}$")


class PilotRejected(Exception):
    """Fail-closed pilot error. The message is a stable code and nothing else."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or code == "":
            code = "GMAIL_PILOT_TRANSPORT_REJECTED"
        super().__init__(code)
        self.code = code

    def __repr__(self) -> str:
        return f"PilotRejected({self.code!r})"

    def __str__(self) -> str:
        return self.code


class PilotTransport(Protocol):
    """One injected exchange. The pilot calls it with GET only."""

    def exchange(self, method: str, url: str) -> tuple[int, bytes]:
        """Return one HTTP status and raw body, or raise TimeoutError."""


@dataclass(frozen=True)
class AcquiredMessage:
    """One provider message after parsing. The MIME body is not retained."""

    provider_message_id: str
    disposition: str
    reasons: tuple[str, ...]
    instruction_ids: tuple[str, ...]
    content_digest: str
    provider_message_ref: str | None
    source_timestamp: str | None
    duplicate: bool


@dataclass(frozen=True)
class PilotEvidence:
    """Offline acquisition result. It cannot become durable or economic."""

    durable_state: str
    economic_dispatch: bool
    scope: str
    retention_policy: str
    messages: tuple[AcquiredMessage, ...]
    content_retained: bool
    request_count: int
    ignored_attachment_count: int

    def __post_init__(self) -> None:
        if self.durable_state != DURABLE_STATE or self.economic_dispatch is not False:
            raise RuntimeError("pilot evidence is non-durable and non-economic")
        if self.content_retained is not False:
            raise RuntimeError("pilot evidence retains no content")
        if self.scope != READONLY_SCOPE or self.retention_policy != EMAIL_RETENTION_POLICY:
            raise RuntimeError("pilot scope and retention are fixed")
        if self.request_count < 0 or self.request_count > 3 + MAX_LIST_RESULTS:
            raise RuntimeError("pilot request count is outside the offline cap")
        if len(self.messages) > MAX_LIST_RESULTS:
            raise RuntimeError("pilot message count is outside the offline cap")


def acquire_readonly_messages(
    transport: PilotTransport,
    selectors: tuple[str, ...],
    *,
    limit: int = MAX_LIST_RESULTS,
    registry: MessageIdentityRegistry | None = None,
    seen_provider_ids: set[str] | None = None,
) -> PilotEvidence:
    """Read at most ten messages through the injected transport.

    ``selectors`` may contain only local ``from:`` and ``label:`` terms.
    A provider message id is remembered in ``seen_provider_ids`` and is never
    used as an instruction id. The same MIME bytes stay subject to the parser
    registry when the caller supplies one.
    """

    if type(limit) is not int or limit < 1 or limit > MAX_LIST_RESULTS:
        raise PilotRejected("GMAIL_PILOT_LIMIT_REJECTED")
    if type(selectors) is not tuple or selectors == ():
        raise PilotRejected("GMAIL_PILOT_SELECTOR_REJECTED")
    if any(type(item) is not str or _SELECTOR.fullmatch(item) is None for item in selectors):
        raise PilotRejected("GMAIL_PILOT_SELECTOR_REJECTED")
    if registry is not None and type(registry) is not MessageIdentityRegistry:
        raise PilotRejected("GMAIL_PILOT_TRANSPORT_REJECTED")
    if seen_provider_ids is not None and type(seen_provider_ids) is not set:
        raise PilotRejected("GMAIL_PILOT_TRANSPORT_REJECTED")
    active_registry = MessageIdentityRegistry() if registry is None else registry
    seen = set() if seen_provider_ids is None else seen_provider_ids
    session = _Session(transport)
    profile = session.get_object(_PROFILE)
    if type(profile.get("emailAddress")) is not str or profile.get("emailAddress") == "":
        raise PilotRejected("GMAIL_PILOT_MALFORMED")
    labels = session.get_object(_LABELS)
    if type(labels.get("labels")) is not list:
        raise PilotRejected("GMAIL_PILOT_MALFORMED")
    listed = session.get_object(_list_url(selectors, limit))
    rows = listed.get("messages", [])
    if type(rows) is not list or len(rows) > limit:
        raise PilotRejected("GMAIL_PILOT_MALFORMED")
    messages: list[AcquiredMessage] = []
    ignored = 0
    for row in rows:
        provider_id = row.get("id") if type(row) is dict else None
        if type(provider_id) is not str or _MESSAGE_ID.fullmatch(provider_id) is None:
            raise PilotRejected("GMAIL_PILOT_MALFORMED")
        if provider_id in seen:
            messages.append(_duplicate(provider_id))
            continue
        seen.add(provider_id)
        fetched, payload = session.get_message(_message_url(provider_id))
        if not fetched or payload is None:
            messages.append(_partial(provider_id))
            continue
        mime, skipped = _mime_from_payload(payload)
        ignored += skipped
        if mime is None:
            messages.append(_partial(provider_id))
            continue
        outcome = parse_email(mime, active_registry)
        instruction_ids = tuple(item.instruction_id for item in outcome.instructions)
        if any(item == provider_id or item == outcome.message_id for item in instruction_ids):
            raise PilotRejected("GMAIL_PILOT_IDENTITY_REJECTED")
        messages.append(
            AcquiredMessage(
                provider_message_id=provider_id,
                disposition=outcome.disposition.value,
                reasons=tuple(outcome.reasons),
                instruction_ids=instruction_ids,
                content_digest=outcome.content_digest,
                provider_message_ref=outcome.provenance.provider_message_ref,
                source_timestamp=outcome.provenance.source_timestamp,
                duplicate=False,
            )
        )
    return PilotEvidence(
        durable_state=DURABLE_STATE,
        economic_dispatch=False,
        scope=READONLY_SCOPE,
        retention_policy=EMAIL_RETENTION_POLICY,
        messages=tuple(messages),
        content_retained=False,
        request_count=session.request_count,
        ignored_attachment_count=ignored,
    )


class _Session:
    def __init__(self, transport: PilotTransport) -> None:
        self._transport = transport
        self.request_count = 0

    def get_object(self, url: str) -> dict[str, object]:
        status, body = self._exchange(url)
        if status != 200 or body is None:
            raise PilotRejected("GMAIL_PILOT_PROVIDER_ERROR")
        return body

    def get_message(self, url: str) -> tuple[bool, dict[str, object] | None]:
        status, body = self._exchange(url)
        if status == 404:
            return False, None
        if status != 200 or body is None:
            raise PilotRejected("GMAIL_PILOT_PROVIDER_ERROR")
        payload = body.get("payload")
        if type(payload) is not dict:
            return False, None
        return True, payload

    def _exchange(self, url: str) -> tuple[int, dict[str, object] | None]:
        _require_readonly_url(url)
        if self.request_count >= 3 + MAX_LIST_RESULTS:
            raise PilotRejected("GMAIL_PILOT_LIMIT_REJECTED")
        try:
            status, raw = self._transport.exchange("GET", url)
        except PilotRejected:
            raise
        except TimeoutError:
            raise PilotRejected("GMAIL_PILOT_TIMEOUT") from None
        except Exception:
            raise PilotRejected("GMAIL_PILOT_TRANSPORT_REJECTED") from None
        self.request_count += 1
        if type(status) is not int or type(raw) is not bytes:
            raise PilotRejected("GMAIL_PILOT_MALFORMED")
        if status in {401, 403}:
            raise PilotRejected("GMAIL_PILOT_DENIED")
        if status not in {200, 404}:
            raise PilotRejected("GMAIL_PILOT_PROVIDER_ERROR")
        if status == 404:
            return status, None
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            raise PilotRejected("GMAIL_PILOT_MALFORMED") from None
        if type(parsed) is not dict:
            raise PilotRejected("GMAIL_PILOT_MALFORMED")
        return status, dict(parsed)


def _duplicate(provider_id: str) -> AcquiredMessage:
    return AcquiredMessage(
        provider_message_id=provider_id,
        disposition="DUPLICATE",
        reasons=("DUPLICATE_PROVIDER_MESSAGE",),
        instruction_ids=(),
        content_digest="",
        provider_message_ref=None,
        source_timestamp=None,
        duplicate=True,
    )


def _partial(provider_id: str) -> AcquiredMessage:
    return AcquiredMessage(
        provider_message_id=provider_id,
        disposition="QUARANTINE",
        reasons=("GMAIL_PILOT_PARTIAL",),
        instruction_ids=(),
        content_digest="",
        provider_message_ref=None,
        source_timestamp=None,
        duplicate=False,
    )


def _list_url(selectors: tuple[str, ...], limit: int) -> str:
    query = _quote(" ".join(selectors))
    return f"{_MESSAGES}?maxResults={limit}&q={query}"


def _message_url(provider_id: str) -> str:
    return f"{_MESSAGES}/{_quote(provider_id)}?format=full"


def _require_readonly_url(url: str) -> None:
    if not url.startswith(_API) or "#" in url or "\\" in url or " " in url:
        raise PilotRejected("GMAIL_PILOT_ENDPOINT_REJECTED")
    path, separator, query = url[len(_API) :].partition("?")
    pairs = _query(query) if separator else ()
    if pairs is None:
        raise PilotRejected("GMAIL_PILOT_ENDPOINT_REJECTED")
    if path == "profile" or path == "labels":
        allowed = not pairs
    elif path == "messages":
        allowed = len(pairs) == 2 and pairs[0][0] == "maxResults" and pairs[1][0] == "q"
    elif path.startswith("messages/"):
        message_id = path.removeprefix("messages/")
        allowed = (
            _MESSAGE_ID.fullmatch(message_id) is not None
            and pairs == (("format", "full"),)
        )
    else:
        allowed = False
    if not allowed:
        raise PilotRejected("GMAIL_PILOT_ENDPOINT_REJECTED")


def _query(query: str) -> tuple[tuple[str, str], ...] | None:
    if query == "":
        return ()
    pairs: list[tuple[str, str]] = []
    for part in query.split("&"):
        key, separator, value = part.partition("=")
        if separator != "=" or key == "" or value == "":
            return None
        pairs.append((key, value))
    return tuple(pairs)


def _quote(value: str) -> str:
    encoded: list[str] = []
    for char in value:
        if char.isalnum() or char in "-._~":
            encoded.append(char)
        else:
            encoded.append(f"%{ord(char):02X}")
    return "".join(encoded)


def _mime_from_payload(payload: Mapping[str, object]) -> tuple[bytes | None, int]:
    mime_type = payload.get("mimeType")
    if mime_type == "message/rfc822":
        return _decode_body(payload), 0
    if mime_type in {"text/plain", "text/html"}:
        text = _text_part(payload)
        if text is None:
            return None, 0
        return _single_part(payload, mime_type, text), 0
    if type(mime_type) is str and mime_type.startswith("multipart/"):
        return _multipart(payload)
    return None, 0


def _multipart(payload: Mapping[str, object]) -> tuple[bytes | None, int]:
    parts = payload.get("parts")
    if type(parts) is not list:
        return None, 0
    plain: str | None = None
    html: str | None = None
    ignored = 0
    for part in parts:
        if type(part) is not dict:
            return None, ignored
        if _attachment(part):
            ignored += 1
            continue
        kind = part.get("mimeType")
        text = _text_part(part)
        if text is None or kind not in {"text/plain", "text/html"}:
            return None, ignored
        if kind == "text/plain":
            plain = text if plain is None else plain + "\n" + text
        else:
            html = text if html is None else html + "\n" + text
    if plain is None and html is None:
        return None, ignored
    lines = _header_lines(payload)
    if lines is None:
        return None, ignored
    boundary = "pilot-boundary"
    chunks = [
        "\r\n".join(lines),
        "MIME-Version: 1.0",
        f'Content-Type: multipart/alternative; boundary="{boundary}"',
        "",
    ]
    if plain is not None:
        chunks.extend(("", f"--{boundary}", "Content-Type: text/plain; charset=utf-8", "", plain))
    if html is not None:
        chunks.extend(("", f"--{boundary}", "Content-Type: text/html; charset=utf-8", "", html))
    chunks.extend(("", f"--{boundary}--", ""))
    return "\r\n".join(chunks).encode("utf-8"), ignored


def _single_part(payload: Mapping[str, object], mime_type: str, text: str) -> bytes | None:
    lines = _header_lines(payload)
    if lines is None:
        return None
    subtype = "plain" if mime_type == "text/plain" else "html"
    header = "\r\n".join(lines)
    body = (
        f"{header}\r\nMIME-Version: 1.0\r\n"
        f"Content-Type: text/{subtype}; charset=utf-8\r\n\r\n{text}"
    )
    return body.encode("utf-8")


def _header_lines(payload: Mapping[str, object]) -> list[str] | None:
    if "headers" not in payload:
        return []
    headers = payload.get("headers")
    if type(headers) is not list:
        return None
    lines: list[str] = []
    for item in headers:
        if type(item) is not dict:
            return None
        name = item.get("name")
        value = item.get("value")
        if type(name) is not str or type(value) is not str:
            return None
        if _HEADER_NAME.fullmatch(name) is None or "\r" in value or "\n" in value:
            return None
        if name.lower() in {"mime-version", "content-type", "content-transfer-encoding"}:
            continue
        lines.append(f"{name}: {value}")
    return lines


def _text_part(payload: Mapping[str, object]) -> str | None:
    raw = _decode_body(payload)
    if raw is None:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeError:
        return None


def _decode_body(payload: Mapping[str, object]) -> bytes | None:
    body = payload.get("body")
    if type(body) is not dict or "attachmentId" in body:
        return None
    data = body.get("data")
    if data is None:
        return b""
    if type(data) is not str:
        return None
    try:
        return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
    except ValueError:
        return None


def _attachment(part: Mapping[str, object]) -> bool:
    filename = part.get("filename")
    body = part.get("body")
    if type(filename) is str and filename != "":
        return True
    return type(body) is dict and "attachmentId" in body
