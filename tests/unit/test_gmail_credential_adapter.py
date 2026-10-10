"""Offline tests for the mocked Gmail credential adapter.

Restart coverage uses a fake store. It is not Windows reboot evidence.
Allocation release is mock cleanup. It is not native CredFree certification.
The in-process lock is not cross-process atomicity.
"""

from __future__ import annotations

import ast
import logging
import socket
import threading
from pathlib import Path

import pytest

from swingtrade.gmail_credential import (
    CANONICAL_TARGET,
    CRED_PERSIST_ENTERPRISE,
    CRED_PERSIST_LOCAL_MACHINE,
    CRED_PERSIST_SESSION,
    CRED_TYPE_GENERIC,
    NATIVE_BACKEND_ENABLED,
    CredentialOperationError,
    GmailCredentialAdapter,
    MockCredentialPort,
    SyntheticSecret,
    synthetic_fixture,
)

MARKER = b"synthetic-fixture-redaction-value"
CASE_VARIANT = "Swing-Trading/Lane3/Gmail/Dev/Refresh-Token"
TRADESTATION_TARGET = "swing-trading/lane2/tradestation/dev/refresh-token"
OTHER_TARGET = "swing-trading/lane3/gmail/dev/refresh-token-extra"
PACKAGE = Path("src/swingtrade/gmail_credential")


def _adapter() -> tuple[GmailCredentialAdapter, MockCredentialPort]:
    port = MockCredentialPort()
    return GmailCredentialAdapter(port), port


def _secret(material: bytes = b"synthetic-fixture-initial") -> SyntheticSecret:
    return synthetic_fixture(material)


def _code(callback: object) -> str:
    with pytest.raises(CredentialOperationError) as caught:
        if not callable(callback):
            raise AssertionError("callback")
        callback()
    return caught.value.code


def _leaks(text: str) -> bool:
    return MARKER.decode("ascii") in text


def test_initial_store_and_retrieve() -> None:
    adapter, port = _adapter()
    secret = _secret()
    adapter.store(secret)
    view = adapter.retrieve()
    assert view.matches(secret) is True
    assert view.target == CANONICAL_TARGET
    assert view.cred_type == CRED_TYPE_GENERIC
    assert view.persist == CRED_PERSIST_LOCAL_MACHINE
    assert port.entry_count() == 1
    assert port.create_attempts == 1
    assert port.replace_attempts == 0


def test_duplicate_store_collision_does_not_overwrite() -> None:
    adapter, port = _adapter()
    original = _secret(b"synthetic-fixture-original")
    challenger = _secret(b"synthetic-fixture-challenger")
    adapter.store(original)
    assert _code(lambda: adapter.store(challenger)) == "collision"
    assert port.create_attempts == 1
    assert port.replace_attempts == 0
    assert adapter.retrieve().matches(original) is True
    assert adapter.retrieve().matches(challenger) is False


def test_case_variant_collides_and_does_not_create_second_credential() -> None:
    adapter, port = _adapter()
    original = _secret(b"synthetic-fixture-original")
    challenger = _secret(b"synthetic-fixture-challenger")
    adapter.store(original)
    attempts = port.create_attempts
    code = _code(lambda: adapter.store(challenger, target=CASE_VARIANT))
    assert code == "collision"
    assert port.create_attempts == attempts
    assert port.entry_count() == 1
    assert adapter.retrieve().matches(original) is True
    absent = _adapter()
    empty_adapter, empty_port = absent
    code = _code(lambda: empty_adapter.store(original, target=CASE_VARIANT))
    assert code == "non_canonical_target"
    assert empty_port.create_attempts == 0
    assert empty_port.entry_count() == 0


