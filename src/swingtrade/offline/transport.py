"""Offline transport seam. Naming a host does not open a socket or broker client."""

from __future__ import annotations

from swingtrade.contracts.monitoring import (
    MonitoringEmitter,
    broker_transport_unavailable,
)
from swingtrade.contracts.secret_refs import DeploymentEnvironment
from swingtrade.offline.environment import OfflineEnvironment
from swingtrade.offline.hosts import HostDecision, classify_api_host


class OfflineTransportError(RuntimeError):
    """Network I/O is outside the offline foundation."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class OfflineTransport:
    """A transport object with no send implementation."""

    __slots__ = ("_emitter", "environment", "host")

    def __init__(
        self,
        environment: DeploymentEnvironment,
        host: HostDecision | None,
        emitter: MonitoringEmitter | None,
    ) -> None:
        if environment is DeploymentEnvironment.LIVE:
            raise OfflineTransportError("LIVE_INITIALIZATION_DENIED")
        if host is not None and host.connect_allowed:
            raise OfflineTransportError("NETWORK_IO_PROHIBITED")
        self.environment = environment
        self.host = host
        self._emitter = emitter

    def send(self, method: str, path: str) -> None:
        if type(method) is not str or type(path) is not str:
            raise OfflineTransportError("NETWORK_IO_PROHIBITED")
        self._deny("NETWORK_IO_PROHIBITED")

    def _deny(self, reason: str) -> None:
        if self._emitter is not None:
            self._emitter.emit(
                broker_transport_unavailable(
                    "offline transport has no network I/O",
                    environment=self.environment.value,
                )
            )
        raise OfflineTransportError(reason)


def open_offline_transport(
    posture: OfflineEnvironment,
    host_url: str | None = None,
    *,
    emitter: MonitoringEmitter | None = None,
) -> OfflineTransport:
    """Bind a no-I/O transport. DEV and TEST reject every host."""
    if not isinstance(posture, OfflineEnvironment) or posture.network_allowed:
        raise OfflineTransportError("NETWORK_IO_PROHIBITED")
    if posture.environment in {DeploymentEnvironment.DEV, DeploymentEnvironment.TEST}:
        if host_url is not None:
            if emitter is not None:
                emitter.emit(
                    broker_transport_unavailable(
                        "DEV and TEST have no broker network",
                        environment=posture.environment.value,
                    )
                )
            raise OfflineTransportError("DEV_TEST_NETWORK_PROHIBITED")
        return OfflineTransport(posture.environment, None, emitter)
    if host_url is None:
        if emitter is not None:
            emitter.emit(
                broker_transport_unavailable(
                    "SIM transport requires a named host and still cannot connect",
                    environment=posture.environment.value,
                )
            )
        raise OfflineTransportError("MISSING_HOST")
    decision = classify_api_host(host_url, emitter=emitter)
    if decision.connect_allowed:
        raise OfflineTransportError("NETWORK_IO_PROHIBITED")
    return OfflineTransport(posture.environment, decision, emitter)
