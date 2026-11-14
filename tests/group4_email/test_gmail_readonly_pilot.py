"""Mocked read-only Gmail acquisition. No provider call is made."""

from __future__ import annotations

import base64
import hashlib
import json
import threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from swingtrade.group4_email.gmail_readonly_pilot import (
    READONLY_SCOPE,
    DailyBudget,
    FileBudgetStore,
    MemoryBudgetStore,
    PilotRejected,
    TokenGrant,
    _require_readonly_url,
    acquire_readonly_messages,
    exchange_readonly_grant,
    run_readonly_connection,
    seed_daily_budget,
)
from swingtrade.group4_email.local_oauth_probe import (
    LocalOAuthProbeRejected,
    build_refresh_request,
    build_token_request,
)
from swingtrade.group4_email.parse import MessageIdentityRegistry
from tests.group4_email.conftest import body, plain_message

MODULE = Path("src/swingtrade/group4_email/gmail_readonly_pilot.py")
SELECTORS = ("from:signals@example.invalid", "label:synthetic")
API = "https://gmail.googleapis.com/gmail/v1/users/me"


class Scripted:
    def __init__(self, responses: list[tuple[int, bytes]]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str]] = []
        self.body = b""
        self.bodies: list[bytes] = []
        self.digests: list[str | None] = []

    def exchange(
        self,
        method: str,
        url: str,
        body: bytes = b"",
        bearer: str | None = None,
    ) -> tuple[int, bytes]:
        self.calls.append((method, url))
        self.body = body
        self.bodies.append(body)
        if bearer is None:
            self.digests.append(None)
        else:
            self.digests.append(hashlib.sha256(bearer.encode("utf-8")).hexdigest())
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)


class TimeoutAt(Scripted):
    def __init__(self, index: int, responses: list[tuple[int, bytes]]) -> None:
        super().__init__(responses)
        self.index = index
        self._seen = 0

    def exchange(
        self,
        method: str,
        url: str,
        body: bytes = b"",
        bearer: str | None = None,
    ) -> tuple[int, bytes]:
        current = self._seen
        self._seen += 1
        if current == self.index:
            self.calls.append((method, url))
            raise TimeoutError
        return super().exchange(method, url, body, bearer)


def _json(payload: object, status: int = 200) -> tuple[int, bytes]:
    return status, json.dumps(payload).encode("utf-8")


def _encoded(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _profile() -> tuple[int, bytes]:
    return _json(
        {
            "emailAddress": "signals@example.invalid",
            "messagesTotal": 1,
            "threadsTotal": 1,
            "historyId": "history-shape",
        }
    )


def _labels() -> tuple[int, bytes]:
    return _json({"labels": [{"id": "LABEL_1", "name": "synthetic"}]})


def _listed(*ids: str) -> tuple[int, bytes]:
    return _json({"messages": [{"id": item} for item in ids]})


def _rfc822(provider_id: str, raw: bytes) -> tuple[int, bytes]:
    return _json(
        {
            "id": provider_id,
            "payload": {"mimeType": "message/rfc822", "body": {"data": _encoded(raw)}},
        }
    )


def _ready(*messages: tuple[int, bytes]) -> list[tuple[int, bytes]]:
    return [_profile(), _labels(), *messages]


def test_mocked_success_keeps_provider_identity_distinct_from_instruction() -> None:
    raw = plain_message(body("tday_dated.txt"), "<pilot-success@example.invalid>")
    transport = Scripted(_ready(_listed("provider-success"), _rfc822("provider-success", raw)))

    evidence = _acquire(transport, SELECTORS, limit=1)
    repeated = _acquire(
        Scripted(_ready(_listed("provider-success"), _rfc822("provider-success", raw))),
        SELECTORS,
        limit=1,
    )

    assert evidence == repeated
    assert evidence.durable_state == "UNAVAILABLE"
    assert evidence.economic_dispatch is False
    assert evidence.scope == READONLY_SCOPE
    assert evidence.retention_policy == "HASH_PROVIDER_REF_FIELD_EVIDENCE"
    assert evidence.content_retained is False
    assert evidence.request_count == 4
    message = evidence.messages[0]
    assert message.disposition == "ACCEPT"
    assert message.provider_message_id == "provider-success"
    assert message.instruction_ids
    assert message.provider_message_id not in message.instruction_ids
    assert message.provider_message_ref == "<pilot-success@example.invalid>"
    assert message.instruction_ids[0] != message.provider_message_ref
    assert message.source_timestamp is None
    assert "emailAddress" not in repr(evidence)
    assert [method for method, _ in transport.calls] == ["GET", "GET", "GET", "GET"]
    assert transport.calls[2][1] == (
        API + "/messages?maxResults=1&q="
        "from%3Asignals%40example.invalid%20label%3Asynthetic"
    )
    assert transport.calls[3][1] == API + "/messages/provider-success?format=full"
    assert all("attachments" not in url and "format=raw" not in url for _, url in transport.calls)


def test_empty_mailbox_performs_no_message_read() -> None:
    transport = Scripted(_ready(_json({"resultSizeEstimate": 0})))

    evidence = _acquire(transport, ("label:synthetic",))

    assert evidence.messages == ()
    assert evidence.request_count == 3
    assert len(transport.calls) == 3


def test_malformed_mime_is_rejected_by_the_existing_parser() -> None:
    malformed = (
        b"Message-ID: <bad-pilot@example.invalid>\r\n"
        b"MIME-Version: 1.0\r\n"
        b'Content-Type: multipart/mixed; boundary="abc"\r\n'
        b"\r\n--abc\r\nContent-Type: text/plain\r\n\r\nhello\r\n"
    )
    transport = Scripted(_ready(_listed("provider-bad"), _rfc822("provider-bad", malformed)))

    evidence = _acquire(transport, ("label:synthetic",), limit=1)

    assert evidence.messages[0].disposition == "REJECT"
    assert evidence.messages[0].reasons == ("MALFORMED_MIME",)
    assert evidence.messages[0].instruction_ids == ()


def test_bad_timestamp_and_non_trading_text_do_not_become_instructions() -> None:
    incomplete = plain_message(
        "Entry: Buy stop $7.23.\n",
        "<pilot-note@example.invalid>",
    ).replace(b"Subject: fixture", b"Date: not-a-timestamp\r\nSubject: fixture")
    note = plain_message("Hello from the fixture list.\n", "<pilot-hello@example.invalid>")
    incomplete_transport = Scripted(
        _ready(_listed("provider-note"), _rfc822("provider-note", incomplete))
    )
    note_transport = Scripted(_ready(_listed("provider-hello"), _rfc822("provider-hello", note)))

    incomplete_evidence = _acquire(
        incomplete_transport, ("label:synthetic",), limit=1
    )
    note_evidence = _acquire(note_transport, ("label:synthetic",), limit=1)
    message = incomplete_evidence.messages[0]

    assert message.disposition == "QUARANTINE"
    assert message.instruction_ids == ()
    assert message.source_timestamp is None
    assert "INCOMPLETE_TRADE" in message.reasons
    assert note_evidence.messages[0].disposition == "ACCEPT"
    assert note_evidence.messages[0].instruction_ids == ()


def test_partial_message_is_quarantined_and_the_complete_message_is_kept() -> None:
    raw = plain_message("Entry: Buy stop $7.23.\n", "<pilot-partial@example.invalid>")
    transport = Scripted(
        _ready(
            _listed("provider-whole", "provider-missing"),
            _rfc822("provider-whole", raw),
            (404, b""),
        )
    )

    evidence = _acquire(transport, ("label:synthetic",), limit=2)

    assert [item.provider_message_id for item in evidence.messages] == [
        "provider-whole",
        "provider-missing",
    ]
    assert "INCOMPLETE_TRADE" in evidence.messages[0].reasons
    assert evidence.messages[1].reasons == ("GMAIL_PILOT_PARTIAL",)
    assert evidence.messages[1].instruction_ids == ()


def test_timeout_and_provider_denial_fail_closed() -> None:
    timeout = TimeoutAt(2, _ready(_listed("provider-late")))
    denied = Scripted([(403, b"{}")])

    with pytest.raises(PilotRejected) as timed:
        _acquire(timeout, ("label:synthetic",))
    with pytest.raises(PilotRejected) as blocked:
        _acquire(denied, ("label:synthetic",))

    assert timed.value.code == "GMAIL_PILOT_TIMEOUT"
    assert blocked.value.code == "GMAIL_PILOT_DENIED"
    assert len(denied.calls) == 1


def test_duplicate_provider_id_is_not_fetched_twice_and_replay_is_stable() -> None:
    raw = plain_message(body("tday_dated.txt"), "<pilot-replay@example.invalid>")
    seen: set[str] = set()
    registry = MessageIdentityRegistry()
    first = Scripted(
        _ready(_listed("provider-replay", "provider-replay"), _rfc822("provider-replay", raw))
    )
    second_raw = plain_message(body("tday_dated.txt"), "<pilot-replay@example.invalid>")
    second = Scripted(_ready(_listed("provider-other"), _rfc822("provider-other", second_raw)))

    original = _acquire(
        first,
        ("label:synthetic",),
        limit=2,
        registry=registry,
        seen_provider_ids=seen,
    )
    replay = _acquire(
        second,
        ("label:synthetic",),
        limit=1,
        registry=registry,
        seen_provider_ids=seen,
    )

    assert original.messages[1].duplicate is True
    assert original.messages[1].reasons == ("DUPLICATE_PROVIDER_MESSAGE",)
    assert [url for _, url in first.calls if "/messages/provider-replay?" in url]
    assert len([url for _, url in first.calls if "provider-replay?format=full" in url]) == 1
    assert replay.messages[0].disposition == "ACCEPT"
    assert replay.messages[0].instruction_ids == original.messages[0].instruction_ids
    assert "provider-other" in seen


def test_malformed_list_selector_and_limit_are_rejected() -> None:
    malformed = Scripted(_ready((200, b"[]")))
    with pytest.raises(PilotRejected) as listed:
        _acquire(malformed, ("label:synthetic",))
    with pytest.raises(PilotRejected) as selected:
        _acquire(Scripted([]), ("subject:trade",))
    with pytest.raises(PilotRejected) as limited:
        _acquire(Scripted([]), ("label:synthetic",), limit=11)

    assert listed.value.code == "GMAIL_PILOT_MALFORMED"
    assert selected.value.code == "GMAIL_PILOT_SELECTOR_REJECTED"
    assert limited.value.code == "GMAIL_PILOT_LIMIT_REJECTED"
    assert selected.value.code != "" and Scripted([]).calls == []


def test_attachment_part_is_not_fetched() -> None:
    payload = {
        "id": "provider-file",
        "payload": {
            "mimeType": "multipart/mixed",
            "headers": [
                {"name": "Message-ID", "value": "<pilot-file@example.invalid>"},
                {"name": "From", "value": "signals@example.invalid"},
                {"name": "To", "value": "signals@example.invalid"},
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": _encoded(b"Entry: Buy stop $7.23.\n")},
                },
                {
                    "mimeType": "application/octet-stream",
                    "filename": "note.bin",
                    "body": {"attachmentId": "attachment-1", "size": 4},
                },
            ],
        },
    }
    transport = Scripted(_ready(_listed("provider-file"), _json(payload)))

    evidence = _acquire(transport, ("label:synthetic",), limit=1)

    assert evidence.ignored_attachment_count == 1
    assert evidence.messages[0].disposition == "QUARANTINE"
    assert all("attachments" not in url for _, url in transport.calls)


