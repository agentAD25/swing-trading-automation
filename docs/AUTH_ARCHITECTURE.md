# P2-B/r1 Authentication Architecture Research and Proposed Control Contract

- Status: **PROPOSED**
- Date: 2026-09-26
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
- `openid` is required. `offline_access` is required only when refresh tokens
  are requested. TradeStation defines `MarketData`, `ReadAccount`, `Trade`,
  `OptionSpreads`, and `Matrix` scopes. [E2, E4]
- Refresh tokens must be stored securely. The default is non-expiring.
  TradeStation documents an optional expiring/rotating policy and a 24-hour
  absolute lifetime, but its pages conflict on whether rotation occurs every
  30 or 40 minutes. [E1, E5]
- Revoking one refresh token revokes all refresh tokens for that API key.
  Disabling and later re-enabling a key can make old non-expiring refresh
  tokens usable again. Rotating the client secret does not invalidate existing
  non-expiring refresh tokens. [E1, E5]
- TradeStation session logout does not invalidate existing access or refresh
  tokens. Access tokens retain their 20-minute lifetime and refresh tokens
  remain subject to their separate lifetime and revocation rules. [E13]
- The authentication overview lists default API scopes as `MarketData`,
  `ReadAccount`, and `Trade`; the scopes page also describes
  `OptionSpreads` and `Matrix` as defaults. The actual key contract is
  unresolved. [E1, E4]
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
  are not documented.
- **Disposition:** candidate only after Client Experience confirms the chosen
  application topology and key configuration.

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
| Secret manager | Hold encrypted client secret (if any), refresh token, credential generation, and revocation metadata | No repository/file fallback and no DEV/TEST broker-secret namespace |
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
   and expiry. Otherwise the auth state is `NO_CREDENTIALS / BLOCKED`.
2. **Flow selection:** use only the exact key type accepted at P2-B/r2. PKCE,
   if selected, is mandatory `S256`; a missing challenge, missing verifier, or
   attempted downgrade blocks the transaction. No fallback between Options A,
   B, and C is permitted.
3. **Request creation:** generate transaction-specific, cryptographically
   random `state`; for PKCE generate a single-use high-entropy verifier and its
   `S256` challenge. Keep both only in encrypted/ephemeral server-side session
   state with a short, approved expiry. Do not put a token, verifier, secret,
   or sensitive diagnostic in a URL.
4. **Redirect:** use one exact, pre-registered HTTPS callback URI for SIM
   administration. Wildcards, open redirects, unregistered ports, and
   environment-shared callbacks are denied. Loopback HTTP is not proposed for
   a deployed environment.
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

| Future profile | Exact requested scopes | Explicitly absent |
| --- | --- | --- |
| Bounded G2 read-only probe | `openid ReadAccount`; add `MarketData` only if the approved probe includes market data | `offline_access`, `Trade`, `OptionSpreads`, `Matrix`, `profile`, `email` |
| Continuous SIM read-only worker | `openid offline_access ReadAccount`; add `MarketData` only for a named requirement | `Trade`, `OptionSpreads`, `Matrix`, `profile`, `email` |
| Future bounded SIM order harness, not authorized here | A separate key/token family with `openid offline_access ReadAccount Trade`; any `MarketData` or `OptionSpreads` addition requires a separately approved test need | `Matrix`, `profile`, `email`, and every unapproved scope |

The one-shot G2 profile intentionally requests no refresh token if the bounded
probe fits within the documented 20-minute access-token lifetime. A different
duration is not silently justified by adding `offline_access`.

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

1. Refresh begins before expiry using an Operator-approved safety margin. The
   exact margin, clock-skew tolerance, retry budget, and service objective are
   unresolved; no value is invented here.
2. A single auth coordinator holds a short lease with a monotonically
   increasing fencing generation. The secret-manager record contains the
   credential-family ID, current refresh-token version, current owner fence,
   expected scopes, environment, and lifecycle state.
3. Only the current fence owner may read the refresh token or call the token
   endpoint. Other workers wait for a newer access-token lease; they do not
   refresh independently.
4. The response is committed with compare-and-swap against both the refresh
   version and fence. When rotation returns a new refresh token, the new value
   is durably committed before an access token is published. The previous
   secret version is made unreadable and deleted according to the approved
   revocation/retention policy.
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

