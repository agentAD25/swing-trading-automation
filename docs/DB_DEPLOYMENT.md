# Managed PostgreSQL Deployment Decision Research

- Workstream: `P2-C/r1`
- Status: engineering recommendation for Operator consideration; **not an
  accepted ADR and not provider-selection authority**
- Evidence baseline: canonical `main`
  `1ecbbe6d487d97195fde393b05c9499357599bdb`
- Research access date: 2026-09-26
- Task scope: documentation research only; this does not start Phase 2
  implementation
- Execution authority remains: local, deterministic, non-network `DRY_RUN`
  only

## 1. Scope and safety boundary

This document compares Supabase PostgreSQL, Amazon RDS for PostgreSQL, Neon
PostgreSQL, and Google Cloud SQL for PostgreSQL for a future low-volume,
high-correctness trading ledger. It also proposes an environment and
connection-source contract. It does not provision a resource, handle a
credential, make a cloud call, run a migration, select a provider on the
Operator's behalf, accept an ADR, authorize TradeStation `SIM`, or configure
`LIVE`.

The repository currently uses PostgreSQL through SQLAlchemy 2, psycopg 3, and
Alembic ([R1]). The application checks only that the SQLAlchemy dialect is
`postgresql`; this is a useful portability boundary. Local PostgreSQL remains
appropriate for development, deterministic tests, migration rehearsal, and
adversarial/fault testing. It must never be treated as the authoritative copy,
backup, failover target, or recovery source for a future cloud `SIM` or `LIVE`
ledger.

Facts below come from current first-party product documentation and pricing.
Recommendations and targets are explicitly labeled. Undocumented or
contract-dependent properties are marked **UNKNOWN**.

## 2. Decision summary

`PHASE_2_PLAN.md` intentionally made no provider recommendation. This scoped
research task explicitly requests an engineering `RECOMMENDED` /
`ALTERNATIVE` / `DEFERRED` view for Operator consideration. The ranking below
therefore updates the evidence presented for consideration; it does not select
a provider, accept an ADR, authorize procurement, or complete a decision gate.

### RECOMMENDED — Amazon RDS for PostgreSQL, for Operator consideration

For a future authorized `SIM` environment, use an RDS for PostgreSQL Multi-AZ
DB instance with one synchronous standby, private networking only, encrypted
storage, automated backups and seven-day PITR retention. Start with a
burstable Graviton class no smaller than `db.t4g.small` and General Purpose
SSD (`gp3`), subject to a pre-provisioning compatibility and price check. Use
the direct PostgreSQL endpoint, not RDS Proxy, for migrations, long-running
workers, and any session-scoped behavior.

Why this is the engineering preference:

1. RDS documents synchronous cross-Availability-Zone replication, automatic
   failover, and typical 60–120 second failover behavior ([A1], [A2]).
2. It preserves ordinary PostgreSQL transaction, advisory-lock, SQLAlchemy,
   psycopg, Alembic, `pg_dump`, and `pg_restore` semantics through a direct
   connection. No application dependency on an AWS database SDK is required.
3. VPC, subnet, security-group, TLS, Secrets Manager, CloudWatch, database log
   export, maintenance, and upgrade controls form a mature operational set.
4. It has less product-level lock-in than a BaaS or storage-separated
   serverless design if the application continues to avoid provider APIs and
   proprietary extensions.

Material disadvantages:

- Multi-AZ duplicates major compute and storage cost components and can add
  synchronous-commit latency. The standby cannot serve reads ([A1], [A7]).
- Failover closes existing connections and changes the endpoint's DNS target;
  workers must reconnect and must not infer transaction success after a
  disconnect ([A2]).
- Parameter groups, version upgrades, certificates, maintenance windows,
  backups, restore drills, alarms, and cost controls remain the Operator's
  responsibility. This is a moderate operational burden.
- RDS Proxy is an additional paid service with PostgreSQL limitations,
  session pinning concerns, and no client `CancelRequest` support ([A6]). It is
  not justified by this workload's initially low connection count.
- Exact monthly cost is **UNKNOWN** until region, engine version, instance
  class, storage, I/O, backup growth, monitoring, network path, and support
  choices are fixed in the official calculator.

Change triggers: reconsider the recommendation if a pre-provisioning check
shows that the deployment region lacks the required PostgreSQL version or
extensions; measured memory/CPU/connection or I/O load exceeds the proposed
class; cross-AZ commit latency breaches the accepted service objective; the
compute platform is committed to GCP; a restore/failover exercise misses
accepted objectives; or the all-in price is materially above the accepted
budget.

### ALTERNATIVE — Google Cloud SQL for PostgreSQL

Cloud SQL Enterprise edition with regional HA is the strongest alternative,
especially if future application compute is on GCP. It documents synchronous
replication across two zones, a shared static IP through failover, and about
60 seconds of expected failover unavailability ([G1]). It also offers private
IP, Cloud SQL Auth Proxy/connectors, IAM database authentication, Cloud
Monitoring, Cloud Logging, standard or enhanced backups, and PITR.

Its database portability is comparable to RDS when accessed through the
standard PostgreSQL protocol. Operational burden is also comparable. The main
reason it is the alternative rather than co-recommendation is topology: no
future compute cloud or region has been selected. Choosing GCP database
operations before choosing the compute and identity plane would create
avoidable cross-cloud networking, IAM, latency, and egress complexity.

Material disadvantages include approximately doubled HA CPU, memory, and
storage charges, VPC/private-services-access setup, Cloud SQL-specific proxy
and IAM operations if adopted, maintenance/version lifecycle work, and
region-dependent pricing ([G1], [G4], [G6]). Exact monthly cost is **UNKNOWN**.

Change triggers: prefer Cloud SQL if GCP becomes the accepted compute and
identity platform, a same-region private topology is demonstrably simpler,
and failover/restore drills and an official estimate meet the accepted
objectives and budget.

### DEFERRED — Supabase and Neon

