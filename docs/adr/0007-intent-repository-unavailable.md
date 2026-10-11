# ADR-0007: Sanitized PostgreSQL intent-repository failure

- Status: Proposed
- Date: 2026-10-11
- Sole Phase 1 decider: Human Operator
- Scope: Caller-visible driver-failure classification for `PostgresIntentRepository.create_or_get`
- Supersedes: None
- Superseded by: None

## Context

`PostgresIntentRepository.create_or_get` is the PostgreSQL boundary for
canonical `DRY_RUN` intent identity. `DryRunAdapter.dispatch` calls it
after `authorize_dispatch` and does not catch its result. On canonical
`main` `8a17bec501df94238fe7588f84f7f1f51fee8baf`, tree
`03d48c9ae453bdfc6a1cdf9cdc43a359e76efb1b`, both files are blob-identical
to draft PR #24: `src/swingtrade/persistence.py` blob
`7d7d4eadd4436e07f256ccb9c1afe52fc921a1a1` and `src/swingtrade/broker.py`
blob `62cb03dd343d0de4b0ffc58d6c65504ed1428fce`. Inspected 2026-10-11,
`create_or_get` has no handler around `engine.begin()`. A SQLAlchemy or
psycopg failure therefore leaves `dispatch` as the driver exception.

SQLAlchemy 2.1.4 `DBAPIError` builds its message as
`({module}.{name}) {str(orig)}` and sets `__cause__` to the driver
exception. `URL.render_as_string` masks a password as `***` by default,
but this failure path does not use that renderer. psycopg 3.3.6 puts the
libpq text in `OperationalError`. Its DEBUG log records host and port
during connect. SQLAlchemy's pool logger records `Error on connect():`
plus the driver text at DEBUG, before application code can catch it.

A prior Lane 4 reproduction, dated 2026-10-10, used synthetic credentials
and local or mocked failures only. It was not re-executed for this
proposal. It showed:

- A closed local port put the host and port in the exception text, `repr`,
  `args`, formatted traceback, `__cause__`, and `logging.exception`. The
  password and username were absent from that rendered text.
- A local authentication failure added the username:
  `password authentication failed for user "[REDACTED_USER]"`, with the
  host. The password was absent from that rendered text.
- A mocked `psycopg.OperationalError` whose message was a PostgreSQL URL
  copied the password, username, host, and database into the SQLAlchemy
  exception text, `repr`, `args`, formatted traceback, `__cause__`, the
  pool DEBUG line, and `logging.exception`. Redacted form:
  `postgresql://[REDACTED_USER]:[REDACTED_PASSWORD]@[REDACTED_HOST]:5432/[REDACTED_DB]`.
- Traceback frame locals on the real dial included `conninfo` and the
  engine. Ordinary `traceback.format_exception` did not print those
  locals. `raise ... from None` does not erase them.

That exposure is a shared caller-visible failure. `dispatch` is the
broker adapter boundary. Changing the type that leaves it requires this
Proposed ADR and later Operator acceptance. This file does not implement
the change.

Existing success and domain behavior, inspected in the same blobs:

- `authorize_dispatch` raises `AuthorizationDenied` before the repository
  call when identity, mode, expiry, replay, or reporting checks fail.
- `create_or_get` raises `NonCanonicalIntentKey` when the supplied key is
  not the canonical dispatch digest, and when a stored row fails that
  check.
- It raises `DurableObservationError` when the stored observation is not
  a canonical object.
- It raises `IntentIdentityConflict` when the same idempotency key or
  intent id is reused with a different canonical payload. That raise is
  inside `engine.begin()`, so the context manager exits by rollback.
- A matching canonical payload returns the stored row.
  `materialize_dry_run_observation` turns that into the `OrderObservation`
  `dispatch` returns.
- The idempotency key remains `v1:{operation}:{scope}:{sha256}` from
  `idempotency_key`. The insert is `on_conflict_do_nothing` followed by a
  read and compare. Unique constraints on `order_intents.idempotency_key`
  and `order_intents.intent_id` are unchanged.
