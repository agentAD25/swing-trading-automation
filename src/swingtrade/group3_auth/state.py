"""Single-use CSRF state. Randomness is the standard library unless a test replaces it."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from collections.abc import Callable
from datetime import datetime

from swingtrade.domain import DomainValidationError, utc_instant
from swingtrade.group3_auth.outcomes import AuthDecision, AuthModelError, OutcomeCode, decision

TokenFactory = Callable[[int], str]


def _stdlib_token(nbytes: int) -> str:
    if type(nbytes) is not int or nbytes < 32:
        raise AuthModelError("STATE_ENTROPY_REJECTED")
    return secrets.token_urlsafe(nbytes)


class IssuedState:
    """Opaque state. Its rendering does not include the token."""

    __slots__ = ("value",)

    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:
        return "IssuedState"

    def __repr__(self) -> str:
        return "IssuedState"


class _Pending:
    __slots__ = ("consumed", "expires_at")

    def __init__(self, expires_at: datetime) -> None:
        self.expires_at = expires_at
        self.consumed = False


class StateIssuer:
    """Process-local state. This is not a token store."""

    __slots__ = ("_factory", "_pending")

    def __init__(self, token_factory: TokenFactory | None = None) -> None:
        self._factory = _stdlib_token if token_factory is None else token_factory
        self._pending: dict[bytes, _Pending] = {}

    def issue(self, *, issued_at: datetime, expires_at: datetime) -> IssuedState:
        try:
            issued = utc_instant(issued_at)
            expires = utc_instant(expires_at)
        except DomainValidationError:
            raise AuthModelError("STATE_EXPIRY_REJECTED") from None
        if expires <= issued:
            raise AuthModelError("STATE_EXPIRY_REJECTED")
        token = self._factory(32)
        if (
            type(token) is not str
            or len(token) < 43
            or any(character.isspace() for character in token)
        ):
            raise AuthModelError("STATE_ENTROPY_REJECTED")
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        if digest in self._pending:
            raise AuthModelError("STATE_ENTROPY_REJECTED")
        self._pending[digest] = _Pending(expires)
        return IssuedState(token)

    def consume(self, presented: object, *, now: datetime) -> AuthDecision:
        if type(presented) is not str or presented == "":
            return decision(OutcomeCode.REJECTED, "MISSING_STATE")
        try:
            instant = utc_instant(now)
        except DomainValidationError:
            return decision(OutcomeCode.REJECTED, "INVALID_INSTANT")
        pending = self._match(hashlib.sha256(presented.encode("utf-8")).digest())
        if pending is None:
            return decision(OutcomeCode.REJECTED, "STATE_MISMATCH")
        if pending.consumed:
            return decision(OutcomeCode.REJECTED, "STATE_REPLAY")
        if instant >= pending.expires_at:
            pending.consumed = True
            return decision(OutcomeCode.REJECTED, "STATE_EXPIRED")
        pending.consumed = True
        return decision(OutcomeCode.CLASSIFIED, "STATE_MATCHED")

    def _match(self, digest: bytes) -> _Pending | None:
        found: _Pending | None = None
        for key, pending in self._pending.items():
            if hmac.compare_digest(key, digest):
                found = pending
        return found