Both products remain technically plausible PostgreSQL hosts, but current
evidence does not yet satisfy this ledger's combined recovery, plan-contract,
private-connectivity, and portability requirements.

- **Supabase:** straightforward dedicated PostgreSQL, daily backups, a
  documented two-minute worst-case PITR RPO, direct/session/transaction
  endpoints, and low application burden are positives ([S1]–[S5]). The
  retrievable first-party material does not document a generally available,
  production-supported synchronous multi-AZ database standby or failover
  target comparable to RDS or Cloud SQL. A search index surfaced a “Multigres”
  page, but direct retrieval of the canonical first-party URL returned `404`
  on the same date. Because the underlying page and terms were not
  reproducible, no claim from the search snippet is treated as evidence
  ([S7]).
  PrivateLink and platform audit logs require Team or Enterprise; the Team
  plan starts at $599/month before project compute/PITR adjustments ([S4]).
  Restore makes the project inaccessible for size-dependent, unspecified
  downtime ([S1]). Defer unless Supabase supplies a plan-specific contractual
  HA design, SLA, recovery target, region/network fit, and acceptable quote.
- **Neon:** low usage-based cost, branching, direct and pooled endpoints,
  scale-to-zero, built-in history, multi-AZ WAL quorum, and explicit
  SQLAlchemy and Alembic guidance are positives ([N1]–[N9]). Neon documents
  seconds-level Postgres/VM recovery, 1–2 minute node recovery, and **1–10
  minute** AZ recovery, with reconnect and session-state loss ([N7]). That AZ
  range can miss this document's proposed five-minute `SIM` objective; Neon
  also documents no cross-region replication. Scale is required for IP allow
  rules, Private Networking, metrics/log export, 14-day monitoring, and an
  uptime SLA whose details require contacting support ([N1], [N5]).
  Transaction pooling drops session state and session advisory locks, while
  compute suspension also discards session state ([N2], [N9]). Defer unless
  plan-specific contractual terms meet the accepted objective and the service
  passes always-on direct-connection, transaction, advisory-lock, failover,
  restore, and export drills.

This categorization is advice for an Operator decision. It is not procurement
approval or a durable architecture decision.

## 3. Workload requirements and proposed objectives

The workload is expected to have low query volume but unusually high
correctness requirements:

- an append-oriented event ledger and atomic intent/outbox transaction;
- exact transaction outcome handling after disconnects;
- long-running execution and reconciliation workers;
- bounded connection counts rather than high fan-out;
- predictable PostgreSQL transaction isolation and advisory-lock behavior;
- deterministic schema migration and restore rehearsal;
- durable audit evidence and fail-closed recovery;
- low tolerance for silent data loss, cross-environment writes, or restore
  ambiguity.

### Proposed `SIM` service objectives

These are engineering targets, not provider guarantees and not Operator
acceptance:

| Concern | Proposed minimum |
| --- | --- |
| Availability topology | Synchronous cross-zone HA with automatic failover |
| HA data-loss target | No acknowledged transaction loss for the documented single-instance/single-zone failure model; must be demonstrated, not inferred |
| PITR recovery point | Seven-day recovery window; latest restorable point no more than five minutes behind under an active write probe |
| Failover recovery time | Application usable within 5 minutes of an induced failover |
| Backup restore time | New isolated restore usable and reconciled within 4 hours |
| Restore evidence | Quarterly isolated restore plus row counts, schema head, ledger digest/high-water mark, and reconciliation result |
| Connections | Direct PostgreSQL; bounded pool; reserved operational headroom |
| Encryption | TLS with full server verification; encrypted storage/backups |
| Network | No public database route; explicit workload identity/network path |
| Monitoring | Availability, connections, CPU, memory, storage, I/O, replication/failover, backup/PITR freshness, errors, locks, long transactions, and cost |

The five-minute and four-hour values are proposed project objectives, not
contractual RDS or Cloud SQL claims. The Operator must accept or replace them.
No `LIVE` objective is proposed; `LIVE` remains unconfigured and unauthorized.

## 4. Comparative evidence matrix

