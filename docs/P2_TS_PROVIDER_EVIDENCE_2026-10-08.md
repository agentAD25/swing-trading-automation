# TradeStation provider evidence intake — 2026-10-08

Lane 2 record of the Operator's written Client Experience clarification.
This note does not authenticate, configure a key, call SIM or LIVE, place
an order, or accept ADR-0005. `DRY_RUN` remains the only authorized
execution mode. No Phase 2 authorization is granted.

The 2026-10-06 verbatim replies stay in `docs/P2_TS_PROVIDER_EVIDENCE.md`
and `docs/TRADESTATION_CLIENT_EXPERIENCE_QUESTIONS.md`. This file does not
replace them and does not add words to those quotations. The 2026-10-08
intake restates the same provider claims and records the architectural
consequences. It does not claim that a second, different email was fetched
from TradeStation by this agent.

Labels:

- **CONFIRMED** — the written provider reply states it.
- **PARTIALLY_CONFIRMED** — the reply states part of the claim and leaves
  the operational remainder open.
- **UNRESOLVED** — not answered for this key.
- **DOCUMENTED_PUBLIC** — a public page states it. That is not a
  Client Experience confirmation of this key.
- **ENGINEERING CONSEQUENCE** — a local design result, not a provider
  sentence.
- **PROPOSAL** — not an accepted ADR decision.

## Provenance

| Item | Value |
| --- | --- |
| Intake date | 2026-10-08 |
| Source | Operator-supplied written correspondence with TradeStation Client Experience, presented for this intake |
| Historical verbatim | 2026-10-06 replies already quoted in `docs/P2_TS_PROVIDER_EVIDENCE.md` |
| Official pages compared | TradeStation API specification, authentication overview, Auth Code, PKCE, scopes, refresh tokens, SIM vs LIVE, and rate-limit overview. Canonical URLs under `https://api.tradestation.com/docs/`. Accessed 2026-10-08 |
| Key reconfiguration | Not claimed. The Operator has received an API key. It has not been configured, used, or uploaded here |

Where the provider's account-specific reply and a public page differ, the
written reply is the evidence for this key's described default. Public
pages are not rewritten.

## TS-EVIDENCE-001 — OAuth application types

**PARTIALLY_CONFIRMED.**

CONFIRMED subclaims, matching the 2026-10-06 Q1 quotation:

- A Regular Web application uses standard Authorization Code and must send
  `client_secret` on the applicable token request.
- A Native or Single Page application can use Authorization Code with PKCE.
  PKCE uses a session-generated code verifier in place of `client_secret`.
- The supported flow depends on the configured application type.
- TradeStation did not choose an application type.

UNRESOLVED: the application type of the issued key. It is not assumed to
be Native, Single Page, or Regular Web.

DOCUMENTED_PUBLIC, authentication overview, accessed 2026-10-08: keys are
by default Regular Web and use standard Auth Code. PKCE for SPA or Native
requires a Client Experience configuration change. That default is not
proof of this key's configuration. The same page agrees with the provider
that the flow follows the application type.

ENGINEERING CONSEQUENCE: model both confidential Authorization Code and
public PKCE. Do not select the issued key's type in code.

## TS-EVIDENCE-002 — SIM and LIVE isolation

**CONFIRMED.**

CONFIRMED subclaims, matching the 2026-10-06 Q2 quotation:

- A SIM-only API key is not available.
- The same API key can be used for SIM and LIVE.
- The API environment is selected by the base URL.

DOCUMENTED_PUBLIC hosts, SIM vs LIVE page, accessed 2026-10-08. These URL
strings are not attributed to the Client Experience email:

- SIM: `https://sim-api.tradestation.com/v3`
- LIVE: `https://api.tradestation.com/v3`

The public page also warns that applications which let users switch
between SIM and LIVE can cause mistakes.

ENGINEERING CONSEQUENCE: a provider-enforced SIM-only credential boundary
does not exist. `DRY_RUN` must not send an authenticated brokerage
request. Both hosts are denied at the destination boundary. A string,
environment variable, header, or redirect cannot select LIVE or turn SIM
naming into a connection. Future SIM enablement is a separate governed
decision. LIVE enablement remains a stronger, separate process.

## TS-EVIDENCE-003 — Minimum scopes

**PARTIALLY_CONFIRMED.**

CONFIRMED subclaim, matching the 2026-10-06 Q3 quotation: after a key has
been generated and provided, scope configuration could be performed.

UNRESOLVED:

