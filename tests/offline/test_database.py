from __future__ import annotations

import ast
from pathlib import Path

import pytest

from swingtrade.contracts.monitoring import MonitoringConditionCode, NullMonitoringEmitter
from swingtrade.contracts.secret_refs import (
    DeploymentEnvironment,
    SecretRefBindingError,
    SecretRefSchema,
    validate_database_ref_binding,
)
from swingtrade.offline import database as database_module
from swingtrade.offline.database import (
    DatabaseConnectionDenied,
    bind_database_reference,
    require_local_database_connection,
)

DEV_REFS = {"SWINGTRADE_DEV_DATABASE_URL_REF": "dev-ref"}
SIM_REFS = {"SWINGTRADE_SIM_DATABASE_URL_REF": "sim-ref"}


def test_database_module_delegates_selection_instead_of_forking_it() -> None:
    source = Path("src/swingtrade/offline/database.py").read_text()
    tree = ast.parse(source)
    defined = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    assert "validate_database_ref_binding" not in defined
    assert "SWINGTRADE_DEV_DATABASE_URL_REF" not in source
    assert "SWINGTRADE_SIM_DATABASE_URL_REF" not in source
    called: dict[str, object] = {}

    def fake(
        environment: DeploymentEnvironment,
        configured_refs: dict[str, str | None],
        *,
        schema: object = None,
    ) -> str:
        called["environment"] = environment
        called["refs"] = configured_refs
        return "SWINGTRADE_DEV_DATABASE_URL_REF"

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(database_module, "validate_database_ref_binding", fake)
    try:
        binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    finally:
        monkeypatch.undo()
    assert called == {"environment": DeploymentEnvironment.DEV, "refs": DEV_REFS}
    assert binding.reference_name == "SWINGTRADE_DEV_DATABASE_URL_REF"
    assert binding.connect_allowed is True


def test_valid_dev_binding_returns_the_contract_name_not_the_pointer() -> None:
    binding = bind_database_reference(DeploymentEnvironment.DEV, DEV_REFS)
    assert binding.reference_name == validate_database_ref_binding(
        DeploymentEnvironment.DEV, DEV_REFS
    )
    assert binding.reference_name == "SWINGTRADE_DEV_DATABASE_URL_REF"
    assert binding.connect_allowed is True
    require_local_database_connection(binding)


def test_dev_cannot_silently_select_sim() -> None:
    emitter = NullMonitoringEmitter()
    with pytest.raises(SecretRefBindingError, match="SIM"):
        bind_database_reference(
            DeploymentEnvironment.DEV,
            {
                "SWINGTRADE_DEV_DATABASE_URL_REF": "dev-ref",
                "SWINGTRADE_SIM_DATABASE_URL_REF": "sim-ref",
            },
            emitter=emitter,
        )
    assert emitter.conditions[-1].code is MonitoringConditionCode.DB_CONFIGURATION_MISMATCH


def test_sim_cannot_fall_back_to_local_dev_or_test() -> None:
    with pytest.raises(SecretRefBindingError, match="DEV/TEST"):
        bind_database_reference(
            DeploymentEnvironment.SIM,
            {
                "SWINGTRADE_SIM_DATABASE_URL_REF": "sim-ref",
                "SWINGTRADE_TEST_DATABASE_URL_REF": "test-ref",
            },
        )
    with pytest.raises(SecretRefBindingError, match="DEV/TEST"):
        bind_database_reference(DeploymentEnvironment.SIM, DEV_REFS)


def test_live_cannot_fall_back_to_sim() -> None:
    with pytest.raises(SecretRefBindingError, match="LIVE"):
        bind_database_reference(
            DeploymentEnvironment.LIVE,
            {
                "SWINGTRADE_LIVE_DATABASE_URL_REF": "live-ref",
                "SWINGTRADE_SIM_DATABASE_URL_REF": "sim-ref",
            },
        )


def test_generic_database_url_is_rejected_without_echoing_the_value() -> None:
    secret = "postgresql://user:supersecret@localhost/db"
    with pytest.raises(SecretRefBindingError, match="generic") as captured:
        bind_database_reference(
            DeploymentEnvironment.DEV,
            {
                "SWINGTRADE_DEV_DATABASE_URL_REF": "dev-ref",
                "SWINGTRADE_DATABASE_URL": secret,
            },
        )
    assert "supersecret" not in str(captured.value)


def test_sim_reference_can_be_named_but_cannot_connect() -> None:
    binding = bind_database_reference(DeploymentEnvironment.SIM, SIM_REFS)
    assert binding.reference_name == "SWINGTRADE_SIM_DATABASE_URL_REF"
    assert binding.connect_allowed is False
    with pytest.raises(DatabaseConnectionDenied, match="SIM_CONNECTION_PROHIBITED"):
        require_local_database_connection(binding)


@pytest.mark.parametrize("value", ["DEV", "TEST", "SIM", "LIVE", "live", "nope"])
def test_string_environments_do_not_select_the_live_reference(value: str) -> None:
    live_only = {"SWINGTRADE_LIVE_DATABASE_URL_REF": "live-ref"}
    with pytest.raises(SecretRefBindingError) as captured:
        bind_database_reference(value, live_only)
    assert "live-ref" not in str(captured.value)
    assert str(captured.value) != "SWINGTRADE_LIVE_DATABASE_URL_REF"


def test_dev_schema_alias_cannot_select_the_live_reference() -> None:
    schema = SecretRefSchema(dev_database_url_ref="SWINGTRADE_LIVE_DATABASE_URL_REF")
    with pytest.raises(SecretRefBindingError, match="LIVE") as captured:
        bind_database_reference(
            DeploymentEnvironment.DEV,
            {"SWINGTRADE_LIVE_DATABASE_URL_REF": "live-ref"},
            schema=schema,
        )
    rendered = str(captured.value)
    assert "SWINGTRADE_LIVE_DATABASE_URL_REF" not in rendered
    assert "live-ref" not in rendered
    assert "connect_allowed" not in rendered


def test_exact_string_dev_uses_the_dev_reference() -> None:
    binding = bind_database_reference("DEV", DEV_REFS)
    assert binding.environment is DeploymentEnvironment.DEV
    assert binding.reference_name == "SWINGTRADE_DEV_DATABASE_URL_REF"
    assert binding.connect_allowed is True
    require_local_database_connection(binding)


def test_exactly_one_reference_rule_is_unchanged() -> None:
    with pytest.raises(SecretRefBindingError, match="exactly one"):
        bind_database_reference(
            DeploymentEnvironment.TEST,
            {
                "SWINGTRADE_TEST_DATABASE_URL_REF": "test-ref",
                "SWINGTRADE_DEV_DATABASE_URL_REF": "dev-ref",
            },
        )