The future secret store must be explicitly approved at G1. The Phase 2 plan's
candidate pattern is Cursor Dashboard secrets or an equivalent managed secret
manager; this document does not provision or select a product.

Required properties:

- workload-identity access with least privilege and no shared human-readable
  bootstrap secret;
- separate SIM namespace, encryption at rest with managed keys separate from
  secret data, TLS in transit, object-level access policy, versioned
  compare-and-swap, auditing, expiry, revocation, and deletion;
- auth coordinator read/write access only to its exact SIM credential family;
  broker workers receive only bounded access-token leases;
- no repository, environment-file, command-line, image, application database,
  queue, artifact, clipboard, local disk, swap, core dump, or support-bundle
  copy;
- no plaintext backup; any approved backup has separate encryption,
  restricted restore authority, and tested deletion/retention;
- secret access, failed access, generation change, rotation, and revocation
  metadata are auditable without recording secret values.

The secret store is a mandatory safety dependency. Unavailable, stale,
partially available, or unverifiable storage makes readiness false, stops token
issuance/refresh, invalidates worker leases, and permits no broker request.
There is no file, environment-variable, cached-token, alternate-manager, or
operator-copy fallback.

Rotation and revocation are separate:

- client-secret rotation follows an approved cadence and immediately on
  suspected exposure, but TradeStation states that it does not revoke existing
  non-expiring refresh tokens;
- refresh-token rotation uses the broker-confirmed expiring/rotating policy
  and atomic generation handling above;
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
unresolved and must be confirmed before automation.

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
   application type, PKCE/client-auth support, exact callback, exact allowed
   scopes, refresh rotation/expiry, permitted logins, SIM-only restriction,
   account entitlements, revocation behavior, and rate-limit identity;
4. a separately owned read-only G2 credential profile with no `Trade`,
   `OptionSpreads`, `Matrix`, `profile`, or `email` grant;
5. an approved managed secret store and workload identities satisfying the
   fail-closed, encryption, audit, generation, rotation, revocation, backup,
   and deletion requirements above;
6. independent evidence that the exact SIM artifact has no LIVE adapter or
   endpoint selection and that application, DNS/proxy, mesh, firewall, and
   egress controls allow only the declared destinations;
7. synthetic-canary evidence for repository, build artifact, process
   arguments, local storage, logs, traces, exceptions, metrics, alerts,
   support bundles, and crash handling; and
8. legal/compliance/entitlement approval for the bounded SIM use.

The human Operator provisions or directs provisioning of the future credential
through the approved manager; no agent performs that action. Missing,
conflicting, stale, or key-generic evidence keeps G1 closed.

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
- one-shot G2 uses no `offline_access` unless a separately accepted need
  proves refresh is necessary.

The first authenticated activity is limited to token exchange and the approved
read-only SIM queries. Responses are quarantined as provenance-tagged
observations with identifiers and personal data excluded from logs. Any
unexpected scope, host, account class, response shape, authorization error, or
control degradation ends the probe. An independent post-run check must prove
zero write/order calls before G2 can be considered complete.

G2 evidence does not resolve future G3 order authorization and cannot
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

Passing these checks establishes document conformance only. It does not verify
runtime controls or open H2, G1, or G2.

Rollback is removal or supersession of this proposed document. No credential,
account, secret-manager object, network route, broker state, or runtime state
exists from this work.

## Proposed decision

No architecture decision is accepted at r1. The proposed candidate for P2-B/r2
is:

1. Authorization Code flow with transaction-specific `state` and mandatory
   `S256` PKCE when first-party support for the chosen client topology is
   confirmed; no flow downgrade;
2. capability-specific keys and exact scopes, with a one-shot, no-refresh,
   no-`Trade` G2 profile;
3. a centralized auth coordinator, managed encrypted secret store,
   generation/fencing-based single refresh owner, and no local fallback;
4. positive auth/SIM destination allowlists plus explicit multi-layer LIVE
   denial, separate from mode checks;
5. separate DEV/TEST/SIM identities, artifacts, data, networks, and secrets,
   with no broker credentials or egress in DEV/TEST and no LIVE environment;
   and
6. stop/revoke/reauthorize on uncertainty rather than retry, broaden scope, or
   cross an environment boundary.