- TokenStore maps its own driver failures to
  `TokenStoreError("AUTH_UNKNOWN")` and raises that outside the `except`,
  so the raised object has no `__cause__`. That classification stays on
  TokenStore.

`DatabaseConnectionDenied("CONNECTION_PROHIBITED")` is the offline
reference gate. It refuses a connection before a TokenStore dial. It is
not a driver failure inside `create_or_get`.

ADR numbers already used on 2026-10-11: `0001` through `0004` and `0006`
on `main`; `0005` on open PR #22; a historical `0003` filename on PR #19.
`0007` is the next unused identifier. No open PR proposes
`IntentRepositoryUnavailable`.

## Safety impact

`DRY_RUN` remains the only authorized execution mode. This proposal does
not authorize implementation, a remote database, Supabase provisioning or
connection, credentials, a migration, broker activity, TradeStation
`SIM`, or `LIVE`. Supabase Free stays the Operator's preferred provider
and stays **NOT_ACCEPTED**. `DEP-DB-001` and `DEP-DB-002` stay OPEN.
Lane 4 stays `READY_FOR_VERIFICATION`. Integration stays `not_eligible`.

An accepted ADR would not by itself authorize coding.
`docs/adr/README.md` requires every governing gate and an explicit
Operator sentence in `docs/CURRENT_STATE.md`. This proposal does not edit
`docs/CURRENT_STATE.md`. A denied capability stays unauthorized.

The proposed fail-closed effect is narrower than today's driver leak and
does not add a success path. A driver failure still fails the call. It
does not retry, replay, fall back to memory, or submit an order. The
caller must not treat `DATABASE_UNAVAILABLE` as proof of rollback.

## Options considered

### Option A — `IntentRepositoryUnavailable("DATABASE_UNAVAILABLE")`

Add `IntentRepositoryUnavailable(RuntimeError)` in
`src/swingtrade/persistence.py`. Its only argument is the stable string
`DATABASE_UNAVAILABLE`. `create_or_get` catches only `psycopg.Error` and
`sqlalchemy.exc.SQLAlchemyError` around the driver work inside
`engine.begin()`. It raises
`IntentRepositoryUnavailable("DATABASE_UNAVAILABLE")` with `from None`.
The message and `args` contain that string and no driver text, URL,
credential, host, port, username, or database name. The repository does
not log the caught exception.

`DryRunAdapter.dispatch` is not edited. The new exception propagates
because `dispatch` already calls `create_or_get` and does not catch it.
That propagation is the shared caller-visible classification.

Preserved without translation:

- `AuthorizationDenied`
- `IntentIdentityConflict`
- `NonCanonicalIntentKey`
- `DurableObservationError`
- `DurableRepositoryRequired`
- the existing non-`DRY_RUN` `AssertionError` guard

A successful call still returns the same `OrderObservation`. Idempotency
keys, compare-and-swap predicates, the `begin()` transaction boundary,
unique constraints, and economic canonicalization stay as they are. There
is no automatic retry, replay, memory fallback, or order resubmission.

`DATABASE_UNAVAILABLE` means the driver boundary failed and the caller
does not have a trustworthy completion signal. It does not mean the
transaction rolled back. A connection loss during commit can leave the
server outcome unknown. A later human or separately authorized procedure
may reconcile. This classification must not retry that attempt on its
own.

Not reused:

- `TokenStoreError("AUTH_UNKNOWN")` belongs to TokenStore. Reusing it
  would merge two failure domains and would require editing TokenStore or
  importing its classification into intent persistence.
- `DatabaseConnectionDenied("CONNECTION_PROHIBITED")` means the offline
  reference gate refused a dial. A driver error after a permitted local
  engine is a different fact.

Benefits: one stable public argument, no driver text in ordinary
exception formatting, domain outcomes unchanged, broker adapter source
unchanged. Costs: callers that match `sqlalchemy.exc.OperationalError`
from `dispatch` would observe a new type. That is the shared-contract
change this ADR exists to propose. Residuals are listed under
Consequences.

### Option B — Leave the driver exception uncaught

No source change. Ordinary logs and formatted tracebacks can carry host,
port, username, and any URL the driver message contains. Rejected because
the exposure is already reproduced for synthetic credentials.