def test_seeded_case_variant_collides_with_canonical_store() -> None:
    adapter, port = _adapter()
    seeded = _secret(b"synthetic-fixture-seeded")
    challenger = _secret(b"synthetic-fixture-challenger")
    port.seed_case_variant(seeded, CRED_PERSIST_LOCAL_MACHINE)
    assert _code(lambda: adapter.store(challenger)) == "collision"
    assert port.create_attempts == 0
    assert port.entry_count() == 1
    assert adapter.retrieve().matches(seeded) is True
    assert adapter.retrieve().matches(challenger) is False


def test_noncanonical_target_rejected_before_mock() -> None:
    adapter, port = _adapter()
    secret = _secret()
    for target in (TRADESTATION_TARGET, OTHER_TARGET, "", "Microsoft_RAS_target"):
        store_code = _code(lambda target=target: adapter.store(secret, target=target))
        assert store_code == "target_rejected"
        assert _code(lambda target=target: adapter.retrieve(target=target)) == "target_rejected"
        assert _code(lambda target=target: adapter.delete(target=target)) == "target_rejected"
    assert port.create_attempts == 0
    assert port.read_attempts == 0
    assert port.delete_attempts == 0
    assert port.replace_attempts == 0


def test_missing_retrieve_replace_and_delete() -> None:
    adapter, port = _adapter()
    secret = _secret()
    assert _code(adapter.retrieve) == "missing"
    assert _code(lambda: adapter.replace(secret)) == "missing"
    assert _code(adapter.delete) == "missing"
    assert port.create_attempts == 0
    assert port.replace_attempts == 0
    assert port.entry_count() == 0


def test_replace_updates_only_existing() -> None:
    adapter, port = _adapter()
    original = _secret(b"synthetic-fixture-original")
    replacement = _secret(b"synthetic-fixture-replacement")
    adapter.store(original)
    adapter.replace(replacement)
    assert port.create_attempts == 1
    assert port.replace_attempts == 1
    assert port.entry_count() == 1
    assert adapter.retrieve().matches(replacement) is True
    assert adapter.retrieve().matches(original) is False


def test_delete_and_second_delete() -> None:
    adapter, port = _adapter()
    secret = _secret()
    adapter.store(secret)
    adapter.delete()
    assert port.entry_count() == 0
    assert _code(adapter.delete) == "missing"
    assert _code(adapter.retrieve) == "missing"


def test_unsupported_os_fails_closed() -> None:
    adapter, port = _adapter()
    port.session_fault = "unsupported_os"
    secret = _secret(MARKER)
    assert _code(lambda: adapter.store(secret)) == "unsupported_os"
    assert port.create_attempts == 0
    assert port.entry_count() == 0


def test_invalid_security_context_fails_closed() -> None:
    adapter, port = _adapter()
    port.session_fault = "invalid_security_context"
    assert _code(lambda: adapter.store(_secret())) == "invalid_security_context"
    assert port.create_attempts == 0


def test_permission_denied_fails_closed_without_disclosure() -> None:
    adapter, port = _adapter()
    secret = _secret(MARKER)
    adapter.store(secret)
    port.operation_fault = "permission_denied"
    with pytest.raises(CredentialOperationError) as caught:
        adapter.retrieve()
    assert caught.value.code == "permission_denied"
    assert _leaks(f"{caught.value!r} {caught.value}") is False
    assert adapter.retrieve().matches(secret) is True
    fresh, fresh_port = _adapter()
    fresh_port.operation_fault = "permission_denied"
    assert _code(lambda: fresh.store(secret)) == "permission_denied"
    assert fresh_port.entry_count() == 0
    assert fresh_port.create_attempts == 1


def test_missing_logon_session() -> None:
    adapter, port = _adapter()
    port.session_fault = "no_logon_session"
    assert _code(lambda: adapter.store(_secret())) == "no_logon_session"
    assert port.create_attempts == 0
    assert port.read_attempts == 0


def test_wrong_persistence_rejected() -> None:
    adapter, port = _adapter()
    secret = _secret()
    assert _code(lambda: adapter.store(secret, persist=CRED_PERSIST_SESSION)) == (
        "unsupported_persistence"
    )
    assert _code(lambda: adapter.store(secret, persist=0)) == "unsupported_persistence"
    assert _code(lambda: adapter.replace(secret, persist=9)) == "unsupported_persistence"
    assert port.create_attempts == 0
    assert port.replace_attempts == 0


