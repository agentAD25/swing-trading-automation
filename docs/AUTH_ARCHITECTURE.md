# P2-B/r1 Authentication Architecture Research and Proposed Control Contract

- Status: **PROPOSED**
- Date: 2026-09-26
- Revised: 2026-09-29 (independent-verification F1–F4 / N1–N9 remediation;
  r1 remains documentation-only); 2026-09-30 (proposed C1/U-10 resolution
  in [`TOKEN_STORE.md`](TOKEN_STORE.md); status remains **PROPOSED**)
- Workstream: `P2-B/r1`
- Canonical base: `1ecbbe6d487d97195fde393b05c9499357599bdb`
- Sole acceptance decider: Human Operator
- Scope: Research and design only; future TradeStation SIM authentication,
  token, secret, and network-isolation controls
- Supersedes: None
- Superseded by: None

## Status and authority

This document is a proposal, not an accepted ADR, phase transition, credential
authorization, or implementation specification. It records evidence, options,
candidate controls, unresolved risks, and human gates for later review.

The only currently authorized execution mode remains local, deterministic,
fixture/mock-only, non-network `DRY_RUN`. Phase 2, credentials, OAuth client
registration, authorization, token exchange, secret-manager provisioning,
broker/account/network activity, TradeStation `SIM`, order submission, real
capital, and `LIVE` remain unauthorized by
[`CURRENT_STATE.md`](CURRENT_STATE.md). This work performed none of those
actions. Public documentation was read without an account or credential.

Nothing in this proposal can weaken the non-overridable `LIVE` boundary.
Changing `EXECUTION_MODE`, this file, another configuration value, or an ADR
status cannot grant broker access. Future SIM access requires every applicable
human gate and independent control attestation. `LIVE` remains categorically
outside P2-B and subject to every conjunctive prerequisite in
[`LIVE_PROMOTION.md`](LIVE_PROMOTION.md).

## Context and governing contracts

The bounded Phase 1 baseline establishes requirements that this proposal
inherits:

1. unknown mode, authorization, endpoint, account class, environment, scope,
   credential state, or control health fails closed before a broker request;
2. DRY_RUN, SIM, and LIVE require separate artifacts, identities, secrets,
   network policy, data boundaries, and authorization policy;
3. credentials, tokens, raw broker payloads, account identifiers, and personal
   data are prohibited from logs;
4. a future SIM endpoint must be positively allowlisted while every LIVE
   endpoint and fallback remains unreachable; and
5. no document, environment variable, feature flag, fallback, degraded state,
   or successful test can grant denied authority.

The public TradeStation material establishes parts of the OAuth contract but
does not establish a safe key for this system. Key type, configured callbacks,
actual granted scopes, permitted logins, account entitlements, refresh policy,
SIM-only restriction, and rate-limit identity are key-specific. Those facts
must not be inferred from defaults.

`P2-A/r1` is specified as an upstream input in
[`PHASE_2_PLAN.md`](PHASE_2_PLAN.md) §6.3/§7.2, while the same plan's DAG
runs `P2-A/r1` and `P2-B/r1` in parallel. This document does not treat any
unmerged broker-research branch as established fact. Unresolved
authentication, entitlement, and rate-limit items remain those recorded in
[`BROKER_CONTRACT.md`](BROKER_CONTRACT.md). The coordinator reconciles that
plan conflict at H1; this author does not.

## Safety impact

This proposal, while `PROPOSED` and unaccepted, would affect a later SIM
connectivity phase only after the Operator records every named gate. It does
not change the currently authorized `DRY_RUN` mode, does not introduce
credentials or network activity, and cannot by itself authorize TradeStation
`SIM`, order submission, real capital, or `LIVE`.

If later accepted and implemented under those gates, the intended fail-closed
effects are: no broker request without exact artifact, secret-store, host,
scope, and generation health; no environment-variable or local-file
credential copy; no LIVE-reachable adapter; refresh-token families with
`offline_access` only when broker-confirmed rotation/expiry or
sender-constraint exists; and residual bearer-token risks accepted only by an
explicit Operator record, never by this author or a security-owner shortcut.
Rollback is document supersession; this work creates no runtime state.

## Evidence findings

### Verified broker facts

The following facts were re-verified in current first-party TradeStation
documentation on 2026-09-26:

- Default Auth0 API keys are regular web applications using Authorization Code
  flow. PKCE is a non-default configuration requested through TradeStation
  Client Experience and is documented for public native or single-page
  clients. [E1, E2]
- Authorization uses `signin.tradestation.com/authorize`; token exchange uses
  `signin.tradestation.com/oauth/token`; access tokens expire after 20 minutes.
  Standard Authorization Code flow requires a client secret. PKCE uses an
  `S256` code challenge and verifier instead of that client secret. [E2, E3]
- `openid` is required. Auth-code, PKCE, and refresh-token pages describe
  `offline_access` as the scope that enables refresh tokens and is therefore
  requested when a refresh token is wanted [E2, E3, E5]. The Scopes page
  table, however, labels `offline_access` **required** with no
  qualification that it applies only when refresh tokens are requested [E4].
  That conflict is unresolved (U-17). This document does not choose a winner.
  The one-shot G2 profile that omits `offline_access` remains a candidate
  only if Client Experience confirms that a refresh-less grant is accepted;
  if the table's unqualified "required" is the actual key contract, the
  exchange fails closed and G2 cannot use that profile.
- TradeStation defines `MarketData`, `ReadAccount`, `Trade`,
  `OptionSpreads`, and `Matrix` scopes. [E4]
- Refresh tokens must be stored securely. The default is non-expiring.
  TradeStation documents an optional expiring/rotating policy and a 24-hour
  absolute lifetime, but its pages conflict on whether rotation occurs every
  30 or 40 minutes. [E1, E5] Default non-expiring unconstrained refresh
  tokens are rejected for any `offline_access` profile under this proposal
  (see G1 item 3 and U-07).
- Revoking one refresh token revokes all refresh tokens for that API key.
  Disabling and later re-enabling a key can make old non-expiring refresh
  tokens usable again. Rotating the client secret does not invalidate existing
  non-expiring refresh tokens. [E1, E5]
- TradeStation session logout does not invalidate existing access or refresh
  tokens. Access tokens retain their 20-minute lifetime and refresh tokens
  remain subject to their separate lifetime and revocation rules. [E13]
- Default API-scope statements conflict three ways and remain unresolved
  (U-02): the authentication overview lists `MarketData`, `ReadAccount`, and
  `Trade` [E1]; the Scopes page prose lists `MarketData`, `ReadAccount`,
  `Trade`, and `OptionSpreads` (no `Matrix`) [E4]; the Scopes page table
  marks all five, including `Matrix`, as Default [E4]. The actual key
  contract is unknown.
- The documented SIM resource host is `sim-api.tradestation.com`; the
  documented LIVE resource host is `api.tradestation.com`. TradeStation warns
  that applications which permit switching can make mistakes. The OAuth
  audience shown in the authorization documentation is
  `https://api.tradestation.com`, not a SIM-specific audience. [E2, E6]

