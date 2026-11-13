# Item 29 Stage E evidence matrix

Status of this file: branch evidence for proposed Item 37. It is not
canonical certification. It does not make Item 37 effective, does not
authorize Stage F execution, and does not authorize the three Item 30
source paths.

Observation time: 2026-11-13, Cursor Local Windows, read-only. No SQL
was sent to either PostgreSQL instance during this observation. No
scheduled task, service, configuration file, or application path was
modified. No secret is recorded here.

Parent main at branch creation: `0890546d63eaa0e0e5b917675071bc662b1e2d50`,
tree `0b17e98773a544a3fb11937fa2e2b7301a331161`.

Stage A baseline used for comparison: the same-day attended inventory
before `initdb`, in which VWAP and SupaOpti were not running, six eBay
tasks were present with two Disabled and four Ready, none of those tasks
was Running, and functional health was `NOT_VERIFIED`.

Classifications are only `PASS`, `FAIL`, `SKIPPED`, or `NOT_RUN`.
`blocks_stage_f` is `yes` only under the unamended Item 29 rule. Proposed
Item 37 would change that block for Dimension C only after Item 37 is
accepted and effective.

## Dimension A — infrastructure security

| test_id | dimension | requirement | source_evidence | observed_identity | execution_environment | execution_status | pass_fail_reason | requires_operator_approval | blocks_stage_f |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SE-A-01 | A | Service identity | `Get-CimInstance Win32_Service` | `postgresql-swingtrade-16`, Running, Manual, `NT SERVICE\postgresql-swingtrade-16`, data directory present in the service path, path does not name port 5432 | Cursor Local Windows, read-only, 2026-11-13 | PASS | Service name, account, start mode, and data-directory path match the provisioned cluster. | no | no |
| SE-A-02 | A | System identifier | `pg_controldata` on `D:\SwingTrade\PostgreSQL16\data` | `7707684291752896980`, cluster state `in production` | Cursor Local Windows, read-only, 2026-11-13 | PASS | Identifier matches the initialized cluster. Port number was not used as the identity. | no | no |
| SE-A-03 | A | Data-directory identity | Service path and `pg_controldata` directory argument | `D:\SwingTrade\PostgreSQL16\data` | Cursor Local Windows, read-only, 2026-11-13 | PASS | The running service path names the directory whose control file produced SE-A-02. | no | no |
| SE-A-04 | A | IPv4 loopback binding | `netstat -ano -p tcp` and active `postgresql.conf` | One listener, `127.0.0.1:5433`, PID 41344; `listen_addresses = '127.0.0.1'` | Cursor Local Windows, read-only, 2026-11-13 | PASS | The new listener is IPv4 loopback only. | no | no |
| SE-A-05 | A | No IPv6 listener | `netstat -ano -p tcpv6` | Zero lines containing `:5433` | Cursor Local Windows, read-only, 2026-11-13 | PASS | No IPv6 socket was observed for port 5433. | no | no |
| SE-A-06 | A | No external listener | `netstat` filtered against non-loopback `:5433` | Count 0 | Cursor Local Windows, read-only, 2026-11-13 | PASS | No non-loopback 5433 listener was observed. | no | no |
| SE-A-07 | A | Port 5433 isolation | `netstat` and active `port = 5433` | One `127.0.0.1:5433` listener | Cursor Local Windows, read-only, 2026-11-13 | PASS | The dedicated port is bound once, on loopback. | no | no |
| SE-A-08 | A | SCRAM acceptance | Operator `ITEM29_STAGE_E_AUTH_COMPLETE` positive authentication, plus current `pg_hba.conf` and `password_encryption = 'scram-sha-256'` | One active rule: `host all all 127.0.0.1/32 scram-sha-256` | Prior Operator session for the live handshake; this session re-read configuration only | PASS | The live handshake was not replayed. The system identifier, service, and single SCRAM rule are unchanged, so the prior successful handshake remains bound to this cluster. | no | no |
| SE-A-09 | A | Incorrect-password rejection | Operator `ITEM29_STAGE_E_AUTH_COMPLETE` negative authentication, exit 2 | Same cluster as SE-A-02 | Prior Operator session; not replayed | PASS | A wrong password was rejected in the prior attended test. Replaying it would be a new authentication attempt and was not done. | no | no |
| SE-A-10 | A | No trust authentication | Active non-comment lines of the new `pg_hba.conf` | `NEW_HBA_TRUST=0` | Cursor Local Windows, read-only, 2026-11-13 | PASS | The only active rule is SCRAM. No trust rule is present. | no | no |
| SE-A-11 | A | Least-privilege roles | Operator `ITEM29_PROVISIONING_COMPLETE` checkpoint H | `swingtrade_owner` NOLOGIN; `swingtrade_migrator`, `swingtrade_app`, and `swingtrade_test_runner` LOGIN and NOINHERIT | Prior Operator session; catalog was not re-queried | PASS | The Operator's fail-closed catalog assertions passed, and this session confirmed the same system identifier and HBA. No privilege was expanded. | no | no |
| SE-A-12 | A | No unauthorized SUPERUSER, CREATEDB, CREATEROLE, REPLICATION, or BYPASSRLS | Operator checkpoint H role-attribute matrix | Those five attributes false for the four non-bootstrap roles | Prior Operator session; catalog was not re-queried | PASS | Reuse is limited to the unchanged cluster identity. This session did not grant any attribute. | no | no |
| SE-A-13 | A | No unintended role membership | Operator checkpoint H `MEMBERSHIP=0` | No membership of `swingtrade_migrator` in `swingtrade_owner` | Prior Operator session; catalog was not re-queried | PASS | The shared-owner `SET ROLE` path was not created. It was not re-queried. | no | no |
| SE-A-14 | A | Database CONNECT isolation | Operator checkpoint I negative connections | Test runner denied `swingtrade_receipt_dev`; app denied `swingtrade_receipt_test`; migrator denied `swingtrade_receipt_dev` | Prior Operator session; not replayed | PASS | The denials were executed before this review. Repeating them would open new authenticated sessions, so they were not repeated. | no | no |
| SE-A-15 | A | Schema permissions | Operator checkpoint H schema-privilege matrix and checkpoint I create-table denials | App USAGE on dev only; test runner USAGE on test only; migrator USAGE and CREATE on test public only; both create probes absent afterward | Prior Operator session; not replayed | PASS | The probes were denied and reported absent. No schema change was made in this session. | no | no |
| SE-A-16 | A | No unauthorized PUBLIC privileges | Operator checkpoint H PUBLIC ACL result | PUBLIC lacked CONNECT on the two new databases, `postgres`, and `template1` except the expected remaining TEMPORARY on `postgres`; PUBLIC schema privileges were none | Prior Operator session; not replayed | PASS | The result is the prior catalog assertion, tied to the reattested system identifier. | no | no |
| SE-A-17 | A | No secrets in evidence | This matrix and the Item 37 text | No password, token, connection URL, or command-line secret | Cursor Local Windows, 2026-11-13 | PASS | Evidence names services, ports, roles, and hashes only. | no | no |
| SE-A-18 | A | Protected 5432 preservation | Service query and SHA-256 of the protected configuration files | `postgresql-x64-16` Running, Automatic, `NT AUTHORITY\NetworkService`; `postgresql.conf` `E136B69566CB9A42E1424F4D92CB3CF153EEBAA3672EEF09F2E5BA4728404611`; `pg_hba.conf` `D704A72F523AA44A5EACFD8A3C9BB5CEA0A6FB7470F67B456D83FE0A0393D0FA` | Cursor Local Windows, read-only, 2026-11-13 | PASS | Both preserved hashes match. The protected service was not restarted or edited. Its pre-existing `0.0.0.0:5432` listener remains and was not changed. | no | no |
| SE-A-19 | A | No leftover security-test objects | Operator checkpoint I probe count | Both create-table probes reported absent | Prior Operator session; catalog was not re-queried | PASS | The prior session reported a zero probe count and did not delete through this review. No new probe was created. | no | no |
| SE-A-20 | A | No unintended network exposure of the new cluster | SE-A-04 through SE-A-07 | `127.0.0.1:5433` only | Cursor Local Windows, read-only, 2026-11-13 | PASS | Exposure finding for the new cluster is loopback-only. The protected instance's pre-existing wildcard listener is outside this test and was not remediated. | no | no |