### Option C — Reuse `TokenStoreError("AUTH_UNKNOWN")`

Rejected. TokenStore's reason code is the sanitized classification for
token-family reads and compare-and-swap. Intent identity is a different
aggregate. The implementation task forbids that reuse and forbids
TokenStore edits.

### Option D — Reuse `DatabaseConnectionDenied("CONNECTION_PROHIBITED")`

Rejected. That reason means the reference gate prohibited a connection.
Using it for a failed `begin()` would collapse a pre-dial denial and an
ambiguous driver failure.

### Option E — Keep raising SQLAlchemy's exception after scrubbing its text

Rejected. `__cause__`, `.orig`, and pool DEBUG output would still carry
the driver object. Callers would still see a SQLAlchemy type whose
attributes are the credential-bearing exception.

### Option F — Catch and translate only inside `DryRunAdapter.dispatch`

Rejected. Direct `create_or_get` callers would still leak, and the change
would edit the broker adapter. This proposal forbids broker-adapter
edits.

### Option G — Redact every psycopg and SQLAlchemy log record

Rejected as this ADR's implementation. DEBUG lines from psycopg and
`sqlalchemy.pool` are a residual. A process-wide logging redesign is a
separate authorization. It does not replace the exception-boundary
classification.

## Decision

## Consequences

If the Operator later accepts this exact proposal, the accepted
classification is Option A only. Acceptance still does not authorize
coding. Coding begins only after a later gate records both the Accepted
ADR and an explicit implementation sentence in `docs/CURRENT_STATE.md`
on canonical `main`, and that authorization commit adds no application
code.

Until then, Lane 4 must not change `create_or_get`, tests, migrations,
TokenStore, Gmail, or broker adapters for this boundary.

Positive consequences of a later authorized implementation:

- Ordinary `str`, `repr`, `args`, formatted traceback, and
  `logging.exception` of the new error contain `DATABASE_UNAVAILABLE`
  and no connection material.
- `__cause__` and `__context__` are absent when the implementation uses
  `from None`. That suppresses normal chaining. It does not delete the
  original object from traceback frame locals.
- Domain exceptions and the successful `OrderObservation` stay in place.
- No new retry loop can repeat a write whose commit state is unknown.

Negative consequences and residuals, which this ADR does not close:

- `from None` does not clear frame locals. A debugger or a formatter
  that walks `tb_frame.f_locals` can still read `conninfo` or
  `engine.url.password` while the engine is on `self`. A future test
  must not claim those locals are gone.
- psycopg DEBUG logs host and port during connect. SQLAlchemy pool DEBUG
  logs the driver text in `Error on connect():` before the repository
  catch. Default log levels do not emit those lines. Enabling DEBUG
  remains an exposure. This proposal does not add a global log filter.
- Callers of `dispatch` gain a new exception type on the driver-failure
  path. They do not gain a new success outcome.
- `DATABASE_UNAVAILABLE` can be raised both when PostgreSQL has rolled
  back and when the commit result is unknown. Treating it as rollback
  and inserting again would be a caller bug. The repository must not
  hide that ambiguity by retrying.

Unchanged operational authority:

- `DEP-DB-001` OPEN. Supabase Free preferred, **NOT_ACCEPTED**.
- `DEP-DB-002` OPEN.
- Lane 4 `READY_FOR_VERIFICATION`.
- Integration `not_eligible`.
- PR #24 remains the separate database evidence draft and is not the
  carrier of this ADR.
- `DRY_RUN` only. `SIM` and `LIVE` unauthorized.

## Validation and rollback

This documentation commit is not the implementation. Its checks are
governance and diff checks only. A later implementation, after Operator
acceptance and a `CURRENT_STATE` authorization sentence, requires a
distinct verifier and all of the following. Synthetic credentials only.
No Supabase connection.

Negative security cases:

- Mocked driver exception whose message is a full synthetic PostgreSQL
  URL. Password, username, host, and database name are absent from
  `str`, `repr`, `args`, formatted traceback, and ordinary
  `logging.exception` of the raised `IntentRepositoryUnavailable`.
