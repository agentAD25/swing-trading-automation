# Phase 1B Decision Register

## Status vocabulary

`CONTRACT` means this Phase 1B design set uses the decision for internal
consistency. Material decisions remain **Proposed** until an identified human
accepts the corresponding ADR. `UNRESOLVED` means no selection may be inferred.
Phase 1C assigns the overall state `PROPOSED / FREEZE_BLOCKED`; no decision in
this register is `PHASE1_ACCEPTED`.

## Design contracts

| ID | Status | Decision | Rationale |
| --- | --- | --- | --- |
| D-001 | CONTRACT / Proposed ADR | Ports-and-adapters domain with a SIM-only execution port | Isolates broker uncertainty and external effects |
| D-002 | CONTRACT / Proposed ADR | Append-only events with rebuildable projections | Auditability and deterministic replay |
| D-003 | CONTRACT / Proposed ADR | Atomic intent/outbox boundary plus stable idempotency keys | Survives at-least-once processing without duplicate logical intent |
| D-004 | CONTRACT / Proposed ADR | Decimal strings, UTC instants, explicit session dates, supplied clock | Removes platform and locale ambiguity |
| D-005 | CONTRACT / Proposed ADR | Ambiguity and unknown state fail closed into reconciliation | Prevents guessed execution state |
| D-006 | CONTRACT / Proposed ADR | Reports bind to immutable inputs and an event high-water mark | Makes results reproducible and auditable |
| D-007 | CONTRACT / Proposed ADR | `SIM` is the only possible authorization; no live-capable adapter | Preserves the current authority boundary |
| D-008 | CONTRACT / Proposed ADR | Deterministic synthetic WDC fixture is conformance data, not research data | Tests contracts without efficacy claims |

The umbrella record is
[ADR-0001](adr/0001-phase-1b-foundation-contracts.md). It intentionally remains
Proposed because human deciders have not been named.

## Dependencies

- Phase 1A governance must be adopted.
- Broker/API research must supply first-party evidence for every affected
  behavior before any adapter contract is asserted. The current public-doc
  handoff leaves twelve production-critical behavior groups unresolved.
- Strategy/data research must define universe, signal, source, calendar,
  revisions, bias controls, and validation protocol.
- Risk/operations research must define approved limits, owners, response
  objectives, recovery objectives, and operating procedures.
- Legal/security review must address licensing, compliance, privacy, retention,
  secrets, and infrastructure.
- Human owners must accept material ADRs and authorize any later phase.

## Unresolved operator choices

Technology stack; persistence and queue products; deployment topology;
environment ownership; calendar; data vendor; strategy; risk and capital
limits; cost/fee model; rounding/tick/lot rules; retention; backup and recovery
objectives; availability/freshness/latency thresholds; alert routes and
staffing; incident/change processes; report recipients; waiver authority; SIM
certification deciders; and all `LIVE` decisions.

## Broker-dependent unknowns

Public documentation establishes separate v3 LIVE and SIM hosts, fake SIM
accounts/money, instant simulated fills, selected endpoint schemas, command
acknowledgement behavior, read limits, and default rate-limit mechanics.
It does not prove runtime isolation or resolve key-specific scopes/quotas,
client idempotency and timeout recovery, the complete order state machine,
fills/corrections, stream recovery, group atomicity, precision/time semantics,
simulator fidelity, retention, outages, or reconciliation facilities. See
[BROKER_CONTRACT.md](BROKER_CONTRACT.md) and
[PHASE_1C_RECONCILIATION.md](PHASE_1C_RECONCILIATION.md).

## Phase 1C disposition

- D-001 through D-008 remain internally coherent proposals.
- ADR-0001 remains Proposed with unassigned human deciders.
- FM-01 through FM-24 remain open safety findings; later design narrows but
  does not close selected findings.
- The exact implementation-freeze blockers and human decisions are maintained
  in `PHASE_1C_RECONCILIATION.md`.
- No repository document, validation result, or `CONTRACT` label grants phase
  authority.

## Prohibited inferences

This design set does not authorize implementation, Phase 2, credentials,
account access, order submission, `LIVE`, or investment decisions. The WDC
fixture is synthetic and does not establish strategy efficacy or market facts.
