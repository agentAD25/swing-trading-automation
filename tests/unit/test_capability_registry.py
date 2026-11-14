"""The public capability registry describes grants. It does not authorize them."""

from __future__ import annotations

import json
from pathlib import Path

REGISTRY = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "connectivity"
    / "capability-registry.json"
)

RUNTIME_KINDS = {"attended_diagnostic_grant", "execution_grant"}


def test_registry_cannot_authorize_runtime_access() -> None:
    document = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert document["authorizes_runtime"] is False
    assert document["registry_status_is_not_authorization"] is True
    names = [item["name"] for item in document["capabilities"]]
    assert names.count("LANE1_GMAIL_STANDING_READONLY_CONNECTION_AUTHORIZED") == 1
    assert "gmail.readonly" in json.dumps(document)
    assert "paper-api.alpaca.markets/v2/account" in json.dumps(document)
    assert "5432" not in json.dumps(document)
    for item in document["capabilities"]:
        if item["kind"] in RUNTIME_KINDS:
            assert item["authorization_status"] == "INACTIVE"
            assert item["approved_operations"] is not None
    order = next(
        item
        for item in document["capabilities"]
        if item["name"] == "LANE1_ALPACA_STANDING_PAPER_ORDER_AUTHORIZED"
    )
    assert order["approved_operations"] == []
