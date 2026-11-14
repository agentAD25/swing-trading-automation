"""Signed-grant attacks. No production anchor is installed."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime

import pytest

from swingtrade.alpaca_paper_account_runtime import (
    AccountRuntimeError,
    ScriptedCredentials,
    ScriptedTransport,
    observe_scripted,
    read_paper_account,
)
from swingtrade.alpaca_paper_grant import (
    PRODUCTION_PUBLIC_MODULUS,
    GrantError,
    VerifiedGrant,
    authorize_production,
    canonical_grant,
    load_verified_bundle,
    verify_signed_grant,
)
from swingtrade.alpaca_paper_request_budget import BoundLedger
from tests.unit.test_alpaca_paper_support import (
    ACCOUNT,
    EXPONENT,
    GRANT_ID,
    LEDGER,
    MODULUS,
    SID,
    WHEN,
    fields,
    issue,
    revocation,
    sign,
)


def test_production_anchor_rejects_every_caller_argument() -> None:
    assert PRODUCTION_PUBLIC_MODULUS is None
    assert inspect.signature(authorize_production).parameters == {}
    assert inspect.signature(read_paper_account).parameters == {}
    with pytest.raises(GrantError) as caught:
        authorize_production()
    assert caught.value.reason == "GRANT_ANCHOR_ABSENT"
    issue()
    with pytest.raises(AccountRuntimeError) as runtime:
        read_paper_account()
    assert runtime.value.reason == "GRANT_ANCHOR_ABSENT"


def test_boolean_and_unissued_objects_are_rejected(tmp_path) -> None:  # type: ignore[no-untyped-def]
    class Declared:
        effective = True
        attended = True
        name = "LANE1_ALPACA_STANDING_PAPER_ACCOUNT_READ_AUTHORIZED"

    ledger = BoundLedger(tmp_path / LEDGER)
    with pytest.raises(AccountRuntimeError) as caught:
        observe_scripted(
            Declared(),  # type: ignore[arg-type]
            ScriptedCredentials(b"synthetic-paper-key", b"synthetic-paper-secret"),
            ScriptedTransport((200, b"{}")),
            ledger,
            WHEN,
        )
    assert caught.value.reason == "GRANT_UNVERIFIED"
    with pytest.raises(GrantError) as forged:
        VerifiedGrant({}, object())  # type: ignore[arg-type]
    assert forged.value.reason == "GRANT_UNVERIFIED"


def test_signature_expiry_revocation_and_identity_fail_closed() -> None:
    payload = canonical_grant(fields())
    statement = revocation()
    signature = bytearray(sign(payload))
    signature[-1] ^= 0x01
    _deny(
        lambda: verify_signed_grant(
            payload,
            bytes(signature),
            MODULUS,
            EXPONENT,
            observed_sid=SID,
            now=WHEN,
            revocation_payload=statement,
            revocation_signature=sign(statement),
        ),
        "GRANT_SIGNATURE_INVALID",
    )
    _deny(
        lambda: verify_signed_grant(
            payload,
            sign(payload),
            MODULUS ^ 1,
            EXPONENT,
            observed_sid=SID,
            now=WHEN,
            revocation_payload=statement,
            revocation_signature=sign(statement),
        ),
        "GRANT_SIGNATURE_INVALID",
    )
    _deny(lambda: issue(now=datetime(2025, 12, 31, tzinfo=UTC)), "GRANT_NOT_ACTIVE")
    _deny(lambda: issue(now=datetime(2027, 1, 1, tzinfo=UTC)), "GRANT_EXPIRED")
    _deny(lambda: issue(now=datetime(2026, 11, 14, 15, 0)), "GRANT_CLOCK_DENIED")
    _deny(lambda: issue(revoked=[GRANT_ID]), "GRANT_REVOKED")
    _deny(lambda: issue(generation=2), "GRANT_REVOCATION_MISMATCH")
    _deny(lambda: issue(sid="S-1-5-18"), "IDENTITY_MISMATCH")
    _deny(lambda: issue(capability="DECLARED_ONLY"), "GRANT_TERMS_REJECTED")
    _deny(lambda: issue(daily_ceiling=31), "GRANT_TERMS_REJECTED")
    _deny(lambda: issue(method="POST"), "GRANT_TERMS_REJECTED")
    _deny(
        lambda: issue(endpoint="https://api.alpaca.markets/v2/account"),
        "GRANT_TERMS_REJECTED",
    )
    _deny(
        lambda: issue(credential_targets=["swing-trading/lane2/alpaca/live/secret"]),
        "GRANT_TERMS_REJECTED",
    )


def test_duplicate_and_unsigned_payloads_are_rejected() -> None:
    payload = canonical_grant(fields())
    duplicate = payload.replace(b'"grant_id"', b'"grant_id":"other","grant_id"', 1)
    statement = revocation()
    _deny(
        lambda: verify_signed_grant(
            duplicate,
            sign(duplicate),
            MODULUS,
            EXPONENT,
            observed_sid=SID,
            now=WHEN,
            revocation_payload=statement,
            revocation_signature=sign(statement),
        ),
        "DUPLICATE_FIELD",
    )
    _deny(
        lambda: load_verified_bundle(b"{}", b"{}", MODULUS, EXPONENT, observed_sid=SID, now=WHEN),
        "GRANT_BUNDLE_MALFORMED",
    )


def test_bundle_round_trip_uses_the_signed_bytes() -> None:
    payload = canonical_grant(fields())
    statement = revocation()
    grant_blob = b"SWTG1\n" + sign(payload).hex().encode("ascii") + b"\n" + payload
    revocation_blob = b"SWTG1\n" + sign(statement).hex().encode("ascii") + b"\n" + statement
    grant = load_verified_bundle(
        grant_blob,
        revocation_blob,
        MODULUS,
        EXPONENT,
        observed_sid=SID,
        now=WHEN,
    )
    assert grant.account_id == ACCOUNT
    assert grant.daily_ceiling == 30
    assert repr(grant) == "VerifiedGrant()"
    assert ACCOUNT not in repr(grant)


def _deny(operation: object, reason: str) -> None:
    with pytest.raises(GrantError) as caught:
        operation()  # type: ignore[operator]
    assert caught.value.reason == reason
    assert str(caught.value) == reason
