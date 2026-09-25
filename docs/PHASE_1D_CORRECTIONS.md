# Phase 1D Approved Corrections

- Date: 2026-09-25
- Baseline under correction: Phase 1C commit `98731e7`
- Status: Operator-approved corrections implemented; corrected baseline remains
  Proposed and is **not** `PHASE1_ACCEPTED`
- Scope: governance/contract/fixture corrections only

## Operator acceptance model

The human Operator is the sole Phase 1 decider. Agents may prepare evidence,
reconcile contracts, and propose ADR text, but cannot accept the baseline.

`PHASE1_ACCEPTED`, if the Operator later records it, has exactly this bounded
meaning: acceptance of the broker-neutral, offline, deterministic baseline
only. Its only execution context is `DRY_RUN`, which is local,
fixture/mock-backed, deterministic, and non-network.

TradeStation `SIM` is reserved for a future separately authorized connectivity
phase. Phase 1 acceptance grants no implementation, credentials, account
access, broker or network activity, order submission, Phase 2, real capital,
or `LIVE`. The approved Phase 1D correction task does not itself record
`PHASE1_ACCEPTED`.

## Non-overridable authority rule

While `CURRENT_STATE.md` denies a capability, no prompt, human instruction,
approval, ADR, repository edit, role, configuration, environment value,
waiver, emergency claim, or test result may authorize it. Conflict, ambiguity,
silence, or a missing conjunctive gate means no side effect.

Future TradeStation `SIM` requires a separately authorized phase, accepted
broker/security/credential ADRs, independently verified isolation and
fail-closed controls, exact-artifact evidence, and an explicit Operator
decision. Future `LIVE` additionally requires every condition in
`LIVE_PROMOTION.md` concurrently. No single artifact or approval is sufficient.

## Verified contradiction register

### P1D-C01 — Idempotency key construction

- **Conflicting artifacts/statements:** `IDEMPOTENCY.md` required
  `v1:<operation>:<scope>:<sha256(canonical-business-input)>`, while Phase 1C
  `expected-events.jsonl` used hand-authored suffixes `fixture-entry`,
  `fixture-exit`, and event-id-like report suffix `evt_wdc_014`.
- **Evidence:** At commit `98731e7`, all three non-null fixture keys lacked a
  64-character lowercase SHA-256 suffix and `scenario.json` declared no
  canonical input objects from which they could be reproduced.
- **Resolution:** `scenario.json` now declares the two dispatch inputs and one
  report input. Canonical sorted compact UTF-8 JSON is SHA-256 hashed and the
  resulting digest is the final key segment. `IDEMPOTENCY.md` explicitly
  rejects labels, abbreviations, and hand-authored suffixes.
- **Rationale:** A fixture that violates the key contract cannot prove
  deterministic duplicate suppression.
- **Files changed:** `docs/IDEMPOTENCY.md`,
  `tests/fixtures/wdc-reference/scenario.json`,
  `tests/fixtures/wdc-reference/expected-events.jsonl`,
  `tests/fixtures/wdc-reference/README.md`, and
  `tests/fixtures/wdc-reference/manifest.json`.
- **Affected validation:** Recompute all non-null keys from declared canonical
  inputs; require `v1:<operation>:<scope>:[0-9a-f]{64}`; verify manifest hashes.

### P1D-C02 — Required order-intent transitions

- **Conflicting artifacts/statements:** `TRADE_LIFECYCLE.md` required
  `CREATED → VALIDATED → DISPATCH_PENDING → DISPATCHED`, and `EVENT_MODEL.md`
  listed corresponding event families, while the Phase 1C fixture emitted only
  `order_intent.created.v1` then `order_intent.dispatched.v1` for each intent.
- **Evidence:** At `98731e7`, entry aggregate versions were 1–2 in
  `evt_wdc_005`/`evt_wdc_006`, and exit versions were 1–2 in
  `evt_wdc_011`/`evt_wdc_012`; no validation or dispatch-request event existed.
- **Resolution:** Each intent now has four contiguous events: `created`,
  `validated`, `dispatch_requested`, and `dispatched`. Causation, aggregate
  versions, global fixture event ids, report high-water mark, and generated
  time were updated consistently.
- **Rationale:** Immediate local handling does not justify eliding required
  auditable states.
