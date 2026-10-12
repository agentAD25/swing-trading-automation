"""Synthetic broker-report sequence evidence. No broker, credential, or order action."""

import ast
import copy
import subprocess
from pathlib import Path

import pytest

from swingtrade.group3_auth.boundary import ExecutionPosture, evaluate_destination
from swingtrade.group3_auth.order_report_sequence import (
    SequenceEvidence,
    SequenceLabel,
    evaluate_report_sequence,
)
from swingtrade.group3_auth.outcomes import OutcomeCode

_ORDER = "ORD_SYN_1"
_OTHER = "ORD_SYN_2"
_OMIT = object()
_PARSER = "ecbf5a0d06c6db3c839407df341ee407eac05dcf"
_CLASSIFIER = "7ddf267e707d0c7aabe7106eebfc24d090ed6648"


def _report(
    fact: object = "ACKNOWLEDGED",
    order_id: object = _ORDER,
    sequence: object = _OMIT,
    *,
    facts: object = _OMIT,
    extra: tuple[tuple[str, object], ...] = (),
) -> dict[str, object]:
    body: dict[str, object] = {}
    if facts is _OMIT:
        body["facts"] = [fact]
    elif facts is not None:
        body["facts"] = facts
    if order_id is not _OMIT:
        body["order_id"] = order_id
    if sequence is not _OMIT:
        body["sequence"] = sequence
    for key, value in extra:
        body[key] = value
    return body


def _expect(
    result: SequenceEvidence,
    label: SequenceLabel,
    reasons: tuple[str, ...],
    order_id: str | None,
) -> None:
    assert result == SequenceEvidence(label, order_id, reasons)
    assert result.classification is label
    assert result.safe_to_retry is False
    assert result.resubmit_permitted is False
    assert result.submit_permitted is False
    assert result.cancel_permitted is False
    assert result.network_permitted is False
    assert result.connect_allowed is False
    rendered = repr(result)
    assert _ORDER not in rendered
    assert _OTHER not in rendered
    assert "ACKNOWLEDGED" not in rendered
    assert "FILLED" not in rendered
    assert "SYN_ACCOUNT" not in rendered


def test_one_supported_report_without_sequence_is_consistent() -> None:
    result = evaluate_report_sequence([_report()])
    _expect(result, SequenceLabel.CONSISTENT, (), _ORDER)


def test_one_supported_report_with_sequence_is_consistent() -> None:
    result = evaluate_report_sequence([_report(sequence=7)])
    _expect(result, SequenceLabel.CONSISTENT, (), _ORDER)


def test_same_facts_with_increasing_sequences_are_consistent() -> None:
    reports = [_report(sequence=0), _report(sequence=1), _report(sequence=2)]
    _expect(evaluate_report_sequence(reports), SequenceLabel.CONSISTENT, (), _ORDER)
    offset = [_report(sequence=4), _report(sequence=5)]
    _expect(evaluate_report_sequence(offset), SequenceLabel.CONSISTENT, (), _ORDER)


def test_exact_duplicates_do_not_depend_on_object_or_dict_order() -> None:
    first = {"facts": ["ACKNOWLEDGED"], "order_id": _ORDER}
    second = {"order_id": _ORDER, "facts": ["ACKNOWLEDGED"]}
    repeated = evaluate_report_sequence([first, second])
    _expect(repeated, SequenceLabel.DUPLICATE, ("DUPLICATE",), _ORDER)
    sequenced = [
        {"sequence": 3, "facts": ["FILLED"], "order_id": _ORDER},
        {"order_id": _ORDER, "sequence": 3, "facts": ["FILLED"]},
    ]
    _expect(
        evaluate_report_sequence(sequenced),
        SequenceLabel.DUPLICATE,
        ("DUPLICATE", "OUT_OF_ORDER"),
        _ORDER,
    )


def test_equal_labels_with_unequal_fact_multisets_conflict() -> None:
    reports = [
        {"facts": ["FILLED"], "order_id": _ORDER, "sequence": 0},
        {"facts": ["FILLED", "FILLED"], "order_id": _ORDER, "sequence": 1},
    ]
    _expect(
        evaluate_report_sequence(reports),
        SequenceLabel.CONFLICT,
        ("INCONSISTENT_EVIDENCE",),
        _ORDER,
    )


