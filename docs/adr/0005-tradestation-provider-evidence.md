# ADR-0005: TradeStation provider evidence for a future attended probe

- Status: Proposed
- Date: 2026-10-06
- Amended: 2026-10-08 (proposal only; Decision remains blank)
- Sole Phase 1 decider: Human Operator
- Scope: How Client Experience answers constrain a future probe and which
  OAuth architecture is proposed for a cloud-hosted service
- Supersedes: None
- Superseded by: None

## Context

Draft PR #19 (`bc6ab7ea92310ffa133b75b498f7f245af11f166`) held a Proposed
pre-credential ADR numbered 0003. That number is already the accepted
Group 4A ADR on canonical `main`. PR #19 is not an ancestor of `main`.
This record does not revive that number and does not merge PR #19.

The Operator supplied written Client Experience answers on 2026-10-06.
They are quoted and bounded in `docs/P2_TS_PROVIDER_EVIDENCE.md`. No
TradeStation call was made to obtain them.

## Safety impact

This ADR does not authorize a credential, an authorization code, an
access token, a refresh token, a client secret, a SIM call, a LIVE call,
or an order. The provider confirmed that one key can be used against both
environments by changing the base URL. LIVE denial therefore cannot depend
on the provider issuing a SIM-only key. A future implementation must keep
the controls in `docs/P2_PRE_CREDENTIAL_DECISION.md`. Accepting this ADR
later would still not grant those capabilities while current state denies
them.

## Options considered

### Option A — Regular Web confidential client

Standard Authorization Code. `client_secret` is required on the token
request. The provider confirmed that behavior for this application type
and did not choose it. The public authentication overview, accessed
2026-10-08, says the default key type is Regular Web. That default is not
proof of the issued key.

This option fits a cloud-hosted, eventually unattended service: the
secret stays on the server, the callback is one exact HTTPS URL, and
native loopback is unnecessary. It does not fit a host that cannot keep
a client secret. The issued key's type is still unverified, so this
option is a proposal, not a provider authorization.

### Option B — Native or public client with PKCE

Authorization Code with a code verifier. `client_secret` can be omitted.
The 2026-10-06 note preferred this for an attended probe because it
avoids a persistent secret. The native callback form is still
unconfirmed. A public client is a weaker custody model for an unattended
cloud service. This option remains available if the Operator rejects
Option A. It is not selected.

### Option C — Single Page application with PKCE

The provider confirmed the same PKCE omission of `client_secret`. A
browser-resident client is a poor fit for server-side custody, restart
recovery, and unattended operation. Not proposed.

No other documented flow fits the objectives better. Implicit grant is
not the provider's described model. Resource-owner password is not a
documented option used here.

## Proposal (not a Decision)

Option A is the proposed architecture for the cloud-hosted service.
Supporting points: server-side secret custody, one HTTPS callback, no
dependence on native loopback, refresh design that can later sit behind
an encrypted store, and the same fail-closed host boundary whether the
key is later shown to be Regular Web or not. The proposal does not
assume the issued key is already Regular Web. Accepting it would still
require `DEP-TS-002`, `DEP-TS-003`, and `DEP-TS-004` in
`docs/P2_TS_PROVIDER_EVIDENCE_2026-10-08.md`.

## Decision

## Consequences

The Decision section is blank because status is Proposed. The repository
ADR template requires that. This agent cannot accept the ADR.

Until the Operator accepts a decision, no API client should be created
and no credential should be onboarded. `offline_access` stays omitted
for the initial attended profile. A returned refresh token would be
discarded and the attempt stopped. Default personal-use refresh tokens,
if a later unattended phase requests them, are high-value long-lived
secrets, not 30-minute or 40-minute rotating tokens. Profile B in
`src/swingtrade/group3_auth/session.py` raises
`PROFILE_B_NOT_AUTHORIZED`.

If the Operator later accepts Option A, native loopback (`DEP-TS-001`)
becomes architecturally unnecessary. That would be an architectural
supersession, not a provider answer. If the Operator rejects Option A,
`DEP-TS-001` remains blocking.

## Validation and rollback

Rollback is to leave this ADR Proposed and make no TradeStation call.
Failure signals are any scope broader than `openid` and `ReadAccount`, any
LIVE host, any write method, or any stored token.

## Unresolved questions

The issued key's application type. Granted-scope behavior. The sole HTTPS
callback and removal of other callbacks if Option A is accepted. The
native loopback form if Option A is rejected. Optional rotating-policy
interval. Refresh concurrency and revocation for a real token.
Non-default key configurations. The Operator's expected SIM account
inventory. Operator acceptance of this ADR.

## Evidence

Operator-supplied Client Experience writing, 2026-10-06, recorded in
`docs/P2_TS_PROVIDER_EVIDENCE.md`. The 2026-10-08 intake, which does not
replace those quotations, is
`docs/P2_TS_PROVIDER_EVIDENCE_2026-10-08.md`. Limitation: neither record
chooses an application type or describes loopback callbacks. Public
pages accessed 2026-10-08 are cited in that intake. Prior first-party
page conflicts remain in `docs/P2_BROKER_RESEARCH.md` and are not deleted.
