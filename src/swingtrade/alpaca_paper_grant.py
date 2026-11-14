"""Signed paper-account grant verification. No credential and no provider call.

The production trust anchor is empty until an Operator installs a public
modulus in this module. A caller cannot pass a key, a boolean, or a path.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from swingtrade.alpaca_paper_account_read import ACCOUNT_URL
from swingtrade.alpaca_paper_custody import PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET

GRANT_NAME = "LANE1_ALPACA_STANDING_PAPER_ACCOUNT_READ_AUTHORIZED"
DAILY_CEILING = 30
_DIGESTINFO = bytes.fromhex("3031300d060960864801650304020105000420")
_TARGETS = (PAPER_KEY_ID_TARGET, PAPER_SECRET_TARGET)
PRODUCTION_PUBLIC_MODULUS: int | None = None
PRODUCTION_PUBLIC_EXPONENT = 65537


class _Issue:
    """Private issuance token. Production entry points never accept a grant object."""


_ISSUE = _Issue()


class GrantError(RuntimeError):
    """Reason code only."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class VerifiedGrant:
    """A signature-checked grant. The constructor rejects objects it did not issue."""

    __slots__ = (
        "account_id",
        "activated_at",
        "credential_targets",
        "daily_ceiling",
        "endpoint",
        "expires_at",
        "grant_id",
        "ledger_genesis",
        "ledger_id",
        "method",
        "provenance",
        "revocation_generation",
        "windows_sid",
        "_issue",
    )

    def __init__(self, fields: dict[str, object], issue: _Issue) -> None:
        if issue is not _ISSUE:
            raise GrantError("GRANT_UNVERIFIED")
        account_id = _text(fields.get("account_id"))
        grant_id = _text(fields.get("grant_id"))
        ledger_id = _text(fields.get("ledger_id"))
        ledger_genesis = _hex64(fields.get("ledger_genesis"))
        windows_sid = _text(fields.get("windows_sid"))
        provenance = _text(fields.get("provenance"))
        method = _text(fields.get("method"))
        endpoint = _text(fields.get("endpoint"))
        activated = _text(fields.get("activated_at"))
        expires = _text(fields.get("expires_at"))
        ceiling = fields.get("daily_ceiling")
        generation = fields.get("revocation_generation")
        targets = fields.get("credential_targets")
        if (
            account_id is None
            or grant_id is None
            or ledger_id is None
            or ledger_genesis is None
            or windows_sid is None
            or provenance is None
            or method is None
            or endpoint is None
            or activated is None
            or expires is None
            or type(ceiling) is not int
            or type(generation) is not int
            or targets != list(_TARGETS)
        ):
            raise GrantError("GRANT_UNVERIFIED")
        self.account_id = account_id
        self.grant_id = grant_id
        self.ledger_id = ledger_id
        self.ledger_genesis = ledger_genesis
        self.windows_sid = windows_sid
        self.provenance = provenance
        self.method = method
        self.endpoint = endpoint
        self.activated_at = _moment(activated)
        self.expires_at = _moment(expires)
        self.daily_ceiling = ceiling
        self.revocation_generation = generation
        self.credential_targets = tuple(_TARGETS)
        self._issue = issue

    def ensure(self) -> None:
        if self._issue is not _ISSUE:
            raise GrantError("GRANT_UNVERIFIED")

    def __repr__(self) -> str:
        return "VerifiedGrant()"


