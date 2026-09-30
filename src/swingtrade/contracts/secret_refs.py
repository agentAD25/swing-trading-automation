from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DeploymentEnvironment(StrEnum):
    DEV = "DEV"
    TEST = "TEST"
    SIM = "SIM"
    LIVE = "LIVE"


class SecretRefBindingError(ValueError):
    """Secret reference configuration violates the offline environment contract."""


_LIVE_DATABASE_REF_NAME = "SWINGTRADE_LIVE_DATABASE_URL_REF"


@dataclass(frozen=True)
class SecretRefSchema:
    """Configuration schema references only; values are never stored in code."""

    dev_database_url_ref: str = "SWINGTRADE_DEV_DATABASE_URL_REF"
    test_database_url_ref: str = "SWINGTRADE_TEST_DATABASE_URL_REF"
    sim_database_url_ref: str = "SWINGTRADE_SIM_DATABASE_URL_REF"
    live_database_url_ref: str = _LIVE_DATABASE_REF_NAME


_DEFAULT_SCHEMA = SecretRefSchema()

_ENVIRONMENT_REF_FIELD: dict[DeploymentEnvironment, str] = {
    DeploymentEnvironment.DEV: _DEFAULT_SCHEMA.dev_database_url_ref,
    DeploymentEnvironment.TEST: _DEFAULT_SCHEMA.test_database_url_ref,
    DeploymentEnvironment.SIM: _DEFAULT_SCHEMA.sim_database_url_ref,
    DeploymentEnvironment.LIVE: _DEFAULT_SCHEMA.live_database_url_ref,
}

_ALL_DATABASE_REF_NAMES = frozenset(_ENVIRONMENT_REF_FIELD.values())


def as_deployment_environment(environment: object) -> DeploymentEnvironment:
    """Return the enum member for an exact name. Unknown values do not become LIVE."""
    if type(environment) is DeploymentEnvironment:
        return environment
    if type(environment) is str:
        try:
            return DeploymentEnvironment(environment)
        except ValueError:
            raise SecretRefBindingError("unknown environment") from None
    raise SecretRefBindingError("unknown environment")


def configured_database_ref_name(
    environment: DeploymentEnvironment, schema: SecretRefSchema = _DEFAULT_SCHEMA
) -> str:
    resolved = as_deployment_environment(environment)
    if resolved is DeploymentEnvironment.LIVE:
        raise SecretRefBindingError("LIVE database references are prohibited")
    if resolved is DeploymentEnvironment.DEV:
        name = schema.dev_database_url_ref
    elif resolved is DeploymentEnvironment.TEST:
        name = schema.test_database_url_ref
    elif resolved is DeploymentEnvironment.SIM:
        name = schema.sim_database_url_ref
    else:
        raise SecretRefBindingError("unknown environment")
    if name == _LIVE_DATABASE_REF_NAME or name == schema.live_database_url_ref:
        raise SecretRefBindingError("LIVE database references are prohibited")
    return name


def validate_database_ref_binding(
    environment: DeploymentEnvironment,
    configured_refs: dict[str, str | None],
    *,
    schema: SecretRefSchema = _DEFAULT_SCHEMA,
) -> str:
    """Return the sole configured reference name for ``environment`` or fail closed."""
    resolved = as_deployment_environment(environment)
    if resolved is DeploymentEnvironment.LIVE:
        raise SecretRefBindingError("LIVE database references are prohibited")

    expected = configured_database_ref_name(resolved, schema)
    present = {
        name: value
        for name, value in configured_refs.items()
        if name in _ALL_DATABASE_REF_NAMES and value is not None
    }
    if "SWINGTRADE_DATABASE_URL" in configured_refs and configured_refs["SWINGTRADE_DATABASE_URL"]:
        raise SecretRefBindingError("generic DATABASE_URL source is prohibited")
    if resolved is DeploymentEnvironment.DEV or resolved is DeploymentEnvironment.TEST:
        if schema.sim_database_url_ref in present:
            raise SecretRefBindingError("DEV/TEST cannot select SIM database reference")
    if resolved is DeploymentEnvironment.SIM:
        for forbidden in (schema.dev_database_url_ref, schema.test_database_url_ref):
            if forbidden in present:
                raise SecretRefBindingError("SIM cannot fall back to DEV/TEST database reference")
    if expected not in present:
        raise SecretRefBindingError(f"missing required reference for {resolved.value}")
    if len(present) != 1:
        raise SecretRefBindingError("exactly one database reference must be configured")
    return expected
