"""Offline MIME normalization. HTML is text only; nothing is fetched or executed."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

from swingtrade.group4_email.contract import MAX_EMAIL_BYTES, ReasonCode

_FIXTURE_MESSAGE_ID = re.compile(r"^<[^<>\s@]+@example\.invalid>$")
_FORWARD_BANNER = re.compile(
    r"(?i)^(?:-+\s*forwarded message\s*-+|begin forwarded message)\s*$"
)
_OUTLOOK_ORIGINAL = re.compile(r"(?i)^-+\s*original message\s*-+\s*$")
_OUTLOOK_RULE = re.compile(r"^_{8,}\s*$")
_DISPLAY_VISIBLE = frozenset(
    {
        "block",
        "inline",
        "inline-block",
        "flex",
        "grid",
        "table",
        "table-row",
        "table-cell",
        "contents",
        "list-item",
        "flow-root",
    }
)
_ALLOWED_CHARSETS = frozenset({"utf-8", "us-ascii"})
_REMOTE_ATTRS = frozenset({"src", "href"})
_SKIP_TAGS = frozenset({"script", "style", "noscript"})
_BREAK_TAGS = frozenset({"p", "div", "br", "tr", "li", "h1", "h2", "h3", "table"})
_VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"}
)


@dataclass(frozen=True)
class NormalizedEmail:
    message_id: str | None
    message_id_reason: str | None
    plain_text: str | None
    html_text: str | None
    content_digest: str
    ignored_remote_references: int
    ignored_attachment_count: int
    reject_reason: str | None
    source_timestamp: str | None = None
    visibility_failure: str | None = None


class _HtmlText(HTMLParser):
    """Collect visible text. Hidden regions, script, and style are not used."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip = 0
        self._conceal: list[bool] = []
        self.remote_references = 0
        self.ambiguous = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        visibility = _visibility(attrs)
        if visibility == "ambiguous":
            self.ambiguous = True
        if lowered in _VOID_TAGS:
            self._count_remote(attrs)
            return
        conceal = lowered in _SKIP_TAGS or visibility == "hidden"
        if conceal:
            self._skip += 1
        self._conceal.append(conceal)
        if lowered in _BREAK_TAGS and self._skip == 0:
            self._parts.append("\n")
        self._count_remote(attrs)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in _VOID_TAGS:
            return
        if not self._conceal:
            self.ambiguous = True
            return
        conceal = self._conceal.pop()
        if conceal and self._skip:
            self._skip -= 1
        if lowered in _BREAK_TAGS and self._skip == 0:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip == 0 and not self.ambiguous:
            self._parts.append(data)

    def text(self) -> str:
        return "".join(self._parts)

    def _count_remote(self, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name.lower() not in _REMOTE_ATTRS or not value:
                continue
            target = value.strip()
            if "://" in target or target.startswith("//"):
                self.remote_references += 1


def content_digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalize_email(raw: bytes) -> NormalizedEmail:
    digest = content_digest(raw)
    if len(raw) > MAX_EMAIL_BYTES:
        return _rejected(digest, ReasonCode.OVERSIZED_INPUT)
    if not raw.strip():
        return _rejected(digest, ReasonCode.EMPTY_INPUT)

    message = BytesParser(policy=policy.default).parsebytes(raw)
    if message.defects:
        return _rejected(digest, ReasonCode.MALFORMED_MIME)

    message_id, message_id_reason = _message_id(message)
    plain_parts: list[str] = []
    html_parts: list[str] = []
    remote_references = 0
    attachment_count = 0

    for part in _leaf_parts(message):
        if _is_attachment(part):
            attachment_count += 1
            continue
        content_type = part.get_content_type()
        if content_type not in {"text/plain", "text/html"}:
            continue
        decoded, decode_reason = _decode(part)
        if decode_reason is not None:
            return _rejected(digest, decode_reason)
        assert decoded is not None
        if content_type == "text/plain":
            plain_parts.append(decoded)
            continue
        extractor = _HtmlText()
        extractor.feed(decoded)
        extractor.close()
        if extractor.ambiguous or any(extractor._conceal):
            return _rejected(
                digest,
                ReasonCode.AMBIGUOUS_VISIBILITY,
                message_id=message_id,
                message_id_reason=message_id_reason,
                source_timestamp=_source_timestamp(message),
                visibility_failure=ReasonCode.AMBIGUOUS_VISIBILITY.value,
            )
        html_parts.append(extractor.text())
        remote_references += extractor.remote_references

    plain = _join(plain_parts)
    html = _join(html_parts)
    if plain is None and html is None:
        return _rejected(digest, ReasonCode.NO_TEXT_BODY)
    return NormalizedEmail(
        message_id=message_id,
        message_id_reason=message_id_reason,
        plain_text=_authoritative(plain) if plain is not None else None,
        html_text=_authoritative(html) if html is not None else None,
        content_digest=digest,
        ignored_remote_references=remote_references,
        ignored_attachment_count=attachment_count,
        reject_reason=None,
        source_timestamp=_source_timestamp(message),
    )


def _rejected(
    digest: str,
    reason: ReasonCode,
    *,
    message_id: str | None = None,
    message_id_reason: str | None = None,
    source_timestamp: str | None = None,
    visibility_failure: str | None = None,
) -> NormalizedEmail:
    quarantine_visibility = reason is ReasonCode.AMBIGUOUS_VISIBILITY
    return NormalizedEmail(
        message_id=message_id,
        message_id_reason=message_id_reason,
        plain_text=None,
        html_text=None,
        content_digest=digest,
        ignored_remote_references=0,
        ignored_attachment_count=0,
        reject_reason=None if quarantine_visibility else reason.value,
        source_timestamp=source_timestamp,
        visibility_failure=visibility_failure,
    )


def _message_id(message: Message) -> tuple[str | None, str | None]:
    raw_id = message.get("Message-ID")
    if not isinstance(raw_id, str) or not raw_id.strip():
        return None, ReasonCode.MISSING_MESSAGE_ID.value
    token = raw_id.strip()
    if _FIXTURE_MESSAGE_ID.fullmatch(token) is None:
        return None, ReasonCode.NON_FIXTURE_MESSAGE_ID.value
    return token, None


def _leaf_parts(message: Message) -> list[Message]:
    if message.is_multipart():
        return [part for part in message.walk() if not part.is_multipart()]
    return [message]


def _is_attachment(part: Message) -> bool:
    disposition = part.get_content_disposition()
    if disposition == "attachment":
        return True
    filename = part.get_filename()
    return isinstance(filename, str) and filename != ""


def _decode(part: Message) -> tuple[str | None, ReasonCode | None]:
    charset = part.get_content_charset()
    if charset is not None and charset not in _ALLOWED_CHARSETS:
        return None, ReasonCode.UNSUPPORTED_CHARSET
    payload = part.get_payload(decode=True)
    if not isinstance(payload, bytes):
        return None, ReasonCode.MALFORMED_MIME
    encoding = "us-ascii" if charset == "us-ascii" else "utf-8"
    try:
        text = payload.decode(encoding)
    except UnicodeDecodeError:
        return None, ReasonCode.UNDECODABLE_BODY
    return text.replace("\r\n", "\n").replace("\r", "\n"), None


def _join(parts: list[str]) -> str | None:
    if not parts:
        return None
    return "\n".join(parts)


def _authoritative(text: str) -> str:
    """Drop quoted lines and forwarded header blocks. They are not economic authority."""

    lines = text.split("\n")
    kept: list[str] = []
    skipping_headers = False
    for line in lines:
        if _FORWARD_BANNER.match(line.strip()):
            skipping_headers = True
            continue
        if skipping_headers:
            if line.strip() == "":
                skipping_headers = False
            continue
        if _OUTLOOK_ORIGINAL.match(line.strip()) or _OUTLOOK_RULE.match(line.strip()):
            break
        if line.lstrip().startswith(">"):
            continue
        kept.append(line)
    return "\n".join(kept)


def _source_timestamp(message: Message) -> str | None:
    """Record one validated UTC timestamp. It is not an economic session date."""

    raw_date = message.get("Date")
    if not isinstance(raw_date, str) or raw_date.strip() == "":
        return None
    try:
        parsed = parsedate_to_datetime(raw_date.strip())
    except (TypeError, ValueError, IndexError, OverflowError):
        return None
    if parsed.tzinfo is None:
        return None
    utc = parsed.astimezone(UTC).replace(microsecond=0)
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def _visibility(attrs: list[tuple[str, str | None]]) -> str:
    style: str | None = None
    for name, value in attrs:
        lowered = name.lower()
        if lowered == "hidden":
            return "hidden"
        if lowered == "style" and value:
            style = value
    if style is None:
        return "visible"
    found = "visible"
    for part in style.split(";"):
        if ":" not in part:
            continue
        prop, raw_value = part.split(":", 1)
        prop = prop.strip().lower()
        value = raw_value.strip().lower().strip("\"'")
        if prop not in {"display", "visibility"}:
            continue
        if prop == "display" and value == "none":
            return "hidden"
        if prop == "visibility" and value == "hidden":
            return "hidden"
        if prop == "display" and value in _DISPLAY_VISIBLE:
            continue
        if prop == "visibility" and value == "visible":
            continue
        found = "ambiguous"
    return found