def verify_signed_grant(
    payload: bytes,
    signature: bytes,
    modulus: int,
    exponent: int,
    *,
    observed_sid: str,
    now: datetime,
    revocation_payload: bytes,
    revocation_signature: bytes,
) -> VerifiedGrant:
    """Check one signed grant and one signed revocation statement."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise GrantError("GRANT_CLOCK_DENIED")
    if not _verify_pkcs1_sha256(payload, signature, modulus, exponent):
        raise GrantError("GRANT_SIGNATURE_INVALID")
    if not _verify_pkcs1_sha256(revocation_payload, revocation_signature, modulus, exponent):
        raise GrantError("REVOCATION_SIGNATURE_INVALID")
    fields = _object(payload)
    revocation = _object(revocation_payload)
    _require_terms(fields)
    if payload != canonical_grant(fields):
        raise GrantError("GRANT_MALFORMED")
    if fields["windows_sid"] != observed_sid:
        raise GrantError("IDENTITY_MISMATCH")
    activated = _moment(_text(fields["activated_at"]) or "")
    expires = _moment(_text(fields["expires_at"]) or "")
    if now < activated:
        raise GrantError("GRANT_NOT_ACTIVE")
    if now >= expires:
        raise GrantError("GRANT_EXPIRED")
    generation = fields["revocation_generation"]
    if revocation.get("generation") != generation or type(generation) is not int:
        raise GrantError("GRANT_REVOCATION_MISMATCH")
    revoked = revocation.get("revoked_grant_ids")
    if type(revoked) is not list or any(type(item) is not str for item in revoked):
        raise GrantError("GRANT_REVOCATION_MISMATCH")
    if fields["grant_id"] in revoked:
        raise GrantError("GRANT_REVOKED")
    return VerifiedGrant(fields, _ISSUE)


def authorize_production() -> VerifiedGrant:
    """Production entry. It accepts no caller grant, key, path, clock, or boolean."""
    if PRODUCTION_PUBLIC_MODULUS is None:
        raise GrantError("GRANT_ANCHOR_ABSENT")
    if sys.platform != "win32":
        raise GrantError("RUNTIME_PLATFORM_DENIED")
    grant_blob, revocation_blob = _read_installed_bundles()
    return load_verified_bundle(
        grant_blob,
        revocation_blob,
        PRODUCTION_PUBLIC_MODULUS,
        PRODUCTION_PUBLIC_EXPONENT,
        observed_sid=current_windows_sid(),
        now=datetime.now(UTC),
    )


def load_verified_bundle(
    grant_blob: bytes,
    revocation_blob: bytes,
    modulus: int,
    exponent: int,
    *,
    observed_sid: str,
    now: datetime,
) -> VerifiedGrant:
    """Verify two installed bundles. The caller of production code cannot choose their paths."""
    payload, signature = split_bundle(grant_blob)
    revocation_payload, revocation_signature = split_bundle(revocation_blob)
    return verify_signed_grant(
        payload,
        signature,
        modulus,
        exponent,
        observed_sid=observed_sid,
        now=now,
        revocation_payload=revocation_payload,
        revocation_signature=revocation_signature,
    )


def split_bundle(blob: bytes) -> tuple[bytes, bytes]:
    """Split ``SWTG1\\n`` + hex signature + ``\\n`` + payload."""
    prefix = b"SWTG1\n"
    if not blob.startswith(prefix):
        raise GrantError("GRANT_BUNDLE_MALFORMED")
    rest = blob[len(prefix) :]
    marker = rest.find(b"\n")
    if marker <= 0:
        raise GrantError("GRANT_BUNDLE_MALFORMED")
    encoded = rest[:marker]
    payload = rest[marker + 1 :]
    try:
        signature = bytes.fromhex(encoded.decode("ascii"))
    except (UnicodeError, ValueError):
        raise GrantError("GRANT_BUNDLE_MALFORMED") from None
    if payload == b"" or signature == b"":
        raise GrantError("GRANT_BUNDLE_MALFORMED")
    return payload, signature


def canonical_grant(fields: dict[str, object]) -> bytes:
    """Canonical payload bytes. Signature input must equal this encoding."""
    body = {
        "account_id": fields.get("account_id"),
        "activated_at": fields.get("activated_at"),
        "capability": fields.get("capability"),
        "credential_targets": fields.get("credential_targets"),
        "daily_ceiling": fields.get("daily_ceiling"),
        "endpoint": fields.get("endpoint"),
        "expires_at": fields.get("expires_at"),
        "grant_id": fields.get("grant_id"),
        "ledger_genesis": fields.get("ledger_genesis"),
        "ledger_id": fields.get("ledger_id"),
        "method": fields.get("method"),
        "provenance": fields.get("provenance"),
        "revocation_generation": fields.get("revocation_generation"),
        "windows_sid": fields.get("windows_sid"),
    }
    return json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")


def verify_pkcs1_sha256(message: bytes, signature: bytes, modulus: int, exponent: int) -> bool:
    """Public PKCS#1 v1.5 SHA-256 check. This does not sign."""
    return _verify_pkcs1_sha256(message, signature, modulus, exponent)


def _verify_pkcs1_sha256(message: bytes, signature: bytes, modulus: int, exponent: int) -> bool:
    if type(modulus) is not int or type(exponent) is not int:
        return False
    if modulus.bit_length() < 2048 or exponent <= 1:
        return False
    size = (modulus.bit_length() + 7) // 8
    if len(signature) != size:
        return False
    signature_int = int.from_bytes(signature, "big")
    if signature_int <= 0 or signature_int >= modulus:
        return False
    encoded = pow(signature_int, exponent, modulus).to_bytes(size, "big")
    digest = hashlib.sha256(message).digest()
    tail = _DIGESTINFO + digest
    if len(tail) + 11 > size:
        return False
    padding = b"\xff" * (size - len(tail) - 3)
    expected = b"\x00\x01" + padding + b"\x00" + tail
    return hmac.compare_digest(encoded, expected)


def _require_terms(fields: dict[str, object]) -> None:
    targets = fields.get("credential_targets")
    if (
        fields.get("capability") != GRANT_NAME
        or fields.get("method") != "GET"
        or fields.get("endpoint") != ACCOUNT_URL
        or fields.get("daily_ceiling") != DAILY_CEILING
        or targets != list(_TARGETS)
        or _text(fields.get("provenance")) is None
        or _text(fields.get("account_id")) is None
        or _text(fields.get("grant_id")) is None
        or _text(fields.get("ledger_id")) is None
        or _hex64(fields.get("ledger_genesis")) is None
        or _text(fields.get("windows_sid")) is None
        or type(fields.get("revocation_generation")) is not int
        or not _ordered(fields.get("activated_at"), fields.get("expires_at"))
    ):
        raise GrantError("GRANT_TERMS_REJECTED")