### Authoritative security guidance

- OAuth Security Best Current Practice requires PKCE for public clients,
  recommends it for confidential clients, identifies `S256` as the method that
  does not expose the verifier, recommends restricting tokens to resources and
  actions, and requires public-client refresh tokens to be sender-constrained
  or rotated. [E7, E8]
- OAuth authorization codes are short-lived, single-use, and bound to the
  client and redirect URI; `state` binds request and callback and protects
  against CSRF. [E9]
- Clients must tolerate unexpected invalidation. Revocation endpoints use
  HTTPS, and a successful revocation means the client must stop using the
  token even if server-side propagation has some delay. [E10]
- OAuth bearer-token guidance associates `invalid_token` with HTTP 401 and
  `insufficient_scope` with HTTP 403. Its permission to obtain a token and
  retry does not establish that replaying a state-changing broker operation is
  safe. [E14]
- Central secret management, object-level least privilege, rotation,
  revocation, expiry, access auditing, and encryption at rest are recommended.
  Access tokens, passwords, connection strings, encryption keys, and primary
  secrets should not be logged. [E11, E12]

These standards guide client controls; they do not prove that TradeStation
supports sender-constrained tokens, confidential-client PKCE, introspection,
SIM-only credentials, or any other unlisted capability.

## Options considered

### Option A — Standard confidential Authorization Code client

Use the TradeStation default regular-web-application configuration with a
client secret.

- **Benefits:** directly documented for server-side confidential clients;
  authenticates the client at code exchange and refresh.
- **Costs and risks:** TradeStation does not document PKCE for this key type;
  `state` protects the callback against CSRF but does not by itself prevent
  authorization-code injection; this proposal does not consume and validate a
  transaction-bound OpenID Connect ID token as an alternate defense. A
  long-lived client secret adds another high-impact secret; default
  non-expiring refresh tokens and default `Trade` scope are also unacceptable
  without key-specific changes.
- **Disposition:** **blocked** under this proposal. It may be reconsidered only
  if TradeStation confirms a supported transaction-bound code-injection
  defense and P2-B/r2 defines and independently verifies that defense. Neither
  Operator acceptance of residual risk nor an automatic downgrade can replace
  the missing control.

### Option B — Public client with Authorization Code plus PKCE

Use the first-party documented PKCE configuration with a per-transaction
`S256` verifier and no client secret.

- **Benefits:** prevents intercepted authorization-code redemption; removes a
  static client secret from the workload.
- **Costs and risks:** the refresh token becomes the primary bearer secret;
  TradeStation documents PKCE for native and single-page public clients, not
  the proposed multi-worker server topology; sender-constrained refresh tokens
  are not documented [E1, E7]. Under Option B there is no client secret, so
  a non-expiring refresh token would mean no credential rotates, which fails
  [`SIM_CERTIFICATION.md`](SIM_CERTIFICATION.md) "least scopes and rotation".
  Any `offline_access` profile therefore requires broker-confirmed
  expiring/rotating refresh tokens **or** confirmed sender-constraint; the
  documented default non-expiring refresh token is rejected and blocks G1.
  Absence of sender-constraint (U-07) cannot be accepted as residual risk
  while rotation/expiry is also absent.
- **Disposition:** candidate only after Client Experience confirms the chosen
  application topology, key configuration, and refresh
  rotation/expiry-or-sender-constraint for the exact key.

### Option C — Confidential client authentication plus PKCE

Use client authentication and transaction-specific `S256` PKCE together, as
recommended for confidential clients by OAuth Security BCP.

- **Benefits:** defense against both client impersonation and authorization
  code interception/injection.
- **Costs and risks:** current TradeStation documentation describes standard
  confidential flow and public-client PKCE as separate configurations; it does
  not establish that this combination is supported.
- **Disposition:** preferred security target, but **UNKNOWN** and blocked
  pending first-party confirmation. Unsupported behavior must not be invented
  or emulated.

## Proposed control architecture

This section is a candidate contract for H1 review and P2-B/r2 drafting. It is
not an accepted decision.

### Trust boundaries and component ownership

| Component | Proposed authority | Explicit denial |
| --- | --- | --- |
| Human authorization station | Initiate an approved authorization-code session and consent to the exact scopes | No token display, export, copy, logging, or account switching |
| Callback handler | Receive one exact callback, validate transaction binding, and hand the code to the auth coordinator | No broker-resource calls, arbitrary redirect, or debug-body logging |
| Auth coordinator | Sole process allowed to exchange, refresh, and revoke tokens after the applicable gates | No order call, arbitrary URL, environment fallback, or plaintext persistence |
| Bootstrap secret holder | Hold static bootstrap secrets only: a client secret if the accepted flow has one, plus non-token references | Not the runtime refresh store; no repository, file, or environment-variable copy of broker tokens; no DEV/TEST broker-secret namespace; production must not depend on Cursor Dashboard start-time injection |
| TokenStore | Hold runtime mutable token state for one credential family, as specified in [`TOKEN_STORE.md`](TOKEN_STORE.md) | No access-token bearer values, client secrets, or ledger rows; no AWS or Supabase API; no Cursor production dependency |
| Token broker | Return a bounded in-memory access-token lease to an authorized SIM workload | Never return client secrets or refresh tokens; never serve an unknown/stale generation |
| SIM broker client | Use a valid lease only for the exact authorized capability and exact SIM host | No auth administration, LIVE host, arbitrary URL, or credential selection |
| Policy/egress layers | Independently enforce environment, artifact, destination, method, and scope policy | No default route, proxy bypass, or configuration-only grant |

The auth coordinator owns one credential family. Workers never read the
client secret or refresh token. An access token is treated as a secret and may
exist only in bounded process memory. It is not persisted in application
tables, queues, caches, traces, or logs.

### Authorization-code lifecycle

1. **Precondition:** all G1 requirements are affirmatively satisfied for an
   exact artifact, credential profile, callback, human authorization record,
   and expiry, **and** G2 attestation (below) is complete before the first
   token exchange or broker request. G1 alone does not authorize a token
   call. Otherwise the auth state is `NO_CREDENTIALS / BLOCKED`.
2. **Flow selection:** use only the exact key type accepted at P2-B/r2. PKCE,
   if selected, is mandatory `S256`; a missing challenge, missing verifier, or
   attempted downgrade blocks the transaction. No fallback between Options A,
   B, and C is permitted.
3. **Request creation:** generate transaction-specific, cryptographically
   random `state`; for PKCE generate a single-use high-entropy verifier and its
   `S256` challenge. Keep both only in encrypted/ephemeral server-side session
   state with a short, approved expiry. Do not put a token, verifier, secret,
   or sensitive diagnostic in a URL. Include `prompt=login` (or the
   Client-Experience-confirmed equivalent that forces an interactive
   TradeStation login) so the authorization cannot silently reuse an existing
   browser session. E2/E3 document that the flow may reuse a session; the ID
   token is unused here (step 9), so without this parameter the authorized
   login is not verified before commit. If TradeStation does not confirm
   `prompt=login` for the exact key, that gap remains U-05 and blocks G1
   until Client Experience confirms another login-binding control.
