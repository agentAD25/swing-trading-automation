# Event Model Contract

## Canonical envelope

Every domain event contains:

| Field | Contract |
| --- | --- |
| `event_id` | globally unique opaque id |
| `event_type` | versioned name such as `order_intent.created.v1` |
| `schema_version` | positive integer |
| `aggregate_type`, `aggregate_id`, `aggregate_version` | ordered aggregate stream |
| `run_id` | originating run |
| `correlation_id` | end-to-end operation |
| `causation_id` | direct predecessor event or command |
| `idempotency_key` | stable key for duplicate suppression, when applicable |
| `effective_at` | when the source says the fact occurred |
| `recorded_at` | supplied-clock time accepted by this system |
| `producer`, `producer_version` | attributable component |
| `payload` | schema-validated domain content |
| `source` | provenance and raw-observation digest, when external |

Field names, canonical serialization, decimals, and times follow
[DATA_MODEL.md](DATA_MODEL.md). Trace ids are diagnostic and cannot replace
domain correlation or causation ids.

## Event families

- Run: created, validation failed, stage completed, stopped, finalized.
- Data: manifest accepted, quality failed, revision detected.
- Decision/risk: decision produced, risk allowed, risk blocked.
- Intent/order: intent created, validated, blocked, dispatch requested,
  dispatched, observation recorded, mapping unresolved.
- Execution: fill recorded, fill corrected, fee recorded.
- Position/trade: position changed, trade opened, exit requested, trade closed,
  operator review required.
- Reconciliation: check completed, discrepancy opened, acknowledged, resolved.
- Reporting: report requested, generated, withheld, published.
- Authorization: authorization denied. No Phase 1 event can grant TradeStation
  `SIM` or `LIVE`.

The required order-intent path emits one event for each state transition:
`order_intent.created.v1`, `order_intent.validated.v1`,
`order_intent.dispatch_requested.v1`, and
`order_intent.dispatched.v1`. Immediate DRY_RUN processing does not permit
elision of an intermediate event.

Each of those events requires payload fields `prior_state`, `next_state`,
`reason_code`, and `initiating_event_id`. The envelope's `aggregate_id`,
`aggregate_version`, `event_id`, `effective_at`, `recorded_at`,
`causation_id`, and `correlation_id` supply durable identity, ordering,
timestamps, immediate cause, and end-to-end correlation. Absence of any
required transition payload or envelope field is a schema error, not an
optional projection detail.

`reconciliation.check_completed.v1` is the sole source event that can support a
report reconciliation result of `PASS`. Its payload requirements are defined
in `RECONCILIATION.md`. A report projection, flat position, absent discrepancy,
or report field cannot substitute for this source event.

## Append and delivery semantics

The ledger is append-only. Producers append with optimistic aggregate version
checks. Consumers are at-least-once and must checkpoint only after their
transactional projection update succeeds. Ordering is guaranteed only within
an aggregate stream; cross-aggregate behavior uses causation and explicit
process state rather than timestamp order.

Duplicate `event_id` with identical canonical bytes is a no-op. Reuse with
different bytes is a critical conflict. Schema-invalid or unmappable external
observations are retained in a quarantine store with digest and metadata, then
emit no trusted domain fact until resolved.

## Evolution

Event schemas are immutable after use. Additive compatible changes require a
new schema version declaration; semantic or breaking changes require a new
event type version and deterministic upcaster where possible. Replay tests
must cover all retained versions. Raw broker fields are not allowed to leak
into the domain envelope as undocumented semantics.

## Replay and temporal rules

Projectors consume ledger sequence, not wall-clock order. `recorded_at` must be
greater than or equal to the prior event's recorded time within a run, using
the supplied clock. An effective time may be earlier because observations can
arrive late. Replay never emits external effects; an explicit replay flag is
part of the execution context and the execution port rejects dispatch during
replay.

## Integrity

Each immutable artifact records its digest; an event batch may additionally
record previous-batch and current-batch digests for tamper evidence. Whether a
regulated immutable store or digital signatures are needed is unresolved and
requires legal/security input.
