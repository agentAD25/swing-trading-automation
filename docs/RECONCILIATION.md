# Reconciliation Contract

## Objective

Reconciliation detects disagreement; it does not manufacture agreement. The
corrected offline baseline checks deterministic fixtures and local non-network
DRY_RUN state only. Broker reconciliation fields and timing remain unresolved.
TradeStation SIM reconciliation remains a future connectivity contract.

## Check layers

1. **Ledger integrity:** event sequence, schema, digests, causation, and
   aggregate versions.
2. **Projection:** rebuild and compare orders, positions, trades, and report
   high-water marks.
3. **Execution:** compare intents and expected DRY_RUN observations with local
   orders, fills, quantities, and states.
4. **Cash and valuation:** proposed only; blocked until currency, fee,
   settlement, and valuation contracts are selected.
5. **Report:** totals and rows tie to reconciled projections and the same event
   high-water mark.

## Comparison identity

Match by durable source identity first, then declared client identity. Never
match solely by symbol, quantity, price, or nearby timestamp. If identity is
missing or non-unique, open a discrepancy rather than guessing.

## Case model

A discrepancy records check type, scope, severity, expected value, observed
value, difference, source digests, first/last seen, owner, and status:
`OPEN`, `ACKNOWLEDGED`, `RESOLVED`, or `WAIVED`. Waiver requires a named human,
rationale, expiry, and evidence; critical safety discrepancies cannot be
automatically waived.

Severity:

- `CRITICAL`: unknown authorization, unexplained order/fill, position
  disagreement, duplicate effect, integrity failure;
- `HIGH`: stale/missing execution observation or report mismatch;
- `MEDIUM`: non-position data-quality or timing breach;
- `LOW`: informational metadata drift.

## Fail-closed actions

Critical and high discrepancies stop dependent dispatch and withhold final
reports. Unknown state is a discrepancy. Automated repair is limited to
rebuilding a projection from the immutable ledger. The system must not create,
cancel, or offset an order to repair drift. Resolution appends evidence and
reruns the check; it never deletes the original case.

## Cadence and recovery points

Checks run at startup, before dispatch, after every execution observation,
before a trade is considered closed, at run finalization, and after replay.
Future broker cadence, settlement timing, outage tolerance, and operator
service levels require research and approval.

Recovery captures the source high-water marks and obtains a stable snapshot.
If a source cannot provide snapshot consistency, page/cursor semantics and
overlap strategy must be proven before certification.

## Required tests

Cover exact match, duplicate and missing fill, late correction, excess fill,
unexpected negative/reversed position, stale observation, projection
corruption repaired by rebuild, ambiguous identity, and report high-water-mark
mismatch. Each scenario asserts discrepancy severity, quarantine behavior,
dispatch inhibition, evidence, and deterministic rerun.
