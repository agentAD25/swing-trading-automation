"""Database connection gate over the secret-ref binding. It does not reselect references."""

from __future__ import annotations

from swingtrade.contracts.monitoring import MonitoringEmitter, db_configuration_mismatch
from swingtrade.contracts.secret_refs import (
    DeploymentEnvironment,
    SecretRefBindingError,
    SecretRefSchema,
    as_deployment_environment,
    validate_database_ref_binding,
)


class DatabaseConnectionDenied(RuntimeError):
    """A reference may be named, but this offline path must not connect."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class DatabaseBinding:
    """The reference name chosen by ``validate_database_ref_binding``."""

    __slots__ = ("connect_allowed", "environment", "reference_name")

    def __init__(
        self,
        environment: DeploymentEnvironment,
        reference_name: str,
        *,
        connect_allowed: bool,
    ) -> None:
        if type(environment) is not DeploymentEnvironment:
            raise DatabaseConnectionDenied("CONNECTION_PROHIBITED")
        local_dev_or_test = (
            environment is DeploymentEnvironment.DEV or environment is DeploymentEnvironment.TEST
        )
        if environment is DeploymentEnvironment.LIVE or connect_allowed is not local_dev_or_test:
            raise DatabaseConnectionDenied("CONNECTION_PROHIBITED")
        self.environment = environment
        self.reference_name = reference_name
        self.connect_allowed = connect_allowed


def _emit_binding_denied(emitter: MonitoringEmitter | None, environment_name: str) -> None:
    if emitter is not None:
        emitter.emit(
            db_configuration_mismatch(
                "database reference binding denied",
                environment=environment_name,
            )
        )


def bind_database_reference(
    environment: object,
    configured_refs: dict[str, str | None],
    *,
    schema: SecretRefSchema | None = None,
    emitter: MonitoringEmitter | None = None,
) -> DatabaseBinding:
    """Bind the single reference selected by the secret-ref contract."""
    try:
        resolved = as_deployment_environment(environment)
    except SecretRefBindingError:
        _emit_binding_denied(emitter, "UNKNOWN")
        raise
    try:
        if schema is None:
            reference_name = validate_database_ref_binding(resolved, configured_refs)
        else:
            reference_name = validate_database_ref_binding(
                resolved, configured_refs, schema=schema
            )
    except SecretRefBindingError:
        _emit_binding_denied(emitter, resolved.value)
        raise
    return DatabaseBinding(
        resolved,
        reference_name,
        connect_allowed=resolved is DeploymentEnvironment.DEV
        or resolved is DeploymentEnvironment.TEST,
    )


def require_local_database_connection(binding: DatabaseBinding) -> None:
    """DEV and TEST may use an isolated local fixture. SIM and LIVE cannot."""
    if not isinstance(binding, DatabaseBinding):
        raise DatabaseConnectionDenied("CONNECTION_PROHIBITED")
    if (
        binding.environment is DeploymentEnvironment.SIM or not binding.connect_allowed
    ):
        raise DatabaseConnectionDenied("SIM_CONNECTION_PROHIBITED")
    if (
        binding.environment is not DeploymentEnvironment.DEV
        and binding.environment is not DeploymentEnvironment.TEST
    ):
        raise DatabaseConnectionDenied("CONNECTION_PROHIBITED")