| Dimension | Supabase | Amazon RDS PostgreSQL | Neon PostgreSQL | Google Cloud SQL PostgreSQL |
| --- | --- | --- | --- | --- |
| HA/failover | No retrievable generally available production HA contract found; a search-indexed Multigres page returned `404` and is not credited ([S7]) | Multi-AZ provisions synchronous standby in another AZ; automatic failover typically 60–120s, but not a contractual RTO ([A1], [A2]) | Multi-AZ WAL/storage redundancy; compute is recreated/rescheduled: seconds for Postgres/VM, 1–2m node, 1–10m AZ; no cross-region replication ([N7], [N8]) | Regional HA synchronously writes persistent disks in two zones; expected failover interruption about 60s, environment-dependent, not a contractual RTO ([G1]) |
| Backups/PITR | Paid plans: daily backups retained 7/14/up to 30 days. PITR paid add-on, Small compute minimum, worst-case two-minute RPO; restore takes project offline for size-dependent time ([S1], [S2]) | Automated backup retention 0–35 days; logs uploaded every five minutes; PITR creates a new instance ([A3], [A4]) | Root-branch instant restore: 6h Free, up to 7d Launch, 30d Scale; in-place overwrite, backup branch, brief connection interruption; child branches cannot PITR ([N1], [N4]) | Standard/enhanced incremental backups; retention from 1 day to 10 years depending on option; PITR creates a new instance; standalone PITR RPO typically 5m or less ([G1]–[G3]) |
| RPO/RTO status | PITR RPO documented as worst-case 2m; restore RTO **UNKNOWN** | latest-restorable lag derives from 5m log uploads; HA loss target and contractual RTO **UNKNOWN**; typical failover 60–120s | Commit occurs after a WAL quorum acknowledgement; documented recovery ranges are not identified as contractual RTOs; cross-region RPO/RTO **UNKNOWN** ([N7], [N8]) | HA uses synchronous disks; ~60s expected failover; contractual RPO/RTO **UNKNOWN** |
| Regions | One primary region per project; general and exact AWS regions documented; general regions do not support read replicas/API management ([S8]) | Region availability varies by engine version, class, extension, IAM, and proxy; exact combination must be rechecked ([A11], [A12]) | Eight AWS regions listed; project region is immutable and Azure creation is deprecated; products vary by region ([N10]) | Region/edition/machine/feature availability varies; exact combination must be rechecked ([G1], [G4]) |
| Direct connections | Direct is recommended for persistent backends, migrations, dump/restore, replication ([S3]) | Standard SQL clients connect to a private or public PostgreSQL endpoint; private-only is supported ([A13]) | Direct recommended for migrations, dump/restore, logical replication, analytics, session state ([N2]) | Direct private/public IP or connector; Google recommends direct private-IP connectivity with enforced TLS ([G10]) |
| Pooling | Shared session and transaction modes; dedicated transaction pooler on paid plans. Transaction mode loses session state and session advisory locks ([S3]) | Client-side pool by default; optional paid RDS Proxy has session/pinning limitations ([A6]) | PgBouncer transaction mode, 10,000 client limit; session state and session advisory locks unsupported ([N2]) | No mandatory pooler; connector/Proxy is connectivity/auth, not assumed to be a transaction pool |
| Long workers | Direct or session endpoint; not transaction pooler | Direct endpoint; reconnect after failover | Direct endpoint; disable scale-to-zero for predictable workers; pre-ping/recycle stale connections and rebuild session state after failover ([N2], [N3], [N7], [N9]) | Direct/connector path; reconnect after failover |
| Transactions and advisory locks | PostgreSQL semantics are expected on direct/session connections; transaction pooler loses session locks ([S3], [R2]) | Standard PostgreSQL transaction/lock semantics are expected through a direct standard-client connection and must be tested ([A12], [A13], [R2]) | Standard PostgreSQL runs in compute; transaction pooler and compute replacement invalidate session locks ([N2], [N8], [N9], [R2]) | PostgreSQL semantics are expected through a direct connection and must be tested; connector behavior must not be assumed to preserve sessions ([G10], [R2]) |
| SQLAlchemy 2/psycopg/Alembic | Standard PostgreSQL connection; use direct endpoint for migrations; exact stack must be tested ([S3], [R1]) | Standard SQL clients are supported; repository stack remains provider-neutral and requires a compatibility test ([A12], [A13], [R1]) | First-party guides cover SQLAlchemy and Alembic; direct endpoint required for migrations; SQLAlchemy 2.0.33+ stale-connection fix noted ([N3], [N6]) | Direct standard PostgreSQL connectivity requires no provider dialect; repository stack still requires a compatibility test ([G10], [R1]) |
| PostgreSQL features/extensions | More than 50 preconfigured extensions; software upgrade may be required for a newer extension ([S6]) | Curated extension set varies by engine version; custom parameters and privileges are constrained ([A8]) | Plans advertise common extensions, but the exact extension/version matrix for the target region is **UNKNOWN** ([N1]) | Exact extension/version compatibility is **UNKNOWN** and must be checked for the selected engine/edition/region |
| TLS | SSL can be enforced; use `verify-full` and downloaded CA; changing enforcement reboots DB ([S5]) | TLS and server certificate verification supported; AWS manages CA rotation for supported versions ([A5]) | TLS required; `verify-full` supported ([N5]) | TLS through direct certificates or Auth Proxy/connector; exact selected path must require verification |
| Private network/IP | Shared pooler is public IPv4; direct defaults IPv6. PrivateLink is Team/Enterprise ([S3], [S4]) | Private subnets/security groups; no public accessibility required; RDS Proxy must be in same VPC | IP allow and Private Networking require Scale; private transfer $0.01/GB ([N1], [N5]) | Private IP/Private Service Connect; Auth Proxy can use private IP; VPC/IAM setup required ([G5]) |
| Secrets | Password/role secrets; external approved secret manager required | Password auth or 15-minute IAM tokens; IAM has memory, logging, replication, and endpoint limitations ([A11]) | Password/role secrets; Neon recommends a secret manager ([N5]) | Built-in password or one-hour IAM token; automatic connector refresh is recommended for long workers ([G9]) |
| Monitoring/audit | Metrics endpoint on Pro+; platform audit logs Team+; log drains are paid ([S4]) | CloudWatch metrics, Enhanced Monitoring, logs, Database Insights; IAM DB authentication attempts are not logged by CloudWatch/CloudTrail ([A9], [A11]) | Monitoring 1d/3d/14d by plan; logs/metrics export Scale only ([N1]) | System Insights, Cloud Monitoring dashboards/alerts, Logging, and optional paid Data Access audit logs ([G7], [G9]) |
| Maintenance/upgrades | Compute resize and SSL changes cause downtime; extension updates can require software upgrade/restart ([S5], [S6], [S9]) | Maintenance windows; major upgrades manual and can take minutes; minor auto-upgrade optional; blue/green available ([A10]) | Managed compute restarts/reschedules; application must reconnect and recreate session state; detailed customer maintenance control **UNKNOWN** ([N7], [N9]) | Maintenance window/deny-period controls vary by edition; application must tolerate brief downtime ([G8]) |
| Export/restore | `pg_dump`; physical backups not directly downloadable after PITR disable; custom role passwords omitted from daily backup ([S1]) | Standard PostgreSQL clients and client-side copy/import are supported; native snapshots are provider-specific; portable logical dump/restore must be tested ([A12]–[A14]) | `pg_dump`/`pg_restore` on direct connection; history/branch metadata is not portable ([N2]) | SQL dump export/import is documented; managed backups are provider-specific ([G2], [G11]) |
| Ops burden | Low platform burden; material plan/add-on boundaries | Moderate; most explicit infrastructure controls | Low platform burden, but serverless/session semantics add application burden | Moderate; most explicit infrastructure controls |
| Lock-in | Low if BaaS APIs are prohibited; higher if Auth/Storage/Realtime adopted | Low-to-moderate; IAM, monitoring, snapshots, proxy are AWS-specific | Moderate; branching/history/scale-to-zero are proprietary | Low-to-moderate; IAM, monitoring, backup vault, proxy are GCP-specific |

