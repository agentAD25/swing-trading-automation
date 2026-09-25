# SIM / LIVE Boundary

## Authorization

`SIM` is the sole authorized mode. `LIVE` is unauthorized. This boundary is a
security and safety invariant, not a deployment preference.

## Enforcement contract

1. Mode is a required typed value at process start, run creation, intent
   creation, risk evaluation, dispatch, and report generation.
2. Missing, malformed, conflicting, or unknown mode is denied.
3. Phase 1B builds contain no live adapter, live endpoint, live credentials,
   account selection, live-capital configuration, or route capable of external
   order submission.
4. Dispatch accepts a non-forgeable authorization decision tied to exact run,
   intent, mode, build identity, environment, and expiry. In Phase 1B the only
   possible grant is `SIM`.
5. The SIM adapter rejects non-SIM intents and has no network order client.
6. Replay and reporting contexts categorically reject dispatch.
7. Configuration, environment variables, command-line flags, feature flags,
   database edits, or operator role changes cannot grant `LIVE`.

No fallback converts an authorization or adapter error into another route.
Denial is recorded and alerted.

## Separation requirements

Future consideration of `LIVE` requires separately built and deployed
artifacts, identities, secrets, network policy, data stores or strongly
isolated scopes, dashboards, and authorization policy. SIM credentials, if a
simulator ever requires them, must not be accepted by a live adapter. A
production-capable dependency must not be linked into a SIM-only executable
without explicit security review.

These are requirements, not implemented facts. No credentials may be obtained
during Phase 1B.

## Test obligations

Static checks prove absence of live adapter and endpoint configuration.
Contract tests deny omitted, unknown, lowercase/unrecognized, conflicting, and
`LIVE` mode at every boundary. Integration tests verify a denied request
creates no intent/outbox item or network call. Artifact inspection verifies no
live route. Fault injection verifies fail-closed behavior when authorization
or mode services are unavailable.

Tests use mocks and fixtures only. A test that touches an account is invalid.

## Broker uncertainty

No assertion is made about TradeStation SIM/LIVE URL separation, account
classes, credential scopes, order-routing behavior, or environment labels.
Those facts require first-party evidence and cannot weaken this boundary.

## Change control

Any proposal to add a live-capable artifact is a new phase, requires named
human approval, accepted ADRs, successful SIM certification, completion of
[LIVE_PROMOTION.md](LIVE_PROMOTION.md), and an explicit update to
`docs/CURRENT_STATE.md`. Passing tests or changing a mode value is
insufficient.
