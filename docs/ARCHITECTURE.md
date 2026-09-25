# Architecture Contract

- Status: Phase 1B design contract; implementation not authorized
- Execution authorization: local non-network `DRY_RUN` only; TradeStation
  `SIM` and `LIVE` unauthorized
- Broker facts: limited to accepted evidence; unresolved behavior cannot be
  inferred from the existence of research

## Purpose and invariants

This document defines logical boundaries for a deterministic, auditable
swing-trading foundation. It is not production code, a broker integration, or
evidence that any strategy works.

The foundation must:

1. fail closed when mode, authorization, data quality, or state is unknown;
2. separate pure decisions from external effects;
3. preserve immutable facts and derive replaceable projections;
4. make every effect idempotent and attributable to one decision;
5. use UTC instants, explicit market-session dates, decimal quantities, and a
   supplied clock;
6. permit deterministic replay from versioned inputs, configuration, and
   events; and
7. prevent a configuration change from granting `LIVE` authority.

## Logical components

| Component | Responsibility | Must not |
| --- | --- | --- |
| Run controller | Create a run, pin versions, sequence stages, and stop safely | Hide retries or select `LIVE` |
| Market-data port | Return normalized bars plus provenance and quality results | Invent, forward-fill, or silently revise observations |
| Decision engine | Apply a versioned strategy contract to immutable inputs | Read wall-clock time or call a broker |
| Risk gate | Return explicit allow/block decisions and evidence | Route orders or default unknown checks to allow |
| Intent ledger | Persist immutable order intent before dispatch | Treat intent as broker acknowledgement |
| Execution port | In `DRY_RUN`, model local effects behind a broker-neutral contract | Claim broker connectivity or TradeStation semantics |
| Event ledger | Append canonical domain events with uniqueness constraints | Mutate or delete accepted events |
| Projectors | Build orders, positions, trades, and reports from events | Become the source of truth |
| Reconciler | Compare internal and external snapshots and quarantine drift | Auto-correct ambiguous discrepancies |
| Observability | Emit structured logs, metrics, alerts, and run reports | Contain secrets or account identifiers |

The architecture is ports-and-adapters: domain contracts have no dependency on
TradeStation or any transport. A future broker adapter may be designed only
after every affected behavior has sufficient evidence and human acceptance.
The current public-document research leaves twelve production-critical groups
unresolved. The external-execution port therefore remains an unresolved
boundary and only the deterministic, non-network DRY_RUN adapter is eligible.

## Control flow

1. Create a `Run` with `mode=DRY_RUN`, an as-of cutoff, supplied clock, input
   manifest, configuration digest, and component versions.
2. Ingest and validate data; any unresolved critical defect stops the run.
3. Produce decisions and risk results as immutable events.
4. Persist an order intent and outbox record atomically.
5. Dispatch only to the local DRY_RUN adapter, using the intent idempotency key.
6. Append execution observations; project order, position, and trade state.
7. Reconcile source events, projections, DRY_RUN state, and generated report.
8. Finalize the report only when required reconciliation checks pass.

## Storage and consistency boundaries

The required logical stores are an append-only event ledger, immutable input
artifacts, a transactional intent/outbox boundary, and rebuildable
projections. One database may implement several logical stores later, but no
technology is selected. Appending an intent event and making it dispatchable
must be one atomic unit. External observations cannot share that transaction;
reconciliation closes that uncertainty.

## Determinism contract

A replay is deterministic when the input bytes, schemas, configuration,
component versions, calendar version, clock seed, and run seed are identical.
Canonical serialization and rounding rules are defined in
[DATA_MODEL.md](DATA_MODEL.md) and [EVENT_MODEL.md](EVENT_MODEL.md). Network
responses, machine time, random global state, unordered iteration, and
locale-dependent parsing are prohibited inputs.

## Failure model

Errors are typed as validation, authorization, dependency, conflict,
reconciliation, or internal errors. Critical validation, authorization, and
unresolved reconciliation errors stop the affected run and leave durable
evidence. Retriable dependency errors may retry within a declared budget using
the same idempotency key. Exhaustion transitions to operator review, never to
an assumed success.

## Contract map

- Lifecycle: [TRADE_LIFECYCLE.md](TRADE_LIFECYCLE.md)
- Entities and values: [DATA_MODEL.md](DATA_MODEL.md)
- Events: [EVENT_MODEL.md](EVENT_MODEL.md)
- Duplicate suppression: [IDEMPOTENCY.md](IDEMPOTENCY.md)
- Drift handling: [RECONCILIATION.md](RECONCILIATION.md)
- Operations: [MONITORING.md](MONITORING.md), [METRICS.md](METRICS.md)
- Safety boundary: [SIM_LIVE_BOUNDARY.md](SIM_LIVE_BOUNDARY.md)
- Gates: [SIM_CERTIFICATION.md](SIM_CERTIFICATION.md),
  [LIVE_PROMOTION.md](LIVE_PROMOTION.md)

## Explicitly unresolved

TradeStation public documentation establishes selected environment, endpoint,
schema, acknowledgement, read-limit, and rate-limit facts in
[BROKER_CONTRACT.md](BROKER_CONTRACT.md). Key-specific authentication and
entitlements, idempotency and timeout recovery, complete status transitions,
stream recovery, group atomicity, precision/time semantics, fill/correction
behavior, simulator parity, retention, and availability remain unresolved.
Technology stack, deployment topology, market-data source, exchange calendar,
strategy, risk limits, retention, recovery objectives, and human ownership
also remain open.
