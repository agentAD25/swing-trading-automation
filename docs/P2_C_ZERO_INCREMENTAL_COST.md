# Zero-incremental-cost database evidence

- Workstream: `P2-C` evidence update after `P2-C/r1`
- Status: engineering evidence and a SIM suitability recommendation for
  Operator consideration. **Not an accepted ADR. Not provider acceptance.
  Not procurement or provisioning authority.**
- Evidence baseline: `9631de3bd8a6a2e24c6833ca534c5e626fdb7b75`
- Superseding main evidence merged into this branch and not edited here:
  `a03c7372fe08b6b42618e72958892154ffebb511`, tree
  `93dd5c0a3c305bbf1ad2ef46e3ab103f3993f038`
- Public-documentation access date: 2026-09-30
- Historical research left unchanged: `docs/DB_DEPLOYMENT.md`
- `docs/CURRENT_STATE.md` and `docs/ENGINEERING_JOURNAL.md` are not edited
  by this update
- Execution authority remains: local, deterministic, non-network `DRY_RUN`
  only

## 1. Scope and non-actions

This document records an Operator cost constraint, the effect of that
constraint on the earlier RDS recommendation, and a first-party review of
what Supabase documents at zero incremental service cost. It is an overlay.
It does not rewrite `docs/DB_DEPLOYMENT.md`, `docs/PHASE_2_PLAN.md`, or
Phase 1 history.

This update does not:

- accept Supabase, RDS, Cloud SQL, Neon, or any other provider;
- provision a project, instance, network, or disk, or connect to one;
- request, store, or use a credential, connection string, or project
  identifier;
- add a Supabase client, Auth, Storage, Realtime, Edge Functions, or
  PostgREST dependency;
- add a backup runner, schedule, workflow, wrapper, or script;
- authorize TradeStation `SIM`, order submission, real capital, or `LIVE`;
- start Phase 2 implementation;
- close `P2_0_CONTRACT_CONFLICT` C1 (U-10);
- change Group 2 status in `docs/CURRENT_STATE.md`.

`docs/CURRENT_STATE.md` at `a03c737` still records Group 2 as unauthorized
and Phase 2 implementation as unstarted. This file does not change that
record. The cost decision below is evidence for the Operator. It is not,
by itself, a current-state grant.

## 2. Operator cost decision

The Operator decision supplied for this evidence update is:

`INITIAL_DATABASE_INCREMENTAL_SERVICE_COST = 0 USD.`

Recorded consequences:

- This is an initial cost constraint, not a permanent architecture
  commitment.
- Eligible now: existing local PostgreSQL, and existing Supabase access.
- Amazon RDS for PostgreSQL remains historical future-paid evidence. It is
  not the current initial-deployment target.
- Local PostgreSQL is for development, test, adversarial testing, and
  migration verification only.
- Supabase PostgreSQL is a candidate for a remotely available SIM ledger.
  It is not automatically accepted.
- Persistence remains Python to SQLAlchemy 2.x to PostgreSQL.
- DEV and TEST may use isolated local PostgreSQL.
- SIM must not fall back to local PostgreSQL.
- LIVE stays unconfigured and must not fall back to SIM.

This agent did not inspect the existing Supabase account. Plan, region,
PostgreSQL major version, project identity, and remaining free-project
quota are **UNKNOWN**. The capability inventory below is the documented
Free-plan envelope, which is the only public envelope this review can
treat as zero incremental cost. Features already paid for on an existing
organization, if any, are **UNKNOWN** and are not treated as free.

## 3. Original RDS recommendation

`docs/DB_DEPLOYMENT.md` §2, from `P2-C/r1`, is an engineering
recommendation for Operator consideration. It is not an accepted ADR.
`docs/PHASE_2_PLAN.md` made no provider selection. The research text
recommends, for a future authorized SIM environment:

- Amazon RDS for PostgreSQL;
- Multi-AZ with one synchronous standby;
- private networking, encrypted storage, automated backups, and seven-day
  PITR;
- a burstable Graviton class no smaller than `db.t4g.small`, and `gp3`;
- the direct PostgreSQL endpoint, not RDS Proxy.

