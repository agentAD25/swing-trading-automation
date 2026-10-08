# Lane 4 independent verification of TokenStore PostgreSQL nodes

- Workstream: `LANE-4` Database / PostgreSQL Infrastructure
- Status: independent verifier evidence for Lane 1 certification review.
  **Not Operator acceptance. Not provider selection. Not `DEP-DB-002`
  closure. Not integration approval.**
- Evidence date (UTC): 2026-10-08
- Verifier run: `bc-6040b738-314c-499a-96c2-7383ac84c385`
  (https://cursor.com/agents/bc-6040b738-314c-499a-96c2-7383ac84c385)
- Implementer run (distinct): `bc-f38dad08-03c5-5ee8-9b28-8701f8b051f4`
  (https://cursor.com/agents/bc-f38dad08-03c5-5ee8-9b28-8701f8b051f4)
- Implementer evidence reviewed:
  `docs/LANE4_ZERO_COST_BOOTSTRAP_RESEARCH.md` at commit
  `d949ce0197bc51ceef0b627eea325e9c4d13aaaf`, tree
  `d54619c30221dac05dd3a08887397cd7cad237e0`
- Canonical main at verification time:
  `af0d69b1dfc2046899db05a2f12767fc20b623ae`, tree
  `4e1ed263e745b9896bf9384a2a9453566ebd6e0b`
- Cost constraint (unchanged):
  `INITIAL_DATABASE_INCREMENTAL_SERVICE_COST = 0 USD`

## 1. Verdict

**PASS** for local reproducible execution of the twelve TokenStore
PostgreSQL nodes named in `DEP-DB-002`.

Token: `LANE4_DEP_DB_002_INDEPENDENT_PASS`.

This PASS does not resolve `DEP-DB-002`. Resolution authority remains
specialist evidence plus coordinator certification review, and Operator
acceptance of any certification claim
(`docs/WORKSTREAM_DEPENDENCIES.md`).

## 2. Facts

1. Verifier and implementer agent IDs differ.
2. `git diff --stat d949ce0197bc51ceef0b627eea325e9c4d13aaaf origin/main -- src tests migrations pyproject.toml docker-compose.yml`
   is empty. The executable TokenStore code and tests on the research
   commit match canonical main `af0d69b1dfc2046899db05a2f12767fc20b623ae`.
3. The only commits between parent
   `24466ab9e551c6bb13dc1af67c6b33f148ac854a` and those two tips are
   docs-only: research evidence `d949ce0` and registry reconciliation
   `af0d69b`. Classification of that main divergence:
   `DOCS_ONLY_REGISTRY_DIVERGENCE`. It was not overwritten.
4. `pytest -m postgres` on `tests/offline/test_token_store.py` collects
   no tests (exit 5). The twelve nodes are `skipif` tests, not a marker
   named `postgres`. The inventory is the parametrized expansion of six
   functions decorated with `pytestmark_postgres`.
5. Collected node IDs with the URL set match the implementer inventory
   exactly:

   1. `test_matching_cas_increments_version_once`
   2. `test_predicate_mismatch_updates_zero_rows[version-9]`
   3. `test_predicate_mismatch_updates_zero_rows[fence-9]`
   4. `test_predicate_mismatch_updates_zero_rows[state-REVOKED]`
   5. `test_predicate_mismatch_updates_zero_rows[environment-TEST]`
   6. `test_predicate_mismatch_updates_zero_rows[owner_id-owner_b]`
   7. `test_stale_writer_is_not_retried_in_the_same_attempt`
   8. `test_ambiguous_database_error_does_not_replay_or_chain_material`
   9. `test_terminal_state_cas_does_not_replace_ciphertext[REVOKED]`
   10. `test_terminal_state_cas_does_not_replace_ciphertext[REAUTH_REQUIRED]`
   11. `test_terminal_state_cas_does_not_replace_ciphertext[AUTH_UNKNOWN]`
   12. `test_concurrent_cas_lets_exactly_one_writer_win`

6. This VM had no Docker and no pre-existing PostgreSQL listener.
   PostgreSQL 16.15 was installed from Ubuntu packages and started with
   `pg_ctlcluster`. `listen_addresses` is `localhost`. Port is `5432`.
7. Role `swingtrade` and database `swingtrade_test` were created only on
   that local cluster. No Supabase, Neon, RDS, or Operator database was
   contacted.
8. `src/swingtrade/offline/token_store.py` still blocks host markers
   `tradestation`, `supabase`, `amazonaws`, and `neon.tech`.

## 3. Commands and outcomes

Environment identity:

| Item | Value |
| --- | --- |
| PostgreSQL | 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) |
| Listen | localhost port 5432 |
| Database | `swingtrade_test` |
| Python | 3.12.3 |
| pytest | 9.1.1 |
| psycopg | 3.3.6 |

URL used only in the process environment, matching the public
`docker-compose.yml` local password pattern:

`SWINGTRADE_TEST_POSTGRES_URL=postgresql+psycopg://swingtrade:swingtrade@127.0.0.1:5432/swingtrade_test`

```bash
python3 -m pytest tests/offline/test_token_store.py -o addopts= \
  -k 'matching_cas or predicate_mismatch or stale_writer or ambiguous_database or terminal_state or concurrent_cas' \
  --collect-only -q
```

Outcome: **12/44 tests collected (32 deselected)**. Node IDs are the list
in section 2.

```bash
python3 -m pytest tests/offline/test_token_store.py -o addopts= \
  -k 'matching_cas or predicate_mismatch or stale_writer or ambiguous_database or terminal_state or concurrent_cas' \
  --tb=no -q
```

Outcome: **12 passed, 32 deselected in 0.80s**. Exit 0.

```bash
python3 -m pytest tests/offline tests/contracts -o addopts= --tb=no -q
```

Outcome: **161 passed in 0.88s**. Exit 0. No skips in that run.

```bash
env -u SWINGTRADE_TEST_POSTGRES_URL python3 -m pytest tests/offline/test_token_store.py -o addopts= \
  -k 'matching_cas or predicate_mismatch or stale_writer or ambiguous_database or terminal_state or concurrent_cas' \
  --tb=no -rs -q
```

Outcome: **12 skipped, 32 deselected in 0.29s**. Each skip reason is
`SWINGTRADE_TEST_POSTGRES_URL is required` (1 + 5 + 1 + 1 + 3 + 1).

## 4. Inferences

1. The implementer’s 12/12 and 161/161 counts are reproducible by a
   different agent on a new disposable local cluster.
2. Reporting those nodes as passed requires the local URL. Unset, they
   stay skipped and must not be counted as passes.
3. Coordinator review can treat this file as the missing independent
   execution record. It still cannot, by itself, mark `DEP-DB-002`
   resolved.

## 5. Assumptions

1. The disposable cluster is destroyed with this VM and is not a SIM
   ledger.
2. Identity of `src/` and `tests/` with main was checked by path diff,
   not by re-running the suite on a checkout of `af0d69b`. Because those
   paths are identical, a second checkout would execute the same bytes.

## 6. Open questions

1. Will Lane 1 record this PASS in `docs/WORKSTREAM_STATUS.md` without
   moving Lane 4 to `READY_FOR_INTEGRATION`?
2. `DEP-DB-001` remains Operator host selection. Supabase and Neon stay
   **NOT_ACCEPTED**. This verification does not inform that choice.

## 7. Requested registry fields (Lane 1 owns the registry)

| Field | Requested value |
| --- | --- |
| Current state | Stay `READY_FOR_VERIFICATION` until Lane 1 records this PASS. Do not set `READY_FOR_INTEGRATION`. |
| Certification status | Independent verifier PASS for the twelve local nodes. Coordinator certification review still required. Not Operator-accepted. |
| Integration eligibility | `not_eligible` |
| `DEP-DB-002` | Remains `OPEN` |
| `DEP-DB-001` | Remains `OPEN` |

## 8. Safety attestation

- `LIVE` unauthorized preserved: yes
- No production broker orders: yes
- No TradeStation auth: yes
- No Gmail auth: yes
- No Supabase connection: yes
- No Neon or other remote database connection: yes
- No credential provisioning: yes
- No paid database service: yes
- No remote migration: yes
- No secrets committed: yes
