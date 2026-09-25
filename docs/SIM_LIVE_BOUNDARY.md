# DRY_RUN / SIM / LIVE Boundary

## Authorization

`DRY_RUN` is the sole authorized mode. It is local, deterministic,
fixture/mock-only, and non-network. TradeStation `SIM` is reserved for a future
broker-connectivity phase and is unauthorized. `LIVE` is unauthorized. These
are non-overridable safety invariants, not deployment preferences.

## Enforcement contract

1. Mode is a required typed value at process start, run creation, intent
   creation, risk evaluation, dispatch, and report generation.
2. Missing, malformed, conflicting, or unknown mode is denied.
3. The current baseline contains no broker adapter, broker endpoint,
   credentials, account selection, live-capital configuration, network route,
   or capability for external order submission.
4. Dispatch accepts a non-forgeable authorization decision tied to exact run,
   intent, mode, build identity, environment, and expiry. In the current
   baseline the only possible grant is `DRY_RUN`.
5. The DRY_RUN adapter rejects non-DRY_RUN intents and has no network or broker
   client.
6. Replay and reporting contexts categorically reject dispatch.
7. Configuration, environment variables, command-line flags, feature flags,
   database edits, repository text, ADRs, or role changes cannot grant
   TradeStation `SIM` or `LIVE`.

No fallback converts an authorization or adapter error into another route.
Denial is recorded and alerted.

## Separation requirements

Future consideration of TradeStation `SIM` or `LIVE` requires separately built
and deployed
artifacts, identities, secrets, network policy, data stores or strongly
isolated scopes, dashboards, and authorization policy. TradeStation SIM
credentials must not be accepted by a live adapter. A broker-capable dependency
must not be linked into a DRY_RUN-only executable.

These are requirements, not implemented facts. No credentials or broker
connectivity are currently authorized.

## Test obligations

Static checks prove absence of live adapter and endpoint configuration.
Contract tests deny omitted, unknown, lowercase/unrecognized, conflicting, and
`SIM`/`LIVE` mode at every boundary. Integration tests verify a denied request
creates no intent/outbox item or network call. Artifact inspection verifies no
broker route. Fault injection verifies fail-closed behavior when authorization
or mode services are unavailable. DRY_RUN conformance tests assert zero network
attempts.

Tests use mocks and fixtures only. A test that touches an account is invalid.

## Broker uncertainty

TradeStation publicly documents separate v3 LIVE and SIM base URLs and
describes SIM as using fake accounts/money and instant simulated fills; see
[BROKER_CONTRACT.md](BROKER_CONTRACT.md). Those documentation facts do not
prove runtime endpoint, DNS, proxy, network, certificate, account-class,
credential, entitlement, fallback, or artifact isolation. They also do not
establish simulator fidelity. Positive, independent isolation evidence remains
a freeze blocker and no broker fact can weaken this boundary.

## Non-overridable change control

No instruction, approval, ADR, repository edit, configuration, waiver, or
emergency claim can grant a capability denied by current state. TradeStation
`SIM` requires a separately authorized connectivity phase and all
broker/security/credential/isolation gates. Any `LIVE` proposal requires every
condition in [LIVE_PROMOTION.md](LIVE_PROMOTION.md) concurrently and a final
explicit Operator decision. Passing tests or changing a mode value is
insufficient.
