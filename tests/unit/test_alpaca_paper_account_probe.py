"""Negative checks for the offline Alpaca paper account probe."""

from __future__ import annotations

import ast
import hashlib
import inspect
import os
from pathlib import Path

import pytest

from swingtrade.alpaca_paper_account_probe import (
    ACCOUNT_URL,
    ProbeClassification,
    ProbeDecision,
    ProbeError,
    ProbeSession,
    RuntimeAuthorization,
    ScriptedOutcome,
    SyntheticCustody,
    SyntheticTransport,
    read_account,
)
from swingtrade.alpaca_paper_boundary import (
    LIVE_HOST,
    PAPER_HOST,
    evaluate_paper_boundary,
)
from swingtrade.alpaca_paper_custody import PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET

_KEY_ID = b"synthetic-paper-key-id"
_SECRET = b"synthetic-paper-secret"
_MODULE = Path(__file__).parents[2] / "src" / "swingtrade" / "alpaca_paper_account_probe.py"
_BOUNDARY = Path(__file__).parents[2] / "src" / "swingtrade" / "alpaca_paper_boundary.py"
_BOUNDARY_TESTS = Path(__file__).parents[2] / "tests" / "unit" / "test_alpaca_paper_boundary.py"
_CUSTODY = Path(__file__).parents[2] / "src" / "swingtrade" / "alpaca_paper_custody.py"
_CUSTODY_TESTS = Path(__file__).parents[2] / "tests" / "unit" / "test_alpaca_paper_custody.py"
_SCAN_TOKENS = ("requests.", "httpx.", "socket.", "tradestation", "place_order", "cancel_order")
_FLAGS = (
    "connect_allowed",
    "network_permitted",
    "submit_permitted",
    "cancel_permitted",
    "replace_permitted",
    "resubmit_permitted",
    "safe_to_retry",
)
_BLOBS = {
    _BOUNDARY: "854e6adb5c1c2d20370f724d3a7e6d4f32970509",
    _BOUNDARY_TESTS: "8e5d89ac0a3f33463d518e62ccaefdadcdf2cdd1",
    _CUSTODY: "86ba61b5bfecc2ec203e36c099face0e15c4068d",
    _CUSTODY_TESTS: "81c0a9d5f1cbbd12d9fe8d9fb3bcf07423424a4c",
}


def _papers() -> dict[str, bytes]:
    return {PAPER_KEY_ID_TARGET: _KEY_ID, PAPER_SECRET_TARGET: _SECRET}


def _ready(
    entries: dict[str, bytes] | None = None,
    *,
    host: object = None,
    hosts: object = None,
    fault: object = None,
    outcome: ScriptedOutcome | None = None,
    runtime: object = None,
    method: object = "GET",
    url: object = ACCOUNT_URL,
) -> tuple[ProbeSession, SyntheticCustody, SyntheticTransport, object]:
    custody = SyntheticCustody(
        _papers() if entries is None else entries,
        host=host,
        hosts=hosts,
        fault=fault,
    )
    transport = SyntheticTransport(outcome or ScriptedOutcome(body={"status": "ACTIVE"}))
    selected = RuntimeAuthorization("Windows") if runtime is None else runtime
    return ProbeSession(), custody, transport, selected


def _observe(**kwargs: object) -> tuple[ProbeDecision, SyntheticTransport]:
    session, custody, transport, runtime = _ready(**kwargs)  # type: ignore[arg-type]
    method = kwargs.get("method", "GET")
    url = kwargs.get("url", ACCOUNT_URL)
    decision = read_account(session, custody, transport, runtime, method=method, url=url)
    return decision, transport


def _denied(operation: object, reason: str) -> ProbeError:
    with pytest.raises(ProbeError) as caught:
        operation()  # type: ignore[operator]
    assert caught.value.reason == reason
    assert str(caught.value) == reason
    assert caught.value.decision.classification is ProbeClassification.DENIED
    _flags_false(caught.value.decision)
    return caught.value


def _flags_false(decision: object) -> None:
    for name in _FLAGS:
        assert getattr(decision, name) is False


