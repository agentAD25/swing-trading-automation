"""Offline paper account read. No credential is loaded and no request is sent.

A scripted exchange may run once. The seven Gate C2 flags stay closed.
Importing this module does not retrieve a credential or contact a provider.
"""

from __future__ import annotations

from enum import StrEnum

from swingtrade.alpaca_paper_boundary import (
    PAPER_HOST,
    BoundaryClassification,
    evaluate_paper_boundary,
)
from swingtrade.alpaca_paper_custody import PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET

ACCOUNT_PATH = "/v2/account"
ACCOUNT_URL = f"https://{PAPER_HOST}{ACCOUNT_PATH}"
_LIVE_TARGET_PREFIX = "swing-trading/lane2/alpaca/live/"
_PAPER_TARGETS = (PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET)
_ACCEPTED_CURRENCY = "USD"
_STATUSES = frozenset(
    {
        "ONBOARDING",
        "SUBMISSION_FAILED",
        "SUBMITTED",
        "ACCOUNT_UPDATED",
        "APPROVAL_PENDING",
        "ACTIVE",
        "REJECTED",
    }
)
_REQUIRED = (
    "id",
    "account_number",
    "status",
    "currency",
    "trading_blocked",
    "account_blocked",
    "trade_suspended_by_user",
)
_DOCUMENTED = frozenset(
    {
        *_REQUIRED,
        "crypto_status",
        "cash",
        "portfolio_value",
        "non_marginable_buying_power",
        "accrued_fees",
        "pending_transfer_in",
        "pending_transfer_out",
        "transfers_blocked",
        "created_at",
        "shorting_enabled",
        "long_market_value",
        "short_market_value",
        "equity",
        "last_equity",
        "multiplier",
        "buying_power",
        "initial_margin",
        "maintenance_margin",
        "sma",
        "last_maintenance_margin",
        "regt_buying_power",
    }
)
_MISSING = object()
_FAULTS = frozenset({"ambiguous", "inconsistent", "incomplete", "malformed", "env-fallback"})


class ReadClassification(StrEnum):
    """Observation label. Neither value permits a provider call."""

    ACCEPTED = "ACCEPTED"
    DENIED = "DENIED"