## Dimension B — protected baseline preservation

| test_id | dimension | requirement | source_evidence | observed_identity | execution_environment | execution_status | pass_fail_reason | requires_operator_approval | blocks_stage_f |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SE-B-01 | B | Existing services remain intact | SE-A-01 and SE-A-18 | Both PostgreSQL services Running in their prior start modes | Cursor Local Windows, read-only, 2026-11-13 | PASS | No service was started, stopped, or reconfigured by this review. | no | no |
| SE-B-02 | B | Protected application paths unchanged by this work | Prior path observation and this session's read-only boundary | VWAP and SupaOpti under `D:\alphadrip database\supabase-opti-database`; eBay under `D:\alphadrip_ebayops\ebay-standalone` | Cursor Local Windows, 2026-11-13 | PASS | This session did not write to those paths. Byte-level comparison with a stored Stage A directory hash was not available and is not claimed. | no | no |
| SE-B-03 | B | Protected configuration hashes unchanged | SE-A-18 | Both expected hashes matched | Cursor Local Windows, read-only, 2026-11-13 | PASS | The protected configuration files match the preserved hashes. | no | no |
| SE-B-04 | B | Scheduled-task state unchanged | `Get-ScheduledTask` | Order Scanner Disabled; SourceWatchlistScan Disabled; BatchWatchlistScan Ready; DailyScanEmail Ready; GmailOAuthHealth Ready; WeeklyInventoryEmail Ready | Cursor Local Windows, read-only, 2026-11-13 | PASS | Enabled and Disabled states match the Stage A record. No task was enabled, disabled, or started. | no | no |
| SE-B-05 | B | No post-baseline task execution | `Get-ScheduledTaskInfo` | Latest last-run values remain 2026-06-09, never-run, 2026-11-07, 2026-11-13 05:00, 2026-11-12 18:00, and 2026-11-09 | Cursor Local Windows, read-only, 2026-11-13 | PASS | None of the six last-run times is after the Stage A baseline. Weekly result 1 remains the pre-baseline result. | no | no |
| SE-B-06 | B | Task-definition byte identity versus Stage A | `Export-ScheduledTask` SHA-256 recorded in this file | Hashes recorded below; no Stage A hash exists to compare | Cursor Local Windows, read-only, 2026-11-13 | NOT_RUN | Current definition hashes were captured for a later comparison. They do not prove the XML was unchanged, and they are not converted to PASS. | no | no |
| SE-B-07 | B | Previously dormant applications remain dormant | Process census | `dbeaver` 1; research-named `node.exe` or `python.exe` matches 0; no VWAP, SupaOpti, mdpipe, or eBay service | Cursor Local Windows, read-only, 2026-11-13 | PASS | The workloads that were dormant at Stage A are still not executing. DBeaver's presence matches the baseline and is not application functional health. | no | no |
| SE-B-08 | B | No new adverse post-provisioning application event | SE-B-05 and SE-B-07 | No task entered Running and no research process appeared after baseline | Cursor Local Windows, read-only, 2026-11-13 | PASS | Absence of a new failure is preservation evidence only. It is not functional PASS. | no | no |

