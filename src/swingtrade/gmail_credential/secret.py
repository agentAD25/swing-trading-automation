"""Explicit synthetic-secret capability. Content is not classified."""

from __future__ import annotations

from typing import NoReturn

from swingtrade.gmail_credential.errors import CredentialOperationError

_SYNTHETIC_CAPABILITY: object = object()


class SyntheticSecret:
    """Secret bytes issued only by :func:`synthetic_fixture`.

    The type is the deny-by-default boundary. Arbitrary bytes are not inspected
    to decide whether they look like an OAuth token.
    """

    __slots__ = ("_material",)

    def __init__(self, material: bytes, capability: object) -> None:
        if capability is not _SYNTHETIC_CAPABILITY:
            raise CredentialOperationError("non_synthetic_input")
        if type(material) is not bytes or len(material) == 0:
            raise CredentialOperationError("non_synthetic_input")
        self._material = bytes(material)

    def __repr__(self) -> str:
        return "SyntheticSecret(redacted)"

    def __str__(self) -> str:
        return "SyntheticSecret(redacted)"

    def __format__(self, format_spec: str) -> str:
        return "SyntheticSecret(redacted)"

    def __reduce__(self) -> NoReturn:
        raise CredentialOperationError("secret_export_rejected")

    def matches(self, other: object) -> bool:
        if type(other) is not SyntheticSecret:
            return False
        return self._material == other._material


def synthetic_fixture(material: bytes) -> SyntheticSecret:
    """Issue one synthetic fixture. This is not a real-token detector."""
    return SyntheticSecret(material, _SYNTHETIC_CAPABILITY)


def _material_of(secret: SyntheticSecret) -> bytes:
    return secret._material
