from __future__ import annotations

import secrets
from datetime import UTC, datetime
from urllib.parse import parse_qsl, urlsplit

from swingtrade.contracts.monitoring import MonitoringConditionCode, NullMonitoringEmitter
from swingtrade.group3_auth import (
    DOCUMENTED_AUDIENCE,
    FlowMode,
    OutcomeCode,
    StateIssuer,
    assemble_authorization_request,
    authorization_code_form,
    classify_callback,
    read_token_fixture,
    refresh_form,
    s256_challenge,
)

ISSUED = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)
EXPIRES = datetime(2026, 9, 30, 12, 10, tzinfo=UTC)
NOW = datetime(2026, 9, 30, 12, 1, tzinfo=UTC)
REDIRECT = "https://app.example/cb"
VERIFIER = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
CHALLENGE = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"


def _factory(value: str):
    def issue(nbytes: int) -> str:
        assert nbytes == 32
        return value

    return issue


def test_stdlib_randomness_is_the_default_seam(monkeypatch) -> None:
    def fake(nbytes: int) -> str:
        assert nbytes == 32
        return "s" * 43

    monkeypatch.setattr(secrets, "token_urlsafe", fake)
    issued = StateIssuer().issue(issued_at=ISSUED, expires_at=EXPIRES)
    assert issued.value == "s" * 43
    assert str(issued) == "IssuedState"


def test_s256_uses_the_documented_challenge_shape() -> None:
    assert s256_challenge(VERIFIER) == CHALLENGE