def _blob(path: Path) -> str:
    payload = path.read_bytes().replace(b"\r\n", b"\n")
    prefix = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(prefix + payload).hexdigest()


def test_scripted_paper_account_observation_keeps_flags_closed() -> None:
    decision, transport = _observe()
    assert decision.classification is ProbeClassification.ACCEPTED
    assert decision.reason == "ACCOUNT_OBSERVED"
    assert transport.calls == 1
    _flags_false(decision)
    boundary = evaluate_paper_boundary(ACCOUNT_URL, "GET")
    assert boundary.reason == "CLASSIFIED"
    _flags_false(boundary)


def test_missing_key_or_secret_is_rejected() -> None:
    secret_only = _ready(entries={PAPER_SECRET_TARGET: _SECRET})
    _denied(lambda: read_account(*secret_only), "MISSING_KEY_ID")
    assert secret_only[2].calls == 0
    key_only = _ready(entries={PAPER_KEY_ID_TARGET: _KEY_ID})
    _denied(lambda: read_account(*key_only), "MISSING_SECRET")
    assert key_only[2].calls == 0


def test_empty_or_malformed_material_is_rejected() -> None:
    empty = _ready(entries={PAPER_KEY_ID_TARGET: b"", PAPER_SECRET_TARGET: _SECRET})
    _denied(lambda: read_account(*empty), "INCOMPLETE_MATERIAL")
    malformed = _ready(entries={PAPER_KEY_ID_TARGET: _KEY_ID, PAPER_SECRET_TARGET: "synthetic"})  # type: ignore[dict-item]
    _denied(lambda: read_account(*malformed), "MALFORMED_MATERIAL")
    spaced = _ready(entries={PAPER_KEY_ID_TARGET: _KEY_ID, PAPER_SECRET_TARGET: b"has space"})
    _denied(lambda: read_account(*spaced), "MALFORMED_MATERIAL")


def test_ambiguous_or_inconsistent_custody_is_rejected() -> None:
    extra = _papers()
    extra["swing-trading/lane2/alpaca/paper/other"] = _KEY_ID
    ambiguous = _ready(entries=extra)
    _denied(lambda: read_account(*ambiguous), "AMBIGUOUS_CUSTODY")
    listed = _ready(entries={PAPER_KEY_ID_TARGET: [_KEY_ID], PAPER_SECRET_TARGET: _SECRET})  # type: ignore[dict-item]
    _denied(lambda: read_account(*listed), "AMBIGUOUS_CUSTODY")
    faulted = _ready(fault="ambiguous")
    _denied(lambda: read_account(*faulted), "AMBIGUOUS_CUSTODY")
    inconsistent = _ready(fault="inconsistent")
    _denied(lambda: read_account(*inconsistent), "INCONSISTENT_CUSTODY")
    split = _ready(hosts={PAPER_KEY_ID_TARGET: PAPER_HOST, PAPER_SECRET_TARGET: "other.example"})
    _denied(lambda: read_account(*split), "HOST_MISMATCH")


def test_live_targets_and_live_hosts_are_rejected() -> None:
    live_name = _ready(entries={"swing-trading/lane2/alpaca/live/key-id": _KEY_ID})
    _denied(lambda: read_account(*live_name), "LIVE_TARGET_DENIED")
    live_host = _ready(host=LIVE_HOST)
    _denied(lambda: read_account(*live_host), "LIVE_HOST_DENIED")
    live_target = f"https://{LIVE_HOST}/v2/account"
    live_url = _ready(url=live_target)
    _denied(lambda: read_account(*live_url, url=live_target), "LIVE_HOST_DENIED")
    other = _ready(url="https://example.test/v2/account")
    _denied(
        lambda: read_account(*other[:3], other[3], url="https://example.test/v2/account"),
        "HOST_DENIED",
    )
    assert other[2].calls == 0


