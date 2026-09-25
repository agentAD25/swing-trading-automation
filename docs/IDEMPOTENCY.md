# Idempotency Contract

## Principle

At-least-once attempts are expected; at-most-one *logical effect* is required.
Idempotency does not prove an external effect did or did not occur. Ambiguous
outcomes are reconciled rather than retried with a new identity.

## Key construction

Keys are derived from immutable business identity, never attempt number or
time:

`v1:<operation>:<scope>:<sha256(canonical-business-input)>`

Examples of scope are `run_id`, `decision_id`, or `order_intent_id`. Canonical
input includes the operation's semantic fields and relevant contract version.
It excludes trace ids, retry counters, and `recorded_at`. The complete key and
input digest are persisted before any effect.

The digest component is exactly 64 lowercase hexadecimal characters. The
fixture canonicalizes the declared input object using the JSON rules in
`DATA_MODEL.md`, hashes those UTF-8 bytes with SHA-256, and records the input
object in `scenario.json` so the key is independently reproducible. Labels,
abbreviated hashes, and hand-authored suffixes are invalid.

## Required behavior

| Boundary | Duplicate behavior |
| --- | --- |
| Command receipt | Return the original result for the same key and input |
| Event append | Identical event is a no-op; conflicting reuse is critical |
| Intent/outbox | Unique intent key; atomic create plus dispatch eligibility |
| DRY_RUN dispatch | Return the original local order identity and observations |
| Projection | Record processed event id in the same transaction as the update |
| Report generation | Reuse byte-identical artifact for identical report key |

Concurrent first use is serialized by a unique constraint or compare-and-set,
not by process-local locks.

## Dispatch recovery

An outbox item transitions from pending to leased to observed. Lease expiry
permits another attempt using the same key. A crash after dispatch but before
recording the result creates an ambiguous state. The dispatcher must query or
reconcile using the original identity before trying again. If the external
system cannot support safe lookup or idempotent submission, automated dispatch
is not certifiable.

No claim is made that TradeStation accepts client idempotency keys, preserves
client order ids, or supports suitable lookup. Those are blocking research
questions for any future adapter.

## Retention and conflict

Idempotency records must outlive the longest possible retry, late observation,
replay, and correction window. The duration is unresolved. Reuse of a key with
a different input digest blocks the operation, emits a conflict event, and
alerts an operator. Records are not silently expired while related orders or
reconciliation cases remain open.

## Verification scenarios

Tests must inject duplicate commands, duplicate events, concurrent requests,
timeouts before and after effects, lease expiry, delayed observations, process
restart, and conflicting key reuse. Assertions cover one logical intent, one
effect identity, stable response, complete audit history, and fail-closed
ambiguity handling.
