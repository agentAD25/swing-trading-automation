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
from dataclasses import dataclass, field
from typing import Protocol

from swingtrade.group4_email.contract import EMAIL_RETENTION_POLICY
from swingtrade.group4_email.local_oauth_probe import (
    LocalOAuthProbeRejected,
    require_exact_granted_scope,
)
from swingtrade.group4_email.normalize import message_id_classification
from swingtrade.group4_email.parse import MessageIdentityRegistry, parse_email

READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
DURABLE_STATE = "UNAVAILABLE"
MAX_LIST_RESULTS = 10
_MAX_TOKEN_ATTEMPTS = 20
_MAX_READ_GETS = 50
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_RETRY_STATUSES = frozenset({429, 500})
_GET_ATTEMPTS = 3
_API = "https://gmail.googleapis.com/gmail/v1/users/me/"
_PROFILE = _API + "profile"
_LABELS = _API + "labels"
_MESSAGES = _API + "messages"
_SELECTOR = re.compile(r"^(from|label):[A-Za-z0-9][A-Za-z0-9._+@-]{0,63}$")
_MESSAGE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_PAGE_TOKEN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
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

    def exchange(self, method: str, url: str, body: bytes = b"") -> tuple[int, bytes]:
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
    rfc_message_id: str | None = None
    actionable: bool = False


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
        if self.request_count < 0 or self.request_count > _MAX_READ_GETS:
            raise RuntimeError("pilot request count is outside the offline cap")
        if len(self.messages) > MAX_LIST_RESULTS:
            raise RuntimeError("pilot message count is outside the offline cap")


@dataclass
class ReadBudget:
    """Caller-held request counts. A restart passes the same counts forward."""

    token_attempts: int = 0
    read_gets: int = 0

    def __post_init__(self) -> None:
        if type(self.token_attempts) is not int or type(self.read_gets) is not int:
            raise PilotRejected("GMAIL_PILOT_BUDGET_EXHAUSTED")
        if not 0 <= self.token_attempts <= _MAX_TOKEN_ATTEMPTS:
            raise PilotRejected("GMAIL_PILOT_BUDGET_EXHAUSTED")
        if not 0 <= self.read_gets <= _MAX_READ_GETS:
            raise PilotRejected("GMAIL_PILOT_BUDGET_EXHAUSTED")


@dataclass
class TokenGrant:
    """In-memory grant. Ordinary repr omits both token values."""

    scope: str
    access_token: str = field(repr=False)
    refresh_token: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.scope != READONLY_SCOPE or self.access_token == "":
            raise PilotRejected("GMAIL_PILOT_SCOPE_REJECTED")
        if self.refresh_token is not None and self.refresh_token == "":
            raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")