- The issued key has not been confirmed as restricted to `openid` and
  `ReadAccount`.
- Returned `scope` has not been confirmed as an authoritative list of
  every granted permission.
- Broader default scopes are not assumed to have been removed.
- Requesting only `ReadAccount` is not treated as proof that the token
  lacks `Trade`, `MarketData`, `Matrix`, `OptionSpreads`, or
  `offline_access`.

DOCUMENTED_PUBLIC scopes and Auth Code pages, accessed 2026-10-08, still
show examples that include `MarketData`, `ReadAccount`, and `Trade`, and
still describe `offline_access` as required for refresh tokens. The
historical default-scope conflict in `docs/BROKER_CONTRACT.md` stays
recorded.

ENGINEERING CONSEQUENCE: the initial profile may request only
`openid ReadAccount`. A granted set that is missing `ReadAccount` or
`openid`, or that contains any other scope, fails closed as
`MISSING_READ_SCOPE` or `UNEXPECTED_SCOPE_GRANTED`. This task does not
perform authorization to discover the real grant.

## TS-EVIDENCE-004 — offline_access

**CONFIRMED.**

Matching the 2026-10-06 Q4 quotation: `offline_access` may be omitted.
Without it, the session lifetime is at most 20 minutes and
re-authorization is required after expiration.

DOCUMENTED_PUBLIC pages still say `offline_access` is required to obtain
refresh tokens. For the attended, no-refresh profile, the provider reply
is the controlling statement. The public pages are not edited to hide
that conflict.

ENGINEERING CONSEQUENCE: profile A does not request `offline_access` and
does not fall back to requesting it. Expiration becomes
`REAUTHORIZATION_REQUIRED` or `EXPIRED_DURING_REQUEST`. There is no
automatic refresh.

## TS-EVIDENCE-005 — Refresh tokens

**CONFIRMED** for the default personal-use configuration the provider
described. UNRESOLVED whether the issued key is that default.

Matching the 2026-10-06 Q5 quotation:

- Default personal API-key refresh tokens are non-rotating.
- Those refresh tokens do not expire.
- Access tokens obtained through refresh last at most 20 minutes.

The 20-minute access-token lifetime also appears on the public Auth Code,
PKCE, and refresh-token pages (accessed 2026-10-08). The historical
30-versus-40-minute rotating-policy conflict stays open for a rotating
configuration. It does not describe the stated default.

ENGINEERING CONSEQUENCE, profile A (implemented with fake markers only):
access-token lifetime is exactly 1,200 seconds. A refresh token is
`UNEXPECTED_REFRESH_TOKEN`. Restart requires re-authorization because
nothing durable is stored.

ENGINEERING CONSEQUENCE, profile B (design only, activation raises
`PROFILE_B_NOT_AUTHORIZED`):

- Future secret storage must be encrypted and least-privilege.
- No plaintext token persistence.
- No secrets in logs or exception text.
- Refresh must be single-flight so concurrent callers do not each refresh.
- Rotation must be an explicit control. The provider's non-rotation
  statement is not a guarantee to depend on.
- Revocation and incident response stay Operator procedures.
- Authorization failure closes the session.
- Onboarding requires a later explicit authorization.
- This task does not acquire or persist a real refresh token.

## TS-EVIDENCE-006 — Callbacks

**PARTIALLY_CONFIRMED.**

CONFIRMED subclaim, matching the 2026-10-06 Q6 quotation: additional
callback URLs can be requested through Client Experience.

UNRESOLVED:

- Whether existing callbacks can be removed.
- Which native loopback forms this key would accept.
- Whether a dynamic port is accepted.
- Whether the current registration suits a cloud-hosted confidential
  client.

ENGINEERING CONSEQUENCE: native loopback is not treated as approved.
Choosing a cloud-hosted Regular Web client would make native loopback
unnecessary only as an architectural proposal. That is not provider
confirmation. See DEP-TS-001 below.

## TS-EVIDENCE-007 — Account entitlement

**CONFIRMED.**

Matching the 2026-10-06 Q7 quotation:

- API access follows the authenticated login.
- Accounts available to that login are the accessible set.
- Other clients cannot use the key for their accounts without prior
  authorization.
- No additional entitlement is required merely to view that login's own
  accounts or existing data subscriptions.

UNRESOLVED: which accounts exist. This repository does not record account
identifiers. Fixture parsers keep SHA-256 digests and do not render raw
ids.

ENGINEERING CONSEQUENCE: one Operator login. No multi-user credential
sharing.

## TS-EVIDENCE-008 — Rate limits

