"""Offline auth monitoring using the existing condition codes."""

from __future__ import annotations

from swingtrade.contracts.monitoring import (
    MonitoringEmitter,
    auth_configuration_failure,
    forbidden_host,
)
from swingtrade.group3_auth.outcomes import AuthDecision, OutcomeCode


def emit_auth_decision(
    emitter: MonitoringEmitter | None,
    result: AuthDecision,
    *,
    environment: str = "",
) -> None:
    """Emit one non-secret condition. Assembled templates are not alerts."""
    if emitter is None or result.code is OutcomeCode.ASSEMBLED:
        return
    if result.code is OutcomeCode.CLASSIFIED and result.reason != "ACCESS_DENIED":
        return
    context: dict[str, str] = {"outcome": result.code.value, "reason": result.reason}
    if environment in {"DEV", "TEST", "SIM", "LIVE", "UNKNOWN"}:
        context["environment"] = environment
    if result.reason == "LIVE_HOST_PROHIBITED":
        emitter.emit(forbidden_host("LIVE API host is prohibited", classification="LIVE"))
        return
    if result.code is OutcomeCode.UNKNOWN:
        summary = "authorization outcome is unknown"
    else:
        summary = "authorization input was not accepted"
    emitter.emit(auth_configuration_failure(summary, **context))