def test_fact_list_order_uses_a_multiset() -> None:
    reports = [
        {"facts": ["FILLED", "REJECTED"], "order_id": _ORDER},
        {"facts": ["REJECTED", "FILLED"], "order_id": _ORDER},
    ]
    _expect(
        evaluate_report_sequence(reports),
        SequenceLabel.CONFLICT,
        ("CONTRADICTORY_EVIDENCE", "DUPLICATE"),
        _ORDER,
    )


@pytest.mark.parametrize(
    ("reports", "label", "reasons", "order_id"),
    [
        ([_report(order_id=_OMIT)], SequenceLabel.MISSING, ("MISSING_ORDER_ID",), None),
        ([_report(order_id=12)], SequenceLabel.UNKNOWN, ("MALFORMED_IDENTITY",), None),
        ([_report(order_id="")], SequenceLabel.UNKNOWN, ("MALFORMED_IDENTITY",), None),
        ([_report(order_id=" ")], SequenceLabel.UNKNOWN, ("MALFORMED_IDENTITY",), None),
        (
            [_report(order_id="X" * 65)],
            SequenceLabel.UNKNOWN,
            ("MALFORMED_IDENTITY",),
            None,
        ),
        (
            [{"facts": ["FILLED"], "order_id": [_ORDER, _OTHER]}],
            SequenceLabel.CONFLICT,
            ("CONFLICTING_IDENTITY",),
            None,
        ),
        (
            [_report(), _report(order_id=_OTHER)],
            SequenceLabel.CONFLICT,
            ("CONFLICTING_IDENTITY",),
            None,
        ),
        (
            [_report(order_id=[_ORDER, _ORDER])],
            SequenceLabel.CONSISTENT,
            (),
            _ORDER,
        ),
    ],
)
def test_identity_failures(
    reports: list[object],
    label: SequenceLabel,
    reasons: tuple[str, ...],
    order_id: str | None,
) -> None:
    result = evaluate_report_sequence(reports)
    _expect(result, label, reasons, order_id)
    assert result.order_id == order_id


def test_account_identifier_is_not_disclosed() -> None:
    hidden = "SYN_ACCOUNT_SHOULD_NOT_RENDER"
    result = evaluate_report_sequence([_report(extra=(("account", hidden),))])
    _expect(result, SequenceLabel.UNKNOWN, ("UNDOCUMENTED_FIELD",), None)
    assert hidden not in repr(result)


@pytest.mark.parametrize(
    ("reports", "label", "reasons", "order_id"),
    [
        (
            [_report(sequence=1), _report(sequence=0)],
            SequenceLabel.OUT_OF_ORDER,
            ("OUT_OF_ORDER",),
            _ORDER,
        ),
        (
            [_report(sequence=0), _report(sequence=0)],
            SequenceLabel.DUPLICATE,
            ("DUPLICATE", "OUT_OF_ORDER"),
            _ORDER,
        ),
        ([_report(sequence=True)], SequenceLabel.UNKNOWN, ("MALFORMED_SEQUENCE",), None),
        ([_report(sequence=False)], SequenceLabel.UNKNOWN, ("MALFORMED_SEQUENCE",), None),
        ([_report(sequence=-1)], SequenceLabel.UNKNOWN, ("MALFORMED_SEQUENCE",), None),
        ([_report(sequence=1.0)], SequenceLabel.UNKNOWN, ("MALFORMED_SEQUENCE",), None),
        ([_report(sequence="0")], SequenceLabel.UNKNOWN, ("MALFORMED_SEQUENCE",), None),
        ([_report(sequence=None)], SequenceLabel.UNKNOWN, ("MALFORMED_SEQUENCE",), None),
        (
            [_report(sequence=0), _report()],
            SequenceLabel.UNKNOWN,
            ("PARTIAL_SEQUENCE",),
            _ORDER,
        ),
        (
            [_report(), _report(sequence=0)],
            SequenceLabel.UNKNOWN,
            ("PARTIAL_SEQUENCE",),
            _ORDER,
        ),
        (
            [_report(sequence=0), _report(sequence=2)],
            SequenceLabel.MISSING,
            ("SEQUENCE_GAP",),
            _ORDER,
        ),
        (
            [_report(sequence=0), _report(sequence=1), _report(sequence=3)],
            SequenceLabel.MISSING,
            ("SEQUENCE_GAP",),
            _ORDER,
        ),
    ],
)
def test_sequence_metadata(
    reports: list[object],
    label: SequenceLabel,
    reasons: tuple[str, ...],
    order_id: str | None,
) -> None:
    _expect(evaluate_report_sequence(reports), label, reasons, order_id)