**CONFIRMED** for per-login enforcement. Numeric quotas and header
presence on this key remain UNRESOLVED.

Matching the 2026-10-06 Q8 quotation:

- Limits are enforced per login associated with the key.
- Additional logins can have separate rate and streaming limits.
- Those logins may share application credential configuration.

DOCUMENTED_PUBLIC, rate-limit overview, accessed 2026-10-08: quotas are
applied on a per-user basis; HTTP 429 is the excess response; headers
beginning with `X-RateLimit-*` describe the interval, remaining requests,
and reset. The provider reply did not confirm those header names for this
key. Absence of the headers is not a fixture failure. A non-numeric
documented header stops the login rather than being guessed.

ENGINEERING CONSEQUENCE: throttle state is per synthetic login label.
HTTP 429 stops that login. `Retry-After` is recorded only when it is a
bounded integer number of seconds. The initial retry budget is zero.
Additional logins are not provisioned. Limits are not bypassed.

## Discrepancies retained

| Earlier assumption | 2026-10-08 classification |
| --- | --- |
| A SIM-only key might isolate LIVE | CONFIRMED unavailable |
| Native PKCE was the engineering preference | Superseded as a preference by the confidential-web proposal below. Not selected by the provider. ADR Decision remains blank |
| Public pages require `offline_access` on every authorization | Provider CONFIRMED omission for a session of at most 20 minutes. Public pages remain in the evidence register |
| Default refresh tokens rotate every 30 or 40 minutes or die at 24 hours | Not the stated personal-use default. Rotating-policy interval stays UNRESOLVED |
| Requested scope equals granted scope | UNRESOLVED. Local validation denies elevated grants anyway |
| This key is Regular Web because that is the documented default | UNRESOLVED. The default is DOCUMENTED_PUBLIC only |

## DEP-TS-001

`DEP-TS-001_NATIVE_PKCE_CALLBACK = NOT_CLOSED_BY_PROVIDER`

The original dependency asks for the native loopback callback form. The
2026-10-08 reply does not answer it. Additional callback URLs being
requestable does not close it.

`ARCHITECTURAL_NECESSITY_UNDER_PROPOSED_OPTION_A = NOT_REQUIRED`

A cloud-hosted confidential Regular Web client uses one exact HTTPS
callback. It does not need a native loopback callback. That conclusion is
a proposal in ADR-0005. It is not a provider resolution and it is not an
accepted decision. The ADR template leaves the Decision section blank
while status is Proposed, and this agent cannot accept an ADR.

`FORMAL_REGISTRY_STATUS = OPEN_FOR_LANE_1`

`docs/WORKSTREAM_DEPENDENCIES.md` is Lane 1's registry. This branch does
not change it. On 2026-10-09 the Operator recorded
`OPERATOR_PREFERENCE_OPTION_A_REGULAR_WEB_CONFIDENTIAL_CLIENT`. That
preference is not ADR acceptance and is not a provider answer. Lane 2
recommends the narrative disposition
`SUPERSEDED_BY_OPTION_A_PENDING_ARCHITECTURE_ACCEPTANCE`. Until Lane 1
records it, the registry Current state stays `OPEN`. The controlled lane
state `SUPERSEDED` is not the recommendation, because architecture
acceptance is still pending. `DEP-TS-001` stays
`NOT_CLOSED_BY_PROVIDER`. If Option A later becomes infeasible, the
native callback question is blocking again. The historical unsent native
question stays in `docs/TRADESTATION_CLIENT_EXPERIENCE_QUESTIONS.md` and
is not the active follow-up.

Separate open items, proposed for Lane 1 registration and not inserted
into that file here:

| Proposed id | State | Claim |
| --- | --- | --- |
| `DEP-TS-002` | `OPEN` / UNRESOLVED | Issued key application type is unverified. Ask whether it is Regular Web, and whether conversion is possible, without requesting a change now |
| `DEP-TS-003` | `OPEN` / UNRESOLVED | Granted scope is not confirmed as only `openid` and `ReadAccount`, excluding Trade, MarketData, Matrix, OptionSpreads, and `offline_access` |
| `DEP-TS-004` | `OPEN` / UNRESOLVED | Whether one later-named HTTPS callback can be the sole registration is not confirmed. No production hostname is selected |

## ADR-0005 proposal

Status remains **Proposed**. Decision section remains blank.

