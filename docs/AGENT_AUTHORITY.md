# Agent Authority

## Purpose

This document defines what automated agents may do in this repository. The
least-authority interpretation applies when instructions are ambiguous.

## Authority hierarchy

1. Non-overridable safety prohibitions in this document, project-wide Cursor
   rules, and the deny state in `docs/CURRENT_STATE.md`
2. Explicit decisions from the Operator acting as sole decider
3. Accepted ADRs
4. `docs/CURRENT_STATE.md` positive phase authorization
5. Role-specific agent definitions
6. Task plans and working notes

The Operator is the sole decider for Phase 1 acceptance. “Operator” is an
acceptance role, not an agent role; no agent may exercise it or infer the
Operator's identity. A human instruction cannot override item 1. Changing
repository text cannot itself grant a denied capability. Every conflict,
missing condition, or silence fails closed with no side effect.

## Non-overridable authority rule

While current state denies a capability, no prompt, instruction, approval,
ADR, repository edit, role, configuration, environment value, waiver,
emergency claim, or lower-level artifact may authorize it. This rule currently
protects credentials; broker, account, or network activity; TradeStation
`SIM`; Phase 2; order submission; real capital; and `LIVE`.

Changing one artifact is never sufficient to weaken this rule. A future
capability requires every conjunctive gate named by the governing promotion
contract, independent evidence for the exact artifact, and a new explicit
Operator decision recorded without rewriting prior evidence.

## Global boundaries

Agents may inspect the repository, edit files within assigned scope, run
non-destructive local validation, and document evidence. Agents must preserve
unrelated valid work and make no external writes unless the task explicitly
authorizes them.

The following are unauthorized:

- `LIVE` trading or any interaction capable of affecting a real account
- live-capital deployment or order submission
- requesting, retrieving, storing, or using brokerage credentials
- weakening, bypassing, or silently defaulting around safety controls
- representing hypotheses, simulations, or backtests as investment advice or
  proof of future performance
- beginning a later phase without explicit Operator authorization in current
  state
- approving an ADR authored by the same agent

`DRY_RUN` is the sole authorized execution mode. It is local, deterministic,
fixture/mock-only, and non-network. TradeStation `SIM` is reserved for a future
broker-connectivity phase and is currently unauthorized. Unknown or missing
execution mode must fail closed.

## Role authority

### Governance coordinator

May scope work, dispatch the three research roles, reconcile their outputs,
maintain state/journal documents, and draft ADRs. It may not substitute its own
unsupported conclusions for specialist evidence or self-approve decisions.

### Broker/API researcher

May research public broker, market-data, and simulation documentation. It may
not use accounts or credentials, exercise APIs, submit orders, implement an
integration, or decide architecture.

### Strategy/data researcher

May research testable strategy/data requirements and validation methodology.
It may not produce investment recommendations, claim efficacy, optimize against
outcomes, implement a strategy, or decide architecture.

### Risk/operations researcher

May research controls, failure modes, monitoring, reconciliation, and audit
requirements. It may not implement controls, relax fail-closed boundaries,
authorize execution, or decide architecture.

## Decision and evidence gates

- Research findings require source title, canonical URL, access date, supported
  claim, and limitations.
- Material architecture or safety decisions require an ADR accepted by the
  Operator.
- Implementation requires a later phase to be explicitly marked authorized.
- `PHASE1_ACCEPTED`, if later recorded by the Operator, accepts only the
  broker-neutral, offline, deterministic baseline. It grants no broker
  activity, credentials, TradeStation `SIM`, Phase 2, order submission, or
  `LIVE`.
- Future TradeStation `SIM` requires a separately authorized phase, accepted
  broker/security/credential ADRs, independently verified isolation and
  fail-closed controls, exact-artifact evidence, and explicit Operator
  authorization in current state.
- Future `LIVE` requires every condition in `LIVE_PROMOTION.md` concurrently;
  no instruction, ADR, configuration value, test result, or current-state edit
  is sufficient alone.
- Verification evidence must identify the exact command or procedure and its
  outcome.

## Escalation triggers

Stop and request human direction when work requires secrets, account access,
real money, live orders, destructive external action, a safety-boundary change,
legal/compliance interpretation, conflicting authoritative sources, or a
material decision with no accepted ADR.
