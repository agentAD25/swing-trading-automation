"""Per-login throttle state. HTTP 429 stops. This module does not retry or connect."""

from __future__ import annotations

import re
from collections.abc import Mapping

_LOGIN = re.compile(r"^LOGIN_[A-Z0-9_]{1,32}$")
_LIMIT_HEADERS = frozenset({"X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"})


class ThrottleError(RuntimeError):
    """Reason code only. Header values are not part of the message."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class ThrottleVerdict:
    """One login's throttling decision. Retries stay exhausted."""

    __slots__ = ("action", "login_label", "retry_after_seconds", "retry_budget", "safe_to_retry")

    def __init__(self, login_label: str, action: str, retry_after_seconds: int | None) -> None:
        self.login_label = login_label
        self.action = action
        self.retry_after_seconds = retry_after_seconds
        self.retry_budget = 0
        self.safe_to_retry = False

    def __repr__(self) -> str:
        return f"ThrottleVerdict({self.action})"


class LoginThrottle:
    """Independent state for one synthetic login label."""

    __slots__ = ("_stopped", "label")

    def __init__(self, label: str) -> None:
        if _LOGIN.fullmatch(label) is None:
            raise ThrottleError("MALFORMED_LOGIN_LABEL")
        self.label = label
        self._stopped = False

    def observe(self, *, status: object, headers: object) -> ThrottleVerdict:
        if self._stopped:
            return self._verdict("STOP", None)
        retry_after = _retry_after(headers)
        limits = _limits(headers)
        if limits == "MALFORMED_HEADER":
            self._stopped = True
            return self._verdict("STOP", None)
        if status == 429 or retry_after == "PRESENT_UNPARSED":
            self._stopped = True
            seconds = retry_after if type(retry_after) is int else None
            return self._verdict("STOP", seconds)
        if type(status) is not int or status < 100 or status > 599:
            self._stopped = True
            return self._verdict("STOP", None)
        return self._verdict("CONTINUE", None)

    def allow(self) -> ThrottleVerdict:
        if self._stopped:
            return self._verdict("STOP", None)
        return self._verdict("CONTINUE", None)

    def _verdict(self, action: str, retry_after: int | None) -> ThrottleVerdict:
        return ThrottleVerdict(self.label, action, retry_after)


class ThrottleBook:
    """Per-login book. One login's 429 does not stop another login."""

    __slots__ = ("_logins",)

    def __init__(self) -> None:
        self._logins: dict[str, LoginThrottle] = {}

    def login(self, label: str) -> LoginThrottle:
        existing = self._logins.get(label)
        if existing is None:
            existing = LoginThrottle(label)
            self._logins[label] = existing
        return existing


def retry_permitted(verdict: ThrottleVerdict) -> bool:
    """The initial read-only budget is zero. A stored Retry-After does not retry."""
    return verdict.retry_budget > 0 and verdict.safe_to_retry


def _retry_after(headers: object) -> int | None | str:
    if headers is None:
        return None
    if not isinstance(headers, Mapping):
        return "PRESENT_UNPARSED"
    for key, value in headers.items():
        if type(key) is not str or key.lower() != "retry-after":
            continue
        if type(value) is not str or not value.isdigit():
            return "PRESENT_UNPARSED"
        parsed = int(value)
        if parsed < 0 or parsed > 86_400:
            return "PRESENT_UNPARSED"
        return parsed
    return None


def _limits(headers: object) -> str | None:
    if headers is None:
        return None
    if not isinstance(headers, Mapping):
        return "MALFORMED_HEADER"
    for key, value in headers.items():
        if type(key) is not str or key not in _LIMIT_HEADERS:
            continue
        if type(value) is not str or not value.isdigit():
            return "MALFORMED_HEADER"
    return None