PROPOSAL: Option A, Regular Web confidential-client Authorization Code,
for a cloud-hosted service. Rationale is in the ADR. The issued key is
not assumed to be configured that way. On 2026-10-09 the Operator recorded
`OPERATOR_PREFERENCE_OPTION_A_REGULAR_WEB_CONFIDENTIAL_CLIENT`. That
preference is not acceptance. Option B remains an alternative if the
issued key cannot support the confidential-client architecture. It is not
characterized as insecure or unsupported, and TradeStation did not reject
it. Option C, a browser SPA, is a worse fit for unattended server custody.

## Offline boundary that this intake adds

`src/swingtrade/group3_auth/boundary.py` boots only `DRY_RUN`. It denies
LIVE host forms, denies SIM connection, denies redirects and host
overrides, separates `signin.tradestation.com` from the brokerage hosts,
and denies order-placement paths and write methods. `connect_allowed` is
false. The module does not import a network client.

`src/swingtrade/group3_auth/scopes.py` enforces the initial scope set.
`src/swingtrade/group3_auth/session.py` models a 1,200-second attended
session with fake markers and refuses profile B.
`src/swingtrade/group3_auth/brokerage_read.py` parses in-memory fixtures
for accounts, balances, positions, and orders using property names from
the public v3 specification. It does not send requests. Optional `Spread`
is rejected until its nested types are pinned.
`src/swingtrade/group3_auth/throttle.py` stops a synthetic login on
HTTP 429.

These tests do not prove TradeStation connectivity or real-account
compatibility.

## Credential onboarding workflow (not executed)

Future onboarding, after a separate authorization, would:

1. Store the client secret and any later refresh token in an encrypted
   secret manager, not in Git, CI logs, Markdown, or fixtures.
2. Name the Operator as the rotation and revocation owner.
3. Require a written Operator approval that names `DRY_RUN` versus a
   future SIM phase. Approval text cannot enable LIVE.
4. Keep the secret out of the DRY_RUN artifact. A SIM phase would use a
   separate deployment identity.
5. Record only redacted audit evidence: timestamps, reason codes, and
   digests.
6. On compromise, revoke through the provider, discard local material,
   and fail closed until a new Operator authorization.

This task does not ask for the secret, authorization code, access token,
refresh token, password, cookie, or account number, and it does not
perform steps 1–6.

## Readiness

`C2_READONLY_SIM_PROBE_READY = NO`

Still required before any connection:

1. Operator acceptance of ADR-0005, which is not this record.
2. Written confirmation of this key's application type (`DEP-TS-002`).
3. Written or later-authorized confirmation of the granted scope
   (`DEP-TS-003`).
4. A registered sole HTTPS callback if Option A is accepted
   (`DEP-TS-004`), or the native callback answer if Option A is rejected.
5. A separate authorization to onboard credentials and to open a
   read-only SIM connection. Phase 2 is not that authorization.

`GROUP4B_TRADE_PLAN_ENGINE_READY` is unchanged. Gmail PR #21 and the
Lane 4 branch are not modified.

## 2026-10-09 Operator preference

`OPERATOR_PREFERENCE_OPTION_A_REGULAR_WEB_CONFIDENTIAL_CLIENT`

Fact: the Operator approved Option A as the preferred TradeStation OAuth
architecture. The approval is limited to architectural planning, provider
clarification, and non-credential readiness preparation. It is conditional
on repository governance, accepted authorization requirements, provider
confirmation, a compatible issued-key configuration, and continued SIM/LIVE
safety enforcement.

Fact: the approval does not accept ADR-0005, onboard a credential, start
OAuth, make a broker request, connect to SIM or LIVE, submit an order,
authorize Phase 2, or merge PR #22. ADR-0005 status remains Proposed. Its
Decision section remains blank. `DRY_RUN` remains the only authorized
runtime posture.

### Dependency recommendation

| ID | Evidence classification | Registry recommendation |
| --- | --- | --- |
| `DEP-TS-001` | `NOT_CLOSED_BY_PROVIDER` | Narrative `SUPERSEDED_BY_OPTION_A_PENDING_ARCHITECTURE_ACCEPTANCE`. Current state stays `OPEN` until Lane 1 records it. Not provider-confirmed |
| `DEP-TS-002` | UNRESOLVED | Stay `OPEN`. Is the issued key Regular Web? If not, can it be converted or replaced by an equivalent compatible application, with no change requested now? |
| `DEP-TS-003` | UNRESOLVED | Stay `OPEN`. Can the key and authorization be restricted to `openid` and `ReadAccount`, excluding Trade, MarketData, Matrix, OptionSpreads, and `offline_access`, and do returned granted scopes reflect that restriction? |
| `DEP-TS-004` | UNRESOLVED | Stay `OPEN`. Can one specifically registered HTTPS callback be the sole callback, with unused registrations removed? No production hostname is chosen |

