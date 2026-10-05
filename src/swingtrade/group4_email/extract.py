"""Deterministic extraction from normalized text. No clock and no strategy engine."""

from __future__ import annotations

import re
from dataclasses import dataclass, fields, is_dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from swingtrade.domain import DomainValidationError, Side, decimal_value
from swingtrade.group4_email.contract import (
    CALENDAR_ASSUMPTION,
    MAX_EVIDENCE_CHARS,
    QUANTITY_ROUNDING_POLICY,
    RESOLUTION_ABSENT,
    RESOLUTION_CONFLICT,
    RESOLUTION_EXPLICIT,
    RESOLUTION_MALFORMED,
    RESOLUTION_UNRESOLVED,
    RESOLUTION_UNSUPPORTED,
    TIMEZONE_ASSUMPTION,
    CanonicalInstructionEnvelope,
    Direction,
    Disposition,
    FieldEvidence,
    MessageType,
    NewTradeInstruction,
    OrderType,
    PriceOrder,
    ReasonCode,
    SessionEvent,
    SiblingCancel,
    Sizing,
    TimeExit,
    TimeInForce,
    TriggerBasis,
)

_POLICY = re.compile(
    r"(?i)\b("
    r"execution\s+mode|enable\s+live|switch\s+to\s+live|live\s+trading|"
    r"api\s*key|client\s+secret|password|risk\s+limit|parser\s+policy|"
    r"broker\s+credential"
    r")\b"
)
_AMENDMENT = re.compile(r"(?im)^\s*(?:trade\s+amendment|amendment)\s*:")
_EXIT_ALERT = re.compile(r"(?im)^\s*exit\s+alert\s*:")
_CANCEL = re.compile(r"(?im)^\s*(?:trade\s+cancel|cancel\s+trade)\s*:")
_LABEL = re.compile(
    r"(?im)^((?:protective\s+stop)|(?:time\s+exit)|symbol|company|strategy|"
    r"entry|sizing|target|stop)\s*:\s*"
)
_ORDER = re.compile(
    r"(?i)\b(buy|sell)\s+(stop\s+limit|stop-limit|stop|limit|market)\b"
    r"(?:\s+\$([^\s,;]+))?"
)
_STOP_LIMIT_PAIR = re.compile(
    r"(?i)\b(buy|sell)\s+stop(?:\s+|-)limit\s+\$([^\s,;]+)\s+limit\s+\$([^\s,;]+)"
)
_PRICE_TOKEN = re.compile(r"\$([^\s,;]+)")
_STRICT_PRICE = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")
_THOUSANDS = re.compile(r"^[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?$")
_GTC = re.compile(r"(?i)\b(?:good\s+till\s+cancelled|gtc)\b")
_DAY = re.compile(r"(?i)\bday\s+order\b")
_DAILY_CLOSE = re.compile(r"(?i)\b(?:daily\s+close|on\s+the\s+close)\b")
_REAL_ORDER = re.compile(r"(?i)\breal\s+order\b")
_AT_OPEN = re.compile(r"(?i)\bat\s+the\s+open\b")
_BELOW_PRICE = re.compile(r"(?i)\b(?:below|above|under|over)\s+\$([^\s,;]+)")
_PERCENT = re.compile(
    r"(?i)(?:about\s+)?([0-9]+(?:\.[0-9]+)?)\s*%\s*of\s+(?:the\s+)?(?:account|equity)\b"
)
_EXAMPLE = re.compile(
    r"(?i)\$([0-9][0-9,]*(?:\.[0-9]+)?)\s+account\b"
    r".*?\$([0-9][0-9,]*(?:\.[0-9]+)?)\s+allocation\b"
    r".*?([0-9]+)\s+shares\b",
    re.DOTALL,
)
_FIRST_EXIT = re.compile(r"(?i)\bwhichever\s+exit\s+comes\s+first\b")
_SIBLING = re.compile(
    r"(?i)\b(?:cancel\s+the\s+other|cancel\s+both\s+outstanding\s+exits)\b"
)
# A cue in the same sentence, or this close to the phrase, blocks affirmation.
_POLICY_CUE_RADIUS = 120
_NEGATION_CUE = (
    r"(?:n['\u2019]t\b|\b(?:not|never|no|cannot|cant|dont|doesnt|wont|"
    r"isnt|arent|shouldnt|wouldnt|mustnt)\b)"
)
_NEGATION = re.compile(rf"(?i){_NEGATION_CUE}")
_CANCEL_STEM = r"\bcancel(?:l?ed|l?ing|lation)?\b"
_FIRST_EXIT_NEGATED = re.compile(
    rf"(?i)(?:{_NEGATION_CUE}.{{0,80}}?\bwhichever\s+exit\b"
    rf"|\bwhichever\s+exit\b.{{0,80}}?{_NEGATION_CUE})"
)
_SIBLING_NEGATED = re.compile(
    rf"(?i)(?:{_NEGATION_CUE}.{{0,80}}?{_CANCEL_STEM}.{{0,40}}?\bthe\s+other\b"
    rf"|{_NEGATION_CUE}.{{0,80}}?\bcancel\s+both\s+outstanding\s+exits\b"
    rf"|\bthe\s+other\b.{{0,80}}?{_NEGATION_CUE}.{{0,40}}?{_CANCEL_STEM}"
    rf"|{_CANCEL_STEM}.{{0,40}}?\bthe\s+other\b.{{0,60}}?{_NEGATION_CUE}"
    rf"|\bcancel\s+both\s+outstanding\s+exits\b.{{0,60}}?{_NEGATION_CUE})"
)
_OPEN_EXIT = re.compile(r"(?i)\b(buy|sell)\s+at\s+the\s+open\b")
_NON_AUTHORITATIVE_SENTENCE = re.compile(
    r"(?i)\b(?:charts?|disclaimer|copyright|footer|published|publication|"
    r"received|receipt|historical|unsubscribe)\b"
)
_UNSUPPORTED_DATE = re.compile(
    r"\d{4}-\d{2}-\d{2}[Tt](?:\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?"
    r"|"
    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"
)
_SENTENCE_BREAK = re.compile(r"\n+|(?<=[.!?])\s+")
_PROJECTION_EXCLUDED = frozenset(
    {
        "evidence",
        "session_source_date",
        "source_date",
        "company_name",
    }
)
_ORDER_VERB = re.compile(r"(?i)\b(?:buy|sell)\b")
_SYMBOL = re.compile(r"^[A-Z][A-Z0-9.]{0,9}$")
_WEEKDAY = (
    r"mon(?:day)?|tue(?:s|sday)?|wed(?:nesday)?|thu(?:rs|rsday)?|"
    r"fri(?:day)?|sat(?:urday)?|sun(?:day)?"
)
_MONTH = (
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:tember|t)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
)
_ISO_DATE = re.compile(rf"(?i)\b(?:({_WEEKDAY})\s+)?(\d{{4}})-(\d{{2}})-(\d{{2}})\b")
_MONTH_DAY_YEAR = re.compile(
    rf"(?i)\b(?:({_WEEKDAY})\s+)?({_MONTH})\s+(\d{{1,2}})(?:\s*,\s*|\s+)(\d{{4}})\b"
)
_MONTH_DAY = re.compile(rf"(?i)\b(?:({_WEEKDAY})\s+)?({_MONTH})\s+(\d{{1,2}})\b")
_WEEKDAY_ONLY = re.compile(rf"(?i)\b({_WEEKDAY})\b")
_WEEKDAY_INDEX = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}
_MONTH_INDEX = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