def test_method_path_order_position_and_stream_are_rejected() -> None:
    posted = _ready(method="POST")
    _denied(lambda: read_account(*posted[:3], posted[3], method="POST"), "METHOD_DENIED")
    orders = _ready(url=f"https://{PAPER_HOST}/v2/orders")
    _denied(
        lambda: read_account(*orders[:3], orders[3], url=f"https://{PAPER_HOST}/v2/orders"),
        "ORDER_ROUTE_DENIED",
    )
    positions = _ready(url=f"https://{PAPER_HOST}/v2/positions")
    _denied(
        lambda: read_account(
            *positions[:3], positions[3], url=f"https://{PAPER_HOST}/v2/positions"
        ),
        "POSITION_ROUTE_DENIED",
    )
    stream = _ready(url=f"https://{PAPER_HOST}/v2/events/accounts")
    _denied(
        lambda: read_account(
            *stream[:3], stream[3], url=f"https://{PAPER_HOST}/v2/events/accounts"
        ),
        "STREAM_ROUTE_DENIED",
    )
    assert posted[2].calls == 0
    assert orders[2].calls == 0


def test_redirect_timeout_network_and_ambiguous_results_do_not_repeat() -> None:
    redirected = _ready(outcome=ScriptedOutcome(status=302, redirected=True))
    _denied(lambda: read_account(*redirected), "REDIRECT_DENIED")
    assert redirected[2].calls == 1
    _denied(lambda: read_account(*redirected), "MULTIPLE_GET_DENIED")
    assert redirected[2].calls == 1
    timed = _ready(outcome=ScriptedOutcome(fault="timeout"))
    _denied(lambda: read_account(*timed), "TIMEOUT")
    assert timed[2].calls == 1
    failed = _ready(outcome=ScriptedOutcome(fault="network"))
    _denied(lambda: read_account(*failed), "NETWORK_DENIED")
    assert failed[2].calls == 1
    ambiguous = _ready(outcome=ScriptedOutcome(status=None))
    _denied(lambda: read_account(*ambiguous), "AMBIGUOUS_RESPONSE")
    unexpected = _ready(outcome=ScriptedOutcome(status=500))
    _denied(lambda: read_account(*unexpected), "UNEXPECTED_STATUS")
    hidden = _ready(outcome=ScriptedOutcome(status=200, redirected=True, body=_SECRET))
    _denied(lambda: read_account(*hidden), "REDIRECT_DENIED")


def test_a_second_observation_is_rejected_without_another_exchange() -> None:
    session, custody, transport, runtime = _ready()
    first = read_account(session, custody, transport, runtime)
    assert first.reason == "ACCOUNT_OBSERVED"
    _denied(
        lambda: read_account(session, custody, transport, runtime),
        "MULTIPLE_GET_DENIED",
    )
    assert transport.calls == 1
    function = ast.parse(inspect.getsource(read_account)).body[0]
    assert isinstance(function, ast.FunctionDef)
    assert not any(isinstance(node, ast.While) for node in ast.walk(function))
    assert not any(isinstance(node, ast.For) for node in ast.walk(function))


