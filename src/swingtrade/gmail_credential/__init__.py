"""Offline Gmail credential adapter.

This package stores one synthetic development credential behind an injected
mock. It does not call Windows Credential Manager.

``CRED_PERSIST_LOCAL_MACHINE`` keeps a real credential for later logon
sessions of the same Windows user on the same computer. It does not expose
that credential to every Windows user. It is not hardware-backed protection,
and it does not stop code running in that same user session from reading it.

A fake store surviving a new adapter instance is not evidence that a Windows
reboot would. Releasing a mock allocation is not ``CredFree`` certification.
The in-process lock is not cross-process atomicity. Methods on the mock whose
names end in ``holding_lock`` must run while that lock is held. The adapter
does so. Native ``CredWriteW`` replaces an existing match; store never uses
that replace behavior.

Accepted ADR-0006 does not set a 2,560-byte blob ceiling. This mock does not
invent one. A future native backend would apply the platform limit only under
a later authorization. ``synthetic_fixture`` is an offline type check, not a
cryptographic boundary: same-process code can still build a
``SyntheticSecret``, and that object can enter only the injected mock.
Case-fold rejection stays conservative for non-ASCII confusables and does not
create a second mock credential.
"""

from swingtrade.gmail_credential.adapter import GmailCredentialAdapter
from swingtrade.gmail_credential.errors import CredentialOperationError
from swingtrade.gmail_credential.identity import (
    CANONICAL_TARGET,
    CRED_PERSIST_ENTERPRISE,
    CRED_PERSIST_LOCAL_MACHINE,
    CRED_PERSIST_SESSION,
    CRED_TYPE_GENERIC,
    NATIVE_BACKEND_ENABLED,
)
from swingtrade.gmail_credential.mock_port import MockCredentialPort
from swingtrade.gmail_credential.secret import SyntheticSecret, synthetic_fixture

__all__ = [
    "CANONICAL_TARGET",
    "CRED_PERSIST_ENTERPRISE",
    "CRED_PERSIST_LOCAL_MACHINE",
    "CRED_PERSIST_SESSION",
    "CRED_TYPE_GENERIC",
    "NATIVE_BACKEND_ENABLED",
    "CredentialOperationError",
    "GmailCredentialAdapter",
    "MockCredentialPort",
    "SyntheticSecret",
    "synthetic_fixture",
]
