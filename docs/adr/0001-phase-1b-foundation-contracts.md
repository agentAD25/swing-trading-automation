# ADR-0001: Phase 1B foundation contracts

- Status: Proposed
- Date: 2026-09-25
- Sole decider: Operator
- Scope: Foundation architecture and safety
- Supersedes: None
- Superseded by: None

## Context

The repository needs a deterministic, auditable design before implementation.
Broker, strategy, data, risk, operational, legal, and technology choices are
not yet validated. Only local, deterministic, non-network `DRY_RUN` is
authorized. TradeStation `SIM`, broker activity, Phase 2, and `LIVE` remain
unauthorized.

## Safety impact

The proposal excludes a live-capable adapter and treats unknown mode, state,
data quality, authorization, and reconciliation as blocking. It requests no
credentials or account access and grants no implementation or phase authority.

## Options considered

### Option A — Mutable workflow records and direct integration

This can appear simpler, but conflates decisions with effects, weakens replay
and audit, and would require inventing broker behavior. Rejected by this
proposal.

### Option B — Event-led, ports-and-adapters design

Persist immutable inputs and events, build replaceable projections, create
intent before effects, require stable idempotency, and isolate execution behind
a local non-network DRY_RUN port. This adds modeling and operational complexity but exposes
ambiguity and supports deterministic evidence.

### Option C — Defer all architecture

Avoids premature selection but leaves no consistent research and future
implementation target. It does not satisfy the Phase 1B bootstrap.

## Decision

Proposed: Option B, with the detailed contracts in `docs/ARCHITECTURE.md`
through `docs/LIVE_PROMOTION.md`, `docs/REPORTING.md`, and
`docs/TEST_PLAN.md`. No decision is accepted until named humans review it.

## Consequences

Broker adapters cannot shape the domain model implicitly. Event schema,
idempotency, reconciliation, and deterministic fixture work become mandatory.
Storage and queue technologies remain selectable later. More design validation
is required before implementation, but unsafe assumptions remain visible.

If the Operator later changes this ADR to Accepted and records
`PHASE1_ACCEPTED`, that acceptance is bounded to the broker-neutral, offline,
deterministic baseline. It grants no implementation, credentials,
broker/network/account activity, TradeStation `SIM`, Phase 2, order submission,
real capital, or `LIVE`.

## Validation and rollback

Validate links, terminology, state transitions, fixture digests/canonical
bytes, cross-document safety language, and unresolved broker claims. Rollback
is removal or supersession of these design-only artifacts; no runtime or
account state exists.

## Unresolved questions

Authenticated Operator identity and durable acceptance mechanism; technology
stack; broker facts; strategy/data/risk contracts; operator thresholds and
owners; security, licensing, legal, and compliance requirements.

## Evidence

- Repository reference: `docs/AGENT_AUTHORITY.md`, accessed 2026-09-25.
  Supports least authority, accepted-ADR requirements, and the execution-mode
  boundary as corrected by Phase 1D.
- Repository reference: `docs/CURRENT_STATE.md`, accessed 2026-09-25. Supports
  that architecture, broker facts, and implementation were not established by
  Phase 1A.
- Repository reference: `docs/ENGINEERING_JOURNAL.md`, accessed 2026-09-25.
  Supports the Phase 1A baseline and unresolved decisions. These repository
  sources do not establish external broker behavior.
- Repository reference: `docs/PHASE_1D_CORRECTIONS.md`, accessed 2026-09-25.
  Records the Operator-directed acceptance model and four resolved
  contract/fixture contradictions. It does not mark this ADR Accepted.