def test_caller_order_is_not_reordered() -> None:
    increasing = [_report(sequence=0), _report(sequence=1)]
    decreasing = [_report(sequence=1), _report(sequence=0)]
    _expect(evaluate_report_sequence(increasing), SequenceLabel.CONSISTENT, (), _ORDER)
    _expect(
        evaluate_report_sequence(decreasing),
        SequenceLabel.OUT_OF_ORDER,
        ("OUT_OF_ORDER",),
        _ORDER,
    )


def test_absent_sequence_is_not_zero() -> None:
    mixed = [_report(sequence=0), _report()]
    _expect(evaluate_report_sequence(mixed), SequenceLabel.UNKNOWN, ("PARTIAL_SEQUENCE",), _ORDER)
    assert evaluate_report_sequence(mixed).classification is not SequenceLabel.DUPLICATE


@pytest.mark.parametrize(
    ("reports", "label", "reasons", "order_id"),
    [
        (
            [_report(), _report(fact="FILLED")],
            SequenceLabel.CONFLICT,
            ("INCONSISTENT_EVIDENCE",),
            _ORDER,
        ),
        (
            [_report(), _report(fact="FILLED", sequence=1)],
            SequenceLabel.UNKNOWN,
            ("PARTIAL_SEQUENCE", "INCONSISTENT_EVIDENCE"),
            _ORDER,
        ),
        (
            [_report(fact="FILLED", sequence=1), _report(sequence=0)],
            SequenceLabel.CONFLICT,
            ("INCONSISTENT_EVIDENCE", "OUT_OF_ORDER"),
            _ORDER,
        ),
        (
            [_report(facts=["FILLED", "REJECTED"])],
            SequenceLabel.CONFLICT,
            ("CONTRADICTORY_EVIDENCE",),
            _ORDER,
        ),
        (
            [_report(fact="EXPIRED")],
            SequenceLabel.UNKNOWN,
            ("UNSUPPORTED_EVIDENCE",),
            _ORDER,
        ),
        (
            [_report(facts="FILLED")],
            SequenceLabel.UNKNOWN,
            ("MALFORMED_REPORT",),
            None,
        ),
        (
            [_report(fact="EXPIRED"), _report(fact="EXPIRED")],
            SequenceLabel.DUPLICATE,
            ("DUPLICATE", "UNSUPPORTED_EVIDENCE"),
            _ORDER,
        ),
        (
            [_report(fact="CANCEL_REQUESTED", sequence=0), _report(fact="FILLED", sequence=1)],
            SequenceLabel.CONFLICT,
            ("INCONSISTENT_EVIDENCE", "CANCEL_UNCONFIRMED"),
            _ORDER,
        ),
        (
            [_report(fact="FILLED", sequence=0), _report(fact="REJECTED", sequence=1)],
            SequenceLabel.CONFLICT,
            ("INCONSISTENT_EVIDENCE",),
            _ORDER,
        ),
        (
            [_report(fact="REJECTED", sequence=0), _report(fact="FILLED", sequence=1)],
            SequenceLabel.CONFLICT,
            ("INCONSISTENT_EVIDENCE",),
            _ORDER,
        ),
        (
            [
                _report(sequence=0),
                _report(fact="PARTIALLY_FILLED", sequence=1),
                _report(fact="FILLED", sequence=2),
            ],
            SequenceLabel.CONFLICT,
            ("INCONSISTENT_EVIDENCE",),
            _ORDER,
        ),
        (
            [_report(fact="ORDER_ID_ASSIGNED")],
            SequenceLabel.MISSING,
            ("INSUFFICIENT_EVIDENCE",),
            _ORDER,
        ),
        (
            [_report(fact="CANCEL_REQUESTED")],
            SequenceLabel.MISSING,
            ("CANCEL_UNCONFIRMED",),
            _ORDER,
        ),
        (
            [_report(fact="PENDING_CANCEL")],
            SequenceLabel.MISSING,
            ("CANCEL_UNCONFIRMED",),
            _ORDER,
        ),
        (
            [_report(fact="ORDER_ID_ASSIGNED"), _report(fact="ORDER_ID_ASSIGNED")],
            SequenceLabel.DUPLICATE,
            ("DUPLICATE", "INSUFFICIENT_EVIDENCE"),
            _ORDER,
        ),
        ([{"order_id": _ORDER}], SequenceLabel.MISSING, ("MISSING_EVIDENCE",), _ORDER),
        ([_report(facts=[])], SequenceLabel.MISSING, ("MISSING_EVIDENCE",), _ORDER),
        (
            [_report(fact="CANCELED", sequence=1), _report(fact="CANCEL_REQUESTED", sequence=0)],
            SequenceLabel.CONFLICT,
            ("INCONSISTENT_EVIDENCE", "OUT_OF_ORDER", "CANCEL_UNCONFIRMED"),
            _ORDER,
        ),
    ],
)
def test_evidence_failures(
    reports: list[object],
    label: SequenceLabel,
    reasons: tuple[str, ...],
    order_id: str | None,
) -> None:
    result = evaluate_report_sequence(reports)
    _expect(result, label, reasons, order_id)
    assert result.classification is not SequenceLabel.CONSISTENT


