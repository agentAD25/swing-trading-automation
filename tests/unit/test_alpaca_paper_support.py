"""Synthetic grant signer. This key is not a production trust anchor."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from swingtrade.alpaca_paper_account_read import ACCOUNT_URL
from swingtrade.alpaca_paper_custody import PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET
from swingtrade.alpaca_paper_grant import (
    GRANT_NAME,
    VerifiedGrant,
    canonical_grant,
    verify_signed_grant,
)
from swingtrade.alpaca_paper_request_budget import BoundLedger, BudgetError, expected_genesis

MODULUS = int(
    "1973921074319571210232494132924656887863620785148911773358733566288630"
    "4980983159797757781069739378646489789208789129092386890036703781035655"
    "9104061327185287351980769303936708270356115542445891466348516778068428"
    "3440631942061704373134327688878513513086544190602899291441160425177766"
    "7258011094448666376368916347950626943085770483475782543681394327333150"
    "8711187963878558430745200588796871369311997561095931641378069450589946"
    "7202781261738568917354830293879253402245802820853474185900489348104387"
    "0610012474599690795945240690957457170224784197054975959997424263186699"
    "398364040698961471277774444632054234858124626088438065639"
)
PRIVATE = int(
    "1629176874605488904476644340510362325425806977577395772353743035752602"
    "5340286557160390560078173745065646568931940930798423779986501430031885"
    "2533649407949393139081614849920510353721297065877911947545014587828239"
    "8882878715505129182709140165389439163165299934600323871604495301254109"
    "5864215299904219188613623665437778243584044740054333230654554028889831"
    "7756468331416600426704142066950074909358685462012865929745290936924499"
    "1942092124229214288769598649826771125044387836382545890960969533800242"
    "9881616817595421763096284398026971848193833303238187373031587680333124"
    "522878933597023818521529902618523556773464862302594842505"
)
EXPONENT = 65537
SID = "S-1-5-21-100-200-300-400"
ACCOUNT = "synthetic-account"
LEDGER = "ledger0001"
GRANT_ID = "grant0001"
ACTIVATED = "2026-01-01T00:00:00Z"
EXPIRES = "2027-01-01T00:00:00Z"
WHEN = datetime(2026, 11, 14, 15, 0, tzinfo=UTC)
_INFO = bytes.fromhex("3031300d060960864801650304020105000420")


def sign(message: bytes) -> bytes:
    """PKCS#1 v1.5 SHA-256 signature for the synthetic test key."""
    size = (MODULUS.bit_length() + 7) // 8
    tail = _INFO + hashlib.sha256(message).digest()
    encoded = b"\x00\x01" + b"\xff" * (size - len(tail) - 3) + b"\x00" + tail
    return pow(int.from_bytes(encoded, "big"), PRIVATE, MODULUS).to_bytes(size, "big")


def fields(**overrides: object) -> dict[str, object]:
    """Canonical grant fields. Genesis follows the account and ledger unless overridden."""
    grant_id = str(overrides.get("grant_id", GRANT_ID))
    account_id = str(overrides.get("account_id", ACCOUNT))
    ledger_id = str(overrides.get("ledger_id", LEDGER))
    body: dict[str, object] = {
        "account_id": account_id,
        "activated_at": ACTIVATED,
        "capability": GRANT_NAME,
        "credential_targets": [PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET],
        "daily_ceiling": 30,
        "endpoint": ACCOUNT_URL,
        "expires_at": EXPIRES,
        "grant_id": grant_id,
        "ledger_genesis": expected_genesis(grant_id, account_id, ledger_id),
        "ledger_id": ledger_id,
        "method": "GET",
        "provenance": "synthetic-test-issuance",
        "revocation_generation": 1,
        "windows_sid": SID,
    }
    body.update(overrides)
    if "ledger_genesis" not in overrides:
        body["ledger_genesis"] = expected_genesis(
            str(body["grant_id"]),
            str(body["account_id"]),
            str(body["ledger_id"]),
        )
    return body


def revocation(generation: int = 1, revoked: list[str] | None = None) -> bytes:
    body = {"generation": generation, "revoked_grant_ids": [] if revoked is None else revoked}
    return json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")


def issue(
    now: datetime = WHEN,
    sid: str = SID,
    revoked: list[str] | None = None,
    generation: int = 1,
    **overrides: object,
) -> VerifiedGrant:
    """Verify a synthetic grant. This does not install a production anchor."""
    payload = canonical_grant(fields(**overrides))
    statement = revocation(generation, revoked)
    return verify_signed_grant(
        payload,
        sign(payload),
        MODULUS,
        EXPONENT,
        observed_sid=sid,
        now=now,
        revocation_payload=statement,
        revocation_signature=sign(statement),
    )


def prepare(directory: Path, **overrides: object) -> tuple[VerifiedGrant, BoundLedger]:
    """Initialize one disposable ledger for the synthetic grant."""
    grant = issue(**overrides)
    ledger = BoundLedger(directory)
    ledger.initialize(grant, WHEN)
    return grant, ledger


def child_reserve(directory: str) -> None:
    """One child process. It prints the number of accepted reservations."""
    ledger = BoundLedger(Path(directory))
    grant = issue()
    accepted = 0
    for _ in range(20):
        try:
            ledger.reserve(grant, WHEN)
        except BudgetError as error:
            if error.reason != "BUDGET_EXHAUSTED":
                raise
        else:
            accepted += 1
    print(accepted)