def test_enterprise_persistence_rejected() -> None:
    adapter, port = _adapter()
    secret = _secret()
    code = _code(lambda: adapter.store(secret, persist=CRED_PERSIST_ENTERPRISE))
    assert code == "enterprise_persistence_rejected"
    code = _code(lambda: adapter.replace(secret, persist=CRED_PERSIST_ENTERPRISE))
    assert code == "enterprise_persistence_rejected"
    assert port.create_attempts == 0
    assert port.entry_count() == 0


def test_mock_read_write_and_delete_failures() -> None:
    adapter, port = _adapter()
    secret = _secret(MARKER)
    port.operation_fault = "write_failure"
    assert _code(lambda: adapter.store(secret)) == "write_failure"
    assert port.entry_count() == 0
    adapter.store(secret)
    port.operation_fault = "read_failure"
    with pytest.raises(CredentialOperationError) as caught:
        adapter.retrieve()
    assert caught.value.code == "read_failure"
    assert _leaks(f"{caught.value!r} {caught.value}") is False
    port.operation_fault = "delete_failure"
    assert _code(adapter.delete) == "delete_failure"
    assert port.entry_count() == 1
    assert adapter.retrieve().matches(secret) is True


def test_interrupted_write_is_not_success_and_retry_stores_once() -> None:
    adapter, port = _adapter()
    secret = _secret()
    port.operation_fault = "interrupted_write"
    assert _code(lambda: adapter.store(secret)) == "interrupted_write"
    assert port.create_attempts == 1
    assert port.read_attempts >= 1
    assert port.entry_count() == 0
    assert _code(adapter.retrieve) == "missing"
    adapter.store(secret)
    assert port.create_attempts == 2
    assert port.entry_count() == 1
    assert adapter.retrieve().matches(secret) is True


def test_ambiguous_write_reconciles_without_retry() -> None:
    adapter, port = _adapter()
    secret = _secret()
    port.operation_fault = "ambiguous_write"
    assert _code(lambda: adapter.store(secret)) == "ambiguous_write"
    assert port.create_attempts == 1
    assert adapter.retrieve().matches(secret) is True
    assert _code(lambda: adapter.store(secret)) == "collision"
    assert port.create_attempts == 1
    replacement = _secret(b"synthetic-fixture-replacement")
    port.operation_fault = "ambiguous_write"
    assert _code(lambda: adapter.replace(replacement)) == "ambiguous_write"
    assert port.replace_attempts == 1
    assert adapter.retrieve().matches(replacement) is True
    assert port.replace_attempts == 1


def test_restart_retrieve_duplicate_replace_and_delete() -> None:
    adapter, port = _adapter()
    original = _secret(b"synthetic-fixture-original")
    replacement = _secret(b"synthetic-fixture-replacement")
    adapter.store(original)
    restarted = GmailCredentialAdapter(port)
    assert restarted.retrieve().matches(original) is True
    assert _code(lambda: restarted.store(original)) == "collision"
    restarted.replace(replacement)
    after_replace = GmailCredentialAdapter(port)
    assert after_replace.retrieve().matches(replacement) is True
    after_replace.delete()
    after_delete = GmailCredentialAdapter(port)
    assert _code(after_delete.retrieve) == "missing"
    isolated, _isolated_port = _adapter()
    assert _code(isolated.retrieve) == "missing"


def test_secret_excluded_from_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="swingtrade.gmail_credential")
    adapter, port = _adapter()
    secret = _secret(MARKER)
    adapter.store(secret)
    adapter.retrieve()
    adapter.replace(secret)
    port.operation_fault = "permission_denied"
    assert _code(adapter.delete) == "permission_denied"
    assert _leaks(caplog.text) is False


