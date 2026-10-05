"""Fixture mail builder. Addresses stay on example.invalid."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parents[1] / "fixtures" / "group4_email"
MAILBOX = "signals@example.invalid"


def body(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def plain_message(text: str, message_id: str = "<tday@example.invalid>") -> bytes:
    header = (
        f"Message-ID: {message_id}\r\n"
        f"From: {MAILBOX}\r\n"
        f"To: {MAILBOX}\r\n"
        "Subject: fixture\r\n"
        "MIME-Version: 1.0\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "\r\n"
    )
    return (header + text.replace("\n", "\r\n")).encode("utf-8")


@pytest.fixture
def dated_raw() -> bytes:
    return plain_message(body("tday_dated.txt"), "<tday-dated@example.invalid>")


@pytest.fixture
def undated_raw() -> bytes:
    return plain_message(body("tday_undated.txt"), "<tday-undated@example.invalid>")
