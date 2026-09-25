# Data Model Contract

## Representation rules

- Identifiers are opaque, immutable strings with a type prefix; consumers must
  not parse meaning from them.
- Monetary values, prices, and quantities use base-10 decimals serialized as
  canonical strings. Binary floating point is prohibited at persistence and
  contract boundaries.
- Currency is an explicit ISO 4217 code; no default currency is implied.
- Instants are RFC 3339 UTC strings with `Z` and microsecond precision.
- A market-session date is a separate `YYYY-MM-DD` value interpreted using a
  named, versioned calendar.
- Enumerations are uppercase closed sets. An unknown external value is retained
  raw and mapped to `UNKNOWN`; it is never coerced.
- Canonical JSON uses UTF-8, lexicographically sorted keys, no insignificant
  whitespace, and decimal values as strings. Digests are lowercase SHA-256.
- Domain rounding requires an explicitly versioned rule. No default tick size,
  lot size, or currency scale is assumed.

## Core records

| Record | Required identity and content |
| --- | --- |
| `Run` | `run_id`, mode, status, as-of cutoff, supplied clock, seed, config/input/calendar/component digests |
| `Instrument` | `instrument_id`, symbol, asset class, currency, source namespace, validity interval |
| `Bar` | instrument, interval, session date, open/high/low/close, volume, source, observed-at, revision |
| `Decision` | decision id, run, strategy version, inputs digest, action, reason codes |
| `RiskResult` | risk-result id, decision, rule-set version, `ALLOW`/`BLOCK`, rule outcomes |
| `OrderIntent` | intent id, run, decision, instrument, side, quantity, order terms, mode, idempotency key |
| `OrderObservation` | observation id, source, source order id if any, mapped state, raw status, cumulative quantities, source/effective/recorded times |
| `Fill` | fill id, order, instrument, side, quantity, price, currency, fee components, effective and recorded times |
| `PositionSnapshot` | scope, instrument, signed quantity, cost basis method/version, as-of event sequence |
| `TradeProjection` | trade id, lifecycle state, entry/exit intent ids, quantity, realized values, opening/closing event sequences |
| `ReconciliationCase` | case id, run/scope, check type, severity, expected/observed values, status, owner, evidence |
| `ReportArtifact` | report id, run, schema version, source high-water mark, content digest, reconciliation status |

## Keys and constraints

- Every event has a globally unique `event_id`; every aggregate event has a
  unique `(aggregate_type, aggregate_id, aggregate_version)`.
- Bars are unique by `(source, instrument_id, interval, session_date,
  revision)`. Revisions append; they do not overwrite.
- Fill identity is source-specific. Before source semantics are validated, the
  system cannot assume source fill ids are globally unique.
- One intent has one stable idempotency key. Retries reuse it.
- A report is unique by `(run_id, report_type, schema_version,
  source_high_water_mark)`.
- Requested and cumulative fill quantities must be nonnegative. Side supplies
  direction. A fill cannot silently exceed requested quantity; it opens a
  reconciliation case.
- OHLC validation requires `low <= open,close <= high` and nonnegative volume.
  These checks establish structural validity, not market truth.

## Provenance

Every imported or generated artifact records source identifier, retrieval or
generation time, schema version, byte digest, parent digests, and producer
version. Input manifests are immutable after a run starts. Corrections create a
new manifest and run.

## Sensitive data

The Phase 1B model contains no credentials, secrets, personal data, brokerage
account identifiers, or live-capital fields. A future account-scope model
requires separate security, retention, and authorization decisions.

## Open model choices

Order-term vocabulary, tick/lot rules, corporate-action treatment, adjusted
versus unadjusted data, fee and tax semantics, cost-basis method, calendar,
retention, and broker identifier behavior remain unresolved.
