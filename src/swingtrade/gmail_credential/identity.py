"""Gmail development credential identity. The target name is not a secret."""

from __future__ import annotations

from typing import Literal

CRED_TYPE_GENERIC: int = 1
CRED_PERSIST_SESSION: int = 1
CRED_PERSIST_LOCAL_MACHINE: int = 2
CRED_PERSIST_ENTERPRISE: int = 3

CANONICAL_TARGET: str = "swing-trading/lane3/gmail/dev/refresh-token"

# This gate has no native backend. Flipping the constant does not load one.
NATIVE_BACKEND_ENABLED: bool = False

TargetClass = Literal["canonical", "case_variant", "rejected"]


def classify_target(target: object) -> TargetClass:
    """Classify a public target without treating case variants as aliases."""
    if type(target) is not str or target == "":
        return "rejected"
    if target == CANONICAL_TARGET:
        return "canonical"
    if target.casefold() == CANONICAL_TARGET.casefold():
        return "case_variant"
    return "rejected"


def persistence_code(persist: object) -> str | None:
    """Return an error code when persistence is not local-machine, else None."""
    if type(persist) is not int:
        return "unsupported_persistence"
    if persist == CRED_PERSIST_LOCAL_MACHINE:
        return None
    if persist == CRED_PERSIST_ENTERPRISE:
        return "enterprise_persistence_rejected"
    return "unsupported_persistence"
