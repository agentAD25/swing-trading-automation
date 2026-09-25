# Trade Lifecycle Contract

## Scope

These are broker-neutral domain states. They do not describe TradeStation
states or promise that any broker exposes equivalent transitions.

## Aggregate boundaries

- An `OrderIntent` records a requested effect.
- An `Order` records observations about one attempted execution.
- A `Position` is the signed quantity derived from fills.
- A `Trade` groups a flat-to-nonflat-to-flat position episode for one strategy,
  symbol, and account scope.

An order is not a trade, submission is not acceptance, and acceptance is not a
fill. Broker payloads, if later researched, must first be retained as source
observations and then mapped explicitly.

## Order-intent lifecycle

`CREATED` → `VALIDATED` → `DISPATCH_PENDING` → `DISPATCHED`

Terminal alternatives are `BLOCKED`, `CANCELLED_BEFORE_DISPATCH`, and
`OPERATOR_REVIEW`. Only an explicit risk result may produce `VALIDATED`.
Unknown validation produces `BLOCKED`. `DISPATCHED` means the SIM port accepted
the command for processing, not that an order was filled.

## Order-observation lifecycle

The broker-neutral projection may use:

- `PENDING`: intent dispatched, no conclusive observation;
- `WORKING`: observed as eligible for execution;
- `PARTIALLY_FILLED`: cumulative filled quantity is between zero and requested;
- `FILLED`: cumulative filled quantity equals requested;
- `CANCELLED`, `REJECTED`, or `EXPIRED`: terminal without further expected
  fills under the source contract;
- `UNKNOWN`: observations are missing, contradictory, or cannot be mapped.

Transitions are driven by facts, not local expectations. Late fills or
corrections append events and may supersede a projection; history is never
rewritten. `UNKNOWN` quarantines further dependent action until reconciled.
Whether a future broker permits transitions after an apparent terminal status
is unresolved and must be researched.

## Position and trade lifecycle

The position is the sum of signed fill quantities. Its state is:

- `FLAT`: quantity is zero;
- `LONG`: quantity is positive;
- `SHORT`: quantity is negative;
- `UNKNOWN`: fill history is incomplete or contradictory.

Phase 1B does not authorize short selling. The state exists to detect and
quarantine an unexpected negative position, not to request one.

A trade projection uses:

`PLANNED` → `ENTRY_PENDING` → `OPEN` → `EXIT_PENDING` → `CLOSED`

Alternatives are `ABANDONED` before the first fill and `OPERATOR_REVIEW` from
any nonterminal state. The first entry fill opens the trade. `CLOSED` requires
the position to return exactly to zero and reconciliation to find no unresolved
fill discrepancy. Partial fills alter quantity but do not create separate
trades. Position reversal is prohibited by the proposed contract: a fill that
crosses through zero triggers `OPERATOR_REVIEW`.

## Required transition evidence

Every transition records aggregate id, prior and next state, triggering event
id, event sequence, effective time, recorded time, reason code, and causation
id. Invalid transitions are rejected as conflicts and surfaced for review.
Projectors must tolerate duplicate delivery but not contradictory facts.

## Restart and recovery

On restart, state is rebuilt from the event ledger before dispatch resumes.
`DISPATCH_PENDING`, `DISPATCHED`, `PENDING`, `UNKNOWN`, and non-flat positions
must reconcile first. Timeouts generate review events; they do not infer
cancellation, rejection, or fills.