def test_pilot_source_has_no_live_or_economic_path() -> None:
    source = MODULE.read_text(encoding="utf-8")

    assert "deliver_synthetic_fixtures" not in source
    assert "record_synthetic_ingestion" not in source
    assert "OrderIntent" not in source
    assert "client_secret" not in source
    assert "import socket" not in source
    assert "urlopen" not in source
    assert READONLY_SCOPE in source
    assert "gmail.metadata" not in source


def _token_form() -> tuple[tuple[str, str], ...]:
    request = build_token_request(
        code="synthetic-code",
        code_verifier="a" * 43,
        client_id="synthetic-client",
        redirect_uri="http://127.0.0.1:43123/",
    )
    return request.form


def _grant_body(scope: str = READONLY_SCOPE, refresh: bool = False) -> bytes:
    payload: dict[str, object] = {"access_token": "synthetic-access", "scope": scope}
    if refresh:
        payload["refresh_token"] = "synthetic-refresh"
    return json.dumps(payload).encode("utf-8")


NY = ZoneInfo("America/New_York")
FIXED = int(datetime(2026, 11, 14, 12, 0, tzinfo=NY).timestamp())
MAILBOX = "signals@example.invalid"
REDIRECT = "http://127.0.0.1:43123/"
VERIFIER = "a" * 43
STATE = "synthetic-state"


def _open_budget(
    now: int = FIXED,
    *,
    tokens: int = 0,
    gets: int = 0,
    clock: list[int] | None = None,
) -> tuple[DailyBudget, MemoryBudgetStore]:
    store = MemoryBudgetStore()
    seed_daily_budget(store, now, token_attempts=tokens, read_gets=gets)
    source = [now] if clock is None else clock
    return DailyBudget(store, lambda: source[0]), store


def _issued_grant() -> TokenGrant:
    budget, _store = _open_budget()
    return exchange_readonly_grant(Scripted([(200, _grant_body())]), _token_form(), budget=budget)


def _acquire(transport: Scripted, selectors: tuple[str, ...], **kwargs: object) -> object:
    if "grant" not in kwargs:
        kwargs["grant"] = _issued_grant()
    if "budget" not in kwargs:
        kwargs["budget"], _store = _open_budget()
    kwargs.setdefault("expected_mailbox", MAILBOX)
    return acquire_readonly_messages(transport, selectors, **kwargs)  # type: ignore[arg-type]


def _counts(store: MemoryBudgetStore) -> tuple[int, int]:
    raw = store.read()
    assert raw is not None
    payload = json.loads(raw)
    return payload["token_attempts"], payload["read_gets"]


def _callback(state: str = STATE, code: str = "synthetic-code") -> tuple[tuple[str, str], ...]:
    return (("code", code), ("state", state), ("iss", "https://accounts.google.com"))


