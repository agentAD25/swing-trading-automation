from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

import swingtrade
from swingtrade.config import RuntimeConfig, UnsafeRuntimeError
from swingtrade.domain import Bar, DomainValidationError, ExecutionMode, decimal_value


def test_package_imports() -> None:
    assert swingtrade.ExecutionMode.DRY_RUN == "DRY_RUN"


def test_decimal_rejects_binary_float() -> None:
    with pytest.raises(DomainValidationError, match="binary"):
        decimal_value(1.2)  # type: ignore[arg-type]


def test_bar_preserves_decimal() -> None:
    bar = Bar(
        "ins_1",
        "WDC",
        "1d",
        date(2024, 1, 2),
        "1.10",
        "1.30",
        "1.00",
        "1.20",
        "10",
        "USD",
        "fixture",
        1,
    )
    assert bar.close == Decimal("1.20")


def test_dry_run_config_is_accepted() -> None:
    assert RuntimeConfig(mode=ExecutionMode.DRY_RUN).mode is ExecutionMode.DRY_RUN


@pytest.mark.parametrize("mode", ["SIM", "LIVE_SHADOW", "LIVE"])
def test_unsafe_modes_fail_closed(mode: str) -> None:
    with pytest.raises((UnsafeRuntimeError, ValidationError), match="not authorized"):
        RuntimeConfig(mode=mode)


def test_missing_credentials_cannot_weaken_safety() -> None:
    with pytest.raises((UnsafeRuntimeError, ValidationError), match="not authorized"):
        RuntimeConfig(mode="LIVE", broker_credentials=None)


def test_broker_configuration_rejected_in_dry_run() -> None:
    with pytest.raises((UnsafeRuntimeError, ValidationError), match="prohibited"):
        RuntimeConfig(mode="DRY_RUN", broker_endpoint="https://example.invalid")


def test_lowercase_mode_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RuntimeConfig(mode="dry_run")