4. **Redirect:** use one exact, pre-registered HTTPS callback URI for SIM
   administration. Wildcards, open redirects, unregistered ports, and
   environment-shared callbacks are denied. Loopback HTTP is not proposed for
   a deployed environment. G1 must also confirm that the authorization
   server's registered redirect URIs, logout URLs, web origins, and CORS
   origins have been reduced to **exactly** that approved HTTPS callback;
   leftover default `http://localhost` callbacks, wildcard origins, or extra
   logout URLs keep G1 closed [E1].
5. **Callback:** require exactly one `code` and a constant-time match of the
   single-use `state`; reject missing, duplicate, malformed, expired,
   previously consumed, or mismatched values. Authorization errors become a
   safe reason code, never an exception dump containing query parameters.
6. **Exchange:** the auth coordinator posts once to the exact token endpoint
   over validated TLS. It binds the original redirect URI, client identifier,
   authorization code, and either the approved client authentication or PKCE
   verifier. Redirects from the token endpoint are disabled.
7. **Response validation:** require a successful expected media type,
   `Bearer` token type, positive bounded `expires_in`, and the exact required
   scope set. Missing required scope or any unrequested privilege blocks use.
   An omitted scope response is blocked because this design cannot prove the
   grant. Access and refresh token values are opaque; their format or length is
   never assumed.
8. **Commit:** persist a returned refresh token only through the secret
   manager's compare-and-swap generation. Publish an access-token lease only
   after durable refresh-token commit succeeds. If persistence fails after the
   token response, discard the response and require reauthorization; never
   continue with an untracked token family.
9. **Cleanup:** immediately consume/erase the code, verifier, callback
   transaction, and response buffers as far as the runtime permits. The
   mandatory `openid` ID token is not used for identity or authorization and
   is not persisted; a later design must define full OpenID Connect validation
   before any claim may be trusted.

### Minimum scope profiles

Scope is capability-specific; there is no broad default.

| Future profile | Exact requested scopes | Explicitly absent | Authorizing gate |
| --- | --- | --- | --- |
| Bounded G2 read-only probe | `openid ReadAccount`; add `MarketData` only if the approved probe includes market data | `offline_access`, `Trade`, `OptionSpreads`, `Matrix`, `profile`, `email` | G2 only, one-shot, after G1 |
| Continuous SIM read-only worker | `openid offline_access ReadAccount`; add `MarketData` only for a named requirement | `Trade`, `OptionSpreads`, `Matrix`, `profile`, `email` | **Not** G2 and **not** G3. Requires a separately named, expiring human gate recorded in `CURRENT_STATE.md` after successful one-shot G2 and before any long-lived `offline_access` worker. Until that gate exists this row is research-only and must not be provisioned |
| Future bounded SIM order harness, not authorized here | A separate key/token family with `openid offline_access ReadAccount Trade`; any `MarketData` or `OptionSpreads` addition requires a separately approved test need | `Matrix`, `profile`, `email`, and every unapproved scope | G3 only, after its own human authorization; out of this r1 grant |

The one-shot G2 profile intentionally requests no refresh token if the bounded
probe fits within the documented 20-minute access-token lifetime. A different
duration is not silently justified by adding `offline_access`. That omission
depends on U-17 remaining unresolved: E2/E3/E5 treat `offline_access` as
refresh-enabling, while the E4 table marks it required without qualification.
If exchange fails because the key requires `offline_access`, G2 ends
fail-closed; agents must not add the scope to recover.

Any profile that includes `offline_access` additionally requires the G1
refresh-token replay control in the next subsection.

The API key itself must also be configured to the least capability; requesting
a narrow scope does not compensate for an unnecessarily broad key. If the
returned grant is broader than requested, the token is quarantined and never
used. G2 must confirm actual scope behavior without converting an observed
result into a general guarantee.

### Token states and local validity

The proposed state machine is:

`NO_CREDENTIALS -> AUTHORIZATION_PENDING -> ACCESS_VALID -> REFRESH_DUE ->`
`REFRESHING -> ACCESS_VALID`

Any uncertainty transitions to one of:

- `REAUTH_REQUIRED`: authorization was denied, expired, revoked, or refresh
  cannot safely continue;
- `REVOKED`: local revocation was confirmed and token use is prohibited;
- `AUTH_UNKNOWN / BLOCKED`: outcome, owner, scope, host, clock, secret-store
  generation, or dependency state is ambiguous.

Only `ACCESS_VALID` permits an otherwise-authorized SIM request. Validity
requires all of the following, independently of `EXECUTION_MODE`:

- current human phase authorization and unexpired operation authorization;
- exact SIM artifact and deployment identity;
- exact credential profile, token generation, and expected scopes;
- access-token deadline with an approved skew margin from a trusted clock;
- healthy secret manager, token broker, policy engine, audit sink, and egress
  controls;
- exact operation class allowed by the current gate; and
- exact allowlisted endpoint with the LIVE denies intact.

### Refresh handling

Refresh, and any `offline_access` grant, is permitted only for a credential
family whose exact API key has a broker-confirmed expiring/rotating refresh
policy **or** confirmed sender-constraint. TradeStation's default
non-expiring refresh token is rejected. That control is a G1 blocker, not an
optional enhancement. RFC 9700 §2.2.2 requires public-client refresh tokens
to be sender-constrained or rotated [E7]; Option B has no client secret, so
without one of those controls no credential rotates.

1. Refresh begins before expiry using an Operator-approved safety margin. The
   exact margin, clock-skew tolerance, retry budget, and service objective are
   unresolved; no value is invented here (U-11).
2. A single auth coordinator holds a short lease with a monotonically
   increasing fencing generation. The TokenStore record contains the
   credential-family ID, current refresh-token version, current owner fence,
   expected scopes, environment, and lifecycle state. Lease TTL is an r2
   parameter bound to U-11 and must be shorter than the refresh safety margin.
   The compare-and-swap, fencing, and stale-writer rules are the proposed
   contract in [`TOKEN_STORE.md`](TOKEN_STORE.md).
3. Only the current fence owner may read the refresh token or **initiate** a
   token-endpoint call. Other workers wait for a newer access-token lease;
   they do not refresh independently. The external TradeStation token
   endpoint cannot enforce this fence: a paused stale owner can still send.
   Therefore the owner must re-check fence generation immediately before send
   (U-11). A send after fence loss is U-08: `AUTH_UNKNOWN / BLOCKED`, no
   replay.
4. The response is committed with compare-and-swap against both the refresh
   version and fence **before** an access token is published. When the
   confirmed policy is rotation, the new refresh token is the value committed.
   When the confirmed policy is sender-constraint without rotation, metadata
   and generation still CAS-commit; a non-expiring unconstrained refresh
   token is never stored. The previous secret version is made unreadable and
   deleted according to the approved revocation/retention policy.
5. A stale owner, failed compare-and-swap, lease uncertainty, split brain, or
   secret-store outage transitions the family to `AUTH_UNKNOWN / BLOCKED`.
   No worker uses a still-cached access token while control state is unknown.