def test_token_exchange_and_refresh_hide_tokens_and_reject_bad_results() -> None:
    budget, store = _open_budget()
    success = Scripted([(200, _grant_body(refresh=True))])
    grant = exchange_readonly_grant(success, _token_form(), budget=budget)
    refresh = build_refresh_request(refresh_token="synthetic-refresh", client_id="synthetic-client")
    refreshed = exchange_readonly_grant(
        Scripted([(200, _grant_body())]),
        refresh.form,
        budget=budget,
    )
    denied = Scripted([(401, b"{}")])
    rejected = Scripted([(500, b"{}"), (200, _grant_body())])
    timed = TimeoutAt(0, [(200, _grant_body())])
    redirected = Scripted([(302, b"")])
    metadata = Scripted([(200, _grant_body("https://www.googleapis.com/auth/gmail.metadata"))])

    with pytest.raises(PilotRejected) as denial:
        exchange_readonly_grant(denied, _token_form(), budget=budget)
    with pytest.raises(PilotRejected) as server:
        exchange_readonly_grant(rejected, _token_form(), budget=budget)
    with pytest.raises(PilotRejected) as ambiguous:
        exchange_readonly_grant(timed, _token_form(), budget=budget)
    with pytest.raises(PilotRejected) as redirect:
        exchange_readonly_grant(redirected, _token_form(), budget=budget)
    with pytest.raises(PilotRejected) as scope:
        exchange_readonly_grant(metadata, _token_form(), budget=budget)

    assert grant.scope == READONLY_SCOPE
    assert refreshed.scope == READONLY_SCOPE
    assert "synthetic-access" not in repr(grant)
    assert "synthetic-refresh" not in repr(grant)
    assert b"client_secret" not in success.body
    assert success.calls == [("POST", "https://oauth2.googleapis.com/token")]
    assert len(rejected.calls) == 1
    assert denial.value.code == "GMAIL_PILOT_DENIED"
    assert server.value.code == "GMAIL_PILOT_TOKEN_REJECTED"
    assert ambiguous.value.code == "GMAIL_PILOT_TOKEN_AMBIGUOUS"
    assert redirect.value.code == "GMAIL_PILOT_REDIRECT_REJECTED"
    assert scope.value.code == "GMAIL_PILOT_SCOPE_REJECTED"
    assert _counts(store) == (7, 0)
    capped, capped_store = _open_budget(tokens=20)
    with pytest.raises(PilotRejected) as stopped:
        exchange_readonly_grant(Scripted([]), _token_form(), budget=capped)
    assert stopped.value.code == "GMAIL_PILOT_BUDGET_EXHAUSTED"
    assert _counts(capped_store) == (20, 0)


def test_metadata_scope_cannot_acquire_messages_and_budget_survives_restart() -> None:
    budget, store = _open_budget(gets=50)
    grant = _issued_grant()
    transport = Scripted([])
    before = store.read()

    with pytest.raises(PilotRejected) as scope:
        acquire_readonly_messages(
            Scripted([]),
            ("label:synthetic",),
            grant=READONLY_SCOPE,  # type: ignore[arg-type]
            budget=budget,
            expected_mailbox=MAILBOX,
        )
    with pytest.raises(PilotRejected) as exhausted:
        acquire_readonly_messages(
            transport,
            ("label:synthetic",),
            grant=grant,
            budget=budget,
            expected_mailbox=MAILBOX,
        )
    restarted = DailyBudget(store, lambda: FIXED)

    with pytest.raises(PilotRejected) as again:
        acquire_readonly_messages(
            transport,
            ("label:synthetic",),
            grant=grant,
            budget=restarted,
            expected_mailbox=MAILBOX,
        )

    assert scope.value.code == "GMAIL_PILOT_SCOPE_REJECTED"
    assert exhausted.value.code == "GMAIL_PILOT_BUDGET_EXHAUSTED"
    assert again.value.code == "GMAIL_PILOT_BUDGET_EXHAUSTED"
    assert transport.calls == []
    assert store.read() == before
    assert _counts(store) == (0, 50)


def test_retry_redirect_and_pagination_stay_inside_the_cap() -> None:
    raw = plain_message("Entry: Buy stop $7.23.\n", "<pilot-page@example.invalid>")
    retry = Scripted(
        [
            _profile(),
            _labels(),
            (429, b"{}"),
            (200, _listed("provider-retry")[1]),
            _rfc822("provider-retry", raw),
        ]
    )
    evidence = _acquire(retry, ("label:synthetic",), limit=1)
    redirected = Scripted([(302, b"https://evil.example/")])
    with pytest.raises(PilotRejected) as redirect:
        _acquire(redirected, ("label:synthetic",))
    hostile = _reject_url("https://evil.example/gmail/v1/users/me/profile")
    first, second = "provider-one", "provider-two"
    pages = Scripted(
        [
            _profile(),
            _labels(),
            _json({"messages": [{"id": first}], "nextPageToken": "page-two"}),
            _json({"messages": [{"id": second}], "nextPageToken": "page-three"}),
            _rfc822(first, raw),
            _rfc822(second, raw.replace(b"pilot-page", b"pilot-next")),
        ]
    )
    paged = _acquire(pages, ("label:synthetic",), limit=2)
    repeated = Scripted([(500, b"{}"), (500, b"{}"), (500, b"{}")])
    with pytest.raises(PilotRejected) as failed:
        _acquire(repeated, ("label:synthetic",))

    assert evidence.messages[0].provider_message_id == "provider-retry"
    assert evidence.request_count == 5
    assert redirect.value.code == "GMAIL_PILOT_REDIRECT_REJECTED"
    assert hostile == "GMAIL_PILOT_ENDPOINT_REJECTED"
    assert [item.provider_message_id for item in paged.messages] == [first, second]
    assert len([url for _, url in pages.calls if "pageToken=" in url]) == 1
    assert "page-three" not in " ".join(url for _, url in pages.calls)
    assert failed.value.code == "GMAIL_PILOT_RETRY_EXHAUSTED"
    assert len(repeated.calls) == 3


def test_realistic_message_id_stays_distinct_and_non_actionable() -> None:
    raw = plain_message(body("tday_dated.txt"), "<abc123+tag@mail.example.com>")
    changed = plain_message("Entry: Buy stop $7.23.\n", "<abc123+tag@mail.example.com>")
    transport = Scripted(
        _ready(
            _listed("provider-real", "provider-copy"),
            _rfc822("provider-real", raw),
            _rfc822("provider-copy", changed),
        )
    )
    evidence = _acquire(transport, ("label:synthetic",), limit=2)
    first, second = evidence.messages

    assert first.rfc_message_id == "<abc123+tag@mail.example.com>"
    assert first.provider_message_id == "provider-real"
    assert first.rfc_message_id not in first.instruction_ids
    assert first.provider_message_id not in first.instruction_ids
    assert first.actionable is False
    assert first.disposition == "QUARANTINE"
    assert "NON_FIXTURE_MESSAGE_ID" in first.reasons
    assert second.reasons == ("CONFLICTING_DUPLICATE",)
    assert second.instruction_ids == ()


def _reject_url(url: str) -> str:
    try:
        _require_readonly_url(url)
    except PilotRejected as rejected:
        return rejected.code
    return ""


