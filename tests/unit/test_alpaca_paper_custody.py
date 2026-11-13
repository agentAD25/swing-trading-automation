"""Negative checks for the offline Alpaca paper custody mock."""

from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path

import pytest

from swingtrade.alpaca_paper_boundary import (
    BROKER_HOST,
    BROKER_SANDBOX_HOST,
    DATA_HOST,
    LIVE_HOST,
    PAPER_HOST,
)
from swingtrade.alpaca_paper_custody import (
    AUTHX_HOST,
    AUTHX_SANDBOX_HOST,
    DATA_SANDBOX_HOST,
    PAPER_KEY_ID_TARGET,
    PAPER_SECRET_TARGET,
    CustodyClassification,
    CustodyDecision,
    CustodyError,
    SyntheticMock,
    delete,
    replace,
    store,
)

_SECRET = b"synthetic-paper-secret"
_KEY_ID = b"synthetic-paper-key-id"
_MODULE = Path(__file__).parents[2] / "src" / "swingtrade" / "alpaca_paper_custody.py"
_BOUNDARY = Path(__file__).parents[2] / "src" / "swingtrade" / "alpaca_paper_boundary.py"
_BOUNDARY_TESTS = Path(__file__).parents[2] / "tests" / "unit" / "test_alpaca_paper_boundary.py"
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


def _closed(decision: CustodyDecision) -> None:
    for name in _FLAGS:
        assert getattr(decision, name) is False


def _denied(operation: object, reason: str) -> CustodyError:
    with pytest.raises(CustodyError) as caught:
        operation()
    error = caught.value
    assert error.reason == reason
    assert str(error) == reason
    assert error.decision.classification is CustodyClassification.DENIED
    assert error.decision.reason == reason
    _closed(error.decision)
    assert _SECRET not in str(error).encode()
    assert _SECRET not in repr(error).encode()
    assert _KEY_ID not in str(error).encode()
    return error


def _blob(path: Path) -> str:
    payload = path.read_bytes().replace(b"\r\n", b"\n")
    prefix = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(prefix + payload).hexdigest()


def test_accepted_paper_mock_keeps_names_and_closed_flags() -> None:
    mock = SyntheticMock()
    stored = store(mock, PAPER_KEY_ID_TARGET, _KEY_ID, PAPER_HOST)
    secret = store(mock, PAPER_SECRET_TARGET, _SECRET, PAPER_HOST)
    assert stored.classification is CustodyClassification.ACCEPTED
    assert stored.reason == "STORED"
    assert secret.reason == "STORED"
    _closed(stored)
    _closed(secret)
    assert mock.target_names() == {PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET}
    assert PAPER_HOST == "paper-api.alpaca.markets"


def test_live_target_is_rejected_on_the_paper_host() -> None:
    mock = SyntheticMock()
    _denied(
        lambda: store(
            mock,
            "swing-trading/lane2/alpaca/live/secret",
            _SECRET,
            PAPER_HOST,
        ),
        "LIVE_TARGET_DENIED",
    )
    assert mock.target_names() == frozenset()


def test_live_name_is_rejected() -> None:
    _denied(
        lambda: store(SyntheticMock(), "paper-live-secret", _SECRET, PAPER_HOST),
        "LIVE_NAME_DENIED",
    )


def test_unsupported_hosts_are_rejected() -> None:
    hosts = (
        DATA_HOST,
        BROKER_HOST,
        BROKER_SANDBOX_HOST,
        AUTHX_HOST,
        AUTHX_SANDBOX_HOST,
        DATA_SANDBOX_HOST,
    )
    assert hosts == (
        "data.alpaca.markets",
        "broker-api.alpaca.markets",
        "broker-api.sandbox.alpaca.markets",
        "authx.alpaca.markets",
        "authx.sandbox.alpaca.markets",
        "data.sandbox.alpaca.markets",
    )
    for host in hosts:
        _denied(
            lambda host=host: store(SyntheticMock(), PAPER_SECRET_TARGET, _SECRET, host),
            "HOST_DENIED",
        )


