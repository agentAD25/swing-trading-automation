from __future__ import annotations

import socket
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from swingtrade.domain import ExecutionMode
from swingtrade.group3_auth.boundary import (
    ExecutionPosture,
    boot_dry_run,
    evaluate_destination,
    evaluate_environment,
)
from swingtrade.group3_auth.brokerage_read import ReadKind, parse_brokerage_fixture
from swingtrade.group3_auth.outcomes import OutcomeCode
from swingtrade.group3_auth.scopes import (
    validate_granted_scopes,
    validate_requested_scopes,
)
from swingtrade.group3_auth.session import (
    ACCESS_TOKEN_MAX_SECONDS,
    SessionError,
    SingleFlight,
    activate_unattended_profile,
    open_attended_session,
    read_store_metadata,
    restore_after_restart,
)
from swingtrade.group3_auth.throttle import LoginThrottle, ThrottleBook, retry_permitted
from swingtrade.offline.hosts import SIM_API_URL

ISSUED = datetime(2026, 10, 8, 16, 0, tzinfo=UTC)
_EVIDENCE = Path("docs/P2_TS_PROVIDER_EVIDENCE_2026-10-08.md")
_ACCOUNT = "SYN_FIXTURE_ONE"
_OTHER = "SYN_FIXTURE_TWO"


def test_provider_evidence_file_keeps_claim_labels() -> None:
    text = _EVIDENCE.read_text(encoding="utf-8")
    for item, label in (
        ("TS-EVIDENCE-001", "PARTIALLY_CONFIRMED"),
        ("TS-EVIDENCE-002", "CONFIRMED"),
        ("TS-EVIDENCE-003", "PARTIALLY_CONFIRMED"),
        ("TS-EVIDENCE-004", "CONFIRMED"),
        ("TS-EVIDENCE-005", "CONFIRMED"),
        ("TS-EVIDENCE-006", "PARTIALLY_CONFIRMED"),
        ("TS-EVIDENCE-007", "CONFIRMED"),
        ("TS-EVIDENCE-008", "CONFIRMED"),
    ):
        section = text.split(item, 1)[1].split("###", 1)[0]
        assert label in section
    assert "ADR-0005" in text
    assert "Proposed" in text
    assert "DEP-TS-001" in text
    assert "NOT_CLOSED_BY_PROVIDER" in text
    assert "PROFILE_B_NOT_AUTHORIZED" in text


def test_dry_run_boot_fails_closed_on_missing_or_ambiguous_identity() -> None:
    context = boot_dry_run(ExecutionPosture.DRY_RUN)
    assert context.network_allowed is False
    assert context.sim_connect_allowed is False
    assert context.live_enabled is False
    assert boot_dry_run("DRY_RUN").posture is ExecutionPosture.DRY_RUN
    for value in (None, "", "SIM", "LIVE", "DRY_RUN,SIM", "dry_run", ExecutionMode.DRY_RUN):
        with pytest.raises(Exception, match="POSTURE|MISSING") as captured:
            boot_dry_run(value)
        assert "api.tradestation.com" not in str(captured.value)


