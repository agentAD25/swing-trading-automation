"""SIM-base GET templates. The URL is named and connection stays denied."""

from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import quote, urlencode, urlsplit

from swingtrade.contracts.monitoring import MonitoringEmitter
from swingtrade.group3_auth.monitoring import emit_auth_decision
from swingtrade.group3_auth.outcomes import AuthDecision, OutcomeCode, decision
from swingtrade.offline.hosts import SIM_API_URL

_LIVE_HOSTNAME = "api.tradestation.com"


class ReadTemplate:
    """One GET URL under the SIM base. `connect_allowed` is false."""

    __slots__ = ("connect_allowed", "decision", "method", "query_names", "url")

    def __init__(
        self,
        result: AuthDecision,
        *,
        method: str,
        url: str | None,
        query_names: tuple[str, ...],
    ) -> None:
        self.decision = result
        self.method = method
        self.url = url
        self.query_names = query_names
        self.connect_allowed = False

    def __repr__(self) -> str:
        return "ReadTemplate"


class RawRead:
    """Response bytes and status text kept raw. No status catalog is selected."""

    __slots__ = ("body", "decision", "status_catalog", "status_text")

    def __init__(self, result: AuthDecision, body: bytes, status_text: str) -> None:
        self.decision = result
        self.body = body
        self.status_text = status_text
        self.status_catalog = "UNKNOWN"

    def __repr__(self) -> str:
        return "RawRead"


def readonly_template(
    *,
    method: object = "GET",
    path: object,
    query: Mapping[str, object] | None = None,
    emitter: MonitoringEmitter | None = None,
) -> ReadTemplate:
    """Join a `/v3` path to the SIM base once. Non-GET and unknown paths fail closed."""
    result = _readonly(method=method, path=path, query=query)
    emit_auth_decision(emitter, result.decision)
    return result


def hold_raw(
    body: object,
    status_text: object,
    *,
    emitter: MonitoringEmitter | None = None,
) -> RawRead:
    """Keep bytes and status text. Unrecognized status text stays `UNKNOWN`."""
    if type(body) is not bytes:
        result = RawRead(decision(OutcomeCode.REJECTED, "MALFORMED_RESPONSE"), b"", "")
    elif type(status_text) is not str:
        result = RawRead(decision(OutcomeCode.UNKNOWN, "UNKNOWN"), body, "")
    else:
        result = RawRead(decision(OutcomeCode.UNKNOWN, "UNKNOWN"), body, status_text)
    emit_auth_decision(emitter, result.decision)
    return result


def _readonly(
    *,
    method: object,
    path: object,
    query: Mapping[str, object] | None,
) -> ReadTemplate:
    if method != "GET":
        return _empty(decision(OutcomeCode.REJECTED, "METHOD_REJECTED"))
    if type(path) is not str or not path.startswith("/v3/"):
        return _empty(decision(OutcomeCode.REJECTED, "MALFORMED_PATH"))
    if _path_rejected(path):
        return _empty(decision(OutcomeCode.REJECTED, "MALFORMED_PATH"))
    suffix = path[len("/v3") :]
    if suffix.startswith("/v3/") or suffix == "/v3":
        return _empty(decision(OutcomeCode.REJECTED, "MALFORMED_PATH"))
    url = SIM_API_URL + suffix
    if not url.startswith(SIM_API_URL + "/"):
        return _empty(decision(OutcomeCode.REJECTED, "MALFORMED_PATH"))
    host = urlsplit(url).hostname
    if host == _LIVE_HOSTNAME:
        return _empty(decision(OutcomeCode.REJECTED, "LIVE_HOST_PROHIBITED"))
    if host != "sim-api.tradestation.com":
        return _empty(decision(OutcomeCode.REJECTED, "UNKNOWN_HOST"))
    if query is None:
        return ReadTemplate(
            decision(OutcomeCode.ASSEMBLED, "READ_TEMPLATE"),
            method="GET",
            url=url,
            query_names=(),
        )
    if not isinstance(query, Mapping):
        return _empty(decision(OutcomeCode.REJECTED, "MALFORMED_QUERY"))
    pairs: list[tuple[str, str]] = []
    for key, value in query.items():
        if type(key) is not str or type(value) is not str or key == "" or value == "":
            return _empty(decision(OutcomeCode.REJECTED, "MALFORMED_QUERY"))
        if any(ord(character) < 32 for character in key + value):
            return _empty(decision(OutcomeCode.REJECTED, "MALFORMED_QUERY"))
        pairs.append((key, value))
    encoded = urlencode(pairs, quote_via=quote)
    return ReadTemplate(
        decision(OutcomeCode.ASSEMBLED, "READ_TEMPLATE"),
        method="GET",
        url=f"{url}?{encoded}",
        query_names=tuple(name for name, _value in pairs),
    )


def _path_rejected(path: str) -> bool:
    if "\\" in path or "://" in path or path.startswith("//"):
        return True
    if any(character.isspace() or ord(character) < 32 for character in path):
        return True
    parts = path.split("/")
    if not parts or parts[0] != "":
        return True
    return any(segment in {"", ".", ".."} for segment in parts[1:])


def _empty(result: AuthDecision) -> ReadTemplate:
    return ReadTemplate(result, method="GET", url=None, query_names=())
