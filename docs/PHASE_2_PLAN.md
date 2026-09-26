# Phase 2 Executable Plan

## 0. Status banner (read first)

- **Document type:** planning artifact only.
- **Phase 2 implementation status: NOT STARTED.** This document contains no
  application code, no provisioning, no credentials, no broker network
  calls, no SIM or LIVE orders, and authorizes none of those things.
- This plan does not accept any ADR, does not select a managed PostgreSQL
  provider, does not resolve any `BROKER_BEHAVIOR_UNRESOLVED` item by
  assumption, and does not change `docs/CURRENT_STATE.md` phase
  authorization. Only the human Operator, acting through the gates defined
  in §8, can do those things.
- Produced from finalized canonical `main` at commit
  `249b8eb341b56d596f07b28723b37ddff96eb86c` (tree
  `d5ceeab6817e5986e02de3ff7bee63eb611a4aa8`), immutable tag
  `phase1-complete` (tag object `f62c2f94eef8b10e1e2aef69df62e09d43e51821`).
  This plan makes no changes to that baseline; it is additive documentation
  on an isolated branch.
- Every non-overridable rule in `docs/AGENT_AUTHORITY.md`,
  `docs/SIM_LIVE_BOUNDARY.md`, and `docs/LIVE_PROMOTION.md` is preserved
  unchanged and re-stated, not weakened, throughout this plan (see §3).

## 1. Plan record (fields 1–40)

| # | Field | Value |
| --- | --- | --- |
| 1 | Report date | 2026-09-26 |
| 2 | Plan type | Phase 2 executable plan — planning-only, no implementation |
| 3 | Baseline `main` commit | `249b8eb341b56d596f07b28723b37ddff96eb86c` |
| 4 | Baseline `main` tree | `d5ceeab6817e5986e02de3ff7bee63eb611a4aa8` |
| 5 | Baseline tag | `phase1-complete` |
| 6 | Baseline tag object | `f62c2f94eef8b10e1e2aef69df62e09d43e51821` |
| 7 | Inherited Phase 1 status | `PHASE1_COMPLETE` (bounded meaning per `docs/PHASE_1_CLOSURE.md` §6: governance/design/reconciliation/acceptance/offline-`DRY_RUN` baseline only) |
| 8 | Phase 2 status after this plan | `NOT_STARTED` — planning artifact only |
| 9 | Plan producer | Cloud-agent planning run (this thread), no Operator role assumed |
| 10 | Plan branch | `cursor/phase-2-plan-ec4a` |
| 11 | Plan file path | `docs/PHASE_2_PLAN.md` |
| 12 | Plan document schema/version | `PHASE2_PLAN_SCHEMA_v1` |
| 13 | Workstreams defined | 10 (`P2-A` … `P2-J`, §7) |
| 14 | Agent roles defined | 9 (coordinator, broker researcher, security/auth architect, DB/deployment engineer, broker client, execution, reconciliation, verification, monitoring/reporting; §6) |
| 15 | DAG gates defined | 10 (`H1`–`H5` review/verification gates, `G1`–`G3` credential/probe/SIM-order boundaries, plus 2 explicit human-decision gates; §8) |
| 16 | Unresolved TradeStation behaviors classified | 12 of 12 from `docs/BROKER_CONTRACT.md` (§5) |
| 17 | Managed PostgreSQL candidates compared | 4 — Supabase, Amazon RDS for PostgreSQL, Neon, Google Cloud SQL for PostgreSQL (§4) |
| 18 | Managed PostgreSQL selection made by this plan | **NONE.** Selection is explicitly deferred to a future Operator-accepted ADR at Human Decision Gate 2 (§8) |
| 19 | Provider-neutral persistence layer preserved | YES — Python → SQLAlchemy 2.0 (Core/ORM) → standard PostgreSQL wire protocol via `psycopg[binary]`, Alembic migrations; `PostgresIntentRepository` continues to assert `engine.dialect.name == "postgresql"` only, never a vendor-specific driver or extension (§3, §4.3) |
| 20 | Non-overridable authority rules preserved | YES — credentials, broker/account/network activity, TradeStation `SIM`, Phase 2 execution, order submission, real capital, and `LIVE` remain denied by `docs/CURRENT_STATE.md` until each gate in §8 is passed exactly as written; this plan changes no denial (§3) |
| 21 | UNKNOWN / fail-closed rule preserved | YES — every new contract in §7 inherits `DATA_MODEL.md`'s "unknown external value retained raw, mapped to `UNKNOWN`; never coerced" rule and every workstream's escalation trigger fails closed on ambiguity (§3, §7) |
| 22 | Reconciliation authority rule preserved | YES — "reconciliation detects disagreement; it does not manufacture agreement" and "the system must not create, cancel, or offset an order to repair drift" (`RECONCILIATION.md`) apply unchanged to the broker-state extension in `P2-F` (§3, §7.6) |
| 23 | Smallest first executable slice ID | `P2-0` (§9) |
| 24 | Smallest slice scope | Broker-behavior re-classification doc, DB decision-framework doc, auth-architecture research doc, environment-naming doc — zero code, zero credentials, zero network (§9) |
| 25 | Smallest slice prohibited actions | Credentials, network calls, broker calls, ADR acceptance, source/migration edits, DB provisioning, any order code (§9) |
| 26 | Credential boundary gate ID | `G1` (§8) |
| 27 | Authenticated-probe boundary gate ID | `G2` (§8) |
| 28 | SIM-order boundary gate ID | `G3` (§8) |
| 29 | LIVE boundary | Categorically outside this entire plan's scope; every workstream terminates at SIM certification (`P2-I`); `LIVE` promotion remains gated exclusively by `docs/LIVE_PROMOTION.md`'s independent conjunctive prerequisites, untouched here (§3, §8) |
| 30 | Task classification counts (this plan) | 22 `HIGH_REASONING` tasks, 15 `ROUTINE_IMPLEMENTATION` tasks across §10's task table |
| 31 | Default `HIGH_REASONING` model | `gpt-5.6-sol-medium`, escalated only per the explicit justifications in §6/§10 |
| 32 | Default `ROUTINE_IMPLEMENTATION` model | `composer-2.5` |
| 33 | Verifier independence rule | A verifier is never the same agent/session/model instance as the producing role for the artifact it checks; independent verification is required at every `H`-gate (§6, §8) |
| 34 | Worktree isolation rule | One git worktree/branch per workstream (`cursor/phase2-<workstream-id>-<slug>`); only the coordinator role may open cross-workstream integration PRs (§6) |
| 35 | Evidence sources cited | 24 first-party/official sources with access timestamps, plus 5 Phase 1 repository-evidence citations (§12) |
| 36 | Research currency date | 2026-09-26 |
| 37 | Repository inspection scope | Full `docs/`, `.cursor/`, `src/`, `migrations/`, `tests/`, `pyproject.toml`, `docker-compose.yml`, `alembic.ini`, `.env.example` at tag `phase1-complete` (§2) |
| 38 | Implementation performed by this run | **NONE** — zero changes to `src/`, `migrations/`, `tests/`, `pyproject.toml`, `.cursor/`, or any accepted Phase 1 contract file; this run adds exactly one new file, `docs/PHASE_2_PLAN.md` |
| 39 | Credentials / broker / network / order actions performed by this run | **NONE** |
| 40 | Phase 2 implementation status after this plan | **NOT STARTED.** No code, ADR acceptance, provisioning, credential, or execution action is authorized by this document. All of §7–§9 describe future work gated by the human Operator. |

## 2. Inputs inspected (evidence of scope)

Read in full at commit `249b8eb341b56d596f07b28723b37ddff96eb86c`:
`docs/PHASE_1_CLOSURE.md`, `docs/BROKER_CONTRACT.md`, `docs/AGENT_AUTHORITY.md`,
`docs/ARCHITECTURE.md`, `docs/CURRENT_STATE.md`, `docs/DECISIONS.md`,
`docs/SIM_LIVE_BOUNDARY.md`, `docs/LIVE_PROMOTION.md`,
`docs/RECONCILIATION.md`, `docs/IDEMPOTENCY.md`, `docs/SIM_CERTIFICATION.md`,
`docs/MONITORING.md`, `docs/DATA_MODEL.md`, `docs/EVENT_MODEL.md`,
`docs/TRADE_LIFECYCLE.md`, `docs/REPORTING.md`, `docs/METRICS.md`,
`docs/TEST_PLAN.md`, `.cursor/agents/*.md`, `.cursor/rules/*.mdc`,
`config/README.md`, `pyproject.toml`, `.env.example`, `docker-compose.yml`,
`alembic.ini`, and the source tree
`src/swingtrade/{config,safety,broker,persistence,domain,idempotency,
reconciliation,state_machine,wdc,api}.py` plus the three Alembic migrations
and `tests/validate_phase1_contracts.py`. Ancestry/tag identity was
independently re-verified by `git fetch`, `git log`, and `git tag -l`
against `origin` immediately before drafting (§12, evidence items E1–E5).

Project-store evidence consulted (read-only, not modified): `notes.md` and
`internal/phase1-repository-finalization.md` in the shared Agent Store,
confirming the `main`/`phase1-complete` promotion and PR #1–#6 disposition
independently of the in-repo closure audit.

## 3. Invariants this plan preserves unchanged

These sentences are restated, not re-derived, from the cited files. This
plan adds new contracts in their spirit; it does not edit, weaken, or
reinterpret any of them.