- SQLAlchemy exception wrapping a psycopg exception, with the same
  absence checks.
- Authentication failure and connection refusal on a local or mocked
  endpoint, with the same absence checks.
- Connection failure before the transaction executes.
- A failure whose commit result is ambiguous. The test asserts the type
  and argument only. It must not assert that the database rolled back.
- `__cause__` is `None` after `from None`. The test must not assert that
  frame locals lack the engine or conninfo. Those locals are a separate
  residual.
- psycopg and SQLAlchemy DEBUG behavior is recorded. Expanding this fix
  into a global logging redesign requires a separate authorization.

Persistence regressions:

- `AuthorizationDenied`, `IntentIdentityConflict`,
  `NonCanonicalIntentKey`, and `DurableObservationError` still propagate
  with their current messages.
- Successful `dispatch` still returns `OrderObservation`.
- Existing idempotency convergence and conflict tests, and the existing
  concurrency test, still pass without a new retry.
- TokenStore tests still expect `AUTH_UNKNOWN` rather than
  `DATABASE_UNAVAILABLE`.
- Diff excludes TokenStore, Alembic migrations, Gmail, and broker
  adapter source.

Rollback of this proposal, while it is Proposed, is to leave it
unaccepted. Rollback of a later implementation is to revert that
implementation commit. Reverting must not add a retry or a second
classification.

## Unresolved questions

- Whether the Operator accepts Option A. Owner: human Operator. The
  Decision section stays blank until that acceptance.
- Whether a later `CURRENT_STATE` sentence authorizes implementation.
  Owner: human Operator. This ADR does not.
- Whether DEBUG logging and traceback-local capture need a separate
  redaction control. Owner: Lane 4 proposal, Lane 1 if the control
  becomes shared. Not decided here.
- Fresh independent certification of TokenStore and of PR #24's
  documentation tip. Owner: Lane 1 review and Operator acceptance.
  `DEP-DB-002` stays OPEN.

## Evidence

1. Repository source, inspected 2026-10-11. Canonical `main`
   `8a17bec501df94238fe7588f84f7f1f51fee8baf`, tree
   `03d48c9ae453bdfc6a1cdf9cdc43a359e76efb1b`.
   `src/swingtrade/persistence.py` blob
   `7d7d4eadd4436e07f256ccb9c1afe52fc921a1a1`.
   `src/swingtrade/broker.py` blob
   `62cb03dd343d0de4b0ffc58d6c65504ed1428fce`.
   Claim: `create_or_get` does not catch driver errors; `dispatch` does
   not catch `create_or_get`. Limitation: inspection is not a runtime
   test.
2. Prior Lane 4 local reproduction, 2026-10-10, synthetic credentials,
   closed port, local authentication failure, and a mocked URL-bearing
   `psycopg.OperationalError`. Claim: rendered exception text and
   ordinary logging can carry URL components, and a URL planted in the
   driver message is copied through SQLAlchemy. Limitation: that run was
   not repeated for this commit. The persistence and broker blobs above
   match the blobs on PR #24 at
   `a567d5ed8cae07e2d61cc8b3d2e491971f48ba44`, which was the tree under
   inspection. No live connection string was recorded.
3. Installed libraries during that reproduction: SQLAlchemy 2.1.4,
   psycopg 3.3.6. Claim: `DBAPIError` stringifies `orig`; psycopg and
   the SQLAlchemy pool log driver text at DEBUG. Limitation: library
   behavior can change in a later install.
4. `docs/adr/README.md` on this `main`. Claim: only the human Operator
   moves a Phase 1 ADR to Accepted, and acceptance does not authorize
   implementation, credentials, `SIM`, or `LIVE`.
5. `docs/CURRENT_STATE.md` and `docs/AGENT_AUTHORITY.md` on this `main`.
   Claim: `DRY_RUN` is the only authorized execution mode; Phase 2 is
   not generally authorized; silence fails closed. This proposal does
   not edit those files.
6. ADR inventory, 2026-10-11. `0001`–`0004` and `0006` exist on `main`.
   `0005` exists on PR #22. Claim: `0007` does not collide with those
   identifiers.