6. A definite pre-send transport failure may receive a bounded retry only if
   instrumentation proves no request bytes left the process. A timeout,
   disconnect, or lost response after possible submission is ambiguous,
   especially for rotating refresh tokens: do not replay the old token.
   Transition to `REAUTH_REQUIRED`.
7. `invalid_grant`, a revoked/expired refresh token, detected replay, or an
   unexpected token generation discards all access-token leases and requires
   a new human authorization session. `invalid_client` blocks the credential
   family and triggers security review. Transient errors never cause a
   credential, host, scope, or environment fallback.

This design favors reauthorization over attempting to recover an unknown
rotating token. Availability loss is acceptable; ambiguous privilege is not.

### Secret storage, rotation, and revocation

Bootstrap static secrets and runtime mutable token state are separate.
The proposed runtime contract is [`TOKEN_STORE.md`](TOKEN_STORE.md). This
document does not provision a product, select AWS or Supabase APIs, or
accept an ADR.

**Proposed resolution of the H1-carried conflict (U-10):** plan G1 had
named Cursor Dashboard secrets. Cursor documents those secrets as values
**injected when an agent starts**; already-running agents do not pick up
changes [E15]. That mechanism cannot be the workload-writable versioned
store. The 2026-09-30 proposal therefore rejects Cursor as a production
dependency, keeps static bootstrap secrets out of the token row, and
specifies a provider-neutral PostgreSQL TokenStore for runtime token
state. Bounded wording in [`PHASE_2_PLAN.md`](PHASE_2_PLAN.md) §6.3 and
Gate G1 records that same proposal. It is not Operator acceptance. H2
still has to accept or reject it. `CURRENT_STATE.md` is not edited here
and still carries the pre-resolution conflict until a later evidence
update.

Required properties:

- workload-identity access with least privilege; bootstrap static secrets
  are not the refresh-token record and are not a shared human-readable
  token copy;
- separate SIM namespace, encryption at rest with keys separate from token
  data, TLS in transit, versioned compare-and-swap, fencing, authorized
  revocation, stale-writer rejection, auditing, and deletion, as
  `TOKEN_STORE.md` specifies;
- auth coordinator read/write access only to its exact SIM credential
  family; broker workers receive only bounded in-memory access-token
  leases;
- no repository, environment-file, command-line, image, ledger table,
  queue, artifact, clipboard, local disk, swap, core dump,
  environment-variable copy, or support-bundle copy of token material;
  the TokenStore relation is the only proposed database exception, and it
  holds refresh ciphertext plus redacted metadata, not access tokens;
- no plaintext backup; any approved backup has separate encryption,
  restricted restore authority, and tested deletion/retention;
- secret access, failed access, generation change, rotation, and revocation
  metadata are auditable without recording secret values;
- the TokenStore must be writable by the authorized auth-coordinator
  identity after start so rotation CAS can commit a new refresh-token
  generation without restarting the workload onto a stale environment copy.

The TokenStore is a mandatory safety dependency for any future refresh.
Unavailable, stale, partially available, or unverifiable storage makes
readiness false, stops token issuance/refresh, invalidates worker leases,
and permits no broker request. There is no file, environment-variable,
cached-token, alternate-manager, operator-copy, or Cursor fallback.

Rotation and revocation are separate:

- client-secret rotation follows an approved cadence and immediately on
  suspected exposure, but TradeStation states that it does not revoke existing
  non-expiring refresh tokens; those defaults are already G1-rejected for
  `offline_access` families;
- refresh-token rotation, where that is the confirmed replay control, uses the
  broker-confirmed expiring/rotating policy and atomic generation handling
  above; it is mandatory for `offline_access`, not conditional;
- suspected compromise stops consumers first, revokes the entire API-key
  refresh-token family, rotates the client secret if one exists, removes old
  secret versions, and independently verifies denial before recovery;
- disabling the API key alone is not accepted as revocation because
  TradeStation states that re-enabling can revive old non-expiring refresh
  tokens;
- browser/authentication-session logout is not accepted as revocation because
  TradeStation states that logout leaves existing access and refresh tokens
  valid under their separate lifetimes;
- local deletion alone is not broker revocation, and a broker HTTP success is
  not enough until local leases are invalidated and denial is verified.

Exact broker revocation request encoding and propagation behavior remain
unresolved and must be confirmed before automation (U-06, U-14).

### Redaction at rest, in logs, and in exceptions

The sensitive-value taxonomy includes client secret, authorization code,
refresh/access/ID token, PKCE verifier, `state`, cookie, authorization and
token endpoint payloads, secret-manager response, account identifier, login,
personal claim, raw broker payload, and any URL/query/header that can contain
one.

Controls:

- allowlist structured diagnostic fields; do not rely on a denylist regex;
- never log request/response headers or bodies for authorization, token,
  revocation, secret-manager, or broker calls;
- convert errors at the trust boundary to stable safe reason codes such as
  `AUTH_STATE_MISMATCH`, `AUTH_SCOPE_MISSING`, `AUTH_TOKEN_EXPIRED`,
  `AUTH_REFRESH_REVOKED`, `AUTH_STORE_UNAVAILABLE`, and
  `AUTH_DESTINATION_DENIED`;
- exception renderers suppress object representations, nested causes, URL
  query strings, local variables, HTTP debug traces, and upstream response
  bodies; crash dumps and tracing payload capture are disabled for these
  components;
- use a random non-secret credential-family record ID and token generation for
  correlation, never a token substring, deterministic token hash, account ID,
  or subject claim;
- scan logs, traces, metrics, alerts, test artifacts, support bundles, and
  exception paths with synthetic canaries before G1 and continuously after
  authorization;
- a redaction failure is a security incident: block readiness, contain access,
  revoke affected credentials, and preserve only sanitized evidence.

At-rest audit records contain metadata and safe reason codes only. Tokens and
raw claims are neither audit evidence nor reconciliation state.

## SIM/LIVE defense in depth

### Network destination policy

| Destination | Future permitted purpose | Policy |
| --- | --- | --- |
| `signin.tradestation.com:443` | Authorization, token, and revocation only from auth components after the applicable gate | Exact allowlist; validated TLS; fixed paths; redirects disabled |
| `sim-api.tradestation.com:443` | Approved SIM resource methods only from the SIM broker client after G2/G3 as applicable | Exact allowlist; validated TLS; fixed base path; method policy |
| `api.tradestation.com` on every port/path | LIVE resources | Explicit application, resolver/proxy, service-mesh, firewall, and egress deny |
| Any other TradeStation alias, hostname, IP literal, redirect target, proxy, or destination | None | Default deny |

An endpoint is constructed from a typed, artifact-owned endpoint identifier,
not accepted as a URL from an environment variable, database, token response,
redirect, broker payload, or user input. The client rejects user information,
non-HTTPS schemes, unexpected ports, Unicode/lookalike names, suffix matches,
IP literals, and redirects before DNS or connection. Certificate and hostname
validation are mandatory. Proxy environment variables and generic outbound
proxies are absent unless a later accepted design proves an equally strict
destination policy.

