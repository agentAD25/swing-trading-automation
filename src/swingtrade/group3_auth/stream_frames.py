"""Offline newline-delimited stream frames. No connection and no restart."""

from __future__ import annotations

import json

from swingtrade.contracts.monitoring import MonitoringEmitter
from swingtrade.group3_auth.monitoring import emit_auth_decision
from swingtrade.group3_auth.outcomes import AuthDecision, OutcomeCode, decision

_MAX_BUFFER = 65536
_EXACT_MARKERS = {
    "EndSnapshot": "END_SNAPSHOT",
    "GoAway": "GO_AWAY",
}


class StreamFrame:
    """One classified frame. Payload bytes are not rendered."""

    __slots__ = ("connect_allowed", "decision", "marker", "restart_performed")

    def __init__(self, result: AuthDecision, marker: str | None) -> None:
        self.decision = result
        self.marker = marker
        self.connect_allowed = False
        self.restart_performed = False

    def __repr__(self) -> str:
        return f"StreamFrame({self.decision.reason})"


class StreamFrameClassifier:
    """Buffer chunks locally. Documented markers do not open a socket."""

    __slots__ = ("_buffer",)

    def __init__(self) -> None:
        self._buffer = bytearray()

    @property
    def connect_allowed(self) -> bool:
        return False

    def push(
        self,
        chunk: object,
        *,
        emitter: MonitoringEmitter | None = None,
    ) -> tuple[StreamFrame, ...]:
        if type(chunk) is not bytes:
            frame = _frame(decision(OutcomeCode.REJECTED, "MALFORMED_FRAME"), None)
            emit_auth_decision(emitter, frame.decision)
            return (frame,)
        self._buffer.extend(chunk)
        if len(self._buffer) > _MAX_BUFFER:
            self._buffer.clear()
            frame = _frame(decision(OutcomeCode.REJECTED, "MALFORMED_FRAME"), None)
            emit_auth_decision(emitter, frame.decision)
            return (frame,)
        frames: list[StreamFrame] = []
        while True:
            newline = self._buffer.find(b"\n")
            if newline < 0:
                break
            raw = bytes(self._buffer[:newline])
            del self._buffer[: newline + 1]
            if raw.endswith(b"\r"):
                raw = raw[:-1]
            frame = _classify_line(raw)
            emit_auth_decision(emitter, frame.decision)
            frames.append(frame)
        return tuple(frames)

    def finish(self, *, emitter: MonitoringEmitter | None = None) -> tuple[StreamFrame, ...]:
        """A trailing fragment without a newline is not a frame."""
        if not self._buffer:
            return ()
        self._buffer.clear()
        frame = _frame(decision(OutcomeCode.REJECTED, "INCOMPLETE_FRAME"), None)
        emit_auth_decision(emitter, frame.decision)
        return (frame,)


def _classify_line(raw: bytes) -> StreamFrame:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return _frame(decision(OutcomeCode.REJECTED, "MALFORMED_FRAME"), None)
    if text == "":
        return _frame(decision(OutcomeCode.REJECTED, "MALFORMED_FRAME"), None)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return _frame(decision(OutcomeCode.REJECTED, "MALFORMED_FRAME"), None)
    if type(payload) is not dict:
        return _frame(decision(OutcomeCode.UNKNOWN, "UNKNOWN"), None)
    keys = set(payload)
    if any(type(key) is not str for key in keys):
        return _frame(decision(OutcomeCode.UNKNOWN, "UNKNOWN"), None)
    if "StreamStatus" in payload and "ERROR" in payload:
        return _frame(decision(OutcomeCode.UNKNOWN, "UNKNOWN"), None)
    if "StreamStatus" in payload:
        return _stream_status(payload)
    if "ERROR" in payload:
        return _frame(decision(OutcomeCode.CLASSIFIED, "ERROR"), "ERROR")
    return _frame(decision(OutcomeCode.CLASSIFIED, "UNMARKED"), None)


def _stream_status(payload: dict[object, object]) -> StreamFrame:
    if set(payload) != {"StreamStatus"}:
        return _frame(decision(OutcomeCode.UNKNOWN, "UNKNOWN"), None)
    status = payload["StreamStatus"]
    if type(status) is not str:
        return _frame(decision(OutcomeCode.UNKNOWN, "UNKNOWN"), None)
    marker = _EXACT_MARKERS.get(status)
    if marker is None:
        return _frame(decision(OutcomeCode.UNKNOWN, "UNKNOWN"), None)
    return _frame(decision(OutcomeCode.CLASSIFIED, marker), marker)


def _frame(result: AuthDecision, marker: str | None) -> StreamFrame:
    return StreamFrame(result, marker)
