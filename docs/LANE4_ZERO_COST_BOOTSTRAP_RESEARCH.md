# Lane 4 zero-cost PostgreSQL bootstrap research

- Workstream: `LANE-4` Database / PostgreSQL Infrastructure
- Status: engineering evidence for Operator and Lane 1 consideration.
  **Not an accepted ADR. Not provider acceptance. Not certification.
  Not procurement or provisioning authority.**
- Evidence date (UTC): 2026-10-08
- Canonical main baseline at branch start:
  `24466ab9e551c6bb13dc1af67c6b33f148ac854a` /
  tree `74ef01fd9ae067e29ae7ecc97c466a39104da2f1`
- Agent run: `bc-f38dad08-03c5-5ee8-9b28-8701f8b051f4`
  (https://cursor.com/agents/bc-f38dad08-03c5-5ee8-9b28-8701f8b051f4)
- Cost constraint (unchanged):
  `INITIAL_DATABASE_INCREMENTAL_SERVICE_COST = 0 USD`
- Historical overlays left unchanged:
  `docs/DB_DEPLOYMENT.md`, `docs/P2_C_ZERO_INCREMENTAL_COST.md`,
  `docs/TOKEN_STORE.md`

## 1. Scope and non-actions

This bootstrap:

- re-verifies published zero-incremental-cost PostgreSQL hosting envelopes;
- inventories the twelve TokenStore PostgreSQL test nodes (`DEP-DB-002`);
- records implementer execution of those tests against a disposable local
  PostgreSQL instance in this Cursor Cloud environment;
- restates Supabase suitability against the prior
  `NOT_ACCEPTED` / unattended-SIM verdict.

This bootstrap does not:

- accept Supabase, Neon, RDS, Cloud SQL, or any other provider;
- connect to Supabase, Operator-owned local PostgreSQL, or any operational
  database;
- provision a paid service, remote project, IPv4 add-on, PITR, replica, or
  branch;
- authorize TradeStation `SIM`, broker auth, Gmail auth, credentials, or
  `LIVE`;
- mark `DEP-DB-001` or `DEP-DB-002` resolved;
- rewrite Phase 1 ledger schemas or production economic migrations.

## 2. Facts / inferences / assumptions / open questions

### Facts

1. Canonical main at start matches the assigned baseline SHA/tree above.
2. `docs/P2_C_ZERO_INCREMENTAL_COST.md` already records Supabase Free-plan
   evidence (access 2026-09-30) and the verdict
   `UNSUITABLE_FOR_UNATTENDED_AUTONOMOUS_SIM`;
   `CONDITIONAL_CANDIDATE_FOR_ATTENDED_INITIAL_SIM`; `NOT_ACCEPTED`.
3. Public Supabase pages fetched 2026-10-08 still document a Free plan at
   0 USD/month, two active projects, 500 MB database size, inactivity pause
   after about one week of low activity, Nano compute at 0 USD (shared CPU,
   up to 0.5 GB memory), no Free-plan automatic backups, and no Free-plan
   PITR ([Z1], [Z3], [Z5]).
4. Public Neon pages fetched 2026-10-08 document a Free plan at 0 USD/month
   with 100 CU-hours/project, 1 GB storage/project (20 GB account total),
   scale-to-zero after 5 minutes of inactivity (disablement is a paid-plan
   control), and AZ compute recovery commonly 1–10 minutes ([N1], [N2],
   [N3]).
5. Offline `PostgresTokenStore` refuses non-local dial targets and blocks
   host markers including `supabase`, `neon.tech`, and `amazonaws`
   (`src/swingtrade/offline/token_store.py`). `DEP-DB-002` therefore cannot
   be satisfied by connecting TokenStore tests to a remote host.
6. At agent start, this environment had no listening PostgreSQL on
   `127.0.0.1:5432`, no Docker, and no `SWINGTRADE_TEST_POSTGRES_URL`.
7. A disposable local PostgreSQL 16.15 cluster was started in this VM only
   (`apt` packages `postgresql` / `postgresql-16`; databases
   `swingtrade_test` / `swingtrade`; role `swingtrade`). No remote host was
   used.
8. With
   `SWINGTRADE_TEST_POSTGRES_URL=postgresql+psycopg://swingtrade:swingtrade@127.0.0.1:5432/swingtrade_test`,
   the twelve TokenStore PostgreSQL nodes passed (section 5). This is
   implementer evidence, not independent certification and not Operator
   acceptance.

### Inferences

1. Supabase Free remains a conditional attended-SIM candidate only; the
   2026-10-08 re-fetch does not overturn the prior unattended-SIM rejection.
2. Neon Free is a documented 0 USD remote PostgreSQL envelope, but it is not
   the same as the prior Operator eligibility set that named only existing
   local PostgreSQL and existing Supabase access. It also cannot disable
   scale-to-zero on Free, so unattended always-on SIM remains blocked under
   the current cost constraint.
3. Closing `DEP-DB-002` still requires coordinator certification review (and
   Operator acceptance of any certification claim). Passing tests alone are
   not integration approval.

### Assumptions

1. The disposable VM PostgreSQL instance is destroyed with the agent
   environment and is not an operational SIM ledger.
2. Public pricing pages may change; figures below are current only as
   fetched on 2026-10-08.

### Open questions

1. Does the Operator still have an existing Supabase Free-plan slot
   (plan, region, major version, quota) — still **UNKNOWN**; not inspected.
2. Does the Operator have or want existing Neon access under the same 0 USD
   constraint — **UNKNOWN**; not inspected; not selected.
3. Will Lane 1 treat the section-5 run as sufficient `DEP-DB-002` specialist
   evidence pending an independent verifier distinct from this implementer?

## 3. Zero-cost hosting options under the 0 USD constraint

| Candidate | Published incremental service cost | Prior eligibility (`P2_C`) | 2026-10-08 research role | Autonomous SIM |
| --- | --- | --- | --- | --- |
| Disposable / existing local PostgreSQL | 0 USD | Eligible for DEV/TEST/adversarial/migration only | Confirmed usable in this Cursor Cloud VM after local install; not a SIM ledger | Forbidden as SIM / SIM fallback |
| Existing Supabase Free access | 0 USD organization plan | Candidate only; **NOT_ACCEPTED** | Reconfirmed Free envelope; verdict unchanged | Unsuitable (pause, no Free HA/PITR) |
| Neon Free | 0 USD/month | Not listed as existing-access eligible | Documented 0 USD envelope; candidate for Operator consideration only | Unsuitable while Free scale-to-zero cannot be disabled |
| Amazon RDS / Cloud SQL / paid Supabase / Neon Launch|Scale | > 0 USD | Not eligible for initial deployment | Still not eligible under the cost constraint | N/A for this bootstrap |

### 3.1 Supabase Free (re-verification)

Supported claims from 2026-10-08 first-party fetches:

- Free plan from 0 USD/month; two active projects; Free projects pause after
  inactivity; paid plans do not pause ([Z1], [Z5]).
- Nano remains the Free compute size at 0 USD, shared CPU, up to 0.5 GB
  memory, recommended max DB size 500 MB; Free compute resources subject to
  change ([Z3]).
- Automatic backups and PITR remain outside the Free envelope ([Z1]).

**Suitability restatement (selection remains Operator / NOT_ACCEPTED):**

`UNSUITABLE_FOR_UNATTENDED_AUTONOMOUS_SIM`;
`CONDITIONAL_CANDIDATE_FOR_ATTENDED_INITIAL_SIM`;
`NOT_ACCEPTED`.

No connection, project inspection, or selection occurred.

### 3.2 Neon Free (new comparative envelope)

Supported claims from 2026-10-08 first-party fetches:

- Free plan price 0 USD/month with included CU-hours and storage ([N1]).
- Scale-to-zero after 5 minutes of inactivity; paid plans can disable it
  ([N2]).
- Compute HA is recreate/reschedule rather than a continuous synchronous
  standby; documented AZ recovery 1–10 minutes; no cross-region replication
  ([N3]).
- Instant restore / longer history windows are paid-plan features relative
  to Free allowances ([N1]).

**Classification for this bootstrap:**

- Eligible as a *documented* 0 USD remote PostgreSQL option for Operator
  research comparison.
- **Not accepted.** Not connected. Not assumed to be “existing access.”
- `BLOCKS_AUTONOMOUS_SIM` while Free scale-to-zero cannot be disabled and
  SIM must not fall back to local PostgreSQL.
- Not a `DEP-DB-002` execution host: TokenStore offline dial rules reject
  `neon.tech`.

### 3.3 What remains blocked for remote SIM (`DEP-DB-001`)

`DEP-DB-001` stays `OPEN`. Operator selection is still required. Zero-cost
remote envelopes reviewed here do not meet the historical proposed SIM HA /
PITR objectives in `docs/DB_DEPLOYMENT.md` §3 without paid features.

## 4. TokenStore / persistence contract inspection

| Artifact | Observation |
| --- | --- |
| `docs/TOKEN_STORE.md` | Provider-neutral PostgreSQL CAS contract; host selection residual; DEV/TEST may use isolated local PostgreSQL; SIM must not fall back to local; `LIVE` invalid |
| `docs/P2_C_ZERO_INCREMENTAL_COST.md` | Cost overlay; Supabase Free inventory; `NOT_ACCEPTED` |
| `docs/DB_DEPLOYMENT.md` | Historical RDS recommendation; unchanged; initial-deployment effect superseded only by the 0 USD constraint |
| `src/swingtrade/offline/token_store.py` | Local-only dial freeze; fixture ciphertext prefix; environment limited to `DEV`/`TEST` in fixture schema |
| ADR-0002 | Accepted for C1/U-10 contract; not operational credential certification or Supabase selection |

## 5. `DEP-DB-002` inventory and implementer execution evidence

### 5.1 The twelve nodes

Parametrized expansion of six `@pytestmark_postgres` tests equals twelve
nodes (matches the journal residual “12 Group 2 token-store PostgreSQL
tests”):

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

Skip gate when unset:
`SWINGTRADE_TEST_POSTGRES_URL is required`.

### 5.2 Environment

| Item | Value |
| --- | --- |
| PostgreSQL | 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) |
| Listen | `127.0.0.1:5432` only |
| Database | `swingtrade_test` |
| URL env | `SWINGTRADE_TEST_POSTGRES_URL=postgresql+psycopg://swingtrade:swingtrade@127.0.0.1:5432/swingtrade_test` |
| Python | 3.12.3 |
| pytest | 9.1.1 |
| Branch tip at evidence capture | recorded in journal / PR after commit |