Network control is conjunctive: application validation, separate workload
identity, default-deny namespace/network policy, egress gateway policy,
resolver policy, and destination-side TLS checks must all allow the same SIM
request. Failure or disagreement at any layer denies.

### Environment, artifact, data, and credential separation

| Environment | Broker credentials | Broker/auth egress | Artifact and data rule |
| --- | --- | --- | --- |
| DEV | None | Denied | Local mocks/fixtures only; no secret namespace or broker adapter |
| TEST/CI | None | Denied | Synthetic canaries and recorded contract fixtures only; no account data |
| SIM | None today; future SIM-only family only after G1 | Default deny; exact auth/SIM allows only after G2/G3 | Separately built/deployed artifact, identity, secret namespace, datastore, policy, audit, and dashboard |
| LIVE | None; environment absent and unauthorized | Explicitly denied | No artifact, adapter, credential namespace, route, deployment, or fallback |

DEV and TEST must remain capable of exercising every state transition with
synthetic values and a non-network fake authorization server. They must not
inherit, mount, query, or reference SIM secrets.

A future SIM key must be broker-restricted to fake SIM accounts and must not
be usable for LIVE resources where TradeStation offers that capability. The
current public documentation does not establish such a restriction and uses a
common OAuth audience. Therefore:

1. G1 requires first-party confirmation of the strongest available key,
   login, account, and entitlement restriction;
2. separate keys/token families are required for read-only G2 and any later
   order-capable G3 work;
3. a key with real-account entitlement or an unbounded permitted login is
   rejected; and
4. if a credential's inability to access LIVE cannot be established, classify
   it `POTENTIALLY_LIVE_CAPABLE` and block G1. Network denial is necessary
   defense in depth, not a substitute for credential isolation.

No runtime switch exists among environments. A SIM process cannot load a LIVE
profile, and no unknown/missing environment defaults to SIM or DRY_RUN.

## Failure and recovery contract

| Condition | Mandatory fail-closed behavior | Recovery |
| --- | --- | --- |
| Missing/unknown/conflicting mode, environment, artifact, authority, scope, owner, or credential generation | No token lease and no broker request; readiness `BLOCKED` | Correct through the approved change process and independently re-attest |
| Wrong/missing/malformed host or any redirect | Reject before DNS/connection; emit `AUTH_DESTINATION_DENIED` without the supplied value | Investigate configuration/artifact integrity; no host fallback |
| Missing required or extra granted scope | Quarantine and erase token; no request | Correct key/request through human review and repeat authorization |
| Access token locally expired or inside safety margin | Do not send; enter approved refresh flow if authorized | Successful fenced refresh or human reauthorization |
| Resource response `401` | Invalidate current lease; do not infer expiry versus revocation | Read-only operation may retry once only after a fully successful refresh and policy recheck; write/unknown operations never auto-retry |
| Resource response `403` | Treat as entitlement/scope/policy denial; no refresh loop | Human review of exact key/account/scope; no privilege expansion fallback |
| Browser/session logout | Do not infer token invalidation; invalidate local leases if logout is part of containment | Use the approved token-family revocation procedure; logout is not a substitute |
| Refresh `invalid_grant`, revoked/expired token, or replay signal | Invalidate family and all leases; `REAUTH_REQUIRED` | Security review and new human authorization; revoke family if compromise is possible |
| Refresh timeout/lost response | `AUTH_UNKNOWN / BLOCKED`; never replay old rotating token | New authorization unless broker evidence later proves a safe recovery contract |
| Secret manager unavailable/stale/split | Invalidate leases; no use of cached token | Restore and independently verify store/generation health, then reauthorize if continuity is uncertain |
| Clock unavailable/skew unknown | Token considered invalid | Restore trusted clock and re-evaluate; no extended lifetime |
| Redaction/audit/egress policy unavailable | Readiness false; no broker request | Contain, repair, verify with synthetic canaries, rotate if exposure possible |
| Suspected credential exposure | Stop consumers, invalidate leases, preserve sanitized metadata | Revoke refresh family, rotate client secret if present, delete stale copies, investigate, and require independent restart approval |

Authentication recovery never changes host, environment, account, scope,
artifact, credential family, or operation class. It never retries a write or
an operation with an ambiguous external outcome. Reauthentication restores
identity only; it grants no phase or execution authority.

## Human gates

### H2 / Human Decision Gate 1 — contract freeze

Before G1, the Operator must accept or reject the P2-B/r2 ADR together with
the dependent design ADRs and record the bounded decision in
`CURRENT_STATE.md`. An independent verifier must confirm the frozen artifact
still contains no credential or broker-network primitive. This r1 proposal
does not satisfy H2.

### G1 — credential boundary

G1 remains closed until humans provide all of the following affirmative,
exact-artifact evidence:

1. explicit Operator authorization of a bounded TradeStation SIM connectivity
   phase in `CURRENT_STATE.md`, with scope and expiry;
2. accepted P2-B ADR (at H2 or explicitly at G1) and named security, system,
   operations, and incident owners;
3. TradeStation Client Experience confirmation for the exact API key:
   application type, PKCE/client-auth support, exact HTTPS callback **and**
   reduction of registered redirect URIs, logout URLs, web origins, and CORS
   origins to that callback only (no leftover localhost or wildcards), exact
   allowed scopes, `prompt=login` or confirmed alternate login-binding,
   **broker-confirmed expiring/rotating refresh policy or confirmed
   sender-constraint** (default non-expiring unconstrained refresh tokens are
   rejected and keep G1 closed), permitted logins, SIM-only restriction,
   account entitlements, revocation behavior, and rate-limit identity;
4. a separately owned read-only G2 credential profile with no `Trade`,
   `OptionSpreads`, `Matrix`, `profile`, or `email` grant, and no
   `offline_access` unless U-17 is resolved in favor of a refresh-required
   key **and** a separately accepted need plus the replay control in item 3;
5. Operator acceptance of the proposed TokenStore contract in
   [`TOKEN_STORE.md`](TOKEN_STORE.md), including workload identities and
   its fail-closed, encryption, audit, versioned CAS, fencing, rotation,
   authorized revocation, stale-writer rejection, redaction, backup, and
   deletion rules, plus a separate non-Cursor path for bootstrap static
   secrets. Cursor Dashboard start-time injection [E15] does not satisfy
   this item. This row proposes the plan wording; it does not itself
   accept the ADR or open G1;
6. independent evidence that the exact SIM artifact has no LIVE adapter or
   endpoint selection and that application, DNS/proxy, mesh, firewall, and
   egress controls allow only the declared destinations;
7. synthetic-canary evidence for repository, build artifact, process
   arguments, local storage, logs, traces, exceptions, metrics, alerts,
   support bundles, and crash handling;
8. legal/compliance/entitlement approval for the bounded SIM use; and
9. explicit Operator records in `CURRENT_STATE.md` for any residual-risk
   acceptance of U-07 and/or U-14. Those records are Operator-only. A
   security owner, this author, or this document cannot accept them. U-07
   residual-risk acceptance is **forbidden** if refresh rotation/expiry is
   also absent; G1 stays closed.