The stated reasons were synchronous cross-zone failover, ordinary
PostgreSQL session semantics, and a mature private-network control plane.
Supabase and Neon were deferred there because the reviewed material did
not establish a production synchronous multi-AZ standby, a plan contract,
private connectivity, and portability together. Cloud SQL was the
alternative if compute were later committed to GCP.

Those sections stay as written. This update does not delete, soften, or
replace their evidence.

## 4. Superseded initial-deployment effect

The Operator cost constraint supersedes only the initial-deployment
effect of that RDS recommendation.

What remains true:

- The historical comparison and the RDS rationale stay available for a
  later paid decision.
- No provider is selected.
- The proposed SIM objectives in `docs/DB_DEPLOYMENT.md` §3, including
  synchronous cross-zone HA and seven-day PITR before authoritative SIM
  writes, are not met by the zero-cost envelope below.

What is no longer the current initial target:

- Provisioning RDS Multi-AZ, or any other new paid database, as the first
  SIM ledger.
- Treating the §6 minimum tier (`db.t4g.small` Multi-AZ, seven-day PITR,
  private subnets) as something that can be deployed while incremental
  service cost must stay at 0 USD.

RDS, Cloud SQL, Neon, and paid Supabase tiers remain future-paid evidence.
They are not eligible initial deployments under this constraint.

## 5. Eligible candidates

| Candidate | Eligibility under the 0 USD constraint | Role |
| --- | --- | --- |
| Existing local PostgreSQL | Eligible now | DEV, TEST, adversarial tests, migration verification, and logical-restore drills only. Not a SIM ledger and not a SIM fallback. |
| Existing Supabase access | Eligible as a candidate only | Possible remote SIM ledger. Not accepted. Not provisioned. Not connected by this work. |
| Amazon RDS for PostgreSQL | Not eligible for initial deployment | Historical recommended future-paid design. Not the current target. |
| Google Cloud SQL for PostgreSQL | Not eligible now | Historical alternative. New paid provisioning. |
| Neon | Not eligible now | Historical deferred candidate. Not existing access under this decision. |

A new Supabase project, a paid organization, a compute upgrade, an IPv4
add-on, PITR, a read replica, or branching would be new provisioning or a
new charge. None of those are authorized or assumed here.

## 6. Revisit conditions

Reopen the initial-deployment choice, without rewriting this record or
`docs/DB_DEPLOYMENT.md`, if any of the following becomes true:

1. The Operator assigns a non-zero incremental database budget.
2. The Operator reinstates synchronous HA, a contractual recovery
   objective, or private networking as a requirement for the first SIM
   ledger.
3. The Supabase project pauses, becomes read-only, or is restricted under
   the published fair-use rules.
4. Database size approaches 500 MB, or disk use, including WAL, approaches
   the 1 GB Free-plan disk.
5. Uncached egress, including logical exports, approaches 5 GB in a
   billing period.
6. Measured memory, CPU, connections, or disk IO exceeds the published
   Nano baseline or exhausts burst.
7. A logical restore drill misses a recovery point or recovery time the
   Operator has accepted.
8. The existing organization is not on the Free plan, or the intended use
   would add a subscription, compute, IPv4, PITR, replica, disk, or
   branching charge.
9. The future SIM host cannot use IPv6 for a direct connection and cannot
   use session-mode pooling without the paid IPv4 add-on.
10. Supabase changes Free-plan limits, Nano resources, pause rules, or
    backup rules. The pricing page says pricing may change. The compute
    page says Free-plan compute resources are subject to change.
11. A second isolation boundary, including any future LIVE boundary or a
    second cloud restore target, would exceed the two active Free
    projects.
12. An obligation requires an uptime SLA, platform audit logs, or
    PrivateLink.
13. A generally available, production-supported, zero-cost synchronous
    failover offer is documented. That is not established in this review.

## 7. Zero-cost capabilities

Facts in this section come from first-party Supabase pages fetched on
2026-09-30. They describe the published Free plan. They do not describe
the Operator's unseen project. "Dedicated Postgres" on the pricing page
means a project instance. Nano and other sizes through Medium use shared
CPU in an isolated environment ([Z3]). That is not dedicated-vCPU capacity
and it is not Multi-AZ high availability.

Published Free-plan inclusions ([Z1], [Z3], [Z4]):

