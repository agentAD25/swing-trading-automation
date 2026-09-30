from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class MonitoringSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MonitoringConditionCode(StrEnum):
    """Stable offline condition codes aligned with P2_MONITORING_TAXONOMY.md."""

    AUTH_CONFIGURATION_FAILURE = "AUTH_CONFIGURATION_FAILURE"
    FORBIDDEN_HOST = "FORBIDDEN_HOST"
    UNKNOWN_ENVIRONMENT = "UNKNOWN_ENVIRONMENT"
    DTO_QUARANTINE = "DTO_QUARANTINE"
    UNKNOWN_BROKER_VALUE = "UNKNOWN_BROKER_VALUE"
    BROKER_TRANSPORT_UNAVAILABLE = "BROKER_TRANSPORT_UNAVAILABLE"
    DB_UNAVAILABLE = "DB_UNAVAILABLE"
    DB_CONFIGURATION_MISMATCH = "DB_CONFIGURATION_MISMATCH"


_TAXONOMY_REFERENCES: dict[MonitoringConditionCode, str] = {
    MonitoringConditionCode.AUTH_CONFIGURATION_FAILURE: "MON-AUT-001",
    MonitoringConditionCode.FORBIDDEN_HOST: "MON-BRK-001",
    MonitoringConditionCode.UNKNOWN_ENVIRONMENT: "MON-DB-001",
    MonitoringConditionCode.DTO_QUARANTINE: "MON-DTO-001",
    MonitoringConditionCode.UNKNOWN_BROKER_VALUE: "MON-DTO-003",
    MonitoringConditionCode.BROKER_TRANSPORT_UNAVAILABLE: "MON-BRK-001",
    MonitoringConditionCode.DB_UNAVAILABLE: "MON-DB-001",
    MonitoringConditionCode.DB_CONFIGURATION_MISMATCH: "MON-DB-001",
}


@dataclass(frozen=True)
class MonitoringCondition:
    code: MonitoringConditionCode
    severity: MonitoringSeverity
    summary: str
    readiness: bool = False
    safe_context: dict[str, str] = field(default_factory=dict)

    @property
    def taxonomy_reference(self) -> str:
        return _TAXONOMY_REFERENCES[self.code]


class MonitoringEmitter(Protocol):
    """Stable sink for structured monitoring conditions (no external alerting)."""

    def emit(self, condition: MonitoringCondition) -> None: ...


class NullMonitoringEmitter:
    """Default no-op emitter for offline tests and local wiring."""

    def __init__(self) -> None:
        self.conditions: list[MonitoringCondition] = []

    def emit(self, condition: MonitoringCondition) -> None:
        self.conditions.append(condition)


def auth_configuration_failure(summary: str, **context: str) -> MonitoringCondition:
    return MonitoringCondition(
        code=MonitoringConditionCode.AUTH_CONFIGURATION_FAILURE,
        severity=MonitoringSeverity.HIGH,
        summary=summary,
        safe_context=dict(context),
    )


def forbidden_host(summary: str, **context: str) -> MonitoringCondition:
    return MonitoringCondition(
        code=MonitoringConditionCode.FORBIDDEN_HOST,
        severity=MonitoringSeverity.CRITICAL,
        summary=summary,
        safe_context=dict(context),
    )


def unknown_environment(summary: str, **context: str) -> MonitoringCondition:
    return MonitoringCondition(
        code=MonitoringConditionCode.UNKNOWN_ENVIRONMENT,
        severity=MonitoringSeverity.HIGH,
        summary=summary,
        safe_context=dict(context),
    )


def dto_quarantine(summary: str, **context: str) -> MonitoringCondition:
    return MonitoringCondition(
        code=MonitoringConditionCode.DTO_QUARANTINE,
        severity=MonitoringSeverity.HIGH,
        summary=summary,
        safe_context=dict(context),
    )


def unknown_broker_value(summary: str, **context: str) -> MonitoringCondition:
    return MonitoringCondition(
        code=MonitoringConditionCode.UNKNOWN_BROKER_VALUE,
        severity=MonitoringSeverity.MEDIUM,
        summary=summary,
        safe_context=dict(context),
    )


def broker_transport_unavailable(summary: str, **context: str) -> MonitoringCondition:
    return MonitoringCondition(
        code=MonitoringConditionCode.BROKER_TRANSPORT_UNAVAILABLE,
        severity=MonitoringSeverity.HIGH,
        summary=summary,
        safe_context=dict(context),
    )


def db_unavailable(summary: str, **context: str) -> MonitoringCondition:
    return MonitoringCondition(
        code=MonitoringConditionCode.DB_UNAVAILABLE,
        severity=MonitoringSeverity.HIGH,
        summary=summary,
        safe_context=dict(context),
    )


def db_configuration_mismatch(summary: str, **context: str) -> MonitoringCondition:
    return MonitoringCondition(
        code=MonitoringConditionCode.DB_CONFIGURATION_MISMATCH,
        severity=MonitoringSeverity.HIGH,
        summary=summary,
        safe_context=dict(context),
    )
