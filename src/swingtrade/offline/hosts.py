"""SIM API host naming. The LIVE host is prohibited and nothing here connects."""

from __future__ import annotations

import unicodedata
from enum import StrEnum
from urllib.parse import unquote, urlsplit

from swingtrade.contracts.monitoring import MonitoringEmitter, forbidden_host

SIM_API_URL = "https://sim-api.tradestation.com/v3"
_LIVE_HOSTNAME = "api.tradestation.com"
_MAX_HOST_INPUT = 2048
_IGNORED_CATEGORIES = frozenset({"Cf", "Cc", "Zs"})


class ApiHostClass(StrEnum):
    SIM = "SIM"


class HostPolicyError(RuntimeError):
    """The host is unknown or is a prohibited LIVE API host."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class HostDecision:
    """The single nameable SIM API URL. Connection stays denied."""

    __slots__ = ("canonical_url", "connect_allowed", "host_class")

    def __init__(
        self,
        host_class: ApiHostClass,
        canonical_url: str,
        connect_allowed: bool,
    ) -> None:
        if host_class is not ApiHostClass.SIM or canonical_url != SIM_API_URL or connect_allowed:
            raise HostPolicyError("UNKNOWN_HOST")
        self.host_class = host_class
        self.canonical_url = canonical_url
        self.connect_allowed = False


def _emit(emitter: MonitoringEmitter | None, *, classification: str, summary: str) -> None:
    if emitter is not None:
        emitter.emit(forbidden_host(summary, classification=classification))


def _strip_ignored(value: str) -> str:
    return "".join(
        character
        for character in value
        if unicodedata.category(character) not in _IGNORED_CATEGORIES
    )


def _variants(raw: str) -> set[str]:
    seeds = {raw, raw.strip(), raw.replace("\\", "/"), _strip_ignored(raw)}
    variants = set(seeds)
    for seed in seeds:
        for form in ("NFC", "NFD", "NFKC", "NFKD"):
            variants.add(unicodedata.normalize(form, seed))
    expanded = set(variants)
    for variant in variants:
        expanded.add(variant.replace("\\", "/"))
        expanded.add(_strip_ignored(variant))
    return expanded


def _prepare(variant: str) -> str:
    normalized = unicodedata.normalize("NFKC", variant).replace("\\", "/")
    if "://" in normalized or normalized.startswith("//"):
        return normalized
    return f"//{normalized}"


def _hostnames(raw: str) -> set[str]:
    hosts: set[str] = set()
    for variant in _variants(raw):
        try:
            host = urlsplit(_prepare(variant)).hostname
        except ValueError:
            continue
        if host is None:
            continue
        decoded = unquote(host).rstrip(".").lower()
        hosts.add(unicodedata.normalize("NFKC", decoded).rstrip(".").lower())
    return hosts


def _is_prohibited_live_host(raw: str) -> bool:
    return _LIVE_HOSTNAME in _hostnames(raw)


def classify_api_host(
    raw: object,
    *,
    emitter: MonitoringEmitter | None = None,
) -> HostDecision:
    """Return the exact SIM API host, or fail closed without normalizing into it."""
    if type(raw) is not str or raw == "" or len(raw) > _MAX_HOST_INPUT:
        _emit(emitter, classification="UNKNOWN", summary="unknown API host")
        raise HostPolicyError("UNKNOWN_HOST")
    if raw == SIM_API_URL:
        return HostDecision(ApiHostClass.SIM, SIM_API_URL, False)
    try:
        prohibited = _is_prohibited_live_host(raw)
    except ValueError:
        prohibited = False
    if prohibited:
        _emit(emitter, classification="LIVE", summary="LIVE API host is prohibited")
        raise HostPolicyError("LIVE_HOST_PROHIBITED")
    _emit(emitter, classification="UNKNOWN", summary="unknown API host")
    raise HostPolicyError("UNKNOWN_HOST")