- Organization plan price 0 USD per month, with a limit of two active
  projects. Paused projects do not count toward that limit. Owner and
  Admin quotas are counted together inside an organization ([Z8]).
- One Postgres instance per project on the Nano size: shared CPU, up to
  0.5 GB memory, 0 USD. Recommended maximum database size 500 MB.
  Published connection guidance is 60 database connections and 200 pooler
  clients. Baseline disk performance is 250 IOPS and 5 MB/s, with burst
  up to 11,800 IOPS and 261 MB/s. Burst is finite.
- Database size quota 500 MB per project. Disk space included is 1 GB.
  New projects already use about 40–60 MB for preinstalled extensions,
  schemas, and default data ([Z6]).
- Uncached egress 5 GB and cached egress 5 GB. Cached egress is a storage
  CDN path ([Z12]).
- Direct Postgres connections on IPv6, and the shared pooler in session
  mode (port 5432) and transaction mode (port 6543) on IPv4 ([Z4]).
- TLS, including `sslmode=require` and `sslmode=verify-full` with the
  project CA, and a dashboard control that rejects non-SSL connections
  ([Z4]).
- Database network restrictions by IP range for Postgres and its pooler.
  The page does not state a plan fee ([Z13]).
- Standard Postgres clients. A project can be used as a database only.
  Auth, Storage, Realtime, and Edge Functions are present and optional;
  unused products are documented as costing nothing ([Z1]).
- Logical export. The backups guide tells Free-plan projects to export
  with the Supabase CLI `db dump` command and keep off-site backups
  ([Z2]). That command runs `pg_dump` and, by default, omits data,
  custom roles, and Supabase-managed schemas such as `auth` and `storage`
  ([Z14]).
- No overage invoice on the Free plan. Exceeding a quota leads to
  restriction rather than a charge ([Z7], [Z8]).
- Pause and later resume. A resumed project returns to its previous data
  and configuration. The documented resume window is one year ([Z5]).

Published exclusions at 0 USD:

- Automatic daily backups. Pro retains 7 days, Team 14 days, Enterprise
  up to 30 days ([Z1], [Z2]). The production checklist states that
  database backups are not available for download on the Free plan ([Z9]).
- Point-in-time recovery. The add-on is about 100 USD per month per 7
  days of retention, and it requires at least a Small compute add-on.
  Documented worst-case PITR recovery point is two minutes ([Z1], [Z2]).
- Inactivity non-pause. Paid projects are not paused for inactivity.
  Free projects can be ([Z1], [Z5]).
- The dedicated IPv4 add-on. It is Pro and above, at 0.0055 USD per hour,
  about 4 USD per month ([Z10], [Z11]).
- The dedicated pooler, read replicas, branching, advanced disk
  configuration, the metrics endpoint, platform audit logs, PrivateLink,
  and an uptime SLA ([Z1], [Z4], [Z17], [Z18]).
- A synchronous Multi-AZ writer standby comparable to the RDS design in
  `docs/DB_DEPLOYMENT.md`. Not documented for the Free plan in the pages
  reviewed here.

## 8. Durability is not high availability

Durability means a committed transaction can be reconstructed after the
database process or its disk is lost. High availability means the service
keeps accepting work through a component failure.

At the documented zero-cost envelope:

- An acknowledged commit is durable to the extent PostgreSQL commits it
  to that project's disk and the project remains restorable. Resume after
  pause is documented to bring back data and configuration ([Z5]). Pause
  is an availability stop, not a documented wipe, inside the one-year
  resume window.
- That is one copy. The production checklist says default disks offer
  99.8–99.9% durability, and it assigns durability against a disk failure
  to PITR and availability against a disk failure to read replicas ([Z9]).
  The pricing page lists 99.9% durability for General Purpose disks and
  99.999% for High Performance disks ([Z1]). Those figures are not the
  same. This review does not pick a winner. Advanced disk configuration
  is not a Free-plan feature ([Z1]).
- PITR and downloadable provider backups are absent at 0 USD. The only
  documented second copy at 0 USD is an export held outside the project.
  Its recovery point is the time of the last verified export, not two
  minutes.
