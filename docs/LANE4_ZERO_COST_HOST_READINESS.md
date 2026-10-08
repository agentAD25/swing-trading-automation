# Lane 4 zero-cost host readiness

- Workstream: `LANE-4`
- Status: comparative evidence for Operator host selection.
  **Neon Free is not ACCEPTED. Supabase Free is not ACCEPTED.
  No project, billing account, connection, or database was created.**
- Access date (UTC): 2026-10-08
- Constraint: `INITIAL_DATABASE_INCREMENTAL_SERVICE_COST = 0 USD`
- Prior research left unchanged:
  `docs/LANE4_ZERO_COST_BOOTSTRAP_RESEARCH.md`,
  `docs/P2_C_ZERO_INCREMENTAL_COST.md`, `docs/DB_DEPLOYMENT.md`

## 1. Recommendation

**Preferred unevaluated candidate: Neon Free.**

Supabase Free remains the alternative. Neither is selected. This
recommendation does not authorize provisioning, a connection string, or
integration.

Neon is preferred for evaluation because the Operator named it, and
because the fetched Free envelope includes a 6-hour instant-restore
history and does not bill overages. Supabase Free has no automatic
backups, and point-in-time recovery is a paid add-on. Both envelopes
fail an unattended always-on SIM. Neon’s idle suspend is 5 minutes and
cannot be disabled on Free. Supabase pauses a Free project after about
a week of low activity.

`src/swingtrade/offline/token_store.py` still refuses host markers
`neon.tech` and `supabase`. Selecting a provider later still requires a
separate authorized code change and a new verification by an agent other
than the author of that change.

## 2. Facts fetched 2026-10-08

### Neon Free

Sources: [N1] Plans, [N2] Pricing, [N3] Free-plan quotas, [N4] Compute
lifecycle, [N5] High availability, [N6] History window, [N7] Connection
pooling, [N8] Secure connections, [N9] Compatibility.

| Topic | Documented fact |
| --- | --- |
| Price | $0/month. No credit card required. Not a trial ([N2]). |
| Compute | 100 CU-hours per project per month. 1 CU is about 4 GB RAM. Minimum size cited is 0.25 CU (about 1 GB RAM). Autoscaling up to 2 CU ([N1], [N2]). |
| Storage | 1 GB Postgres per project and 20 GB across projects ([N1], [N2], [N3]). |
| Egress | 5 GB public network transfer per project per month ([N1]). |
| Idle behavior | Scale to zero after 5 minutes without active queries. Cannot be disabled on Free ([N1], [N4]). An idle-in-transaction session counts as active ([N4]). |
| Cold start | Activation is generally a few hundred milliseconds. Idle longer than 7 days can take longer. First queries are slower while buffers are cold ([N4]). |
| Connections | Direct `max_connections` at 0.25 CU is 104, of which 7 are reserved ([N7], [N9]). PgBouncer transaction-mode pooler accepts up to 10,000 clients. `query_wait_timeout` is 120 seconds. Pooled connections do not support session `SET`, `LISTEN/NOTIFY`, or session advisory locks ([N7]). |
| TLS | Non-TLS connections are rejected. Neon recommends `sslmode=verify-full`. Certificate chain uses Let’s Encrypt ISRG Root X1 ([N8]). |
| Postgres version | Major versions 14, 15, 16, 17, and 18. The project creator chooses the major version. Minor updates are applied by Neon ([N9]). |
| Extensions | Many, including pgvector, PostGIS, and TimescaleDB ([N2]). This repository’s Alembic migrations create no extension. |
| Timeouts | Published parameter table sets `idle_in_transaction_session_timeout` to 300000 ms (5 minutes). `statement_timeout` is not in that table ([N9]). |
| Backup / PITR | History window default and maximum on Free: 6 hours, capped at 1 GB of change history, no history charge. One manual snapshot. Longer instant restore is paid ([N1], [N6]). |
| Export | Pooling guide says `pg_dump` / `pg_restore` need a direct connection, not the pooler ([N7]). History-window page lists `pg_dump` backup guides ([N6]). |
| Quota exhaustion | CU-hours or egress exhausted: compute suspends until the next billing period or an upgrade. Storage above 1 GB per project, or 20 GB account-wide, blocks writes that would grow storage. Data is not deleted. Free does not bill those overages ([N2], [N3]). |
| SLA | Uptime SLA is a Scale-plan feature, not Free ([N1]). |
| HA | Storage is multi-AZ. Compute is rescheduled, not a hot standby. Region failure is not cross-region replicated. Recovery examples: seconds for a Postgres crash, 1–2 minutes for a node, 1–10 minutes for an AZ, about 5 minutes for an unresponsive endpoint ([N5]). |