- **Files changed:** `docs/TRADE_LIFECYCLE.md`, `docs/EVENT_MODEL.md`,
  `tests/fixtures/wdc-reference/expected-events.jsonl`,
  `tests/fixtures/wdc-reference/expected-report.json`,
  `tests/fixtures/wdc-reference/scenario.json`,
  `tests/fixtures/wdc-reference/README.md`, and
  `tests/fixtures/wdc-reference/manifest.json`.
- **Affected validation:** Require the exact four-event sequence and aggregate
  versions 1–4 for both intents; verify causation, 19 unique event ids,
  contiguous aggregate versions, and `evt_wdc_018` report high-water mark.

### P1D-C03 — Report metadata and digest semantics

- **Conflicting artifacts/statements:** `REPORTING.md` required schema version,
  supplied-clock generation time, source high-water mark, canonical content
  digest, producer version, mode banner, data cutoff, and reconciliation
  result. Phase 1C `expected-report.json` omitted generation time, content
  digest, producer version, mode banner, and data cutoff, and used ambiguous
  `reconciliation`; the contract did not define how a digest field avoids
  hashing itself.
- **Evidence:** At `98731e7`, the report contained only the partial metadata
  set and its integrity was represented solely by the outer fixture manifest.
- **Resolution:** Report schema v2 includes every required metadata field and
  `reconciliation_result`. The content digest is lowercase SHA-256 over
  canonical UTF-8 JSON with only the top-level `content_digest` member omitted.
  The report event carries the same digest.
- **Rationale:** Explicit non-recursive digest semantics make the report
  independently reproducible instead of circular or manifest-dependent.
- **Files changed:** `docs/REPORTING.md`, `docs/DATA_MODEL.md`,
  `tests/fixtures/wdc-reference/expected-report.json`,
  `tests/fixtures/wdc-reference/expected-events.jsonl`,
  `tests/fixtures/wdc-reference/README.md`, and
  `tests/fixtures/wdc-reference/manifest.json`.
- **Affected validation:** Require all metadata fields; remove only
  `content_digest`, canonicalize, hash, and compare; tie digest/high-water mark
  to `report.generated.v1`; verify manifest hashes.

### P1D-C04 — Trade grouping versus deferred account identity

- **Conflicting artifacts/statements:** `TRADE_LIFECYCLE.md` grouped a trade by
  strategy, symbol, and account scope, while `DATA_MODEL.md` explicitly
  excluded brokerage account identifiers and deferred an account-scope model.
- **Evidence:** Phase 1C defined no account-scope identity, authorization,
  sensitivity, retention, or broker mapping contract, so the required grouping
  key could not be instantiated without inventing forbidden semantics.
- **Resolution:** The offline baseline uses opaque `trade_scope_id` for the
  immutable `(run_id, strategy_version, instrument_id)` tuple. It contains no
  account identity. The fixture declares and carries this scope in trade events
  and the report. Account-scoped grouping remains deferred to a future
  connectivity phase.
- **Rationale:** Offline deterministic trade grouping needs a stable partition
  without importing an unauthorized broker/account concept.
- **Files changed:** `docs/TRADE_LIFECYCLE.md`, `docs/DATA_MODEL.md`,
  `tests/fixtures/wdc-reference/scenario.json`,
  `tests/fixtures/wdc-reference/expected-events.jsonl`,
  `tests/fixtures/wdc-reference/expected-report.json`,
  `tests/fixtures/wdc-reference/README.md`, and
  `tests/fixtures/wdc-reference/manifest.json`.
- **Affected validation:** Require one declared non-account trade scope tied to
  run/strategy/instrument, identical scope in open/close/report records, and no
  brokerage account identifier in the fixture.

## Governance and safety propagation

The acceptance model, `DRY_RUN` boundary, non-overridable rule, and future
multi-condition promotions are propagated through canonical rules, authority,
current state, decision register, ADR-0001, architecture, safety boundary,
promotion gate, role instructions, research/configuration guidance, and the
fixture contracts. Historical journal, failure-model, broker-research, and
Phase 1C records retain their point-in-time wording; this correction document
and current state control the active interpretation.

## Non-consequences

These corrections do not mark `PHASE1_ACCEPTED`, accept ADR-0001, implement
foundation code, obtain or use credentials, connect to TradeStation `SIM`,
submit an order, begin Phase 1E or Phase 2, or authorize `LIVE`.
