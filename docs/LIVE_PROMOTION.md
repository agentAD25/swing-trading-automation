# LIVE Promotion Gate

## Current decision

Promotion to `LIVE` is unauthorized and out of scope. There is no promotion
date, procedure, credential plan, live adapter, or approved broker behavior.
This document lists conjunctive prerequisites so future TradeStation `SIM`
work cannot accidentally be treated as live readiness.

No instruction, approval, ADR, repository edit, current-state edit,
configuration, waiver, emergency claim, or test result can authorize `LIVE`
alone. Every condition below must be satisfied concurrently, and ambiguity
denies promotion.

## Hard prerequisites

All of the following require affirmative evidence:

- separately authorized and current TradeStation SIM certification plus
  independent safety review;
- completed first-party TradeStation capability evidence, with every
  production-facing unresolved behavior closed, including
  authentication, environments, account/order/fill semantics, identifiers,
  idempotency, reconciliation, rate limits, outages, and corrections;
- accepted ADRs for broker adapter, authorization, secrets, network isolation,
  deployment, data retention, recovery, observability, and rollback;
- legal, regulatory, tax, market-data licensing, and organizational approvals;
- named system, risk, security, compliance, operations, and capital owners;
- approved strategy, universe, risk/capital limits, kill criteria, operating
  hours, incident response, and change-management policy;
- live-specific tests in a legally authorized non-capital environment where
  available, without assuming simulator parity;
- separate live artifact and infrastructure with deny-by-default policy;
- staged exposure plan and independent reconciliation proven before any
  increase.
- a frozen exact artifact/evidence digest and successful final preflight; and
- an explicit, bounded, expiring `LIVE` decision by the human Operator acting
  as sole promotion decider, recorded only after every other condition is
  independently attested.

If any prerequisite is unknown, stale, or waived without authority, promotion
is denied.

## Required controls before consideration

Independent pre-trade limits, aggregate exposure limits, duplicate prevention,
stale-data guards, market-session controls, kill switch, cancel/replace policy,
position and cash reconciliation, immutable audit, alerting with staffed
response, backup/restore, disaster recovery, and rollback must be implemented
and exercised. Exact limits and procedures are unresolved and must not be
invented by an agent.

## Decision procedure

1. Freeze a candidate artifact and evidence bundle.
2. Obtain independent technical, risk, security, compliance, and operations
   attestations from named humans. These are required evidence, not additional
   acceptance deciders.
3. The Operator accepts dedicated ADRs and explicitly authorizes a new phase in
   `docs/CURRENT_STATE.md`.
4. Conduct a preflight proving identities, environment, account scope,
   network policy, limits, monitoring, reconciliation, and abort path.
5. Require the Operator's final explicit authorization for the bounded,
   expiring launch after all attestations and controls remain current.

No flag, environment variable, configuration edit, ADR alone, current-state
edit alone, successful SIM run, or favorable performance report can perform
these steps.

## Automatic stop and rollback

Any unknown mode, authorization failure, unexplained order/fill, position/cash
drift, stale data, telemetry loss, limit breach, integrity failure, or
unavailable kill/reconciliation control blocks or stops activity. Rollback
must prevent new orders while preserving evidence; whether cancellation is
safe depends on researched broker semantics and cannot be prescribed yet.

## Phase status

This gate does not start Phase 2. Phase 2 and `LIVE` remain unstarted and
unauthorized.
