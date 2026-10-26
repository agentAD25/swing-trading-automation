"""Classify synthetic Alpaca Paper fixtures. No request and no order action.

The input is a project-defined fixture, not an Alpaca wire response and not
permission to call ``paper-api.alpaca.markets`` or ``api.alpaca.markets``.
Those hostnames are denied. Quantities stay ``Decimal`` values parsed from
strings. The module does not generate an order id, construct an ``OrderIntent``,
or read credentials.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from enum import StrEnum

PAPER_HOST = "paper-api.alpaca.markets"
LIVE_HOST = "api.alpaca.markets"
DENIED_HOSTS = frozenset({PAPER_HOST, LIVE_HOST})

_ALLOW = frozenset(
    {"client_order_id", "id", "status", "qty", "filled_qty", "remaining_qty"}
)
_SUPPORTED = frozenset(
    {
        "new",
        "partially_filled",
        "filled",
        "canceled",
        "expired",
        "rejected",
        "pending_new",
        "pending_cancel",
    }
)
_SUBMISSION_UNKNOWN = "submission_unknown"
_TERMINAL = frozenset({"filled", "canceled", "rejected", "expired"})
_MAX_CLIENT_ID = 128


class PaperClassification(StrEnum):
    """Fixture evidence label. This is not an order command or a broker status."""

    OBSERVED = "OBSERVED"
    DUPLICATE = "DUPLICATE"
    RECONCILE_BEFORE_RESUBMIT = "RECONCILE_BEFORE_RESUBMIT"
    REJECTED = "REJECTED"


class PaperEvidence:
    """One fixture classification. Network and economic actions stay closed."""

    __slots__ = (
        "broker_order_id",
        "classification",
        "client_order_id",
        "filled_qty",
        "qty",
        "reason",
        "remaining_qty",
        "status",
    )

    def __init__(
        self,
        classification: PaperClassification,
        reason: str,
        *,
        client_order_id: str | None = None,
        broker_order_id: str | None = None,
        status: str | None = None,
        qty: Decimal | None = None,
        filled_qty: Decimal | None = None,
        remaining_qty: Decimal | None = None,
    ) -> None:
        self.classification = classification
        self.reason = reason
        self.client_order_id = client_order_id
        self.broker_order_id = broker_order_id
        self.status = status
        self.qty = qty
        self.filled_qty = filled_qty
        self.remaining_qty = remaining_qty

    @property
    def generated_client_order_id(self) -> None:
        """The module never mints a replacement client order id."""
        return None

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
    def resubmit_permitted(self) -> bool:
        return False

    @property
    def safe_to_retry(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PaperEvidence):
            return NotImplemented
        return (
            self.classification,
            self.reason,
            self.client_order_id,
            self.broker_order_id,
            self.status,
            self.qty,
            self.filled_qty,
            self.remaining_qty,
        ) == (
            other.classification,
            other.reason,
            other.client_order_id,
            other.broker_order_id,
            other.status,
            other.qty,
            other.filled_qty,
            other.remaining_qty,
        )

    def __repr__(self) -> str:
        return f"PaperEvidence({self.classification.value}, {self.reason})"


class HostDenial:
    """A hostname is not a connection grant. Paper and live hosts are denied."""

    __slots__ = ("reason",)

    def __init__(self, reason: str) -> None:
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
    def resubmit_permitted(self) -> bool:
        return False

    @property
    def safe_to_retry(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"HostDenial({self.reason})"


def deny_host(host: object) -> HostDenial:
    """Deny every host. The paper and live names are recognized only to deny them."""
    if host == PAPER_HOST:
        return HostDenial("PAPER_HOST_DENIED")
    if host == LIVE_HOST:
        return HostDenial("LIVE_HOST_DENIED")
    return HostDenial("HOST_DENIED")


def evaluate_paper_fixtures(fixtures: object) -> tuple[PaperEvidence, ...]:
    """Classify synthetic fixtures in caller order. The input is not modified."""
    if type(fixtures) is not list:
        return (_rejected("MALFORMED_FIXTURE"),)
    seen: set[str] = set()
    return tuple(_one(item, seen) for item in fixtures)


def _rejected(
    reason: str,
    *,
    client_order_id: str | None = None,
    broker_order_id: str | None = None,
) -> PaperEvidence:
    return PaperEvidence(
        PaperClassification.REJECTED,
        reason,
        client_order_id=client_order_id,
        broker_order_id=broker_order_id,
    )


def _one(item: object, seen: set[str]) -> PaperEvidence:
    if type(item) is not dict:
        return _rejected("MALFORMED_FIXTURE")
    if not set(item).issubset(_ALLOW):
        return _rejected("UNDOCUMENTED_FIELD")
    client_id, identity_reason = _client_id(item.get("client_order_id"), "client_order_id" in item)
    broker_id, broker_reason = _broker_id(item)
    if identity_reason is not None:
        return _rejected(identity_reason)
    if broker_reason is not None:
        return _rejected(broker_reason, client_order_id=client_id)
    if client_id is None:
        return _rejected("MISSING_CLIENT_ORDER_ID", broker_order_id=broker_id)
    if client_id in seen:
        return PaperEvidence(
            PaperClassification.DUPLICATE,
            "DUPLICATE_CLIENT_ORDER_ID",
            client_order_id=client_id,
        )
    status, status_reason = _status(item)
    if status_reason is not None or status is None:
        return _rejected(status_reason or "MISSING_STATUS", client_order_id=client_id)
    qty, filled, remaining, quantity_reason = _quantities(status, item)
    if quantity_reason is not None:
        return _rejected(quantity_reason, client_order_id=client_id, broker_order_id=broker_id)
    seen.add(client_id)
    if status == _SUBMISSION_UNKNOWN:
        return PaperEvidence(
            PaperClassification.RECONCILE_BEFORE_RESUBMIT,
            "RECONCILE_BEFORE_RESUBMIT",
            client_order_id=client_id,
            broker_order_id=broker_id,
            status=status,
            qty=qty,
            filled_qty=filled,
            remaining_qty=remaining,
        )
    return PaperEvidence(
        PaperClassification.OBSERVED,
        "CLASSIFIED",
        client_order_id=client_id,
        broker_order_id=broker_id,
        status=status,
        qty=qty,
        filled_qty=filled,
        remaining_qty=remaining,
    )


def _client_id(value: object, present: bool) -> tuple[str | None, str | None]:
    if not present:
        return None, None
    if type(value) is not str or value == "" or any(_bad_id_char(char) for char in value):
        return None, "MALFORMED_CLIENT_ORDER_ID"
    if len(value) > _MAX_CLIENT_ID:
        return None, "CLIENT_ORDER_ID_TOO_LONG"
    return value, None


def _broker_id(item: Mapping[str, object]) -> tuple[str | None, str | None]:
    if "id" not in item:
        return None, None
    value = item["id"]
    if type(value) is not str or value == "" or any(_bad_id_char(char) for char in value):
        return None, "MALFORMED_BROKER_ORDER_ID"
    if len(value) > _MAX_CLIENT_ID:
        return None, "MALFORMED_BROKER_ORDER_ID"
    return value, None


def _bad_id_char(char: str) -> bool:
    return char.isspace() or ord(char) < 32


def _status(item: Mapping[str, object]) -> tuple[str | None, str | None]:
    if "status" not in item:
        return None, "MISSING_STATUS"
    value = item["status"]
    if type(value) is not str or value == "" or value != value.strip():
        return None, "MALFORMED_STATUS"
    if value == _SUBMISSION_UNKNOWN:
        return value, None
    if value not in _SUPPORTED:
        return None, "UNKNOWN_STATUS"
    return value, None


def _quantities(
    status: str,
    item: Mapping[str, object],
) -> tuple[Decimal | None, Decimal | None, Decimal | None, str | None]:
    qty, qty_reason = _optional_decimal(item, "qty")
    if qty_reason is not None:
        return None, None, None, qty_reason
    filled, filled_reason = _optional_decimal(item, "filled_qty")
    if filled_reason is not None:
        return None, None, None, filled_reason
    remaining, remaining_reason = _optional_decimal(
        item,
        "remaining_qty",
        invalid="INVALID_REMAINING",
    )
    if remaining_reason is not None:
        return None, None, None, remaining_reason
    if qty is not None and qty <= 0:
        return None, None, None, "NEGATIVE_QUANTITY" if qty < 0 else "INVALID_QUANTITY"
    if filled is not None and filled < 0:
        return None, None, None, "NEGATIVE_QUANTITY"
    if remaining is not None and remaining < 0:
        return None, None, None, "NEGATIVE_QUANTITY"
    if qty is not None and filled is not None and filled > qty:
        return None, None, None, "FILLED_EXCEEDS_QTY"
    relation = _relation(status, qty, filled, remaining)
    if relation is not None:
        return None, None, None, relation
    if (
        status == "partially_filled"
        and remaining is None
        and qty is not None
        and filled is not None
    ):
        remaining = qty - filled
    return qty, filled, remaining, None


def _optional_decimal(
    item: Mapping[str, object],
    key: str,
    *,
    invalid: str = "MALFORMED_QUANTITY",
) -> tuple[Decimal | None, str | None]:
    if key not in item:
        return None, None
    parsed, reason = _decimal(item[key])
    if reason is not None or parsed is None:
        return None, invalid
    return parsed, None


def _decimal(value: object) -> tuple[Decimal | None, str | None]:
    if type(value) is not str or value == "" or value != value.strip():
        return None, "MALFORMED_QUANTITY"
    if any(char in value for char in "eE_") or value.startswith("+"):
        return None, "MALFORMED_QUANTITY"
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return None, "MALFORMED_QUANTITY"
    if not parsed.is_finite():
        return None, "MALFORMED_QUANTITY"
    return parsed, None


def _relation(
    status: str,
    qty: Decimal | None,
    filled: Decimal | None,
    remaining: Decimal | None,
) -> str | None:
    if qty is not None and filled is not None and remaining is not None:
        if filled + remaining != qty:
            return "INCONSISTENT_QUANTITY"
    if status == "partially_filled":
        if qty is None or filled is None:
            return "MISSING_FILL"
        if filled == 0 or filled >= qty:
            return "PARTIAL_FILL_RANGE"
        expected = qty - filled
        if remaining is not None and remaining != expected:
            return "INCONSISTENT_QUANTITY"
        return None
    if status == "new" or status == "pending_new":
        if filled is not None and filled != 0:
            return "INCONSISTENT_QUANTITY"
        if qty is not None and remaining is not None and remaining != qty:
            return "INCONSISTENT_QUANTITY"
        return None
    if status == "filled":
        if qty is not None and filled is not None and filled != qty:
            return "INCONSISTENT_QUANTITY"
        if remaining is not None and remaining != 0:
            return "INCONSISTENT_QUANTITY"
        return None
    if remaining is not None and qty is not None and filled is None and remaining > qty:
        return "INVALID_REMAINING"
    if status in _TERMINAL or status == "pending_cancel" or status == _SUBMISSION_UNKNOWN:
        return None
    return "UNKNOWN_STATUS"
