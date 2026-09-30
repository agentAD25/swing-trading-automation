"""Explicit OAuth flow input. An absent or unknown mode is not a default."""

from __future__ import annotations

from enum import StrEnum


class FlowMode(StrEnum):
    STANDARD = "STANDARD"
    PKCE = "PKCE"


def parse_flow(value: object) -> FlowMode | None:
    if type(value) is FlowMode:
        return value
    if type(value) is str:
        try:
            return FlowMode(value)
        except ValueError:
            return None
    return None
