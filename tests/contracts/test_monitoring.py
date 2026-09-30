from __future__ import annotations

from swingtrade.contracts.monitoring import (
    MonitoringConditionCode,
    MonitoringSeverity,
    NullMonitoringEmitter,
    auth_configuration_failure,
    broker_transport_unavailable,
    db_configuration_mismatch,
    db_unavailable,
    dto_quarantine,
    forbidden_host,
    unknown_broker_value,
    unknown_environment,
)


def test_monitoring_condition_codes_are_stable() -> None:
    assert MonitoringConditionCode.DTO_QUARANTINE.value == "DTO_QUARANTINE"
    assert MonitoringConditionCode.FORBIDDEN_HOST.value == "FORBIDDEN_HOST"


def test_emitter_records_conditions_without_external_alerting() -> None:
    emitter = NullMonitoringEmitter()
    emitter.emit(forbidden_host("live host denied", policy_digest="abc"))
    emitter.emit(dto_quarantine("payload quarantined", payload_digest="def"))
    assert len(emitter.conditions) == 2
    assert emitter.conditions[0].severity is MonitoringSeverity.CRITICAL
    assert emitter.conditions[0].taxonomy_reference == "MON-BRK-001"
    assert emitter.conditions[1].code is MonitoringConditionCode.DTO_QUARANTINE


def test_factory_helpers_cover_required_conditions() -> None:
    factories = (
        auth_configuration_failure,
        forbidden_host,
        unknown_environment,
        dto_quarantine,
        unknown_broker_value,
        broker_transport_unavailable,
        db_unavailable,
        db_configuration_mismatch,
    )
    emitter = NullMonitoringEmitter()
    for factory in factories:
        emitter.emit(factory("summary", reason_code="safe"))
    assert len(emitter.conditions) == len(factories)
