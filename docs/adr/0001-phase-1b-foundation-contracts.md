# ADR-0001: Phase 1B foundation contracts

- Status: Proposed
- Date: 2026-09-25
- Deciders: Unassigned human owner(s)
- Scope: Foundation architecture and safety
- Supersedes: None
- Superseded by: None

## Context

The repository needs a deterministic, auditable design before implementation.
Broker, strategy, data, risk, operational, legal, and technology choices are
not yet validated. Current authority permits `SIM` only and prohibits `LIVE`.

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
a SIM-only port. This adds modeling and operational complexity but exposes
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

## Validation and rollback

Validate links, terminology, state transitions, fixture digests/canonical
bytes, cross-document safety language, and unresolved broker claims. Rollback
is removal or supersession of these design-only artifacts; no runtime or
account state exists.

## Unresolved questions

Named deciders; Phase 1B acceptance criteria; technology stack; broker facts;
strategy/data/risk contracts; operator thresholds and owners; security,
licensing, legal, and compliance requirements.

## Evidence

- Repository reference: `docs/AGENT_AUTHORITY.md`, accessed 2026-09-25.
  Supports least authority, accepted-ADR requirement, and `SIM`-only boundary.
- Repository reference: `docs/CURRENT_STATE.md`, accessed 2026-09-25. Supports
  that architecture, broker facts, and implementation were not established by
  Phase 1A.
- Repository reference: `docs/ENGINEERING_JOURNAL.md`, accessed 2026-09-25.
  Supports the Phase 1A baseline and unresolved decisions. These repository
  sources do not establish external broker behavior.