def test_live_api_hostname_is_rejected() -> None:
    assert LIVE_HOST == "api.alpaca.markets"
    _denied(
        lambda: store(SyntheticMock(), PAPER_SECRET_TARGET, _SECRET, LIVE_HOST),
        "LIVE_HOST_DENIED",
    )


def test_paper_target_and_other_host_mismatch() -> None:
    _denied(
        lambda: store(SyntheticMock(), PAPER_KEY_ID_TARGET, _KEY_ID, "example.test"),
        "HOST_MISMATCH",
    )
    _denied(
        lambda: store(
            SyntheticMock(),
            PAPER_SECRET_TARGET,
            _SECRET,
            "https://paper-api.alpaca.markets",
        ),
        "MALFORMED_HOST",
    )


def test_missing_mock_fails_closed() -> None:
    _denied(lambda: store(None, PAPER_SECRET_TARGET, _SECRET, PAPER_HOST), "MISSING_MOCK")


def test_ambiguous_mock_does_not_retry_or_store() -> None:
    mock = SyntheticMock(
        {PAPER_SECRET_TARGET: [(_SECRET, PAPER_HOST), (_KEY_ID, PAPER_HOST)]}
    )
    _denied(lambda: store(mock, PAPER_SECRET_TARGET, _SECRET, PAPER_HOST), "AMBIGUOUS_MOCK")
    _denied(lambda: store(mock, PAPER_SECRET_TARGET, _SECRET, PAPER_HOST), "RETRY_DENIED")
    assert mock.target_names() == frozenset()
    function = ast.parse(inspect.getsource(store)).body[0]
    assert isinstance(function, ast.FunctionDef)
    calls = [
        node.func.id
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    assert "store" not in calls
    assert not any(isinstance(node, ast.While) for node in ast.walk(function))


def test_inconsistent_incomplete_and_malformed_mocks_fail_closed() -> None:
    inconsistent = SyntheticMock({PAPER_SECRET_TARGET: (_SECRET, LIVE_HOST)})
    incomplete = SyntheticMock({PAPER_SECRET_TARGET: (b"", PAPER_HOST)})
    malformed = SyntheticMock(["not-a-mapping"])
    _denied(
        lambda: store(inconsistent, PAPER_SECRET_TARGET, _SECRET, PAPER_HOST),
        "INCONSISTENT_MOCK",
    )
    _denied(
        lambda: replace(incomplete, PAPER_SECRET_TARGET, _SECRET, PAPER_HOST),
        "INCOMPLETE_MOCK",
    )
    _denied(lambda: delete(malformed, PAPER_SECRET_TARGET), "MALFORMED_MOCK")
    assert inconsistent.target_names() == frozenset()
    assert _SECRET not in repr(inconsistent).encode()
    assert _SECRET not in str(inconsistent).encode()


def test_secret_bytes_stay_out_of_decision_text() -> None:
    mock = SyntheticMock()
    decision = store(mock, PAPER_SECRET_TARGET, _SECRET, PAPER_HOST)
    assert _SECRET not in repr(decision).encode()
    assert _SECRET not in str(decision).encode()
    assert _SECRET not in repr(mock).encode()
    assert _SECRET not in str(mock).encode()
    replaced = replace(mock, PAPER_SECRET_TARGET, b"synthetic-paper-secret-2", PAPER_HOST)
    assert replaced.reason == "REPLACED"
    _closed(replaced)
    assert b"synthetic-paper-secret-2" not in repr(mock).encode()


def test_exception_text_omits_secret_bytes() -> None:
    _denied(
        lambda: store(SyntheticMock(), PAPER_SECRET_TARGET, _SECRET, LIVE_HOST),
        "LIVE_HOST_DENIED",
    )


def test_existing_target_and_absent_target_fail_closed() -> None:
    mock = SyntheticMock()
    store(mock, PAPER_SECRET_TARGET, _SECRET, PAPER_HOST)
    _denied(
        lambda: store(mock, PAPER_SECRET_TARGET, _SECRET, PAPER_HOST),
        "TARGET_EXISTS",
    )
    empty = SyntheticMock()
    _denied(
        lambda: replace(empty, PAPER_SECRET_TARGET, _SECRET, PAPER_HOST),
        "TARGET_ABSENT",
    )
    _denied(lambda: delete(empty, PAPER_KEY_ID_TARGET), "TARGET_ABSENT")
    assert delete(mock, PAPER_SECRET_TARGET).reason == "DELETED"
    assert mock.target_names() == frozenset()


def test_malformed_input_is_rejected() -> None:
    mock = SyntheticMock()
    cases = (
        (lambda: store(mock, None, _SECRET, PAPER_HOST), "MALFORMED_TARGET"),
        (lambda: store(mock, "", _SECRET, PAPER_HOST), "MALFORMED_TARGET"),
        (lambda: store(mock, "other-target", _SECRET, PAPER_HOST), "TARGET_DENIED"),
        (
            lambda: store(mock, PAPER_SECRET_TARGET.swapcase(), _SECRET, PAPER_HOST),
            "TARGET_CASE_DENIED",
        ),
        (
            lambda: store(mock, PAPER_SECRET_TARGET, "synthetic-paper-secret", PAPER_HOST),
            "MALFORMED_MATERIAL",
        ),
        (lambda: store(mock, PAPER_SECRET_TARGET, b"", PAPER_HOST), "INCOMPLETE_MATERIAL"),
        (lambda: store(mock, PAPER_SECRET_TARGET, _SECRET, None), "MALFORMED_HOST"),
        (lambda: store(mock, PAPER_SECRET_TARGET, _SECRET, ""), "MALFORMED_HOST"),
        (lambda: store(object(), PAPER_SECRET_TARGET, _SECRET, PAPER_HOST), "MALFORMED_MOCK"),
    )
    for operation, reason in cases:
        _denied(operation, reason)


def test_module_does_not_read_the_environment_or_call_windows() -> None:
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
    ):
        assert token not in lowered
    for token in _SCAN_TOKENS:
        assert token not in lowered


