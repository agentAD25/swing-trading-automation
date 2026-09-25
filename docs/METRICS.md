# Metrics Contract

## Rules

Metrics use base units, documented histograms, and bounded labels. Permitted
labels include component, version, environment, mode, stage, outcome, reason
code, and severity. Symbol, order id, trade id, run id, account, exception
text, URL, and raw status are prohibited labels; those belong in logs or
reports.

## Required operational metrics

| Name | Type | Meaning |
| --- | --- | --- |
| `run_total` | counter | runs by terminal outcome |
| `run_duration_seconds` | histogram | end-to-end run duration |
| `stage_duration_seconds` | histogram | stage latency |
| `data_quality_failure_total` | counter | rejected inputs by reason |
| `decision_total` | counter | domain decisions by action/reason |
| `risk_result_total` | counter | allow/block results |
| `order_intent_total` | counter | intents by lifecycle outcome |
| `dispatch_attempt_total` | counter | DRY_RUN attempts by outcome |
| `idempotency_dedup_total` | counter | safely suppressed duplicates |
| `idempotency_conflict_total` | counter | key/input conflicts |
| `event_consumer_lag_events` | gauge | ledger-to-projector sequence lag |
| `event_consumer_lag_seconds` | gauge | age of oldest unprocessed event |
| `reconciliation_case_total` | counter | opened cases by check/severity |
| `reconciliation_open` | gauge | unresolved cases by check/severity |
| `reconciliation_age_seconds` | gauge | oldest unresolved case |
| `position_unknown` | gauge | unknown position scopes |
| `report_total` | counter | generated/withheld/published reports |
| `authorization_denied_total` | counter | denied effects by reason/mode |

Metric definitions are contract versioned. Counters never decrease within a
process; gauges expose collection time. Missing telemetry is itself monitored.

## Safety indicators

The following conditions are release or run blockers, not performance targets:

- any attempted or observed `LIVE` operation;
- any unexplained order, fill, negative/reversed position, duplicate effect,
  idempotency conflict, or ledger integrity failure;
- any critical reconciliation case;
- any report published from an unreconciled high-water mark.

Thresholds for freshness, latency, availability, retry rate, and backlog are
not selected. Owners must set them from measured DRY_RUN baselines and operational
needs before certification; this document does not invent values.

## Strategy analytics boundary

Return, drawdown, turnover, exposure, hit rate, and similar analytics may be
reported for deterministic offline runs, clearly labeled `DRY_RUN` and
non-predictive. They are never service-health metrics and cannot authorize
`LIVE`, establish efficacy, or be optimized without an approved research
protocol. Calculation formulas, benchmark, corporate-action treatment, costs,
and statistical acceptance criteria remain unresolved.

## Validation

Contract tests verify name, type, unit, allowed labels, and bounded
cardinality. Scenario tests assert expected counter deltas and blocker gauges.
Dashboards must display mode and data cutoff prominently and link to source run
and reconciliation status without putting their ids in metric labels.