def _connection_args(budget: DailyBudget) -> dict[str, object]:
    return {
        "capability": "readonly",
        "client_id": "synthetic-client",
        "redirect_uri": REDIRECT,
        "state": STATE,
        "code_verifier": VERIFIER,
        "selectors": ("label:synthetic",),
        "budget": budget,
        "expected_mailbox": MAILBOX,
        "limit": 1,
    }


def test_readonly_connection_uses_the_validated_grant_for_every_get() -> None:
    raw = plain_message(body("tday_dated.txt"), "<pilot-success@example.invalid>")
    responses = [(200, _grant_body())]
    responses.extend(_ready(_listed("provider-success"), _rfc822("provider-success", raw)))
    transport = Scripted(responses)
    budget, store = _open_budget()
    evidence = run_readonly_connection(transport, callback=_callback(), **_connection_args(budget))
    digest = hashlib.sha256(b"synthetic-access").hexdigest()

    assert evidence.durable_state == "UNAVAILABLE"
    assert evidence.economic_dispatch is False
    assert evidence.messages[0].disposition == "ACCEPT"
    assert evidence.messages[0].actionable is True
    assert transport.calls[0] == ("POST", "https://oauth2.googleapis.com/token")
    assert transport.digests[0] is None
    assert transport.digests[1:] == [digest, digest, digest, digest]
    assert b"grant_type=authorization_code" in transport.bodies[0]
    assert b"code_verifier=" in transport.bodies[0]
    assert b"client_secret" not in b"".join(transport.bodies)
    assert "synthetic-access" not in repr(evidence)
    assert _counts(store) == (1, 4)


def test_connection_rejects_metadata_callback_and_redirect_before_http() -> None:
    budget, store = _open_budget()
    transport = Scripted([(200, _grant_body())])
    metadata = dict(_connection_args(budget), capability="metadata")
    bad_state = _callback(state="other-state")
    with pytest.raises(PilotRejected) as scope:
        run_readonly_connection(transport, callback=_callback(), **metadata)
    with pytest.raises(LocalOAuthProbeRejected) as state:
        run_readonly_connection(
            transport,
            callback=bad_state,
            **_connection_args(budget),
        )
    with pytest.raises(LocalOAuthProbeRejected) as redirect:
        run_readonly_connection(
            transport,
            callback=_callback(),
            **dict(_connection_args(budget), redirect_uri="https://evil.example/callback"),
        )
    with pytest.raises(LocalOAuthProbeRejected) as verifier:
        run_readonly_connection(
            transport,
            callback=_callback(),
            **dict(_connection_args(budget), code_verifier="short"),
        )

    assert scope.value.code == "GMAIL_PILOT_SCOPE_REJECTED"
    assert state.value.code == "GMAIL_OAUTH_STATE_REJECTED"
    assert redirect.value.code == "GMAIL_OAUTH_REDIRECT_REJECTED"
    assert verifier.value.code == "GMAIL_OAUTH_PKCE_REJECTED"
    assert transport.calls == []
    assert _counts(store) == (0, 0)


def test_connection_rejects_bad_token_results_without_a_message_read() -> None:
    budget, store = _open_budget()
    missing = Scripted([(200, b'{"scope":"https://www.googleapis.com/auth/gmail.readonly"}')])
    broader = Scripted(
        [(200, _grant_body(READONLY_SCOPE + " https://www.googleapis.com/auth/gmail.modify"))]
    )
    metadata = Scripted([(200, _grant_body("https://www.googleapis.com/auth/gmail.metadata"))])
    denied = Scripted([(403, b"{}")])
    timed = TimeoutAt(0, [(200, _grant_body())])
    injected = json.dumps(
        {"access_token": "synthetic\r\nhidden-value", "scope": READONLY_SCOPE}
    ).encode()
    hostile = Scripted([(200, injected)])

    with pytest.raises(PilotRejected) as absent:
        run_readonly_connection(missing, callback=_callback(), **_connection_args(budget))
    with pytest.raises(PilotRejected) as wide:
        run_readonly_connection(broader, callback=_callback(), **_connection_args(budget))
    with pytest.raises(PilotRejected) as wrong:
        run_readonly_connection(metadata, callback=_callback(), **_connection_args(budget))
    with pytest.raises(PilotRejected) as blocked:
        run_readonly_connection(denied, callback=_callback(), **_connection_args(budget))
    with pytest.raises(PilotRejected) as ambiguous:
        run_readonly_connection(timed, callback=_callback(), **_connection_args(budget))
    with pytest.raises(PilotRejected) as leaked:
        run_readonly_connection(hostile, callback=_callback(), **_connection_args(budget))

    assert absent.value.code == "GMAIL_PILOT_TOKEN_REJECTED"
    assert wide.value.code == "GMAIL_PILOT_SCOPE_REJECTED"
    assert wrong.value.code == "GMAIL_PILOT_SCOPE_REJECTED"
    assert blocked.value.code == "GMAIL_PILOT_DENIED"
    assert ambiguous.value.code == "GMAIL_PILOT_TOKEN_AMBIGUOUS"
    assert leaked.value.code == "GMAIL_PILOT_TOKEN_REJECTED"
    assert "hidden-value" not in f"{leaked.value} {leaked.value!r}"
    assert len(timed.calls) == 1
    assert all(call[0] == "POST" for call in missing.calls + broader.calls + metadata.calls)
    assert _counts(store) == (6, 0)


def test_refresh_connection_and_mailbox_mismatch_stop_at_the_right_request() -> None:
    raw = plain_message("Entry: Buy stop $7.23.\n", "<pilot-refresh@example.invalid>")
    responses = [(200, _grant_body())]
    responses.extend(_ready(_listed("provider-refresh"), _rfc822("provider-refresh", raw)))
    transport = Scripted(responses)
    budget, _store = _open_budget()
    evidence = run_readonly_connection(
        transport,
        refresh_token="synthetic-refresh",
        **_connection_args(budget),
    )
    mismatch = Scripted([(200, _grant_body()), _profile()])
    mismatch_budget, mismatch_store = _open_budget()
    with pytest.raises(PilotRejected) as rejected:
        run_readonly_connection(
            mismatch,
            callback=_callback(),
            **dict(_connection_args(mismatch_budget), expected_mailbox="other@example.invalid"),
        )

    assert evidence.messages[0].provider_message_id == "provider-refresh"
    assert evidence.economic_dispatch is False
    assert b"grant_type=refresh_token" in transport.bodies[0]
    assert b"grant_type=authorization_code" not in transport.bodies[0]
    assert "synthetic-refresh" not in repr(evidence)
    assert rejected.value.code == "GMAIL_PILOT_MAILBOX_REJECTED"
    assert [method for method, _url in mismatch.calls] == ["POST", "GET"]
    assert "/messages" not in mismatch.calls[1][1]
    assert _counts(mismatch_store) == (1, 1)


def test_hand_built_grant_and_missing_budget_do_not_dispatch() -> None:
    transport = Scripted([_profile()])
    with pytest.raises(PilotRejected) as unverified:
        TokenGrant(scope=READONLY_SCOPE, access_token="synthetic-access")
    with pytest.raises(PilotRejected) as missing:
        acquire_readonly_messages(
            transport,
            ("label:synthetic",),
            grant=_issued_grant(),
            expected_mailbox=MAILBOX,
        )

    assert unverified.value.code == "GMAIL_PILOT_GRANT_UNVERIFIED"
    assert "synthetic-access" not in f"{unverified.value} {unverified.value!r}"
    assert missing.value.code == "GMAIL_PILOT_BUDGET_UNAVAILABLE"
    assert transport.calls == []