### Compatibility interpretation

All four expose PostgreSQL's wire protocol and can support the current
SQLAlchemy 2 + psycopg + Alembic stack in principle. That is not enough to
claim behavioral equivalence. Provider engine versions, extensions,
privileges, pool modes, maintenance, TLS roots, and connection limits must be
checked for the exact plan, region, engine version, and endpoint before any
future provisioning decision.

For correctness, migrations, `pg_dump`/`pg_restore`, long transactions,
`LISTEN/NOTIFY`, and session-level advisory locks must use a direct or true
session connection. A transaction pool may be used only after tests prove that
every operation is transaction-scoped; a pooled connection must never be
silently substituted for the migration or worker source.

## 5. Cost comparison

Prices are public list prices accessed 2026-09-26, not quotes. Taxes, support,
discounts, credits, currency conversion, and future changes are excluded.
Unknown usage and configuration make exact totals **UNKNOWN**.

| Provider | Base/compute | Backup/PITR | HA | Network | Monitoring/audit | Minimum relevant cost conclusion |
| --- | --- | --- | --- | --- | --- | --- |
| Supabase | Pro starts $25/month; Small compute is about $15/month; one $10 compute credit is included per paid organization ([S2], [S4]) | 7d PITR about $100/month per project; 14d ~$200; 28d ~$400 | No separately priced synchronous standby found | 250GB egress included on Pro/Team, then published overage; private path requires Team/Enterprise | Metrics included Pro+; log drain $60/month plus usage; platform audit logs Team+ | Official one-project Pro + Small + 7d PITR example totals **$130/month** after credit ([S2]). It still lacks documented compute HA. Team starts $599/month before PITR/usage adjustments. |
| RDS | Region/class/deployment hourly rate; exact static rate not exposed by the fetched page | Backup storage and retention growth can add cost; exact amount **UNKNOWN** | Multi-AZ deployment charges primary/standby resources; write I/O can double ([A7]) | Region/topology/egress dependent | Basic metrics plus optional logs, Enhanced Monitoring, Database Insights, alarms; exact amount **UNKNOWN** | **UNKNOWN** until an official calculator estimate fixes region and configuration. Required estimate must itemize DB hours, storage/IOPS, backups, transfer, logs/metrics/alarms, secrets/KMS, and support. |
| Neon | Launch $0.106/CU-hour; Scale $0.222/CU-hour; 0.25 CU is 1GB RAM ([N1]) | Data $0.35/GB-month; history $0.20/GB-month; snapshots $0.09/GB-month | Multi-AZ storage included; separate compute HA charge/model not documented | 500GB public egress included on paid plans then $0.10/GB; Scale private transfer $0.01/GB | Scale includes 14d retention and export; external sink cost **UNKNOWN** | Always-on 0.25 CU on Scale is an illustrative **$40.52/month** compute (`0.25 × 730 × $0.222`) plus data, history, snapshots, private transfer, and external monitoring. Total is **UNKNOWN**; compute HA/RTO remains unproven. |
| Cloud SQL | Region-, edition-, vCPU-, and memory-dependent | Storage/backups priced by GiB; enhanced backup-vault charges can differ | Regional HA CPU/memory and storage are approximately twice standalone ([G1], [G6]) | Same-region GCE is free; cross-region/internet rates apply ([G6]) | Built-in metrics; Logging, Monitoring, audit retention/ingestion/alerts can add cost | **UNKNOWN** until an official calculator estimate fixes region, edition, machine, HA storage, backup option, transfer, logs/metrics/alerts, KMS, DNS, and support. |

The apparent Neon compute floor is not directly comparable to RDS/Cloud SQL:
Neon uses quorum-backed storage plus ephemeral-compute rescheduling rather
than a continuously running synchronous compute standby, and documents up to
10 minutes for AZ recovery. The Supabase $130 example is not an HA price.
Cost must be compared only after topologies satisfy the same accepted recovery
and isolation requirements.

## 6. Minimum future `SIM` tier

Subject to a future accepted ADR and explicit authorization, the proposed
minimum is an engineering sizing hypothesis, not a vendor minimum or validated
capacity:

- RDS for PostgreSQL Multi-AZ DB instance with one standby;
- a currently supported PostgreSQL major version matching the migration/test
  matrix, selected only after exact region, class, extension, and upgrade
  compatibility is verified;
- provisionally `db.t4g.small` or larger, never `micro`, with a load test and
  connection budget before promotion. AWS identifies `db.t4g` as a
  burstable, Unlimited-mode family; this recommendation deliberately reserves
  more memory than `micro` but is not evidence of workload sufficiency
  ([A15]);
- `gp3`, 20 GiB minimum, storage autoscaling with a finite maximum and billing
  alarms;
- seven-day automated-backup/PITR retention plus protected manual snapshot
  before a risky upgrade;
- encrypted storage and backups;
- private subnets in at least two Availability Zones, `PubliclyAccessible =
  false`, narrowly scoped security groups, and verified TLS;
- deletion protection and final-snapshot protection;
- direct writer endpoint with a small bounded SQLAlchemy pool, connection
  health checks, finite connect/statement/lock/idle-transaction timeouts, and
  retry only around operations whose transaction outcome is known;
- CloudWatch alarms and database log exports sufficient to observe the
  proposed objectives;
- no RDS Proxy initially;
- no read replica initially; the standby is for HA, not reads;
- a tested `pg_dump`/`pg_restore` export and an isolated PITR restore before
  acceptance.

