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
  `SIM`, synthetic/backtest as applicable, with assumptions and limitations.

## Publication rules

Reports are projections, not sources of truth. Every report has a schema
version, generation time from the supplied clock, source high-water mark,
canonical content digest, producer version, mode banner, data cutoff, and
reconciliation result. Generation is idempotent.

A final report is withheld when inputs are unverified, a required projection
lags its high-water mark, a critical/high discrepancy is open, state is
unknown, or mode authorization is invalid. Preliminary output must be marked
`UNRECONCILED — DO NOT USE FOR EXECUTION`.

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

## Access and retention

Report audience, storage, retention, signing, immutable archive, deletion,
redaction, and regulatory requirements are unresolved operator choices.