- High availability is a separate gap. Free Nano is one instance. The
  reviewed pages do not document a synchronous standby or automatic
  writer failover. A node, zone, or platform outage stops SIM until that
  instance returns or an export is restored somewhere else. SIM still
  must not fail over to local PostgreSQL.
- Read replicas are asynchronous, read-only, and billed as extra compute
  and disk ([Z17], [Z18]). They do not accept ledger writes. They are not
  PITR. They are not a zero-cost capability.
- Multigres is not a zero-cost capability. A direct retrieval of
  `https://supabase.com/docs/guides/database/multigres` on 2026-09-30
  returned **404**. A same-day index of that URL described a public
  alpha for paid-plan organizations, excluded from the uptime SLA, and
  not aimed at production or mission-critical use. The conflict is
  unresolved. Multigres is not an eligible SIM tier. This repeats the
  kind of document-stability conflict already recorded for Multigres in
  `docs/DB_DEPLOYMENT.md` [S7], without editing that entry.

## 9. Limitation classification

Each material limitation has one class:

| Class | Meaning in this review |
| --- | --- |
| `ACCEPTABLE_FOR_SIM` | The limitation can remain for an initial, non-LIVE SIM ledger under the 0 USD constraint. |
| `MITIGATABLE_FOR_SIM` | A zero-cost, provider-neutral control can contain it. The control is not built in this change. |
| `BLOCKS_AUTONOMOUS_SIM` | While it applies, an unattended SIM ledger cannot keep operating, and local fallback is forbidden. |
| `REQUIRES_PAID_TIER` | Removing the limitation as Supabase defines it adds incremental service cost. |
| `UNKNOWN` | The reviewed sources do not establish the fact. |

