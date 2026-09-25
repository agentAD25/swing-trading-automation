"""Deterministic, broker-neutral swing-trading foundation."""

from swingtrade.config import RuntimeConfig
from swingtrade.domain import Bar, ExecutionMode, OrderIntent

__all__ = ["Bar", "ExecutionMode", "OrderIntent", "RuntimeConfig"]