def acquire_readonly_messages(
    transport: PilotTransport,
    selectors: tuple[str, ...],
    *,
    limit: int = MAX_LIST_RESULTS,
    registry: MessageIdentityRegistry | None = None,
    seen_provider_ids: set[str] | None = None,
    granted_scope: str = READONLY_SCOPE,
    budget: ReadBudget | None = None,
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
    if granted_scope != READONLY_SCOPE:
        raise PilotRejected("GMAIL_PILOT_SCOPE_REJECTED")
    if budget is not None and type(budget) is not ReadBudget:
        raise PilotRejected("GMAIL_PILOT_BUDGET_EXHAUSTED")
    active_registry = MessageIdentityRegistry() if registry is None else registry
    seen = set() if seen_provider_ids is None else seen_provider_ids
    seen_rfc: dict[str, str] = {}
    session = _Session(transport, budget or ReadBudget())
    profile = session.get_object(_PROFILE)
    if type(profile.get("emailAddress")) is not str or profile.get("emailAddress") == "":
        raise PilotRejected("GMAIL_PILOT_MALFORMED")
    labels = session.get_object(_LABELS)
    if type(labels.get("labels")) is not list:
        raise PilotRejected("GMAIL_PILOT_MALFORMED")
    rows = _collect_ids(session, selectors, limit)
    messages: list[AcquiredMessage] = []
    ignored = 0
    for provider_id in rows:
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
        kind, rfc_message_id = message_id_classification(mime)
        acquired = _acquired(provider_id, outcome, kind, rfc_message_id)
        if rfc_message_id is not None:
            previous = seen_rfc.get(rfc_message_id)
            if previous is None:
                seen_rfc[rfc_message_id] = acquired.content_digest
            elif previous == acquired.content_digest:
                acquired = _duplicate(provider_id, rfc_message_id)
            else:
                acquired = _conflict(provider_id, rfc_message_id)
        if any(item == provider_id or item == rfc_message_id for item in acquired.instruction_ids):
            raise PilotRejected("GMAIL_PILOT_IDENTITY_REJECTED")
        messages.append(acquired)
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
    def __init__(self, transport: PilotTransport, budget: ReadBudget) -> None:
        self._transport = transport
        self._budget = budget
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
        for attempt in range(_GET_ATTEMPTS):
            self._consume_get()
            status, raw = self._call("GET", url, b"", "GMAIL_PILOT_TIMEOUT")
            if status in _REDIRECT_STATUSES:
                raise PilotRejected("GMAIL_PILOT_REDIRECT_REJECTED")
            if status in _RETRY_STATUSES and attempt + 1 < _GET_ATTEMPTS:
                continue
            if status in _RETRY_STATUSES:
                raise PilotRejected("GMAIL_PILOT_RETRY_EXHAUSTED")
            return _interpret_response(status, raw)
        raise PilotRejected("GMAIL_PILOT_RETRY_EXHAUSTED")

    def _consume_get(self) -> None:
        if self._budget.read_gets >= _MAX_READ_GETS or self.request_count >= _MAX_READ_GETS:
            raise PilotRejected("GMAIL_PILOT_BUDGET_EXHAUSTED")
        self._budget.read_gets += 1
        self.request_count += 1

    def _call(self, method: str, url: str, body: bytes, timeout_code: str) -> tuple[int, bytes]:
        try:
            if method == "POST":
                status, raw = self._transport.exchange(method, url, body)
            else:
                status, raw = self._transport.exchange(method, url)
        except PilotRejected:
            raise
        except TimeoutError:
            raise PilotRejected(timeout_code) from None
        except Exception:
            if method == "POST":
                raise PilotRejected("GMAIL_PILOT_TOKEN_AMBIGUOUS") from None
            raise PilotRejected("GMAIL_PILOT_TRANSPORT_REJECTED") from None
        if type(status) is not int or type(raw) is not bytes:
            raise PilotRejected("GMAIL_PILOT_MALFORMED")
        return status, raw


def _interpret_response(status: int, raw: bytes) -> tuple[int, dict[str, object] | None]:
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


def _acquired(
    provider_id: str,
    outcome: object,
    kind: str,
    rfc_message_id: str | None,
) -> AcquiredMessage:
    from swingtrade.group4_email.contract import Disposition, ParseOutcome

    if type(outcome) is not ParseOutcome:
        raise PilotRejected("GMAIL_PILOT_MALFORMED")
    disposition = outcome.disposition.value
    reasons = tuple(outcome.reasons)
    instruction_ids = tuple(item.instruction_id for item in outcome.instructions)
    actionable = outcome.disposition is Disposition.ACCEPT and kind == "FIXTURE"
    if kind != "FIXTURE":
        actionable = False
        instruction_ids = ()
        if outcome.disposition is Disposition.ACCEPT:
            disposition = "QUARANTINE"
            reasons = tuple(dict.fromkeys((*reasons, "NON_FIXTURE_MESSAGE_ID")))
    return AcquiredMessage(
        provider_message_id=provider_id,
        disposition=disposition,
        reasons=reasons,
        instruction_ids=instruction_ids,
        content_digest=outcome.content_digest,
        provider_message_ref=outcome.provenance.provider_message_ref,
        source_timestamp=outcome.provenance.source_timestamp,
        duplicate=False,
        rfc_message_id=rfc_message_id,
        actionable=actionable,
    )


def _conflict(provider_id: str, rfc_message_id: str) -> AcquiredMessage:
    return AcquiredMessage(
        provider_message_id=provider_id,
        disposition="QUARANTINE",
        reasons=("CONFLICTING_DUPLICATE",),
        instruction_ids=(),
        content_digest="",
        provider_message_ref=None,
        source_timestamp=None,
        duplicate=False,
        rfc_message_id=rfc_message_id,
        actionable=False,
    )


def _duplicate(provider_id: str, rfc_message_id: str | None = None) -> AcquiredMessage:
    return AcquiredMessage(
        provider_message_id=provider_id,
        disposition="DUPLICATE",
        reasons=("DUPLICATE_PROVIDER_MESSAGE",),
        instruction_ids=(),
        content_digest="",
        provider_message_ref=None,
        source_timestamp=None,
        duplicate=True,
        rfc_message_id=rfc_message_id,
        actionable=False,
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


def _collect_ids(session: _Session, selectors: tuple[str, ...], limit: int) -> list[str]:
    collected: list[str] = []
    page_token: str | None = None
    for _page in range(2):
        listed = session.get_object(_list_url(selectors, limit, page_token))
        rows = listed.get("messages", [])
        if type(rows) is not list:
            raise PilotRejected("GMAIL_PILOT_MALFORMED")
        for row in rows:
            provider_id = row.get("id") if type(row) is dict else None
            if type(provider_id) is not str or _MESSAGE_ID.fullmatch(provider_id) is None:
                raise PilotRejected("GMAIL_PILOT_MALFORMED")
            collected.append(provider_id)
            if len(collected) > limit:
                raise PilotRejected("GMAIL_PILOT_MALFORMED")
        token = listed.get("nextPageToken")
        if len(collected) >= limit or token is None:
            return collected
        if type(token) is not str or _PAGE_TOKEN.fullmatch(token) is None:
            raise PilotRejected("GMAIL_PILOT_MALFORMED")
        page_token = token
    return collected


def _list_url(selectors: tuple[str, ...], limit: int, page_token: str | None = None) -> str:
    query = _quote(" ".join(selectors))
    url = f"{_MESSAGES}?maxResults={limit}&q={query}"
    if page_token is None:
        return url
    return url + "&pageToken=" + _quote(page_token)


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
        allowed = _message_list_query(pairs)
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


def _message_list_query(pairs: tuple[tuple[str, str], ...]) -> bool:
    if len(pairs) == 2:
        return pairs[0][0] == "maxResults" and pairs[1][0] == "q"
    if len(pairs) != 3:
        return False
    return (
        pairs[0][0] == "maxResults"
        and pairs[1][0] == "q"
        and pairs[2][0] == "pageToken"
        and _PAGE_TOKEN.fullmatch(pairs[2][1]) is not None
    )


def exchange_readonly_grant(
    transport: PilotTransport,
    form: tuple[tuple[str, str], ...],
    *,
    budget: ReadBudget | None = None,
) -> TokenGrant:
    """Exchange or refresh one readonly grant. Ambiguous failures are not retried."""

    active = budget if budget is not None else ReadBudget()
    if type(active) is not ReadBudget:
        raise PilotRejected("GMAIL_PILOT_BUDGET_EXHAUSTED")
    if active.token_attempts >= _MAX_TOKEN_ATTEMPTS:
        raise PilotRejected("GMAIL_PILOT_BUDGET_EXHAUSTED")
    if type(form) is not tuple or any(type(item) is not tuple or len(item) != 2 for item in form):
        raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
    keys = tuple(key for key, _ in form)
    forbidden = "client_" "secret"
    untyped = any(type(key) is not str or type(value) is not str for key, value in form)
    if forbidden in keys or untyped:
        raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
    if keys not in {
        ("grant_type", "code", "code_verifier", "client_id", "redirect_uri"),
        ("grant_type", "refresh_token", "client_id"),
    }:
        raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
    grant = form[0]
    code_grant = ("grant_type", "authorization_code")
    refresh_grant = ("grant_type", "refresh_token")
    if grant != code_grant and grant != refresh_grant:
        raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
    active.token_attempts += 1
    encoded = "&".join(f"{_quote(key)}={_quote(value)}" for key, value in form).encode("ascii")
    try:
        status, raw = transport.exchange("POST", _TOKEN_URL, encoded)
    except PilotRejected:
        raise
    except TimeoutError:
        raise PilotRejected("GMAIL_PILOT_TOKEN_AMBIGUOUS") from None
    except Exception:
        raise PilotRejected("GMAIL_PILOT_TOKEN_AMBIGUOUS") from None
    if type(status) is not int or type(raw) is not bytes:
        raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
    if status in _REDIRECT_STATUSES:
        raise PilotRejected("GMAIL_PILOT_REDIRECT_REJECTED")
    if status in {401, 403}:
        raise PilotRejected("GMAIL_PILOT_DENIED")
    if status != 200:
        raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise PilotRejected("GMAIL_PILOT_MALFORMED") from None
    if type(parsed) is not dict:
        raise PilotRejected("GMAIL_PILOT_MALFORMED")
    try:
        require_exact_granted_scope(parsed.get("scope"), READONLY_SCOPE)
    except LocalOAuthProbeRejected:
        raise PilotRejected("GMAIL_PILOT_SCOPE_REJECTED") from None
    access_token = parsed.get("access_token")
    refresh_token = parsed.get("refresh_token")
    if type(access_token) is not str or access_token == "":
        raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
    if refresh_token is not None and (type(refresh_token) is not str or refresh_token == ""):
        raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
    return TokenGrant(
        scope=READONLY_SCOPE,
        access_token=access_token,
        refresh_token=refresh_token if type(refresh_token) is str else None,
    )


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
