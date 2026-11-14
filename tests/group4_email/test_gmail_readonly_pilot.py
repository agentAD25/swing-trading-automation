"""Mocked read-only Gmail acquisition. No provider call is made."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from swingtrade.group4_email.gmail_readonly_pilot import (
    READONLY_SCOPE,
    PilotRejected,
    ReadBudget,
    _require_readonly_url,
    acquire_readonly_messages,
    exchange_readonly_grant,
)
from swingtrade.group4_email.local_oauth_probe import build_refresh_request, build_token_request
from swingtrade.group4_email.parse import MessageIdentityRegistry
from tests.group4_email.conftest import body, plain_message

MODULE = Path("src/swingtrade/group4_email/gmail_readonly_pilot.py")
SELECTORS = ("from:signals@example.invalid", "label:synthetic")
API = "https://gmail.googleapis.com/gmail/v1/users/me"


class Scripted:
    def __init__(self, responses: list[tuple[int, bytes]]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str]] = []

    def exchange(self, method: str, url: str, body: bytes = b"") -> tuple[int, bytes]:
        self.calls.append((method, url))
        self.body = body
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)


class TimeoutAt(Scripted):
    def __init__(self, index: int, responses: list[tuple[int, bytes]]) -> None:
        super().__init__(responses)
        self.index = index
        self._seen = 0

    def exchange(self, method: str, url: str) -> tuple[int, bytes]:
        current = self._seen
        self._seen += 1
        if current == self.index:
            self.calls.append((method, url))
            raise TimeoutError
        return super().exchange(method, url)


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

    evidence = acquire_readonly_messages(transport, SELECTORS, limit=1)
    repeated = acquire_readonly_messages(
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

    evidence = acquire_readonly_messages(transport, ("label:synthetic",))

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

    evidence = acquire_readonly_messages(transport, ("label:synthetic",), limit=1)

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

    incomplete_evidence = acquire_readonly_messages(
        incomplete_transport, ("label:synthetic",), limit=1
    )
    note_evidence = acquire_readonly_messages(note_transport, ("label:synthetic",), limit=1)
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

    evidence = acquire_readonly_messages(transport, ("label:synthetic",), limit=2)

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
        acquire_readonly_messages(timeout, ("label:synthetic",))
    with pytest.raises(PilotRejected) as blocked:
        acquire_readonly_messages(denied, ("label:synthetic",))

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

    original = acquire_readonly_messages(
        first,
        ("label:synthetic",),
        limit=2,
        registry=registry,
        seen_provider_ids=seen,
    )
    replay = acquire_readonly_messages(
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
        acquire_readonly_messages(malformed, ("label:synthetic",))
    with pytest.raises(PilotRejected) as selected:
        acquire_readonly_messages(Scripted([]), ("subject:trade",))
    with pytest.raises(PilotRejected) as limited:
        acquire_readonly_messages(Scripted([]), ("label:synthetic",), limit=11)

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

    evidence = acquire_readonly_messages(transport, ("label:synthetic",), limit=1)

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


def test_token_exchange_and_refresh_hide_tokens_and_reject_bad_results() -> None:
    budget = ReadBudget()
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
    assert budget.token_attempts == 7
    capped = ReadBudget(token_attempts=20)
    with pytest.raises(PilotRejected) as stopped:
        exchange_readonly_grant(Scripted([]), _token_form(), budget=capped)
    assert stopped.value.code == "GMAIL_PILOT_BUDGET_EXHAUSTED"
    assert capped.token_attempts == 20


def test_metadata_scope_cannot_acquire_messages_and_budget_survives_restart() -> None:
    budget = ReadBudget(read_gets=50)
    transport = Scripted([])

    with pytest.raises(PilotRejected) as scope:
        acquire_readonly_messages(Scripted([]), ("label:synthetic",), granted_scope="metadata")
    with pytest.raises(PilotRejected) as exhausted:
        acquire_readonly_messages(transport, ("label:synthetic",), budget=budget)

    assert scope.value.code == "GMAIL_PILOT_SCOPE_REJECTED"
    assert exhausted.value.code == "GMAIL_PILOT_BUDGET_EXHAUSTED"
    assert transport.calls == []
    assert budget.read_gets == 50


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
    evidence = acquire_readonly_messages(retry, ("label:synthetic",), limit=1)
    redirected = Scripted([(302, b"https://evil.example/")])
    with pytest.raises(PilotRejected) as redirect:
        acquire_readonly_messages(redirected, ("label:synthetic",))
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
    paged = acquire_readonly_messages(pages, ("label:synthetic",), limit=2)
    repeated = Scripted([(500, b"{}"), (500, b"{}"), (500, b"{}")])
    with pytest.raises(PilotRejected) as failed:
        acquire_readonly_messages(repeated, ("label:synthetic",))

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
    evidence = acquire_readonly_messages(transport, ("label:synthetic",), limit=2)
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