### 5.3 Commands and outcomes

```bash
sudo pg_ctlcluster 16 main start
# create local role/db swingtrade / swingtrade_test (password local-only)
export SWINGTRADE_TEST_POSTGRES_URL='postgresql+psycopg://swingtrade:swingtrade@127.0.0.1:5432/swingtrade_test'
python3 -m pytest tests/offline/test_token_store.py \
  -k 'matching_cas or predicate_mismatch or stale_writer or ambiguous_database or terminal_state or concurrent_cas' \
  -v --tb=short
```

Outcome: **12 passed, 32 deselected**.

Broader local context (same URL):

```bash
python3 -m pytest tests/offline tests/contracts --tb=no
```

Outcome: **161 passed** (the previous 12 skips become passes).

### 5.4 Certification boundary

| Claim | Status |
| --- | --- |
| Implementer reproducible local PASS for the twelve nodes | Recorded here |
| Independent verifier distinct from implementer | **Not done** |
| `DEP-DB-002` resolved | **No** — remains open until certification review |
| Remote / SIM TokenStore host certified | **No** |
| Supabase accepted | **No** |

## 6. Requested registry updates (Lane 1)

Proposed `WORKSTREAM_STATUS` fields for Lane 4 (Lane 1 owns the registry):

| Field | Requested value |
| --- | --- |
| Current state | `READY_FOR_VERIFICATION` (implementer evidence only) |
| Current branch | `cursor/db-zero-cost-bootstrap-51f4` |
| Current objective | Independent verification of TokenStore PostgreSQL evidence; Operator decision path for `DEP-DB-001` remains open |
| Current blocker | `DEP-DB-001` still Operator-blocked; `DEP-DB-002` awaiting independent certification |
| Certification status | Not certified |
| Integration eligibility | `not_eligible` until verification + protocol gates |

