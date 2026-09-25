# SIM Certification Contract

## Status

This is a proposed future TradeStation SIM connectivity evidence gate, not a
certification result. TradeStation `SIM`, credentials, broker networking, and
implementation are currently unauthorized. The Phase 1 offline baseline uses
local non-network `DRY_RUN`; its fixture validation is not SIM certification.

During current Phase 1, no credential/OAuth flow, account discovery, endpoint
connection, query, order confirmation, simulated order submission,
replace/cancel, or stream test may run. Public documentation and offline
fixtures are the only permitted broker evidence.

## Future activation preconditions

This contract becomes executable only after the human Operator explicitly
authorizes a separate TradeStation SIM connectivity phase in current state.
That phase must have accepted broker, authentication, credential, endpoint,
account-scope, order-lifecycle, reconciliation, network-isolation, and incident
ADRs plus independent security/risk attestations. Authorization must bind an
exact artifact, scope, expiry, and authenticated TradeStation SIM environment.

## Future entry criteria

- named human system, risk, security, and release sign-off owners; these are
  future operational attestations, not Phase 1 acceptance deciders;
- accepted architecture, safety, data, event, and test ADRs;
- approved strategy/data/risk research contracts;
- deterministic implementation and pinned build artifact;
- controlled SIM-only OAuth/client configuration and credentials, if required,
  issued through an approved secret manager with least scopes and rotation;
- an authenticated TradeStation simulated account and approved account scope,
  if required, with no real account accepted;
- an exact allowlisted TradeStation SIM endpoint and network policy that denies
  every LIVE endpoint and fallback;
- approved bounded query, confirmation, simulated order, replace/cancel,
  stream, ambiguity, and reconciliation test cases with zero real-capital path;
- no live adapter, LIVE credential, real-account dependency, or live network
  route; and
- resolved licensing and legal/compliance obligations applicable to SIM.

## Required evidence packs

1. **Build:** source commit, dependency lock digest, toolchain, artifact digest,
   software inventory, and vulnerability/license results.
2. **Determinism:** repeated clean runs and replay produce byte-identical
   canonical events and reports from the WDC fixture.
3. **Correctness:** lifecycle, decimal/rounding, data-quality, state-machine,
   event evolution, and report calculation tests pass.
4. **Safety:** all mode-denial tests pass; inspection proves no reachable LIVE
   route, accepted LIVE identity/credential, or fallback from SIM.
5. **Resilience:** crash, duplicate, timeout, restart, lag, stale data, and
   dependency fault scenarios preserve invariants.
6. **Reconciliation:** all required mismatch scenarios are detected and block
   dependent activity; clean runs have no unresolved critical/high cases.
7. **Operations:** dashboards, alerts, runbooks, backup/restore, and incident
   exercises are demonstrated with named owners.
8. **Research:** input provenance, bias controls, cost assumptions, and
   limitations are documented; no efficacy claim is inferred from the fixture.
9. **Authenticated SIM contract:** only after future activation, evidence may
   include controlled OAuth/token lifecycle, SIM account/endpoint attestation,
   read-only account/order/position queries, order confirmation, bounded
   simulated order/replace/cancel tests, stream recovery, rate limits, and
   reconciliation. Every operation must prove SIM scope and preserve the
   separate non-overridable `LIVE` denial.

## Exit criteria

Certification requires zero safety blockers, zero unresolved critical/high
reconciliation cases, complete required evidence, reproducibility in an
independent clean environment, and signed approval by the named owners. Any
waiver is explicit, scoped, expiring, and cannot waive `LIVE` denial or ledger
integrity.

Quantitative reliability and performance thresholds are unresolved operator
choices; they must be set before certification based on approved requirements,
not selected after observing favorable results.

## Validity and revocation

Certification binds exact source, configuration schema, dependencies, artifact
digest, data/calendar versions, and evidence. A material change triggers a
declared subset or full recertification. Safety regression, unexplained
execution effect, integrity failure, or unreconciled position immediately
revokes certification and blocks dispatch.

## Explicit non-consequence

SIM certification authorizes neither Phase 2 nor `LIVE`. It supplies evidence
to the human Operator's separate decision process only. Credentials, accounts,
queries, and simulated orders used under a future authorization remain
prohibited before that authorization and confer no LIVE authority afterward.
