# Reporting Contract

## Artifact classes

- **Run manifest:** exact source/config/calendar/component versions, mode,
  cutoff, clock/seed, artifact digests, and event high-water mark.
- **Decision report:** inputs, decisions, risk outcomes, intent linkage, and
  reason codes.
- **Execution report:** intent/order/fill/trade lifecycle and reconciliation
  status.
- **Operations report:** data quality, retries, lag, alerts, discrepancies, and
  withheld outputs.
- **Simulation analytics:** optional research measures, visibly labeled
  `DRY_RUN`, synthetic/backtest as applicable, with assumptions and
  limitations.

## Publication rules

Reports are projections, not sources of truth. Every report has a schema
version, generation time from the supplied clock, source high-water mark,
canonical content digest, producer version, mode banner, data cutoff, and
reconciliation result. Generation is idempotent.

The canonical content digest is lowercase SHA-256 over the canonical UTF-8 JSON
object with the top-level `content_digest` member omitted. Verification removes
that one member, serializes by `DATA_MODEL.md`, hashes the bytes, and compares
the result to `content_digest`. This non-recursive rule is mandatory; hashing
the file including its digest field or relying only on the manifest hash is
invalid.

A final report is withheld when inputs are unverified, a required projection
lags its high-water mark, a critical/high discrepancy is open, state is
unknown, or mode authorization is invalid. Preliminary output must be marked
`UNRECONCILED — DO NOT USE FOR EXECUTION`.

`reconciliation_result` is `PASS` only when the report high-water mark is a
qualifying `reconciliation.check_completed.v1` event under
`RECONCILIATION.md`. Without that event the only contract-supported value is
`UNRECONCILED`, the report event is `report.withheld.v1`, and the artifact must
contain the exact preliminary-output warning above. Report generation cannot
manufacture reconciliation evidence.

Reports must not contain credentials, account identifiers, personal data, raw
broker payloads, or claims of profitability/safety. A favorable simulation is
not evidence of future performance.

## Required ties

For a given high-water mark:

- fills tie to projected order cumulative quantities;
- signed fills tie to ending position;
- a closed trade ties to an exactly flat position;
- report rows link to source event ids without relying on timestamps;
- discrepancy counts tie to the reconciliation case projection;
- report digest and status tie to the run manifest.

Cash, fee, tax, corporate-action, valuation, and performance formula ties
remain undefined until their domain contracts are approved.

## WDC reference report

`tests/fixtures/wdc-reference/expected-report.json` is the byte-level reference
for a synthetic conformance run. It validates ordering, decimal
representation, linkage, lifecycle, and report reconciliation. It is not a
backtest, strategy selection, or observation of WDC market prices.

The current WDC source ledger contains no reconciliation-completion event.
Accordingly its reference report is `UNRECONCILED` and withheld. This is a
negative conformance case, not a failed or fabricated reconciliation run.

The reference must contain `report_id`, `report_type`, `run_id`,
`schema_version`, `generated_at`, `producer_version`, `mode`, `mode_banner`,
`data_cutoff`, `source_high_water_mark`, `content_digest`, and
`reconciliation_result`.

## Access and retention

Report audience, storage, retention, signing, immutable archive, deletion,
redaction, and regulatory requirements are unresolved operator choices.