def test_daily_budget_is_restart_safe_and_fail_closed(tmp_path: Path) -> None:
    budget, store = _open_budget()
    observed = store.read()
    DailyBudget(store, lambda: FIXED)
    assert store.read() == observed
    budget.consume_token()
    fresh = DailyBudget(store, lambda: FIXED)
    fresh.consume_get()
    with pytest.raises(PilotRejected) as seeded:
        seed_daily_budget(store, FIXED)
    path = tmp_path / "budget.json"
    file_store = FileBudgetStore(path)
    seed_daily_budget(file_store, FIXED)
    DailyBudget(file_store, lambda: FIXED).consume_get()
    recorded = path.read_text(encoding="utf-8")
    reopened = FileBudgetStore(path)
    assert reopened.read() == recorded
    DailyBudget(reopened, lambda: FIXED).consume_get()
    missing = tmp_path / "missing.json"
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{", encoding="utf-8")
    with pytest.raises(PilotRejected) as absent:
        DailyBudget(FileBudgetStore(missing), lambda: FIXED).consume_token()
    with pytest.raises(PilotRejected) as broken:
        DailyBudget(FileBudgetStore(corrupt), lambda: FIXED).consume_get()
    rolled = DailyBudget(store, lambda: FIXED - 60)
    with pytest.raises(PilotRejected) as rollback:
        rolled.consume_token()

    assert _counts(store) == (1, 1)
    assert seeded.value.code == "GMAIL_PILOT_BUDGET_INVALID"
    assert json.loads(path.read_text(encoding="utf-8"))["read_gets"] == 2
    assert absent.value.code == "GMAIL_PILOT_BUDGET_MISSING"
    assert missing.exists() is False
    assert broken.value.code == "GMAIL_PILOT_BUDGET_INVALID"
    assert corrupt.read_text(encoding="utf-8") == "{"
    assert rollback.value.code == "GMAIL_PILOT_BUDGET_INVALID"


def test_budget_day_boundary_daylight_saving_and_concurrency(tmp_path: Path) -> None:
    start = int(datetime(2026, 11, 14, 23, 30, tzinfo=NY).timestamp())
    later = int(datetime(2026, 11, 15, 0, 30, tzinfo=NY).timestamp())
    clock = [start]
    budget, store = _open_budget(start, tokens=20, clock=clock)
    with pytest.raises(PilotRejected) as exhausted:
        budget.consume_token()
    clock[0] = later
    budget.consume_token()
    early = int(datetime(2026, 3, 8, 1, 30, tzinfo=NY).timestamp())
    sprung = int(datetime(2026, 3, 8, 3, 30, tzinfo=NY).timestamp())
    spring_clock = [early]
    spring, spring_store = _open_budget(early, gets=4, clock=spring_clock)
    spring_clock[0] = sprung
    spring.consume_get()
    first = int(datetime(2026, 11, 1, 1, 30, tzinfo=NY, fold=0).timestamp())
    second = int(datetime(2026, 11, 1, 1, 30, tzinfo=NY, fold=1).timestamp())
    fall_clock = [first]
    fall, fall_store = _open_budget(first, gets=3, clock=fall_clock)
    fall_clock[0] = second
    fall.consume_get()
    shared = MemoryBudgetStore()
    seed_daily_budget(shared, FIXED)
    ok: list[int] = []
    bad: list[str] = []
    guard = threading.Lock()

    def worker() -> None:
        try:
            DailyBudget(shared, lambda: FIXED).consume_token()
        except PilotRejected as exc:
            with guard:
                bad.append(exc.code)
        else:
            with guard:
                ok.append(1)

    threads = [threading.Thread(target=worker) for _index in range(30)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    file_store = FileBudgetStore(tmp_path / "shared.json")
    seed_daily_budget(file_store, FIXED)
    file_ok: list[int] = []

    def file_worker() -> None:
        DailyBudget(FileBudgetStore(tmp_path / "shared.json"), lambda: FIXED).consume_get()
        with guard:
            file_ok.append(1)

    file_threads = [threading.Thread(target=file_worker) for _index in range(8)]
    for thread in file_threads:
        thread.start()
    for thread in file_threads:
        thread.join()
    rolled = json.loads(store.read() or "")
    spring_payload = json.loads(spring_store.read() or "")
    fall_payload = json.loads(fall_store.read() or "")

    assert exhausted.value.code == "GMAIL_PILOT_BUDGET_EXHAUSTED"
    assert rolled["day"] == "2026-11-15"
    assert rolled["token_attempts"] == 1
    assert spring_payload["day"] == "2026-03-08"
    assert spring_payload["read_gets"] == 5
    assert second > first
    assert fall_payload["day"] == "2026-11-01"
    assert fall_payload["read_gets"] == 4
    assert len(ok) == 20
    assert bad == ["GMAIL_PILOT_BUDGET_EXHAUSTED"] * 10
    assert len(file_ok) == 8
    assert json.loads((tmp_path / "shared.json").read_text(encoding="utf-8"))["read_gets"] == 8


def test_operator_grant_rejects_forgeries_and_cannot_enable_the_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from swingtrade.gmail_local_connect import run_local_windows_readonly_runtime
    from swingtrade.group4_email.gmail_readonly_pilot import (
        READONLY_CAMPAIGN,
        OperatorGrant,
        RuntimePaths,
        assess_readonly_runtime,
        grant_mac,
        mailbox_hash,
        standing_network_allowed,
        validate_operator_grant,
    )

    key = b"k" * 32
    document = _grant_document()
    mac = grant_mac(document, key)
    grant = validate_operator_grant(document, mac, key, FIXED)
    forged = dict(document)
    forged["effective"] = True
    forged["attended"] = True
    revoked = dict(document)
    revoked["revoked"] = True
    expired = dict(document)
    expired["expires_at"] = FIXED - 1

    with pytest.raises(PilotRejected) as unverified:
        OperatorGrant(
            capability="readonly",
            campaign=READONLY_CAMPAIGN,
            mailbox_hash=mailbox_hash(MAILBOX),
            expires_at=FIXED + 60,
        )
    with pytest.raises(PilotRejected) as extra:
        validate_operator_grant(forged, grant_mac(forged, key), key, FIXED)
    with pytest.raises(PilotRejected) as edited:
        validate_operator_grant(revoked, mac, key, FIXED)
    with pytest.raises(PilotRejected) as late:
        validate_operator_grant(expired, grant_mac(expired, key), key, FIXED)

    assert grant.capability == "readonly"
    assert MAILBOX not in repr(grant)
    assert unverified.value.code == "GMAIL_PILOT_GRANT_UNVERIFIED"
    assert extra.value.code == "GMAIL_PILOT_GRANT_REJECTED"
    assert edited.value.code == "GMAIL_PILOT_GRANT_REJECTED"
    assert late.value.code == "GMAIL_PILOT_GRANT_REJECTED"
    assert standing_network_allowed({"effective": True, "attended": True}) is False
    assert standing_network_allowed(grant) is False
    assert assess_readonly_runtime(document, mac, key=key, now=FIXED) == (
        "GMAIL_OAUTH_LIVE_UNAUTHORIZED"
    )
    assert assess_readonly_runtime(forged, mac, key=None, now=FIXED) == (
        "GMAIL_OAUTH_LIVE_UNAUTHORIZED"
    )
    empty = tmp_path / "empty"
    budget = empty / READONLY_CAMPAIGN
    budget.mkdir(parents=True)
    monkeypatch.setattr(
        "swingtrade.group4_email.gmail_readonly_pilot.production_runtime_paths",
        lambda: RuntimePaths(
            empty / "standing-grant.json",
            empty / "grant-key.bin",
            budget,
            empty / "desktop-client.json",
        ),
    )
    with pytest.raises(LocalOAuthProbeRejected) as blocked:
        run_local_windows_readonly_runtime()
    assert blocked.value.code == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"


def test_protected_budget_survives_restart_and_rejects_resets(tmp_path: Path) -> None:
    from swingtrade.group4_email.gmail_readonly_pilot import (
        ProtectedBudget,
        SealedFileStore,
        SealedMemoryStore,
        establish_protected_budget,
        protected_budget_file,
    )

    key = b"b" * 32
    directory = tmp_path / "GMAIL-READONLY-SIGNAL-DISCOVERY-20261114-R1"
    store = SealedFileStore(directory)
    establish_protected_budget(store, FIXED, key)
    ProtectedBudget(store, lambda: FIXED, key).consume_token()
    recorded = protected_budget_file(directory).read_text(encoding="utf-8")
    restarted = ProtectedBudget(SealedFileStore(directory), lambda: FIXED, key)
    restarted.consume_get()
    later = int(datetime(2026, 11, 15, 0, 30, tzinfo=NY).timestamp())
    with pytest.raises(PilotRejected) as forwarded:
        ProtectedBudget(store, lambda: later, key).consume_token()
    with pytest.raises(PilotRejected) as rolled:
        ProtectedBudget(store, lambda: FIXED - 60, key).consume_get()
    path = protected_budget_file(directory)
    path.unlink()
    with pytest.raises(PilotRejected) as missing:
        ProtectedBudget(SealedFileStore(directory), lambda: FIXED, key).consume_token()
    other = tmp_path / "other-budget.json"
    other.write_text(recorded, encoding="utf-8")
    with pytest.raises(PilotRejected) as caller_path:
        protected_budget_file(tmp_path)
    memory = SealedMemoryStore()
    establish_protected_budget(memory, FIXED, key)
    ProtectedBudget(memory, lambda: FIXED, key).consume_token()
    tampered = json.loads(memory.read() or "")
    tampered["token_attempts"] = 0
    memory.update(lambda _current: json.dumps(tampered))
    with pytest.raises(PilotRejected) as seal:
        ProtectedBudget(memory, lambda: FIXED, key).consume_token()

    assert json.loads(path.read_text(encoding="utf-8") if path.exists() else "{}") == {}
    assert missing.value.code == "GMAIL_PILOT_BUDGET_MISSING"
    assert path.exists() is False
    assert forwarded.value.code == "GMAIL_PILOT_BUDGET_INVALID"
    assert rolled.value.code == "GMAIL_PILOT_BUDGET_INVALID"
    assert caller_path.value.code == "GMAIL_PILOT_BUDGET_INVALID"
    assert seal.value.code == "GMAIL_PILOT_BUDGET_INVALID"
    assert other.read_text(encoding="utf-8") == recorded
    assert "token_attempts" in recorded


def test_readonly_transport_ignores_proxies_and_verifies_tls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ssl
    from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request

    from swingtrade.group4_email.gmail_readonly_pilot import (
        bounded_body,
        readonly_opener,
        retry_class,
    )

    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    opener = readonly_opener()
    rendered = " ".join(type(item).__name__ for item in opener.handlers)
    https = [item for item in opener.handlers if isinstance(item, HTTPSHandler)]
    redirects = [item for item in opener.handlers if isinstance(item, HTTPRedirectHandler)]
    hostile = Request("https://evil.example/path")

    assert "127.0.0.1:9" not in rendered
    assert "ProxyHandler" not in rendered
    assert https[0]._context is not None
    assert https[0]._context.check_hostname is True
    assert https[0]._context.verify_mode == ssl.CERT_REQUIRED
    with pytest.raises(PilotRejected) as wrong_host:
        https[0].https_open(hostile)
    with pytest.raises(PilotRejected) as redirect:
        redirects[0].redirect_request(hostile, None, 302, "moved", {}, "https://evil.example/")
    assert wrong_host.value.code == "GMAIL_PILOT_ENDPOINT_REJECTED"
    assert redirect.value.code == "GMAIL_PILOT_REDIRECT_REJECTED"
    assert retry_class(429) == "RETRYABLE_GET"
    assert retry_class(401) == "DENIED"
    assert retry_class(302) == "REDIRECT_REJECTED"
    with pytest.raises(PilotRejected) as oversized:
        bounded_body(b"x" * 65537)
    assert oversized.value.code == "GMAIL_PILOT_MALFORMED"
    assert "urlopen" not in MODULE.read_text(encoding="utf-8")


def test_mock_custody_releases_and_native_read_stays_closed() -> None:
    from swingtrade.gmail_credential.errors import CredentialOperationError
    from swingtrade.gmail_credential.mock_port import MockCredentialPort
    from swingtrade.gmail_credential.secret import synthetic_fixture
    from swingtrade.group4_email.gmail_readonly_pilot import (
        exercise_mock_custody,
        native_credential_read,
    )

    secret = synthetic_fixture(b"synthetic-refresh-material")
    port = MockCredentialPort()
    assert exercise_mock_custody(secret, port) == "CUSTODY_SHAPE_PASS"
    assert port.live_allocation_count() == 0
    assert port.release_count >= 1
    port.raise_after_read = True
    with pytest.raises(CredentialOperationError) as failed:
        port.read_attempts = port.read_attempts
        from swingtrade.gmail_credential.adapter import GmailCredentialAdapter

        GmailCredentialAdapter(port).retrieve()
    with pytest.raises(PilotRejected) as native:
        native_credential_read()

    assert failed.value.code == "read_consumer_failed"
    assert "synthetic-refresh-material" not in f"{failed.value} {failed.value!r}"
    assert native.value.code == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"
    assert port.live_allocation_count() == 0


def test_fixture_receipt_handoff_does_not_admit_real_message_ids() -> None:
    from swingtrade.group4_email.gmail_readonly_pilot import READONLY_CAMPAIGN, handoff_mime
    from swingtrade.instruction_receipt import InMemoryReceiptStore

    store = InMemoryReceiptStore()
    accepted = plain_message(body("tday_dated.txt"), "<pilot-success@example.invalid>")
    first = handoff_mime(accepted, "provider-success", store)
    replay = handoff_mime(accepted, "provider-success", store)
    recognized = plain_message(body("tday_dated.txt"), "<abc123+tag@mail.example.com>")
    held = handoff_mime(recognized, "provider-real", store)
    forwarded = plain_message(
        "---------- Forwarded message ---------\n" + body("tday_undated.txt"),
        "<forward@example.invalid>",
    )
    quarantine = handoff_mime(forwarded, "provider-forward", store)

    assert first.classification == "ACCEPT"
    assert first.replay_kind == "NEW"
    assert first.campaign == READONLY_CAMPAIGN
    assert replay.replay_kind == "REPLAY"
    assert replay.receipt_key == first.receipt_key
    assert held.classification == "NON_ACTIONABLE"
    assert held.receipt_key is None
    assert held.replay_kind is None
    assert quarantine.classification == "QUARANTINE"
    assert quarantine.receipt_key is None
    assert len(store) == 1
    assert MAILBOX not in repr(first)
    assert "synthetic-access" not in repr(first)


def _grant_document() -> dict[str, object]:
    from swingtrade.group4_email.gmail_readonly_pilot import READONLY_CAMPAIGN, mailbox_hash

    return {
        "budget_id": READONLY_CAMPAIGN,
        "campaign": READONLY_CAMPAIGN,
        "capability": "readonly",
        "custody_target": "swing-trading/lane3/gmail/dev/refresh-token",
        "decision": "LANE1_GMAIL_STANDING_READONLY_CONNECTION_AUTHORIZED",
        "scope": "https://www.googleapis.com/auth/gmail.readonly",
        "selector": "from:signals@example.invalid",
        "endpoints": [
            "https://oauth2.googleapis.com/token",
            "https://gmail.googleapis.com/gmail/v1/users/me/",
        ],
        "expires_at": FIXED + 3600,
        "mailbox_hash": mailbox_hash(MAILBOX),
        "methods": ["GET", "POST"],
        "not_before": FIXED - 10,
        "revoked": False,
        "runtime": "win32",
    }


class _Port:
    def __init__(self, material: bytes = b"synthetic-refresh", fail: str | None = None) -> None:
        self.material = bytearray(material)
        self.fail = fail
        self.reads = 0
        self.releases = 0

    def read(self) -> bytes:
        self.reads += 1
        if self.fail is not None:
            raise PilotRejected(self.fail)
        return bytes(self.material)

    def release(self) -> None:
        self.releases += 1
        self.material = bytearray(b"\x00" * len(self.material))


class _Bindings:
    def __init__(
        self,
        blob: bytes = b"synthetic-refresh",
        *,
        fail_copy: bool = False,
        fail_free: bool = False,
    ) -> None:
        self.blob = blob
        self.fail_copy = fail_copy
        self.fail_free = fail_free
        self.reads = 0
        self.frees = 0

    def cred_read(self, _target: str, pointer: list[object]) -> bool:
        self.reads += 1
        pointer[0] = object()
        return True

    def copy_blob(self, _pointer: list[object]) -> bytes:
        if self.fail_copy:
            raise RuntimeError("copy failed")
        return self.blob

    def cred_free(self, pointer: list[object]) -> None:
        self.frees += 1
        pointer[0] = None
        if self.fail_free:
            raise RuntimeError("free failed")


def _prepare(
    root: Path,
    document: dict[str, object] | None = None,
    *,
    mac: str | None = None,
    key: bytes = b"k" * 32,
    write_grant: bool = True,
) -> object:
    from swingtrade.group4_email.gmail_readonly_pilot import (
        READONLY_CAMPAIGN,
        RuntimePaths,
        grant_mac,
    )

    budget = root / READONLY_CAMPAIGN
    budget.mkdir(parents=True)
    (root / "grant-key.bin").write_bytes(key)
    if write_grant:
        chosen = _grant_document() if document is None else document
        signature = grant_mac(chosen, key) if mac is None else mac
        (root / "standing-grant.json").write_text(
            json.dumps({"document": chosen, "mac": signature}),
            encoding="utf-8",
        )
    (root / "desktop-client.json").write_text(
        json.dumps({"installed": {"client_id": "synthetic-client"}}),
        encoding="utf-8",
    )
    return RuntimePaths(
        root / "standing-grant.json",
        root / "grant-key.bin",
        budget,
        root / "desktop-client.json",
    )


def _seal(paths: object, key: bytes = b"k" * 32) -> None:
    from swingtrade.group4_email.gmail_readonly_pilot import (
        SealedFileStore,
        establish_protected_budget,
    )

    establish_protected_budget(SealedFileStore(paths.budget_dir), FIXED, key)  # type: ignore[attr-defined]


def test_authorized_runtime_fails_closed_until_a_real_grant(tmp_path: Path) -> None:
    import ssl

    from swingtrade.group4_email.gmail_readonly_pilot import (
        BoundOpenerTransport,
        PilotRejected,
        execute_trusted_runtime,
        native_credential_read,
        read_native_credential,
        readonly_opener,
    )

    def run(
        name: str,
        document: dict[str, object] | None = None,
        *,
        mac: str | None = None,
        key: bytes = b"k" * 32,
        write_grant: bool = True,
        seal: bool = False,
        transport: Scripted | None = None,
        port: _Port | None = None,
        live: bool = False,
    ) -> object:
        paths = _prepare(
            tmp_path / name,
            document,
            mac=mac,
            key=key,
            write_grant=write_grant,
        )
        if seal:
            _seal(paths, key)
        holder = port or _Port()
        calls = {"count": 0}

        def factory() -> _Port:
            calls["count"] += 1
            return holder

        if live:
            return execute_trusted_runtime(paths, now=FIXED, transport=None)  # type: ignore[arg-type]
        try:
            result = execute_trusted_runtime(
                paths,  # type: ignore[arg-type]
                now=FIXED,
                transport=transport or Scripted([]),
                custody_factory=factory,
            )
        except PilotRejected as rejected:
            assert calls["count"] == 0 or holder.reads == holder.releases
            return rejected
        assert calls["count"] == 1
        assert holder.reads == 1
        assert holder.releases == 1
        return result

    missing = run("missing", write_grant=False, key=b"x")
    forged = run("forged", mac="ab" * 32)
    expired = dict(_grant_document())
    expired["expires_at"] = FIXED
    late = run("expired", expired)
    revoked = dict(_grant_document())
    revoked["revoked"] = True
    stopped = run("revoked", revoked)
    wrong_box = dict(_grant_document())
    wrong_box["mailbox_hash"] = "ab" * 32
    mailbox = run(
        "mailbox",
        wrong_box,
        seal=True,
        transport=Scripted(
            [
                _json({"access_token": "synthetic-access", "scope": READONLY_SCOPE}),
                _profile(),
            ]
        ),
    )
    campaign = dict(_grant_document())
    campaign["campaign"] = "OTHER-CAMPAIGN"
    campaign["budget_id"] = "OTHER-CAMPAIGN"
    other = run("campaign", campaign)
    scope = dict(_grant_document())
    scope["scope"] = "https://www.googleapis.com/auth/gmail.metadata"
    metadata = run("scope", scope)
    runtime = dict(_grant_document())
    runtime["runtime"] = "linux"
    platform = run("runtime", runtime)
    custody = dict(_grant_document())
    custody["custody_target"] = "swing-trading/other"
    target = run("custody", custody)
    budget = run("budget", seal=False)
    corrupt_paths = _prepare(tmp_path / "corrupt")
    _seal(corrupt_paths)
    budget_file = corrupt_paths.budget_dir / "budget.json"  # type: ignore[attr-defined]
    budget_file.write_text(
        "deleted",
        encoding="utf-8",
    )
    corrupt_port = _Port()
    with pytest.raises(PilotRejected) as corrupt:
        execute_trusted_runtime(
            corrupt_paths,  # type: ignore[arg-type]
            now=FIXED,
            transport=Scripted([]),
            custody_factory=lambda: corrupt_port,
        )
    with pytest.raises(PilotRejected) as blocked_live:
        run("live", seal=True, live=True)

    opener = readonly_opener()
    names = ",".join(type(handler).__name__ for handler in opener.handlers)
    hostile = BoundOpenerTransport(opener)

    class _Redirect:
        def open(self, _request: object, timeout: int = 0) -> object:
            raise PilotRejected("GMAIL_PILOT_REDIRECT_REJECTED")

    class _Tls:
        def open(self, _request: object, timeout: int = 0) -> object:
            raise ssl.SSLError("synthetic")

    with pytest.raises(PilotRejected) as wrong_host:
        hostile.exchange("GET", "https://evil.example/messages")
    with pytest.raises(PilotRejected) as redirect:
        BoundOpenerTransport(_Redirect()).exchange(
            "GET",
            "https://gmail.googleapis.com/gmail/v1/users/me/profile",
        )
    with pytest.raises(PilotRejected) as tls:
        BoundOpenerTransport(_Tls()).exchange(
            "GET",
            "https://gmail.googleapis.com/gmail/v1/users/me/profile",
        )
    native = _Bindings()
    with pytest.raises(PilotRejected) as unread:
        native_credential_read()
    with pytest.raises(PilotRejected) as wrong_native:
        read_native_credential("swing-trading/other", native)
    failed_copy = _Bindings(fail_copy=True)
    with pytest.raises(PilotRejected):
        read_native_credential(
            "swing-trading/lane3/gmail/dev/refresh-token",
            failed_copy,
        )
    failed_free = _Bindings(fail_free=True)
    with pytest.raises(PilotRejected):
        read_native_credential(
            "swing-trading/lane3/gmail/dev/refresh-token",
            failed_free,
        )
    raw = (
        b"Message-ID: <outside@signals.example>\r\n"
        b"From: signals@example.invalid\r\n"
        b"Subject: Desk note\r\n"
        b"Date: Sat, 14 Nov 2026 17:00:00 +0000\r\n"
        b"\r\n"
        b"not a signal\r\n"
    )
    scripted = Scripted(
        [
            _json({"access_token": "synthetic-access", "scope": READONLY_SCOPE}),
            _profile(),
            _labels(),
            _listed("provider-1"),
            _rfc822("provider-1", raw),
        ]
    )
    inspected = run("connected", seal=True, transport=scripted)
    empty = Scripted(
        [
            _json({"access_token": "synthetic-access", "scope": READONLY_SCOPE}),
            _profile(),
            _labels(),
            _json({"messages": []}),
        ]
    )
    quiet = run("quiet", seal=True, transport=empty)
    mismatched = Scripted(
        [
            _json({"access_token": "synthetic-access", "scope": READONLY_SCOPE}),
            _json({"emailAddress": "other@example.invalid", "messagesTotal": 1, "threadsTotal": 1}),
        ]
    )
    rejected_box = run("profile", seal=True, transport=mismatched)
    malformed = run("token", seal=True, transport=Scripted([(200, b"{")]))
    denied = run(
        "denied",
        seal=True,
        transport=Scripted(
            [
                _json({"access_token": "synthetic-access", "scope": READONLY_SCOPE}),
                (403, b"{}"),
            ]
        ),
    )
    failed_port = run("credential", seal=True, port=_Port(fail="GMAIL_PILOT_CUSTODY_REJECTED"))

    assert missing.code == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"  # type: ignore[attr-defined]
    assert forged.code == "GMAIL_PILOT_GRANT_REJECTED"  # type: ignore[attr-defined]
    assert late.code == "GMAIL_PILOT_GRANT_REJECTED"  # type: ignore[attr-defined]
    assert stopped.code == "GMAIL_PILOT_GRANT_REJECTED"  # type: ignore[attr-defined]
    assert mailbox.code == "GMAIL_PILOT_MAILBOX_REJECTED"  # type: ignore[attr-defined]
    assert other.code == "GMAIL_PILOT_GRANT_REJECTED"  # type: ignore[attr-defined]
    assert metadata.code == "GMAIL_PILOT_GRANT_REJECTED"  # type: ignore[attr-defined]
    assert platform.code == "GMAIL_PILOT_GRANT_REJECTED"  # type: ignore[attr-defined]
    assert target.code == "GMAIL_PILOT_GRANT_REJECTED"  # type: ignore[attr-defined]
    assert budget.code == "GMAIL_PILOT_BUDGET_INVALID"  # type: ignore[attr-defined]
    assert corrupt.value.code == "GMAIL_PILOT_BUDGET_INVALID"
    assert corrupt_port.reads == 0
    assert blocked_live.value.code == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"
    assert "ProxyHandler" not in names
    assert wrong_host.value.code == "GMAIL_PILOT_ENDPOINT_REJECTED"
    assert redirect.value.code == "GMAIL_PILOT_REDIRECT_REJECTED"
    assert tls.value.code == "GMAIL_PILOT_TLS_REJECTED"
    assert unread.value.code == "GMAIL_OAUTH_LIVE_UNAUTHORIZED"
    assert wrong_native.value.code == "GMAIL_PILOT_CUSTODY_REJECTED"
    assert native.reads == 0
    assert failed_copy.frees == 1
    assert failed_free.frees == 1
    assert inspected.code == "READONLY_RUNTIME_INJECTED_PASS"  # type: ignore[attr-defined]
    assert inspected.transport_mode == "injected"  # type: ignore[attr-defined]
    assert inspected.economic_dispatch is False  # type: ignore[attr-defined]
    assert inspected.profile_matched is True  # type: ignore[attr-defined]
    assert inspected.message_count == 1  # type: ignore[attr-defined]
    assert inspected.classifications == ("NON_ACTIONABLE",)  # type: ignore[attr-defined]
    assert inspected.token_attempts == 1  # type: ignore[attr-defined]
    assert inspected.read_gets == 4  # type: ignore[attr-defined]
    assert quiet.message_count == 0  # type: ignore[attr-defined]
    assert quiet.read_gets == 3  # type: ignore[attr-defined]
    assert rejected_box.code == "GMAIL_PILOT_MAILBOX_REJECTED"  # type: ignore[attr-defined]
    assert malformed.code == "GMAIL_PILOT_MALFORMED"  # type: ignore[attr-defined]
    assert denied.code == "GMAIL_PILOT_DENIED"  # type: ignore[attr-defined]
    assert failed_port.code == "GMAIL_PILOT_CUSTODY_REJECTED"  # type: ignore[attr-defined]
    rendered = repr(inspected)
    assert MAILBOX not in rendered
    assert "synthetic-access" not in rendered
    assert "synthetic-refresh" not in rendered
    assert all("attachments" not in url for _method, url in scripted.calls)
    assert scripted.calls[0][0] == "POST"
    assert [method for method, _url in scripted.calls].count("GET") == 4
