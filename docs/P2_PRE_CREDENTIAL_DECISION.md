# Pre-credential decision

Planning only. This note does not authorize a credential, an OAuth
session, a TradeStation call, a Supabase connection, a SIM order, or
`LIVE`. `DRY_RUN` remains the only authorized execution mode.

## Provenance

The 2026-10-01 package is commit
`bc6ab7ea92310ffa133b75b498f7f245af11f166` on draft PR #19. That commit is
not an ancestor of canonical `main`
`41218abb2eda5f06001703fb83c2cb9e43e5ec2e`. Its Proposed ADR used number
0003, which canonical `main` already uses for the accepted Group 4A
envelope ADR. This file is the current package. PR #19 is not updated and
is not merged by this change.

The 2026-10-01 gate token was
`P2_PRE_CREDENTIAL_CONTRACT_DECISION_REQUIRED` because official pages
conflicted with omitting `offline_access` and `Trade`. The 2026-10-06
Client Experience answers supersede that conflict for the attended probe
only, as classified in `docs/P2_TS_PROVIDER_EVIDENCE.md`. They do not
erase the historical page conflicts.

Current stop token:
`P2_TS_PROVIDER_EVIDENCE_RECONCILED_CALLBACK_CLARIFICATION_REQUIRED`.

ADR-0005 is Proposed. Its Decision is blank. The 2026-10-06 Native PKCE
preference is historical. The 2026-10-08 proposal is Option A, Regular
Web, and is not accepted. On 2026-10-09 the Operator recorded
`OPERATOR_PREFERENCE_OPTION_A_REGULAR_WEB_CONFIDENTIAL_CLIENT` for
planning and provider clarification only. That preference does not accept
the ADR and does not change this stop token. See
`docs/P2_TS_PROVIDER_EVIDENCE_2026-10-08.md`.

## First-probe profile

Attended. Read-only. SIM only by application enforcement, not by a
provider SIM-only key. Short session. No `offline_access`. No refresh
token. No orders. No streaming. No market data.

Requested scopes, and no others unless a later written technical
requirement appears: `openid`, `ReadAccount`.

Before any brokerage request, compare granted scope with that set. If the
grant contains an unexpected economic scope such as `Trade`, stop with
`UNEXPECTED_SCOPE_GRANTED`. Do not assume requested scope equals granted
scope.

If a refresh token is returned anyway, do not persist it, do not log it,
discard it, and stop with `UNEXPECTED_REFRESH_TOKEN_RETURNED`.

The access token is ephemeral and memory-only. It is not written to
PostgreSQL, Git, docs, logs, or chat. No durable token database is part
of this probe. TokenStore remains a later unattended-phase contract.

## LIVE controls

The provider cannot issue a SIM-only key. The same key is potentially
usable against LIVE if the base URL changes. A future implementation,
not built here, must keep all of the following. No configuration switch
promotes this probe to LIVE.

1. Typed environment authority. The only initial allowed environment is
   `SIM`. `LIVE` is not a default, a fallback, or a free-typed string.
2. Host allowlist. The only broker API host for the initial probe is
   `sim-api.tradestation.com`. `api.tradestation.com` is denied.
3. Transport enforcement. The HTTP transport rejects any TradeStation host
   other than that SIM host. The caller does not supply an arbitrary URL.
4. Credential policy. The material is classified
   `POTENTIALLY_LIVE_CAPABLE_PROVIDER_CREDENTIAL` and may be used only
   inside the SIM-authorized environment.
5. Endpoint allowlist. Higher layers do not receive a generic path method.
   The only read in C2 is `GET /v3/brokerage/accounts`.
6. Economic method deny. `POST`, `PUT`, `PATCH`, and `DELETE` brokerage
   operations are unavailable. The token `POST` to
   `https://signin.tradestation.com/oauth/token` is the authorization-code
   exchange only, not an order.
7. Tests, when that gate is authorized, must show a LIVE host attempt and
   a write attempt failing before any network transmission.