`db.t4g.small` is a provisional starting floor, not a performance guarantee or
accepted tier. Burstable CPU
credits, memory, connection count, autovacuum, I/O latency, WAL rate, lock
waits, long transactions, and restore time must be measured. A non-burstable
class becomes mandatory if sustained CPU, credit depletion, memory pressure,
or latency variance threatens the accepted objectives.

## 7. Proposed connection-source and environment-isolation contract

This section is an `r1` design input because the task explicitly requests
environment separation. It does not claim `P2-C/r2` completion. Final
network/secret mechanics depend on the separately owned `P2-B` architecture
and must be reconciled before any later contract freeze.

### 7.1 One explicit source per environment

Future configuration should expose references to secrets, never connection
strings in the repository:

| Environment | Sole permitted source | Status |
| --- | --- | --- |
| `DEV` | `SWINGTRADE_DEV_DATABASE_URL_REF` | Local developer secret source; local PostgreSQL only |
| `TEST` | `SWINGTRADE_TEST_DATABASE_URL_REF` | Ephemeral/local CI secret source; disposable PostgreSQL only |
| `SIM` | `SWINGTRADE_SIM_DATABASE_URL_REF` | Future isolated managed-secret reference; currently unconfigured and unauthorized |
| `LIVE` | `SWINGTRADE_LIVE_DATABASE_URL_REF` | **Must be absent/unconfigured**; `LIVE` remains unauthorized |

`*_REF` denotes an opaque reference to an approved secret store, not a URL,
password, host, account identifier, or secret value. The eventual
security/auth architecture decides the secret store and workload identity.

The resolver contract must:

1. require an explicit environment enum;
2. accept exactly the corresponding source and reject zero or multiple
   sources;
3. reject a generic `DATABASE_URL`;
4. reject aliases, inheritance, interpolation, or lookup from another
   environment;
5. reject `SIM` when its dedicated reference is absent;
6. reject `LIVE` unconditionally while current governance denies it, even if a
   value is injected;
7. validate the resolved endpoint identity, database name, role, TLS mode,
   and expected provider/account/project metadata before opening a socket;
8. never retry against another endpoint, region, provider, replica, local
   database, or cached URL;
9. bind migration and application sources separately within the same
   environment if pooling is introduced; and
10. redact the resolved value from logs, traces, errors, metrics, reports, and
    process listings.

Missing, malformed, mismatched, stale, or inaccessible configuration is a hard
startup failure. There is no local fallback for a cloud ledger and no
`SIM`-to-`DEV`, `LIVE`-to-`SIM`, primary-to-unverified-restore, or
managed-to-local fallback.

### 7.2 Isolation units

- `DEV`: local PostgreSQL per developer/worktree where practical; synthetic or
  sanitized data only.
- `TEST`: a separate disposable PostgreSQL database or container per test
  execution; never share the developer database.
- `SIM`: a dedicated cloud account/sub-account or equivalent security
  boundary, dedicated network, managed database instance/project, secret
  namespace, encryption key policy, monitoring sink, backup policy, and
  least-privilege database roles. Do not share an instance, project, database,
  role, connection pool, backup set, or network trust with future `LIVE`.
- `LIVE`: no account, project, instance, network, secret, DNS name, role, or
  connection source is designed or configured by this work. If ever
  authorized, it requires a separate cloud account/project and a separate
  accepted architecture.

For RDS, the recommendation is separate AWS accounts for `SIM` and any future
`LIVE`, not merely separate databases in one instance. For Cloud SQL, use
separate GCP projects and VPCs. For Supabase or Neon, use separate
organizations/accounts where supported plus separate projects; a child
database branch is not sufficient isolation for `SIM` versus `LIVE`.

### 7.3 Roles and endpoint classes

Each environment should have distinct least-privilege roles:

- migration owner: DDL only during a controlled migration;
- application writer: required DML only, no schema ownership;
- reconciliation reader: read-only where feasible;
- backup/export operator: narrowly scoped, time-bound operational role;
- monitoring integration: no table-data access unless explicitly required.

Migration and export tooling always uses a direct connection. Long-running
workers use direct connections. If a transaction pool is later approved for
short requests, it gets a separate secret reference and role; it must not
replace the direct worker or migration source.

## 8. Transaction and recovery rules

- Keep the intent/event/outbox atomic unit in one PostgreSQL transaction.
- Use transaction-scoped advisory locks where possible. Session advisory
  locks require a direct/session connection and explicit cleanup.
- Never assume a commit succeeded or failed solely because the client
  disconnected. Persist and reconcile using the existing idempotency and
  ledger contracts.
- Set finite `statement_timeout`, `lock_timeout`, and
  `idle_in_transaction_session_timeout` values after workload testing.
- Bound every process pool and reserve connections for migrations,
  observability, and incident response. Exact `max_connections` and pool
  budgets are **UNKNOWN** until the selected class is tested.
- Use `pool_pre_ping`/bounded connection lifetime and dispose pools after
  failover. Retries require a new transaction and the same idempotency
  identity; retry exhaustion stops for Operator review.
- Do not use unlogged tables for authoritative ledger data. Cloud SQL
  explicitly documents that unlogged contents do not survive HA failover or
  backup restore ([G2]); the same PostgreSQL durability property makes them
  unsuitable across providers.

## 9. Backups, PITR, and recovery evidence

PITR is necessary but not sufficient. A future accepted deployment should:

1. enable seven-day PITR before any authoritative `SIM` write;
2. monitor latest-restorable time and automated-backup success;
3. keep backups in the `SIM` isolation boundary and protect deletion;
4. create an isolated new-instance restore for drills; never overwrite the
   only ledger as the first recovery action;
5. apply the exact migration revision and verify schema compatibility;
6. compare event count, aggregate versions, intent/outbox states, canonical
   digests, and accepted high-water mark;
7. run reconciliation before permitting dispatch;
8. record measured recovery point and recovery time, not just provider job
   success;