def test_process_env_is_not_a_credential_source(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APCA_API_KEY_ID", "synthetic-from-process")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "synthetic-secret-from-process")
    missing = _ready(entries={})
    _denied(lambda: read_account(*missing), "MISSING_KEY_ID")
    fallback = _ready(fault="env-fallback")
    _denied(lambda: read_account(*fallback), "ENV_FALLBACK_DENIED")
    assert os.environ["APCA_API_KEY_ID"] == "synthetic-from-process"
    assert missing[2].calls == 0


def test_invalid_synthetic_body_is_terminal() -> None:
    cases = (
        (ScriptedOutcome(status=200), "MISSING_BODY"),
        (ScriptedOutcome(status=200, body=None), "NULL_BODY"),
        (ScriptedOutcome(status=200, body={}), "EMPTY_BODY"),
        (ScriptedOutcome(status=200, body=["ACTIVE"]), "MALFORMED_BODY"),
        (ScriptedOutcome(status=200, body={"state": "ACTIVE"}), "MISSING_STATUS"),
        (ScriptedOutcome(status=200, body={"status": 1}), "MALFORMED_STATUS"),
        (ScriptedOutcome(status=200, body={"status": True}), "MALFORMED_STATUS"),
        (ScriptedOutcome(status=200, body={"status": None}), "MALFORMED_STATUS"),
        (ScriptedOutcome(status=200, body={"status": ""}), "MALFORMED_STATUS"),
        (ScriptedOutcome(status=200, body={"status": "INACTIVE"}), "UNSUPPORTED_STATUS"),
        (
            ScriptedOutcome(status=200, body={"status": "ACTIVE", "state": "INACTIVE"}),
            "CONTRADICTORY_BODY",
        ),
        (
            ScriptedOutcome(status=200, body={"status": "ACTIVE", "classification": "DENIED"}),
            "CONTRADICTORY_BODY",
        ),
    )
    for outcome, reason in cases:
        ready = _ready(outcome=outcome)
        _denied(lambda current=ready: read_account(*current), reason)
        assert ready[2].calls == 1
        _denied(lambda current=ready: read_account(*current), "MULTIPLE_GET_DENIED")
        assert ready[2].calls == 1


def test_transport_exception_does_not_repeat() -> None:
    failed = _ready(outcome=ScriptedOutcome(fault="exception", body={"status": "ACTIVE"}))
    _denied(lambda: read_account(*failed), "TRANSPORT_EXCEPTION")
    assert failed[2].calls == 1
    _denied(lambda: read_account(*failed), "MULTIPLE_GET_DENIED")
    assert failed[2].calls == 1


def test_secret_bytes_stay_out_of_text() -> None:
    session, custody, transport, runtime = _ready(
        outcome=ScriptedOutcome(body={"status": "ACTIVE"})
    )
    decision = read_account(session, custody, transport, runtime)
    rendered = " ".join(
        (
            repr(custody),
            str(custody),
            repr(transport),
            str(transport),
            repr(decision),
            str(decision),
            repr(runtime),
        )
    )
    assert _SECRET.decode() not in rendered
    assert _KEY_ID.decode() not in rendered
    denied = _ready(
        outcome=ScriptedOutcome(
            status=200,
            body={"status": "ACTIVE", "note": _SECRET.decode()},
        )
    )
    error = _denied(lambda: read_account(*denied), "CONTRADICTORY_BODY")
    assert _SECRET.decode() not in repr(error)
    assert _SECRET.decode() not in str(error)


def test_runtime_must_be_an_explicit_windows_grant() -> None:
    closed = _ready(runtime=False)
    _denied(lambda: read_account(*closed[:3], None), "RUNTIME_UNAUTHORIZED")
    assert closed[2].calls == 0
    linux = _ready(runtime=RuntimeAuthorization("Linux"))
    _denied(lambda: read_account(*linux), "RUNTIME_PLATFORM_DENIED")
    assert linux[2].calls == 0
    raw = _ready(runtime="Windows")
    _denied(lambda: read_account(*raw), "MALFORMED_RUNTIME")


def test_only_the_scripted_transport_can_be_used() -> None:
    called = {"count": 0}

    def network() -> None:
        called["count"] += 1
        raise AssertionError("provider")

    session, custody, _transport, runtime = _ready()
    _denied(lambda: read_account(session, custody, network, runtime), "TRANSPORT_DENIED")
    assert called["count"] == 0


def test_module_has_no_provider_or_native_store_path() -> None:
    source = _MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".", 1)[0])
    assert imported == {"__future__", "enum", "swingtrade"}
    lowered = source.lower()
    for token in (
        "getenv",
        "environ",
        "advapi32",
        "ctypes",
        "winreg",
        "keyring",
        "credread",
        "credwrite",
        "psycopg",
        "sqlalchemy",
        "orderintent",
        "logging",
        "urllib",
        "httplib",
    ):
        assert token not in lowered
    for token in _SCAN_TOKENS:
        assert token not in lowered
    signature = inspect.signature(read_account)
    assert tuple(signature.parameters) == (
        "session",
        "custody",
        "transport",
        "runtime",
        "method",
        "url",
    )
    assert {"proxy", "verify", "follow_redirects"}.isdisjoint(signature.parameters)


def test_protected_gate_blobs_stay_unchanged() -> None:
    for path, blob in _BLOBS.items():
        assert _blob(path) == blob