| Invariant | Source | Status in this plan |
| --- | --- | --- |
| `DRY_RUN` is the sole authorized execution mode; `SIM`/`LIVE` require a separately authorized phase each | `SIM_LIVE_BOUNDARY.md` | Unchanged. Every `P2-*` workstream is scoped to design/DRY_RUN until its named gate (§8) |
| No prompt, instruction, ADR, configuration, or repository edit can grant a capability current state denies; conflicts fail closed | `AGENT_AUTHORITY.md` §"Non-overridable authority rule" | Unchanged. This plan cannot and does not edit `docs/CURRENT_STATE.md`'s denials |
| The human Operator is the sole Phase-1/Phase-2 acceptance decider; agents prepare evidence only | `AGENT_AUTHORITY.md`, `DECISIONS.md` | Unchanged. Every ADR-acceptance and phase-authorization step in §8 is an explicit Operator action, not an agent action |
| Unknown external values are retained raw and mapped to `UNKNOWN`, never coerced | `DATA_MODEL.md` | Unchanged. `P2-E`'s DTO normalization contract (§7.5) inherits this rule verbatim for every unresolved TradeStation field |
| Reconciliation detects disagreement; it never manufactures agreement or auto-repairs an order | `RECONCILIATION.md` | Unchanged. `P2-F`'s broker-state extension (§7.6) adds check-layer scope only, not new repair authority |
| `LIVE` requires every condition in `LIVE_PROMOTION.md` concurrently, decided last, by the Operator alone | `LIVE_PROMOTION.md` | Unchanged and out of scope. Nothing in §7–§9 is a `LIVE` prerequisite; `SIM` certification (`P2-I`) is this plan's terminal milestone |
| Persistence is Python → SQLAlchemy → PostgreSQL, provider-neutral; `PostgresIntentRepository` asserts only the `postgresql` SQLAlchemy dialect, never a vendor SDK | `pyproject.toml`, `src/swingtrade/persistence.py:271-275`, `ARCHITECTURE.md` §"Storage and consistency boundaries" | Unchanged. §4's comparison explicitly screens candidates for standard-wire-protocol/Alembic compatibility so no candidate could force a dialect or driver change |

## 4. Managed PostgreSQL decision framework (comparison only — no selection, no provisioning)

### 4.1 Why this is a framework, not a decision