9. test a native backup restore and a portable logical restore; and
10. treat a missed objective, stale recovery point, failed digest, or
    unreconciled state as fail-closed.

RDS PITR restores to a new instance, which fits the safe-first-restore rule.
Supabase and Neon offer in-place workflows that require extra care: the
Supabase project is unavailable during restore, while Neon overwrites the root
branch and preserves the prior state as a backup branch ([S1], [N4]).

## 10. Monitoring, audit, maintenance, and upgrades

Minimum signals:

- connection saturation/rejections and pool wait;
- database availability and reconnect duration;
- CPU, burst credits where applicable, memory/swap, storage, IOPS, throughput,
  and latency;
- transaction rate, rollback rate, deadlocks, lock waits, oldest transaction,
  idle-in-transaction sessions, autovacuum health, and replication/failover
  events;
- backup success, age of latest restorable point, retained-window coverage,
  restore-drill age/result, and backup-storage growth;
- database errors and slow queries with sensitive values redacted;
- TLS certificate expiry/rotation, authentication failures, security-group or
  network-policy changes, privileged role changes, and provider control-plane
  audit events;
- maintenance and engine-support deadlines; and
- itemized spend and forecast by compute, HA, storage/I/O, backup, network,
  monitoring/logging, secrets/KMS, and support.

Every critical alert needs an owner, route, runbook, and tested escalation.
Database logs, broadly visible telemetry, and reports must not contain
credentials, connection URLs, brokerage account identifiers, or raw broker
payloads. Access-controlled infrastructure audit evidence may retain the
minimum provider resource/principal identifiers required for attribution and
endpoint/account-boundary validation; those identifiers must be classified,
access-limited, and pseudonymized before entering broader telemetry.

Major-version upgrades require a rehearsal from backup in an isolated
environment, application/migration compatibility tests, a portable export,
and a rollback plan. Provider snapshots generally restore only to compatible
provider versions and are not the portability plan. Minor/maintenance updates
still require reconnect testing and an approved maintenance window.

## 11. Portability and exit plan

The portable core is PostgreSQL schema plus data, not a provider snapshot,
branch history, IAM policy, metric dashboard, or backup catalog.

Provider-neutral rules:

- keep `postgresql+psycopg` and SQLAlchemy's PostgreSQL dialect;
- avoid Supabase Auth/Storage/Realtime/PostgREST dependencies;
- avoid Neon branching/history assumptions in application correctness;
- avoid mandatory RDS Proxy/IAM-token or Cloud SQL connector behavior in the
  domain/persistence layer;
- use only required extensions after confirming availability on all viable
  targets;
- maintain Alembic as the schema history;
- regularly produce and restore encrypted logical exports using direct
  connections;
- document roles, grants, parameters, extensions, collation/locale, time zone,
  and sequence state;
- keep provider infrastructure and monitoring adapters outside application
  domain code.

Exit procedure:

1. freeze schema changes and establish a source high-water mark;
2. create native recovery evidence and a portable `pg_dump`;
3. restore into an isolated target of the same supported PostgreSQL major
   version;
4. apply roles/grants and verify extensions/parameters explicitly;
5. validate schema head, counts, constraints, sequence values, canonical
   digests, ledger replay, and reconciliation;
6. perform a bounded final delta/cutover using an accepted migration method;
7. rotate source/target secrets and keep the source read-only for the accepted
   rollback window;
8. delete only after retention, audit, legal, and Operator gates are met.

Expected exit friction is lowest for direct RDS/Cloud SQL PostgreSQL use,
slightly higher for Supabase if BaaS features are avoided, and higher for Neon
because branch/history/scale-to-zero behavior cannot be exported. Exact
migration downtime and logical-replication compatibility remain **UNKNOWN**
until source and target versions/topologies are fixed.

## 12. Open decisions and required pre-acceptance evidence

The Operator still must decide or delegate decisions for:

- provider, cloud/region, account/project ownership, and budget;
- accepted availability, RPO, RTO, retention, and restore-drill frequency;
- PostgreSQL major version, extensions, parameters, and support lifecycle;
- workload compute location and private network path;
- secret manager, database authentication, encryption-key ownership, and
  rotation;
- audit/log retention and incident ownership;
- data classification, regulatory/legal obligations, and deletion policy.

Before any provider ADR can be accepted:

1. obtain official same-day estimates for an equivalent HA topology from RDS
   and Cloud SQL, plus any Supabase/Neon topology claimed as equivalent;
2. obtain plan/contract confirmation for undocumented HA/RPO/RTO/SLA details;
3. verify exact region, PostgreSQL version, extension, instance/machine,
   private-network, backup, monitoring, and support compatibility;
4. define connection and database-role budgets;
5. prove migration, transaction, advisory-lock, disconnect, failover, PITR,
   portable export/restore, and reconciliation behavior in an authorized
   isolated non-production exercise; and
6. have an independent reviewer verify the evidence. This document's author
   cannot accept the decision.

## 13. Evidence catalog

Every web source below is first-party and was accessed 2026-09-26. A page with
no visible publication/update timestamp is current only as fetched; pricing
and plan terms are mutable and must be rechecked at decision time. Cloud SQL
pages fetched here displayed “Last updated 2026-09-24 UTC.” Product docs are
not automatically contractual SLAs.

### Repository evidence

- **[R1]** `pyproject.toml`, `migrations/env.py`,
  `src/swingtrade/persistence.py`, and `docker-compose.yml` at baseline
  `1ecbbe6d487d97195fde393b05c9499357599bdb`. Supports: SQLAlchemy 2,
  psycopg 3, Alembic, PostgreSQL-dialect-only repository guard, `NullPool` for
  migrations, and local PostgreSQL development. Limitation: local behavior
  does not prove managed-service compatibility or recovery.
- **[R2]** PostgreSQL Global Development Group, “Explicit Locking — Advisory
  Locks,”
  <https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS>.
  Supports: transaction versus session advisory-lock lifetime, cleanup, and
  limits. Limitation: provider pool/failover behavior still requires testing.

