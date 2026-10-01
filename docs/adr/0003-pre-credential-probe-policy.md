# ADR-0003: Pre-credential probe policy

- Status: Proposed
- Date: 2026-10-01
- Sole Phase 1 decider: Human Operator
- Scope: Whether a future attended, bounded, read-only, no-refresh, no-persistent-token probe may be requested
- Supersedes: None
- Superseded by: None

## Context

`origin/main` at the start of this proposal is
`12e852c6d523a8fbfe2082a33887e36045ee04ae`, tree
`99db680fb2a82d594aa4f6b1bbc0de7e47a217b8`. PR #18 is merged by ancestry
at that commit. `DRY_RUN` remains the only authorized execution mode.
Credentials, broker calls, TradeStation `SIM`, order submission, and
`LIVE` remain unauthorized. ADR-0002 is Accepted for the provider-neutral
TokenStore contract only. It does not certify credentials, key custody, or
a SIM host.

The preferred future probe, already described as a candidate in
`docs/AUTH_ARCHITECTURE.md` and not adopted here, is attended, bounded,
read-only, without refresh, and without a persistent token. Its requested
scopes would be `openid` and `ReadAccount` only. `Trade`, `MarketData`,
and `offline_access` would be omitted.

Official pages already recorded in this repository conflict with that
preference. `docs/AUTH_ARCHITECTURE.md` U-17 and
`docs/P2_BROKER_RESEARCH.md` record that the Auth Code, PKCE, and Refresh
Tokens pages describe `offline_access` as the scope that enables refresh
tokens, while the Scopes table labels `offline_access` **required** with
no such qualification. U-02 records three incompatible default-scope
lists, and each published default includes `Trade`. The preferred
omission of `Trade`, `MarketData`, and `offline_access` is therefore not
the documented default key. This proposal does not choose a winner and
does not re-fetch those pages.

Refresh rotation remains 30 minutes on the Refresh Tokens page and 40
minutes on the Authentication Overview (`BROKER_CONTRACT.md` finding 9).
The preferred probe does not refresh, so that interval is not a probe
step. It stays unresolved for any later refresh-token gate.

No first-party page in the repository states that TradeStation can make
an API key incapable of calling `https://api.tradestation.com`. The
documented SIM/LIVE switch is the base URL, and the documented audience
is `https://api.tradestation.com` (`AUTH_ARCHITECTURE.md`, findings under
SIM/LIVE defense). Whether a provider can remove LIVE use is
`UNKNOWN` / `PROVIDER_CONFIRMATION_REQUIRED`.

## Safety impact

This ADR does not authorize a credential, an OAuth session, a broker
call, a Supabase connection, a SIM order, or `LIVE`. It does not add an
execution-mode override. While current state denies those capabilities,
accepting or rejecting this ADR still cannot grant them.

Fail-closed consequences of leaving the probe unadopted: no key request
is sent, no callback is registered by an agent, and no token is stored.
Observability of a future probe is specified only as a candidate in
`docs/P2_PRE_CREDENTIAL_DECISION.md`. Rollback is deletion or
supersession of this proposal. No runtime state exists to roll back.

## Options considered

### Option A — Adopt the preferred probe profile

Ask Client Experience for one confidential or PKCE key, one HTTPS
callback, scopes `openid` and `ReadAccount`, no `offline_access`, and no
persistent token, and treat that profile as compatible with current
official pages.

Benefits: matches the least-privilege candidate already written in
`AUTH_ARCHITECTURE.md` for one-shot G2. Costs and risks: the Scopes table
conflicts with omitting `offline_access`; the default-scope pages conflict
with omitting `Trade` and `MarketData`; confidential Authorization Code,
public PKCE, and confidential PKCE remain blocked, candidate-only, or
`UNKNOWN` in that same document. Selecting a flow or a scope winner would
be a guess. Evidence: U-17, U-02, and `BROKER_CONTRACT.md` findings 5–10.

### Option B — Hold for a written contract decision