def test_multi_defect_precedence_is_independent_of_element_order() -> None:
    missing_and_reversed = [
        _report(order_id=_OMIT, sequence=0),
        _report(order_id=_OMIT, sequence=2),
    ]
    reversed_missing = list(reversed(missing_and_reversed))
    _expect(
        evaluate_report_sequence(missing_and_reversed),
        SequenceLabel.MISSING,
        ("MISSING_ORDER_ID", "SEQUENCE_GAP"),
        None,
    )
    _expect(
        evaluate_report_sequence(reversed_missing),
        SequenceLabel.OUT_OF_ORDER,
        ("OUT_OF_ORDER", "MISSING_ORDER_ID"),
        None,
    )
    decreasing_without_id = [
        _report(order_id=_OMIT, sequence=2),
        _report(order_id=_OMIT, sequence=0),
    ]
    _expect(
        evaluate_report_sequence(decreasing_without_id),
        SequenceLabel.OUT_OF_ORDER,
        ("OUT_OF_ORDER", "MISSING_ORDER_ID"),
        None,
    )
    _expect(
        evaluate_report_sequence(list(reversed(decreasing_without_id))),
        SequenceLabel.MISSING,
        ("MISSING_ORDER_ID", "SEQUENCE_GAP"),
        None,
    )
    conflict_first = [
        _report(order_id=_OTHER, facts=["FILLED", "REJECTED"]),
        _report(),
    ]
    conflict_second = list(reversed(conflict_first))
    expected = ("CONFLICTING_IDENTITY", "CONTRADICTORY_EVIDENCE")
    _expect(evaluate_report_sequence(conflict_first), SequenceLabel.CONFLICT, expected, None)
    _expect(evaluate_report_sequence(conflict_second), SequenceLabel.CONFLICT, expected, None)
    duplicate_and_conflict = [_report(), _report(), _report(fact="FILLED")]
    _expect(
        evaluate_report_sequence(duplicate_and_conflict),
        SequenceLabel.CONFLICT,
        ("INCONSISTENT_EVIDENCE", "DUPLICATE"),
        _ORDER,
    )
    _expect(
        evaluate_report_sequence(list(reversed(duplicate_and_conflict))),
        SequenceLabel.CONFLICT,
        ("INCONSISTENT_EVIDENCE", "DUPLICATE"),
        _ORDER,
    )
    partial_and_duplicate = [_report(sequence=1), _report(sequence=1), _report()]
    _expect(
        evaluate_report_sequence(partial_and_duplicate),
        SequenceLabel.UNKNOWN,
        ("PARTIAL_SEQUENCE", "DUPLICATE"),
        _ORDER,
    )
    malformed_and_conflict = [
        _report(extra=(("account", "SYN_ACCOUNT"),)),
        {"facts": ["FILLED"], "order_id": [_ORDER, _OTHER]},
    ]
    _expect(
        evaluate_report_sequence(malformed_and_conflict),
        SequenceLabel.UNKNOWN,
        ("UNDOCUMENTED_FIELD",),
        None,
    )
    _expect(
        evaluate_report_sequence(list(reversed(malformed_and_conflict))),
        SequenceLabel.UNKNOWN,
        ("UNDOCUMENTED_FIELD",),
        None,
    )
    malformed_sequence_and_conflict = [
        _report(sequence=-1),
        _report(fact="REJECTED", sequence=0),
    ]
    _expect(
        evaluate_report_sequence(malformed_sequence_and_conflict),
        SequenceLabel.UNKNOWN,
        ("MALFORMED_SEQUENCE",),
        None,
    )


