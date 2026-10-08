# Lane 4 database certification packet

- Workstream: `LANE-4` Database / PostgreSQL Infrastructure
- Status: recommendation for Lane 1. **Not coordinator certification.
  Not Operator acceptance. Not provider acceptance. Not integration
  authorization. Not closure of `DEP-DB-001` or `DEP-DB-002`.**
- Evidence date (UTC): 2026-10-08
- Agent run: `bc-6040b738-314c-499a-96c2-7383ac84c385`
  (https://cursor.com/agents/bc-6040b738-314c-499a-96c2-7383ac84c385)
- Decision token: `LANE4_DB_CERTIFICATION_PACKET_READY`
- Prior token preserved: `LANE4_DEP_DB_002_INDEPENDENT_PASS`

## 1. Canonical identities

Fetched `origin/main` and `origin/cursor/db-dep-db-002-verify-c385` on
2026-10-08.

| Identity | SHA |
| --- | --- |
| `main` at the local reconfirm | `af0d69b1dfc2046899db05a2f12767fc20b623ae` |
| That `main` tree | `4e1ed263e745b9896bf9384a2a9453566ebd6e0b` |
| PR #24 HEAD at the local reconfirm | `db570fac13cb33b84c98afb89c3f4722128ae179` |
| That PR tree | `d754a9b28dfcf77a25a32f114c5882767fac8e59` |
| Later coordinator `main` | `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` |
| Later coordinator tree | `fc97582f22ebf2d24f132c9afe2720430b197f9f` |

The first fetch showed merge-base `af0d69b` and an empty
`src/` `tests/` `migrations/` `pyproject.toml` diff. Before publication,
`main` advanced by two docs-only coordinator commits:
`0f70ab0` and `8cef3d7`. Classification:
`DOCS_ONLY_COORDINATOR_CHECKPOINT`. Those commits update
`docs/CURRENT_STATE.md`, `docs/ENGINEERING_JOURNAL.md`,
`docs/INTEGRATION_PROTOCOL.md`, `docs/WORKSTREAM_DEPENDENCIES.md`, and
`docs/WORKSTREAM_STATUS.md`. They do not change executable files. This
branch merges `8cef3d7` and keeps that governance text. The merge commit
hash is not written here.

Lane 1 already recorded `LANE4_DEP_DB_002_INDEPENDENT_PASS` against
`db570fa` and left both dependencies open. This packet does not treat
that registry edit as closure.

Implementer and verifier are distinct:

| Role | Agent | Commit |
| --- | --- | --- |
| Implementer of the research note | `bc-f38dad08-03c5-5ee8-9b28-8701f8b051f4` | `d949ce0197bc51ceef0b627eea325e9c4d13aaaf` |
| Independent verifier | `bc-6040b738-314c-499a-96c2-7383ac84c385` | `13d6a93f83e7d8c8c34df196ad40c484862af371` |

This packet is further documentation by the verifier agent. It does not
replace the verifier record in
`docs/LANE4_DEP_DB_002_INDEPENDENT_VERIFICATION.md`, and it does not change
`src/`, `tests/`, or `migrations/`.

## 2. Four separate decisions

These are not interchangeable.

| Decision | Question | This packet |
| --- | --- | --- |
| 1. Local implementation verification | Did the twelve TokenStore PostgreSQL nodes pass on disposable local PostgreSQL, with skips remaining skips? | **Sufficient.** Independent PASS already recorded. Reconfirmed on PR HEAD `db570fa` in section 3. |
| 2. Coordinator certification | Does Lane 1 accept that local evidence as the `DEP-DB-002` execution record? | **Not done.** Requested in section 6. This agent cannot certify its own packet as closed. |
| 3. Remote provider acceptance | Is Neon Free or Supabase Free the selected host? | **Not done.** Both remain **NOT_ACCEPTED**. Comparison is in `docs/LANE4_ZERO_COST_HOST_READINESS.md`. |
| 4. Remote integration authorization | May the application open a remote database, run migrations there, or store SIM state? | **Not authorized.** `DRY_RUN` remains the only execution mode. TokenStore still refuses non-local dials. |

No additional local tests are required for decision 1. Remote smoke tests
in `docs/LANE4_REMOTE_SMOKE_TEST.md` are future work after Operator host
selection. They are not missing evidence for the local twelve-node claim.

## 3. Local evidence reconfirmed

Same disposable PostgreSQL 16.15 on localhost port 5432. No remote
connection. URL is the local fixture pattern already recorded in the
verification note.

On HEAD `db570fac13cb33b84c98afb89c3f4722128ae179`:

- Twelve TokenStore nodes: **12 passed, 32 deselected in 0.81s**
- `python3 -m pytest tests/offline tests/contracts`: **161 passed in 0.88s**
- URL unset: **12 skipped, 32 deselected in 0.30s**, reason
  `SWINGTRADE_TEST_POSTGRES_URL is required`

Node IDs remain the twelve listed in the independent verification note.

## 4. Recommendation to Lane 1

Certify **only** local PostgreSQL TokenStore execution of those twelve
nodes, at the SHAs in section 1, after reviewing the verifier note.

Do not:

- set Lane 4 to `READY_FOR_INTEGRATION` or `INTEGRATED`
- mark `DEP-DB-002` resolved until that review is recorded by Lane 1
- treat the PASS as remote-host acceptance
- merge PR #24 from this packet alone

Requested registry text is in section 6. Lane 1 owns
`docs/WORKSTREAM_STATUS.md` and `docs/WORKSTREAM_DEPENDENCIES.md`. This
packet does not edit them.

## 5. What other lanes may rely on

No other lane's code was modified.

### Lane 1

Must review this packet, the verifier note, and the host-readiness note.
Must keep integration eligibility `not_eligible` until a later protocol
pass. Must not authorize a remote migration.

### Lane 2

May treat these as stable local contracts already on `main`, not as a
remote TradeStation store:

- `PostgresIntentRepository.create_or_get` persists canonical `DRY_RUN`
  intent identity in `order_intents`, with a primary key on
  `idempotency_key` and a unique `intent_id`.
- A reused key or intent id with a different canonical payload raises
  `IntentIdentityConflict` inside the same transaction.
- Dispatch remains `DRY_RUN` only (`src/swingtrade/broker.py`).

Lane 2 must not rely on:

- a remote or SIM TokenStore
- broker credential persistence
- any change to TradeStation adapters (none was made)

### Lane 3

May treat the offline Group 4A parser on `main` as unchanged. Future
signal-ingestion persistence is not authorized here. If a later phase
stores ingested instructions, the existing unique key on
`domain_events (aggregate_type, aggregate_id, aggregate_version)` and the
`idempotency_records` primary key are the stable identity shapes. This
packet does not write those tables from Gmail.

### Remains blocked

- `DEP-DB-001` remote host selection
- `DEP-DB-002` coordinator closure
- Supabase and Neon acceptance
- SIM and `LIVE` database connections
- paid provisioning
- automatic migration against an unapproved remote database
- TradeStation OAuth and Gmail OAuth

### Contracts and schemas left unchanged

- ADR-0002 (Accepted; not a provider selection)
- `docs/TOKEN_STORE.md`, `docs/DB_DEPLOYMENT.md`,
  `docs/P2_C_ZERO_INCREMENTAL_COST.md`
- Alembic revisions `0001_offline_foundation`,
  `0002_canonical_order_intents`, `0003_durable_dry_run_observation`
- `offline_token_families` compare-and-swap predicate and check
  constraints
- local dial freeze: hosts outside `localhost`, `127.0.0.1`, and `::1`,
  and markers `tradestation`, `supabase`, `amazonaws`, `neon.tech`

`offline_token_families` is fixture DDL in
`src/swingtrade/offline/token_store.py`. It is not an Alembic revision.

## 6. Requested Lane 1 registry update

Do not apply this table in this branch.

| Field | Requested value |
| --- | --- |
| Lane 4 current state | Keep `READY_FOR_VERIFICATION`. Lane 1 already set this on `8cef3d7`. Do not move to `READY_FOR_INTEGRATION`. |
| Certification status | Keep the `8cef3d7` wording: independent local PASS, not Operator-accepted, not integration approval. This packet adds host-readiness evidence; it is not a second verifier pass. |
| Integration eligibility | `not_eligible` |
| `DEP-DB-002` current state | Keep `OPEN` as updated on `8cef3d7`. Do not mark resolved. |
| `DEP-DB-001` current state | Keep `OPEN`. Optional later note: Neon Free is the preferred unevaluated candidate; Supabase Free remains the alternative; neither is accepted. |
| PR | Stay on draft #24. Do not open a second PR. A distinct agent should verify the post-merge SHA before any integration proposal, because this merge is a new tree even though `src/` and `tests/` are unchanged. |

## 7. Safety attestation

- `LIVE` unauthorized preserved: yes
- No production broker orders: yes
- No TradeStation auth: yes
- No Gmail auth: yes
- No Supabase or Neon connection: yes
- No credential provisioning: yes
- No paid database service: yes
- No remote migration: yes
- No secrets added: yes