@dataclass(frozen=True)
class DateResolution:
    status: str
    source_date: str
    resolved: date | None
    resolution_rule: str


@dataclass(frozen=True)
class Extraction:
    disposition: Disposition
    message_type: MessageType
    reasons: tuple[str, ...]
    instructions: tuple[NewTradeInstruction, ...]
    evidence: tuple[FieldEvidence, ...]


@dataclass
class _Issues:
    reasons: list[str]
    evidence: list[FieldEvidence]

    def add(self, reason: str, field: str, source_text: str) -> None:
        if len(source_text) > MAX_EVIDENCE_CHARS:
            reason = ReasonCode.OVERSIZED_FIELD.value
            source_text = ""
        if reason not in self.reasons:
            self.reasons.append(reason)
        self.evidence.append(FieldEvidence(field, source_text))


def economic_decimal(value: object) -> Decimal:
    """Currency authority is an exact decimal string. Exponents are not amplified."""

    if type(value) is str:
        if re.search(r"[eE]", value):
            raise DomainValidationError("scientific amplification is rejected")
        number = decimal_value(value)
    elif type(value) is Decimal:
        number = decimal_value(value)
    else:
        raise DomainValidationError("decimal input type must be exactly Decimal or str")
    if not number.is_finite():
        raise DomainValidationError("decimal must be finite")
    return number