| ID | Limitation | Class |
| --- | --- | --- |
| L1 | No documented synchronous standby or automatic writer failover at 0 USD. An outage stops the ledger. It does not, by itself, erase a commit that reached disk. | `ACCEPTABLE_FOR_SIM` |
| L2 | Unattended continuation through a node or zone failure. | `BLOCKS_AUTONOMOUS_SIM` |
| L3 | Free-plan inactivity pause when user database activity over seven days is "not sufficient." The page says a few requests a day are typically enough, and that active use can still be too low. A low-volume swing ledger can fall into that description. | `BLOCKS_AUTONOMOUS_SIM` |
| L4 | The numeric activity threshold that prevents pause. | `UNKNOWN` |
| L5 | Guaranteed non-pause. Documented only for paid plans. | `REQUIRES_PAID_TIER` |
| L6 | Resume after pause is a dashboard action by the owner, not an application failover. The resume window is one year. | `BLOCKS_AUTONOMOUS_SIM` |
| L7 | Provider daily backups and downloadable backup files. | `REQUIRES_PAID_TIER` |
| L8 | Two-minute PITR, including Supabase's stated disk-failure durability path. Small compute is also required. | `REQUIRES_PAID_TIER` |
| L9 | No provider-held second copy at 0 USD. An off-site logical export is the documented substitute. Recovery point equals export age. | `MITIGATABLE_FOR_SIM` |
| L10 | Default disk-durability number. Production checklist says 99.8–99.9%. Pricing says 99.9% for General Purpose and 99.999% for High Performance. | `UNKNOWN` |
| L11 | Read replicas as redundancy. They are billed, asynchronous, and read-only. | `REQUIRES_PAID_TIER` |
| L12 | Multigres terms and availability after a direct 404 and a conflicting index. | `UNKNOWN` |
| L13 | 500 MB database-size quota for the expected low-volume ledger, remembering that about 40–60 MB is already used. | `ACCEPTABLE_FOR_SIM` |
| L14 | Whether this ledger, indexes, and WAL stay inside 500 MB and the 1 GB disk. | `UNKNOWN` |
| L15 | Read-only mode above 500 MB database size, or on disk exhaustion (`25006`, and `53100` when the disk is full). Writes stop. | `BLOCKS_AUTONOMOUS_SIM` |
| L16 | Raising the database-size or disk quota. | `REQUIRES_PAID_TIER` |
| L17 | Nano shared CPU, 0.5 GB memory, and 250 IOPS / 5 MB/s baseline versus this workload. Sufficiency is unmeasured. Published Free resources are subject to change. | `UNKNOWN` |
| L18 | 60 direct connections and 200 pooler clients for a bounded worker set. | `ACCEPTABLE_FOR_SIM` |
| L19 | Two active Free projects for a single SIM project. | `ACCEPTABLE_FOR_SIM` |
| L20 | Whether the existing organization still has a free active-project slot. Not inspected. | `UNKNOWN` |
| L21 | A second cloud project as the first restore target. A drill can instead restore into isolated local PostgreSQL. That local database must not become SIM. | `MITIGATABLE_FOR_SIM` |
| L22 | 5 GB uncached egress, which includes database export traffic. Staying inside the quota avoids a charge. | `MITIGATABLE_FOR_SIM` |
| L23 | Fair-use restriction after a quota is exceeded: pause, read-only mode, blocked launches, or HTTP 402. The Free plan does not bill the overage. A later breach in the same warning window may not get another grace period. | `BLOCKS_AUTONOMOUS_SIM` |
| L24 | Unpublished abuse-pause criteria. The billing FAQ allows restriction without prior notice for suspected abuse. | `UNKNOWN` |
| L25 | Dedicated IPv4 for the direct host. | `REQUIRES_PAID_TIER` |
| L26 | IPv4-only clients. Direct connections are IPv6 unless the add-on is enabled. Session-mode pooling is IPv4 on every plan and keeps session state. | `MITIGATABLE_FOR_SIM` |
| L27 | Transaction-mode pooling drops prepared statements, session advisory locks, and other session state. Workers and migrations must not use it. | `MITIGATABLE_FOR_SIM` |
| L28 | No dedicated pooler on the Free plan. | `ACCEPTABLE_FOR_SIM` |
| L29 | No uptime SLA. Enterprise is the plan that lists one. Contractual Free-plan uptime is unpublished. | `ACCEPTABLE_FOR_SIM` |
| L30 | One-day API and database log retention. The ledger remains the audit record. Platform audit logs are a Team feature if later required. | `ACCEPTABLE_FOR_SIM` |
| L31 | No email support on the Free plan. | `ACCEPTABLE_FOR_SIM` |
| L32 | Database network restrictions default to allow-all until configured. The reviewed page states no fee. | `MITIGATABLE_FOR_SIM` |
| L33 | Those restrictions do not cover PostgREST, Storage, Auth, or client libraries. Ledger tables still need ordinary PostgreSQL privileges, and the application must not use those platform APIs. | `MITIGATABLE_FOR_SIM` |
| L34 | Auth, Storage, Realtime, Edge Functions, and PostgREST ship with a project. Using them would add a product dependency and weaken portability. Leaving them unused is documented at no extra cost. | `MITIGATABLE_FOR_SIM` |
| L35 | No database branching. Migration rehearsal stays on local PostgreSQL. | `ACCEPTABLE_FOR_SIM` |
| L36 | PrivateLink. | `REQUIRES_PAID_TIER` |
| L37 | Existing project plan, region, PostgreSQL major version, and endpoint identity. Not inspected, because this work must not connect. | `UNKNOWN` |
| L38 | Future Free-plan price and Nano size. Supabase says pricing may change and Free compute resources are subject to change. | `UNKNOWN` |

L1 and L2 are both about one missing failover mechanism. L1 is acceptable
only as a fail-closed initial SIM posture: the ledger stops, and committed
data is not treated as lost merely because the instance is down. L2 is the
autonomous-operation consequence: nobody and nothing in this design brings
the SIM ledger back on another node without a human or a later paid tier.

## 10. Backup and restore available at zero cost

Provider-managed backup and restore are not available at 0 USD.

- There is no Free-plan daily backup and no downloadable provider backup
  ([Z2], [Z9]).
- PITR is a paid add-on. Enabling it also requires paid Small compute
  ([Z2]).
- Dashboard restore of a provider backup, including the in-place restore
  that takes the project offline, is a paid-plan procedure. It is not a
  zero-cost tool.
- Deleting a project permanently removes provider-held backups. That does
  not create a backup; it removes one the Free plan does not offer ([Z2]).
- Pause resume can return the same project for up to one year ([Z5]).
  That is recovery of an availability pause, not a customer-held backup,
  and it is not a point-in-time choice.