Lane 1 owns the registry. The request is in `docs/LANE2_OPTION_A_HANDOFF.md`.
This file does not edit `docs/WORKSTREAM_DEPENDENCIES.md` or
`docs/WORKSTREAM_STATUS.md`.

The active provider draft is the unsent 2026-10-09 consolidated follow-up
in `docs/TRADESTATION_CLIENT_EXPERIENCE_QUESTIONS.md`. It is not sent.
The native PKCE draft remains historical and is not the active question.

### Onboarding architecture review

This review inspects existing contracts. It does not create a secret store,
a callback service, a hostname, or a token.

| Control | Existing coverage | Gap |
| --- | --- | --- |
| Confidential client-secret storage | `docs/AUTH_ARCHITECTURE.md` separates a bootstrap secret holder from TokenStore and rejects repository, file, and environment-variable copies | No operational secret store exists |
| Secure server-side handling | Same design: auth coordinator is the only future exchanger; forms in `src/swingtrade/group3_auth/forms.py` are unsent templates with `connect_allowed` false | No server is deployed |
| HTTPS callback validation | `src/swingtrade/group3_auth/callback.py` classifies an allowlisted callback and does not retain the authorization code. `docs/AUTH_ARCHITECTURE.md` requires one exact pre-registered HTTPS callback | No production hostname or callback service. `DEP-TS-004` is open |
| OAuth state and CSRF | `src/swingtrade/group3_auth/state.py` issues single-use process-local state and is not a token store. The callback path validates and consumes it | Process-local only. Not a deployed CSRF binding |
| Token-exchange restrictions | Standard-flow form templates require `client_secret` and are not posted. `boundary.py` denies auth-endpoint connection, redirects, and host overrides under `DRY_RUN` | No exchange is authorized |
| Expiration and reauthorization | `session.py` accepts only a 1,200-second attended session and returns `REAUTHORIZATION_REQUIRED` after restart | Fake markers only |
| Future refresh-token handling | Profile B raises `PROFILE_B_NOT_AUTHORIZED`. Design refresh rules are in `docs/AUTH_ARCHITECTURE.md` | Unattended refresh is not authorized |
| Long-lived refresh protection | Design rejects storing a non-expiring unconstrained refresh token. Provider default personal-use refresh tokens are non-rotating and non-expiring | Whether this key uses that default is unresolved. No refresh credential is held |
| Secret rotation | Design separates client-secret rotation from refresh revocation. Provider evidence says rotating the client secret does not invalidate existing non-expiring refresh tokens | No rotation procedure is implemented |
| Credential revocation | Design requires provider revocation plus local deletion, and records that key disable and logout are insufficient | Exact revocation request encoding remains unresolved in `docs/AUTH_ARCHITECTURE.md` |
| Audit without secrets | Design allowlists diagnostic fields. Session and callback rendering omit secret values | No operational audit sink |
| SIM host allowlisting | `docs/AUTH_ARCHITECTURE.md` names `sim-api.tradestation.com` as a future allowlist entry. `boundary.py` denies SIM connection in `DRY_RUN` | SIM connectivity is unauthorized |
| LIVE host denial | `boundary.py` denies the LIVE host without treating the SIM host as LIVE. `docs/SIM_LIVE_BOUNDARY.md` keeps LIVE unauthorized | Must stay independent of the shared API key |
| Unexpected elevated scopes | `scopes.py` fail-closes Trade, MarketData, Matrix, OptionSpreads, and `offline_access` | Granted-scope behavior for this key is `DEP-TS-003` and remains open |

Inference: the design covers the listed controls as contracts and offline
checks. It does not cover them as an operational credential integration.
Assumption: a future hosting architecture and DNS owner will name the
callback. That hostname is unknown. Open questions are `DEP-TS-002`,
`DEP-TS-003`, `DEP-TS-004`, ADR acceptance, and a separate credential
authorization.

## 2026-10-10 official documentation

`docs/P2_TS_OFFICIAL_DOCS_2026-10-10.md` compares current TradeStation
pages with this intake. It does not replace the provider quotations or
the classifications above. Published defaults are not key-specific
confirmation. `DEP-TS-002`, `DEP-TS-003`, and `DEP-TS-004` stay open.
ADR-0005 stays Proposed.