## 7. Evidence catalog

### Repository

- **[R1]** `docs/P2_C_ZERO_INCREMENTAL_COST.md` on baseline main. Supports prior
  Supabase Free inventory and `NOT_ACCEPTED` verdict.
- **[R2]** `docs/DB_DEPLOYMENT.md` on baseline main. Supports historical RDS
  recommendation and proposed SIM objectives.
- **[R3]** `docs/TOKEN_STORE.md`, `src/swingtrade/offline/token_store.py`,
  `tests/offline/test_token_store.py` on baseline main. Support CAS contract,
  local-only dial rules, and the twelve PostgreSQL nodes.

### Supabase (fetched 2026-10-08)

- **[Z1]** Supabase, “Pricing,” https://supabase.com/pricing
- **[Z3]** Supabase, “Compute and Disk,”
  https://supabase.com/docs/guides/platform/compute-and-disk
- **[Z5]** Supabase, “Project Pausing,”
  https://supabase.com/docs/guides/platform/free-project-pausing

### Neon (fetched 2026-10-08)

- **[N1]** Neon, “Plans,” https://neon.com/docs/introduction/plans
- **[N2]** Neon, “Compute lifecycle,”
  https://neon.com/docs/introduction/compute-lifecycle
- **[N3]** Neon, “High Availability (HA) in Neon,”
  https://neon.com/docs/introduction/high-availability

## 8. Safety attestation

- `LIVE` unauthorized preserved: yes
- No production broker orders: yes
- No TradeStation auth: yes
- No Gmail auth: yes
- No Supabase connection: yes
- No credential provisioning for brokers/cloud projects: yes
- No paid database service: yes
- No remote migration: yes
- No secrets committed: yes (local test password used only in ephemeral env
  vars / local roles; not written into git)
