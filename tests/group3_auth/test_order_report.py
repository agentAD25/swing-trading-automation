"""Synthetic broker-report evidence. No broker, credential, or order action."""

import ast
from pathlib import Path

from swingtrade.group3_auth.boundary import ExecutionPosture, evaluate_destination
from swingtrade.group3_auth.order_report import ReportEvidence, ReportLabel, classify_report
from swingtrade.group3_auth.outcomes import OutcomeCode

_ORDER = "ORD_SYN_1"
_OTHER = "ORD_SYN_2"


def _report(fact: str, order_id: object = _ORDER) -> dict[str, object]:
    body: dict[str, object] = {"facts": [fact]}
    if order_id is not None:
        body["order_id"] = order_id
    return body


def test_supported_evidence_labels_are_not_order_commands() -> None:
    cases = (
        ("ACKNOWLEDGED", ReportLabel.ACKNOWLEDGMENT),
        ("PARTIALLY_FILLED", ReportLabel.PARTIAL_FILL),
        ("FILLED", ReportLabel.FILL),
        ("REJECTED", ReportLabel.REJECTION),
        ("CANCELED", ReportLabel.CANCELLATION),
    )
    for fact, label in cases:
        result = classify_report(_report(fact))
        assert result == ReportEvidence(label, _ORDER, "CLASSIFIED")
        assert result.safe_to_retry is False
        assert result.resubmit_permitted is False
        assert result.submit_permitted is False
        assert result.cancel_permitted is False
        assert result.network_permitted is False
        assert result.connect_allowed is False
        assert _ORDER not in repr(result)


def test_unknown_does_not_upgrade_and_missing_order_id_is_not_invented() -> None:
    missing = classify_report({"facts": ["FILLED"]})
    assert missing == ReportEvidence(ReportLabel.FILL, None, "CLASSIFIED")
    unknown = classify_report({"facts": ["EXPIRED"]})
    assert unknown.label is ReportLabel.UNKNOWN
    assert unknown.reason == "UNSUPPORTED_EVIDENCE"
    assert unknown.order_id is None
    again = classify_report({"facts": ["EXPIRED"]})
    assert again == unknown
    assert again.label is not ReportLabel.FILL


def test_invalid_and_conflicting_order_ids_fail_closed() -> None:
    invalid = classify_report(_report("ACKNOWLEDGED", order_id=12))
    assert invalid == ReportEvidence(ReportLabel.UNKNOWN, None, "MALFORMED_IDENTITY")
    blank = classify_report(_report("ACKNOWLEDGED", order_id=""))
    assert blank.reason == "MALFORMED_IDENTITY"
    conflict = classify_report({"facts": ["FILLED"], "order_id": [_ORDER, _OTHER]})
    assert conflict == ReportEvidence(ReportLabel.UNKNOWN, None, "CONFLICTING_IDENTITY")
    assert _ORDER not in repr(conflict)
    assert _OTHER not in repr(conflict)


def test_contradictory_and_insufficient_evidence_stay_unknown() -> None:
    filled_rejected = classify_report({"facts": ["FILLED", "REJECTED"], "order_id": _ORDER})
    assert filled_rejected.label is ReportLabel.UNKNOWN
    assert filled_rejected.reason == "CONTRADICTORY_EVIDENCE"
    filled_canceled = classify_report({"facts": ["FILLED", "CANCELED"]})
    assert filled_canceled.reason == "CONTRADICTORY_EVIDENCE"
    both_fills = classify_report({"facts": ["PARTIALLY_FILLED", "FILLED"], "order_id": _ORDER})
    assert both_fills.reason == "CONTRADICTORY_EVIDENCE"
    assert both_fills.order_id == _ORDER
    assigned = classify_report(_report("ORDER_ID_ASSIGNED"))
    assert assigned == ReportEvidence(ReportLabel.UNKNOWN, _ORDER, "INSUFFICIENT_EVIDENCE")
    requested = classify_report({"facts": ["CANCEL_REQUESTED"], "order_id": _ORDER})
    assert requested.reason == "CANCEL_UNCONFIRMED"
    pending = classify_report({"facts": ["PENDING_CANCEL"]})
    assert pending.reason == "CANCEL_UNCONFIRMED"
    assert pending.label is not ReportLabel.CANCELLATION


def test_missing_and_malformed_reports_do_not_coerce_evidence() -> None:
    assert classify_report({}).reason == "MISSING_EVIDENCE"
    assert classify_report({"order_id": _ORDER}).reason == "MISSING_EVIDENCE"
    assert classify_report({"facts": []}).reason == "MISSING_EVIDENCE"
    assert classify_report({"facts": "FILLED"}).reason == "MALFORMED_REPORT"
    assert classify_report(["FILLED"]).reason == "MALFORMED_REPORT"
    assert classify_report({"facts": [None]}).reason == "MALFORMED_REPORT"
    hidden = "SYN_ACCOUNT_SHOULD_NOT_RENDER"
    leaked = classify_report({"facts": ["FILLED"], "order_id": _ORDER, "account": hidden})
    assert leaked == ReportEvidence(ReportLabel.UNKNOWN, None, "UNDOCUMENTED_FIELD")
    assert hidden not in repr(leaked)
    assert hidden not in str(leaked)


def test_replay_does_not_mutate_the_report_or_change_the_result() -> None:
    report = {"facts": ["PARTIALLY_FILLED"], "order_id": _ORDER}
    snapshot = {"facts": ["PARTIALLY_FILLED"], "order_id": _ORDER}
    first = classify_report(report)
    second = classify_report(report)
    assert report == snapshot
    assert first == second
    assert first.label is ReportLabel.PARTIAL_FILL


def test_classifier_has_no_provider_path_and_denials_stay_closed() -> None:
    source = Path("src/swingtrade/group3_auth/order_report.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module.split(".", 1)[0])
    forbidden = {"socket", "urllib", "requests", "http", "sqlite3", "psycopg", "sqlalchemy"}
    assert imported.isdisjoint(forbidden)
    live = evaluate_destination(
        ExecutionPosture.DRY_RUN,
        "https://api.tradestation.com/v3/brokerage/accounts",
    )
    assert live.decision.reason == "LIVE_HOST_PROHIBITED"
    order = evaluate_destination(
        ExecutionPosture.DRY_RUN,
        "https://sim-api.tradestation.com/v3/orderexecution/orders",
        method="POST",
    )
    assert order.decision.reason == "ORDER_PLACEMENT_DENIED"
    assert set(OutcomeCode) == {
        OutcomeCode.ASSEMBLED,
        OutcomeCode.CLASSIFIED,
        OutcomeCode.REJECTED,
        OutcomeCode.UNKNOWN,
    }
