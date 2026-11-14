"""Injected-transport Gmail read-only acquisition.

The transport is supplied by the caller. This module does not open a socket,
read a credential, send mail, or submit an order. Message bytes are parsed
and then dropped. Evidence keeps hashes, dispositions, and identities.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo

from swingtrade.group4_email.contract import EMAIL_RETENTION_POLICY
from swingtrade.group4_email.local_oauth_probe import (
    AuthorizationRequest,
    LocalOAuthProbeRejected,
    build_refresh_request,
    build_scoped_authorization_request,
    build_token_request,
    pkce_s256_challenge,
    require_exact_granted_scope,
    validate_callback,
    validate_redirect_uri,
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
    """One injected exchange. The bearer stays out of the URL and the body."""

    def exchange(
        self,
        method: str,
        url: str,
        body: bytes = b"",
        bearer: str | None = None,
    ) -> tuple[int, bytes]:
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
    classification: str = "NON_ACTIONABLE"


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


_BUDGET_KEYS = frozenset(
    {"version", "zone", "day", "recorded_at", "token_attempts", "read_gets"}
)
_NY = ZoneInfo("America/New_York")
_BUDGET_ZONE = "America/New_York"


class _IssuedGrant:
    """Private proof that a grant passed the token-response checks."""


_ISSUED = _IssuedGrant()


class BudgetStore(Protocol):
    """Persistent counts. A new client reads the same record."""

    def read(self) -> str | None:
        """Return the current record, or None when no record exists."""

    def update(self, mutate: Callable[[str | None], str]) -> None:
        """Replace the record only when ``mutate`` returns normally."""


class MemoryBudgetStore:
    """In-process record. Restart is a new budget object on this same store."""

    def __init__(self) -> None:
        self._payload: str | None = None
        self._lock = threading.Lock()

    def read(self) -> str | None:
        with self._lock:
            return self._payload

    def update(self, mutate: Callable[[str | None], str]) -> None:
        with self._lock:
            self._payload = _budget_text(mutate(self._payload))


class FileBudgetStore:
    """Local record. Two callers share the file through an exclusive lock."""

    def __init__(self, path: Path) -> None:
        if not isinstance(path, Path) or not path.is_absolute():
            raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
        self._path = path
        self._lock_path = path.with_name(path.name + ".lock")

    def read(self) -> str | None:
        descriptor = self._acquire()
        try:
            return self._read()
        finally:
            self._release(descriptor)

    def update(self, mutate: Callable[[str | None], str]) -> None:
        descriptor = self._acquire()
        try:
            self._write(_budget_text(mutate(self._read())))
        finally:
            self._release(descriptor)

    def _read(self) -> str | None:
        if not self._path.exists():
            return None
        return self._path.read_text(encoding="utf-8")

    def _write(self, payload: str) -> None:
        temporary = self._path.with_name(self._path.name + ".tmp")
        temporary.write_text(payload, encoding="utf-8", newline="\n")
        os.replace(temporary, self._path)

    def _acquire(self) -> int:
        for _attempt in range(50):
            try:
                return os.open(self._lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except FileExistsError:
                time.sleep(0.01)
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")

    def _release(self, descriptor: int) -> None:
        os.close(descriptor)
        try:
            os.remove(self._lock_path)
        except OSError:
            return


class DailyBudget:
    """New York calendar-day counts loaded from a store before every attempt."""

    def __init__(self, store: BudgetStore, now: Callable[[], int]) -> None:
        if not callable(now):
            raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
        self._store = store
        self._now = now

    def __repr__(self) -> str:
        return "DailyBudget"

    def consume_token(self) -> None:
        self._consume("token_attempts", _MAX_TOKEN_ATTEMPTS)

    def consume_get(self) -> None:
        self._consume("read_gets", _MAX_READ_GETS)

    def _consume(self, field: str, limit: int) -> None:
        moment = self._now()

        def mutate(current: str | None) -> str:
            state = _budget_for_moment(current, moment)
            count = state[field]
            if type(count) is not int or count >= limit:
                raise PilotRejected("GMAIL_PILOT_BUDGET_EXHAUSTED")
            state[field] = count + 1
            state["recorded_at"] = moment
            state["day"] = _ny_day(moment)
            return _dump_budget(state)

        self._store.update(mutate)


@dataclass
class TokenGrant:
    """Validated grant. Ordinary repr omits both token values and the proof."""

    scope: str
    access_token: str = field(repr=False)
    refresh_token: str | None = field(default=None, repr=False)
    proof: object = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.proof is not _ISSUED:
            raise PilotRejected("GMAIL_PILOT_GRANT_UNVERIFIED")
        if self.scope != READONLY_SCOPE:
            raise PilotRejected("GMAIL_PILOT_SCOPE_REJECTED")
        if not _printable_secret(self.access_token, 2048):
            raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
        if self.refresh_token is not None and not _printable_secret(self.refresh_token, 512):
            raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")


def acquire_readonly_messages(
    transport: PilotTransport,
    selectors: tuple[str, ...],
    *,
    grant: TokenGrant | None = None,
    budget: DailyBudget | None = None,
    expected_mailbox: str | None = None,
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
    if type(grant) is not TokenGrant or type(budget) is not DailyBudget:
        raise PilotRejected(
            "GMAIL_PILOT_SCOPE_REJECTED"
            if type(grant) is not TokenGrant
            else "GMAIL_PILOT_BUDGET_UNAVAILABLE"
        )
    assert isinstance(grant, TokenGrant)
    assert isinstance(budget, DailyBudget)
    if type(expected_mailbox) is not str or expected_mailbox == "":
        raise PilotRejected("GMAIL_PILOT_MAILBOX_REJECTED")
    active_registry = MessageIdentityRegistry() if registry is None else registry
    seen = set() if seen_provider_ids is None else seen_provider_ids
    seen_rfc: dict[str, str] = {}
    session = _Session(transport, budget, grant.access_token)
    profile = session.get_object(_PROFILE)
    mailbox = profile.get("emailAddress")
    if type(mailbox) is not str or mailbox == "":
        raise PilotRejected("GMAIL_PILOT_MALFORMED")
    if mailbox != expected_mailbox:
        raise PilotRejected("GMAIL_PILOT_MAILBOX_REJECTED")
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
    def __init__(self, transport: PilotTransport, budget: DailyBudget, bearer: str) -> None:
        self._transport = transport
        self._budget = budget
        self._bearer = bearer
        self.request_count = 0

    def __repr__(self) -> str:
        return "_Session"

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
        self._budget.consume_get()
        if self.request_count >= _MAX_READ_GETS:
            raise PilotRejected("GMAIL_PILOT_BUDGET_EXHAUSTED")
        self.request_count += 1

    def _call(self, method: str, url: str, body: bytes, timeout_code: str) -> tuple[int, bytes]:
        try:
            if method == "POST":
                status, raw = self._transport.exchange(method, url, body)
            else:
                status, raw = self._transport.exchange(method, url, bearer=self._bearer)
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


def _classification(disposition: str, kind: str) -> str:
    if kind != "FIXTURE":
        return "NON_ACTIONABLE"
    if disposition == "ACCEPT":
        return "ACCEPT"
    if disposition == "REJECT":
        return "REJECT"
    return "QUARANTINE"


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
        classification=_classification(disposition, kind),
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
        classification="QUARANTINE",
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
    budget: DailyBudget | None = None,
) -> TokenGrant:
    """Exchange or refresh one readonly grant. Ambiguous failures are not retried."""

    if type(budget) is not DailyBudget:
        raise PilotRejected("GMAIL_PILOT_BUDGET_UNAVAILABLE")
    assert isinstance(budget, DailyBudget)
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
    budget.consume_token()
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
    if type(access_token) is not str or not _printable_secret(access_token, 2048):
        raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
    if refresh_token is None:
        issued_refresh: str | None = None
    elif type(refresh_token) is str and _printable_secret(refresh_token, 512):
        issued_refresh = refresh_token
    else:
        raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
    return TokenGrant(
        scope=READONLY_SCOPE,
        access_token=access_token,
        refresh_token=issued_refresh,
        proof=_ISSUED,
    )


def run_readonly_connection(
    transport: PilotTransport,
    *,
    capability: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    code_verifier: str,
    selectors: tuple[str, ...],
    budget: DailyBudget | None,
    expected_mailbox: str,
    callback: tuple[tuple[str, str], ...] | None = None,
    refresh_token: str | None = None,
    limit: int = MAX_LIST_RESULTS,
    registry: MessageIdentityRegistry | None = None,
    seen_provider_ids: set[str] | None = None,
) -> PilotEvidence:
    """Connect one explicit readonly selection to injected Gmail reads.

    The capability string selects the authorization request. Message reads
    accept only the grant returned by the token endpoint.
    """

    if capability != "readonly":
        raise PilotRejected("GMAIL_PILOT_SCOPE_REJECTED")
    if type(budget) is not DailyBudget:
        raise PilotRejected("GMAIL_PILOT_BUDGET_UNAVAILABLE")
    assert isinstance(budget, DailyBudget)
    if type(client_id) is not str or client_id == "" or type(state) is not str or state == "":
        raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
    _require_loopback(redirect_uri)
    challenge = pkce_s256_challenge(code_verifier)
    authorization = build_scoped_authorization_request(
        capability="readonly",
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state,
        code_challenge=challenge,
    )
    _require_readonly_authorization(
        authorization,
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state,
        challenge=challenge,
    )
    if (callback is None) == (refresh_token is None):
        raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
    if refresh_token is not None:
        token_request = build_refresh_request(refresh_token=refresh_token, client_id=client_id)
    elif callback is not None:
        code = validate_callback(callback, state)
        token_request = build_token_request(
            code=code,
            code_verifier=code_verifier,
            client_id=client_id,
            redirect_uri=redirect_uri,
        )
    else:
        raise PilotRejected("GMAIL_PILOT_TOKEN_REJECTED")
    if token_request.endpoint != _TOKEN_URL:
        raise PilotRejected("GMAIL_PILOT_ENDPOINT_REJECTED")
    issued = exchange_readonly_grant(transport, token_request.form, budget=budget)
    return acquire_readonly_messages(
        transport,
        selectors,
        grant=issued,
        budget=budget,
        expected_mailbox=expected_mailbox,
        limit=limit,
        registry=registry,
        seen_provider_ids=seen_provider_ids,
    )


def seed_daily_budget(
    store: BudgetStore,
    now: int,
    *,
    token_attempts: int = 0,
    read_gets: int = 0,
) -> None:
    """Create the first daily record. An existing record is not replaced."""

    if type(now) is not int or type(token_attempts) is not int or type(read_gets) is not int:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    payload = _dump_budget(
        {
            "version": 1,
            "zone": _BUDGET_ZONE,
            "day": _ny_day(now),
            "recorded_at": now,
            "token_attempts": token_attempts,
            "read_gets": read_gets,
        }
    )
    _parse_budget(payload)

    def mutate(current: str | None) -> str:
        if current is not None:
            raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
        return payload

    store.update(mutate)


def _printable_secret(value: object, limit: int) -> bool:
    if type(value) is not str or value == "" or len(value) > limit:
        return False
    return all(33 <= ord(char) <= 126 for char in value)


def _budget_text(payload: object) -> str:
    if type(payload) is not str or payload == "" or "\x00" in payload or len(payload) > 512:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    _parse_budget(payload)
    return payload


def _budget_for_moment(current: str | None, now: object) -> dict[str, object]:
    if current is None:
        raise PilotRejected("GMAIL_PILOT_BUDGET_MISSING")
    if type(now) is not int:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    state = _parse_budget(current)
    recorded = state["recorded_at"]
    if type(recorded) is not int or now < recorded:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    if _ny_day(now) != state["day"]:
        state["token_attempts"] = 0
        state["read_gets"] = 0
    return state


def _parse_budget(current: str) -> dict[str, object]:
    try:
        parsed = json.loads(current)
    except json.JSONDecodeError:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID") from None
    if type(parsed) is not dict or set(parsed) != _BUDGET_KEYS:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    version = parsed.get("version")
    zone = parsed.get("zone")
    day = parsed.get("day")
    recorded = parsed.get("recorded_at")
    tokens = parsed.get("token_attempts")
    gets = parsed.get("read_gets")
    counts_ok = (
        type(tokens) is int
        and type(gets) is int
        and 0 <= tokens <= _MAX_TOKEN_ATTEMPTS
        and 0 <= gets <= _MAX_READ_GETS
    )
    identity_ok = (
        type(version) is int
        and version == 1
        and zone == _BUDGET_ZONE
        and type(day) is str
        and type(recorded) is int
        and counts_ok
    )
    if not identity_ok or type(recorded) is not int or _ny_day(recorded) != day:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    return {
        "version": version,
        "zone": zone,
        "day": day,
        "recorded_at": recorded,
        "token_attempts": tokens,
        "read_gets": gets,
    }


def _dump_budget(state: Mapping[str, object]) -> str:
    if set(state) != _BUDGET_KEYS:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    return json.dumps({key: state[key] for key in sorted(_BUDGET_KEYS)}, separators=(",", ":"))


def _ny_day(epoch: int) -> str:
    if epoch < 0 or epoch > 4_102_444_800:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    try:
        zoned = datetime.fromtimestamp(epoch, tz=_NY)
    except (OverflowError, OSError, ValueError):
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID") from None
    return zoned.date().isoformat()


def _require_loopback(uri: object) -> None:
    if type(uri) is not str or not uri.startswith("http://127.0.0.1:"):
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED")
    port_text, slash, tail = uri.removeprefix("http://127.0.0.1:").partition("/")
    if slash != "/" or tail != "" or not port_text.isdigit() or port_text.startswith("0"):
        raise LocalOAuthProbeRejected("GMAIL_OAUTH_REDIRECT_REJECTED")
    validate_redirect_uri(uri, int(port_text))


def _require_readonly_authorization(
    request: AuthorizationRequest,
    *,
    client_id: str,
    redirect_uri: str,
    state: str,
    challenge: str,
) -> None:
    if request.endpoint != "https://accounts.google.com/o/oauth2/v2/auth":
        raise PilotRejected("GMAIL_PILOT_ENDPOINT_REJECTED")
    expected = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": READONLY_SCOPE,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    if dict(request.parameters) != expected:
        raise PilotRejected("GMAIL_PILOT_SCOPE_REJECTED")


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


READONLY_CAMPAIGN = "GMAIL-READONLY-SIGNAL-DISCOVERY-20261114-R1"
_GRANT_KEYS = frozenset(
    {
        "budget_id",
        "campaign",
        "capability",
        "custody_target",
        "endpoints",
        "expires_at",
        "mailbox_hash",
        "methods",
        "not_before",
        "revoked",
        "runtime",
    }
)
_GRANT_ENDPOINTS = [
    "https://oauth2.googleapis.com/token",
    "https://gmail.googleapis.com/gmail/v1/users/me/",
]
_GRANT_METHODS = ["GET", "POST"]
_PROTECTED_KEYS = frozenset(
    {"budget_id", "day", "read_gets", "recorded_at", "token_attempts", "version", "zone"}
)
_MAX_RESPONSE_BYTES = 65536


class _Authorized:
    """Private proof that a grant passed the local authenticator."""


_AUTHORIZED = _Authorized()


def standing_network_allowed(grant: object) -> bool:
    """Caller flags cannot enable a provider call. The standing grant is inactive."""

    if type(grant) is dict and (grant.get("effective") is True or grant.get("attended") is True):
        return False
    return False


@dataclass(frozen=True)
class OperatorGrant:
    """Locally checked readonly grant. It does not enable the network by itself."""

    capability: str
    campaign: str
    mailbox_hash: str = field(repr=False)
    expires_at: int
    proof: object = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.proof is not _AUTHORIZED:
            raise PilotRejected("GMAIL_PILOT_GRANT_UNVERIFIED")
        if self.capability != "readonly" or self.campaign != READONLY_CAMPAIGN:
            raise PilotRejected("GMAIL_PILOT_GRANT_REJECTED")


@dataclass(frozen=True)
class AcquisitionAudit:
    """Sanitized handoff record. It has no body, token, or mailbox address."""

    campaign: str
    provider_message_id: str
    content_digest: str
    classification: str
    reasons: tuple[str, ...]
    receipt_key: str | None
    replay_kind: str | None
    correlation_id: str
    source_timestamp: str | None

    def __post_init__(self) -> None:
        if self.campaign != READONLY_CAMPAIGN or self.classification not in {
            "ACCEPT",
            "REJECT",
            "QUARANTINE",
            "NON_ACTIONABLE",
        }:
            raise PilotRejected("GMAIL_PILOT_MALFORMED")
        if len(self.correlation_id) != 64 or any(
            character not in "0123456789abcdef" for character in self.correlation_id
        ):
            raise PilotRejected("GMAIL_PILOT_MALFORMED")


def mailbox_hash(mailbox: str) -> str:
    if type(mailbox) is not str or mailbox == "" or any(ord(char) < 33 for char in mailbox):
        raise PilotRejected("GMAIL_PILOT_MAILBOX_REJECTED")
    return hashlib.sha256(mailbox.encode("utf-8")).hexdigest()


def grant_mac(document: Mapping[str, object], key: bytes) -> str:
    return hmac.new(key, _grant_bytes(document), hashlib.sha256).hexdigest()


def validate_operator_grant(
    document: object,
    mac: object,
    key: object,
    now: object,
) -> OperatorGrant:
    """Accept one canonical grant. A caller flag is not a signature."""

    if type(key) is not bytes or len(key) < 32 or type(mac) is not str or type(now) is not int:
        raise PilotRejected("GMAIL_PILOT_GRANT_REJECTED")
    payload = _grant_bytes(document)
    expected = hmac.new(key, payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, mac):
        raise PilotRejected("GMAIL_PILOT_GRANT_REJECTED")
    if type(document) is not dict:
        raise PilotRejected("GMAIL_PILOT_GRANT_REJECTED")
    _require_grant_fields(document, now)
    return OperatorGrant(
        capability="readonly",
        campaign=READONLY_CAMPAIGN,
        mailbox_hash=str(document["mailbox_hash"]),
        expires_at=int(document["expires_at"]),
        proof=_AUTHORIZED,
    )


def assess_readonly_runtime(
    document: object,
    mac: object,
    *,
    key: object,
    now: object,
) -> str:
    """Report the runtime gate. A valid grant still does not open the network."""

    if standing_network_allowed(document) is not False or key is None:
        return "GMAIL_OAUTH_LIVE_UNAUTHORIZED"
    try:
        validate_operator_grant(document, mac, key, now)
    except PilotRejected as rejected:
        return rejected.code
    return "GMAIL_OAUTH_LIVE_UNAUTHORIZED"


def establish_protected_budget(store: BudgetStore, now: int, key: bytes) -> None:
    """Write the first sealed record. An existing or deleted-and-reused store is refused."""

    if type(now) is not int or type(key) is not bytes or len(key) < 32:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    payload = _seal_budget(_protected_state(now, 0, 0), key)

    def mutate(current: str | None) -> str:
        if current is not None:
            raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
        return payload

    store.update(mutate)


class SealedMemoryStore:
    """Process-local sealed record. It does not interpret or reset counts."""

    def __init__(self) -> None:
        self._payload: str | None = None
        self._lock = threading.Lock()

    def read(self) -> str | None:
        with self._lock:
            return self._payload

    def update(self, mutate: Callable[[str | None], str]) -> None:
        with self._lock:
            replacement = mutate(self._payload)
            self._payload = _sealed_text(replacement)


class SealedFileStore:
    """Cross-process sealed record. The caller does not choose the file name."""

    def __init__(self, directory: Path) -> None:
        self._path = protected_budget_file(directory)
        self._lock_path = self._path.with_name(self._path.name + ".lock")

    def read(self) -> str | None:
        descriptor = self._acquire()
        try:
            if not self._path.exists():
                return None
            return self._path.read_text(encoding="utf-8")
        finally:
            self._release(descriptor)

    def update(self, mutate: Callable[[str | None], str]) -> None:
        descriptor = self._acquire()
        try:
            current = self._path.read_text(encoding="utf-8") if self._path.exists() else None
            payload = _sealed_text(mutate(current))
            temporary = self._path.with_name(self._path.name + ".tmp")
            temporary.write_text(payload, encoding="utf-8", newline="\n")
            os.replace(temporary, self._path)
        finally:
            self._release(descriptor)

    def _acquire(self) -> int:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        for _attempt in range(50):
            try:
                return os.open(self._lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except FileExistsError:
                time.sleep(0.01)
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")

    def _release(self, descriptor: int) -> None:
        os.close(descriptor)
        try:
            os.remove(self._lock_path)
        except OSError:
            return


def _sealed_text(payload: object) -> str:
    if type(payload) is not str or payload == "" or "\x00" in payload or len(payload) > 1024:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    return payload


class ProtectedBudget:
    """Sealed New York counts. A clock change cannot restore allowance."""

    def __init__(self, store: BudgetStore, now: Callable[[], int], key: bytes) -> None:
        if type(key) is not bytes or len(key) < 32 or not callable(now):
            raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
        self._store = store
        self._now = now
        self._key = key

    def __repr__(self) -> str:
        return "ProtectedBudget"

    def consume_token(self) -> None:
        self._consume("token_attempts", _MAX_TOKEN_ATTEMPTS)

    def consume_get(self) -> None:
        self._consume("read_gets", _MAX_READ_GETS)

    def _consume(self, field: str, limit: int) -> None:
        moment = self._now()
        key = self._key

        def mutate(current: str | None) -> str:
            if current is None:
                raise PilotRejected("GMAIL_PILOT_BUDGET_MISSING")
            state = _open_budget(current, key, moment)
            count = state[field]
            if type(count) is not int or count >= limit:
                raise PilotRejected("GMAIL_PILOT_BUDGET_EXHAUSTED")
            state[field] = count + 1
            state["recorded_at"] = moment
            return _seal_budget(state, key)

        self._store.update(mutate)


def protected_budget_file(directory: Path) -> Path:
    """Return the one filename used inside an approved directory."""

    if not isinstance(directory, Path) or not directory.is_absolute():
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    if directory.name != READONLY_CAMPAIGN:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    return directory / "budget.json"


def readonly_opener() -> object:
    """Build an opener that ignores environment proxies and verifies TLS."""

    import ssl
    from http.client import HTTPResponse
    from urllib.request import (
        HTTPHandler,
        HTTPRedirectHandler,
        HTTPSHandler,
        ProxyHandler,
        Request,
        build_opener,
    )

    context = ssl.create_default_context()
    if context.check_hostname is not True or context.verify_mode != ssl.CERT_REQUIRED:
        raise PilotRejected("GMAIL_PILOT_TRANSPORT_REJECTED")

    class _NoEnvironmentProxy(ProxyHandler):
        def __init__(self) -> None:
            super().__init__(proxies={})

    class _RefusePlain(HTTPHandler):
        def http_open(self, req: Request) -> HTTPResponse:
            raise PilotRejected("GMAIL_PILOT_ENDPOINT_REJECTED")

    class _RefuseRedirect(HTTPRedirectHandler):
        def redirect_request(
            self,
            req: object,
            fp: object,
            code: int,
            msg: str,
            headers: object,
            newurl: str,
        ) -> None:
            raise PilotRejected("GMAIL_PILOT_REDIRECT_REJECTED")

    class _PinnedHttps(HTTPSHandler):
        def https_open(self, req: Request) -> HTTPResponse:
            full_url = req.full_url
            allowed = (
                "https://gmail.googleapis.com/",
                "https://oauth2.googleapis.com/",
                "https://accounts.google.com/",
            )
            if not full_url.startswith(allowed):
                raise PilotRejected("GMAIL_PILOT_ENDPOINT_REJECTED")
            return super().https_open(req)

    return build_opener(
        _NoEnvironmentProxy(),
        _RefusePlain(),
        _RefuseRedirect(),
        _PinnedHttps(context=context),
    )


def bounded_body(raw: object) -> bytes:
    if type(raw) is not bytes or len(raw) > _MAX_RESPONSE_BYTES:
        raise PilotRejected("GMAIL_PILOT_MALFORMED")
    return raw


def retry_class(status: object) -> str:
    if type(status) is not int:
        return "NO_RETRY"
    if status in _RETRY_STATUSES:
        return "RETRYABLE_GET"
    if status in {401, 403}:
        return "DENIED"
    if status in _REDIRECT_STATUSES:
        return "REDIRECT_REJECTED"
    return "NO_RETRY"


def handoff_mime(raw: bytes, provider_id: str, store: object) -> AcquisitionAudit:
    """Project one parsed message. Non-fixture mail is not admitted."""

    from swingtrade.instruction_receipt import InMemoryReceiptStore, admit_instruction_receipt

    if type(raw) is not bytes or type(provider_id) is not str or provider_id == "":
        raise PilotRejected("GMAIL_PILOT_MALFORMED")
    if type(store) is not InMemoryReceiptStore:
        raise PilotRejected("GMAIL_PILOT_TRANSPORT_REJECTED")
    outcome = parse_email(raw, MessageIdentityRegistry())
    kind, _rfc = message_id_classification(raw)
    classification = _classification(outcome.disposition.value, kind)
    receipt_key = None
    replay_kind = None
    if classification == "ACCEPT":
        decision = admit_instruction_receipt(outcome, store)
        receipt_key = decision.receipt.receipt_key
        replay_kind = decision.kind.value
    digest = outcome.content_digest
    return AcquisitionAudit(
        campaign=READONLY_CAMPAIGN,
        provider_message_id=provider_id,
        content_digest=digest,
        classification=classification,
        reasons=tuple(outcome.reasons),
        receipt_key=receipt_key,
        replay_kind=replay_kind,
        correlation_id=_correlation(provider_id, digest),
        source_timestamp=outcome.provenance.source_timestamp,
    )


def exercise_mock_custody(secret: object, port: object) -> str:
    """Store and retrieve one synthetic secret. Native reads stay closed."""

    from swingtrade.gmail_credential.adapter import GmailCredentialAdapter
    from swingtrade.gmail_credential.identity import NATIVE_BACKEND_ENABLED
    from swingtrade.gmail_credential.mock_port import MockCredentialPort
    from swingtrade.gmail_credential.secret import SyntheticSecret

    if NATIVE_BACKEND_ENABLED is not False or standing_network_allowed(None) is not False:
        raise PilotRejected("GMAIL_OAUTH_LIVE_UNAUTHORIZED")
    if type(secret) is not SyntheticSecret or type(port) is not MockCredentialPort:
        raise PilotRejected("GMAIL_PILOT_CUSTODY_REJECTED")
    adapter = GmailCredentialAdapter(port)
    adapter.store(secret)
    view = adapter.retrieve()
    if not view.matches(secret) or port.live_allocation_count() != 0:
        raise PilotRejected("GMAIL_PILOT_CUSTODY_REJECTED")
    return "CUSTODY_SHAPE_PASS"


def native_credential_read() -> None:
    """The native credential backend is not enabled."""

    from swingtrade.gmail_credential.identity import NATIVE_BACKEND_ENABLED

    if NATIVE_BACKEND_ENABLED is not False or standing_network_allowed(None) is not False:
        raise PilotRejected("GMAIL_OAUTH_LIVE_UNAUTHORIZED")
    raise PilotRejected("GMAIL_OAUTH_LIVE_UNAUTHORIZED")


def _grant_bytes(document: object) -> bytes:
    if type(document) is not dict or set(document) != _GRANT_KEYS:
        raise PilotRejected("GMAIL_PILOT_GRANT_REJECTED")
    ordered = {key: document[key] for key in sorted(_GRANT_KEYS)}
    return json.dumps(ordered, separators=(",", ":")).encode("utf-8")


def _require_grant_fields(document: dict[str, object], now: int) -> None:
    from swingtrade.gmail_credential.identity import CANONICAL_TARGET

    if (
        document.get("capability") != "readonly"
        or document.get("campaign") != READONLY_CAMPAIGN
        or document.get("budget_id") != READONLY_CAMPAIGN
        or document.get("runtime") != "win32"
        or document.get("revoked") is not False
        or document.get("custody_target") != CANONICAL_TARGET
        or document.get("endpoints") != _GRANT_ENDPOINTS
        or document.get("methods") != _GRANT_METHODS
    ):
        raise PilotRejected("GMAIL_PILOT_GRANT_REJECTED")
    digest = document.get("mailbox_hash")
    starts = document.get("not_before")
    ends = document.get("expires_at")
    if (
        type(digest) is not str
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or type(starts) is not int
        or type(ends) is not int
        or starts > now
        or now >= ends
    ):
        raise PilotRejected("GMAIL_PILOT_GRANT_REJECTED")


def _protected_state(now: int, tokens: int, gets: int) -> dict[str, object]:
    return {
        "version": 1,
        "zone": _BUDGET_ZONE,
        "day": _ny_day(now),
        "recorded_at": now,
        "token_attempts": tokens,
        "read_gets": gets,
        "budget_id": READONLY_CAMPAIGN,
    }


def _seal_budget(state: Mapping[str, object], key: bytes) -> str:
    if set(state) != _PROTECTED_KEYS:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    ordered = {name: state[name] for name in sorted(_PROTECTED_KEYS)}
    raw = json.dumps(ordered, separators=(",", ":")).encode("utf-8")
    sealed = dict(ordered)
    sealed["seal"] = hmac.new(key, raw, hashlib.sha256).hexdigest()
    return json.dumps(sealed, separators=(",", ":"), sort_keys=True)


def _open_budget(current: str, key: bytes, now: object) -> dict[str, object]:
    try:
        parsed = json.loads(current)
    except json.JSONDecodeError:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID") from None
    if type(parsed) is not dict or set(parsed) != _PROTECTED_KEYS | {"seal"}:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    seal = parsed.get("seal")
    body = {name: parsed[name] for name in sorted(_PROTECTED_KEYS)}
    raw = json.dumps(body, separators=(",", ":")).encode("utf-8")
    expected = hmac.new(key, raw, hashlib.sha256).hexdigest()
    if type(seal) is not str or not hmac.compare_digest(expected, seal):
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    if type(now) is not int:
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    recorded = body["recorded_at"]
    day = body["day"]
    tokens = body["token_attempts"]
    gets = body["read_gets"]
    if (
        body.get("budget_id") != READONLY_CAMPAIGN
        or body.get("zone") != _BUDGET_ZONE
        or body.get("version") != 1
        or type(recorded) is not int
        or type(day) is not str
        or type(tokens) is not int
        or type(gets) is not int
        or now < recorded
        or _ny_day(now) != day
        or _ny_day(recorded) != day
        or tokens < 0
        or gets < 0
        or tokens > _MAX_TOKEN_ATTEMPTS
        or gets > _MAX_READ_GETS
    ):
        raise PilotRejected("GMAIL_PILOT_BUDGET_INVALID")
    return body


def _correlation(provider_id: str, digest: str) -> str:
    material = f"{READONLY_CAMPAIGN}:{provider_id}:{digest}".encode()
    return hashlib.sha256(material).hexdigest()
