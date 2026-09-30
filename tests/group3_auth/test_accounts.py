from __future__ import annotations

import hashlib
import socket

import pytest

from swingtrade.contracts.monitoring import NullMonitoringEmitter
from swingtrade.contracts.secret_refs import DeploymentEnvironment
from swingtrade.group3_auth import OutcomeCode, SimAccountAllowlist
from swingtrade.group3_auth.outcomes import AuthModelError

_KNOWN = "SYN_OK"


def _digest(material: bytes) -> str:
    return hashlib.sha256(material).hexdigest()


def test_constructor_rejects_malformed_and_duplicate_ids() -> None:
    with pytest.raises(AuthModelError) as malformed:
        SimAccountAllowlist(["12345678"])
    assert malformed.value.reason == "MALFORMED_ACCOUNT"
    assert "12345678" not in str(malformed.value)
    with pytest.raises(AuthModelError) as duplicate:
        SimAccountAllowlist([_KNOWN, _KNOWN])
    assert duplicate.value.reason == "DUPLICATE_ACCOUNT"
    assert _KNOWN not in str(duplicate.value)


def test_known_sim_account_is_classified_and_not_selected() -> None:
    allowlist = SimAccountAllowlist([_KNOWN])
    emitter = NullMonitoringEmitter()
    observation = allowlist.observe(_KNOWN, environment=DeploymentEnvironment.SIM, emitter=emitter)
    assert observation.decision.code is OutcomeCode.CLASSIFIED
    assert observation.decision.reason == "KNOWN_ACCOUNT"
    assert observation.decision.safe_to_retry is False
    assert observation.decision.network_permitted is False
    assert observation.quarantine is None
    assert observation.selected is False
    assert allowlist.selected_account is None
    assert emitter.conditions == []
    again = allowlist.observe(_KNOWN, environment="SIM")
    assert again.selected is False
    assert allowlist.selected_account is None
    assert _KNOWN in allowlist


def test_unexpected_account_is_quarantined_and_not_added() -> None:
    allowlist = SimAccountAllowlist([_KNOWN])
    emitter = NullMonitoringEmitter()
    unexpected = "SYN_OTHER"
    observation = allowlist.observe(
        unexpected,
        environment=DeploymentEnvironment.SIM,
        emitter=emitter,
    )
    assert observation.decision.code is OutcomeCode.REJECTED
    assert observation.decision.reason == "UNEXPECTED_ACCOUNT"
    assert observation.selected is False
    assert observation.quarantine is not None
    assert observation.quarantine.digest == _digest(unexpected.encode("utf-8"))
    assert unexpected not in repr(observation)
    assert unexpected not in repr(observation.quarantine)
    assert unexpected not in allowlist
    assert allowlist.selected_account is None
    assert _KNOWN in allowlist
    condition = emitter.conditions[0]
    assert condition.safe_context["reason"] == "UNEXPECTED_ACCOUNT"
    assert condition.safe_context["environment"] == "SIM"
    assert unexpected not in str(condition.safe_context)


@pytest.mark.parametrize(
    "account_id",
    ["", "12345678", " SYN_OK", "SYN_ok", "SYN_", "SYN_" + ("A" * 33), None, 12345, b"SYN_OK"],
)
def test_malformed_account_is_quarantined_without_the_raw_id(account_id: object) -> None:
    allowlist = SimAccountAllowlist([_KNOWN])
    observation = allowlist.observe(account_id, environment=DeploymentEnvironment.SIM)
    assert observation.decision.reason == "MALFORMED_ACCOUNT"
    assert observation.selected is False
    assert observation.quarantine is not None
    rendered = repr(observation) + repr(observation.quarantine)
    if isinstance(account_id, str) and account_id != "":
        assert account_id not in rendered
    if type(account_id) is str:
        expected = _digest(account_id.encode("utf-8"))
    else:
        expected = _digest(type(account_id).__name__.encode("ascii"))
    assert observation.quarantine.digest == expected
    assert allowlist.selected_account is None
    assert _KNOWN in allowlist


@pytest.mark.parametrize(
    "environment",
    [
        DeploymentEnvironment.LIVE,
        DeploymentEnvironment.DEV,
        DeploymentEnvironment.TEST,
        None,
        "sim",
        "LIVE",
        "",
    ],
)
def test_cross_environment_account_is_quarantined_even_when_listed(environment: object) -> None:
    allowlist = SimAccountAllowlist([_KNOWN])
    emitter = NullMonitoringEmitter()
    observation = allowlist.observe(_KNOWN, environment=environment, emitter=emitter)
    assert observation.decision.reason == "CROSS_ENVIRONMENT"
    assert observation.selected is False
    assert observation.quarantine is not None
    assert observation.quarantine.digest == _digest(_KNOWN.encode("utf-8"))
    assert _KNOWN not in repr(observation.quarantine)
    assert allowlist.selected_account is None
    assert emitter.conditions[0].safe_context["environment"] == "UNKNOWN"
    assert _KNOWN not in str(emitter.conditions[0].safe_context)


def test_account_checks_do_not_open_sockets(monkeypatch) -> None:
    def explode(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket")

    monkeypatch.setattr(socket, "socket", explode)
    monkeypatch.setattr(socket, "create_connection", explode)
    allowlist = SimAccountAllowlist(())
    observation = allowlist.observe(_KNOWN, environment=DeploymentEnvironment.SIM)
    assert observation.decision.reason == "UNEXPECTED_ACCOUNT"
    assert allowlist.selected_account is None
