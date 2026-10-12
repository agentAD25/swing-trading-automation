# Lane 4 remote PostgreSQL smoke test

- Status: procedure for use **after** Operator host selection and an
  explicit authorization to connect.
- **Do not run this procedure now. Do not point it at a shared or
  production database. Do not run Alembic against an unapproved remote
  host.**
- Evidence date (UTC): 2026-10-08
- Applies to a future disposable database or a dedicated schema on the
  selected zero-dollar host. Neon Free and Supabase Free are both
  **NOT_ACCEPTED**.

## 1. Preconditions

All of the following are required before any command runs:

1. Operator has selected one host under
   `INITIAL_DATABASE_INCREMENTAL_SERVICE_COST = 0 USD`.
2. Lane 1 has authorized a remote connectivity test in writing. Draft
   PR review is not that authorization.
3. The URL is supplied only through an ignored environment variable or
   an approved secret manager. It is not committed, pasted into chat, or
   written into logs.
4. The target is a new empty database, or a new schema created for this
   test and dropped at the end. It is not the Operator’s application
   database if one already contains data.
5. `sslmode=verify-full` is set. `disable` and `prefer` are failures.
6. The client role is not a superuser, and it cannot see other
   projects’ data.
7. `DRY_RUN` remains the execution mode. No broker, Gmail, or order
   call is part of this procedure.

If any precondition is missing, stop.

## 2. Connection and server identity

Use a direct connection for catalog and migration checks. Use the
provider pooler only for the later application-style section, and record
which hostname was used.

```sql
SELECT version();
SHOW server_version;
SHOW ssl;
SELECT current_database(), current_user, inet_server_addr(), inet_server_port();
```

Record the exact version string. Local TokenStore evidence used
PostgreSQL 16.15. A different major version does not fail the smoke
test by itself; it must be one of the provider’s supported majors and
must be written into the evidence note.

Confirm TLS by the client’s verify-full handshake, not only by `SHOW ssl`.
A handshake that falls back to plaintext fails the test.

## 3. Migration compatibility

Against the empty disposable database only:

```bash
alembic upgrade head
alembic upgrade head
alembic current
```

The second upgrade must be a no-op. Expected head is
`0003_durable_dry_run_observation`.

Required relations after head:

| Relation | Identity constraint |
| --- | --- |
| `domain_events` | primary key `event_id`; unique `(aggregate_type, aggregate_id, aggregate_version)` |
| `idempotency_records` | primary key `key` |
| `outbox_items` | primary key `intent_id`; unique `idempotency_key` |
| `order_intents` | primary key `idempotency_key`; unique `intent_id`; column `canonical_observation` |

`offline_token_families` is not created by Alembic. Create it only
through `create_fixture_schema` inside the disposable database, after
the dial policy allows that host. Confirm check constraints
`ck_token_family_env`, `ck_token_family_version`, `ck_token_family_fence`,
`ck_token_family_state`, and `ck_token_family_material`.

Do not run `alembic downgrade`. Cleanup is `DROP SCHEMA` or dropping the
disposable database, and only when the Operator has allowed teardown of
that fixture.

## 4. TokenStore and idempotency checks

Run these only in the disposable database, with fixture ciphertext
(`fixture:` prefix or empty), never with a real token.

1. Insert one token family. Read the redacted row. Confirm ciphertext
   is absent from the redacted result.
2. Compare-and-swap once with the matching predicate. Version becomes 2.
3. Replay the same `attempt_id`. Expect `SAME_ATTEMPT_RETRY_DENIED` and
   an unchanged ciphertext.
4. Submit two concurrent compare-and-swap calls for the same predicate.
   Expect one success and one `STALE_WRITER`.
5. Insert one `order_intents` row through `PostgresIntentRepository`.
   Repeat the same canonical intent. Expect the same stored digest.
6. Repeat with the same idempotency key and a different canonical
   payload. Expect `IntentIdentityConflict` and no second row.
7. Open a transaction, insert a fixture row, and roll it back. Confirm
   the row is absent.
8. Drop the client connection during an open transaction that has not
   committed. Reconnect. Confirm the uncommitted row is absent and that
   no second economic row appeared.

## 5. Disconnect, pool, and migration repeatability

1. Stop the client. Open a new connection with verify-full. Repeat the
   version query.
2. If the provider scale-to-zero or pause behavior can be observed
   without leaving the test database, record the observed delay. Do not
   generate traffic solely to keep a Free compute awake.
3. Open connections up to one below the documented pool or direct limit
   for the selected size, then one more. Record the provider error text
   with the URL removed. Do not raise the provider’s `max_connections`.
4. Run `alembic upgrade head` again. It must report no new revision.
5. Take one logical dump of the disposable database with `pg_dump` on a
   **direct** connection (Neon’s pooler is the wrong endpoint for
   `pg_dump`). Restore it into a second empty disposable database.
   Compare relation names and row counts for the fixture rows. Then drop
   both fixtures if teardown is authorized.

## 6. Evidence to bring back

Record command names, provider and Postgres version, pass/fail for each
numbered check, and the git SHA under test. Omit hostnames, passwords,
and full URLs. A failure stops remote use. It does not by itself change
`DEP-DB-001` or authorize `LIVE`.

## 7. Out of scope

- TradeStation, Gmail, orders, and SIM sessions
- Production or shared data
- Provider upgrades, compute resizing, and paid PITR
- Editing Alembic revisions to match a provider quirk
