# ADR-0006: Lane 3 offline Windows credential adapter

- Status: Proposed
- Date: 2026-10-09
- Sole Phase 1 decider: Human Operator
- Scope: Offline, synthetic, mocked credential-storage interface for one recorded Lane 3 development target
- Supersedes: None
- Superseded by: None

## Context

Lane 3 owns Gmail OAuth and the read-only source adapter. ADR-0004 remains
Proposed. Its scope is Gmail acquisition, and its Decision section stays
blank. This record does not supersede ADR-0002, ADR-0003, or ADR-0004.
ADR-0005 is the TradeStation proposal on open PR #22 and is not reused.
`DEP-GMAIL-001` remains OPEN.

The Operator's local custody design is already recorded on commit
`eae6a9be0d5c8485f9c7bf0df5b2283954f742d8`, tree
`253b5221c9d3e31de4d6b1b56991405909fd1027`, which is on draft PR #27 and
is not canonical `main`. That record names Windows Credential Manager,
`CRED_TYPE_GENERIC` = 1, `CRED_PERSIST_LOCAL_MACHINE` = 2, the current
operator-controlled Windows user, incremental cost 0 USD, and the target
identifier `swing-trading/lane3/gmail/dev/refresh-token`. The identifier
is not a provisioning instruction. Local-machine persistence is not
hardware-backed security. This proposal does not invent a second custody
design.

Canonical `main` at the branch point of this proposal is
`2c895291a3b4282f8cf5c7426c705bfdab365c47`, tree
`25ebd09e495bb2db7b7f856963a0af876a378457`. No equivalent ADR file exists
on that tree or on PR #27 head
`6e20bff808802a467789b5e882c5c38d075669ca`. No credential-adapter source
or test exists on `main`.

The authoring agent does not accept this ADR. Only the human Operator may
move it to Accepted. `docs/adr/README.md` states that an Accepted ADR
still does not authorize implementation, credentials, broker or network
activity, TradeStation `SIM`, or `LIVE`. Implementation permission also
requires an explicit sentence in `docs/CURRENT_STATE.md` on canonical
`main`. That sentence is not part of this proposal, and this proposal
adds no application code.

## Safety impact

`DRY_RUN` remains the only authorized execution mode. This proposal does
not authorize a real credential read or write, a Google token, OAuth
consent, token exchange, a refresh operation, a Gmail API request,
mailbox access, a TradeStation TokenStore change, broker activity, a
`SIM` order, a `LIVE` order, operational database provisioning, a paid
service, or Gmail Gate B.

A future offline module, if separately authorized, may use only synthetic
non-sensitive values and mocked `advapi32` calls. An unmocked Windows
credential API call and any external network call fail closed. The
recorded target name is an identifier in tests. It is not an instruction
to create a Windows credential. Credential bytes, if a later test
supplies synthetic ones, must not appear in assertions' failure output,
logs, or Git.

Group 4A and Accepted ADR-0003 are unchanged.
`EMAIL_RETENTION_POLICY` remains
`HASH_PROVIDER_REF_FIELD_EVIDENCE`. The certified parser is not a
credential store.

## Options considered

### Option A — Offline mocked adapter for the recorded target

Specify one Python credential-storage interface and one Windows
Credential Manager adapter. The adapter speaks `CRED_TYPE_GENERIC` and
requests `CRED_PERSIST_LOCAL_MACHINE` for the current process token's
Windows user, using only the recorded target identifier. Unit tests are
deterministic and offline. They cover store, retrieve, replace, and
delete, plus collision, missing entry, bad logon session, unsupported
persistence, API failure, restart of the fake store, redaction, and
rejection of every other target. The Windows boundary is a mock. A test
fails if the mock is bypassed or if a network call is attempted.

Benefits: matches the design already recorded on `eae6a9be` and keeps
real secrets out of the suite. Costs: a later accepted ADR plus a
current-state sentence would still be required before any code. Risks:
a mock can pass while a real Windows call would fail. That gap stays
outside this proposal.

### Option B — Documentation only

