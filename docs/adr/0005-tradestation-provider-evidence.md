# ADR-0005: TradeStation provider evidence for a future attended probe

- Status: Proposed
- Date: 2026-10-06
- Sole Phase 1 decider: Human Operator
- Scope: How the 2026-10-06 Client Experience answers constrain a future probe
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

### Option A — Regular Web Application

Standard Authorization Code flow. `client_secret` is required. The
provider confirmed this behavior and did not recommend it. A persistent
client secret is a poor fit for the attended no-refresh probe.

### Option B — Native application with PKCE

Authorization Code with a Code Verifier. `client_secret` can be omitted.
This is the engineering preference for the first attended probe because it
avoids a persistent client secret. It is not a provider recommendation.
The callback form is not confirmed, so this option is not selected.

### Option C — Single Page application with PKCE

The provider confirmed the same PKCE omission of `client_secret`. A
browser-resident client is a worse fit for a short attended probe that
must not persist tokens. Not selected.

## Decision

## Consequences

Until the Native callback question is answered, no API client should be
created. `offline_access` stays omitted. A returned refresh token would be
discarded and the attempt stopped. Default personal-use refresh tokens, if
a later unattended phase requests them, are high-value long-lived secrets,
not 30-minute or 40-minute rotating tokens.

## Validation and rollback

Rollback is to leave this ADR Proposed and make no TradeStation call.
Failure signals are any scope broader than `openid` and `ReadAccount`, any
LIVE host, any write method, or any stored token.

## Unresolved questions

The Native PKCE callback form. Exact scope-configuration mechanics.
Returned-scope behavior. Optional rotating-policy interval. Refresh
concurrency and revocation. Non-default key configurations. The Operator's
expected SIM account inventory.

## Evidence

Operator-supplied Client Experience writing, 2026-10-06, recorded in
`docs/P2_TS_PROVIDER_EVIDENCE.md`. Limitation: the message does not choose
an application type and does not describe loopback callbacks. Prior
first-party page conflicts remain in `docs/P2_BROKER_RESEARCH.md` and are
not deleted.