### Supabase

- **[S1]** Supabase, “Database Backups,”
  <https://supabase.com/docs/guides/platform/backups>. Supports: daily
  retention by plan, PITR Small-compute prerequisite, two-minute worst-case
  RPO, size-dependent offline restore, logical export, and backup limitations.
  Limitation: no contractual restore time or compute HA claim.
- **[S2]** Supabase, “Manage Point-in-Time Recovery usage,”
  <https://supabase.com/docs/guides/platform/manage-your-usage/point-in-time-recovery>.
  Supports: 7/14/28-day hourly and approximate monthly PITR prices and the
  official one-project $130 example. Limitation: taxes and other usage
  excluded.
- **[S3]** Supabase, “Connect to your database,”
  <https://supabase.com/docs/guides/database/connecting-to-postgres>.
  Supports: direct/session/transaction endpoint use, IP versions, persistent
  backend guidance, transaction-pool limitations, direct migration/export,
  TLS configuration. Limitation: client limits depend on compute.
- **[S4]** Supabase, “Pricing,” <https://supabase.com/pricing>. Supports:
  plan, compute, connection, disk, egress, PITR, log, metrics, audit, SLA, and
  PrivateLink plan boundaries. Limitation: pricing can change and Enterprise
  is quote-only.
- **[S5]** Supabase, “Postgres SSL Enforcement,”
  <https://supabase.com/docs/guides/platform/ssl-enforcement>. Supports: SSL
  enforcement, `verify-full`, CA use, and reboot/downtime on changes.
- **[S6]** Supabase, “Postgres Extensions Overview,”
  <https://supabase.com/docs/guides/database/extensions>. Supports:
  preconfigured extension model and extension/software-upgrade coupling.
- **[S7]** Supabase search index result for “Multigres,” canonical URL
  <https://supabase.com/docs/guides/database/multigres>. **Limitation:** direct
  retrieval returned `404` on 2026-09-26. The snippet is not reproducible
  provider documentation, so this report credits no feature claim from it.
- **[S8]** Supabase, “Available regions,”
  <https://supabase.com/docs/guides/platform/regions>. Supports: one primary
  region per project, general/specific AWS regions, data-residency caveats,
  and general-region feature limits.
- **[S9]** Supabase, “Compute and Disk,”
  <https://supabase.com/docs/guides/platform/compute-and-disk>. Supports:
  compute classes, connection limits, storage/IO characteristics, and
  downtime during compute-size changes.

### Amazon Web Services

- **[A1]** AWS, “Multi-AZ DB instance deployments for Amazon RDS,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html>.
  Supports: synchronous cross-AZ standby, automatic failover, standby not
  readable, possible commit latency.
- **[A2]** AWS, “Failing over a Multi-AZ DB instance,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.Failover.html>.
  Supports: typical 60–120 second failover, reconnect and DNS behavior.
  Limitation: timing depends on activity/recovery and is not stated as an SLA.
- **[A3]** AWS, “Restoring a DB instance to a specified time,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PIT.html>.
  Supports: restore creates a new instance and transaction logs upload every
  five minutes.
- **[A4]** AWS, “Backup retention period,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.BackupRetention.html>.
  Supports: 0–35 day DB-instance retention and outage when toggling between
  disabled/enabled.
- **[A5]** AWS, “Using SSL/TLS to encrypt a connection,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html>.
  Supports: TLS, server identity verification, CA bundles, managed certificate
  rotation.
- **[A6]** AWS, “Amazon RDS Proxy,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.html>.
  Supports: pooling, VPC/Secrets Manager/IAM integration, pinning and
  PostgreSQL limitations including absent `CancelRequest`.
- **[A7]** AWS, “Amazon RDS for PostgreSQL pricing,”
  <https://aws.amazon.com/rds/postgresql/pricing/>. Supports: pricing
  dimensions, Multi-AZ resource model, doubled write I/O, backup/network
  components, and calculator requirement. Limitation: fetched page did not
  expose a fixed region/class rate.
- **[A8]** AWS, “Using PostgreSQL extensions with Amazon RDS,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Appendix.PostgreSQL.CommonDBATasks.Extensions.html>.
  Supports: curated/version-dependent extensions, parameter and privilege
  constraints.
- **[A9]** AWS, “Viewing metrics in the Amazon RDS console,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.html>.
  Supports: CloudWatch, Enhanced Monitoring, process list, and Database
  Insights.
- **[A10]** AWS, “Upgrades of the RDS for PostgreSQL DB engine,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_UpgradeDBInstance.PostgreSQL.html>.
  Supports: manual major upgrades, optional automatic minor upgrades,
  Multi-AZ downtime behavior, pre/post snapshots, and blue/green option.
- **[A11]** AWS, “IAM database authentication for MariaDB, MySQL, and
  PostgreSQL,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html>.
  Supports: 15-minute token authentication, TLS, centralized access, memory
  overhead, and PostgreSQL/replication limitations.
- **[A12]** AWS, “Amazon RDS for PostgreSQL,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html>.
  Supports: standard SQL clients, PostgreSQL versions, Multi-AZ, VPC, SSL,
  backups/PITR, and managed-service privilege restrictions.
- **[A13]** AWS, “Connecting to a DB instance running PostgreSQL,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ConnectToPostgreSQLInstance.html>.
  Supports: standard clients/endpoints and public versus private VPC
  accessibility.
- **[A14]** AWS, “Using the `\copy` command to import data,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Procedural.Importing.Copy.html>.
  Supports: client-side standard PostgreSQL copy/import.
- **[A15]** AWS, “DB instance class types,”
  <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.Types.html>.
  Supports: `db.t4g` burstable family and Unlimited-mode cost behavior.
  Limitation: does not validate `small` for this workload.

### Neon

