from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from swingtrade.domain import ExecutionMode


class UnsafeRuntimeError(RuntimeError):
    """Startup configuration would exceed the authorized offline boundary."""


class RuntimeConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SWINGTRADE_",
        env_file=".env",
        extra="forbid",
        case_sensitive=True,
    )

    mode: ExecutionMode
    environment: str = "local"
    build_id: str = "development"
    database_url: str = "postgresql+psycopg://swingtrade:swingtrade@localhost:5432/swingtrade"
    broker_endpoint: str | None = None
    broker_account: str | None = None
    broker_credentials: str | None = Field(default=None, repr=False)

    @model_validator(mode="after")
    def enforce_offline_boundary(self) -> RuntimeConfig:
        if self.mode is not ExecutionMode.DRY_RUN:
            raise UnsafeRuntimeError(f"{self.mode.value} is not authorized")
        forbidden: dict[str, Any] = {
            "broker_endpoint": self.broker_endpoint,
            "broker_account": self.broker_account,
            "broker_credentials": self.broker_credentials,
        }
        supplied = sorted(name for name, value in forbidden.items() if value)
        if supplied:
            raise UnsafeRuntimeError(f"broker configuration is prohibited: {', '.join(supplied)}")
        return self
