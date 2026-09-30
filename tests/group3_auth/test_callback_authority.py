from __future__ import annotations

import socket
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from swingtrade.contracts.monitoring import MonitoringConditionCode, NullMonitoringEmitter
from swingtrade.group3_auth import (
    OutcomeCode,
    StateIssuer,
    assemble_authorization_request,
    classify_callback,
)
from swingtrade.group3_auth.flow import FlowMode

ISSUED = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)
EXPIRES = datetime(2026, 9, 30, 12, 10, tzinfo=UTC)
NOW = datetime(2026, 9, 30, 12, 1, tzinfo=UTC)
REDIRECT = "https://app.example/cb"
_CODE = "variable-length-code"


def _factory(value: str):
    def issue(nbytes: int) -> str:
        assert nbytes == 32
        return value

    return issue


def _fullwidth(text: str) -> str:
    return "".join(
        chr(ord(character) + 0xFEE0) if "!" <= character <= "~" else character
        for character in text
    )


def _issued_state() -> tuple[StateIssuer, str]:
    issuer = StateIssuer(token_factory=_factory("s" * 43))
    assembly = assemble_authorization_request(
        flow=FlowMode.STANDARD,
        client_id="client-1",
        redirect_uri=REDIRECT,
        scope="openid",
        issuer=issuer,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    assert assembly.url is not None
    state = dict(parse_qsl(urlsplit(assembly.url).query))["state"]
    return issuer, state


def _later_legitimate(issuer: StateIssuer, state: str) -> None:
    accepted = classify_callback(
        issuer,
        f"{REDIRECT}?code={_CODE}&state={state}",
        now=NOW,
        allowed_callbacks=(REDIRECT,),
    )
    assert accepted.decision.code is OutcomeCode.CLASSIFIED
    assert accepted.decision.reason == "AUTHORIZATION_CODE"
    assert accepted.code_present is True
    assert accepted.decision.safe_to_retry is False
    assert _CODE not in repr(accepted)


def test_callback_reuses_group2_authority_rule_without_a_second_denylist() -> None:
    source = Path("src/swingtrade/group3_auth/callback.py").read_text(encoding="utf-8")
    assert "live_authority_prohibited" in source
    assert "api.tradestation.com" not in source
    assert ".rstrip(" not in source
    assert "unquote" not in source


def test_noncanonical_live_callback_preserves_state_for_a_later_callback() -> None:
    issuer, state = _issued_state()
    emitter = NullMonitoringEmitter()
    hostile = f"https://api.tradestation.com./cb?code={_CODE}&state={state}"
    classified = classify_callback(
        issuer,
        hostile,
        now=NOW,
        allowed_callbacks=(REDIRECT,),
        emitter=emitter,
    )
    assert classified.decision.reason == "LIVE_HOST_PROHIBITED"
    assert classified.code_present is False
    assert classified.decision.network_permitted is False
    assert _CODE not in repr(classified)
    assert emitter.conditions[-1].code is MonitoringConditionCode.FORBIDDEN_HOST
    assert _CODE not in str(emitter.conditions[-1].safe_context)
    _later_legitimate(issuer, state)


def test_percent_encoded_live_dot_preserves_state(monkeypatch) -> None:
    def explode(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket")

    monkeypatch.setattr(socket, "socket", explode)
    monkeypatch.setattr(socket, "create_connection", explode)
    issuer, state = _issued_state()
    encoded = f"https://api%2etradestation.com/cb?code={_CODE}&state={state}"
    classified = classify_callback(
        issuer,
        encoded,
        now=NOW,
        allowed_callbacks=(REDIRECT, "https://api.tradestation.com/cb"),
    )
    assert classified.decision.reason == "LIVE_HOST_PROHIBITED"
    assert classified.code_present is False
    _later_legitimate(issuer, state)


def test_other_live_authority_forms_do_not_consume_state() -> None:
    forms = [
        "https://api.tradestation.com%2e/cb?code={code}&state={state}",
        "https://API.TRADESTATION.COM/cb?code={code}&state={state}",
        "https://user:supersecret@api.tradestation.com/cb?code={code}&state={state}",
        "https://api.tradestation.com:443/cb?code={code}&state={state}",
        " https://api.tradestation.com/cb?code={code}&state={state} ",
        "https://api.tradestation.com\\cb?code={code}&state={state}",
        _fullwidth("https://api.tradestation.com/cb") + "?code={code}&state={state}",
        "https://api.tradestation.com/cb?code={code}&state={state}".replace("api", "api\u200b"),
        unicodedata.normalize("NFD", "https://api.tradestation.com/cb")
        + "?code={code}&state={state}",
    ]
    for template in forms:
        issuer, state = _issued_state()
        raw = template.format(code=_CODE, state=state)
        classified = classify_callback(
            issuer,
            raw,
            now=NOW,
            allowed_callbacks=(REDIRECT,),
        )
        assert classified.decision.reason == "LIVE_HOST_PROHIBITED"
        assert classified.code_present is False
        assert "supersecret" not in repr(classified)
        assert _CODE not in repr(classified)
        _later_legitimate(issuer, state)


def test_noncanonical_allowlisted_forms_are_rejected_without_repair() -> None:
    forms = [
        "https://app.example./cb?code={code}&state={state}",
        "https://app%2eexample/cb?code={code}&state={state}",
        "https://APP.example/cb?code={code}&state={state}",
        "https://app.example:443/cb?code={code}&state={state}",
        "HTTPS://app.example/cb?code={code}&state={state}",
        "https://app.example/cb/?code={code}&state={state}",
        "https://user:secret@app.example/cb?code={code}&state={state}",
        "https://app.example/cb?code={code}&state={state}#fragment",
    ]
    for template in forms:
        issuer, state = _issued_state()
        classified = classify_callback(
            issuer,
            template.format(code=_CODE, state=state),
            now=NOW,
            allowed_callbacks=(REDIRECT,),
        )
        assert classified.decision.reason == "CALLBACK_AUTHORITY_REJECTED"
        assert classified.code_present is False
        assert classified.decision.safe_to_retry is False
        _later_legitimate(issuer, state)


def test_noncanonical_allowlist_entry_does_not_authorize_a_repaired_host() -> None:
    issuer, state = _issued_state()
    dotted = classify_callback(
        issuer,
        f"https://app.example./cb?code={_CODE}&state={state}",
        now=NOW,
        allowed_callbacks=("https://app.example./cb",),
    )
    assert dotted.decision.reason == "MALFORMED_CALLBACK"
    assert dotted.code_present is False
    repaired = classify_callback(
        issuer,
        f"{REDIRECT}?code={_CODE}&state={state}",
        now=NOW,
        allowed_callbacks=("https://app.example./cb",),
    )
    assert repaired.decision.reason == "MALFORMED_CALLBACK"
    assert repaired.code_present is False
    _later_legitimate(issuer, state)


def test_unknown_callback_error_does_not_consume_state() -> None:
    issuer, state = _issued_state()
    unknown = classify_callback(
        issuer,
        f"{REDIRECT}?error=server_error&state={state}",
        now=NOW,
        allowed_callbacks=(REDIRECT,),
    )
    assert unknown.decision.code is OutcomeCode.UNKNOWN
    assert unknown.code_present is False
    assert unknown.decision.safe_to_retry is False
    _later_legitimate(issuer, state)