The human Operator provisions or directs provisioning of the future credential
through the store accepted at this gate; no agent performs that action.
Missing, conflicting, stale, or key-generic evidence keeps G1 closed.

### G2 — authenticated read-only probe boundary

G2 is a separate explicit human action after G1. It authorizes only the frozen,
expiring probe manifest and does not authorize an order-capable scope or call.
Before the first token exchange or broker request, a human reviewer and an
independent verifier must attest:

- exact commit/artifact digest, SIM deployment identity, callback, credential
  family, requested scope set, operation/method/path allowlist, start/end time,
  response quarantine, redaction, abort, and evidence owner;
- the `Trade` scope is absent and all order/confirm/replace/cancel methods are
  structurally absent or denied;
- the only resource destination is `sim-api.tradestation.com:443`, the LIVE
  deny has been tested, and no proxy/redirect/default route can bypass it;
- secret-manager, fencing, clock, audit, alerting, and egress health are
  affirmative immediately before the action; and
- one-shot G2 uses no `offline_access` unless U-17 is resolved and a
  separately accepted need proves refresh is necessary, in which case G1
  item 3's rotation/expiry-or-sender-constraint already applies; and
- this G2 attestation is conjunctive with G1: the authorization-code
  lifecycle precondition is not met by G1 alone.

The first authenticated activity is limited to token exchange and the approved
read-only SIM queries. Responses are quarantined as provenance-tagged
observations with identifiers and personal data excluded from logs. Any
unexpected scope, host, account class, response shape, authorization error, or
control degradation ends the probe. An independent post-run check must prove
zero write/order calls before G2 can be considered complete.

G2 evidence does not resolve future G3 order authorization, does not
authorize the continuous SIM read-only worker profile, and cannot
authorize LIVE.

## Validation and rollback

Validation for this r1 artifact is documentation-only:

- verify this branch descends directly from canonical main
  `1ecbbe6d487d97195fde393b05c9499357599bdb`;
- verify the diff creates only `docs/AUTH_ARCHITECTURE.md`;
- verify status remains `PROPOSED` and current authority remains DRY_RUN only;
- verify every factual external claim has a current authoritative source,
  access date, claim, and limitation;
- inspect for credential-like values, account identifiers, token examples,
  implementation, provisioning, migrations, and runtime changes;
- review every named failure for a no-request fail-closed result; and
- obtain independent security/auth review before H1.

The checklist bullet that the r1 diff creates only `AUTH_ARCHITECTURE.md`
is historical evidence for that review. The 2026-09-30 C1 proposal also
adds [`TOKEN_STORE.md`](TOKEN_STORE.md) and bounded pointers in the plan,
reconciliation, configuration naming, and monitoring taxonomy. It does
not change the r1 checklist's meaning for the earlier diff, and it does
not edit `CURRENT_STATE.md` or `ENGINEERING_JOURNAL.md`.

Passing these checks establishes document conformance only. It does not verify
runtime controls or open H2, G1, or G2.

Rollback is removal or supersession of this proposed document. No credential,
account, secret-manager object, network route, broker state, or runtime state
exists from this work.

## Proposed decision

No architecture decision is accepted at r1. The proposed candidate for P2-B/r2
is:

1. Authorization Code flow with transaction-specific `state`, `prompt=login`
   (or confirmed equivalent), and mandatory `S256` PKCE when first-party
   support for the chosen client topology is confirmed; no flow downgrade;
2. capability-specific keys and exact scopes, with a one-shot, no-refresh,
   no-`Trade` G2 profile; continuous `offline_access` workers await a
   separately named gate after G2;
3. any `offline_access` family requires broker-confirmed refresh
   rotation/expiry **or** sender-constraint; default non-expiring
   unconstrained refresh tokens block G1;
4. a centralized auth coordinator; bootstrap static secrets held outside
   the token row and outside Cursor; runtime mutable token state in the
   proposed PostgreSQL TokenStore ([`TOKEN_STORE.md`](TOKEN_STORE.md)),
   with versioned CAS, fencing, pre-send fence recheck, and no local or
   environment-variable fallback;
5. positive auth/SIM destination allowlists plus explicit multi-layer LIVE
   denial, separate from mode checks;
6. separate DEV/TEST/SIM identities, artifacts, data, networks, and secrets,
   with no broker credentials or egress in DEV/TEST and no LIVE environment;
7. stop/revoke/reauthorize on uncertainty rather than retry, broaden scope, or
   cross an environment boundary; and
8. U-07 and U-14 residual risk, if still unresolved, are accepted only by an
   explicit Operator record at G1; U-07 cannot be accepted without rotation.

The Operator may accept, reject, or require changes at a later gate. This
author cannot approve the proposal.

## Decision

Leave blank while status is `PROPOSED`. No option is selected.

## Consequences

Expected if a later gate accepts a descendant of this proposal:

- Positive: fail-closed token lifecycle, SIM/LIVE host isolation, no
  repository secrets, and G1 blocked until rotation/sender-constraint, store
  CAS, and Operator residual-risk records exist.
- Negative: availability loss on ambiguous refresh; one-shot G2 may fail if
  E4's unqualified `offline_access` "required" is the live key contract
  (U-17); Cursor Dashboard injection is not the production runtime store.
  The proposed replacement is [`TOKEN_STORE.md`](TOKEN_STORE.md) and is not
  accepted (U-10).
- Operational: Client Experience confirmations, Operator acceptance or
  rejection of the proposed TokenStore at H2, independent verification at
  H2/G1/G2, and a later evidence update to `CURRENT_STATE.md` /
  `ENGINEERING_JOURNAL.md` (this proposal does not edit those documents).

No consequence of this r1 artifact is a credential, network path, or phase
authorization.

## Unresolved risks and decisions