def _object(payload: bytes) -> dict[str, object]:
    try:
        parsed = json.loads(payload.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeError, json.JSONDecodeError):
        raise GrantError("GRANT_MALFORMED") from None
    if type(parsed) is not dict:
        raise GrantError("GRANT_MALFORMED")
    return parsed


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    found: dict[str, object] = {}
    for key, value in pairs:
        if key in found:
            raise GrantError("DUPLICATE_FIELD")
        found[key] = value
    return found


def _ordered(activated: object, expires: object) -> bool:
    start = _text(activated)
    end = _text(expires)
    if start is None or end is None:
        return False
    return _moment(start) < _moment(end)


def _text(value: object) -> str | None:
    if type(value) is not str or value == "" or value != value.strip():
        return None
    return value


def _hex64(value: object) -> str | None:
    text = _text(value)
    if text is None or len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        return None
    return text


def _moment(value: str) -> datetime:
    if not value.endswith("Z"):
        raise GrantError("GRANT_MALFORMED")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        raise GrantError("GRANT_MALFORMED") from None
    return parsed


def current_windows_sid() -> str:
    """Read the process SID. Tests do not call this, and import does not."""
    if sys.platform != "win32":
        raise GrantError("RUNTIME_PLATFORM_DENIED")
    import ctypes
    from ctypes import wintypes

    advapi = cast(Any, ctypes).WinDLL("advapi32")
    kernel = cast(Any, ctypes).WinDLL("kernel32")
    advapi.OpenProcessToken.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    )
    advapi.OpenProcessToken.restype = wintypes.BOOL
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    token = wintypes.HANDLE()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
        raise GrantError("IDENTITY_UNAVAILABLE")
    try:
        needed = wintypes.DWORD(0)
        advapi.GetTokenInformation.argtypes = (
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        )
        advapi.GetTokenInformation.restype = wintypes.BOOL
        advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(needed))
        buffer = ctypes.create_string_buffer(needed.value)
        if not advapi.GetTokenInformation(token, 1, buffer, needed, ctypes.byref(needed)):
            raise GrantError("IDENTITY_UNAVAILABLE")
        sid = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p)).contents
        text = ctypes.c_wchar_p()
        advapi.ConvertSidToStringSidW.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_wchar_p),
        )
        advapi.ConvertSidToStringSidW.restype = wintypes.BOOL
        if not advapi.ConvertSidToStringSidW(sid, ctypes.byref(text)) or not text.value:
            raise GrantError("IDENTITY_UNAVAILABLE")
        try:
            return text.value
        finally:
            kernel.LocalFree.argtypes = (ctypes.c_void_p,)
            kernel.LocalFree.restype = ctypes.c_void_p
            kernel.LocalFree(text)
    finally:
        kernel.CloseHandle(token)


def program_data_directory() -> Path:
    """Known ProgramData folder. This is a location, not an authorization flag."""
    if sys.platform != "win32":
        raise GrantError("GRANT_NOT_INSTALLED")
    import ctypes
    from ctypes import wintypes

    class _Guid(ctypes.Structure):
        _fields_ = (
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", wintypes.BYTE * 8),
        )

    folder = _Guid(
        0x62AB5D82,
        0xFDC1,
        0x4DC3,
        (wintypes.BYTE * 8)(0xA9, 0xDD, 0x07, 0x0D, 0x1D, 0x49, 0x5D, 0x97),
    )
    ole = cast(Any, ctypes).WinDLL("ole32")
    ole.SHGetKnownFolderPath.argtypes = (
        ctypes.POINTER(_Guid),
        wintypes.DWORD,
        wintypes.HANDLE,
        ctypes.POINTER(ctypes.c_wchar_p),
    )
    ole.SHGetKnownFolderPath.restype = ctypes.c_long
    ole.CoTaskMemFree.argtypes = (ctypes.c_void_p,)
    ole.CoTaskMemFree.restype = None
    text = ctypes.c_wchar_p()
    result = ole.SHGetKnownFolderPath(ctypes.byref(folder), 0, None, ctypes.byref(text))
    if result != 0 or not text.value:
        raise GrantError("GRANT_NOT_INSTALLED")
    try:
        return Path(text.value)
    finally:
        ole.CoTaskMemFree(text)


def _read_installed_bundles() -> tuple[bytes, bytes]:
    root = program_data_directory()
    base = root / "swing-trading" / "alpaca-paper-account-read"
    return _read_exact(base / "grant.bundle"), _read_exact(base / "revocation.bundle")


def _read_exact(path: Path) -> bytes:
    if path.is_symlink():
        raise GrantError("GRANT_NOT_INSTALLED")
    try:
        size = path.stat().st_size
        payload = path.read_bytes()
    except OSError:
        raise GrantError("GRANT_NOT_INSTALLED") from None
    if size <= 0 or size > 65536 or len(payload) != size:
        raise GrantError("GRANT_NOT_INSTALLED")
    return payload
