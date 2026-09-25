# Monitoring and Alerting Contract

## Signals

Every run emits structured logs, bounded-cardinality metrics, traces across
stage boundaries, domain events, reconciliation cases, and a final run report.
The event ledger is the audit source; logs are diagnostic and cannot establish
trade state.

Required log fields are timestamp, severity, component/version, environment,
mode, run id, correlation/causation ids, operation, outcome, duration, error
class, and safe reason code. Credentials, tokens, raw broker payloads, account
identifiers, personal data, and unconstrained free-form order fields are
prohibited.

## Health model

- **Liveness:** process can make progress; it does not imply safe dispatch.
- **Readiness:** configuration validated, mode is authorized, ledger and
  required dependencies are reachable, replay is complete, and no blocking
  reconciliation case exists.
- **Run health:** `HEALTHY`, `DEGRADED`, `BLOCKED`, or `UNKNOWN`. `UNKNOWN`
  behaves as `BLOCKED` for effects.

Readiness must be false during startup reconciliation, event lag beyond an
approved bound, clock uncertainty, authorization uncertainty, or integrity
failure.

## Alert classes

Immediate human attention is required for attempted `LIVE`, authorization
denial, unexplained order/fill, position drift, idempotency conflict, ledger
integrity failure, invalid state transition, or lost audit/report evidence.
Operational alerts cover dependency failure, retry exhaustion, stale data,
event lag, reconciliation backlog, report withholding, and resource
exhaustion.

Routing targets, paging hours, owners, response objectives, and escalation
paths are unresolved operator choices. Until assigned, alerts cannot be
considered operationally ready.

## Alert quality

Each alert has a stable code, severity, summary, impact, run/correlation ids,
first/last occurrence, count, evidence link, safe diagnostic context, and
runbook reference. Deduplicate by code and affected scope. Recovery resolves
the alert only after the underlying invariant is rechecked. Silence and
acknowledgement do not authorize dispatch.

## Synthetic checks

Only offline fixture-based checks are authorized: replay the WDC reference
fixture, verify `LIVE` denial, induce duplicate delivery, and induce a
reconciliation mismatch. Checks must not use brokerage credentials, accounts,
or network order endpoints.

## Audit and retention

Authorization denials, intent creation, dispatch attempts, execution
observations, reconciliation case changes, report publication, and operator
actions are auditable. Retention length, log platform, immutable archive,
access controls, and incident-management integration remain undecided.
