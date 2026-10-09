# Lane 4 provider-neutral readiness

- Workstream: `LANE-4`
- Status: inspection record. **No application code changed. Remote dial
  remains refused. No provider is accepted.**
- Evidence date (UTC): 2026-10-08
- Code inspected at `main` `af0d69b1dfc2046899db05a2f12767fc20b623ae`,
  which matches PR #24 for `src/`, `tests/`, and `migrations/`.

This note prepares a future remote PostgreSQL instance by stating which
guarantees already exist and which do not. It does not open a remote
path. A later change that lifts the local dial freeze, or that changes
commit, retry, or error behavior, needs a distinct verifier. This agent
does not self-certify such a change.

## 1. Inspected guarantees

| Requirement | Inspected result |
| --- | --- |
| PostgreSQL compatibility | `PostgresTokenStore` rejects a non-PostgreSQL dialect (`POSTGRESQL_REQUIRED`). `PostgresIntentRepository` raises `ValueError` unless `engine.dialect.name == "postgresql"`. Alembic revisions `0001`–`0003` use portable SQLAlchemy types (`String`, `Integer`, `JSON`) and unique constraints. They do not create extensions. |
| TokenStore atomicity and concurrency | One conditional `UPDATE` matches family, version, fence, state, environment, and owner, then sets version to expected version + 1. Zero rows raise `StaleWriterRejected`. `test_concurrent_cas_lets_exactly_one_writer_win` is one of the twelve verified nodes. |
| Canonical idempotency keys | `idempotency_key` is `v1:{operation}:{scope}:{sha256}`. `PostgresIntentRepository.create_or_get` rejects a supplied key that does not match that digest, and rejects a stored row whose key or digest differs. Unique constraints: `order_intents.idempotency_key` primary key, `order_intents.intent_id` unique, `idempotency_records.key` primary key, `domain_events (aggregate_type, aggregate_id, aggregate_version)` unique. |
| Duplicate operations | Intent insert uses `on_conflict_do_nothing` and then compares the stored canonical payload. A different payload raises `IntentIdentityConflict` before the `begin()` block exits. TokenStore closes an attempt id before the write; a second use of that id raises `SAME_ATTEMPT_RETRY_DENIED`. |
| Acknowledge only after commit | TokenStore builds the redacted row, calls `connection.commit()`, and returns only after that call. A driver error before `committed = True` rolls back and raises `AUTH_UNKNOWN` with no row returned. Intent persistence returns inside `with self._engine.begin()`. **Inference:** SQLAlchemy commits in that context manager’s exit, which runs before the caller receives the return value. This packet did not add a fault-injection test of commit failure on the intent path. |
| Interrupted connections | TokenStore maps `psycopg.Error` and `SQLAlchemyError` to `AUTH_UNKNOWN`, emits `DB_UNAVAILABLE`, and does not replay the same attempt. The ambiguous-database-error node covers one injected `OperationalError` on `UPDATE`. |
| History integrity | Token version and fence checks are monotonic in the CAS statement (`version >= 1`, `fence >= 1`). `domain_events` uniqueness is per aggregate version. No separate aggregate-history rewrite was inspected beyond those constraints. |
| No silent memory fallback | `InMemoryIdempotencyStore` exists for tests (`tests/idempotency/test_idempotency.py`). `PostgresIntentRepository` does not construct it. ADR-0002 forbids falling back from an unavailable store to a file, environment variable, cache, or local PostgreSQL for SIM. |
| Bounded retries | **Not implemented.** TokenStore performs one attempt and then fails closed. There is no retry loop and no sleep/backoff. The explicit outcomes are `STALE_WRITER`, `TERMINAL_STATE_REJECTED`, `SAME_ATTEMPT_RETRY_DENIED`, and `AUTH_UNKNOWN`. Adding retries would change certified behavior and is out of scope for this packet. |
| Secrets not logged by this store | TokenStore replaces driver exceptions with reason codes. It does not log the URL, password, or ciphertext. Redacted reads omit `refresh_ciphertext`. **Gap:** `PostgresIntentRepository` does not catch driver exceptions. A connection failure can therefore surface a SQLAlchemy or psycopg message that contains the URL. That gap is recorded, not patched, here. |

## 1.1 Unresolved security issue

`PostgresIntentRepository` does not catch driver exceptions. A failed
connection or statement can therefore propagate a SQLAlchemy or psycopg
message that includes the database URL. TokenStore does not have this
gap: it replaces those exceptions with `AUTH_UNKNOWN` and does not log
the URL, password, or ciphertext.

This issue is unresolved. This record does not patch it. A later fix
would change error behavior and needs a verifier other than the author
of that fix. Until then, a future remote URL must still stay out of Git,
chat, and process logs, because this repository path can echo it.

## 2. Remote path is still closed

`require_local_database_connection` allows only `DEV` and `TEST`.
`SIM` raises `SIM_CONNECTION_PROHIBITED`. `LIVE` is denied at binding
time.

`_freeze_dial` allows only `localhost`, `127.0.0.1`, and `::1`, and
rejects host markers `tradestation`, `supabase`, `amazonaws`, and
`neon.tech`. Libpq `PGHOSTADDR` and `PGSERVICE` are refused. Custom
creators and `do_connect` listeners are refused.

`PostgresIntentRepository` does not apply that dial freeze. It uses the
engine the caller supplies. Tests that construct it use local
PostgreSQL. A future remote host needs one policy for both the token
store and the intent repository, after Operator selection. This packet
does not add that policy, because enabling remote hosts is not
authorized, and tightening the intent repository would be a new code
change requiring a distinct verifier.

## 3. Minimum future change, not made here

When the Operator selects a host and Lane 1 authorizes the work, the
smallest later change is:

1. Keep the CAS predicate, idempotency key format, and Alembic revisions
   unchanged.
2. Replace the hard-coded local host allow-list with an explicit
   Operator-approved endpoint check, still rejecting `LIVE`, unmarked
   hosts, and plaintext `sslmode`.
3. Map intent-repository driver errors to reason codes that omit the
   URL and password.
4. Keep retries at zero unless a separate ADR defines a bounded retry
   that cannot repeat a committed economic write.
5. Re-run the twelve TokenStore nodes locally, and run
   `docs/LANE4_REMOTE_SMOKE_TEST.md` only against a disposable schema on
   the approved host.
6. Have an agent other than the implementer of that change verify it.

No step in that list is authorized by this packet.