def extract_text(text: str) -> Extraction:
    if _POLICY.search(text):
        return _done(
            Disposition.QUARANTINE,
            MessageType.UNKNOWN,
            (ReasonCode.POLICY_INSTRUCTION_IGNORED.value,),
            (),
            (),
        )
    if _AMENDMENT.search(text):
        return _deferred(MessageType.TRADE_AMENDMENT, ReasonCode.PARSER_DEFERRED)
    if _EXIT_ALERT.search(text):
        return _deferred(MessageType.EXIT_ALERT, ReasonCode.PARSER_DEFERRED)
    if _CANCEL.search(text):
        return _deferred(MessageType.TRADE_CANCEL, ReasonCode.CANCEL_FORMAT_UNSPECIFIED)

    candidates = _candidates(text)
    if not candidates:
        if _ORDER_VERB.search(text) or "$" in text:
            return _done(
                Disposition.QUARANTINE,
                MessageType.UNKNOWN,
                (ReasonCode.INCOMPLETE_TRADE.value,),
                (),
                (),
            )
        return _done(Disposition.ACCEPT, MessageType.INFORMATIONAL, (), (), ())

    issues = _Issues([], [])
    built: list[NewTradeInstruction] = []
    for sections in candidates:
        instruction = _candidate(sections, issues)
        if instruction is not None:
            built.append(instruction)
    if issues.reasons:
        return _done(
            Disposition.QUARANTINE,
            MessageType.NEW_TRADE,
            tuple(issues.reasons),
            (),
            tuple(issues.evidence),
        )
    return _done(
        Disposition.ACCEPT,
        MessageType.NEW_TRADE,
        (),
        tuple(built),
        tuple(item for instruction in built for item in instruction.evidence),
    )


def projection(extraction: Extraction) -> tuple[object, ...]:
    return (
        extraction.message_type,
        extraction.disposition,
        extraction.reasons,
        tuple(_economic_key(item) for item in extraction.instructions),
    )


def _done(
    disposition: Disposition,
    message_type: MessageType,
    reasons: tuple[str, ...],
    instructions: tuple[NewTradeInstruction, ...],
    evidence: tuple[FieldEvidence, ...],
) -> Extraction:
    if disposition is not Disposition.ACCEPT:
        instructions = ()
    return Extraction(disposition, message_type, reasons, instructions, evidence)


def _deferred(message_type: MessageType, reason: ReasonCode) -> Extraction:
    return _done(Disposition.QUARANTINE, message_type, (reason.value,), (), ())


def _label_name(match: re.Match[str]) -> str:
    label = " ".join(match.group(1).lower().split())
    if label == "protective stop":
        return "stop"
    return label


def _trim_before_next_trade(raw: str) -> str:
    """Keep this field from swallowing the preamble of the next Symbol block."""

    head, separator, _tail = raw.partition("\n\n")
    if separator:
        return head
    return raw


class _PolicyReading(Enum):
    """Reading of one accepted exit policy inside authoritative order text."""

    AFFIRMED = "AFFIRMED"
    NEGATED_OR_CONFLICTING = "NEGATED_OR_CONFLICTING"
    ABSENT = "ABSENT"


def _policy_sentences(text: str) -> list[str]:
    return [part.strip() for part in _SENTENCE_BREAK.split(text) if part.strip()]


def _negation_near(text: str, start: int, end: int) -> bool:
    """A cue before the phrase must sit in the radius. A later cue fails closed."""

    before = text[max(0, start - _POLICY_CUE_RADIUS) : start]
    after = text[end:]
    return _NEGATION.search(before) is not None or _NEGATION.search(after) is not None


def _read_policy(
    text: str,
    positive: re.Pattern[str],
    negated: re.Pattern[str],
) -> _PolicyReading:
    """Affirm a phrase only when no negation cue is tied to that phrase.

    A cue in the same sentence, or within the bounded radius, blocks that
    occurrence. Positive and negated readings in one text fail closed together.
    """

    affirmed = False
    contradicted = False
    for sentence in _policy_sentences(text):
        has_positive = positive.search(sentence) is not None
        has_negation = _NEGATION.search(sentence) is not None
        has_negated_form = negated.search(sentence) is not None
        if has_positive and not has_negation:
            affirmed = True
        elif has_positive or has_negated_form:
            contradicted = True
    for match in positive.finditer(text):
        if _negation_near(text, match.start(), match.end()):
            contradicted = True
    if contradicted:
        return _PolicyReading.NEGATED_OR_CONFLICTING
    if affirmed:
        return _PolicyReading.AFFIRMED
    return _PolicyReading.ABSENT


def _sentence_at(text: str, index: int) -> str:
    previous = 0
    for match in _SENTENCE_BREAK.finditer(text):
        if match.start() >= index:
            return text[previous : match.start()]
        previous = match.end()
    return text[previous:]


def _affirmed_phrase(text: str, positive: re.Pattern[str]) -> str:
    for match in positive.finditer(text):
        if _NEGATION.search(_sentence_at(text, match.start())) is not None:
            continue
        if _negation_near(text, match.start(), match.end()):
            continue
        return match.group(0)
    return ""