Current task-definition hashes, first recorded by this review:

| Task | SHA-256 |
| --- | --- |
| AlphaDrip eBay Order Scanner | `194FEE86A958D014599120ECA0E9742A333EE384ED1DF42C06E7A2B77A2E04FF` |
| AlphaDrip_eBay_Arbitrage_1769_L32E_SourceWatchlistScan | `A7A82765CDD85C9968A2F79450DCB181CFFD5D0F71913005BB0AA0166FA86AD5` |
| AlphaDrip_eBay_Arbitrage_BatchWatchlistScan | `B284EEBA0C6968FD539F123402E919854A14EFA515A5B326203E95019D7E1991` |
| AlphaDrip_eBay_Arbitrage_DailyScanEmail | `82C29273A6A6316ABCA3630385F7CB112145411DAA6310C71D1ACC3B43145ECC` |
| AlphaDrip_eBay_Arbitrage_GmailOAuthHealth | `1D928AA1A7496CA1EF209346AB14B72158BE8B8A770ED4398E1FE64B55D545CB` |
| AlphaDrip_eBay_Arbitrage_WeeklyInventoryEmail | `5443B02F85F3089675FD15A78BC8F9EABFFBA2A30F33FC161D5BC66EC3A82981` |

## Dimension C — application functional verification