The Operator may accept, reject, or require changes at a later gate. This
author cannot approve the proposal.

## Unresolved risks and decisions

| ID | Unknown or risk | Why it matters | Required owner/gate |
| --- | --- | --- | --- |
| U-01 | TradeStation says rotating refresh tokens rotate at both 30 and 40 minutes | Cannot safely set refresh timing or expected generation behavior | Client Experience + Operator before G1; observe at G2 only if authorized |
| U-02 | TradeStation pages conflict on default key scopes | A future key may carry unneeded order or options privilege | Client Experience before G1; exact returned scopes checked at G2 |
| U-03 | Confidential-client PKCE support is undocumented | Option C cannot be assumed; downgrade would weaken interception defense | Security owner + Client Experience at P2-B/r2/G1 |
| U-04 | SIM-only credential/key/account restriction is undocumented; OAuth audience is not SIM-specific | A stolen token might be LIVE-capable outside local egress controls | Client Experience + independent security review; unresolved blocks G1 |
| U-05 | Key-specific callbacks, permitted logins, account types, and entitlements are unknown | Wrong login or real-account adjacency can cross the boundary | Operator/Client Experience before G1 |
| U-06 | Refresh revocation request examples and parameter naming are internally inconsistent; propagation is unspecified | Incident response could falsely claim revocation | Broker researcher + Client Experience before G1 |
| U-07 | Sender-constrained access/refresh tokens and token introspection are not documented | Bearer-token theft and remote validity cannot be independently constrained/checked | Security owner; absence remains a residual risk |
| U-08 | Refresh rotation replay/family semantics and lost-response recovery are not fully documented | Concurrent or ambiguous refresh can revoke or orphan a family | Broker researcher; fail-closed reauthorization unless resolved |
| U-09 | Rate-limit identity across keys, users, processes, and accounts is unknown | Multi-worker ownership and backoff cannot be finalized | Operator topology decision before G1; bounded observation at G2 |
| U-10 | Exact secret-manager, workload platform, lease primitive, KMS, retention, and recovery objectives are unselected | Proposed controls cannot yet be independently tested | Human security/operations decision before H2/G1 |
| U-11 | OAuth clock skew, refresh margin, retry budget, lease duration, and recovery objectives are unset | Invented timing can cause expiry races or unsafe retries | Human security/operations decision at P2-B/r2 |
| U-12 | DNS, proxy, egress-gateway, certificate, and broker alias inventory is incomplete | Hostname checks alone do not prove network isolation | Network/security owners before G1 |
| U-13 | Legal, privacy, account-entitlement, automation, and retention obligations are unknown | Technical authorization does not establish permitted use | Qualified humans before G1 |
| U-14 | Access-token revocation behavior and cascade from refresh revocation are not TradeStation-documented | A locally revoked family may retain usable access tokens briefly | Security owner; stop local use immediately and treat remote validity as unknown |
| U-15 | ID-token issuer metadata, signing-key lifecycle, and claim-validation contract are outside r1 | Trusting decoded claims could create identity confusion | Future dedicated design before any ID-token claim is used |
| U-16 | TradeStation token-endpoint error schema, status mapping, throttling, timeout idempotency, and retry behavior are undocumented | Generic OAuth errors do not prove safe broker-specific retry or recovery behavior | Broker researcher + Client Experience before G1; bounded observation at G2 |

Every unresolved item remains a blocker at the named gate. No observation,
default, code path, or agent may silently choose a value.

## Evidence

All external sources were accessed 2026-09-26. TradeStation pages are mutable
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
  `OptionSpreads`, `Matrix`, required `openid`, refresh-enabling
  `offline_access`, and optional profile/email scopes. Limitation: default
  scope statements conflict with E1 and do not prove subset behavior for a
  future key.
- **E5 — TradeStation, “Refresh Tokens.”**
  https://api.tradestation.com/docs/fundamentals/authentication/refresh-tokens/
  Supports secure storage warning, 20-minute access-token lifetime, default
  non-expiring refresh tokens, optional rotation/expiry, 24-hour absolute
  rotating-token lifetime, refresh parameters, and API-key-wide refresh-token
  revocation. Limitation: says 30 minutes where E1 says 40; revocation examples
  are internally inconsistent on request shape.
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
