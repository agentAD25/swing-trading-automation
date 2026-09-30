from __future__ import annotations

import unicodedata

import pytest

from swingtrade.contracts.monitoring import MonitoringConditionCode, NullMonitoringEmitter
from swingtrade.offline.hosts import SIM_API_URL, HostPolicyError, classify_api_host


def _fullwidth(text: str) -> str:
    return "".join(
        chr(ord(character) + 0xFEE0) if "!" <= character <= "~" else character
        for character in text
    )


def test_exact_sim_host_is_named_and_cannot_connect() -> None:
    decision = classify_api_host(SIM_API_URL)
    assert decision.canonical_url == "https://sim-api.tradestation.com/v3"
    assert decision.connect_allowed is False
    assert decision.host_class.value == "SIM"


@pytest.mark.parametrize(
    "raw",
    [
        "https://api.tradestation.com/v3",
        "HTTPS://API.TRADESTATION.COM/v3",
        "https://api.tradestation.com/V3",
        "https://api.tradestation.com/v3/",
        "https://api.tradestation.com/v3/orders",
        "https://api.tradestation.com/v3/../v3",
        "https://api.tradestation.com:443/v3",
        "https://api.tradestation.com:8443/v3",
        "https://user:supersecret@api.tradestation.com/v3",
        "http://api.tradestation.com/v3",
        "//api.tradestation.com/v3",
        "api.tradestation.com/v3",
        "https://api.tradestation.com./v3",
        "https://api.tradestation.com/v3?leak=supersecret",
        "https://api.tradestation.com/v3#supersecret",
        "https://api.tradestation.com\\v3",
        " https://api.tradestation.com/v3 ",
        "https://api.tradestation.com/v3".replace("api", "api\u200b"),
        _fullwidth("https://api.tradestation.com/v3"),
        unicodedata.normalize("NFD", "https://api.tradestation.com/v3"),
        unicodedata.normalize("NFKC", "https://api.tradestation.com/v3"),
    ],
)
def test_live_host_forms_are_prohibited_without_echoing_userinfo(raw: str) -> None:
    emitter = NullMonitoringEmitter()
    with pytest.raises(HostPolicyError, match="LIVE_HOST_PROHIBITED") as captured:
        classify_api_host(raw, emitter=emitter)
    rendered = str(captured.value)
    assert "supersecret" not in rendered
    assert raw not in rendered
    assert emitter.conditions[-1].code is MonitoringConditionCode.FORBIDDEN_HOST
    assert emitter.conditions[-1].safe_context == {"classification": "LIVE"}


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "https://sim-api.tradestation.com/v3/",
        "https://sim-api.tradestation.com/v3/orders",
        "https://SIM-API.tradestation.com/v3",
        "https://sim-api.tradestation.com:443/v3",
        "http://sim-api.tradestation.com/v3",
        "https://sim-api.tradestation.com/v3?x=1",
        "https://notapi.tradestation.com/v3",
        "https://example.invalid/v3",
        "https://api.tradestation.com.evil.example/v3",
        _fullwidth(SIM_API_URL),
        SIM_API_URL + "\u200b",
        None,
        1,
    ],
)
def test_unknown_hosts_fail_closed(raw: object) -> None:
    emitter = NullMonitoringEmitter()
    with pytest.raises(HostPolicyError, match="UNKNOWN_HOST") as captured:
        classify_api_host(raw, emitter=emitter)
    assert SIM_API_URL not in str(captured.value) or raw == ""
    assert emitter.conditions[-1].safe_context["classification"] == "UNKNOWN"


def test_normalization_cannot_turn_a_lookalike_into_the_sim_allowlist() -> None:
    lookalike = _fullwidth(SIM_API_URL)
    assert unicodedata.normalize("NFKC", lookalike) == SIM_API_URL
    with pytest.raises(HostPolicyError, match="UNKNOWN_HOST"):
        classify_api_host(lookalike)
