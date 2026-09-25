# Phase 1B Test Plan

## Status and principles

This is design-time coverage; no test framework or implementation is selected.
Tests must be deterministic, offline, credential-free, and incapable of
external order submission. Every result records commit, artifact digest,
fixture digest, configuration, seed, supplied clock, command, and outcome.

## Coverage matrix

| Area | Required coverage |
| --- | --- |
| Data | canonical decimals/times/JSON, OHLC checks, revisions, provenance, cutoff |
| Events | schema, append conflict, aggregate ordering, late facts, replay, evolution |
| Lifecycle | every valid transition and every invalid transition; partial fill, correction, restart |
| Idempotency | duplicates, concurrency, crashes around effect, lease expiry, key conflict |
| Risk/safety | block on every unknown; mode denial at every boundary; no live route |
| Reconciliation | exact, missing, duplicate, excess, late, ambiguous, stale, projection rebuild |
| Reporting | high-water mark, ties, digest stability, withholding, sensitive-field exclusion |
| Operations | metric contracts, bounded labels, alert dedup/recovery, readiness blockers |
| Resilience | dependency loss, clock fault, corrupt input, lag, restart, retry exhaustion |
| Supply chain | locked dependencies, software inventory, vulnerability/license policy, reproducible build |

## Test layers

1. Schema and pure property tests.
2. Aggregate/state-machine model tests.
3. Component contract tests using in-memory fakes.
4. Local non-network DRY_RUN integration and restart/fault-injection tests.
5. End-to-end deterministic fixture replay.
6. Static artifact and authorization-boundary inspection.
7. Independent clean-environment certification replay.

No test may call a broker endpoint. Broker adapter conformance is deferred
until public behavior is researched and a separately authorized test
environment is approved.

## WDC reference conformance

The fixture at `tests/fixtures/wdc-reference/` supplies synthetic bars and a
fully prescribed test-only decision. A conforming implementation must:

1. verify all manifest SHA-256 values before parsing;
2. use the fixed clock and identifiers from `scenario.json`;
3. emit canonical event lines exactly matching `expected-events.jsonl`;
4. emit canonical report bytes exactly matching `expected-report.json`; and
5. produce no network access or nondeterministic fields.

In addition to byte comparison, validation independently:

- recomputes each 64-hex idempotency digest from the declared canonical input;
- requires `created → validated → dispatch_requested → dispatched` with
  aggregate versions 1–4 for both intents;
- requires each transition's prior/next state, reason code, initiating cause,
  timestamps, durable identity, immediate cause, and correlation; negative
  mutation tests remove `prior_state`, `next_state`, and `reason_code`
  individually and require rejection;
- removes only `content_digest` from the report, canonicalizes and hashes it,
  then ties that digest and high-water mark to the report event; and
- verifies one non-account `trade_scope_id` across scenario, trade events, and
  report.

Run the standard-library regression validator from the repository root:

```sh
python3 tests/validate_phase1_contracts.py
```

The decision rule exists only to exercise contracts and must not be imported
into strategy code.

## Negative acceptance

Any TradeStation `SIM` or `LIVE` acceptance, external network order call,
duplicate logical effect,
silent data correction, guessed identity/state, unreconciled final report,
non-reproducible result, secret/account fixture, or missing evidence fails the
suite.

## Traceability and exit

Each requirement in the architecture contracts must map to one or more test
ids and evidence artifacts. Coverage percentages alone are insufficient.
Phase 1B exit means the contracts and planned coverage are internally
consistent; it does not mean tests have run against nonexistent production
code and does not start Phase 2.
