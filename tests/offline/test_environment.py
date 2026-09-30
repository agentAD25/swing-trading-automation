from __future__ import annotations

import ast
from pathlib import Path

import pytest

from swingtrade.contracts.monitoring import MonitoringConditionCode, NullMonitoringEmitter
from swingtrade.contracts.secret_refs import DeploymentEnvironment
from swingtrade.offline.environment import (
    EnvironmentBoundaryError,
    require_deployment_environment,
    resolve_offline_environment,
)


def test_environment_enum_is_the_secret_ref_contract() -> None:
    source = Path("src/swingtrade/offline/environment.py").read_text()
    tree = ast.parse(source)
    defined = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    assert "DeploymentEnvironment" not in defined
    assert "SWINGTRADE_SIM_DATABASE_URL_REF" not in source
    assert require_deployment_environment("DEV") is DeploymentEnvironment.DEV


@pytest.mark.parametrize("value", ["DEV", "TEST", DeploymentEnvironment.SIM])
def test_known_non_live_environments_have_no_network(value: object) -> None:
    posture = resolve_offline_environment(value)
    assert posture.network_allowed is False
    assert posture.broker_credentials_allowed is False
    assert posture.credential_reference_name is None


def test_sim_may_name_a_future_credential_reference_without_enabling_network() -> None:
    posture = resolve_offline_environment(
        "SIM",
        credential_reference_name="SWINGTRADE_SIM_BROKER_CREDENTIAL_REF",
    )
    assert posture.environment is DeploymentEnvironment.SIM
    assert posture.network_allowed is False
    assert posture.broker_credentials_allowed is False
    assert posture.credential_reference_name == "SWINGTRADE_SIM_BROKER_CREDENTIAL_REF"


@pytest.mark.parametrize(
    "name",
    [
        "supersecret",
        "https://user:secret@example.invalid",
        "SWINGTRADE_SIM_DATABASE_URL_REF",
        "SWINGTRADE_SIM_TOKEN_REF",
        "SWINGTRADE_LIVE_BROKER_CREDENTIAL_REF",
        "",
    ],
)
def test_sim_rejects_non_opaque_credential_names(name: str) -> None:
    with pytest.raises(
        EnvironmentBoundaryError, match="CREDENTIAL_REFERENCE_PROHIBITED"
    ) as captured:
        resolve_offline_environment("SIM", credential_reference_name=name)
    if name:
        assert name not in str(captured.value)


def test_dev_and_test_reject_broker_credential_references() -> None:
    emitter = NullMonitoringEmitter()
    pasted = "supersecret-token"
    with pytest.raises(EnvironmentBoundaryError, match="BROKER_CREDENTIALS_PROHIBITED") as captured:
        resolve_offline_environment(
            "DEV",
            credential_reference_name="SWINGTRADE_SIM_BROKER_CREDENTIAL_REF",
            emitter=emitter,
        )
    assert pasted not in str(captured.value)
    assert emitter.conditions[-1].code is MonitoringConditionCode.AUTH_CONFIGURATION_FAILURE
    with pytest.raises(EnvironmentBoundaryError, match="BROKER_CREDENTIALS_PROHIBITED"):
        resolve_offline_environment("TEST", credential_reference_name=pasted)


@pytest.mark.parametrize("value", [None, "", "dev", "sim", "DRY_RUN", "LIVE_SHADOW", " DEV"])
def test_missing_or_unknown_environment_fails_closed(value: object) -> None:
    emitter = NullMonitoringEmitter()
    with pytest.raises(
        EnvironmentBoundaryError, match="MISSING_ENVIRONMENT|UNKNOWN_ENVIRONMENT"
    ) as captured:
        require_deployment_environment(value, emitter=emitter)
    assert "supersecret" not in str(captured.value)
    assert emitter.conditions[-1].code is MonitoringConditionCode.UNKNOWN_ENVIRONMENT


def test_unknown_environment_does_not_echo_the_supplied_value() -> None:
    pasted = "supersecret"
    with pytest.raises(EnvironmentBoundaryError, match="UNKNOWN_ENVIRONMENT") as captured:
        require_deployment_environment(pasted)
    assert pasted not in str(captured.value)


def test_live_initialization_fails_closed() -> None:
    emitter = NullMonitoringEmitter()
    with pytest.raises(EnvironmentBoundaryError, match="LIVE_INITIALIZATION_DENIED") as captured:
        resolve_offline_environment(
            "LIVE",
            credential_reference_name="supersecret",
            emitter=emitter,
        )
    assert "supersecret" not in str(captured.value)
    assert emitter.conditions[-1].code is MonitoringConditionCode.AUTH_CONFIGURATION_FAILURE


def test_permissive_posture_cannot_be_constructed() -> None:
    from swingtrade.offline.environment import OfflineEnvironment

    with pytest.raises(EnvironmentBoundaryError, match="NETWORK_OR_CREDENTIALS_PROHIBITED"):
        OfflineEnvironment(
            DeploymentEnvironment.DEV,
            network_allowed=True,
            broker_credentials_allowed=False,
            credential_reference_name=None,
        )
    with pytest.raises(EnvironmentBoundaryError, match="LIVE_INITIALIZATION_DENIED"):
        OfflineEnvironment(
            DeploymentEnvironment.LIVE,
            network_allowed=False,
            broker_credentials_allowed=False,
            credential_reference_name=None,
        )