def test_secret_excluded_from_exceptions() -> None:
    adapter, _port = _adapter()
    rejected: object = MARKER
    with pytest.raises(CredentialOperationError) as caught:
        adapter.store(rejected)
    assert caught.value.code == "non_synthetic_input"
    rendered = f"{caught.value!r} {caught.value}"
    assert _leaks(rendered) is False
    secret = _secret(MARKER)
    adapter.store(secret)
    with pytest.raises(CredentialOperationError) as collision:
        adapter.store(secret)
    assert collision.value.code == "collision"
    assert _leaks(f"{collision.value!r} {collision.value}") is False


def test_secret_excluded_from_repr() -> None:
    adapter, port = _adapter()
    secret = _secret(MARKER)
    adapter.store(secret)
    view = adapter.retrieve()
    rendered = f"{secret!r} {secret} {format(secret)} {view!r} {view} {adapter!r} {port!r}"
    assert _leaks(rendered) is False
    assert secret.matches(secret) is True


def test_non_synthetic_input_rejected() -> None:
    adapter, port = _adapter()
    assert _code(lambda: adapter.store(b"synthetic-looking-bytes")) == "non_synthetic_input"
    assert _code(lambda: adapter.store("synthetic-looking-text")) == "non_synthetic_input"
    assert _code(lambda: adapter.replace(object())) == "non_synthetic_input"
    assert port.create_attempts == 0
    assert port.replace_attempts == 0
    with pytest.raises(CredentialOperationError) as caught:
        synthetic_fixture(b"")
    assert caught.value.code == "non_synthetic_input"


def test_tradestation_and_other_targets_do_not_touch_store() -> None:
    adapter, port = _adapter()
    secret = _secret()
    adapter.store(secret)
    reads = port.read_attempts
    creates = port.create_attempts
    assert _code(lambda: adapter.store(secret, target=TRADESTATION_TARGET)) == "target_rejected"
    assert _code(lambda: adapter.retrieve(target=OTHER_TARGET)) == "target_rejected"
    assert _code(lambda: adapter.delete(target=TRADESTATION_TARGET)) == "target_rejected"
    assert port.create_attempts == creates
    assert port.read_attempts == reads
    assert port.entry_count() == 1
    assert adapter.retrieve().matches(secret) is True


def test_alternate_user_rejected() -> None:
    adapter, port = _adapter()
    secret = _secret()
    assert _code(lambda: adapter.store(secret, windows_user="other-user")) == (
        "alternate_user_rejected"
    )
    assert _code(lambda: adapter.retrieve(windows_user="other-user")) == "alternate_user_rejected"
    assert port.create_attempts == 0


