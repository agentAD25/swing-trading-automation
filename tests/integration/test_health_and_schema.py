from fastapi.testclient import TestClient

from swingtrade.api import create_app
from swingtrade.config import RuntimeConfig
from swingtrade.persistence import Base


def test_health_exposes_only_authorized_mode() -> None:
    client = TestClient(create_app(RuntimeConfig(mode="DRY_RUN")))
    assert client.get("/health").json() == {"status": "ok", "mode": "DRY_RUN"}


def test_minimal_persistence_schema_has_unique_boundaries() -> None:
    assert set(Base.metadata.tables) == {
        "domain_events",
        "idempotency_records",
        "outbox_items",
    }
    assert Base.metadata.tables["outbox_items"].c.idempotency_key.unique
