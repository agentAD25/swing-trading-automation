"""Fail-closed offline results. Unknown is not a failure that may be retried."""

from __future__ import annotations

import re
from enum import StrEnum

_SAFE_REASON = re.compile(r"^[A-Z0-9_]{1,64}$")


class OutcomeCode(StrEnum):
    ASSEMBLED = "ASSEMBLED"
    CLASSIFIED = "CLASSIFIED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class AuthModelError(RuntimeError):
    """Reason code only. Request material is not part of the message."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class AuthDecision:
    """Local classification. Network and retry stay unavailable."""

    __slots__ = ("code", "reason")

    def __init__(self, code: OutcomeCode, reason: str) -> None:
        if not isinstance(code, OutcomeCode) or _SAFE_REASON.fullmatch(reason) is None:
            raise AuthModelError("INVALID_OUTCOME")
        self.code = code
        self.reason = reason

    @property
    def safe_to_retry(self) -> bool:
        return False

    @property
    def network_permitted(self) -> bool:
        return False

    def __str__(self) -> str:
        return self.code.value

    def __repr__(self) -> str:
        return f"AuthDecision({self.code.value}, {self.reason})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AuthDecision):
            return NotImplemented
        return (self.code, self.reason) == (other.code, other.reason)


def decision(code: OutcomeCode, reason: str) -> AuthDecision:
    return AuthDecision(code, reason)
