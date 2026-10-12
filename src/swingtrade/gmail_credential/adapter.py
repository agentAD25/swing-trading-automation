"""Orchestrate store, retrieve, replace, and delete against an injected mock."""

from __future__ import annotations

import logging
from typing import NoReturn

from swingtrade.gmail_credential.errors import CredentialOperationError
from swingtrade.gmail_credential.identity import (
    CANONICAL_TARGET,
    CRED_PERSIST_LOCAL_MACHINE,
    CRED_TYPE_GENERIC,
    NATIVE_BACKEND_ENABLED,
    classify_target,
    persistence_code,
)
from swingtrade.gmail_credential.mock_port import MockCredentialPort
from swingtrade.gmail_credential.secret import SyntheticSecret, _material_of

_LOG = logging.getLogger("swingtrade.gmail_credential")


class OfflineCredentialView:
    """Retrieved synthetic material. ``repr`` never includes the bytes."""

    __slots__ = ("_material", "cred_type", "persist", "target")

    def __init__(self, material: bytes, persist: int) -> None:
        self._material = material
        self.target = CANONICAL_TARGET
        self.cred_type = CRED_TYPE_GENERIC
        self.persist = persist

    def __repr__(self) -> str:
        return "OfflineCredentialView(redacted)"

    def __str__(self) -> str:
        return "OfflineCredentialView(redacted)"

    def matches(self, secret: object) -> bool:
        if type(secret) is not SyntheticSecret:
            return False
        return self._material == _material_of(secret)


