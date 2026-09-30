from __future__ import annotations

import ast
import socket
from pathlib import Path

import pytest

from swingtrade.contracts.monitoring import MonitoringConditionCode, NullMonitoringEmitter
from swingtrade.offline.environment import resolve_offline_environment
from swingtrade.offline.hosts import SIM_API_URL
from swingtrade.offline.transport import OfflineTransportError, open_offline_transport

OFFLINE_ROOT = Path("src/swingtrade/offline")
FORBIDDEN_MODULES = {
    "socket",
    "httpx",
    "requests",
    "http.client",
    "urllib.request",
    "websockets",
    "aiohttp",
    "supabase",
    "ftplib",
    "smtplib",
}


def test_offline_sources_have_no_network_client_or_float_literals() -> None:
    for path in sorted(OFFLINE_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                raise AssertionError(f"{path}:{node.lineno} uses a float")
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                if isinstance(node, ast.FunctionDef) and node.name in {
                    "submit_order",
                    "place_order",
                    "route_order",
                    "send_order",
                }:
                    raise AssertionError(node.name)
                continue
            forbidden = [
                name
                for name in names
                if name in FORBIDDEN_MODULES or name.split(".")[0] in FORBIDDEN_MODULES
            ]
            assert forbidden == []


def test_policy_operations_do_not_open_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*args: object, **kwargs: object) -> object:
        raise AssertionError("socket opened")

    monkeypatch.setattr(socket, "socket", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    posture = resolve_offline_environment("SIM")
    emitter = NullMonitoringEmitter()
    transport = open_offline_transport(posture, SIM_API_URL, emitter=emitter)
    assert transport.host is not None
    assert transport.host.connect_allowed is False
    with pytest.raises(OfflineTransportError, match="NETWORK_IO_PROHIBITED"):
        transport.send("GET", "/orders")
    assert emitter.conditions[-1].code is MonitoringConditionCode.BROKER_TRANSPORT_UNAVAILABLE


def test_dev_and_test_reject_any_host_without_connecting(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*args: object, **kwargs: object) -> object:
        raise AssertionError("socket opened")

    monkeypatch.setattr(socket, "create_connection", denied)
    emitter = NullMonitoringEmitter()
    for name in ("DEV", "TEST"):
        posture = resolve_offline_environment(name)
        transport = open_offline_transport(posture, emitter=emitter)
        with pytest.raises(OfflineTransportError, match="NETWORK_IO_PROHIBITED"):
            transport.send("GET", "/v3")
        with pytest.raises(OfflineTransportError, match="DEV_TEST_NETWORK_PROHIBITED"):
            open_offline_transport(posture, SIM_API_URL, emitter=emitter)
        with pytest.raises(OfflineTransportError, match="DEV_TEST_NETWORK_PROHIBITED"):
            open_offline_transport(posture, "https://api.tradestation.com/v3", emitter=emitter)


def test_sim_live_host_is_refused_before_a_transport_exists() -> None:
    posture = resolve_offline_environment("SIM")
    emitter = NullMonitoringEmitter()
    with pytest.raises(Exception, match="LIVE_HOST_PROHIBITED") as captured:
        open_offline_transport(
            posture,
            "https://user:supersecret@api.tradestation.com/v3",
            emitter=emitter,
        )
    assert "supersecret" not in str(captured.value)
    assert emitter.conditions[-1].code is MonitoringConditionCode.FORBIDDEN_HOST


def test_sim_without_a_host_fails_closed() -> None:
    posture = resolve_offline_environment("SIM")
    with pytest.raises(OfflineTransportError, match="MISSING_HOST"):
        open_offline_transport(posture, None)