What is available at zero incremental service cost:

- A logical export of the database, using a direct connection, or
  session-mode pooling when the client has no IPv6. The provider names
  `supabase db dump` for this export ([Z2], [Z14]). The portable tool is
  `pg_dump` against the application schemas. `supabase db dump` is a
  wrapper that runs `pg_dump` and filters managed schemas ([Z14], [Z15]).
- A logical restore with `psql` into a database the Operator already has.
  The zero-cost isolated target already authorized for drills is local
  PostgreSQL, not the SIM project and not a newly provisioned project
  ([Z15], [Z16]).
- Standard PostgreSQL durability of a commit on the single project disk,
  subject to L10 and to the absence of PITR.

No export was taken. No restore was run. No schedule was added.

## 11. Provider-neutral future strategy

This is a strategy for a later phase. It is not implemented. This
repository does not gain a runner, a workflow, a CLI wrapper, or a shell
script.

1. Export only application schemas, grants, and role names. Leave out
   Supabase-managed schemas and do not depend on them for ledger
   correctness.
2. Use a direct Postgres session, or session-mode pooling if the exporter
   is IPv4-only. Do not use transaction-mode pooling for the export,
   migrations, or long-running workers.
3. Keep passwords, connection strings, and project identifiers out of the
   export and out of git. After a restore, set role passwords from the
   SIM secret reference. Do not expect a dump to contain them.
4. Store the export encrypted, outside the Supabase project. The location
   and retention are an Operator decision not made here. Exports count
   toward the 5 GB uncached egress quota.
5. Restore first into an isolated local PostgreSQL database. Do not
   restore over the only SIM database as the first action. Do not point
   SIM at the local database afterward.
6. Treat Alembic as the schema history. Check that the restored schema
   matches the expected revision, including constraints and sequence
   values.
7. Check ledger counts and canonical digests before any later use of the
   restored copy.
8. Record the export time as the recovery point. At 0 USD the recovery
   point objective is that age. It is not the two-minute PITR figure.
9. If the export fails, the digest fails, or SIM cannot be reached, stop.
   There is no second provider endpoint, no local SIM fallback, and no
   LIVE fallback.
10. A later move to RDS, Cloud SQL, Neon, or another PostgreSQL uses the
    same logical export and Alembic history. A provider snapshot, a
    Supabase backup object, or a read replica is not the portability
    plan.

The same boundary as `docs/DB_DEPLOYMENT.md` §11 still applies: the
portable core is PostgreSQL schema and data. SQLAlchemy continues to
require only the `postgresql` dialect. The application continues to use
psycopg over the PostgreSQL wire protocol.

## 12. Environment isolation

The connection-source contract in `docs/DB_DEPLOYMENT.md` §7 is unchanged
and still proposed, not accepted. This constraint uses it as follows:

- DEV: isolated local PostgreSQL only.
- TEST: a separate disposable local PostgreSQL only. It must not share
  the developer database or the SIM project.
- SIM: if the Operator later accepts the candidate, one existing Supabase
  project and one SIM secret reference. No generic `DATABASE_URL`. No
  retry against local PostgreSQL, another project, a read replica, or a
  restored copy.
- LIVE: no project, network, secret, role, or connection source. LIVE
  must not fall back to SIM.
- A Supabase project used for SIM is not shared with DEV, TEST, or any
  future LIVE boundary. A database branch, if one were later purchased,
  is not that isolation boundary.
- Migration rehearsal and adversarial tests stay on local PostgreSQL.
- Network restrictions, TLS verification, and least-privilege roles are
  part of any later use. They are not configured by this change.

## 13. SIM suitability recommendation

**Verdict: `UNSUITABLE_FOR_UNATTENDED_AUTONOMOUS_SIM`;
`CONDITIONAL_CANDIDATE_FOR_ATTENDED_INITIAL_SIM`; `NOT_ACCEPTED`.**

Existing Supabase PostgreSQL, limited to the documented Free-plan
envelope, is not suitable for an unattended autonomous SIM ledger. Three
gaps are sufficient for that conclusion:

- inactivity pause can stop the only database during ordinary low use,
  and only a person can resume it (L3, L6);
