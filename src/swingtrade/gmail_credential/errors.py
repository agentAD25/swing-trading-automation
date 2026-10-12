"""Fail-closed errors that carry a code and no credential material."""

from __future__ import annotations


class CredentialOperationError(Exception):
    """Offline credential operation failed closed.

    ``code`` is a stable identifier. The message is that code. Caller-supplied
    targets and secret bytes are never stored on the exception.
    """

    def __init__(self, code: str) -> None:
        if type(code) is not str or code == "":
            code = "fail_closed"
        super().__init__(code)
        self.code = code

    def __repr__(self) -> str:
        return f"CredentialOperationError({self.code!r})"

    def __str__(self) -> str:
        return self.code