| ID | Unknown or risk | Why it matters | Required owner/gate |
| --- | --- | --- | --- |
| U-01 | TradeStation says rotating refresh tokens rotate at both 30 and 40 minutes | Cannot safely set refresh timing or expected generation behavior | Client Experience + Operator before G1; observe at G2 only if authorized |
| U-02 | TradeStation default-scope statements conflict three ways: E1 lists `MarketData`/`ReadAccount`/`Trade`; E4 prose adds `OptionSpreads` but not `Matrix`; E4 table marks all five including `Matrix` as Default | A future key may carry unneeded order, options, or depth privilege | Client Experience before G1; exact returned scopes checked at G2 |
| U-03 | Confidential-client PKCE support is undocumented | Option C cannot be assumed; downgrade would weaken interception defense | Security owner + Client Experience at P2-B/r2/G1 |
| U-04 | SIM-only credential/key/account restriction is undocumented; OAuth audience is not SIM-specific | A stolen token might be LIVE-capable outside local egress controls | Client Experience + independent security review; unresolved blocks G1 |
| U-05 | Key-specific callbacks, permitted logins, account types, entitlements, leftover localhost/wildcard registrations, and whether `prompt=login` is honored are unknown | Wrong login, silent SSO reuse, or extra registered callbacks can cross the boundary | Operator/Client Experience before G1 |
| U-06 | Refresh revocation request examples and parameter naming are internally inconsistent; propagation is unspecified | Incident response could falsely claim revocation | Broker researcher + Client Experience before G1 |
| U-07 | Sender-constrained access/refresh tokens and token introspection are not documented | Bearer-token theft and remote validity cannot be independently constrained/checked. Residual post-theft use is **not** accepted by this author or a security owner. | **G1.** Operator may record residual-risk acceptance in `CURRENT_STATE.md` only if G1 item 3's expiring/rotating refresh policy is also confirmed. If rotation/expiry is absent, U-07 cannot be accepted and G1 stays closed |
| U-08 | Refresh rotation replay/family semantics and lost-response recovery are not fully documented | Concurrent or ambiguous refresh can revoke or orphan a family | Broker researcher; fail-closed reauthorization unless resolved; G1 |
| U-09 | Rate-limit identity across keys, users, processes, and accounts is unknown | Multi-worker ownership and backoff cannot be finalized | Operator topology decision before G1; bounded observation at G2 |
| U-10 | The Cursor-versus-CAS conflict is **proposed-resolved** by [`TOKEN_STORE.md`](TOKEN_STORE.md): production must not depend on Cursor; bootstrap static secrets are separate from a provider-neutral PostgreSQL TokenStore with versioned CAS, fencing, rotation, authorized revocation, stale-writer rejection, and redaction. Still unselected: bootstrap injector product, workload platform, KMS/key custody, retention, and recovery objectives. | The contract can be reviewed. It is not accepted, not implemented, and not a provider selection. Residuals keep G1 closed. | **Human Operator at H2** to accept or reject the proposal. Agents must not accept it or bind it to AWS or Supabase APIs |
| U-11 | OAuth clock skew, refresh margin, retry budget, lease duration, **pre-send fence recheck**, and recovery objectives are unset | Invented timing can cause expiry races, stale-owner sends, or unsafe retries | Human security/operations decision at P2-B/r2; bind lease TTL and pre-send fence recheck here |
| U-12 | DNS, proxy, egress-gateway, certificate, and broker alias inventory is incomplete | Hostname checks alone do not prove network isolation | Network/security owners before G1 |
| U-13 | Legal, privacy, account-entitlement, automation, and retention obligations are unknown | Technical authorization does not establish permitted use | Qualified humans before G1 |
| U-14 | Access-token revocation behavior and cascade from refresh revocation are not TradeStation-documented | A locally revoked family may retain usable access tokens for up to the 20-minute access-token lifetime. Local stop is mandatory regardless. Remote residual validity is **not** accepted by this author or a security owner. | **G1.** Operator-only residual-risk record in `CURRENT_STATE.md`, or G1 stays closed. Local leases are invalidated immediately in either case |
| U-15 | ID-token issuer metadata, signing-key lifecycle, and claim-validation contract are outside r1 | Trusting decoded claims could create identity confusion | Future dedicated design before any ID-token claim is used |
| U-16 | TradeStation token-endpoint error schema, status mapping, throttling, timeout idempotency, and retry behavior are undocumented. E5's refresh-response example returns `scope: "openid offline_access"` with no API scopes; under the exact-scope rule that response would be quarantined (availability loss, not a safety loss). | Generic OAuth errors do not prove safe broker-specific retry; a refresh that drops API scopes would deny every subsequent request | Broker researcher + Client Experience before G1; bounded observation at G2 |
| U-17 | E2/E3/E5 present `offline_access` as the scope that enables refresh tokens; the E4 Scopes table labels `offline_access` **required** with no such qualification | The one-shot no-refresh G2 profile depends on omitting it. Failure direction is closed (exchange fails), but the conflict must not be silently resolved | Client Experience before G1; confirm at G2 whether a refresh-less grant is accepted |

Every unresolved item remains a blocker at the named gate. No observation,
default, code path, security owner, or agent may silently choose a value or
accept residual risk. Residual-risk acceptance for U-07 and U-14 is an
Operator-only `CURRENT_STATE.md` record at G1.

## Evidence

TradeStation, RFC, and OWASP sources below were accessed 2026-09-26; E4 was
re-read and E15 first accessed on 2026-09-29. TradeStation pages are mutable
and describe Auth0 API keys generally; none proves the configuration of a
future key.

- **E1 — TradeStation, “Overview” (Authentication).**
  https://api.tradestation.com/docs/fundamentals/authentication/auth-overview/
  Supports default regular-web-app Auth Code flow, optional PKCE
  reconfiguration, the 40-minute rotating-token statement, default scope
  statement, callback administration, key disable/re-enable behavior, and
  client-secret rotation behavior. Limitation: key-specific settings require
  Client Experience; conflicts with E4/E5.
- **E2 — TradeStation, “Auth Code Flow.”**
  https://api.tradestation.com/docs/fundamentals/authentication/auth-code/
  Supports authorization/token endpoints, required parameters, audience,
  scopes, standard client secret, 20-minute access-token lifetime, and
  authorization-code flow. Limitation: standard confidential-client flow
  only; examples are not this system's configuration.
- **E3 — TradeStation, “Auth Code Flow With PKCE.”**
  https://api.tradestation.com/docs/fundamentals/authentication/auth-pkce/
  Supports non-default public-client PKCE, 43–128-character verifier,
  `S256`, token exchange without a client secret, and one-use code behavior.
  Limitation: does not establish confidential-client PKCE or this topology.
- **E4 — TradeStation, “Scopes.”**
  https://api.tradestation.com/docs/fundamentals/authentication/scopes/
  Supports meanings of `MarketData`, `ReadAccount`, `Trade`,
  `OptionSpreads`, `Matrix`, required `openid`, the Other Relevant Scopes
  table, and optional profile/email scopes. Limitation: that table labels
  `offline_access` **required** without the refresh-only qualification used
  by E2/E3/E5 (U-17); this citation does not resolve that conflict;
  default-scope prose lists four API defaults while the table marks five
  including `Matrix` (U-02); neither statement proves subset behavior for a
  future key.
- **E5 — TradeStation, “Refresh Tokens.”**
  https://api.tradestation.com/docs/fundamentals/authentication/refresh-tokens/
  Supports secure storage warning, 20-minute access-token lifetime, default
  non-expiring refresh tokens, optional rotation/expiry, 24-hour absolute
  rotating-token lifetime, refresh parameters, and API-key-wide refresh-token
  revocation.   Limitation: says 30 minutes where E1 says 40; revocation examples
  are internally inconsistent on request shape; the documented refresh
  response example returns `scope: "openid offline_access"` with no API
  scopes (U-16).
- **E6 — TradeStation, “SIM vs. LIVE.”**
  https://api.tradestation.com/docs/fundamentals/sim-vs-live/
  Supports exact SIM and LIVE v3 hosts, fake SIM accounts/money, simulated
  instant fills, and the warning against switchable applications. Limitation:
  does not prove credential, account, DNS, proxy, or network isolation.
