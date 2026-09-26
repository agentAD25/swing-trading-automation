from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

import swingtrade
import swingtrade.domain as domain
from swingtrade.config import RuntimeConfig, UnsafeRuntimeError
from swingtrade.domain import Bar, DomainValidationError, ExecutionMode, decimal_value


def test_package_imports() -> None:
    assert swingtrade.ExecutionMode.DRY_RUN == "DRY_RUN"


def test_decimal_rejects_binary_float() -> None:
    with pytest.raises(DomainValidationError, match="exactly Decimal or str"):
        decimal_value(1.2)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [True, False, 1, 0, None, object()],
)
def test_decimal_boundary_rejects_non_declared_runtime_types(value: object) -> None:
    with pytest.raises(DomainValidationError, match="exactly Decimal or str"):
        decimal_value(value)  # type: ignore[arg-type]


def test_decimal_boundary_rejects_custom_coercible_and_subclass_types() -> None:
    class Coercible:
        def __str__(self) -> str:
            raise AssertionError("custom coercion must not run")

    class DecimalSubclass(Decimal):
        pass

    class StringSubclass(str):
        pass

    for value in (Coercible(), DecimalSubclass("2"), StringSubclass("2")):
        with pytest.raises(DomainValidationError, match="exactly Decimal or str"):
            decimal_value(value)  # type: ignore[arg-type]


def test_decimal_boundary_accepts_only_exact_declared_types() -> None:
    assert decimal_value(Decimal("2.00")) == Decimal("2.00")
    assert decimal_value("2.00") == Decimal("2.00")


@pytest.mark.parametrize(
    "raw",
    [
        "9" * 1_000_000,
        "0." + "9" * 1_000_000,
        "1e" + "9" * 1_000_000,
        "9" * 1001,
        "1e1000000",
        " 2",
        "2 ",
        "+ 2",
        "1_0",
        "1.2.3",
        "1e",
        "1e+",
        "--2",
        "",
    ],
)
def test_oversized_or_malformed_string_never_enters_decimal_constructor(
    monkeypatch: pytest.MonkeyPatch, raw: str
) -> None:
    constructor_called = False

    def forbidden_constructor(value: object) -> Decimal:
        nonlocal constructor_called
        constructor_called = True
        raise AssertionError("Decimal constructor must not be called")

    monkeypatch.setattr(domain, "Decimal", forbidden_constructor)
    with pytest.raises(DomainValidationError) as captured:
        decimal_value(raw)
    assert not constructor_called
    assert len(str(captured.value)) < 300
    assert raw not in str(captured.value)


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
