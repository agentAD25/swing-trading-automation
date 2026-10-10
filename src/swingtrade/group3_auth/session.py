"""Fake access-token lifetime model. Profile B cannot be activated."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from enum import StrEnum
from threading import Lock

from swingtrade.domain import utc_instant
from swingtrade.group3_auth.outcomes import OutcomeCode
from swingtrade.group3_auth.scopes import validate_granted_scopes

ACCESS_TOKEN_MAX_SECONDS = 1200
_MAX_SKEW_SECONDS = 5
_SECRET_KEYS = frozenset(
    {"access_token", "client_secret", "code", "id_token", "password", "refresh_token"}
)


class SessionProfile(StrEnum):
    ATTENDED_READ_ONLY = "ATTENDED_READ_ONLY"
    UNATTENDED_REFRESH = "UNATTENDED_REFRESH"


class SessionError(RuntimeError):
    """Reason code only. Token material is not part of the message."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class SessionVerdict:
    """Local session state. safe_to_retry stays false."""

    __slots__ = ("code", "reason", "safe_to_retry")

    def __init__(self, code: OutcomeCode, reason: str) -> None:
        self.code = code
        self.reason = reason
        self.safe_to_retry = False

    def __repr__(self) -> str:
        return f"SessionVerdict({self.reason})"


class AttendedSession:
    """Memory-only attended session. The fake marker is never rendered."""

    __slots__ = ("_deadline", "_marker", "_open", "profile")

    def __init__(
        self,
        *,
        deadline: datetime,
        marker: str,
    ) -> None:
        self.profile = SessionProfile.ATTENDED_READ_ONLY
        self._deadline = deadline
        self._marker = marker
        self._open = True

    def __repr__(self) -> str:
        return "AttendedSession(ATTENDED_READ_ONLY)"

    def before_call(self, now: datetime) -> SessionVerdict:
        self._require_open()
        if _at_or_after(now, self._deadline):
            self._open = False
            return SessionVerdict(OutcomeCode.REJECTED, "REAUTHORIZATION_REQUIRED")
        return SessionVerdict(OutcomeCode.CLASSIFIED, "CALL_ALLOWED")

    def finish_call(self, now: datetime) -> SessionVerdict:
        self._require_open()
        if _at_or_after(now, self._deadline):
            self._open = False
            return SessionVerdict(OutcomeCode.REJECTED, "EXPIRED_DURING_REQUEST")
        return SessionVerdict(OutcomeCode.CLASSIFIED, "CALL_FINISHED")

    def note_provider_failure(self) -> SessionVerdict:
        self._open = False
        return SessionVerdict(OutcomeCode.REJECTED, "AUTHORIZATION_DENIED")

    def note_timeout(self) -> SessionVerdict:
        self._open = False
        return SessionVerdict(OutcomeCode.REJECTED, "NETWORK_TIMEOUT")

    def _require_open(self) -> None:
        if not self._open:
            raise SessionError("SESSION_CLOSED")


def open_attended_session(
    *,
    issued_at: datetime,
    expires_in: object,
    granted_scopes: object,
    refresh_present: object,
    marker: str,
    skew_seconds: int = 0,
) -> AttendedSession:
    """Open profile A. A refresh token, a non-1200 lifetime, or bad scope fails."""
    utc_instant(issued_at)
    if expires_in != ACCESS_TOKEN_MAX_SECONDS:
        raise SessionError("EXPIRES_IN_REJECTED")
    if refresh_present is not False:
        raise SessionError("UNEXPECTED_REFRESH_TOKEN")
    if type(marker) is not str or marker == "":
        raise SessionError("MALFORMED_MARKER")
    if type(skew_seconds) is not int or not 0 <= skew_seconds <= _MAX_SKEW_SECONDS:
        raise SessionError("CLOCK_SKEW_REJECTED")
    granted = validate_granted_scopes(granted_scopes)
    if granted.decision.code is not OutcomeCode.CLASSIFIED:
        raise SessionError(granted.decision.reason)
    deadline = issued_at + timedelta(seconds=ACCESS_TOKEN_MAX_SECONDS - skew_seconds)
    return AttendedSession(deadline=deadline, marker=marker)


def activate_unattended_profile() -> None:
    """Profile B is design-only. Activation is not authorized."""
    raise SessionError("PROFILE_B_NOT_AUTHORIZED")


def restore_after_restart(metadata: object) -> SessionVerdict:
    """An attended session does not survive restart. No refresh token is loaded."""
    checked = _metadata(metadata)
    if checked is not None:
        raise SessionError(checked)
    return SessionVerdict(OutcomeCode.REJECTED, "REAUTHORIZATION_REQUIRED")


def read_store_metadata(metadata: object) -> SessionVerdict:
    """Reject corrupted or secret-bearing metadata without echoing it."""
    checked = _metadata(metadata)
    if checked is not None:
        raise SessionError(checked)
    return SessionVerdict(OutcomeCode.CLASSIFIED, "METADATA_ACCEPTED")


class SingleFlight:
    """One in-process refresh execution. The body must not receive a real token."""

    __slots__ = ("_lock", "executions")

    def __init__(self) -> None:
        self._lock = Lock()
        self.executions = 0

    def refresh_once(self, body: Callable[[], None]) -> SessionVerdict:
        with self._lock:
            if self.executions != 0:
                return SessionVerdict(OutcomeCode.REJECTED, "REFRESH_ALREADY_STARTED")
            self.executions = 1
            body()
        return SessionVerdict(OutcomeCode.CLASSIFIED, "REFRESH_EXECUTED_ONCE")


def _metadata(metadata: object) -> str | None:
    if not isinstance(metadata, Mapping) or type(metadata) is not dict:
        return "CORRUPTED_METADATA"
    keys = set(metadata)
    if keys & _SECRET_KEYS:
        return "SECRET_METADATA_REJECTED"
    if keys != {"profile", "redacted", "version"}:
        return "CORRUPTED_METADATA"
    if metadata["version"] != 1 or metadata["redacted"] is not True:
        return "CORRUPTED_METADATA"
    if metadata["profile"] != SessionProfile.ATTENDED_READ_ONLY.value:
        return "CORRUPTED_METADATA"
    return None


def _at_or_after(now: datetime, deadline: datetime) -> bool:
    utc_instant(now)
    return now >= deadline
