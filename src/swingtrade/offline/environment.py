"""Fail-closed deployment identity. Database-reference selection stays in secret refs."""

from __future__ import annotations

import re

from swingtrade.contracts.monitoring import (
    MonitoringCondition,
    MonitoringEmitter,
    auth_configuration_failure,
    unknown_environment,
)
from swingtrade.contracts.secret_refs import DeploymentEnvironment

_CREDENTIAL_REFERENCE = re.compile(r"^SWINGTRADE_SIM_[A-Z0-9_]{1,48}_REF$")
_CREDENTIAL_MARKERS = ("DATABASE", "URL", "LIVE", "TOKEN", "SECRET", "PASSWORD")


class EnvironmentBoundaryError(ValueError):
    """Missing, unknown, or unauthorized offline environment identity."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _emit(emitter: MonitoringEmitter | None, condition: MonitoringCondition) -> None:
    if emitter is not None:
        emitter.emit(condition)


def require_deployment_environment(
    value: object,
    *,
    emitter: MonitoringEmitter | None = None,
) -> DeploymentEnvironment:
    """Accept only DEV, TEST, or SIM. Missing, unknown, and LIVE fail closed."""
    if isinstance(value, DeploymentEnvironment):
        environment = value
    elif type(value) is str and value != "":
        try:
            environment = DeploymentEnvironment(value)
        except ValueError:
            _emit(
                emitter,
                unknown_environment("environment is unknown", classification="UNKNOWN"),
            )
            raise EnvironmentBoundaryError("UNKNOWN_ENVIRONMENT") from None
    else:
        _emit(
            emitter,
            unknown_environment("environment is missing", classification="MISSING"),
        )
        raise EnvironmentBoundaryError("MISSING_ENVIRONMENT")
    if environment is DeploymentEnvironment.LIVE:
        _emit(
            emitter,
            auth_configuration_failure(
                "LIVE initialization is denied",
                environment=DeploymentEnvironment.LIVE.value,
            ),
        )
        raise EnvironmentBoundaryError("LIVE_INITIALIZATION_DENIED")
    return environment


def _validate_credential_reference(name: str) -> None:
    if not _CREDENTIAL_REFERENCE.fullmatch(name) or any(
        marker in name for marker in _CREDENTIAL_MARKERS
    ):
        raise EnvironmentBoundaryError("CREDENTIAL_REFERENCE_PROHIBITED")


class OfflineEnvironment:
    """Network and broker credentials stay off. SIM may name a future reference only."""

    __slots__ = (
        "broker_credentials_allowed",
        "credential_reference_name",
        "environment",
        "network_allowed",
    )

    def __init__(
        self,
        environment: DeploymentEnvironment,
        *,
        network_allowed: bool,
        broker_credentials_allowed: bool,
        credential_reference_name: str | None,
    ) -> None:
        if environment is DeploymentEnvironment.LIVE:
            raise EnvironmentBoundaryError("LIVE_INITIALIZATION_DENIED")
        if network_allowed or broker_credentials_allowed:
            raise EnvironmentBoundaryError("NETWORK_OR_CREDENTIALS_PROHIBITED")
        if environment in {DeploymentEnvironment.DEV, DeploymentEnvironment.TEST}:
            if credential_reference_name is not None:
                raise EnvironmentBoundaryError("BROKER_CREDENTIALS_PROHIBITED")
        elif environment is DeploymentEnvironment.SIM:
            if credential_reference_name is not None:
                _validate_credential_reference(credential_reference_name)
        else:
            raise EnvironmentBoundaryError("UNKNOWN_ENVIRONMENT")
        self.environment = environment
        self.network_allowed = False
        self.broker_credentials_allowed = False
        self.credential_reference_name = credential_reference_name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OfflineEnvironment):
            return NotImplemented
        return (
            self.environment,
            self.network_allowed,
            self.broker_credentials_allowed,
            self.credential_reference_name,
        ) == (
            other.environment,
            other.network_allowed,
            other.broker_credentials_allowed,
            other.credential_reference_name,
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.environment,
                self.network_allowed,
                self.broker_credentials_allowed,
                self.credential_reference_name,
            )
        )


def resolve_offline_environment(
    value: object,
    *,
    credential_reference_name: str | None = None,
    emitter: MonitoringEmitter | None = None,
) -> OfflineEnvironment:
    environment = require_deployment_environment(value, emitter=emitter)
    try:
        return OfflineEnvironment(
            environment,
            network_allowed=False,
            broker_credentials_allowed=False,
            credential_reference_name=credential_reference_name,
        )
    except EnvironmentBoundaryError:
        _emit(
            emitter,
            auth_configuration_failure(
                "broker credentials are prohibited",
                environment=environment.value,
            ),
        )
        raise
