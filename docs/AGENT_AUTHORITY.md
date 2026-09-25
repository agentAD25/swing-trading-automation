# Agent Authority

## Purpose

This document defines what automated agents may do in this repository. The
least-authority interpretation applies when instructions are ambiguous.

## Authority hierarchy

1. Explicit human instructions and approvals
2. Accepted ADRs
3. This authority document and project-wide Cursor rules
4. `docs/CURRENT_STATE.md` phase authorization
5. Role-specific agent definitions
6. Task plans and working notes

Higher entries prevail. An agent must stop and escalate an irreconcilable
conflict; silence is not authorization.

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
- beginning a later phase without explicit authorization in current state
- approving an ADR authored by the same agent

`SIM` is the sole authorized execution mode. Unknown or missing execution mode
must fail closed.

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
- Material architecture or safety decisions require an accepted ADR.
- Implementation requires a later phase to be explicitly marked authorized.
- Any future movement beyond simulation requires separate human approval and an
  accepted ADR; changing a configuration value is insufficient.
- Verification evidence must identify the exact command or procedure and its
  outcome.

## Escalation triggers

Stop and request human direction when work requires secrets, account access,
real money, live orders, destructive external action, a safety-boundary change,
legal/compliance interpretation, conflicting authoritative sources, or a
material decision with no accepted ADR.
