from __future__ import annotations

import socket
from pathlib import Path

from swingtrade.contracts.monitoring import NullMonitoringEmitter
from swingtrade.group3_auth import OutcomeCode, StreamFrameClassifier

_END = b'{"StreamStatus":"EndSnapshot"}\n'
_GOAWAY = b'{"StreamStatus":"GoAway"}\n'


def test_end_snapshot_may_span_chunks_and_cannot_connect() -> None:
    classifier = StreamFrameClassifier()
    assert classifier.connect_allowed is False
    assert classifier.push(_END[:12]) == ()
    frames = classifier.push(_END[12:])
    assert len(frames) == 1
    frame = frames[0]
    assert frame.decision.code is OutcomeCode.CLASSIFIED
    assert frame.decision.reason == "END_SNAPSHOT"
    assert frame.marker == "END_SNAPSHOT"
    assert frame.connect_allowed is False
    assert frame.restart_performed is False
    assert frame.decision.network_permitted is False
    assert frame.decision.safe_to_retry is False


def test_goaway_is_classified_without_restart() -> None:
    frames = StreamFrameClassifier().push(_GOAWAY)
    assert frames[0].marker == "GO_AWAY"
    assert frames[0].decision.reason == "GO_AWAY"
    assert frames[0].restart_performed is False
    assert frames[0].connect_allowed is False


def test_error_key_is_the_documented_marker_and_payload_is_not_rendered() -> None:
    raw = b'{"ERROR":"terminate","Message":"hidden-detail"}\n'
    frames = StreamFrameClassifier().push(raw)
    assert frames[0].decision.code is OutcomeCode.CLASSIFIED
    assert frames[0].decision.reason == "ERROR"
    assert frames[0].marker == "ERROR"
    assert frames[0].connect_allowed is False
    assert "hidden-detail" not in repr(frames[0])


def test_rate_limit_error_spelling_is_not_the_stream_marker() -> None:
    raw = b'{"Error":"TooManyRequests","Message":"Rate quota exceeded"}\n'
    frames = StreamFrameClassifier().push(raw)
    assert frames[0].decision.code is OutcomeCode.CLASSIFIED
    assert frames[0].decision.reason == "UNMARKED"
    assert frames[0].marker is None
    assert frames[0].decision.safe_to_retry is False


def test_extra_or_unknown_stream_status_is_unknown() -> None:
    classifier = StreamFrameClassifier()
    extra = classifier.push(b'{"StreamStatus":"EndSnapshot","x":1}\n')
    unknown = classifier.push(b'{"StreamStatus":"Heartbeat"}\n')
    both = classifier.push(b'{"StreamStatus":"GoAway","ERROR":"x"}\n')
    for frame in (*extra, *unknown, *both):
        assert frame.decision.code is OutcomeCode.UNKNOWN
        assert frame.decision.safe_to_retry is False
        assert frame.marker is None
        assert frame.restart_performed is False
        assert frame.connect_allowed is False


def test_heartbeat_object_is_unmarked_and_has_no_timeout() -> None:
    classifier = StreamFrameClassifier()
    frames = classifier.push(b'{"Heartbeat":5}\n')
    assert frames[0].decision.reason == "UNMARKED"
    assert frames[0].marker is None
    assert not hasattr(classifier, "timeout")
    assert not hasattr(classifier, "reconnect")
    source = Path("src/swingtrade/group3_auth/stream_frames.py").read_text(encoding="utf-8")
    assert "Heartbeat" not in source
    assert "import socket" not in source


def test_multiple_frames_crlf_and_non_objects() -> None:
    classifier = StreamFrameClassifier()
    frames = classifier.push(b'{"StreamStatus":"EndSnapshot"}\r\n{"StreamStatus":"GoAway"}\n')
    assert [frame.marker for frame in frames] == ["END_SNAPSHOT", "GO_AWAY"]
    parsed = classifier.push(b"[]\nnull\n")
    assert [frame.decision.code for frame in parsed] == [OutcomeCode.UNKNOWN, OutcomeCode.UNKNOWN]


def test_malformed_non_bytes_and_incomplete_frames_fail_closed() -> None:
    classifier = StreamFrameClassifier()
    emitter = NullMonitoringEmitter()
    bad = classifier.push(b"{not json}\n\n\xff\n", emitter=emitter)
    assert [frame.decision.reason for frame in bad] == [
        "MALFORMED_FRAME",
        "MALFORMED_FRAME",
        "MALFORMED_FRAME",
    ]
    text = classifier.push("not-bytes", emitter=emitter)
    assert text[0].decision.reason == "MALFORMED_FRAME"
    held = classifier.push(b'{"StreamStatus":"GoAway"}')
    assert held == ()
    done = classifier.finish(emitter=emitter)
    assert done[0].decision.reason == "INCOMPLETE_FRAME"
    assert done[0].restart_performed is False
    assert "GoAway" not in repr(done[0])
    assert classifier.finish() == ()
    recovered = classifier.push(_END)
    assert recovered[0].marker == "END_SNAPSHOT"
    assert emitter.conditions
    assert all("GoAway" not in str(item.safe_context) for item in emitter.conditions)


def test_oversized_buffer_is_rejected_without_parsing() -> None:
    classifier = StreamFrameClassifier()
    frames = classifier.push(b"a" * 65537)
    assert frames[0].decision.reason == "MALFORMED_FRAME"
    assert classifier.finish() == ()
    assert classifier.push(_GOAWAY)[0].marker == "GO_AWAY"


def test_stream_classification_does_not_open_sockets(monkeypatch) -> None:
    def explode(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket")

    monkeypatch.setattr(socket, "socket", explode)
    monkeypatch.setattr(socket, "create_connection", explode)
    frames = StreamFrameClassifier().push(_END + _GOAWAY)
    assert [frame.marker for frame in frames] == ["END_SNAPSHOT", "GO_AWAY"]
    assert all(frame.connect_allowed is False for frame in frames)
