"""Validate caller-supplied synthetic fixtures and return immutable deliveries.

MIME bytes stay opaque. This module does not parse them, perform I/O, or
create an instruction, receipt, or order.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from swingtrade.group4_email.normalize import content_digest as _content_digest

_DELIVERY_REF = re.compile(r"^syn-delivery-[1-9][0-9]{0,5}$")


class SyntheticAcquisitionError(Exception):
    """Fail-closed acquisition error. The message is a stable code and nothing else."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or code == "":
            code = "fail_closed"
        super().__init__(code)
        self.code = code

    def __repr__(self) -> str:
        return f"SyntheticAcquisitionError({self.code!r})"

    def __str__(self) -> str:
        return self.code


@dataclass(frozen=True)
class SyntheticFixture:
    """Opaque synthetic payload. ``delivery_ref`` is not a message identity."""

    delivery_ref: str
    mime: bytes


@dataclass(frozen=True)
class SyntheticDelivery:
    """Immutable copy of one validated fixture plus the accepted content digest."""

    delivery_ref: str
    mime: bytes
    content_digest: str


def deliver_synthetic_fixtures(
    fixtures: tuple[SyntheticFixture, ...],
) -> tuple[SyntheticDelivery, ...]:
    """Validate the whole tuple, then return deliveries in caller order.

    A failure raises one stable code and produces no delivery. ``delivery_ref``
    is non-authoritative transport metadata.
    """

    if type(fixtures) is not tuple:
        raise SyntheticAcquisitionError("INVALID_FIXTURE")
    for fixture in fixtures:
        if type(fixture) is not SyntheticFixture or type(fixture.mime) is not bytes:
            raise SyntheticAcquisitionError("INVALID_FIXTURE")
    for fixture in fixtures:
        reference = fixture.delivery_ref
        if type(reference) is not str or _DELIVERY_REF.fullmatch(reference) is None:
            raise SyntheticAcquisitionError("INVALID_DELIVERY_REF")
    seen: set[str] = set()
    for fixture in fixtures:
        if fixture.delivery_ref in seen:
            raise SyntheticAcquisitionError("DUPLICATE_DELIVERY_REF")
        seen.add(fixture.delivery_ref)
    return tuple(
        SyntheticDelivery(
            delivery_ref=fixture.delivery_ref,
            mime=bytes(bytearray(fixture.mime)),
            content_digest=_content_digest(fixture.mime),
        )
        for fixture in fixtures
    )
