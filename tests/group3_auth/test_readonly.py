from __future__ import annotations

import ast
import socket
from pathlib import Path

from swingtrade.group3_auth import OutcomeCode, hold_raw, readonly_template
from swingtrade.offline.hosts import SIM_API_URL

_PACKAGE = Path("src/swingtrade/group3_auth")
_FORBIDDEN_MODULES = {
    "socket",
    "http",
    "httpx",
    "requests",
    "webbrowser",
    "urllib.request",
    "ftplib",
    "smtplib",
    "subprocess",
}


def test_sim_get_template_joins_one_v3_and_cannot_connect() -> None:
    template = readonly_template(path="/v3/brokerage/accounts/{accounts}/orders")
    assert template.decision.code is OutcomeCode.ASSEMBLED
    assert template.method == "GET"
    assert template.connect_allowed is False
    assert template.decision.network_permitted is False
    assert template.url == f"{SIM_API_URL}/brokerage/accounts/{{accounts}}/orders"
    assert template.url.count("/v3") == 1


def test_non_get_live_and_unknown_paths_fail_closed() -> None:
    post = readonly_template(method="POST", path="/v3/orderexecution/orders")
    assert post.decision.reason == "METHOD_REJECTED"
    assert post.url is None
    assert post.connect_allowed is False
    live = readonly_template(path="https://api.tradestation.com/v3/brokerage/accounts")
    assert live.decision.code is OutcomeCode.REJECTED
    assert live.url is None
    doubled = readonly_template(path="/v3/v3/brokerage/accounts")
    assert doubled.decision.reason == "MALFORMED_PATH"
    parent = readonly_template(path="/v3/brokerage/../accounts")
    assert parent.decision.reason == "MALFORMED_PATH"
    missing = readonly_template(path="/v2/brokerage/accounts")
    assert missing.decision.reason == "MALFORMED_PATH"


def test_status_text_stays_raw_and_unrecognized_catalog_is_unknown() -> None:
    raw = hold_raw(b'{"Status":"FLL","Status1":"ACK"}', "FLL")
    assert raw.body == b'{"Status":"FLL","Status1":"ACK"}'
    assert raw.status_text == "FLL"
    assert raw.status_catalog == "UNKNOWN"
    assert raw.decision.code is OutcomeCode.UNKNOWN
    assert raw.decision.safe_to_retry is False
    assert "FAILED" not in raw.decision.code


def test_templates_do_not_open_sockets(monkeypatch) -> None:
    def explode(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket")

    monkeypatch.setattr(socket, "socket", explode)
    monkeypatch.setattr(socket, "create_connection", explode)
    template = readonly_template(
        path="/v3/brokerage/accounts",
        query={"accounts": "synthetic"},
    )
    assert template.connect_allowed is False
    assert template.url == f"{SIM_API_URL}/brokerage/accounts?accounts=synthetic"


def test_package_has_no_socket_import_or_contract_stop() -> None:
    for path in _PACKAGE.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "P2_G3_CONTRACT_DECISION_REQUIRED" not in source
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name for alias in node.names}
                assert names.isdisjoint(_FORBIDDEN_MODULES)
            if isinstance(node, ast.ImportFrom) and node.module in _FORBIDDEN_MODULES:
                raise AssertionError(node.module)
            if isinstance(node, ast.FunctionDef) and node.name in {
                "send",
                "connect",
                "urlopen",
            }:
                raise AssertionError(node.name)