def test_mock_required_and_environment_cannot_enable_native(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert NATIVE_BACKEND_ENABLED is False
    monkeypatch.setenv("SWINGTRADE_WINDOWS_CREDENTIALS", "native")
    monkeypatch.setenv("CRED_BACKEND", "advapi32")
    assert _code(lambda: GmailCredentialAdapter(port=None)) == "mock_required"
    assert _code(lambda: GmailCredentialAdapter(object())) == "mock_required"
    adapter, _port = _adapter()
    adapter.store(_secret())


def test_mock_allocation_released_on_success_and_exception() -> None:
    """Mock ids are released. This does not certify native CredFree."""
    adapter, port = _adapter()
    secret = _secret(MARKER)
    adapter.store(secret)
    view = adapter.retrieve()
    assert view.matches(secret) is True
    assert port.alloc_count == port.release_count
    assert port.live_allocation_count() == 0
    port.raise_after_read = True
    with pytest.raises(CredentialOperationError) as caught:
        adapter.retrieve()
    assert caught.value.code == "read_consumer_failed"
    assert _leaks(f"{caught.value!r} {caught.value}") is False
    assert port.alloc_count == port.release_count
    assert port.live_allocation_count() == 0
    port.raise_after_read = False
    port.operation_fault = "ambiguous_write"
    assert _code(lambda: adapter.replace(secret)) == "ambiguous_write"
    assert port.alloc_count == port.release_count
    assert port.live_allocation_count() == 0


def test_package_does_not_invoke_native_or_network_apis() -> None:
    banned_modules = {"ctypes", "socket", "urllib", "http", "winreg", "ssl", "requests"}
    banned_calls = {"CredWriteW", "CredReadW", "CredDeleteW", "CredFree", "WinDLL", "CDLL"}
    for path in sorted(PACKAGE.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "advapi32" not in source
        assert "token_store" not in source
        assert "group3_auth" not in source
        assert "group4_email" not in source
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".", 1)[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [(node.module or "").split(".", 1)[0]]
            else:
                modules = []
            for module in modules:
                assert module not in banned_modules
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    assert func.id not in banned_calls
                if isinstance(func, ast.Attribute):
                    assert func.attr not in banned_calls


def test_operations_do_not_open_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def _deny(*_args: object, **_kwargs: object) -> None:
        raise OSError("network denied")

    monkeypatch.setattr(socket, "socket", _deny)
    monkeypatch.setattr(socket, "create_connection", _deny)
    adapter, _port = _adapter()
    secret = _secret()
    adapter.store(secret)
    assert adapter.retrieve().matches(secret) is True
    adapter.replace(secret)
    adapter.delete()


def test_concurrent_create_replace_and_delete() -> None:
    """In-process serialization only. Cross-process atomicity is not claimed."""
    adapter, port = _adapter()
    barrier = threading.Barrier(6)
    codes: list[str] = []
    lock = threading.Lock()

    def create_worker(index: int) -> None:
        secret = synthetic_fixture(f"synthetic-concurrent-{index}".encode("ascii"))
        barrier.wait()
        try:
            adapter.store(secret)
            code = "stored"
        except CredentialOperationError as exc:
            code = exc.code
        with lock:
            codes.append(code)

    threads = [threading.Thread(target=create_worker, args=(index,)) for index in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert codes.count("stored") == 1
    assert codes.count("collision") == 5
    assert port.create_attempts == 1
    assert port.entry_count() == 1
    matched = [
        index
        for index in range(6)
        if adapter.retrieve().matches(
            synthetic_fixture(f"synthetic-concurrent-{index}".encode("ascii"))
        )
    ]
    assert len(matched) == 1

    replace_barrier = threading.Barrier(4)

    def replace_worker(index: int) -> None:
        secret = synthetic_fixture(f"synthetic-replace-{index}".encode("ascii"))
        replace_barrier.wait()
        adapter.replace(secret)

    replacers = [threading.Thread(target=replace_worker, args=(index,)) for index in range(4)]
    for thread in replacers:
        thread.start()
    for thread in replacers:
        thread.join()
    assert port.replace_attempts == 4
    assert port.entry_count() == 1
    replaced = []
    for index in range(4):
        secret = synthetic_fixture(f"synthetic-replace-{index}".encode("ascii"))
        if adapter.retrieve().matches(secret):
            replaced.append(index)
    assert len(replaced) == 1

    delete_barrier = threading.Barrier(4)
    delete_codes: list[str] = []

    def delete_worker() -> None:
        delete_barrier.wait()
        try:
            adapter.delete()
            code = "deleted"
        except CredentialOperationError as exc:
            code = exc.code
        with lock:
            delete_codes.append(code)

    deleters = [threading.Thread(target=delete_worker) for _index in range(4)]
    for thread in deleters:
        thread.start()
    for thread in deleters:
        thread.join()
    assert sorted(delete_codes) == ["deleted", "missing", "missing", "missing"]
    assert port.entry_count() == 0


def test_secret_export_rejected() -> None:
    secret = _secret(MARKER)
    with pytest.raises(CredentialOperationError) as caught:
        secret.__reduce__()
    assert caught.value.code == "secret_export_rejected"
    assert _leaks(f"{caught.value!r} {caught.value}") is False