### Supabase Free

Sources: [S1] Pricing, [S2] Compute and disk, [S3] Pausing, [S4]
Backups, [S5] Database size, [S6] IPv4 add-on, [S7] Billing FAQ,
[S8] Upgrading.

| Topic | Documented fact |
| --- | --- |
| Price | $0/month. Two active projects. 500 MB database size. 5 GB egress ([S1]). |
| Compute | Nano: shared CPU, up to 0.5 GB memory, recommended max database size 500 MB. Free compute resources are subject to change ([S2]). |
| Connections | Nano: 60 database connections and 200 pooler clients ([S2]). |
| Idle behavior | Free projects pause after about one week of insufficient database activity. A few user requests each day over the previous week is described as typically enough to avoid pausing. Paid plans do not pause. Restore is available for up to 1 year and is a dashboard action ([S3]). |
| Cold start | The pause guide describes restore back to the previous state. It does not publish a numeric resume latency ([S3]). |
| Network | Direct connections are IPv6 unless the dedicated IPv4 add-on is enabled. That add-on is Pro plans and above. Shared Supavisor pooler endpoints are IPv4 ([S6]). |
| TLS | Postgres connections are allowed without SSL until enforcement is enabled in Database Settings. Client default `prefer` tries SSL and can fall back to plaintext. `require` encrypts without verifying the certificate. `verify-full` is the documented recommendation once enforcement is on, and it needs the dashboard CA ([S9]). |
| Postgres version | Platform upgrade docs discuss Postgres 15 and 17. The “print version” example output `15.1` is illustrative. The exact major version of a new hosted Free project was not pinned by the pages fetched ([S8]). |
| Extensions | A new project is described as already using about 40–60 MB for preinstalled extensions and catalogs ([S5]). This application’s migrations do not `CREATE EXTENSION`. |
| Backup / PITR | Automatic daily backups are Pro, Team, and Enterprise. Free projects are told to export with `supabase db dump`. PITR is a paid add-on from about $100/month per 7 days and requires at least a Small compute add-on ([S1], [S4]). |
| Quota exhaustion | Database size above 500 MB puts a Free project into read-only mode. That is database size, not the 1 GB disk figure. Free does not use the paid disk-size meter ([S5]). Billing FAQ: exceeding Free quotas leads to notification and service restrictions, lifted by the next cycle or by upgrading. Spend caps are described on the Pro plan ([S1], [S7]). |
| SLA | Uptime SLA is Enterprise, not Free ([S1]). |

## 3. Scheduled market-hours use

**Assumption, not a provider guarantee.** US regular-hours length of 6.5
hours and about 21 sessions in a month are planning figures only.
`DEP-CORE-002` (calendar and timezone) is unresolved, so these figures
are not a trading calendar.