| test_id | dimension | requirement | source_evidence | observed_identity | execution_environment | execution_status | pass_fail_reason | requires_operator_approval | blocks_stage_f |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SE-C-01 | C | VWAP / mdpipe functional execution | Process, service, and task inspection | On-demand research tree; no resident service or scheduled task; not executing | Cursor Local Windows, read-only, 2026-11-13 | NOT_RUN | No authorized functional test was executed. Dormancy is not a functional pass. | yes | yes |
| SE-C-02 | C | SupaOpti functional execution | Process, service, and task inspection | On-demand research in the same tree; not executing | Cursor Local Windows, read-only, 2026-11-13 | NOT_RUN | No authorized functional test was executed. Dormancy is not a functional pass. | yes | yes |
| SE-C-03 | C | eBay functional execution | Task history and existing logs from before Stage A | Six tasks installed; none has completed since the Stage A baseline | Cursor Local Windows, read-only, 2026-11-13 | NOT_RUN | Scheduler state and older logs were not treated as a new functional pass. No task was started. | yes | yes |

Under the unamended Item 29 sentence, SE-C-01, SE-C-02, and SE-C-03 block a
complete Stage E pass and therefore block Stage F. Proposed Item 37 removes
that block only after it becomes effective, and only while C remains recorded
as `NOT_RUN` rather than `PASS`.

## Stage F preparation

Stage F was not executed. The committed `alembic.ini` names port 5432 and
must not be used. `migrations/env.py` reads that file's URL and does not
read `SWINGTRADE_TEST_POSTGRES_URL`. A future authorized session overrides
the URL in process memory from that environment variable and refuses the
process if the variable is unset, names port 5432, or names a database
other than `swingtrade_receipt_test`.

The future preflight, in order, is:

1. Re-read service `postgresql-swingtrade-16`, its data directory, and
   `pg_controldata` system identifier `7707684291752896980`.
2. Confirm the only 5433 listener is `127.0.0.1`.
3. Confirm protected hashes still match SE-A-18. Do not connect to port 5432.
4. In the migrator session, require `inet_server_port()` 5433,
   `current_database()` `swingtrade_receipt_test`, `current_user`
   `swingtrade_migrator`, and `pg_control_system().system_identifier`
   `7707684291752896980`. PostgreSQL 16 documents
   `pg_control_system()` as a control-file information function. If that
   function is denied to the migrator, stop. Do not use the bootstrap role
   and do not infer identity from the port.
5. Read `alembic_version` before migrating. An empty test database may have
   no version row. Any revision other than absent or a prefix of
   `0001_offline_foundation`, `0002_canonical_order_intents`, and
   `0003_durable_dry_run_observation` stops the session.
6. Upgrade only through `0003_durable_dry_run_observation`. Do not run
   revision 0004. Do not call `SET ROLE swingtrade_owner`.
7. Run the existing PostgreSQL tests, then `python -m pytest tests`.
8. Compare the protected service and hashes again.
9. Stop on the first mandatory failure. Skips remain skips.

Existing tests that use the process-scoped URL, and which stay skipped
while it is unset:

- `tests/integration/test_postgres_intent_identity.py`
- `tests/broker_sim/test_dry_run_adapter.py`
- `tests/offline/test_token_store.py`

Token-store cases that require a table revisions 0001 through 0003 do not
create remain `NOT_RUN`, as Item 29 already states. Receipt `NEW`,
`REPLAY`, and `CONFLICT` coverage belongs to Item 30 and is not created
or executed here.

## Item 30

Item 30 source editing remains closed. The future files, after both a
Stage E security pass under effective governance and a Stage F isolated-test
prerequisite pass for this same cluster, are only:

- `src/swingtrade/postgres_receipt_store.py`
- `tests/integration/test_postgres_receipt_store.py`
- `migrations/versions/0004_instruction_receipts.py`

The store must implement the existing `ReceiptStore.compare_and_insert`
contract and `admit_instruction_receipt`. Those tests are not part of
Stage F.