def test_same_sequence_on_unequal_bodies_conflicts_in_either_order() -> None:
    left = [_report(sequence=4), _report(order_id=_OTHER, fact="FILLED", sequence=4)]
    reasons = ("CONFLICTING_IDENTITY", "SAME_SEQUENCE_UNEQUAL_BODY", "OUT_OF_ORDER")
    _expect(evaluate_report_sequence(left), SequenceLabel.CONFLICT, reasons, None)
    _expect(evaluate_report_sequence(list(reversed(left))), SequenceLabel.CONFLICT, reasons, None)


def test_empty_and_non_list_inputs_fail_closed() -> None:
    _expect(evaluate_report_sequence([]), SequenceLabel.MISSING, ("NO_REPORTS",), None)
    for value in (None, (), _report(), "reports", 0, True):
        result = evaluate_report_sequence(value)
        _expect(result, SequenceLabel.UNKNOWN, ("MALFORMED_REPORT",), None)


def test_non_dict_element_stops_at_malformation() -> None:
    reports = [_report(), "FILLED"]
    _expect(evaluate_report_sequence(reports), SequenceLabel.UNKNOWN, ("MALFORMED_REPORT",), None)
    _expect(
        evaluate_report_sequence(list(reversed(reports))),
        SequenceLabel.UNKNOWN,
        ("MALFORMED_REPORT",),
        None,
    )


def test_input_and_replay_are_immutable_and_deterministic() -> None:
    reports = [
        {"facts": ["FILLED", "ACKNOWLEDGED"], "order_id": _ORDER, "sequence": 1},
        {"order_id": _OTHER, "facts": ["REJECTED"], "sequence": 0},
    ]
    snapshot = copy.deepcopy(reports)
    first = evaluate_report_sequence(reports)
    second = evaluate_report_sequence(reports)
    replay = evaluate_report_sequence(copy.deepcopy(snapshot))
    assert reports == snapshot
    assert first == second == replay
    assert first.classification is SequenceLabel.CONFLICT


def test_classifier_receives_only_facts_and_order_id(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[set[str]] = []
    real = __import__(
        "swingtrade.group3_auth.order_report_sequence",
        fromlist=["classify_report"],
    ).classify_report

    def _wrapped(report: object) -> object:
        assert type(report) is dict
        calls.append(set(report))
        return real(report)

    monkeypatch.setattr(
        "swingtrade.group3_auth.order_report_sequence.classify_report",
        _wrapped,
    )
    evaluate_report_sequence([_report(sequence=0), _report(sequence=1)])
    assert calls == [{"facts", "order_id"}, {"facts", "order_id"}]


def test_module_has_no_provider_or_persistence_path() -> None:
    source = Path("src/swingtrade/group3_auth/order_report_sequence.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module.split(".", 1)[0])
    forbidden = {
        "socket",
        "urllib",
        "requests",
        "http",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "subprocess",
        "pathlib",
    }
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


def test_certified_parser_and_classifier_blobs_stay_unchanged() -> None:
    parser = subprocess.check_output(
        ["git", "hash-object", "src/swingtrade/group3_auth/brokerage_read.py"],
        text=True,
    ).strip()
    classifier = subprocess.check_output(
        ["git", "hash-object", "src/swingtrade/group3_auth/order_report.py"],
        text=True,
    ).strip()
    assert parser == _PARSER
    assert classifier == _CLASSIFIER