| Workload | Neon Free at 0.25 CU | Supabase Free |
| --- | --- | --- |
| Always on for a 730-hour month | 0.25 × 730 = 182.5 CU-hours, above the 100 CU-hour allowance. Documented minimum compute cannot stay active all month. | Pause is inactivity-based, not a CU-hour cap. Always-on still has no Free backups and no SLA. |
| Active only for 136.5 session-hours (6.5 × 21), then fully idle | 0.25 × 136.5 = 34.125 CU-hours, inside 100, if compute stays at 0.25 CU and does not stay awake between sessions. | Daily session queries are the kind of activity the pause guide says can avoid a 7-day pause. A gap of low activity over a week can still pause the project. |
| Same 136.5 hours if autoscaling reaches 2 CU | 2 × 136.5 = 273 CU-hours, above 100. Compute would suspend when the quota is exhausted ([N3]). | Nano does not have this CU-hour meter. Shared CPU and 500 MB remain the limits. |

Neither provider documents that a scheduled trading session will be
available at the opening bell. Neon adds cold-start latency after idle,
longer after 7 days. Supabase restore after pause is manual. Quota
suspension or read-only mode would block new durable writes.

## 4. Inferences

1. A low-frequency, one-user service can fit inside Neon’s 100 CU-hours
   only when active compute stays near 0.25 CU and well below 400 hours
   in the billing month. That is an inference from the published formula
   `compute size × hours running`.
2. Supabase Free is the weaker recovery candidate under a zero-dollar
   rule because automatic backups and PITR are outside the Free
   envelope.
3. The zero-dollar Supabase network path is the shared pooler. The
   dedicated IPv4 add-on is paid and is out of scope.

## 5. Assumptions and open questions

### Assumptions

1. Session-hour arithmetic above is planning math, not measured usage.
2. This application’s schema does not require a non-default extension.
3. Public prices can change after 2026-10-08.

### Open questions

1. Which Postgres major version the Operator would choose on Neon.
   Supported set is 14–18. Local evidence used 16.15.
2. The exact major version Supabase assigns to a new hosted Free
   project. Not pinned here.
3. Supabase `statement_timeout` defaults. Not in the pages fetched for
   this packet.
4. Whether the Operator already has a Free slot on either vendor.
   Not inspected. No account was opened.

## 6. Source catalog

### Neon

- **[N1]** Neon, “Plans,” https://neon.com/docs/introduction/plans
- **[N2]** Neon, “Pricing,” https://neon.com/pricing.md
- **[N3]** Neon, “What are the limits and quotas for Neon's Free plan?”
  https://neon.com/faqs/free-plan-limits-and-quotas
- **[N4]** Neon, “Compute lifecycle,”
  https://neon.com/docs/introduction/compute-lifecycle
- **[N5]** Neon, “High Availability (HA) in Neon,”
  https://neon.com/docs/introduction/high-availability
- **[N6]** Neon, “History window,”
  https://neon.com/docs/postgres/backup-restore/history-window
- **[N7]** Neon, “Connection pooling,”
  https://neon.com/docs/connect/connection-pooling
- **[N8]** Neon, “Connect to Neon securely,”
  https://neon.com/docs/connect/connect-securely
- **[N9]** Neon, “Postgres compatibility,”
  https://neon.com/docs/reference/compatibility

### Supabase

- **[S1]** Supabase, “Pricing,” https://supabase.com/pricing
- **[S2]** Supabase, “Compute and Disk,”
  https://supabase.com/docs/guides/platform/compute-and-disk
- **[S3]** Supabase, “Project Pausing,”
  https://supabase.com/docs/guides/platform/free-project-pausing
- **[S4]** Supabase, “Database Backups,”
  https://supabase.com/docs/guides/platform/backups
- **[S5]** Supabase, “Understanding Database and Disk Size,”
  https://supabase.com/docs/guides/platform/database-size
- **[S6]** Supabase, “Dedicated IPv4 Address for Ingress,”
  https://supabase.com/docs/guides/platform/ipv4-address
- **[S7]** Supabase, “Billing FAQ,”
  https://supabase.com/docs/guides/platform/billing-faq
- **[S8]** Supabase, “Upgrading,”
  https://supabase.com/docs/guides/platform/migrating-and-upgrading-projects
- **[S9]** Supabase, “Postgres SSL Enforcement,”
  https://supabase.com/docs/guides/platform/ssl-enforcement