class AccountReadDecision:
    """One scripted observation. Every action flag stays closed."""

    __slots__ = ("classification", "reason")

    def __init__(self, classification: ReadClassification, reason: str) -> None:
        self.classification = classification
        self.reason = reason

    @property
    def connect_allowed(self) -> bool:
        return False

    @property
    def network_permitted(self) -> bool:
        return False

    @property
    def submit_permitted(self) -> bool:
        return False

    @property
    def cancel_permitted(self) -> bool:
        return False

    @property
    def replace_permitted(self) -> bool:
        return False

    @property
    def resubmit_permitted(self) -> bool:
        return False

    @property
    def safe_to_retry(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"AccountReadDecision({self.classification.value}, {self.reason})"

    def __str__(self) -> str:
        return self.reason


class AccountReadError(RuntimeError):
    """Reason code only. Bytes and response bodies are not included."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        self.decision = AccountReadDecision(ReadClassification.DENIED, reason)
        super().__init__(reason)


class SyntheticCredentials:
    """Scripted custody evidence. Bytes stay inside this object."""

    __slots__ = ("_denial", "_entries")

    def __init__(self, entries: object = None, *, fault: object = None) -> None:
        self._entries: dict[str, bytes] = {}
        self._denial = _credential_denial(entries, fault)
        if self._denial is None and isinstance(entries, dict):
            self._entries = {
                name: value
                for name, value in entries.items()
                if isinstance(name, str) and isinstance(value, bytes)
            }

    def __repr__(self) -> str:
        if self._denial is not None:
            return f"SyntheticCredentials({self._denial})"
        return f"SyntheticCredentials({','.join(sorted(self._entries))})"

    def __str__(self) -> str:
        return repr(self)


class ScriptedExchange:
    """One scripted result. The body is never rendered."""

    __slots__ = ("_body", "fault", "redirected", "status")

    def __init__(
        self,
        *,
        status: object = 200,
        redirected: object = False,
        fault: object = None,
        body: object = _MISSING,
    ) -> None:
        self.status = status
        self.redirected = redirected
        self.fault = fault
        self._body = body

    def __repr__(self) -> str:
        return "ScriptedExchange()"

    def __str__(self) -> str:
        return "ScriptedExchange()"


class SyntheticTransport:
    """In-process script. ``exchange`` does not leave the interpreter."""

    __slots__ = ("_exchange", "calls")

    def __init__(self, exchange: object) -> None:
        if type(exchange) is not ScriptedExchange:
            raise AccountReadError("MALFORMED_TRANSPORT")
        self._exchange = exchange
        self.calls = 0

    def exchange(self) -> ScriptedExchange:
        self.calls += 1
        if self._exchange.fault == "exception":
            raise RuntimeError("TRANSPORT_EXCEPTION")
        return self._exchange

    def __repr__(self) -> str:
        return f"SyntheticTransport(calls={self.calls})"


class ReadSession:
    """One scripted account read. A later attempt is closed."""

    __slots__ = ("_exchanged",)

    def __init__(self) -> None:
        self._exchanged = False


def retrieve_paper_credentials() -> None:
    """Reserved for a later attended grant. It performs no retrieval."""
    raise AccountReadError("RUNTIME_UNAUTHORIZED")


def perform_paper_get() -> None:
    """Reserved for a later attended grant. It performs no request."""
    raise AccountReadError("RUNTIME_UNAUTHORIZED")


def read_account(
    session: object,
    credentials: object,
    transport: object,
    *,
    method: object = "GET",
    url: object = ACCOUNT_URL,
) -> AccountReadDecision:
    """Observe one scripted paper account read, or fail closed."""
    current = _require_session(session)
    if current._exchanged:
        raise AccountReadError("RETRY_DENIED")
    request_reason = _request_reason(method, url)
    if request_reason is not None:
        raise AccountReadError(request_reason)
    _require_credentials(credentials)
    scripted = _require_transport(transport)
    current._exchanged = True
    try:
        outcome = scripted.exchange()
    except RuntimeError:
        raise AccountReadError("TRANSPORT_EXCEPTION") from None
    return _interpret(outcome)


def _require_session(session: object) -> ReadSession:
    if type(session) is not ReadSession:
        raise AccountReadError("MALFORMED_SESSION")
    return session


def _request_reason(method: object, url: object) -> str | None:
    decision = evaluate_paper_boundary(url, method)
    if decision.classification is not BoundaryClassification.PAPER_POLICY_CANDIDATE:
        if decision.reason == "PATH_DENIED" and isinstance(url, str):
            special = _special_path(url)
            if special is not None:
                return special
        return decision.reason
    if not isinstance(url, str) or _path(url) != ACCOUNT_PATH:
        return _special_path(url) if isinstance(url, str) else "PATH_DENIED"
    if url != ACCOUNT_URL:
        return "HOST_DENIED"
    return None


def _special_path(url: str) -> str | None:
    folded = url.casefold()
    if "stream" in folded or "/events" in folded:
        return "STREAM_ROUTE_DENIED"
    if "/v2/orders" in folded:
        return "ORDER_ROUTE_DENIED"
    if "/v2/positions" in folded:
        return "POSITION_ROUTE_DENIED"
    return "PATH_DENIED"


def _path(url: str) -> str:
    remainder = url.split("://", 1)[1]
    slash = remainder.find("/")
    if slash < 0:
        return ""
    return remainder[slash:]


def _require_credentials(credentials: object) -> None:
    if type(credentials) is not SyntheticCredentials:
        raise AccountReadError("MALFORMED_CUSTODY")
    if credentials._denial is not None:
        raise AccountReadError(credentials._denial)


def _require_transport(transport: object) -> SyntheticTransport:
    if type(transport) is not SyntheticTransport:
        raise AccountReadError("TRANSPORT_DENIED")
    if transport.calls != 0:
        raise AccountReadError("RETRY_DENIED")
    return transport


def _interpret(outcome: ScriptedExchange) -> AccountReadDecision:
    fault = outcome.fault
    if fault is not None:
        if fault == "timeout":
            raise AccountReadError("TIMEOUT")
        if fault == "network":
            raise AccountReadError("NETWORK_DENIED")
        raise AccountReadError("AMBIGUOUS_RESPONSE")
    if type(outcome.redirected) is not bool or type(outcome.status) is not int:
        raise AccountReadError("AMBIGUOUS_RESPONSE")
    if outcome.redirected or 300 <= outcome.status < 400:
        raise AccountReadError("REDIRECT_DENIED")
    if outcome.status != 200:
        raise AccountReadError("HTTP_ERROR")
    reason = _body_reason(outcome._body)
    if reason is not None:
        raise AccountReadError(reason)
    return AccountReadDecision(ReadClassification.ACCEPTED, "ACCOUNT_READ")


def _body_reason(body: object) -> str | None:
    if body is _MISSING:
        return "MISSING_BODY"
    if body is None:
        return "NULL_BODY"
    if type(body) is not dict:
        return "MALFORMED_BODY"
    if any(type(key) is not str or key not in _DOCUMENTED for key in body):
        return "UNRECOGNIZED_FIELD"
    for name in _REQUIRED:
        if name not in body:
            return "INCOMPLETE_ACCOUNT"
    identity = _text(body["id"])
    number = _text(body["account_number"])
    if identity is None or number is None:
        return "MALFORMED_IDENTITY"
    status = body["status"]
    if type(status) is not str or status == "" or status != status.strip():
        return "MALFORMED_STATUS"
    if status not in _STATUSES:
        return "UNSUPPORTED_STATUS"
    currency = body["currency"]
    if type(currency) is not str or currency != _ACCEPTED_CURRENCY:
        return "UNSUPPORTED_CURRENCY"
    for name in ("trading_blocked", "account_blocked", "trade_suspended_by_user"):
        if type(body[name]) is not bool:
            return "MALFORMED_PRECONDITION"
    return None


def _text(value: object) -> str | None:
    if type(value) is not str or value == "" or value != value.strip():
        return None
    return value


def _credential_denial(entries: object, fault: object) -> str | None:
    if fault is not None:
        if type(fault) is str and fault in _FAULTS:
            return {
                "ambiguous": "AMBIGUOUS_CUSTODY",
                "inconsistent": "INCONSISTENT_CUSTODY",
                "incomplete": "INCOMPLETE_CUSTODY",
                "malformed": "MALFORMED_CUSTODY",
                "env-fallback": "ENV_FALLBACK_DENIED",
            }[fault]
        return "MALFORMED_CUSTODY"
    if entries is None:
        return "MISSING_CUSTODY"
    if not isinstance(entries, dict):
        return "MALFORMED_CUSTODY"
    names: list[str] = []
    for name in entries:
        if type(name) is not str or name == "":
            return "MALFORMED_CUSTODY"
        if name.startswith(_LIVE_TARGET_PREFIX) or "live" in name.casefold():
            return "LIVE_TARGET_DENIED"
        names.append(name)
    if any(name not in _PAPER_TARGETS for name in names):
        return "AMBIGUOUS_CUSTODY"
    if PAPER_KEY_ID_TARGET not in names:
        return "MISSING_KEY_ID"
    if PAPER_SECRET_TARGET not in names:
        return "MISSING_SECRET"
    for name in _PAPER_TARGETS:
        value = entries[name]
        if isinstance(value, list):
            return "AMBIGUOUS_CUSTODY"
        if type(value) is not bytes or value == b"":
            return "MALFORMED_MATERIAL" if type(value) is not bytes else "INCOMPLETE_MATERIAL"
        if any(byte < 33 or byte > 126 for byte in value):
            return "MALFORMED_MATERIAL"
    return None
