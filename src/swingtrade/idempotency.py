from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")
_TOKEN = re.compile(r"^[a-z0-9_]+$")


class IdempotencyConflict(RuntimeError):
    """A key was reused with different canonical business input."""


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def input_digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def idempotency_key(operation: str, scope: str, business_input: object) -> str:
    if not _TOKEN.fullmatch(operation) or not _TOKEN.fullmatch(scope):
        raise ValueError("operation and scope must be lowercase contract tokens")
    return f"v1:{operation}:{scope}:{input_digest(business_input)}"


@dataclass(frozen=True)
class IdempotencyRecord(Generic[T]):
    input_digest: str
    result: T


class InMemoryIdempotencyStore:
    """Test/local store; production persistence relies on a database unique key."""

    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord[Any]] = {}

    def execute(self, key: str, business_input: object, effect: Callable[[], T]) -> T:
        digest = input_digest(business_input)
        existing = self._records.get(key)
        if existing:
            if existing.input_digest != digest:
                raise IdempotencyConflict("idempotency key reused with different input")
            return existing.result
        result = effect()
        self._records[key] = IdempotencyRecord(digest, result)
        return result