- a node or zone failure has no automatic writer failover (L2);
- there is no provider backup or PITR, and this change deliberately does
  not build the logical-export process that would bound data loss (L7,
  L8, L9).

It remains a conditional candidate the Operator may consider for an
attended initial SIM ledger, and only for that, if the Operator accepts
all of the following at once:

- incremental service cost stays 0 USD, on the existing access, with no
  new project and no paid add-on;
- one Nano instance is enough, including its pause behavior, 500 MB
  quota, 5 GB egress quota, shared CPU, and lack of an SLA;
- durability is a PostgreSQL commit on that disk plus an Operator-owned
  logical export whose age is the accepted recovery point;
- high availability is not claimed and is not required for this initial
  step;
- SIM fails closed when the project is paused, read-only, restricted, or
  unreachable, and it does not fall back to local PostgreSQL;
- the application stays on SQLAlchemy and psycopg and does not adopt
  Supabase APIs;
- DEV and TEST stay on isolated local PostgreSQL.

This recommendation does not accept Supabase. It does not retire the RDS
evidence. It does not authorize a connection, a migration, or a secret.

## 14. Blockers and open facts

1. Unattended autonomous SIM is blocked by L2, L3, L6, L15, and L23 if
   those conditions occur. L3 can occur without a fault.
2. Provider backup and PITR are blocked at 0 USD (L7, L8). The substitute
   in §11 is not built.
3. The existing account's plan, region, version, and free-project quota
   are UNKNOWN (L20, L37). This review therefore uses the public Free
   envelope only.
4. Disk-durability statements conflict and stay unresolved (L10).
5. Multigres documentation conflict stays unresolved (L12).
6. `docs/CURRENT_STATE.md` and `docs/ENGINEERING_JOURNAL.md` were left
   unchanged on instruction. They do not yet point at this file. Group 2
   remains unauthorized in the merged `a03c737` text.
7. C1 (U-10) is untouched.

## 15. Evidence catalog

Repository evidence was read at `9631de3bd8a6a2e24c6833ca534c5e626fdb7b75`.
Web pages below were fetched on 2026-09-30. Pages without a visible
publication time are current only as fetched. Pricing and plan terms are
mutable.

### Repository

- **[R0]** `docs/DB_DEPLOYMENT.md` at the baseline above, especially §2,
  §3, §6, §7, §9, and §11. Supports the original RDS recommendation, the
  proposed SIM objectives, the environment contract, and the portability
  rules. This update does not modify that file.
- **[R1]** `docs/PHASE_2_PLAN.md` at the same baseline. Supports that the
  plan itself selected no provider. This update does not modify that file.
- **[R2]** `docs/CURRENT_STATE.md` at
  `a03c7372fe08b6b42618e72958892154ffebb511`. Supports that Phase 2
  implementation is unstarted, C1 is open, and Group 2 is unauthorized in
  that record. This update does not modify that file.

### Supabase, fetched 2026-09-30

- **[Z1]** Supabase, "Pricing," <https://supabase.com/pricing>. Supports
  the Free, Pro, Team, and Enterprise boundaries used above, including
  0 USD Free, two active projects, 500 MB, egress, pause, backup
  retention, PITR price, compute sizes, disk durability lines, and
  feature gates. Limitation: the page says pricing may change; it is not
  a quote for the existing account.
- **[Z2]** Supabase, "Database Backups,"
  <https://supabase.com/docs/guides/platform/backups>. Supports paid daily
  backup retention, the Free-plan `db dump` recommendation, PITR
  eligibility and the two-minute worst-case recovery point, PITR prices,
  and permanent backup deletion when a project is deleted. Limitation: no
  contractual restore-time guarantee.
- **[Z3]** Supabase, "Compute and Disk,"
  <https://supabase.com/docs/guides/platform/compute-and-disk>. Supports
  Nano price and size, shared-versus-dedicated CPU, disk IOPS and
  throughput, and connection, replication-slot, and pooler limits.
  Limitation: Free-plan compute resources are stated to be subject to
  change; the page does not prove Nano is sufficient for this ledger.
- **[Z4]** Supabase, "Connect to your database,"
  <https://supabase.com/docs/guides/database/connecting-to-postgres>.
  Supports direct, session, and transaction modes, IP versions, the paid
  dedicated pooler, TLS settings, and session-state limits of transaction
  mode. Limitation: no account was connected to test them.