def _candidates(text: str) -> list[dict[str, str]]:
    matches = list(_LABEL.finditer(text))
    candidates: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for index, match in enumerate(matches):
        label = _label_name(match)
        next_match = matches[index + 1] if index + 1 < len(matches) else None
        end = next_match.start() if next_match is not None else len(text)
        raw = text[match.end() : end]
        if next_match is not None and _label_name(next_match) == "symbol":
            raw = _trim_before_next_trade(raw)
        value = raw.strip()
        if label == "symbol":
            current = {"symbol": value}
            candidates.append(current)
            continue
        if current is None:
            continue
        if label in current:
            current[label] = current[label] + "\n" + value
            current["duplicate:" + label] = "true"
            continue
        current[label] = value
    return candidates


def _candidate(sections: dict[str, str], issues: _Issues) -> NewTradeInstruction | None:
    start_count = len(issues.reasons)
    for label in ("symbol", "company", "strategy", "entry", "sizing", "target", "stop"):
        if sections.get("duplicate:" + label) == "true":
            issues.add(
                ReasonCode.CONFLICTING_ECONOMIC_INSTRUCTION.value,
                label,
                sections.get(label, ""),
            )
    symbol, symbol_reason = _symbol(sections.get("symbol", ""))
    if symbol_reason is not None or symbol is None:
        issues.add(
            symbol_reason or ReasonCode.INVALID_SYMBOL.value,
            "symbol",
            sections.get("symbol", ""),
        )
        return None
    entry = _price_order("entry", sections.get("entry"), issues, require=True)
    target = _price_order("target", sections.get("target"), issues, require=True)
    stop = _price_order("protective_stop", sections.get("stop"), issues, require=True)
    sizing = _sizing(sections.get("sizing"), issues)
    time_exit = _time_exit(
        sections.get("time exit"),
        issues,
        None if entry is None else entry.side,
    )
    whole = "\n".join(sections.get(name, "") for name in ("entry", "target", "stop", "time exit"))
    first_reading = _read_policy(whole, _FIRST_EXIT, _FIRST_EXIT_NEGATED)
    sibling_reading = _read_policy(whole, _SIBLING, _SIBLING_NEGATED)
    if entry is not None and target is not None and stop is not None:
        if first_reading is _PolicyReading.ABSENT or sibling_reading is _PolicyReading.ABSENT:
            issues.add(
                ReasonCode.MISSING_EXIT_POLICY.value,
                "exit_policy",
                whole[:MAX_EVIDENCE_CHARS],
            )
        if (
            first_reading is _PolicyReading.NEGATED_OR_CONFLICTING
            or sibling_reading is _PolicyReading.NEGATED_OR_CONFLICTING
        ):
            issues.add(
                ReasonCode.CONFLICTING_ECONOMIC_INSTRUCTION.value,
                "exit_policy",
                whole[:MAX_EVIDENCE_CHARS],
            )
    if len(issues.reasons) != start_count:
        return None
    assert entry is not None and target is not None and stop is not None and sizing is not None
    assert first_reading is _PolicyReading.AFFIRMED
    assert sibling_reading is _PolicyReading.AFFIRMED
    direction = Direction.LONG if entry.side is Side.BUY else Direction.SHORT
    evidence = (
        FieldEvidence("symbol", symbol),
        *_optional_label("company_name", sections.get("company")),
        *_optional_label("strategy_label", sections.get("strategy")),
        FieldEvidence("direction", entry.evidence[0].source_text if entry.evidence else ""),
        *entry.evidence,
        *sizing.evidence,
        *target.evidence,
        *stop.evidence,
        *(time_exit.evidence if time_exit is not None else ()),
        FieldEvidence("first_exit_wins", _affirmed_phrase(whole, _FIRST_EXIT)),
        FieldEvidence("sibling_cancel", _affirmed_phrase(whole, _SIBLING)),
    )
    return NewTradeInstruction(
        symbol=symbol,
        company_name=_clean_label(sections.get("company")),
        strategy_label=_clean_label(sections.get("strategy")),
        direction=direction,
        entry=entry,
        sizing=sizing,
        target=target,
        protective_stop=stop,
        time_exit=time_exit,
        first_exit_wins=True,
        sibling_cancel=SiblingCancel.SIBLING_CANCEL_REQUIRED,
        evidence=evidence,
    )


def _optional_label(field: str, value: str | None) -> tuple[FieldEvidence, ...]:
    cleaned = _clean_label(value)
    if cleaned is None:
        return ()
    return (FieldEvidence(field, cleaned),)


