import pytest

from swingtrade.idempotency import (
    IdempotencyConflict,
    InMemoryIdempotencyStore,
    idempotency_key,
)


def test_key_is_canonical_and_stable() -> None:
    left = idempotency_key("dispatch", "int_1", {"b": 2, "a": 1})
    right = idempotency_key("dispatch", "int_1", {"a": 1, "b": 2})
    assert left == right
    assert len(left.rsplit(":", 1)[1]) == 64


def test_duplicate_input_has_one_logical_effect() -> None:
    calls = 0
    store = InMemoryIdempotencyStore()

    def effect() -> dict[str, str]:
        nonlocal calls
        calls += 1
        return {"order_id": "dry_1"}

    key = idempotency_key("dispatch", "int_1", {"quantity": "2"})
    assert store.execute(key, {"quantity": "2"}, effect) == store.execute(
        key, {"quantity": "2"}, effect
    )
    assert calls == 1


def test_conflicting_key_reuse_is_rejected() -> None:
    store = InMemoryIdempotencyStore()
    key = idempotency_key("dispatch", "int_1", {"quantity": "2"})
    store.execute(key, {"quantity": "2"}, lambda: "first")
    with pytest.raises(IdempotencyConflict):
        store.execute(key, {"quantity": "3"}, lambda: "second")