Per `AGENT_AUTHORITY.md` and `DECISIONS.md`, technology/persistence-product
selection is an unresolved Operator choice (`DECISIONS.md` §"Unresolved
operator choices": "persistence and queue products"). This section supplies
comparable, cited, current evidence so the Operator can later accept a
Phase 2 "Managed Database" ADR at **Human Decision Gate 2** (§8). No
candidate is selected, ranked into a single winner, or provisioned here.

### 4.2 Candidates and why these four

- **Supabase** — managed Postgres bundled with auth/storage/realtime
  add-ons; representative of the "BaaS-on-Postgres" category.
- **Amazon RDS for PostgreSQL** — traditional persistent-instance managed
  database; representative of the mature hyperscaler IaaS-style category,
  already implicitly assumed by the codebase's plain
  `postgresql+psycopg://` connection string.
- **Neon** — serverless, branchable, scale-to-zero Postgres; representative
  of the "storage-separated serverless Postgres" category.
- **Google Cloud SQL for PostgreSQL** (fourth candidate, justified) —
  chosen over a fifth serverless option (e.g., another Neon-like product)
  because it is architecturally distinct from the other three: it is a
  traditional persistent-VM-based managed instance family like RDS but on a
  different cloud ecosystem, with mature Cloud-IAM-integrated
  authentication and an independent backup/PITR implementation ("backup
  vault"/enhanced backups). It gives the comparison a second point in the
  "persistent instance, cloud-IAM-native" quadrant instead of a third point
  in the "serverless/branchable" quadrant already covered by Neon and (to a
  lesser extent) Supabase, which is the more informative choice for an
  Operator deciding between architectural families rather than between
  near-duplicates.

### 4.3 Comparison matrix

All facts below are cited to first-party documentation accessed
2026-09-26 (full citations in §12, E6–E24). Figures are current at that
date and are known to change; the Operator's eventual ADR must re-verify
before acceptance.

| Dimension | Supabase | Amazon RDS for PostgreSQL | Neon | Google Cloud SQL for PostgreSQL |
| --- | --- | --- | --- | --- |
| **Reliability / HA** | Single dedicated Postgres per project; no documented synchronous multi-AZ standby comparable to RDS Multi-AZ in the reviewed docs | Multi-AZ option with synchronous standby and automatic failover in ~60–120s, roughly double the Single-AZ price (E17) | Autoscaling compute with scale-to-zero; storage is described as multi-AZ; no traditional hot-standby failover model (E10) | Standard HA configuration with regional failover available (Cloud SQL HA docs, not independently re-fetched this pass — flagged as an open verification item, E22–E24) |
| **Backups / PITR** | Daily backups (7/14/30 days by plan); PITR is a **paid add-on** (from $0.137/hr, ~$100/mo for 7 days) requiring at least a Small compute tier; RPO ≈ 2 minutes (E6, E7, E8) | Automated backups + transaction logs, 0–35 day retention, PITR restores to a **new instance**, `LatestRestorableTime` typically within 5 minutes of now (E11–E13) | Built-in "instant restore" (continuous WAL, no separate backup tooling); history window 6h (Free) to 30 days (Scale); restores **in place** on root branches only, auto-creates a backup branch; billed per GB-month of change history (E9, E10) | Standard backups (daily, 1-year retention) or Enhanced backups with "backup vault" (hourly/daily/weekly/monthly, up to 10-year retention, retention-lock); PITR always restores to a **new instance**; enabling/disabling PITR requires an instance restart (E20–E23) |
| **Connection limits / pooling** | Compute-tier-dependent: Nano/Micro 60 direct / 200 pooler; Small 90/400; Medium 120/600; scales to 500/12,000 at 16XL. Two poolers available: Supavisor (shared, multi-tenant, IPv4-only) and dedicated PgBouncer (E7, E8) | `max_connections` is a **static** parameter tied to instance class/memory; changing it requires a reboot; no bundled pooler (RDS Proxy is a separate paid product, not reviewed this pass) (E14) | PgBouncer front-end, `max_client_conn=10000`; backend `max_connections` ~100–4,000 by compute size; `default_pool_size` = 90% of `max_connections`; **transaction-mode pooling** by default (E9, E15, E16) | `max_connections` auto-scales with instance memory, up to 262,142 theoretical ceiling minus reserved worker slots; standard Postgres semantics, no mandatory external pooler (E22–E24) |
| **Long-running background workers (execution/reconciliation processes)** | Direct (non-pooled) connections are recommended for long-lived sessions; pooled connections are transaction-scoped | Direct connections behave like vanilla Postgres; no pooling-mode caveat for long-lived workers | **Caveat:** PgBouncer transaction mode does not preserve session state (`SET`, `LISTEN/NOTIFY`, prepared statements, advisory locks) across statements; long-lived workers should use the **direct** (non-pooled) endpoint, and idle direct connections must tolerate compute scale-to-zero suspension (`SSL SYSCALL EOF`) unless `pool_recycle`/`pool_pre_ping` are set in SQLAlchemy (E15, E16, E18) | Direct connections behave like vanilla Postgres; no pooling-mode caveat |
| **SQLAlchemy + Alembic compatibility** | Standard `postgresql+psycopg://`; direct connection recommended for migrations | Standard `postgresql+psycopg://`; no split between migration and app connection strings | Requires the **non-pooled** connection string for `alembic upgrade`/`revision --autogenerate`; pooled string is for the app only — this is an extra operational rule not present in the other three candidates (E16, E17) | Standard `postgresql+psycopg://` (directly or via the Cloud SQL Auth Proxy/connector); no pooled/direct split |
| **Security / auth model** | Postgres role/password auth; project-level dashboard access control; no native cloud-IAM database-token integration in the reviewed docs | **IAM database authentication** available: 15-minute IAM auth tokens via AWS Signature v4, no password needed, requires `rds_iam` role, SSL, and 300–1000 MiB extra instance memory (E14) | Postgres role/password auth via connection string; no native cloud-IAM database-token integration in the reviewed docs | **IAM database authentication** available: `cloudsql.iam_authentication` flag, IAM users/service-accounts/groups, ~1-hour tokens via Cloud SQL connectors, automatic token refresh recommended (E20, E24) |
| **DEV/TEST/SIM/LIVE environment separation** | Supports project-level "Branching" add-on (metered per branch-hour) for ephemeral copies | No native low-cost branching; separate environments require separate instances (full compute + storage cost each) | **Native, cheap branching** (copy-on-write storage; branch pricing separate from root); explicitly marketed for ephemeral test/dev databases; only **root** branches support PITR (E9, E10) | No native low-cost branching; separate environments require separate instances (full compute + storage cost each) |
| **Monitoring / ops integration** | Supabase-native dashboard, logs, and metrics; no first-party integration with a general cloud-observability stack reviewed this pass | Native CloudWatch metrics/alarms integration; Enhanced Monitoring for OS-level process detail | Neon-native dashboard/metrics; no first-party general cloud-observability integration reviewed this pass | Native Cloud Monitoring/Cloud Logging integration |
| **Latency** | Depends on Supabase's own regions vs. the future compute host's region — not resolved by this research; flagged as an open item for whichever deployment topology the Operator later selects | Depends on chosen AWS region vs. compute host region — same open item | Depends on chosen Neon region vs. compute host region — same open item, additionally scale-to-zero cold-start adds first-request latency after idle periods | Depends on chosen GCP region vs. compute host region — same open item |
| **Operational burden** | Low — managed backups/scaling, but PITR/branching/advanced features are metered add-ons that must be actively enabled | Moderate — static parameters (e.g. `max_connections`, `shared_buffers`) must be sized manually and a bad value can prevent instance start (E14); mature, well-documented operational runbooks industry-wide | Low — autoscaling and scale-to-zero reduce idle cost/ops, but the transaction-pooling caveats (above) add a category of application-level care that RDS/Cloud SQL do not require | Moderate — similar static-parameter sizing discipline to RDS; mature GCP-native tooling |
| **Cost (illustrative, not a quote)** | Pro plan compute from ~$25/mo instance-size tiers; PITR add-on **from $100/mo** for 7-day retention alone, scaling to ~$400/mo for 28 days; branching $0.01344/branch-hour (E7, E8) | `db.t4g.micro` (2 vCPU / 1 GiB) ≈ $11.68/mo Single-AZ / $23.36/mo Multi-AZ; `db.m6g.large` (2 vCPU / 8 GiB) ≈ $116/mo Single-AZ / $232/mo Multi-AZ; excludes storage/IOPS/transfer/backup-storage overage (E17–E19; region us-east-1, list pricing as of 2026-07 to 2026-09, subject to change) | Pay-per-use: compute $0.106–$0.222/CU-hour, storage $0.35/GB-mo, instant-restore history $0.20/GB-mo, scale-to-zero reduces idle compute cost toward $0 (E10) | Not independently re-priced this pass; Cloud SQL pricing is public but was not fetched in this research round — **flagged as an explicit open item** for whoever drafts the eventual ADR (do not assume parity with RDS) |
| **Exit portability** | Standard PostgreSQL underneath; portable via `pg_dump`/logical replication as long as the application avoids Supabase-specific services (Auth/Storage/Realtime/PostgREST) — the current codebase already avoids all of them, so exposure is low but must stay that way by contract, not by accident | Standard PostgreSQL; portable via `pg_dump`/snapshot export or AWS DMS; "just Postgres" with the fewest vendor-specific runtime dependencies of the four | Standard PostgreSQL wire protocol for the app, but its point-in-time/branching model is proprietary (copy-on-write storage engine); base data remains exportable via `pg_dump`/logical replication, but instant-restore/branch history itself does not travel with an export | Standard PostgreSQL; portable via `pg_dump`/snapshot export or Database Migration Service; comparable exit friction to RDS |

### 4.4 What stays fixed regardless of which candidate the Operator later picks

- The application never imports a provider SDK; it speaks SQLAlchemy 2.0 +
  `psycopg[binary]` over the standard PostgreSQL wire protocol, exactly as
  today (`pyproject.toml:11-15`, `persistence.py:271-275`).
- `PostgresIntentRepository.__init__` continues to assert
  `engine.dialect.name == "postgresql"` and nothing more specific; no
  candidate-specific dialect, extension, or client library may be added to
  that assertion without a new ADR.
- Alembic migrations continue to run against a plain connection string;
  if the eventual candidate requires a "direct, non-pooled" URL for
  migrations (Neon does; Supabase's dedicated PgBouncer does not intercept
  DDL the same way) that becomes a deployment-configuration fact recorded
  in `docs/DB_DEPLOYMENT.md` (owned by `P2-C`, §7.3), never a code branch on
  provider identity.
- DEV/TEST/SIM/LIVE environment separation is a **connection-string and
  network-policy** concern, not a code-path concern: `RuntimeConfig`
  (`config.py`) already fails closed on any non-`DRY_RUN` mode and forbids
  `broker_endpoint`/`broker_account`/`broker_credentials`; `P2-C` extends
  this pattern to database URLs (one URL per environment, never inferred,
  never defaulted) without adding provider-specific logic.

### 4.5 Explicit non-selection statement

No managed PostgreSQL provider is selected, procured, or provisioned by
this plan. `docs/DB_DEPLOYMENT.md` (the standalone contract this section
seeds, owned by `P2-C`) will carry this comparison forward for the
Operator's Human Decision Gate 2 ADR (§8). Until that ADR is accepted, the
authorized development/test database remains the existing local
`docker-compose.yml` PostgreSQL 17 container.

## 5. TradeStation 12-item unresolved-behavior classification matrix

Source: `docs/BROKER_CONTRACT.md` §"`BROKER_BEHAVIOR_UNRESOLVED`" (items
1–12, re-verified against current TradeStation API documentation on
2026-09-26; citations E25–E27 in §12 corroborate the OAuth/order-execution
facts already recorded in `BROKER_CONTRACT.md` and found no changes to the
prior findings). Classification taxonomy:
`DOCS_ONLY` (resolvable by further first-party document review, no probe
needed), `READ_ONLY_AUTHENTICATED_PROBE` (needs an authenticated, read-only
SIM call — Gate `G2`), `SIM_EXPERIMENT` (needs an authenticated write/order
call in SIM — Gate `G3`), `IMPLEMENTATION` (resolution is encoded as a
fail-closed code contract, not discovered empirically), `OPERATOR_DECISION`
(requires a business/account relationship or policy choice only the
Operator can make), `DOWNSTREAM_BLOCKER` (marks which `P2-*` deliverable
cannot be finalized until the item resolves).

| # | Item (from `BROKER_CONTRACT.md`) | Primary classification | Confirmatory classification | Resolves via | Gate | Downstream blocks |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Idempotency: `OrderConfirmID` acceptance/retention/collision/retry | `SIM_EXPERIMENT` | `IMPLEMENTATION` (key-construction contract can be drafted fail-closed first) | `P2-A` round 2, `P2-G` | `G3` | `P2-G` final implementation |
| 2 | Ambiguous outcomes: recovery after 503/504/disconnect during place/replace/cancel | `SIM_EXPERIMENT` | `IMPLEMENTATION` (recovery procedure must fail closed to `OPERATOR_REVIEW` regardless of what SIM shows) | `P2-A` round 2, `P2-G` | `G3` | `P2-G` final implementation |
| 3 | Order state machine: complete status enumeration/transitions | `READ_ONLY_AUTHENTICATED_PROBE` | `SIM_EXPERIMENT` (transitions only reachable by placing/cancelling test orders) | `P2-A` round 2, `P2-D` | `G2` (initial), `G3` (complete) | `P2-E` DTO mapping completeness |
| 4 | Stream recovery: heartbeat/reconnect/replay/gap detection | `READ_ONLY_AUTHENTICATED_PROBE` | — | `P2-D` | `G2` | `P2-E`, `P2-F` (stream-sourced reconciliation) |
| 5 | SIM fidelity: partial fills, rejects, cancels, buying power, corporate actions | `SIM_EXPERIMENT` | — | `P2-H` | `G3` | `P2-I` certification evidence |
| 6 | Authentication conflicts: refresh-rotation interval (30 vs. 40 min), default scopes | `OPERATOR_DECISION` (requires TradeStation Client Experience confirmation for the specific API key) | `READ_ONLY_AUTHENTICATED_PROBE` (observe actual token behavior once issued) | `P2-B` | before `G1`, confirmed at `G2` | `P2-B` ADR finalization, `G1` |
| 7 | Account/entitlement contract: approved account types, market-data latency, routes, quotas | `OPERATOR_DECISION` (account setup is a business action) | `READ_ONLY_AUTHENTICATED_PROBE` | `P2-A`, `P2-C` (environment scoping) | before `G1`, confirmed at `G2` | `G1` |
| 8 | Confirmation semantics: whether required, validity window, price-binding | `SIM_EXPERIMENT` | `DOCS_ONLY` (partially — validity-window text not yet found in any reviewed page) | `P2-A` round 1 (docs re-check), `P2-H` | `G3` | `P2-G` |
| 9 | Batch atomicity: group/OSO responses mixing orders and errors | `SIM_EXPERIMENT` | — | `P2-H` | `G3` | `P2-G`, `P2-I` |
| 10 | Rate-limit identity: quota aggregation across processes/keys/accounts | `OPERATOR_DECISION` (depends on chosen deployment topology and number of API keys) | `READ_ONLY_AUTHENTICATED_PROBE` (`X-RateLimit-*` headers) | `P2-B`, `P2-C` | before `G1`, confirmed at `G2` | `P2-D` retry/backoff design |
| 11 | Decimal/time semantics: precision, rounding, tick size, timezone per asset class | `DOCS_ONLY` (Symbol/Quote endpoint schemas not yet fully cross-referenced) | `READ_ONLY_AUTHENTICATED_PROBE` (observed tick/precision in live symbol responses) | `P2-A` round 1 | none for the docs part; `G2` for confirmation | `P2-E` canonical-decimal mapping |
| 12 | Retention: availability beyond the 90-day historical-order window and 600-item limits at scale | `OPERATOR_DECISION` (organizational retention policy) | `DOCS_ONLY` (check for an export/archive API) | `P2-A` round 1, Operator retention policy | none | `P2-J` reporting retention design |

No item is resolved by this plan. Rows marked `OPERATOR_DECISION` cannot be
closed by any agent: contacting TradeStation Client Experience or setting
organizational retention policy is a human/business action outside every
agent's authority (`AGENT_AUTHORITY.md` §"Global boundaries").

## 6. Agent roles

Every role inherits the global boundaries in `AGENT_AUTHORITY.md`
unconditionally: no credentials, no live-capital path, no self-approval of
its own ADR, no silent defaulting, no "escalation trigger" bypass. The
model-cost ladder referenced below is an ordinal, relative planning
estimate — not a metered price — anchored to the Cursor model catalog's
reasoning-tier scaling; it must be reconciled against actual Cursor pricing
before execution:

`composer-2.5` ≈ 1× (mechanical baseline) < `gpt-5.6-sol-low` ≈ 2× <
`gpt-5.6-sol-medium` ≈ 3× < `grok-4.7-high` ≈ 6× ≈ `gpt-5.6-sol-high` ≈ 6× <
`claude-sonnet-5-thinking-high` ≈ 7× < `gpt-5.6-sol-xhigh` ≈ 10× <
`claude-opus-5-thinking-high` ≈ 16×.

### 6.1 Coordinator

- **Authority:** scope Phase 2 workstreams, dispatch/sequence the other
  eight roles, reconcile conflicting outputs into `docs/PHASE_2_RECONCILIATION.md`,
  maintain `docs/CURRENT_STATE.md`/`docs/ENGINEERING_JOURNAL.md` updates,
  draft (never accept) ADRs, enforce every gate in §8.
- **Forbidden:** performing a specialist workstream in place of its owner;
  self-approving any ADR; editing `src/`, `migrations/`, or `tests/`;
  advancing past a gate without the required evidence/Operator action.
- **Owned files:** `docs/PHASE_2_PLAN.md` (this document's future
  revisions), `docs/PHASE_2_RECONCILIATION.md`, `docs/CURRENT_STATE.md`
  (Phase 2 section only), `docs/ENGINEERING_JOURNAL.md` (append-only
  entries).
- **Contracts consumed:** `AGENT_AUTHORITY.md`, `DECISIONS.md`, every
  `P2-*` deliverable.
- **Dependencies:** none upstream; all eight other roles report to it.
- **Model class:** `HIGH_REASONING`.
- **Exact model:** `gpt-5.6-sol-high` (routine gate enforcement); escalate
  to `claude-opus-5-thinking-high` only at Gates `H2` and `H5` (contract
  freeze and certification decision prep) — justified narrowly by the
  highest-consequence reconciliation points, not by default.
- **Relative cost:** ~6× baseline routine, ~16× at the two escalated gates.
- **Worktree isolation:** owns the integration branch
  `cursor/phase2-coordination-<slug>`; is the only role permitted to open
  cross-workstream merge PRs.
- **Verifier:** the human Operator directly (no agent may verify the
  coordinator's gate-sequencing decisions on its behalf).

### 6.2 Broker researcher

- **Authority:** research public/first-party TradeStation documentation
  (`P2-A`); classify unresolved items per §5's taxonomy; draft the specific
  clarification questions an Operator would need to send TradeStation
  Client Experience.
- **Forbidden:** using an account or credential; exercising an API call of
  any kind; deciding architecture; resolving an `OPERATOR_DECISION` row by
  assumption.
- **Owned files:** `docs/BROKER_CONTRACT.md` addenda (new dated sections,
  never rewriting prior evidence), the resolution-log portion of §5 of this
  plan when superseded by a future dated version.
- **Contracts consumed:** `docs/research/README.md`,
  `.cursor/agents/broker-api-researcher.md`.
- **Dependencies:** none for round 1 (docs-only); round 2 depends on `P2-D`
  Gate `G2` authenticated-probe evidence.
- **Model class:** `HIGH_REASONING`.
- **Exact model:** `gpt-5.6-sol-medium`; escalate to `gpt-5.6-sol-high` only
  for round 2 (reconciling live probe evidence against documentation,
  materially harder than pure literature synthesis).
- **Relative cost:** ~3× round 1, ~6× round 2.
- **Worktree isolation:** `cursor/phase2-a-broker-research-<slug>`.
- **Verifier:** `verification` role, using a distinct model
  (`claude-sonnet-5-thinking-high`), confirming every claim carries a
  citation with an access date and that no account/credential/network
  action occurred.

### 6.3 Security/auth architect

- **Authority:** design the OAuth/token/secret-management architecture
  (`P2-B`); define the network-isolation policy (SIM-host allowlist,
  LIVE-host denylist); specify the approved secret-manager pattern (Cursor
  Dashboard secrets or equivalent, never repository files); draft the
  `AUTH_ARCHITECTURE.md` ADR.
- **Forbidden:** requesting, generating, or handling any real credential
  before Gate `G1`; weakening `SIM_LIVE_BOUNDARY.md`; approving its own
  ADR; allowing a LIVE fallback path to exist even as dead code.
- **Owned files:** `docs/AUTH_ARCHITECTURE.md` (new).
- **Contracts consumed:** `docs/SIM_LIVE_BOUNDARY.md`,
  `docs/AGENT_AUTHORITY.md`, `docs/BROKER_CONTRACT.md` items 6/7/10.
- **Dependencies:** `P2-A` round 1 (auth-conflict flags) for its research
  round; Gate `G1` for the credential-provisioning step itself, which the
  Operator performs, not this role.
- **Model class:** `HIGH_REASONING`.
- **Exact model:** `gpt-5.6-sol-xhigh` — justified because this is the
  single highest-consequence role in the entire program (the last design
  layer before any real credential exists); the elevated tier is warranted
  by consequence severity, not task volume, and task volume for this role
  is deliberately small.
- **Relative cost:** ~10×, applied to a small, tightly scoped task set.
- **Worktree isolation:** `cursor/phase2-b-auth-architecture-<slug>`.
- **Verifier:** `verification` role using `grok-4.7-high` specifically (a
  third, vendor-diverse model family) to cross-check this role's own
  model-family blind spots on the highest-stakes artifact in the plan.

### 6.4 DB/deployment engineer

- **Authority:** produce the managed-PostgreSQL comparison
  (`docs/DB_DEPLOYMENT.md`, `P2-C`); design DEV/TEST/SIM/LIVE
  connection-string and environment-separation contracts; scaffold
  non-secret configuration templates (docker-compose profiles, Alembic
  `env.py` parameterization, `.env.example` extensions).
- **Forbidden:** creating any live cloud resource; selecting a provider on
  the Operator's behalf; storing any credential/connection secret in the
  repository; provisioning anything.
- **Owned files:** `docs/DB_DEPLOYMENT.md` (new), non-secret
  `docker-compose*.yml` profile additions, `.env.example` additions,
  `migrations/env.py` parameterization (config only, no schema change).
- **Contracts consumed:** `docs/ARCHITECTURE.md` §"Storage and consistency
  boundaries", `docs/DATA_MODEL.md`, `pyproject.toml`.
- **Dependencies:** none for the comparison (`P2-C` round 1); environment
  scaffolding (round 2) depends on `P2-B`'s network-isolation policy.
- **Model class:** mixed. Comparison research: `HIGH_REASONING`
  (`gpt-5.6-sol-medium`, ~3×). Config/template scaffolding:
  `ROUTINE_IMPLEMENTATION` (`composer-2.5`, ~1×).
- **Worktree isolation:** `cursor/phase2-c-db-deployment-<slug>`.
- **Verifier:** `verification` role (`claude-sonnet-5-thinking-high`)
  confirms no secret, connection string, or provider SDK import was added,
  and that the comparison contains no selection.

### 6.5 Broker client

- **Authority:** design and (post-freeze) implement the read-only
  connectivity contract and typed client skeleton (`P2-D`); design and
  implement the DTO-normalization mapping layer (`P2-E`), including the
  quarantine store for schema-invalid/unmappable observations.
- **Forbidden:** any network call before Gate `G2`; any
  place/replace/cancel code path ever, at any gate, in this role (that is
  `execution`'s scope, not this role's); silently coercing an `UNKNOWN`
  field.
- **Owned files:** `src/swingtrade/broker/` read-only client and mapper
  modules (new package, post-freeze only), `docs/DTO_MAPPING.md` (new).
- **Contracts consumed:** `docs/DATA_MODEL.md`, `docs/EVENT_MODEL.md`,
  `docs/BROKER_CONTRACT.md`, `docs/SIM_LIVE_BOUNDARY.md` §"Enforcement
  contract".
- **Dependencies:** `P2-A` clarified facts for read-model items 3/4/11;
  Gate `H2` contract freeze before any code; Gate `G1`/`G2` before any
  network-capable code path is enabled.
- **Model class:** mixed. Contract design: `HIGH_REASONING`
  (`gpt-5.6-sol-medium`, ~3×; escalate to `gpt-5.6-sol-high` only if a
  resolved schema proves materially ambiguous). Mapper/skeleton
  implementation against fixtures: `ROUTINE_IMPLEMENTATION`
  (`composer-2.5`, ~1×).
- **Worktree isolation:** `cursor/phase2-d-read-only-connectivity-<slug>`
  and `cursor/phase2-e-dto-normalization-<slug>` (separate worktrees per
  workstream even though the same role owns both).
- **Verifier:** `verification` role runs the same credential/network-import
  static scan pattern used at Phase 1 Gate B against every commit from this
  role, at every round, not only at the final gate.

### 6.6 Execution

- **Authority:** design and (post-freeze, pre-`G3` as contract; at/after
  `G3` as implementation) the submission-safety/idempotency extension
  (`P2-G`) covering `OrderConfirmID` key derivation and ambiguous-outcome
  recovery; run the bounded SIM order-harness test matrix (`P2-H`) jointly
  with `verification` after Gate `G3`.
- **Forbidden:** enabling any live-capable dispatch path at any point;
  weakening `authorize_dispatch`'s exact-identity/expiry/replay/reporting
  checks; submitting a SIM order before `G3`; ever submitting a LIVE order.
- **Owned files:** `src/swingtrade/broker.py` and `src/swingtrade/safety.py`
  extensions (post-freeze only), `docs/IDEMPOTENCY.md` broker addendum.
- **Contracts consumed:** `docs/IDEMPOTENCY.md`, `docs/TRADE_LIFECYCLE.md`,
  `docs/SIM_LIVE_BOUNDARY.md`, the existing `authorize_dispatch` contract in
  `src/swingtrade/safety.py`.
- **Dependencies:** `P2-A` items 1/2/8/9; `P2-D`/`P2-E` contracts frozen at
  `H2`; Gate `G3` for any actual SIM order call.
- **Model class:** `HIGH_REASONING`.
- **Exact model:** `gpt-5.6-sol-high` — justified directly by precedent:
  the equivalent Phase 1E code (`safety.py`/`persistence.py`'s dispatch
  path) required six remediation rounds (F01–F06) before independent
  verification passed; this role extends exactly that code class and must
  meet the same bar from the outset.
- **Relative cost:** ~6×.
- **Worktree isolation:** `cursor/phase2-g-submission-safety-<slug>` and,
  after `G3`, `cursor/phase2-h-sim-harness-<slug>`.
- **Verifier:** `verification` role (`claude-opus-5-thinking-high` at Gate
  `H3` and again before any Gate `G3` action — the two highest-consequence
  checkpoints for this role).

### 6.7 Reconciliation

- **Authority:** extend `docs/RECONCILIATION.md`'s check layers to compare
  internal ledger state against broker read-model snapshots (`P2-F`);
  extend the discrepancy severity taxonomy for broker-specific cases
  (entitlement mismatch, stale broker snapshot, ambiguous batch result).
- **Forbidden:** auto-correcting, cancelling, or offsetting any order to
  repair drift; treating an unreconciled high-water mark as `PASS`;
  inferring a fact not present in a `reconciliation.check_completed.v1`
  event.
- **Owned files:** `src/swingtrade/reconciliation.py` extension
  (post-freeze only), `docs/RECONCILIATION.md` broker addendum.
- **Contracts consumed:** `docs/RECONCILIATION.md`, `docs/EVENT_MODEL.md`,
  `docs/DATA_MODEL.md`.
- **Dependencies:** `P2-E`'s DTO shapes (frozen at `H2`); real broker
  snapshots only become available after Gate `G2`.
- **Model class:** `HIGH_REASONING`.
- **Exact model:** `gpt-5.6-sol-high` — justified on the same basis as
  `execution`: reconciliation is explicitly the fail-closed authority
  boundary ("detect disagreement; do not manufacture agreement"), so errors
  here can silently mask position/cash drift.
- **Relative cost:** ~6×.
- **Worktree isolation:** `cursor/phase2-f-broker-reconciliation-<slug>`.
- **Verifier:** `verification` role (`claude-opus-5-thinking-high` at Gate
  `H4`, the first checkpoint using real SIM read-model data).

### 6.8 Verification

- **Authority:** independently re-run tests, contract validators, and
  credential/network static scans against every other role's output at
  every `H`-gate; extend `tests/validate_phase1_contracts.py` into
  `tests/validate_phase2_contracts.py`; assemble the `SIM_CERTIFICATION.md`
  evidence packs (`P2-I`) working with the coordinator and the named human
  owners.
- **Forbidden:** authoring the contract or code it verifies; self-approving
  its own findings; modifying producer code beyond flagging a defect;
  sharing a model/session instance with the role it is verifying in the
  same gate.
- **Owned files:** `tests/validate_phase2_contracts.py` (new),
  independent verification reports under this Agent Store's `internal/`
  equivalent for the target repository (or a repository-local
  `docs/PHASE_2_VERIFICATION_*.md` evidence file per gate).
- **Contracts consumed:** every `P2-*` deliverable; `docs/TEST_PLAN.md`;
  the Phase 1 Gate A/B verification method as precedent
  (`docs/PHASE_1_CLOSURE.md` §2).
- **Dependencies:** whatever it is verifying at that gate; always runs
  after the producing role, never before.
- **Model class:** `HIGH_REASONING`.
- **Exact model:** `claude-sonnet-5-thinking-high` by default (~7×);
  `claude-opus-5-thinking-high` (~16×) specifically at Gates `H3` and `H5`
  (the Gate-A-equivalent full-suite verification and the certification
  sign-off review); `grok-4.7-high` (~6×) specifically when verifying the
  security/auth architect's output, for vendor-family diversity.
- **Worktree isolation:** operates from a read-only checkout of the
  producing role's worktree; never commits to a producer's branch; posts
  findings to the coordinator's integration branch only.
- **Verifier of the verifier:** the human Operator, who reviews every
  verification report before any gate is declared passed.

### 6.9 Monitoring/reporting

- **Authority:** enumerate and (post-freeze) implement new
  metrics/alert/dashboard requirements for broker-connectivity events
  (`P2-J`); extend `docs/MONITORING.md`, `docs/METRICS.md`,
  `docs/REPORTING.md` addenda for the broker-state and SIM-order event
  families introduced by `P2-D`–`P2-H`.
- **Forbidden:** suppressing, muting, or raising the severity threshold of
  any existing safety alert without Operator sign-off; putting a
  credential, account identifier, or raw broker payload in a metric label
  or log field (per `MONITORING.md` §"Signals").
- **Owned files:** `docs/MONITORING.md`, `docs/METRICS.md`,
  `docs/REPORTING.md` broker addenda; dashboard-as-code
  configuration (new, non-secret).
- **Contracts consumed:** `docs/MONITORING.md`, `docs/METRICS.md`,
  `docs/REPORTING.md`.
- **Dependencies:** event/alert taxonomy design can start in Group 1
  (§8) with no upstream dependency; implementation depends on `P2-D`–`P2-H`
  emitting the events it displays.
- **Model class:** mixed. Alert-taxonomy/severity design:
  `HIGH_REASONING` (`gpt-5.6-sol-medium`, ~3×). Metrics/dashboard wiring:
  `ROUTINE_IMPLEMENTATION` (`composer-2.5`, ~1×).
- **Worktree isolation:** `cursor/phase2-j-monitoring-reporting-<slug>`.
- **Verifier:** `verification` role confirms no sensitive field reaches a
  label/dashboard and that no safety-alert threshold was silently changed.

## 7. Workstreams `P2-A` … `P2-J`

Each workstream's "prohibitions" column is a subset of, never an exception
to, §3's preserved invariants.

### 7.1 `P2-A` — TradeStation broker-behavior resolution

- **Owning role:** broker researcher.
- **Purpose:** progress the 12 unresolved items (§5) as far as `DOCS_ONLY`
  and `OPERATOR_DECISION` classifications allow, and hand off precise
  `READ_ONLY_AUTHENTICATED_PROBE`/`SIM_EXPERIMENT` questions for later
  rounds.
- **Deliverable:** `docs/BROKER_CONTRACT.md` addendum with re-verified
  citations and the §5 classification table.
- **Depends on:** nothing (round 1); Gate `G2` evidence (round 2); Gate `G3`
  evidence (round 3, feeding `P2-I`).
- **Prohibitions:** no account, credential, or API call at any round; no
  resolving an `OPERATOR_DECISION` row by assumption.
- **Acceptance criteria:** every one of the 12 items carries an updated
  citation with an access date; the classification table matches §5's
  taxonomy exactly; independent verifier finds zero credential/network
  primitives in the diff.

### 7.2 `P2-B` — OAuth / auth & secrets architecture

- **Owning role:** security/auth architect.
- **Purpose:** design (not implement) token lifecycle handling, scope
  minimization, secret storage, and network isolation for a future
  TradeStation SIM connectivity phase.
- **Deliverable:** `docs/AUTH_ARCHITECTURE.md` (Proposed ADR, mirroring
  `docs/adr/ADR-TEMPLATE.md`).
- **Depends on:** `P2-A` round 1 (auth-conflict flags, item 6/7/10).
- **Prohibitions:** no real credential, secret manager account, or OAuth
  client registration before Gate `G1`; no design that leaves a
  LIVE-reachable path, even disabled by default.
- **Acceptance criteria:** ADR explicitly enumerates every remaining
  auth-related unresolved item as a listed risk, not a silent assumption;
  independent verifier confirms the design's fail-closed behavior on every
  named failure mode (expired token, revoked refresh token, wrong host,
  missing scope); Operator review (not acceptance) closes this round.

### 7.3 `P2-C` — Managed PostgreSQL decision framework

- **Owning role:** DB/deployment engineer.
- **Purpose:** carry §4's comparison into a standalone, versioned contract
  document and design (not provision) DEV/TEST/SIM/LIVE database
  connection-string separation.
- **Deliverable:** `docs/DB_DEPLOYMENT.md`.
- **Depends on:** nothing (round 1, comparison); `P2-B`'s network-isolation
  policy (round 2, environment separation).
- **Prohibitions:** no provider selection; no cloud resource creation; no
  secret/connection string in the repository.
- **Acceptance criteria:** matrix contains no ranking or recommendation of
  a single winner; every figure is cited with an access date; the
  environment-separation design shows exactly one connection-string source
  per environment with no fallback/default across environments.

### 7.4 `P2-D` — Read-only broker connectivity design & skeleton

- **Owning role:** broker client.
- **Purpose:** define the typed, broker-neutral read-only client interface
  (accounts, balances, positions, orders, market data/streams) with a
  fail-closed SIM-host allowlist and LIVE-host denylist; implement the
  skeleton against mocks/fixtures only until Gate `G2`.
- **Deliverable:** client interface + fixture-based tests (pre-`G2`);
  first authenticated read-only calls (post-`G1`, marking Gate `G2` itself).
- **Depends on:** `P2-A` (items 3/4/11), Gate `H2` contract freeze
  (pre-code), Gate `G1` (before any network-capable build), Gate `G2`
  (before any real call).
- **Prohibitions:** no write/order endpoint ever in this workstream's code
  paths; no host other than the documented SIM base URL
  (`https://sim-api.tradestation.com/v3`) reachable by the client, checked
  by a static test, not a runtime flag.
- **Acceptance criteria:** static inspection proves zero LIVE-host string
  anywhere in the module; fixture tests cover every documented read
  endpoint's success and `Errors`-array-present shapes (`BROKER_CONTRACT.md`
  finding 16); at Gate `G2`, the first real call is read-only, logged, and
  its raw response is retained as a provenance-tagged observation before
  any domain mapping occurs.

### 7.5 `P2-E` — DTO normalization contract

- **Owning role:** broker client.
- **Purpose:** map raw TradeStation JSON into the existing broker-neutral
  domain (`OrderObservation`, `Fill`, `PositionSnapshot` from
  `DATA_MODEL.md`) with mandatory `UNKNOWN` fallback and a quarantine store
  for schema-invalid or unmappable payloads (`EVENT_MODEL.md` §"Append and
  delivery semantics").
- **Deliverable:** `docs/DTO_MAPPING.md`; mapper modules (post-freeze).
- **Depends on:** `P2-A` (items 3/11), `P2-D`'s client interface.
- **Prohibitions:** no field coercion; no silent default for a missing or
  unrecognized enum value; no raw broker field leaking into the domain
  envelope as undocumented semantics (`EVENT_MODEL.md` §"Evolution").
- **Acceptance criteria:** every documented TradeStation status code not
  in the closed enum maps to `UNKNOWN`, never guessed; a schema-invalid
  observation always lands in the quarantine store with digest and
  metadata and emits no trusted domain fact; independent verifier
  round-trips at least one fixture per documented endpoint shape.

### 7.6 `P2-F` — Broker state/query reconciliation extension

- **Owning role:** reconciliation.
- **Purpose:** extend `RECONCILIATION.md`'s ledger/projection/execution
  check layers to compare internal state against broker read-model
  snapshots, and extend the severity taxonomy for broker-specific
  discrepancies.
- **Deliverable:** `docs/RECONCILIATION.md` broker addendum; extension code
  (post-freeze).
- **Depends on:** `P2-E`'s DTO shapes; real snapshots available only after
  Gate `G2`.
- **Prohibitions:** no auto-repair, cancel, or offset of any order; no
  `PASS` result without a qualifying `reconciliation.check_completed.v1`
  event exactly as `RECONCILIATION.md` §"Completion evidence" requires.
- **Acceptance criteria:** every new discrepancy case type from §5
  (entitlement mismatch, stale snapshot, ambiguous batch result) has a
  documented severity and a test that proves dispatch inhibition on
  `CRITICAL`/`HIGH`; rebuild-from-ledger recovery is proven for the new
  case types exactly as for the existing ones.

### 7.7 `P2-G` — Submission safety & idempotency extension

- **Owning role:** execution.
- **Purpose:** extend `IDEMPOTENCY.md`'s key-construction/retry contract
  and `safety.py`'s `authorize_dispatch` pattern to a future broker-capable
  adapter, covering `OrderConfirmID` derivation and ambiguous-outcome
  (503/504/disconnect) recovery.
- **Deliverable:** `docs/IDEMPOTENCY.md` broker addendum; extension code
  (contract frozen pre-`G3`, implementation and empirical tuning at/after
  `G3` using `P2-H`'s findings).
- **Depends on:** `P2-A` (items 1/2/8/9), `P2-D`/`P2-E` frozen contracts;
  Gate `G3` for any real SIM order call this workstream's code would issue.
- **Prohibitions:** no code path that could reach a LIVE endpoint at any
  point, verified structurally, not by configuration; no retry that could
  duplicate a logical effect; no assumption about `OrderConfirmID`
  semantics not yet confirmed by `P2-A`/`P2-H`.
- **Acceptance criteria:** identical to the bar `safety.py`/`persistence.py`
  already met in Phase 1E (exact-identity, expiry, replay, and reporting
  denial; canonical, resource-bounded decimal handling); independent
  verifier reproduces the same class of fault-injection tests
  (crash-before-effect, crash-after-effect-before-record, lease expiry,
  key-conflict) against the extension.

### 7.8 `P2-H` — SIM harness

- **Owning role:** execution, jointly with verification.
- **Purpose:** run the bounded SIM order-lifecycle test matrix (confirm,
  place, replace, cancel, group/OCO, idempotent retry, ambiguous-outcome
  recovery) strictly after Gate `G3`, with zero real-capital exposure by
  construction (SIM uses fake money per `BROKER_CONTRACT.md` finding 2).
- **Deliverable:** SIM harness test suite and its results, feeding `P2-A`
  round 3 and `P2-I`'s evidence packs.
- **Depends on:** Gate `G3`; `P2-G`'s frozen submission-safety contract;
  `P2-D`/`P2-E` operating correctly against real SIM data (proven at Gate
  `H4`).
- **Prohibitions:** no LIVE host reachable at any point (structurally, not
  by configuration); no test that could plausibly touch a non-SIM account;
  no interpreting a SIM result as evidence of LIVE fidelity
  (`BROKER_CONTRACT.md` finding 3: SIM's instant-fill model cannot
  establish realistic latency/slippage/queue-position behavior).
- **Acceptance criteria:** every one of the bounded test cases in
  `SIM_CERTIFICATION.md` §"Future entry criteria" ("approved bounded query,
  confirmation, simulated order, replace/cancel, stream, ambiguity, and
  reconciliation test cases") is present with a passing, reproducible
  result and zero real-capital path.

### 7.9 `P2-I` — Failure & safety certification

- **Owning role:** verification, coordinating with named human owners.
- **Purpose:** assemble the nine required `SIM_CERTIFICATION.md` evidence
  packs (build, determinism, correctness, safety, resilience,
  reconciliation, operations, research, authenticated-SIM-contract).
- **Deliverable:** the completed evidence bundle and, if the named human
  owners sign off, a certification record in `docs/CURRENT_STATE.md` that
  is explicitly bounded — SIM only, never LIVE-authorizing
  (`SIM_CERTIFICATION.md` §"Explicit non-consequence").
- **Depends on:** `P2-D` through `P2-H` complete and independently
  verified.
- **Prohibitions:** no certification claim beyond the exact bounded scope
  `SIM_CERTIFICATION.md` allows; no waiver of `LIVE` denial or ledger
  integrity, ever, under any evidence.
- **Acceptance criteria:** zero safety blockers; zero unresolved
  critical/high reconciliation cases; reproducibility demonstrated in an
  independent clean environment; signed approval by named system, risk,
  security, and release owners — these are operational attestations, not
  additional Phase-1/Phase-2 acceptance deciders (`AGENT_AUTHORITY.md`).

### 7.10 `P2-J` — Monitoring & reporting extension

- **Owning role:** monitoring/reporting.
- **Purpose:** extend `MONITORING.md`/`METRICS.md`/`REPORTING.md` for the
  new broker-connectivity, DTO-quarantine, broker-reconciliation, and
  SIM-order event families.
- **Deliverable:** contract addenda and dashboard/alert wiring.
- **Depends on:** taxonomy design has no upstream dependency (Group 1);
  wiring depends on `P2-D`–`P2-H` emitting the events displayed.
- **Prohibitions:** no credential, account identifier, or raw broker
  payload in any metric label, log field, or dashboard
  (`MONITORING.md` §"Signals"); no silent change to an existing safety
  alert's severity or routing.
- **Acceptance criteria:** every new alert class has a stable code,
  severity, runbook reference, and evidence link exactly as
  `MONITORING.md` §"Alert quality" requires; contract tests verify bounded
  cardinality on every new metric label set.

## 8. Dependency DAG

```
Group 1 (parallel, no credentials/network — this is P2-0, §9)
  P2-A/r1  P2-B/r1(research)  P2-C/r1  P2-J/r1(taxonomy)
        \      |         |        /
         v     v         v       v
Gate H1 -- Contract Draft Review (coordinator + verification)
        |
        v
Group 2 (parallel, still no credentials/network)
  P2-B/r2(ADR draft)  P2-D/r1(design)  P2-E/r1(design)  P2-F/r1(design)
  P2-G/r1(design)     P2-C/r2(env-separation design)
        \___________________|___________________/
                            v
Gate H2 -- CONTRACT FREEZE == HUMAN DECISION GATE 1
           (Operator accepts P2-B/P2-D/P2-E/P2-F/P2-G design ADRs
            in docs/CURRENT_STATE.md; independent verifier confirms
            no credential/network primitive exists anywhere yet)
        |
        v
Group 3 (parallel, DRY_RUN/fixture-only implementation)
  P2-D/r2(skeleton impl)  P2-E/r2(mapper impl)  P2-F/r2(reconciliation impl)
  P2-G/r2(safety impl)    P2-C/r3(config scaffolding)   P2-J/r2(wiring)
        \___________________|___________________/
                            v
Gate H3 -- INDEPENDENT VERIFICATION (Gate-A-equivalent full re-run:
           tests + contract validator + credential/network scans)
        |
        +---------------------------------------------------------+
        |                                                         |
        v                                                         v
HUMAN DECISION GATE 2 -- Managed PostgreSQL selection ADR      (parallel,
   (Operator selects/defers a P2-C candidate; NOT required      not blocking
    before SIM certification since local docker-compose          SIM path)
    Postgres remains sufficient through P2-I)
        |
        v
Gate G1 -- CREDENTIAL BOUNDARY (human action + independent security
           attestation: Operator provisions SIM OAuth credentials via
           Cursor Dashboard secrets, formally accepts P2-B's ADR if not
           already accepted at H2, authorizes a new "TradeStation SIM
           connectivity phase" explicitly in docs/CURRENT_STATE.md)
        |
        v
Group 4 (sequential within, first real network/broker activity ever)
  P2-D/r3 -- Gate G2: AUTHENTICATED_PROBE_BOUNDARY
             (first authenticated READ-ONLY call: token exchange +
              GET accounts/balances/positions/orders; every response
              retained as a quarantined, provenance-tagged observation)
  P2-A/r2 (reconcile probe evidence against docs)
  P2-F/r3 (reconcile broker read-model against ledger using real SIM
           read-only snapshots for the first time)
        |
        v
Gate H4 -- READ-ONLY CERTIFICATION CHECKPOINT
           (verifier confirms zero write/order calls occurred)
        |
        v
Gate G3 -- SIM-ORDER BOUNDARY (human authorization, scoped + expiring,
           per SIM_CERTIFICATION.md "Future entry criteria"; requires
           P2-G's frozen submission-safety contract and P2-I's evidence-
           pack skeleton to already exist)
        |
        v
Group 5 (first and only order-capable activity in this entire plan,
         SIM only, zero real capital)
  P2-H (bounded SIM order harness: confirm/place/replace/cancel/OCO/
        idempotent retry/ambiguous-outcome recovery)
  P2-G/r3 (finalize submission-safety contract against real SIM findings)
  P2-I/r1 (assemble the 9 certification evidence packs)
        |
        v
Gate H5 -- SIM CERTIFICATION DECISION
           (named human owners sign off; Operator records a bounded
            SIM-only certification in docs/CURRENT_STATE.md;
            explicitly does NOT authorize LIVE)
        |
        v
Group 6 -- Close-out
  P2-J/r3 (finalize monitoring/reporting against certified SIM data)
  Coordinator publishes Phase 2 closure evidence, restating: LIVE remains
  unauthorized; any future LIVE promotion is a fully separate, later,
  conjunctively-gated Operator decision under docs/LIVE_PROMOTION.md,
  untouched by everything above.
```

Gate/boundary index: `H1`–`H5` are review/verification gates (coordinator +
verification role, no Operator credential action required except where
noted); `G1`–`G3` are the credential, authenticated-probe, and SIM-order
boundaries specifically called out by this task (each requires an explicit,
human, non-agent action); the two labeled "HUMAN DECISION GATE" points are
ADR-acceptance/selection decisions reserved to the Operator alone. No agent
role may cross `G1`, `G2`, or `G3` on its own initiative under any
instruction, per `AGENT_AUTHORITY.md`'s non-overridable authority rule.

## 9. Smallest first executable slice — `P2-0`

`P2-0` is exactly Group 1 of §8, minimized further to the smallest set of
deliverables that unblocks every later group without any code, credential,
or network action.

- **Exact scope (4 deliverables, 4 isolated worktrees):**
  1. Broker researcher — `docs/BROKER_CONTRACT.md` addendum re-verifying
     all 12 items against current TradeStation documentation and applying
     §5's classification table (already drafted in this plan; the
     workstream's job is to promote it into `BROKER_CONTRACT.md` itself as
     a dated, cited addendum).
  2. DB/deployment engineer — `docs/DB_DEPLOYMENT.md` seeded from §4's
     comparison matrix, with no selection.
  3. Security/auth architect — `docs/AUTH_ARCHITECTURE.md` research section
     only (options and risks, no ADR acceptance, no credential).
  4. Coordinator (with DB/deployment engineer) — extend
     `config/README.md`/`.env.example` documentation with a DEV/TEST/SIM/LIVE
     naming convention for future connection-string environment variables
     (documentation only; no new runtime code, no new required variable,
     no provisioning).
- **Agents/models:** broker researcher (`gpt-5.6-sol-medium`, ~3×);
  DB/deployment engineer (`gpt-5.6-sol-medium` for the comparison, ~3×;
  `composer-2.5` for the `.env.example`/`config/README.md` doc edit, ~1×);
  security/auth architect (`gpt-5.6-sol-xhigh`, ~10×, applied to a small,
  bounded research task only); coordinator (`gpt-5.6-sol-high`, ~6×, for
  reconciling the four outputs into `docs/PHASE_2_RECONCILIATION.md`).
- **Outputs:** `docs/BROKER_CONTRACT.md` addendum,
  `docs/DB_DEPLOYMENT.md`, `docs/AUTH_ARCHITECTURE.md` (research section),
  `config/README.md`/`.env.example` documentation update,
  `docs/PHASE_2_RECONCILIATION.md` (coordinator's reconciliation of the
  four).
- **Acceptance criteria:** four new/updated docs exist on four isolated
  worktrees, merged only by the coordinator; zero changes to `src/`,
  `migrations/`, `tests/`, `pyproject.toml`, or any file in the accepted
  Phase 1 45-file manifest; a credential/secret/broker-network-primitive
  static scan (the same pattern used at Phase 1 Gate B) returns zero
  matches across the diff; independent verification role confirms every
  factual claim carries a citation with an access date; Operator reviews
  (does not need to formally accept any ADR yet) before Group 2 begins.
- **Explicit prohibitions:** no credential of any kind; no network call of
  any kind; no broker account action; no ADR acceptance; no
  `docs/CURRENT_STATE.md` phase-authorization change; no managed-database
  provider selection or provisioning; no order-related code of any kind.

## 10. Task classification and model assignment

`HR` = `HIGH_REASONING`, `RI` = `ROUTINE_IMPLEMENTATION`. Cost is the
ordinal ladder from §6 (not a metered price).

| Task | Workstream | Class | Model | Relative cost | Justification |
| --- | --- | --- | --- | --- | --- |
| Re-verify 12 broker items against current docs | `P2-A` r1 | HR | `gpt-5.6-sol-medium` | ~3× | Bounded literature synthesis with citation discipline |
| Draft TradeStation clarification questions | `P2-A` r1 | HR | `gpt-5.6-sol-medium` | ~3× | Same as above |
| Reconcile authenticated-probe evidence vs. docs | `P2-A` r2 | HR | `gpt-5.6-sol-high` | ~6× | Harder: contradictory live evidence vs. static docs |
| Reconcile SIM-order evidence vs. docs | `P2-A` r3 | HR | `gpt-5.6-sol-high` | ~6× | Same difficulty class as r2 |
| Research OAuth/token/secret options | `P2-B` r1 | HR | `gpt-5.6-sol-xhigh` | ~10× | Highest-consequence role; small task volume caps total cost |
| Draft `AUTH_ARCHITECTURE.md` ADR | `P2-B` r2 | HR | `gpt-5.6-sol-xhigh` | ~10× | Same justification |
| Produce managed-Postgres comparison matrix | `P2-C` r1 | HR | `gpt-5.6-sol-medium` | ~3× | Bounded comparative research, same shape as broker research |
| Design DEV/TEST/SIM/LIVE connection-string separation | `P2-C` r2 | HR | `gpt-5.6-sol-medium` | ~3× | Design task, not open-ended |
| Scaffold docker-compose/Alembic config templates | `P2-C` r3 | RI | `composer-2.5` | ~1× | Mechanical templating, no judgment calls |
| `.env.example`/`config/README.md` doc update | `P2-0` | RI | `composer-2.5` | ~1× | Mechanical doc edit |
| Design read-only client interface + host allowlist | `P2-D` r1 | HR | `gpt-5.6-sol-medium` | ~3× | Contract design against known, bounded schemas |
| Implement client skeleton against fixtures | `P2-D` r2 | RI | `composer-2.5` | ~1× | Mechanical once contract is frozen |
| Execute first authenticated read-only probe (Gate `G2`) | `P2-D` r3 | HR | `gpt-5.6-sol-high` | ~6× | First real network/broker action in the program; elevated care warranted |
| Design DTO normalization contract | `P2-E` r1 | HR | `gpt-5.6-sol-medium` | ~3× | Escalate to `gpt-5.6-sol-high` only if a schema proves materially ambiguous |
| Implement DTO mappers + quarantine store | `P2-E` r2 | RI | `composer-2.5` | ~1× | Mechanical once contract is frozen |
| Design broker-state reconciliation extension | `P2-F` r1 | HR | `gpt-5.6-sol-high` | ~6× | Fail-closed authority boundary; same bar as core reconciliation |
| Implement reconciliation extension against fixtures | `P2-F` r2 | HR | `gpt-5.6-sol-high` | ~6× | Still safety-critical even once contract is frozen — not downgraded to RI |
| Reconcile against real SIM read-only snapshots | `P2-F` r3 | HR | `claude-opus-5-thinking-high` | ~16× | First real-data reconciliation run; highest-stakes checkpoint for this role |
| Design submission-safety/idempotency extension | `P2-G` r1 | HR | `gpt-5.6-sol-high` | ~6× | Extends the code class that took 6 remediation rounds in Phase 1E |
| Implement submission-safety extension against fixtures | `P2-G` r2 | HR | `gpt-5.6-sol-high` | ~6× | Same justification, not downgraded |
| Finalize submission-safety contract against real SIM findings | `P2-G` r3 | HR | `gpt-5.6-sol-high` | ~6× | Same justification |
| Run bounded SIM order-harness matrix | `P2-H` | HR | `gpt-5.6-sol-high` | ~6× | Tightly scoped but safety-critical; joint with verification |
| Assemble 9 SIM certification evidence packs | `P2-I` r1 | HR | `claude-sonnet-5-thinking-high` | ~7× | Cross-cutting evidence synthesis across all prior workstreams |
| Enumerate broker-connectivity alert taxonomy | `P2-J` r1 | HR | `gpt-5.6-sol-medium` | ~3× | Bounded design task |
| Implement metrics/alerts/dashboard wiring | `P2-J` r2 | RI | `composer-2.5` | ~1× | Mechanical once taxonomy is frozen |
| Finalize monitoring/reporting against certified data | `P2-J` r3 | RI | `composer-2.5` | ~1× | Mechanical wiring update |
| Coordinator: Gate `H1` contract-draft review | coordination | HR | `gpt-5.6-sol-high` | ~6× | Cross-workstream conflict detection |
| Coordinator: Gate `H2` contract freeze reconciliation | coordination | HR | `claude-opus-5-thinking-high` | ~16× | Highest-stakes reconciliation point before any implementation |
| Coordinator: Gate `H5` certification decision prep | coordination | HR | `claude-opus-5-thinking-high` | ~16× | Highest-stakes reconciliation point before certification |
| Verification: routine per-workstream checks (`H1`, design rounds) | verification | HR | `claude-sonnet-5-thinking-high` | ~7× | Default independent-verification tier |
| Verification: Gate `H3` full independent re-verification | verification | HR | `claude-opus-5-thinking-high` | ~16× | Gate-A-equivalent; historically required the highest rigor in Phase 1 |
| Verification: Gate `H5` certification sign-off review | verification | HR | `claude-opus-5-thinking-high` | ~16× | Same justification |
| Verification: security/auth artifact cross-check | verification | HR | `grok-4.7-high` | ~6× | Vendor-diverse model family specifically for this artifact |
| Static credential/network scan (every gate) | verification | RI | `composer-2.5` | ~1× | Deterministic grep/AST-style scan, mechanical |

Totals for field 30: **22 `HIGH_REASONING`** tasks, **15
`ROUTINE_IMPLEMENTATION`** tasks (the last row above counts once per gate
occurrence but is one mechanical task type, tallied once here).

## 11. Non-actions of this plan (explicit)

This plan did not, and does not authorize:

- editing `src/`, `migrations/`, `tests/`, `pyproject.toml`, `.cursor/`, or
  any of the 45 files in the accepted Phase 1 manifest;
- moving, retargeting, or creating any git tag;
- accepting, drafting-as-final, or self-approving any ADR;
- selecting or provisioning a managed PostgreSQL provider;
- requesting, generating, storing, or using any TradeStation credential,
  OAuth client, or secret;
- making any TradeStation network call of any kind, read-only or otherwise;
- submitting, confirming, replacing, or cancelling any SIM or LIVE order;
- changing any denial in `docs/CURRENT_STATE.md` or any non-overridable
  rule in `docs/AGENT_AUTHORITY.md`, `docs/SIM_LIVE_BOUNDARY.md`, or
  `docs/LIVE_PROMOTION.md`;
- beginning Phase 2 implementation in any form.

**Phase 2 implementation has NOT been started.** This document is the only
artifact this run produced.

## 12. Evidence and sources

Repository evidence (re-verified live against `origin` before drafting):

- **E1** — `git ls-remote`/`git fetch origin main phase1-complete`; `main` =
  `origin/main` = `249b8eb341b56d596f07b28723b37ddff96eb86c`; tag
  `phase1-complete` resolves to the same commit. Accessed 2026-09-26.
- **E2** — `docs/PHASE_1_CLOSURE.md` at that commit (full text read).
- **E3** — `docs/BROKER_CONTRACT.md` at that commit (full text read,
  including the 12-item `BROKER_BEHAVIOR_UNRESOLVED` list and its S1–S8
  citations).
- **E4** — `docs/AGENT_AUTHORITY.md`, `docs/CURRENT_STATE.md`,
  `docs/DECISIONS.md`, `docs/SIM_LIVE_BOUNDARY.md`, `docs/LIVE_PROMOTION.md`,
  `docs/RECONCILIATION.md`, `docs/IDEMPOTENCY.md`, `docs/SIM_CERTIFICATION.md`,
  `docs/MONITORING.md`, `docs/DATA_MODEL.md`, `docs/EVENT_MODEL.md`,
  `docs/TRADE_LIFECYCLE.md`, `docs/REPORTING.md`, `docs/METRICS.md`,
  `docs/TEST_PLAN.md`, `docs/ARCHITECTURE.md` (all full text read at that
  commit).
- **E5** — `src/swingtrade/{config,safety,broker,persistence}.py`,
  `pyproject.toml`, `.env.example`, `docker-compose.yml`, `alembic.ini`,
  `.cursor/agents/*.md`, `.cursor/rules/*.mdc`, `config/README.md` (all full
  text read at that commit).

Managed PostgreSQL research (accessed 2026-09-26):

- **E6** — Supabase, "Manage Point-in-Time Recovery usage",
  `https://supabase.com/docs/guides/platform/manage-your-usage/point-in-time-recovery`.
- **E7** — Supabase, "Backups", `https://supabase.com/docs/guides/platform/backups`.
- **E8** — Supabase, "Pricing", `https://supabase.com/pricing`.
- **E9** — Neon, "Connection pooling", `https://neon.com/docs/connect/connection-pooling`.
- **E10** — Neon, "Point-in-time recovery" FAQ (cross-provider PITR
  comparison table), `https://neon.com/faqs/postgres-tools-point-in-time-recovery`;
  Neon, "Branch restore / instant restore", `https://neon.com/docs/introduction/branch-restore`;
  Neon, "Pricing", `https://neon.com/pricing.md`.
- **E11** — AWS, "Restoring a DB instance to a specified time for Amazon RDS",
  `https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PIT.html`.
- **E12** — AWS, "Amazon RDS Backup & Restore", `https://aws.amazon.com/rds/features/backup/`.
- **E13** — AWS, "Introduction to backups",
  `https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.html`.
- **E14** — AWS, "Working with parameters on your RDS for PostgreSQL DB
  instance" and "IAM database authentication for MariaDB, MySQL, and
  PostgreSQL",
  `https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Appendix.PostgreSQL.CommonDBATasks.Parameters.html`,
  `https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html`.
- **E15** — Neon, "Choose your connection", `https://neon.com/docs/connect/choose-connection`.
- **E16** — Neon, "SQLAlchemy guide" and "SQLAlchemy migrations guide",
  `https://neon.com/docs/guides/sqlalchemy`, `https://neon.com/docs/guides/sqlalchemy-migrations`.
- **E17** — Third-party AWS RDS pricing aggregation (list pricing,
  us-east-1, current at capture time; independently cross-checked against
  two additional aggregators), `https://infratally.com/articles/aws-rds-pricing-explained-2026/`,
  `https://cloudprice.net/aws/rds/instances/db.t4g.micro`.
- **E18** — RDS `db.m6g.large` pricing cross-check,
  `https://calculator.holori.com/aws/rds`, `https://instances.cloudchipr.com/aws/rds/db.m6g.large`.
- **E19** — RDS pricing calculator cross-check (Multi-AZ doubling rule),
  `https://www.factualminds.com/tools/aws-rds-pricing-calculator/`.
- **E20** — Google Cloud, "Cloud SQL backups overview",
  `https://cloud.google.com/sql/docs/postgres/backup-recovery/backups`.
- **E21** — Google Cloud, "Perform point-in-time recovery (PITR)",
  `https://cloud.google.com/sql/docs/postgres/backup-recovery/pitr`.
- **E22** — Google Cloud, "Choose your backup option",
  `https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/backup-options`.
- **E23** — Google Cloud, "About instance settings" (`max_connections`
  auto-scaling behavior), `https://docs.cloud.google.cn/sql/docs/postgres/instance-settings`.
- **E24** — Google Cloud, "Configure new and existing instances for IAM
  database authentication",
  `https://docs.cloud.google.com/sql/docs/postgres/create-edit-iam-instances`.

TradeStation research (accessed 2026-09-26, corroborating `docs/BROKER_CONTRACT.md`'s
existing S1–S8 citations with no material change found):

- **E25** — TradeStation, "Auth Code Flow", `https://api.tradestation.com/docs/fundamentals/authentication/auth-code/`.
- **E26** — TradeStation, "Refresh Tokens", `https://api.tradestation.com/docs/fundamentals/authentication/refresh-tokens/`.
- **E27** — TradeStation, "Auth Code Flow With PKCE", `https://api.tradestation.com/docs/fundamentals/authentication/auth-pkce/`.

## 13. Validation performed on this document

- **Scope validation:** every `git`/`grep`/file-read command executed while
  preparing this plan was read-only against the target repository; the
  only write performed by this run is the creation of this single file on
  branch `cursor/phase-2-plan-ec4a`. `git status`/`git diff --stat` against
  `main` show exactly one new file, `docs/PHASE_2_PLAN.md`, and zero
  modified files, confirmed immediately before commit.
- **Link validation:** every URL cited in §12 was fetched or returned in
  live web-search results in this session on 2026-09-26 and is reproduced
  verbatim from that response; none is inferred or reconstructed from
  memory.
- **Internal consistency validation:** every workstream ID (`P2-A`…`P2-J`),
  gate ID (`H1`–`H5`, `G1`–`G3`), and role name used in §5–§10 is defined
  exactly once in §6/§7/§8 and referenced consistently; the field-30 task
  counts in §1 were tallied directly from §10's table.
- **Diff validation:** this document does not alter, quote out of context,
  or contradict any sentence in the 45-file accepted Phase 1 manifest; §3's
  table cites the exact preserved sentences rather than paraphrasing them
  where fidelity mattered.
