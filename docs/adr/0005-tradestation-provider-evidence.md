# ADR-0005: TradeStation provider evidence for a future attended probe

- Status: Proposed
- Date: 2026-10-06
- Amended: 2026-10-08 (proposal only); 2026-10-09 (Operator
  architectural preference recorded; Decision remains blank); 2026-10-10
  (official-documentation research cited; Decision remains blank)
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
option is a proposal, not a provider authorization. On 2026-10-09 the
Operator recorded a preference for this option. That preference is stated
under Proposal and is not an acceptance of this ADR.

### Option B — Native or public client with PKCE

Authorization Code with a code verifier. `client_secret` can be omitted.
The 2026-10-06 note preferred this for an attended probe because it
avoids a persistent secret. The native callback form is still
unconfirmed. A public client is a weaker custody model for an unattended
cloud service. Native or public-client PKCE is not the currently preferred
architecture. It remains an alternative if the existing issued key cannot
support the confidential-client architecture. This record does not
characterize PKCE as insecure or unsupported, and it does not claim that
TradeStation rejected it.

### Option C — Single Page application with PKCE

The provider confirmed the same PKCE omission of `client_secret`. A
browser-resident client is a poor fit for server-side custody, restart
recovery, and unattended operation. Not proposed.

No other documented flow fits the objectives better. Implicit grant is
not the provider's described model. Resource-owner password is not a
documented option used here.

## Proposal (not a Decision)

### Proposed selection

Regular Web confidential-client Authorization Code.

On 2026-10-09 the Operator recorded this architectural preference:

`OPERATOR_PREFERENCE_OPTION_A_REGULAR_WEB_CONFIDENTIAL_CLIENT`

The token is limited to architectural planning, provider clarification,
and non-credential readiness preparation. It is conditional on existing
repository governance, accepted authorization requirements, TradeStation
provider confirmation, a compatible configuration of the issued API key,
and continued SIM/LIVE safety enforcement. It does not accept this ADR,
onboard a credential, authorize OAuth login, authorize a broker request,
authorize SIM or LIVE connectivity or orders, authorize Phase 2, or
authorize a PR merge. `DRY_RUN` remains the only authorized runtime
posture.

Recorded preference details:

- Deployment architecture: cloud-hosted backend.
- OAuth flow: confidential-client Authorization Code.
- Application type: Regular Web, subject to provider confirmation.
- Callback: one explicitly registered HTTPS endpoint, subject to provider
  confirmation. No production callback hostname is selected in this ADR.
- Client secret: eventual secure server-side custody.
- Initial validation profile: attended, read-only, without `offline_access`.
- Future unattended profile: design-only and separately authorized.
- API execution posture: `DRY_RUN`.
- `LIVE`: prohibited.

The proposal does not assume the issued key is already Regular Web.

### Rationale

- The flow is appropriate for a cloud-hosted backend.
- A confidential client secret can eventually be held server-side.
- The deployment does not require native desktop-loopback authentication.
- The shape can support the intended unattended architecture later, subject
  to token-lifecycle constraints and a separate authorization.
- One narrowly defined registered HTTPS callback is sufficient.

### Conditions

- Verify the actual issued key's application type (`DEP-TS-002`).
- Confirm provider-supported callback registration (`DEP-TS-004`).
- Confirm the desired minimum granted scopes (`DEP-TS-003`).
- Maintain an explicit credential-onboarding authorization before any
  secret is stored or used.
- Maintain `DRY_RUN`-only operation until a later authorization.
- Preserve the LIVE host prohibition.
- Preserve independent SIM and LIVE safety gates.

### Known limitation

TradeStation confirmed that the same API key can address both SIM and LIVE
by changing the base URL. The credential itself does not enforce SIM
isolation. The adapter and runtime governance must independently prevent
LIVE connectivity. Accepting this ADR later would still not grant LIVE,
SIM, or credential use while `docs/CURRENT_STATE.md` denies them.

### Deferred alternative

Native or public-client PKCE (Option B) is not the currently preferred
architecture. It remains an alternative if the existing issued key cannot
support the confidential-client architecture. Option C stays not proposed.

## Decision

## Consequences

The Decision section is blank because status is Proposed. The repository
ADR template requires that. This agent cannot accept the ADR. The
2026-10-09 preference is not that acceptance.

Until the Operator accepts a decision, no API client should be created
and no credential should be onboarded. `offline_access` stays omitted
for the initial attended profile. A returned refresh token would be
discarded and the attempt stopped. Default personal-use refresh tokens,
if a later unattended phase requests them, are high-value long-lived
secrets, not 30-minute or 40-minute rotating tokens. Profile B in
`src/swingtrade/group3_auth/session.py` raises
`PROFILE_B_NOT_AUTHORIZED`.

The Operator preference makes native loopback (`DEP-TS-001`) unnecessary
for the proposed deployment. That is an architectural preference, not a
provider answer. Lane 2 recommends the narrative disposition
`SUPERSEDED_BY_OPTION_A_PENDING_ARCHITECTURE_ACCEPTANCE`. The Lane 1
registry still records `OPEN`. The controlled lane state `SUPERSEDED` is
not requested, because ADR acceptance is still pending. `DEP-TS-001` is
not provider-confirmed. If Option A later becomes infeasible, the native
callback question is blocking again.

## Validation and rollback

Rollback is to leave this ADR Proposed and make no TradeStation call.
Failure signals are any scope broader than `openid` and `ReadAccount`, any
LIVE host, any write method, or any stored token.

## Unresolved questions

The issued key's application type. Granted-scope behavior. Whether one
HTTPS callback can be the sole registered callback, with no hostname
chosen here. Native loopback only if Option A becomes infeasible.
Optional rotating-policy interval. Refresh concurrency and revocation for
a real token. Non-default key configurations. The Operator's expected SIM
account inventory. Operator acceptance of this ADR. The 2026-10-09
preference does not close that acceptance.

## Evidence

Operator-supplied Client Experience writing, 2026-10-06, recorded in
`docs/P2_TS_PROVIDER_EVIDENCE.md`. The 2026-10-08 intake, which does not
replace those quotations, is
`docs/P2_TS_PROVIDER_EVIDENCE_2026-10-08.md`. The 2026-10-09 preference
is recorded in that intake and in
`docs/TRADESTATION_CLIENT_EXPERIENCE_QUESTIONS.md`. Limitation: neither
the 2026-10-06 quotations nor the 2026-10-08 intake chooses an
application type or describes loopback callbacks. The preference is an
Operator architecture choice, not a provider confirmation. Public
pages accessed 2026-10-08 are cited in that intake. Prior first-party
page conflicts remain in `docs/P2_BROKER_RESEARCH.md` and are not deleted.
The 2026-10-10 official-documentation comparison is
`docs/P2_TS_OFFICIAL_DOCS_2026-10-10.md`. It does not confirm the issued
key and does not fill this Decision. A later offline parser change accepts
the documented order `Spread` string and classifies HTTP 400 and 404. That
change does not accept this ADR.