Leave the design in the PR #27 journal and add no adapter interface and
no tests. Benefits: no new module to mistake for permission. Costs: the
offline contract stays narrative, so a later implementation has no
Proposed decision to accept or reject. This proposal does not select a
different store. Cloud secret managers, ignored environment files, the
broker TokenStore, and DPAPI-as-a-second-design are outside this record.

## Decision

## Consequences

If the Operator later accepts this exact proposal, the only decision
accepted is the offline synthetic and mocked adapter described in
Option A. Acceptance still does not authorize coding. Coding begins
only after a later integration gate places both the Accepted ADR and an
explicit implementation sentence on canonical `main`, and that
authorization commit adds no application code.

Until then, Lane 3 must not add the adapter. `DEP-GMAIL-001` stays
OPEN. ADR-0004 stays Proposed. Real OAuth consent remains unauthorized.
Rollback of this proposal, while it is Proposed, is to add no code and
not to treat the target identifier as created.

## Validation and rollback

A verifier who did not author this file reviews the exact commit and
tree that introduce it. Repository pytest and PostgreSQL-backed tests
are not part of this draft. No Windows API is called here.

Future offline tests, after a separate implementation authorization,
are not evidence for this proposal. They would need to show at least:

- an existing target collides and is not overwritten
- a missing target fails closed on retrieve and delete
- an invalid Windows security context fails closed
- persistence other than `CRED_PERSIST_LOCAL_MACHINE` is rejected
- store, retrieve, replace, and delete failures fail closed
- a fake restart still returns a synthetic value stored with local-machine persistence
- exceptions and logs omit synthetic secret bytes
- any other target, including a TradeStation name, is rejected before the mock
- a second store without replace collides
- an interrupted write is not reported as success
- replace fails when the target is absent
- a second delete fails
- an unmocked `advapi32` call or any external network call fails the test

Rollback is to keep this ADR Proposed, or for the Operator to reject
it, and to write no adapter.

## Unresolved questions

- Whether the Operator accepts or rejects this exact proposal. The
  authoring agent cannot decide.
- The exact commit and tree a later independent verifier will attest.
  That attestation does not exist yet.
- The current-state sentence that would authorize implementation. It is
  intentionally absent.
- How a future real refresh token would be stored. This identifier is
  not that store, and consent is not authorized.
- Client id and client secret custody. They are outside the recorded
  target and are not decided here.

## Evidence

- Repository: `docs/ENGINEERING_JOURNAL.md` at
  `eae6a9be0d5c8485f9c7bf0df5b2283954f742d8`, tree
  `253b5221c9d3e31de4d6b1b56991405909fd1027`. Accessed 2026-10-09.
  Supports: the Operator recorded Windows Credential Manager,
  `CRED_TYPE_GENERIC` = 1, `CRED_PERSIST_LOCAL_MACHINE` = 2, the
  current operator-controlled Windows user, target identifier
  `swing-trading/lane3/gmail/dev/refresh-token`, and incremental cost
  0 USD, and did not authorize runtime use. The same commit states
  that local-machine persistence is not hardware-backed security.
  Limitation: the commit is on draft PR #27, not on canonical `main`.
- Repository: `docs/adr/README.md` on canonical `main`
  `2c895291a3b4282f8cf5c7426c705bfdab365c47`. Accessed 2026-10-09.
  Supports: only the human Operator may accept a Phase 1 ADR, and
  acceptance alone does not authorize implementation, credentials,
  broker or network activity, `SIM`, or `LIVE`.
- Repository: `docs/adr/0004-gmail-readonly-corpus-acquisition.md` on
  the same `main`. Accessed 2026-10-09. Supports: ADR-0004 is Proposed
  and its Decision section is blank. Limitation: this proposal does
  not edit that file.
- Title: CREDENTIALW structure (wincred.h). URL:
  https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw.
  Accessed 2026-10-09. Supports: `CRED_TYPE_GENERIC` is 1;
  `CRED_PERSIST_LOCAL_MACHINE` is 2 and persists for later logon
  sessions of the same user on the same computer, not for that user
  on other computers; a generic target name is case-insensitive.
  Limitation: this citation fixes the recorded constants. It does not
  authorize a call.