@pytest.mark.parametrize(
    "candidate",
    [
        "https://api.tradestation.com/v3",
        "https://api.tradestation.com/v3/brokerage/accounts",
        "https://user:secret@api.tradestation.com/v3",
        "https://api.tradestation.com:443/v3",
        "https://api.tradestation.com.evil.example/v3",
        "https://sim-api.tradestation.com/v3/orderexecution/orders",
        SIM_API_URL,
    ],
)
def test_live_redirect_and_sim_naming_cannot_connect(candidate: str, monkeypatch) -> None:
    def explode(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket")

    monkeypatch.setattr(socket, "socket", explode)
    monkeypatch.setattr(socket, "create_connection", explode)
    verdict = evaluate_destination(ExecutionPosture.DRY_RUN, candidate, method="GET")
    assert verdict.connect_allowed is False
    assert verdict.network_permitted is False
    assert verdict.order_placement_permitted is False
    assert verdict.decision.safe_to_retry is False
    if candidate == SIM_API_URL:
        assert verdict.decision.reason == "SIM_CONNECT_DENIED"
    elif "orderexecution" in candidate:
        assert verdict.decision.reason == "ORDER_PLACEMENT_DENIED"
    elif "evil.example" in candidate:
        assert verdict.decision.reason == "UNKNOWN_DESTINATION"
    else:
        assert verdict.decision.reason == "LIVE_HOST_PROHIBITED"
    assert "secret" not in repr(verdict)


def test_overrides_and_redirects_cannot_select_a_host() -> None:
    live = evaluate_destination(
        ExecutionPosture.DRY_RUN,
        SIM_API_URL,
        redirect_to="https://api.tradestation.com/v3",
    )
    assert live.decision.reason == "LIVE_HOST_PROHIBITED"
    override = evaluate_destination(
        ExecutionPosture.DRY_RUN,
        SIM_API_URL,
        configured_host=SIM_API_URL,
    )
    assert override.decision.reason == "HOST_OVERRIDE_DENIED"
    header = evaluate_destination(
        ExecutionPosture.DRY_RUN,
        SIM_API_URL,
        header_host="sim-api.tradestation.com",
    )
    assert header.decision.reason == "HOST_OVERRIDE_DENIED"
    environ = evaluate_environment(
        ExecutionPosture.DRY_RUN,
        SIM_API_URL,
        {"TRADESTATION_API_URL": "https://api.tradestation.com/v3"},
    )
    assert environ.decision.reason == "LIVE_HOST_PROHIBITED"
    assert (
        evaluate_destination(
            ExecutionPosture.DRY_RUN,
            "https://signin.tradestation.com/oauth/token",
            method="POST",
        ).decision.reason
        == "AUTH_ENDPOINT_CONNECT_DENIED"
    )
    again = evaluate_destination(ExecutionPosture.DRY_RUN, SIM_API_URL)
    repeated = evaluate_destination(ExecutionPosture.DRY_RUN, SIM_API_URL)
    assert again.decision.reason == repeated.decision.reason


def test_scope_contract_fails_closed_on_elevated_grants() -> None:
    requested = validate_requested_scopes("openid ReadAccount")
    assert requested.decision.reason == "REQUESTED_SCOPE_ACCEPTED"
    assert validate_requested_scopes("openid ReadAccount Trade").decision.reason == (
        "REQUESTED_SCOPE_REJECTED"
    )
    assert validate_requested_scopes("openid ReadAccount offline_access").decision.reason == (
        "REQUESTED_SCOPE_REJECTED"
    )
    granted = validate_granted_scopes({"openid", "ReadAccount"})
    assert granted.decision.code is OutcomeCode.CLASSIFIED
    for scopes, reason in (
        ("ReadAccount", "MISSING_READ_SCOPE"),
        ("openid ReadAccount Trade", "UNEXPECTED_SCOPE_GRANTED"),
        ("openid ReadAccount MarketData", "UNEXPECTED_SCOPE_GRANTED"),
        ("openid ReadAccount Matrix", "UNEXPECTED_SCOPE_GRANTED"),
        ("openid ReadAccount OptionSpreads", "UNEXPECTED_SCOPE_GRANTED"),
        ("openid ReadAccount offline_access", "UNEXPECTED_SCOPE_GRANTED"),
        ("openid ReadAccount profile", "UNEXPECTED_SCOPE_GRANTED"),
    ):
        verdict = validate_granted_scopes(scopes)
        assert verdict.decision.reason == reason
        assert verdict.connect_allowed is False


def test_attended_session_uses_twelve_hundred_seconds_and_redacts_the_marker() -> None:
    marker = "fixture-token-not-real"
    session = open_attended_session(
        issued_at=ISSUED,
        expires_in=ACCESS_TOKEN_MAX_SECONDS,
        granted_scopes="openid ReadAccount",
        refresh_present=False,
        marker=marker,
    )
    assert marker not in repr(session)
    assert session.before_call(ISSUED + timedelta(seconds=1199)).reason == "CALL_ALLOWED"
    fresh = open_attended_session(
        issued_at=ISSUED,
        expires_in=1200,
        granted_scopes="openid ReadAccount",
        refresh_present=False,
        marker=marker,
    )
    assert fresh.before_call(ISSUED + timedelta(seconds=1200)).reason == "REAUTHORIZATION_REQUIRED"
    during = open_attended_session(
        issued_at=ISSUED,
        expires_in=1200,
        granted_scopes="openid ReadAccount",
        refresh_present=False,
        marker=marker,
    )
    assert during.before_call(ISSUED).reason == "CALL_ALLOWED"
    assert during.finish_call(ISSUED + timedelta(seconds=1200)).reason == "EXPIRED_DURING_REQUEST"
    skewed = open_attended_session(
        issued_at=ISSUED,
        expires_in=1200,
        granted_scopes="openid ReadAccount",
        refresh_present=False,
        marker=marker,
        skew_seconds=5,
    )
    assert skewed.before_call(ISSUED + timedelta(seconds=1195)).reason == "REAUTHORIZATION_REQUIRED"
    with pytest.raises(SessionError, match="EXPIRES_IN_REJECTED"):
        open_attended_session(
            issued_at=ISSUED,
            expires_in=1199,
            granted_scopes="openid ReadAccount",
            refresh_present=False,
            marker=marker,
        )
    with pytest.raises(SessionError, match="UNEXPECTED_REFRESH_TOKEN"):
        open_attended_session(
            issued_at=ISSUED,
            expires_in=1200,
            granted_scopes="openid ReadAccount",
            refresh_present=True,
            marker=marker,
        )
    with pytest.raises(SessionError, match="CLOCK_SKEW_REJECTED"):
        open_attended_session(
            issued_at=ISSUED,
            expires_in=1200,
            granted_scopes="openid ReadAccount",
            refresh_present=False,
            marker=marker,
            skew_seconds=-1,
        )
    with pytest.raises(SessionError, match="PROFILE_B_NOT_AUTHORIZED"):
        activate_unattended_profile()
    failed = open_attended_session(
        issued_at=ISSUED,
        expires_in=1200,
        granted_scopes="openid ReadAccount",
        refresh_present=False,
        marker=marker,
    )
    assert failed.note_provider_failure().reason == "AUTHORIZATION_DENIED"
    timed = open_attended_session(
        issued_at=ISSUED,
        expires_in=1200,
        granted_scopes="openid ReadAccount",
        refresh_present=False,
        marker=marker,
    )
    assert timed.note_timeout().reason == "NETWORK_TIMEOUT"
    metadata = {"version": 1, "profile": "ATTENDED_READ_ONLY", "redacted": True}
    assert read_store_metadata(metadata).reason == "METADATA_ACCEPTED"
    assert restore_after_restart(metadata).reason == "REAUTHORIZATION_REQUIRED"
    with pytest.raises(SessionError, match="SECRET_METADATA_REJECTED"):
        read_store_metadata({**metadata, "refresh_token": marker})
    with pytest.raises(SessionError, match="CORRUPTED_METADATA"):
        read_store_metadata({"version": 1})
    gate = SingleFlight()
    calls = {"n": 0}

    def once() -> None:
        calls["n"] += 1

    assert gate.refresh_once(once).reason == "REFRESH_EXECUTED_ONCE"
    assert gate.refresh_once(once).reason == "REFRESH_ALREADY_STARTED"
    assert calls["n"] == 1


def test_brokerage_fixtures_cover_empty_partial_and_failure_statuses() -> None:
    accounts = parse_brokerage_fixture(
        ReadKind.ACCOUNTS,
        {"Accounts": [{"AccountID": _ACCOUNT, "Status": "Active", "AccountType": "Cash"}]},
        status=200,
    )
    assert accounts.decision.reason == "READ_FIXTURE"
    assert _ACCOUNT not in repr(accounts)
    assert accounts.connect_allowed is False
    empty = parse_brokerage_fixture(ReadKind.POSITIONS, {"Positions": []}, status=200)
    assert empty.decision.reason == "EMPTY_COLLECTION"
    multiple = parse_brokerage_fixture(
        ReadKind.BALANCES,
        {
            "Balances": [
                {"AccountID": _ACCOUNT, "CashBalance": "1.00"},
                {"AccountID": _OTHER, "CashBalance": "2.00"},
            ]
        },
        status=200,
    )
    assert multiple.decision.reason == "MULTIPLE_RECORDS"
    assert multiple.record_count == 2
    partial = parse_brokerage_fixture(
        ReadKind.ORDERS,
        {
            "Orders": [{"AccountID": _ACCOUNT, "OrderID": "ORD_1", "Status": "OPN"}],
            "Errors": [{"AccountID": _OTHER, "Error": "Error", "Message": "partial"}],
        },
        status=200,
    )
    assert partial.decision.code is OutcomeCode.UNKNOWN
    assert partial.decision.reason == "PARTIAL_RESPONSE"
    assert partial.decision.safe_to_retry is False
    conflict = parse_brokerage_fixture(
        ReadKind.ACCOUNTS,
        {
            "Accounts": [
                {"AccountID": _ACCOUNT, "Status": "Active"},
                {"AccountID": _ACCOUNT, "Status": "Closed"},
            ]
        },
        status=200,
    )
    assert conflict.decision.reason == "CONFLICTING_RESPONSE"
    hidden = "ACCT-SHOULD-NOT-ECHO"
    undocumented = parse_brokerage_fixture(
        ReadKind.ACCOUNTS,
        {"Accounts": [{"AccountID": _ACCOUNT, "AccountNumber": hidden}]},
        status=200,
    )
    assert undocumented.decision.reason == "UNDOCUMENTED_FIELD"
    assert hidden not in repr(undocumented)
    statuses = (
        (400, "HTTP_400"),
        (401, "HTTP_401"),
        (403, "HTTP_403"),
        (404, "HTTP_404"),
        (429, "HTTP_429"),
        (503, "HTTP_5XX"),
        (504, "HTTP_5XX"),
    )
    for status, reason in statuses:
        observed = parse_brokerage_fixture(ReadKind.ACCOUNTS, {"Accounts": []}, status=status)
        assert observed.decision.reason == reason
    timeout = parse_brokerage_fixture(ReadKind.ACCOUNTS, {"Accounts": []}, status=200, timeout=True)
    assert timeout.decision.reason == "NETWORK_TIMEOUT"
    assert (
        parse_brokerage_fixture(
            ReadKind.ORDERS,
            {"Orders": [{"AccountID": _ACCOUNT, "OrderID": "ORD_1", "Status": "OPN"}]},
            status=200,
        ).decision.reason
        == "READ_FIXTURE"
    )


def test_throttle_stops_per_login_without_retry() -> None:
    book = ThrottleBook()
    first = book.login("LOGIN_ONE")
    second = book.login("LOGIN_TWO")
    stopped = first.observe(
        status=429,
        headers={"Retry-After": "2", "X-RateLimit-Remaining": "0"},
    )
    assert stopped.action == "STOP"
    assert stopped.retry_after_seconds == 2
    assert retry_permitted(stopped) is False
    assert first.allow().action == "STOP"
    assert second.observe(status=200, headers=None).action == "CONTINUE"
    malformed = LoginThrottle("LOGIN_THREE").observe(
        status=200,
        headers={"X-RateLimit-Reset": "soon"},
    )
    assert malformed.action == "STOP"
    with pytest.raises(Exception, match="MALFORMED_LOGIN_LABEL"):
        LoginThrottle("user@example")
