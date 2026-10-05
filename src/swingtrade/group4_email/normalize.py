"""Offline MIME normalization. HTML is text only; nothing is fetched or executed."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from email import policy
from email.message import Message
from email.parser import BytesParser
from html.parser import HTMLParser

from swingtrade.group4_email.contract import MAX_EMAIL_BYTES, ReasonCode

_FIXTURE_MESSAGE_ID = re.compile(r"^<[^<>\s@]+@example\.invalid>$")
_FORWARD_BANNER = re.compile(
    r"(?i)^(?:-+\s*forwarded message\s*-+|begin forwarded message)\s*$"
)
_ALLOWED_CHARSETS = frozenset({"utf-8", "us-ascii"})
_REMOTE_ATTRS = frozenset({"src", "href"})
_SKIP_TAGS = frozenset({"script", "style", "noscript"})
_BREAK_TAGS = frozenset({"p", "div", "br", "tr", "li", "h1", "h2", "h3", "table"})


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


class _HtmlText(HTMLParser):
    """Collect visible text. Script, style, and remote targets are not used."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip = 0
        self.remote_references = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in _SKIP_TAGS:
            self._skip += 1
        if lowered in _BREAK_TAGS:
            self._parts.append("\n")
        self._count_remote(attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in _SKIP_TAGS and self._skip:
            self._skip -= 1
        if tag.lower() in _BREAK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip == 0:
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
    )


def _rejected(digest: str, reason: ReasonCode) -> NormalizedEmail:
    return NormalizedEmail(
        message_id=None,
        message_id_reason=None,
        plain_text=None,
        html_text=None,
        content_digest=digest,
        ignored_remote_references=0,
        ignored_attachment_count=0,
        reject_reason=reason.value,
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
        if line.lstrip().startswith(">"):
            continue
        kept.append(line)
    return "\n".join(kept)