- **[N1]** Neon, “Plans,”
  <https://neon.com/docs/introduction/plans>. Supports: Free/Launch/Scale
  compute, storage, history, snapshot, network, monitoring, security, SLA, and
  pricing boundaries.
- **[N2]** Neon, “Connection pooling,”
  <https://neon.com/docs/connect/connection-pooling>. Supports: PgBouncer
  transaction mode, limits, direct-use cases, unsupported session state and
  session advisory locks.
- **[N3]** Neon, “Connect an SQLAlchemy application to Lakebase Postgres,”
  <https://neon.com/docs/guides/sqlalchemy>. Supports: SQLAlchemy connection,
  stale connections after suspend, `pool_pre_ping`/`pool_recycle`, and
  SQLAlchemy 2.0.33+ note.
- **[N4]** Neon, “Instant restore,”
  <https://neon.com/docs/introduction/branch-restore>. Supports: root-only
  restore, in-place overwrite, backup branch, connection interruption, and
  restore limitations.
- **[N5]** Neon, “Security overview,”
  <https://neon.com/docs/security/security-overview>. Supports: mandatory TLS,
  `verify-full`, Scale IP allow, Private Networking, protected branches,
  encryption, secret-manager guidance.
- **[N6]** Neon, “Schema migration with Lakebase Postgres and SQLAlchemy,”
  <https://neon.com/docs/guides/sqlalchemy-migrations>. Supports: SQLAlchemy
  and Alembic compatibility and direct non-pooled migration requirement.
- **[N7]** Neon, “High Availability (HA) in Neon,”
  <https://neon.com/docs/introduction/high-availability>. Supports:
  multi-AZ Safekeeper/Pageserver redundancy; seconds, 1–2 minute, and 1–10
  minute recovery ranges by failure type; reconnect/session-state effects;
  stable endpoint; and no cross-region replication. Limitation: ranges are
  not presented as contractual guarantees.
- **[N8]** Neon, “The lakebase architecture,”
  <https://neon.com/docs/introduction/architecture-overview>. Supports:
  ephemeral compute, durable storage, Paxos WAL quorum acknowledgement as the
  commit boundary, and object-storage history.
- **[N9]** Neon, “Compute lifecycle,”
  <https://neon.com/docs/introduction/compute-lifecycle>. Supports:
  scale-to-zero behavior, paid-plan disablement, activation latency, and loss
  of advisory locks/temporary tables/prepared statements/notifications when a
  session closes.
- **[N10]** Neon, “Regions,”
  <https://neon.com/docs/introduction/regions>. Supports: current AWS region
  list, immutable project region, Azure region deprecation, and regional
  product availability.

### Google Cloud

- **[G1]** Google Cloud, “About high availability,”
  <https://cloud.google.com/sql/docs/postgres/high-availability>. Supports:
  synchronous two-zone regional HA, shared IP, expected ~60 second failover,
  doubled HA cost, reconnect behavior, and typical standalone PITR RPO of five
  minutes or less. Limitation: timing is environment-dependent.
- **[G2]** Google Cloud, “Cloud SQL backups overview,”
  <https://cloud.google.com/sql/docs/postgres/backup-recovery/backups>.
  Supports: standard/enhanced backups, encryption, incremental model,
  retention ranges, cross-region restore, integrity sampling, and unlogged
  table limitations.
- **[G3]** Google Cloud, “Perform point-in-time recovery,”
  <https://cloud.google.com/sql/docs/postgres/backup-recovery/pitr>. Supports:
  PITR workflow and new-instance recovery. Limitation: exact recovery time is
  not guaranteed.
- **[G4]** Google Cloud, “Cloud SQL pricing,”
  <https://cloud.google.com/sql/pricing>. Supports: region/edition resource
  pricing, HA rates, storage, backup, egress, serverless export, DNS, and
  extended-support dimensions.
- **[G5]** Google Cloud, “Learn about using private IP,”
  <https://cloud.google.com/sql/docs/postgres/private-ip>. Supports: private
  services access, VPC requirements, Auth Proxy private path, encryption,
  isolation guidance, and network limitations.
- **[G6]** Google Cloud, “Cloud SQL pricing,” same canonical URL as [G4].
  Supports specifically: HA CPU/memory rates are twice standalone in the
  displayed Enterprise table; storage and network are separate.
- **[G7]** Google Cloud, “Monitor Cloud SQL instances,”
  <https://cloud.google.com/sql/docs/postgres/monitor-instance>. Supports:
  System Insights, Cloud Monitoring dashboard/alerts, core metrics, and WAL
  retention visibility.
- **[G8]** Google Cloud, “About maintenance on Cloud SQL instances,”
  <https://cloud.google.com/sql/docs/postgres/maintenance>. Supports:
  maintenance timing/control and application reconnect expectations.
- **[G9]** Google Cloud, “IAM authentication,”
  <https://cloud.google.com/sql/docs/postgres/iam-authentication>. Supports:
  built-in versus IAM database authentication, one-hour access tokens,
  automatic connector refresh for long-running processes, SSL requirement,
  audit behavior, and shared-core performance caveat.
- **[G10]** Google Cloud, “Choose how to connect to Cloud SQL,”
  <https://docs.cloud.google.com/sql/docs/postgres/connect-overview>. Supports:
  direct versus connector paths, private/public IP, TLS responsibilities,
  private networking choices, and authentication options.
- **[G11]** Google Cloud, “Export and import using SQL dump files,”
  <https://docs.cloud.google.com/sql/docs/postgres/import-export/import-export-sql>.
  Supports: PostgreSQL SQL dump export/import workflow. Limitation: managed
  backup metadata remains provider-specific.

## 14. Non-actions and completion boundary

This research created only `docs/DB_DEPLOYMENT.md`. It did not alter source,
tests, migrations, configuration, governance state, journal, provider
resources, credentials, networks, accounts, secrets, or accepted decisions.
No network activity occurred except reading public first-party documentation.
No provider API, console, calculator account, or authenticated service was
used.
