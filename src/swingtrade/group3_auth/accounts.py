"""Synthetic SIM account allowlist. Discovery never selects an account."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

from swingtrade.contracts.monitoring import MonitoringEmitter
from swingtrade.contracts.secret_refs import DeploymentEnvironment
from swingtrade.group3_auth.monitoring import emit_auth_decision
from swingtrade.group3_auth.outcomes import AuthDecision, AuthModelError, OutcomeCode, decision

_SYNTHETIC = re.compile(r"^SYN_[A-Z0-9_]{1,32}$")


class AccountQuarantine:
    """Non-secret quarantine record. The raw account id is not stored."""

    __slots__ = ("digest", "reason")

    def __init__(self, reason: str, digest: str) -> None:
        self.reason = reason
        self.digest = digest

    def __repr__(self) -> str:
        return f"AccountQuarantine({self.reason})"


class AccountObservation:
    """One allowlist check. `selected` stays false."""

    __slots__ = ("decision", "quarantine", "selected")

    def __init__(
        self,
        result: AuthDecision,
        *,
        quarantine: AccountQuarantine | None,
    ) -> None:
        self.decision = result
        self.quarantine = quarantine
        self.selected = False

    def __repr__(self) -> str:
        return f"AccountObservation({self.decision.reason})"


class SimAccountAllowlist:
    """Explicit synthetic SIM ids. Observing an id does not add or select it."""

    __slots__ = ("_ids",)

    def __init__(self, account_ids: Iterable[str]) -> None:
        chosen: list[str] = []
        for account_id in account_ids:
            if type(account_id) is not str or _SYNTHETIC.fullmatch(account_id) is None:
                raise AuthModelError("MALFORMED_ACCOUNT")
            if account_id in chosen:
                raise AuthModelError("DUPLICATE_ACCOUNT")
            chosen.append(account_id)
        self._ids = frozenset(chosen)

    @property
    def selected_account(self) -> None:
        return None

    def __contains__(self, account_id: object) -> bool:
        return type(account_id) is str and account_id in self._ids

    def observe(
        self,
        account_id: object,
        *,
        environment: object,
        emitter: MonitoringEmitter | None = None,
    ) -> AccountObservation:
        result = _observe(self._ids, account_id, environment)
        label = "SIM" if _is_sim(environment) else "UNKNOWN"
        emit_auth_decision(emitter, result.decision, environment=label)
        return result


def _observe(
    allowed: frozenset[str],
    account_id: object,
    environment: object,
) -> AccountObservation:
    if not _well_formed(account_id):
        return _quarantine("MALFORMED_ACCOUNT", account_id)
    if not _is_sim(environment):
        return _quarantine("CROSS_ENVIRONMENT", account_id)
    if account_id not in allowed:
        return _quarantine("UNEXPECTED_ACCOUNT", account_id)
    return AccountObservation(
        decision(OutcomeCode.CLASSIFIED, "KNOWN_ACCOUNT"),
        quarantine=None,
    )


def _quarantine(reason: str, account_id: object) -> AccountObservation:
    return AccountObservation(
        decision(OutcomeCode.REJECTED, reason),
        quarantine=AccountQuarantine(reason, _digest(account_id)),
    )


def _well_formed(account_id: object) -> bool:
    return type(account_id) is str and _SYNTHETIC.fullmatch(account_id) is not None


def _is_sim(environment: object) -> bool:
    if environment is DeploymentEnvironment.SIM:
        return True
    return type(environment) is str and environment == "SIM"


def _digest(account_id: object) -> str:
    if type(account_id) is str:
        material = account_id.encode("utf-8")
    else:
        material = type(account_id).__name__.encode("ascii")
    return hashlib.sha256(material).hexdigest()
