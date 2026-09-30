from __future__ import annotations

import pytest

from swingtrade.contracts.secret_refs import (
    DeploymentEnvironment,
    SecretRefBindingError,
    SecretRefSchema,
    configured_database_ref_name,
    validate_database_ref_binding,
)


def test_configured_database_ref_name_per_environment() -> None:
    assert configured_database_ref_name(DeploymentEnvironment.DEV) == (
        "SWINGTRADE_DEV_DATABASE_URL_REF"
    )
    assert configured_database_ref_name(DeploymentEnvironment.SIM) == (
        "SWINGTRADE_SIM_DATABASE_URL_REF"
    )


def test_live_database_ref_fails_closed() -> None:
    with pytest.raises(SecretRefBindingError, match="LIVE"):
        validate_database_ref_binding(
            DeploymentEnvironment.LIVE,
            {"SWINGTRADE_LIVE_DATABASE_URL_REF": "opaque-ref"},
        )


def test_dev_cannot_select_sim_reference() -> None:
    with pytest.raises(SecretRefBindingError, match="SIM"):
        validate_database_ref_binding(
            DeploymentEnvironment.DEV,
            {
                "SWINGTRADE_DEV_DATABASE_URL_REF": "dev-ref",
                "SWINGTRADE_SIM_DATABASE_URL_REF": "sim-ref",
            },
        )


def test_sim_cannot_fall_back_to_dev_reference() -> None:
    with pytest.raises(SecretRefBindingError, match="DEV/TEST"):
        validate_database_ref_binding(
            DeploymentEnvironment.SIM,
            {
                "SWINGTRADE_SIM_DATABASE_URL_REF": "sim-ref",
                "SWINGTRADE_DEV_DATABASE_URL_REF": "dev-ref",
            },
        )


def test_exactly_one_reference_required() -> None:
    with pytest.raises(SecretRefBindingError, match="missing required"):
        validate_database_ref_binding(DeploymentEnvironment.TEST, {})


def test_generic_database_url_rejected() -> None:
    with pytest.raises(SecretRefBindingError, match="generic"):
        validate_database_ref_binding(
            DeploymentEnvironment.DEV,
            {
                "SWINGTRADE_DEV_DATABASE_URL_REF": "dev-ref",
                "SWINGTRADE_DATABASE_URL": "postgresql://local",
            },
        )


@pytest.mark.parametrize("value", ["DEV", "TEST", "SIM", "LIVE", "live", "nope"])
def test_string_environment_does_not_fall_through_to_live_reference(value: str) -> None:
    with pytest.raises(SecretRefBindingError) as captured:
        validate_database_ref_binding(
            value,  # type: ignore[arg-type]
            {"SWINGTRADE_LIVE_DATABASE_URL_REF": "live-ref"},
        )
    assert "live-ref" not in str(captured.value)
    assert "SWINGTRADE_LIVE_DATABASE_URL_REF" not in str(captured.value)


def test_exact_dev_string_names_the_dev_reference() -> None:
    assert configured_database_ref_name("DEV") == "SWINGTRADE_DEV_DATABASE_URL_REF"  # type: ignore[arg-type]
    assert (
        validate_database_ref_binding(
            "DEV",  # type: ignore[arg-type]
            {"SWINGTRADE_DEV_DATABASE_URL_REF": "dev-ref"},
        )
        == "SWINGTRADE_DEV_DATABASE_URL_REF"
    )


@pytest.mark.parametrize(
    ("field", "environment"),
    [
        ("dev_database_url_ref", DeploymentEnvironment.DEV),
        ("test_database_url_ref", DeploymentEnvironment.TEST),
        ("sim_database_url_ref", DeploymentEnvironment.SIM),
    ],
)
def test_schema_slot_cannot_alias_the_live_reference(
    field: str, environment: DeploymentEnvironment
) -> None:
    schema = SecretRefSchema(**{field: "SWINGTRADE_LIVE_DATABASE_URL_REF"})
    with pytest.raises(SecretRefBindingError, match="LIVE") as captured:
        validate_database_ref_binding(
            environment,
            {"SWINGTRADE_LIVE_DATABASE_URL_REF": "live-ref"},
            schema=schema,
        )
    rendered = str(captured.value)
    assert "SWINGTRADE_LIVE_DATABASE_URL_REF" not in rendered
    assert "live-ref" not in rendered
    with pytest.raises(SecretRefBindingError, match="LIVE") as named:
        configured_database_ref_name(environment, schema)
    assert "SWINGTRADE_LIVE_DATABASE_URL_REF" not in str(named.value)


def test_valid_dev_binding_returns_expected_name() -> None:
    name = validate_database_ref_binding(
        DeploymentEnvironment.DEV,
        {"SWINGTRADE_DEV_DATABASE_URL_REF": "vault://dev/db"},
    )
    assert name == "SWINGTRADE_DEV_DATABASE_URL_REF"