- **[Z5]** Supabase, "Project Pausing,"
  <https://supabase.com/docs/guides/platform/free-project-pausing>.
  Supports the seven-day low-activity pause, the non-numeric threshold,
  dashboard resume, data retained on resume, the one-year window, and
  paid-plan exemption.
- **[Z6]** Supabase, "Understanding Database and Disk Size,"
  <https://supabase.com/docs/guides/platform/database-size>. Supports the
  500 MB read-only rule, the 1 GB Free disk, preinstalled size, WAL, and
  read-only SQLSTATE behavior.
- **[Z7]** Supabase, "Control your costs,"
  <https://supabase.com/docs/guides/platform/cost-control>. Supports that
  the Free plan is not charged and that the spend cap is a Pro feature.
- **[Z8]** Supabase, "Billing FAQ,"
  <https://supabase.com/docs/guides/platform/billing-faq>. Supports the
  two-project rule, fair-use restrictions, grace-period behavior, and
  that paused projects are not charged.
- **[Z9]** Supabase, "Production Checklist,"
  <https://supabase.com/docs/guides/deployment/going-into-prod>. Supports
  the Free-plan pause warning, backups not downloadable on Free, the
  99.8–99.9% default disk-durability statement, and the split between
  read replicas and PITR. Limitation: this conflicts with the durability
  percentages on [Z1]; unresolved.
- **[Z10]** Supabase, "Dedicated IPv4 Address for Ingress,"
  <https://supabase.com/docs/guides/platform/ipv4-address>. Supports
  IPv6-by-default direct connections, IPv4 session and transaction
  pooler endpoints, and the IPv4 add-on as Pro and above.
- **[Z11]** Supabase, "Manage IPv4 usage,"
  <https://supabase.com/docs/guides/platform/manage-your-usage/ipv4>.
  Supports 0.0055 USD per hour, about 4 USD per month.
- **[Z12]** Supabase, "Manage Egress usage,"
  <https://supabase.com/docs/guides/platform/manage-your-usage/egress>.
  Supports the 5 GB Free quotas and restriction rather than an overage
  price on Free.
- **[Z13]** Supabase, "Network Restrictions,"
  <https://supabase.com/docs/guides/platform/network-restrictions>.
  Supports per-project IP restrictions for Postgres and the pooler, the
  allow-all default, and the exclusion of HTTPS platform APIs.
  Limitation: no fee is stated; this review does not infer a hidden one,
  and it also does not prove the control is present on the unseen
  project.
- **[Z14]** Supabase, "supabase db dump,"
  <https://supabase.com/docs/reference/cli/supabase-db-dump>. Supports
  that the command dumps a remote database through `pg_dump`, excludes
  managed schemas, and omits data and custom roles unless asked.
- **[Z15]** Supabase, "Restore a Platform Project to Self-Hosted,"
  <https://supabase.com/docs/guides/self-hosting/restore-from-platform>.
  Supports logical export of roles, schema, and data, and restore with
  `psql`. Limitation: cited only as the provider's documented export
  shape. No command was run.
- **[Z16]** Supabase, "Backup and restore" (migrating within Supabase),
  <https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore>.
  Supports the same logical backup and `psql` restore pattern into a
  project the operator creates. This review does not create one. The
  authorized drill target remains local PostgreSQL.
- **[Z17]** Supabase, "Read Replicas,"
  <https://supabase.com/docs/guides/platform/read-replicas>. Supports
  asynchronous replication, read-only replicas, and replication lag.
- **[Z18]** Supabase, "Manage Read Replica usage,"
  <https://supabase.com/docs/guides/platform/manage-your-usage/read-replicas>.
  Supports that each replica is billed for compute, disk, provisioned
  IOPS and throughput, and IPv4 where enabled.
- **[Z19]** Supabase, "Multigres,"
  <https://supabase.com/docs/guides/database/multigres>. Direct fetch on
  2026-09-30 returned 404. A same-day web index of that URL described
  public alpha, paid-organization eligibility, no uptime SLA, and a
  non-production positioning. **Conflict unresolved. Not used as an
  eligible capability.**