def test_authorization_request_copies_the_documented_audience_and_supplied_scope() -> None:
    issuer = StateIssuer(token_factory=_factory("s" * 43))
    assembly = assemble_authorization_request(
        flow=FlowMode.STANDARD,
        client_id="client-1",
        redirect_uri="https://app.example/cb",
        scope="openid ReadAccount",
        issuer=issuer,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    assert assembly.decision.code is OutcomeCode.ASSEMBLED
    assert assembly.decision.safe_to_retry is False
    assert assembly.decision.network_permitted is False
    assert assembly.url is not None
    query = dict(parse_qsl(urlsplit(assembly.url).query))
    assert query["response_type"] == "code"
    assert query["client_id"] == "client-1"
    assert query["redirect_uri"] == "https://app.example/cb"
    assert query["audience"] == DOCUMENTED_AUDIENCE
    assert query["scope"] == "openid ReadAccount"
    assert query["state"] == "s" * 43
    assert "code_challenge" not in query
    assert "client-1" not in repr(assembly)
    assert assembly.parameter_names[:6] == (
        "response_type",
        "client_id",
        "redirect_uri",
        "audience",
        "scope",
        "state",
    )


def test_scope_text_is_not_rewritten() -> None:
    issuer = StateIssuer(token_factory=_factory("s" * 43))
    assembly = assemble_authorization_request(
        flow=FlowMode.STANDARD,
        client_id="client-1",
        redirect_uri="https://app.example/cb",
        scope="Trade",
        issuer=issuer,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    assert assembly.url is not None
    query = dict(parse_qsl(urlsplit(assembly.url).query))
    assert query["scope"] == "Trade"
    assert "offline_access" not in query["scope"]


def test_missing_scope_and_unknown_flow_fail_closed() -> None:
    emitter = NullMonitoringEmitter()
    issuer = StateIssuer(token_factory=_factory("s" * 43))
    missing = assemble_authorization_request(
        flow=FlowMode.STANDARD,
        client_id="client-1",
        redirect_uri="https://app.example/cb",
        scope="",
        issuer=issuer,
        issued_at=ISSUED,
        expires_at=EXPIRES,
        emitter=emitter,
    )
    assert missing.decision.code is OutcomeCode.REJECTED
    assert missing.decision.reason == "MISSING_INPUT"
    assert missing.url is None
    assert emitter.conditions[-1].code is MonitoringConditionCode.AUTH_CONFIGURATION_FAILURE
    unknown = assemble_authorization_request(
        flow="PUBLIC",
        client_id="client-1",
        redirect_uri="https://app.example/cb",
        scope="openid",
        issuer=issuer,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    assert unknown.decision.reason == "UNKNOWN_FLOW"
    assert unknown.decision.safe_to_retry is False


def test_pkce_authorization_puts_s256_challenge_not_the_verifier_in_the_query() -> None:
    issuer = StateIssuer(token_factory=_factory("s" * 43))
    assembly = assemble_authorization_request(
        flow=FlowMode.PKCE,
        client_id="client-1",
        redirect_uri="https://app.example/cb",
        scope="openid",
        issuer=issuer,
        issued_at=ISSUED,
        expires_at=EXPIRES,
        prompt="login",
        code_verifier=VERIFIER,
    )
    assert assembly.url is not None
    query = dict(parse_qsl(urlsplit(assembly.url).query))
    assert query["code_challenge"] == CHALLENGE
    assert query["code_challenge_method"] == "S256"
    assert query["prompt"] == "login"
    assert query["audience"] == DOCUMENTED_AUDIENCE
    assert "code_verifier" not in query
    assert VERIFIER not in assembly.url


def test_unknown_prompt_is_not_a_retryable_failure() -> None:
    issuer = StateIssuer(token_factory=_factory("s" * 43))
    assembly = assemble_authorization_request(
        flow=FlowMode.STANDARD,
        client_id="client-1",
        redirect_uri="https://app.example/cb",
        scope="openid",
        issuer=issuer,
        issued_at=ISSUED,
        expires_at=EXPIRES,
        prompt="none",
    )
    assert assembly.decision.code is OutcomeCode.UNKNOWN
    assert assembly.decision.reason == "UNKNOWN_PROMPT"
    assert assembly.decision.safe_to_retry is False
    assert "FAILED" not in assembly.decision.code


def test_callback_matches_state_and_does_not_keep_the_code() -> None:
    issuer = StateIssuer(token_factory=_factory("s" * 43))
    assembly = assemble_authorization_request(
        flow=FlowMode.STANDARD,
        client_id="client-1",
        redirect_uri="https://app.example/cb",
        scope="openid",
        issuer=issuer,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    assert assembly.url is not None
    state = dict(parse_qsl(urlsplit(assembly.url).query))["state"]
    raw = f"https://app.example/cb?code=variable-length-code&state={state}"
    classified = classify_callback(issuer, raw, now=NOW, allowed_callbacks=(REDIRECT,))
    assert classified.decision.reason == "AUTHORIZATION_CODE"
    assert classified.code_present is True
    assert "variable-length-code" not in repr(classified)
    replay = classify_callback(issuer, raw, now=NOW, allowed_callbacks=(REDIRECT,))
    assert replay.decision.reason == "STATE_REPLAY"
    assert replay.decision.safe_to_retry is False


def test_callback_access_denied_and_unknown_error() -> None:
    issuer = StateIssuer(token_factory=_factory("a" * 43))
    first = assemble_authorization_request(
        flow=FlowMode.STANDARD,
        client_id="client-1",
        redirect_uri="https://app.example/cb",
        scope="openid",
        issuer=issuer,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    assert first.url is not None
    state = dict(parse_qsl(urlsplit(first.url).query))["state"]
    denied = classify_callback(
        issuer,
        f"https://app.example/cb?error=access_denied&error_description=no&state={state}",
        now=NOW,
        allowed_callbacks=(REDIRECT,),
    )
    assert denied.decision.reason == "ACCESS_DENIED"
    assert denied.code_present is False
    assert "no" not in repr(denied)
    issuer = StateIssuer(token_factory=_factory("b" * 43))
    second = assemble_authorization_request(
        flow=FlowMode.STANDARD,
        client_id="client-1",
        redirect_uri="https://app.example/cb",
        scope="openid",
        issuer=issuer,
        issued_at=ISSUED,
        expires_at=EXPIRES,
    )
    assert second.url is not None
    other = dict(parse_qsl(urlsplit(second.url).query))["state"]
    unknown = classify_callback(
        issuer,
        f"https://app.example/cb?error=server_error&state={other}",
        now=NOW,
        allowed_callbacks=(REDIRECT,),
    )
    assert unknown.decision.code is OutcomeCode.UNKNOWN
    assert unknown.decision.safe_to_retry is False
    mismatch = classify_callback(
        StateIssuer(token_factory=_factory("c" * 43)),
        "https://app.example/cb?code=abc&state=not-the-issued-state-value",
        now=NOW,
        allowed_callbacks=(REDIRECT,),
    )
    assert mismatch.decision.reason == "STATE_MISMATCH"


def test_missing_state_fails_closed() -> None:
    issuer = StateIssuer(token_factory=_factory("s" * 43))
    classified = classify_callback(
        issuer,
        "https://app.example/cb?code=abc",
        now=NOW,
        allowed_callbacks=(REDIRECT,),
    )
    assert classified.decision.reason == "MISSING_STATE"
    assert classified.decision.safe_to_retry is False
    assert classified.code_present is False


def test_live_callback_host_is_rejected_without_connecting() -> None:
    emitter = NullMonitoringEmitter()
    issuer = StateIssuer(token_factory=_factory("s" * 43))
    classified = classify_callback(
        issuer,
        "https://api.tradestation.com/v3?code=abc&state=s",
        now=NOW,
        allowed_callbacks=(REDIRECT,),
        emitter=emitter,
    )
    assert classified.decision.reason == "LIVE_HOST_PROHIBITED"
    assert classified.code_present is False
    assert emitter.conditions[-1].code is MonitoringConditionCode.FORBIDDEN_HOST
    assert "abc" not in str(classified.decision)


def test_exchange_forms_follow_the_documented_parameter_split() -> None:
    standard = authorization_code_form(
        flow=FlowMode.STANDARD,
        client_id="client-1",
        redirect_uri="https://app.example/cb",
        code="variable-code",
        client_secret="supersecret",
    )
    assert standard.connect_allowed is False
    assert standard.method == "POST"
    assert standard.url == "https://signin.tradestation.com/oauth/token"
    assert standard.content_type == "application/x-www-form-urlencoded"
    assert standard.parameter_names == (
        "grant_type",
        "client_id",
        "client_secret",
        "code",
        "redirect_uri",
    )
    assert "supersecret" not in repr(standard)
    assert "code_verifier" not in standard.parameter_names
    pkce = authorization_code_form(
        flow=FlowMode.PKCE,
        client_id="client-1",
        redirect_uri="https://app.example/cb",
        code="variable-code",
        code_verifier=VERIFIER,
    )
    assert pkce.parameter_names == (
        "grant_type",
        "client_id",
        "code",
        "redirect_uri",
        "code_verifier",
    )
    assert "client_secret" not in pkce.parameter_names
    assert pkce.connect_allowed is False


def test_refresh_form_names_do_not_choose_an_interval() -> None:
    standard = refresh_form(
        flow=FlowMode.STANDARD,
        client_id="client-1",
        refresh_token="refresh-token-value",
        client_secret="supersecret",
    )
    pkce = refresh_form(
        flow=FlowMode.PKCE,
        client_id="client-1",
        refresh_token="refresh-token-value",
    )
    assert standard.parameter_names == (
        "grant_type",
        "client_id",
        "client_secret",
        "refresh_token",
    )
    assert pkce.parameter_names == ("grant_type", "client_id", "refresh_token")
    assert "expires_in" not in standard.parameter_names
    assert "30" not in standard.parameter_names
    assert "40" not in pkce.parameter_names
    assert standard.connect_allowed is False
    assert "refresh-token-value" not in repr(standard)
    mixed = refresh_form(
        flow=FlowMode.PKCE,
        client_id="client-1",
        refresh_token="refresh-token-value",
        client_secret="supersecret",
    )
    assert mixed.decision.reason == "CLIENT_SECRET_NOT_IN_PKCE"
    assert mixed.body == ""


def test_token_fixture_keeps_expires_in_and_drops_secret_values() -> None:
    fixture = read_token_fixture(
        {
            "access_token": "access-value",
            "refresh_token": "refresh-value",
            "id_token": "id-value",
            "token_type": "Bearer",
            "scope": "openid offline_access",
            "expires_in": 900,
        }
    )
    assert fixture.decision.code is OutcomeCode.CLASSIFIED
    assert fixture.expires_in == 900
    assert fixture.token_type == "Bearer"
    assert fixture.scope == "openid offline_access"
    assert fixture.access_present is True
    assert "access-value" not in repr(fixture)
    missing = read_token_fixture(
        {"access_token": "access-value", "token_type": "Bearer", "scope": "openid"}
    )
    assert missing.decision.reason == "MISSING_INPUT"
    assert missing.expires_in is None
    extra = read_token_fixture(
        {
            "access_token": "access-value",
            "token_type": "Bearer",
            "expires_in": 1200,
            "account": "123",
        }
    )
    assert extra.decision.code is OutcomeCode.UNKNOWN
    assert extra.decision.safe_to_retry is False