- **E7 — IETF, RFC 9700, “Best Current Practice for OAuth 2.0 Security.”**
  https://www.rfc-editor.org/rfc/rfc9700.html
  Supports PKCE requirements/recommendations, `S256`, CSRF binding, token
  resource/action restriction, and refresh replay controls. Limitation:
  security standard, not evidence of TradeStation feature support.
- **E8 — IETF, RFC 7636, “Proof Key for Code Exchange by OAuth Public
  Clients.”** https://www.rfc-editor.org/rfc/rfc7636.html
  Supports per-flow verifier/challenge mechanics, entropy guidance, `S256`,
  and no downgrade to `plain`. Limitation: does not select a TradeStation key
  type.
- **E9 — IETF, RFC 6749, “The OAuth 2.0 Authorization Framework.”**
  https://www.rfc-editor.org/rfc/rfc6749.html
  Supports authorization-code single use/client/redirect binding, `state`,
  scope, TLS, token errors, and refresh-token confidentiality. Limitation:
  baseline framework superseded in security detail by E7.
- **E10 — IETF, RFC 7009, “OAuth 2.0 Token Revocation.”**
  https://www.rfc-editor.org/rfc/rfc7009.html
  Supports HTTPS revocation, immediate client cessation, related-token
  invalidation possibilities, and tolerance of unexpected invalidation.
  Limitation: TradeStation-specific request and cascade behavior governs.
- **E11 — OWASP Cheat Sheet Series, “Secrets Management Cheat Sheet.”**
  https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
  Supports centralized secret management, least privilege, automation,
  rotation, revocation, expiry, auditing, and encryption at rest. Limitation:
  implementation-neutral guidance, not a selected product or acceptance.
- **E12 — OWASP Cheat Sheet Series, “Logging Cheat Sheet.”**
  https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
  Supports excluding access tokens, authentication secrets, connection
  strings, encryption keys, and sensitive data from logs and sanitizing event
  data. Limitation: organization-specific taxonomy, retention, and tooling
  remain undecided.
- **E13 — TradeStation, “Logout Users.”**
  https://api.tradestation.com/docs/fundamentals/authentication/logout/
  Supports the authentication-session logout endpoint and the explicit
  statement that logout does not invalidate existing access or refresh
  tokens. Limitation: session logout is not a token revocation or incident
  containment mechanism.
- **E14 — IETF, RFC 6750, “The OAuth 2.0 Authorization Framework: Bearer Token
  Usage.”** https://www.rfc-editor.org/rfc/rfc6750.html
  Supports `invalid_token`/401 and `insufficient_scope`/403 semantics, avoiding
  bearer tokens in URLs, and the protocol-level option to obtain a token and
  retry after invalidation. Limitation: it does not establish safe replay for
  a broker operation or TradeStation-specific error behavior.
- **E15 — Cursor, “Cloud Agents” (Secrets troubleshooting).**
  https://cursor.com/docs/cloud-agent
  Accessed 2026-09-29. Supports: Dashboard/cloud-agent secrets are
  workspace/team-scoped environment values added at
  `cursor.com/dashboard/cloud-agents`; “Secrets are injected when an agent
  starts. Agents already running won't pick up new secrets”. Limitation:
  documents agent-start injection, not a workload-writable versioned secret
  store. The 2026-09-30 proposal rejects that mechanism as a production
  dependency and specifies runtime token state in
  [`TOKEN_STORE.md`](TOKEN_STORE.md). This citation does not select a
  bootstrap product or a database host.

Repository evidence, read at canonical base
`1ecbbe6d487d97195fde393b05c9499357599bdb` on 2026-09-26:

- [`AGENT_AUTHORITY.md`](AGENT_AUTHORITY.md) and
  [`CURRENT_STATE.md`](CURRENT_STATE.md): non-overridable prohibitions,
  least authority, current DRY_RUN-only status, and sole Operator authority.
- [`SIM_LIVE_BOUNDARY.md`](SIM_LIVE_BOUNDARY.md) and
  [`LIVE_PROMOTION.md`](LIVE_PROMOTION.md): independent environment,
  artifact, identity, secret, network, and policy separation; conjunctive LIVE
  denial.
- [`BROKER_CONTRACT.md`](BROKER_CONTRACT.md): accepted public-document
  findings and unresolved authentication/account/rate-limit groups.
- [`MONITORING.md`](MONITORING.md): prohibited telemetry values and
  fail-closed readiness.
- [`SIM_CERTIFICATION.md`](SIM_CERTIFICATION.md): future SIM-only credential,
  endpoint, account, secret-manager, and evidence gates.
- [`PHASE_2_PLAN.md`](PHASE_2_PLAN.md): P2-B ownership, r1/r2 scope, H2, G1,
  and G2 boundaries. Limitation: planning artifact only; it grants no phase,
  credential, or network authority.

## Dated addendum — Client Experience answers (2026-10-06)

This addendum does not edit the proposal above and does not fill the blank
Decision. Status remains **PROPOSED**. The Operator-supplied answers are
quoted in `docs/P2_TS_PROVIDER_EVIDENCE.md`. No authentication was performed.

Supersession, limited to the stated facts:

- U-17, for an attended probe only. Client Experience confirmed
  `offline_access` may be omitted. The session then lasts at most 20 minutes
  before re-authorization. The historical page conflict stays in the evidence
  register. It is not the live answer for that probe. The first probe omits
  the scope and does not expect a refresh token.
- U-04's "undocumented" clause. A SIM-only API key is not available. The same
  key is used for both environments; the base URL differs. The risk that the
  material is LIVE-capable is confirmed, not removed. G1 stays closed. Local
  host, transport, and test controls cannot be replaced by a provider SIM-only
  key. OAuth audience behavior was not answered.
- The assumption that default personal-use refresh tokens rotate every 30 or
  40 minutes or expire after 24 hours. For that default they are non-rotating,
  non-expiring, and long-lived. Refreshed access tokens last at most 20
  minutes. U-01 itself stays open: it asks which interval applies to a
  rotating configuration, and that configuration was not answered.
- U-09, in part. The quota identity named by the provider is the login.
  Aggregation across processes or tokens under one login stays unknown.
  U-09 is not closed. No additional login is provisioned.

Still open, and not chosen by this addendum:

- U-01 for rotating tokens, U-02 default-scope mechanics, U-03 confidential
  client plus PKCE, U-05 Native loopback and removal of default or wildcard
  callbacks, U-06 and U-08 revocation and refresh concurrency, U-07, U-14,
  and U-16.
- Application type. Regular Web requires `client_secret`. Native or Single
  Page can omit it and use a Code Verifier. The provider did not recommend
  one. Native PKCE remains an engineering preference in ADR-0005 and is not
  selected, because the callback form is unconfirmed.

A long-lived refresh token is a high-value secret. It is out of scope while
`offline_access` is omitted. Before any unattended phase, custody,
revocation, concurrency, replacement, compromise response, and TokenStore
behavior still require certification. This addendum grants none of those.