class GmailCredentialAdapter:
    """Gmail-only offline adapter. A missing mock fails closed.

    Construction ignores environment variables. There is no native fallback.
    """

    def __init__(self, port: object) -> None:
        if NATIVE_BACKEND_ENABLED:
            raise CredentialOperationError("native_backend_disabled")
        if type(port) is not MockCredentialPort:
            raise CredentialOperationError("mock_required")
        self._port = port

    def __repr__(self) -> str:
        return "GmailCredentialAdapter(mock)"

    def store(
        self,
        secret: object,
        *,
        target: str = CANONICAL_TARGET,
        persist: int = CRED_PERSIST_LOCAL_MACHINE,
        windows_user: object | None = None,
    ) -> None:
        """Create the synthetic credential only when the canonical target is absent."""
        material = self._boundary(
            secret,
            target=target,
            persist=persist,
            windows_user=windows_user,
            allow_case_variant=True,
        )
        with self._port.hold():
            self._require_session()
            kind = classify_target(target)
            present = self._port.contains_holding_lock()
            if kind == "case_variant":
                if present:
                    self._fail("collision")
                self._fail("non_canonical_target")
            if present:
                self._fail("collision")
            status = self._port.create_holding_lock(material, persist)
            self._finish_write(
                status,
                success_code="stored",
                material=material,
                persist=persist,
            )

    def retrieve(
        self,
        *,
        target: str = CANONICAL_TARGET,
        windows_user: object | None = None,
    ) -> OfflineCredentialView:
        """Return the synthetic credential for the canonical target only."""
        self._reject_caller(target=target, windows_user=windows_user, allow_case_variant=False)
        with self._port.hold():
            self._require_session()
            return self._read_view()

    def replace(
        self,
        secret: object,
        *,
        target: str = CANONICAL_TARGET,
        persist: int = CRED_PERSIST_LOCAL_MACHINE,
        windows_user: object | None = None,
    ) -> None:
        """Replace an existing canonical credential. Absence does not create."""
        material = self._boundary(
            secret,
            target=target,
            persist=persist,
            windows_user=windows_user,
            allow_case_variant=False,
        )
        with self._port.hold():
            self._require_session()
            if not self._port.contains_holding_lock():
                self._fail("missing")
            status = self._port.replace_holding_lock(material, persist)
            self._finish_write(
                status,
                success_code="replaced",
                material=material,
                persist=persist,
            )

    def delete(
        self,
        *,
        target: str = CANONICAL_TARGET,
        windows_user: object | None = None,
    ) -> None:
        """Delete the canonical target. A second delete fails closed."""
        self._reject_caller(target=target, windows_user=windows_user, allow_case_variant=False)
        with self._port.hold():
            self._require_session()
            status = self._port.delete_holding_lock()
            if status == "deleted" and not self._port.contains_holding_lock():
                self._log("deleted")
                return
            if status == "deleted":
                self._fail("fail_closed")
            self._fail(status)

    def _boundary(
        self,
        secret: object,
        *,
        target: str,
        persist: int,
        windows_user: object | None,
        allow_case_variant: bool,
    ) -> bytes:
        self._reject_caller(
            target=target,
            windows_user=windows_user,
            allow_case_variant=allow_case_variant,
        )
        persist_error = persistence_code(persist)
        if persist_error is not None:
            self._fail(persist_error)
        if type(secret) is not SyntheticSecret:
            self._fail("non_synthetic_input")
        return _material_of(secret)

    def _reject_caller(
        self,
        *,
        target: str,
        windows_user: object | None,
        allow_case_variant: bool,
    ) -> None:
        if windows_user is not None:
            self._fail("alternate_user_rejected")
        kind = classify_target(target)
        if kind == "rejected":
            self._fail("target_rejected")
        if kind == "case_variant" and not allow_case_variant:
            self._fail("non_canonical_target")

    def _require_session(self) -> None:
        fault = self._port.session_block()
        if fault is not None:
            self._fail(fault)

    def _finish_write(
        self,
        status: str,
        *,
        success_code: str,
        material: bytes,
        persist: int,
    ) -> None:
        """Report success only when the mock row matches this write.

        Ambiguous and interrupted results stay failures. The reconcile read
        does not issue another write.
        """
        if status == success_code and self._stored_matches(material, persist):
            self._log(success_code)
            return
        if status == success_code:
            self._fail("fail_closed")
        if status in {"ambiguous_write", "interrupted_write"}:
            self._reconcile()
            self._fail(status)
        if status == "stored" or status == "replaced":
            self._fail("fail_closed")
        self._fail(status)

    def _stored_matches(self, material: bytes, persist: int) -> bool:
        allocation_id: int | None = None
        try:
            outcome = self._port.read_holding_lock()
            if type(outcome) is not tuple or len(outcome) != 3:
                return False
            raw_id, stored, stored_persist = outcome
            if type(raw_id) is int:
                allocation_id = raw_id
            if type(stored) is not bytes:
                return False
            return stored == material and stored_persist == persist
        finally:
            self._port.release(allocation_id)

    def _reconcile(self) -> None:
        """Read mock state after an uncertain write. Do not retry the write."""
        allocation_id: int | None = None
        try:
            outcome = self._port.read_holding_lock()
            if type(outcome) is tuple and len(outcome) >= 1 and type(outcome[0]) is int:
                allocation_id = outcome[0]
        finally:
            self._port.release(allocation_id)

    def _read_view(self) -> OfflineCredentialView:
        allocation_id: int | None = None
        try:
            outcome = self._port.read_holding_lock()
            if isinstance(outcome, str):
                self._fail(outcome)
            if type(outcome) is not tuple or len(outcome) != 3:
                self._fail("fail_closed")
            raw_id, material, persist = outcome
            if type(raw_id) is int:
                allocation_id = raw_id
            if self._port.raise_after_read:
                self._fail("read_consumer_failed")
            persist_error = persistence_code(persist)
            if persist_error is not None:
                self._fail(persist_error)
            if type(material) is not bytes or len(material) == 0:
                self._fail("fail_closed")
            if type(persist) is not int:
                self._fail("fail_closed")
            return OfflineCredentialView(material, persist)
        finally:
            self._port.release(allocation_id)

    def _fail(self, code: str) -> NoReturn:
        self._log(code)
        raise CredentialOperationError(code)

    def _log(self, code: str) -> None:
        _LOG.info("credential_operation code=%s", code)