Record `P2_PRE_CREDENTIAL_CONTRACT_DECISION_REQUIRED`. Keep probe stages
C1 (setup), C2 (accounts only), and C3 (balances, positions, and orders)
closed. Local controls in the planning note stay proposals. The Operator
sends no Client Experience message until the Operator accepts the draft
text and the conflicting pages are reconciled in writing.

Benefits: does not pick a winner between official pages and does not open
a credential path. Costs: the preferred probe cannot start on
documentation alone. Evidence: the same conflicts as Option A, plus
`AGENT_AUTHORITY.md` (missing or conflicting conditions fail closed).

## Decision

Intentionally blank. Status is Proposed. This author does not select
Option A or Option B. The planning note recommends Option B's token as
the gate result. Only the human Operator can accept an ADR.

## Consequences

Positive: the conflict is visible, and no production code is required to
record it. Negative: readiness gates that depend on a settled scope and
flow contract stay `NO`. Operational: Client Experience is not contacted
by this change. Agents must not add `offline_access`, `Trade`, or
`MarketData` later to make an exchange succeed.

## Validation and rollback

Acceptance evidence would be an Operator decision in
`docs/CURRENT_STATE.md` that quotes this ADR's commit and either accepts
a reconciled profile or keeps the token in force. Failure signals: a
commit that treats U-17 or U-02 as closed, a credential or host request,
or a production-code change justified by this proposal.

Rollback is supersession of this file. No account, secret, or network
state is created here.

## Unresolved questions

1. U-17: is `offline_access` required on every authorization, or only when
   a refresh token is wanted? Owner: TradeStation Client Experience, then
   the human Operator.
2. U-02: which default scopes are real, and can a key omit `Trade` and
   `MarketData`? Owner: Client Experience, then the Operator.
3. Authorization Code with a client secret, public PKCE, or confidential
   PKCE for an attended Windows probe. Owner: Operator after Client
   Experience names a supported type. Not selected here.
4. Can the provider make the exact key incapable of LIVE? Owner: Client
   Experience. Until answered, classify any future key
   `POTENTIALLY_LIVE_CAPABLE` and keep G1 closed, as
   `AUTH_ARCHITECTURE.md` already requires.
5. Refresh interval 30 versus 40 minutes. Owner: Client Experience. Not
   used by the no-refresh profile.
6. Bootstrap holder and encryption-key custody. Owner: Operator.
   ADR-0002 items 1 and 3 stay open. Encryption stays deferred until a
   separate refresh-token gate.

## Evidence

- Repository: `docs/AUTH_ARCHITECTURE.md` U-02, U-17, Options A–C, and
  the G2 scope profile. Inspected 2026-10-01 at the baseline commit
  above. Claim: the no-refresh profile is a candidate only if a
  refresh-less grant is confirmed; the Scopes table conflicts with that
  omission; default scopes conflict three ways. Limitation: this ADR does
  not re-fetch the TradeStation pages.
- Repository: `docs/P2_BROKER_RESEARCH.md` `BROKER_EVIDENCE_CONFLICT`
  records for refresh rotation, default scopes, and `offline_access`,
  access dates 2026-09-25 and 2026-09-26. Claim: neither page in each
  pair is preferred. Limitation: not a future key's configuration.
- Repository: `docs/BROKER_CONTRACT.md` findings 5–11 and 33–35, accessed
  2026-09-25. Claim: default flow is Authorization Code; PKCE is a Client
  Experience change; access tokens expire after 20 minutes; rate-limit
  header families are `X-RateLimit-*` and, for streams, `X-Concurrency-*`.
- Repository: `docs/adr/0002-provider-neutral-token-store.md`, Accepted.
  Claim: TokenStore acceptance is not credential certification or key
  custody. Limitation: encryption custody remains unresolved.
- Repository: `docs/AGENT_AUTHORITY.md`. Claim: conflicting or missing
  conditions fail closed and do not authorize broker or network activity.
- Process record, not a new page fetch: `docs/ENGINEERING_JOURNAL.md`
  entry dated 2026-10-01 for the unauthenticated OpenAPI GET. This ADR
  does not use that response as broker evidence.