def _clean_label(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    if cleaned == "":
        return None
    return cleaned


def _symbol(raw: str) -> tuple[str | None, str | None]:
    token = " ".join(raw.split())
    if token == "":
        return None, ReasonCode.INVALID_SYMBOL.value
    if any(ord(character) > 127 for character in token):
        return None, ReasonCode.UNICODE_LOOKALIKE.value
    if _SYMBOL.fullmatch(token) is None:
        return None, ReasonCode.INVALID_SYMBOL.value
    return token, None


def _price_order(
    field: str,
    section: str | None,
    issues: _Issues,
    *,
    require: bool,
) -> PriceOrder | None:
    if section is None:
        if require:
            issues.add(_missing_order_reason(field), field, "")
        return None
    if len(section) > MAX_EVIDENCE_CHARS:
        issues.add(ReasonCode.OVERSIZED_FIELD.value, field, "")
        return None
    pair = _STOP_LIMIT_PAIR.search(section)
    orders = list(_ORDER.finditer(section))
    daily = _DAILY_CLOSE.search(section)
    if pair is not None:
        return _stop_limit_order(field, section, pair, issues)
    if len(orders) > 1:
        issues.add(
            ReasonCode.CONFLICTING_ECONOMIC_INSTRUCTION.value,
            f"{field}.order",
            " | ".join(match.group(0) for match in orders),
        )
        return None
    if not orders:
        opened = _AT_OPEN.search(section)
        if daily is not None:
            token = _BELOW_PRICE.search(section)
            cited = token.group(0) if token else daily.group(0)
            issues.add(
                ReasonCode.UNKNOWN_ORDER_TYPE.value,
                f"{field}.trigger_basis",
                f"{cited} => {TriggerBasis.DAILY_CLOSE_TRIGGER.value}",
            )
        elif opened is not None:
            issues.add(
                ReasonCode.UNKNOWN_ORDER_TYPE.value,
                f"{field}.trigger_basis",
                f"{opened.group(0)} => {TriggerBasis.NEXT_OPEN_TRIGGER.value}",
            )
        elif require:
            issues.add(_missing_order_reason(field), field, section)
        return None
    match = orders[0]
    side = Side.BUY if match.group(1).lower() == "buy" else Side.SELL
    order_type = _order_type(match.group(2))
    price_token = match.group(3)
    price, price_ok = _required_price(field, section, order_type, price_token, issues)
    if order_type is OrderType.STOP_LIMIT:
        issues.add(ReasonCode.INCOMPLETE_STOP_LIMIT.value, f"{field}.order_type", match.group(0))
        return None
    tif = _tif(field, section, issues)
    trigger = _trigger(field, section, issues)
    resolved = _section_date(section)
    _apply_date(field, resolved, issues)
    if (
        not price_ok
        or tif is None
        or trigger is None
        or resolved.status in {"conflict", "unresolved", "malformed", "unsupported"}
    ):
        return None
    evidence: tuple[FieldEvidence, ...] = (
        FieldEvidence(f"{field}.side", match.group(1)),
        FieldEvidence(f"{field}.order_type", match.group(2)),
        FieldEvidence(f"{field}.price", price_token or ""),
        FieldEvidence(f"{field}.time_in_force", tif.value),
        FieldEvidence(f"{field}.trigger_basis", trigger.value),
    )
    if resolved.status == "resolved":
        evidence = (
            *evidence,
            FieldEvidence(f"{field}.session_date", resolved.source_date),
        )
    return PriceOrder(
        side=side,
        order_type=order_type,
        price=price,
        limit_price=None,
        time_in_force=tif,
        trigger_basis=trigger,
        session_date=resolved.resolved,
        session_source_date=resolved.source_date,
        date_resolution_rule=resolved.resolution_rule,
        timezone_assumption=TIMEZONE_ASSUMPTION,
        calendar_assumption=CALENDAR_ASSUMPTION,
        evidence=evidence,
    )


def _missing_order_reason(field: str) -> str:
    reasons = {
        "entry": ReasonCode.MISSING_ENTRY,
        "target": ReasonCode.MISSING_TARGET,
        "protective_stop": ReasonCode.MISSING_STOP,
    }
    return reasons[field].value


def _stop_limit_order(
    field: str,
    section: str,
    pair: re.Match[str],
    issues: _Issues,
) -> PriceOrder | None:
    stop_price = _currency(pair.group(2))
    limit_price = _currency(pair.group(3))
    if stop_price is None or limit_price is None:
        issues.add(ReasonCode.MALFORMED_CURRENCY.value, f"{field}.price", pair.group(0))
        return None
    tif = _tif(field, section, issues)
    trigger = _trigger(field, section, issues)
    resolved = _section_date(section)
    _apply_date(field, resolved, issues)
    if (
        tif is None
        or trigger is None
        or resolved.status in {"conflict", "unresolved", "malformed", "unsupported"}
    ):
        return None
    side = Side.BUY if pair.group(1).lower() == "buy" else Side.SELL
    return PriceOrder(
        side=side,
        order_type=OrderType.STOP_LIMIT,
        price=stop_price,
        limit_price=limit_price,
        time_in_force=tif,
        trigger_basis=trigger,
        session_date=resolved.resolved,
        session_source_date=resolved.source_date,
        date_resolution_rule=resolved.resolution_rule,
        timezone_assumption=TIMEZONE_ASSUMPTION,
        calendar_assumption=CALENDAR_ASSUMPTION,
        evidence=(
            FieldEvidence(f"{field}.side", pair.group(1)),
            FieldEvidence(f"{field}.order_type", "stop limit"),
            FieldEvidence(f"{field}.price", pair.group(2)),
            FieldEvidence(f"{field}.limit_price", pair.group(3)),
            FieldEvidence(f"{field}.time_in_force", tif.value),
            FieldEvidence(f"{field}.trigger_basis", trigger.value),
        ),
    )


def _order_type(raw: str) -> OrderType:
    token = raw.lower().replace("-", " ")
    token = " ".join(token.split())
    if token == "market":
        return OrderType.MARKET
    if token == "limit":
        return OrderType.LIMIT
    if token == "stop":
        return OrderType.STOP
    return OrderType.STOP_LIMIT


def _required_price(
    field: str,
    section: str,
    order_type: OrderType,
    price_token: str | None,
    issues: _Issues,
) -> tuple[Decimal | None, bool]:
    tokens = [match.group(1) for match in _PRICE_TOKEN.finditer(section)]
    if order_type is OrderType.MARKET:
        if tokens:
            issues.add(ReasonCode.MALFORMED_CURRENCY.value, f"{field}.price", tokens[0])
            return None, False
        return None, True
    if price_token is None:
        issues.add(ReasonCode.MALFORMED_CURRENCY.value, f"{field}.price", "")
        return None, False
    parsed = _currency(price_token)
    if parsed is None:
        issues.add(ReasonCode.MALFORMED_CURRENCY.value, f"{field}.price", price_token)
        return None, False
    for token in tokens:
        other = _currency(token)
        if other is None:
            issues.add(ReasonCode.MALFORMED_CURRENCY.value, f"{field}.price", token)
            return None, False
        if other != parsed:
            issues.add(
                ReasonCode.CONFLICTING_ECONOMIC_INSTRUCTION.value,
                f"{field}.price",
                f"{price_token} | {token}",
            )
            return None, False
    return parsed, True


def _currency(token: str) -> Decimal | None:
    if _THOUSANDS.fullmatch(token):
        token = token.replace(",", "")
    if _STRICT_PRICE.fullmatch(token) is None:
        return None
    try:
        number = economic_decimal(token)
    except DomainValidationError:
        return None
    if number <= 0:
        return None
    return number


def _tif(field: str, section: str, issues: _Issues) -> TimeInForce | None:
    day = _DAY.search(section)
    gtc = _GTC.search(section)
    if day and gtc:
        issues.add(
            ReasonCode.CONFLICTING_ECONOMIC_INSTRUCTION.value,
            f"{field}.time_in_force",
            f"{day.group(0)} | {gtc.group(0)}",
        )
        return None
    if day:
        return TimeInForce.DAY
    if gtc:
        return TimeInForce.GTC
    issues.add(ReasonCode.MISSING_TIF.value, f"{field}.time_in_force", section)
    return None


def _trigger(field: str, section: str, issues: _Issues) -> TriggerBasis | None:
    """A parsed stop, limit, or market order is a broker price order.

    "Real order" confirms that basis. Daily-close or next-open wording in the
    same section is a second basis and quarantines instead of collapsing.
    """

    daily = _DAILY_CLOSE.search(section)
    at_open = _AT_OPEN.search(section)
    if daily is not None or at_open is not None:
        cited = [
            match.group(0)
            for match in (daily, at_open, _REAL_ORDER.search(section), _ORDER.search(section))
            if match is not None
        ]
        issues.add(
            ReasonCode.CONFLICTING_ECONOMIC_INSTRUCTION.value,
            f"{field}.trigger_basis",
            " | ".join(cited),
        )
        return None
    return TriggerBasis.BROKER_PRICE_ORDER


def _apply_date(field: str, resolved: DateResolution, issues: _Issues) -> None:
    if resolved.status == "unresolved":
        issues.add(
            ReasonCode.UNRESOLVED_REQUIRED_DATE.value,
            f"{field}.session_date",
            resolved.source_date,
        )
    elif resolved.status == "conflict":
        issues.add(ReasonCode.DATE_CONFLICT.value, f"{field}.session_date", resolved.source_date)
    elif resolved.status == "malformed":
        issues.add(ReasonCode.MALFORMED_DATE.value, f"{field}.session_date", resolved.source_date)
    elif resolved.status == "unsupported":
        issues.add(
            ReasonCode.UNSUPPORTED_DATE_FORMAT.value,
            f"{field}.session_date",
            resolved.source_date,
        )


def _sizing(section: str | None, issues: _Issues) -> Sizing | None:
    if section is None:
        issues.add(ReasonCode.MISSING_SIZING.value, "sizing", "")
        return None
    if len(section) > MAX_EVIDENCE_CHARS:
        issues.add(ReasonCode.OVERSIZED_FIELD.value, "sizing", "")
        return None
    percents = list(_PERCENT.finditer(section))
    if not percents:
        issues.add(ReasonCode.MISSING_SIZING.value, "sizing.percent_equity", section)
        return None
    values: list[Decimal] = []
    for match in percents:
        try:
            number = economic_decimal(match.group(1)) / Decimal("100")
        except DomainValidationError:
            issues.add(ReasonCode.MALFORMED_CURRENCY.value, "sizing.percent_equity", match.group(0))
            return None
        values.append(number)
    if any(value != values[0] for value in values):
        issues.add(
            ReasonCode.CONFLICTING_ECONOMIC_INSTRUCTION.value,
            "sizing.percent_equity",
            " | ".join(match.group(0) for match in percents),
        )
        return None
    example = _EXAMPLE.search(section)
    equity: Decimal | None = None
    allocation: Decimal | None = None
    shares: Decimal | None = None
    if example is not None:
        equity = _currency(example.group(1))
        allocation = _currency(example.group(2))
        try:
            shares = economic_decimal(example.group(3))
        except DomainValidationError:
            shares = None
        if equity is None or allocation is None or shares is None:
            issues.add(ReasonCode.MALFORMED_CURRENCY.value, "sizing.example", example.group(0))
            return None
        if equity * values[0] != allocation:
            issues.add(
                ReasonCode.CONFLICTING_ECONOMIC_INSTRUCTION.value,
                "sizing.example_allocation",
                example.group(0),
            )
            return None
    evidence = [FieldEvidence("sizing.percent_equity", percents[0].group(0))]
    if example is not None:
        evidence.append(FieldEvidence("sizing.example", example.group(0)))
        evidence.append(
            FieldEvidence("sizing.quantity_rounding_policy", QUANTITY_ROUNDING_POLICY)
        )
    return Sizing(
        method="PERCENT_EQUITY",
        percent_equity=values[0],
        example_account_equity=equity,
        example_allocation=allocation,
        example_quantity=shares,
        quantity_rounding_policy=QUANTITY_ROUNDING_POLICY,
        evidence=tuple(evidence),
    )


def _time_exit(
    section: str | None,
    issues: _Issues,
    entry_side: Side | None,
) -> TimeExit | None:
    if section is None:
        return None
    if len(section) > MAX_EVIDENCE_CHARS:
        issues.add(ReasonCode.OVERSIZED_FIELD.value, "time_exit", "")
        return None
    opened = _OPEN_EXIT.search(section)
    if opened is None:
        issues.add(ReasonCode.UNSPECIFIED_TIME_EXIT.value, "time_exit", section)
        return None
    stated = Side.BUY if opened.group(1).lower() == "buy" else Side.SELL
    closing = _closing_side(entry_side)
    if closing is not None and stated is not closing:
        issues.add(
            ReasonCode.CONFLICTING_ECONOMIC_INSTRUCTION.value,
            "time_exit.side",
            opened.group(0),
        )
        return None
    resolved = _section_date(section)
    _apply_date("time_exit", resolved, issues)
    if resolved.status in {"conflict", "unresolved", "malformed", "unsupported"}:
        return None
    return TimeExit(
        side=stated,
        session_event=SessionEvent.REGULAR_SESSION_OPEN,
        source_date=resolved.source_date,
        resolved_date=resolved.resolved,
        resolution_rule=resolved.resolution_rule,
        timezone_assumption=TIMEZONE_ASSUMPTION,
        calendar_assumption=CALENDAR_ASSUMPTION,
        evidence=(
            FieldEvidence("time_exit.side", opened.group(1)),
            FieldEvidence("time_exit.session_event", opened.group(0)),
            FieldEvidence("time_exit.source_date", resolved.source_date),
        ),
    )


def _closing_side(entry_side: Side | None) -> Side | None:
    if entry_side is Side.BUY:
        return Side.SELL
    if entry_side is Side.SELL:
        return Side.BUY
    return None


def _section_date(section: str) -> DateResolution:
    """Bind a date only from authoritative economic sentences in the section."""

    kept: list[str] = []
    for sentence in _SENTENCE_BREAK.split(section):
        stripped = sentence.strip()
        if stripped == "" or _NON_AUTHORITATIVE_SENTENCE.search(stripped):
            continue
        kept.append(stripped)
    scope = " ".join(kept)
    unsupported = _UNSUPPORTED_DATE.search(scope)
    if unsupported is not None:
        return DateResolution(
            "unsupported",
            unsupported.group(0),
            None,
            RESOLUTION_UNSUPPORTED,
        )
    return _resolve_date(scope)


def _resolve_date(section: str) -> DateResolution:
    civil: list[tuple[date, int | None, str]] = []
    occupied: list[tuple[int, int]] = []
    malformed: str | None = None
    for pattern in (_ISO_DATE, _MONTH_DAY_YEAR):
        for match in pattern.finditer(section):
            span = match.span()
            if any(start < span[1] and span[0] < end for start, end in occupied):
                continue
            built = _civil_from_match(match, pattern is _ISO_DATE)
            if built is None:
                malformed = match.group(0)
                continue
            civil.append((*built, match.group(0)))
            occupied.append(span)
    if malformed is not None:
        return DateResolution("malformed", malformed, None, RESOLUTION_MALFORMED)
    if len({item[0] for item in civil}) > 1:
        cited = " | ".join(item[2] for item in civil)
        return DateResolution("conflict", cited, None, RESOLUTION_CONFLICT)
    for resolved, weekday, source in civil:
        if weekday is not None and weekday != resolved.weekday():
            return DateResolution("conflict", source, None, RESOLUTION_CONFLICT)
    masked = _mask(section, occupied)
    partial = _MONTH_DAY.search(masked)
    if partial is not None:
        return DateResolution("unresolved", partial.group(0), None, RESOLUTION_UNRESOLVED)
    leftover = list(_WEEKDAY_ONLY.finditer(masked))
    if not civil:
        if leftover:
            return DateResolution("unresolved", leftover[0].group(0), None, RESOLUTION_UNRESOLVED)
        return DateResolution("absent", "", None, RESOLUTION_ABSENT)
    resolved, _weekday, source = civil[0]
    for match in leftover:
        if _WEEKDAY_INDEX[match.group(1).lower()] != resolved.weekday():
            return DateResolution(
                "conflict",
                f"{source} | {match.group(0)}",
                None,
                RESOLUTION_CONFLICT,
            )
    return DateResolution("resolved", source, resolved, RESOLUTION_EXPLICIT)


def _civil_from_match(match: re.Match[str], iso: bool) -> tuple[date, int | None] | None:
    weekday = _WEEKDAY_INDEX[match.group(1).lower()] if match.group(1) else None
    try:
        if iso:
            resolved = date(int(match.group(2)), int(match.group(3)), int(match.group(4)))
        else:
            month = _MONTH_INDEX[match.group(2).lower()]
            resolved = date(int(match.group(4)), month, int(match.group(3)))
    except ValueError:
        return None
    return resolved, weekday


def _mask(section: str, spans: list[tuple[int, int]]) -> str:
    characters = list(section)
    for start, end in spans:
        for index in range(start, end):
            characters[index] = " "
    return "".join(characters)


def _economic_key(instruction: NewTradeInstruction) -> tuple[object, ...]:
    """Project every economic dataclass field. Omissions require an explicit exclusion."""

    projected = _project_value(instruction)
    if not isinstance(projected, tuple):
        raise RuntimeError("economic projection must be a tuple")
    return projected


def _project_value(value: object) -> object:
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return tuple(_project_value(item) for item in value)
    if is_dataclass(value) and not isinstance(value, type):
        return tuple(
            (field.name, _project_value(getattr(value, field.name)))
            for field in fields(value)
            if field.name not in _PROJECTION_EXCLUDED
        )
    return value


def assign_instruction_ids(
    extraction: Extraction,
    digest: str,
) -> tuple[CanonicalInstructionEnvelope, ...]:
    """Economic identity is the raw-byte digest plus index, never the provider id."""

    return tuple(
        CanonicalInstructionEnvelope(
            instruction_id=f"v1:email_instruction:{digest}:{index}",
            message_type=MessageType.NEW_TRADE,
            payload=item,
            evidence=item.evidence,
        )
        for index, item in enumerate(extraction.instructions)
    )