8. No LIVE promotion by configuration alone. LIVE stays a separate future
   human certification.

`src/swingtrade/group3_auth/readonly.py` already joins a SIM GET and keeps
`connect_allowed` false. That file is not changed here and is not a
connected client.

## C2 sequence — not executed

1. The Operator completes authorization.
2. The application receives the authorization response.
3. Validate OAuth `state`.
4. Exchange the authorization code with the selected flow.
5. Verify returned scope. Stop on `UNEXPECTED_SCOPE_GRANTED`.
6. Verify no refresh token. Stop on `UNEXPECTED_REFRESH_TOKEN_RETURNED`.
7. Verify runtime authority is `SIM`.
8. Verify the transport host is the approved SIM host.
9. Perform one read-only account-list request.
10. Capture sanitized structural evidence only.
11. Do not durably log raw account identifiers.
12. Stop.
13. The Operator reviews the expected SIM inventory.

C3, only after explicit Operator approval of that inventory, may read
balances, positions, and today's or open orders. Still read-only, SIM
only, no orders, and no streaming unless a later gate says otherwise.
C3 is not ready.

## Account identifiers

Raw account identifiers are sensitive. They do not go into Git, docs,
pull-request text, chat, or ordinary logs. The first probe compares them
in memory with an inventory the Operator keeps outside those places. A
later durable correlation, if required, needs a keyed identifier design.
An unkeyed short digest is not that design. This task does not add one.

## Rate limit

One login. No concurrency. No retry storm. One account-list request.
HTTP 429 stops the probe. Do not provision more logins. Capture sanitized
`X-RateLimit-*` metadata when present. Do not fail the probe only because
those headers are absent.

## Readiness

| Gate | Value | Why |
| --- | --- | --- |
| `TRADESTATION_API_ACCESS_REQUEST_READY` | NO | The remaining send is the callback question only. It has not been sent. |
| `BOOTSTRAP_SECRET_CUSTODY_READY` | NO | No holder is accepted. The first probe should not persist a token. |
| `TOKEN_ENCRYPTION_CUSTODY_READY` | NO | Deferred. Default personal refresh tokens are long-lived secrets and are not enabled. |
| `CALLBACK_CONFIGURATION_READY` | NO | Native loopback behavior was not answered. |
| `C2_READONLY_SIM_PROBE_READY` | NO | Callback, client setup, and account-inventory approval are open. |
| `C3_READONLY_SIM_PROBE_READY` | NO | Blocked by C2. |
| `AUTHENTICATED_READONLY_PROBE_READY` | NO | Same blockers. This task does not authorize the probe. |

## Historical 2026-10-01 positions

Preserved, and superseded only where the 2026-10-06 table conflicts:

- Flow was not selected among confidential Authorization Code, public
  PKCE, and confidential PKCE. That remains true. The provider has now
  stated which of the first two matches Web versus Native or Single Page.
  Confidential PKCE remains unconfirmed.
- One callback URI was not named. That remains true.
- Requested scopes were `openid` and `ReadAccount` only, with a broader
  grant erased and the attempt stopped. That local rule remains. The
  provider has now said a key can be configured, without describing the
  mechanism.
- Refresh interval 30 versus 40 was `PROVIDER_CONFIRMATION_REQUIRED`.
  For default personal-use keys it is superseded: those tokens are
  non-rotating and long-lived. The optional rotating interval stays open.
- A provider statement that the key cannot call LIVE did not exist. It
  now exists in the negative: a SIM-only key is not available.
- Memory-only authorization code and access token, and erasure of an
  unexpected refresh token, remain the local rule.
- Bootstrap custody was not selected. It remains unselected.

## 2026-10-08 boundary note

`src/swingtrade/group3_auth/boundary.py` now denies LIVE hosts, SIM
connection, redirects, and host overrides under `DRY_RUN`. It does not
open a socket and does not authorize the future SIM probe described
above. Naming `https://sim-api.tradestation.com/v3` still cannot connect.