def test_signature_has_no_transport_switches() -> None:
    signature = inspect.signature(store)
    assert tuple(signature.parameters) == ("mock", "target", "material", "host")
    forbidden = {"proxy", "base_url", "verify", "redirect", "environ", "follow_redirects"}
    assert forbidden.isdisjoint(signature.parameters)
    with pytest.raises(TypeError):
        store(SyntheticMock(), PAPER_SECRET_TARGET, _SECRET, PAPER_HOST, proxy="off")  # type: ignore[call-arg]


def test_repeated_operations_are_deterministic() -> None:
    first = store(SyntheticMock(), PAPER_KEY_ID_TARGET, _KEY_ID, PAPER_HOST)
    second = store(SyntheticMock(), PAPER_KEY_ID_TARGET, _KEY_ID, PAPER_HOST)
    assert first == second
    denied = _denied(
        lambda: store(None, PAPER_KEY_ID_TARGET, _KEY_ID, PAPER_HOST),
        "MISSING_MOCK",
    )
    again = _denied(
        lambda: store(None, PAPER_KEY_ID_TARGET, _KEY_ID, PAPER_HOST),
        "MISSING_MOCK",
    )
    assert denied.decision == again.decision


def test_gate_c2_blobs_stay_unchanged() -> None:
    assert _blob(_BOUNDARY) == "854e6adb5c1c2d20370f724d3a7e6d4f32970509"
    assert _blob(_BOUNDARY_TESTS) == "8e5d89ac0a3f33463d518e62ccaefdadcdf2cdd1"
