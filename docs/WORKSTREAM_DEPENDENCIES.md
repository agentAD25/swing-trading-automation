# Workstream Dependencies

Cross-lane dependency registry. Identifiers are stable. No specialist may mark
another lane's dependency resolved without cited evidence. Conversation claims
alone are insufficient.

Last attestation date: 2026-10-08
Canonical main baseline: `41218abb2eda5f06001703fb83c2cb9e43e5ec2e` /
`39f0ab05c49b533270964b303601539feeff570f`

## Severity vocabulary

- `BLOCKING` — requesting lane cannot honestly advance past its current gate
- `NONBLOCKING` — tracked residual; does not alone freeze the requesting lane tip

## Resolution authority vocabulary

- `OPERATOR` — human Operator Level 0 decision
- `PROVIDER` — external provider confirmation
- `COORDINATOR` — Lane 1 reconciliation / contract freeze prep
- `SPECIALIST` — owning specialist lane with evidence
- `CROSS_WORKSTREAM_CONTRACT_CONFLICT` — human or architectural resolution required; coordinator must not silently pick a conflicting specialist version

## Dependency records

### DEP-TS-001

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-TS-001` |
| Requesting lane | `LANE-2` TradeStation / Broker |
| Providing lane | External TradeStation / Operator-mediated provider channel |
| Required contract or artifact | Native PKCE callback confirmation for future attended probe design |
| Exact blocking question | What exact callback/redirect behavior does TradeStation require for the native PKCE client path that a future attended probe would use? |
| Required evidence | First-party provider confirmation recorded without credentials or live auth; Proposed ADR-0005 updated only with evidenced bounds |
| Severity | `BLOCKING` for operational probe design closure |
| Blocking/nonblocking | Blocking |
| Resolution authority | `PROVIDER` with Operator recording; coordinator reconciles into contracts |
| Current state | `OPEN` — Lane 2 state `WAITING_PROVIDER` on draft PR #22 head `a6c5f1d7109e156eb0e9257216c3b5dbed17f653` |

### DEP-GMAIL-001

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-GMAIL-001` |
| Requesting lane | `LANE-3` Gmail / Signal Ingestion |
| Providing lane | Operator (credential/OAuth setup authority) |
| Required contract or artifact | Google OAuth setup for read-only corpus acquisition under Proposed ADR-0004 |
| Exact blocking question | Has the Operator completed the authorized Google OAuth setup required for Gate A read-only corpus work? |
| Required evidence | Operator attestation that setup exists out-of-band; no secrets in Git, chat, logs, or PR text |
| Severity | `BLOCKING` for Gate A progression beyond docs-only proposal |
| Blocking/nonblocking | Blocking |
| Resolution authority | `OPERATOR` |
| Current state | `OPEN` — Lane 3 state `WAITING_OPERATOR` on draft PR #21 head `a2cef6f3527b2aab7319a2628874fcdcaf03acac` |

### DEP-DB-001

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-DB-001` |
| Requesting lane | `LANE-4` Database / PostgreSQL Infrastructure |
| Providing lane | Operator (provider selection) with Lane 4 evidence |
| Required contract or artifact | Zero-cost remotely accessible PostgreSQL selection for autonomous-SIM-era needs |
| Exact blocking question | Which zero-incremental-cost remotely accessible PostgreSQL option, if any, is selected under `INITIAL_DATABASE_INCREMENTAL_SERVICE_COST = 0 USD`? |
| Required evidence | Operator-accepted selection ADR or current-state authorization; Supabase remains candidate and **NOT_ACCEPTED** until then |
| Severity | `BLOCKING` for remote autonomous-SIM database use |
| Blocking/nonblocking | Blocking |
| Resolution authority | `OPERATOR` |
| Current state | `OPEN` — remote autonomous-SIM database not selected; local PostgreSQL inaccessible from Cursor Cloud |

### DEP-DB-002

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-DB-002` |
| Requesting lane | `LANE-4` Database / PostgreSQL Infrastructure |
| Providing lane | `LANE-4` with coordinator certification review |
| Required contract or artifact | Accepted execution evidence for twelve TokenStore PostgreSQL tests |
| Exact blocking question | Where is the accepted, reproducible execution evidence for the twelve TokenStore PostgreSQL tests? |
| Required evidence | Exact command, environment identity, pass count, and SHA/tree; skips must remain skips |
| Severity | `BLOCKING` for TokenStore PostgreSQL certification |
| Blocking/nonblocking | Blocking |
| Resolution authority | `SPECIALIST` evidence + coordinator certification review; Operator for acceptance of certification claims |
| Current state | `OPEN` — `NO_ACCEPTED_EVIDENCE_FOUND` per main journal/current-state residual |

### DEP-CORE-001

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-CORE-001` |
| Requesting lane | Shared (`LANE-3` offline parser consumers; future broker sizing) |
| Providing lane | Operator with coordinator ADR drafting |
| Required contract or artifact | Quantity rounding policy |
| Exact blocking question | What quantity rounding policy is accepted for canonical economic instructions? |
| Required evidence | Accepted ADR or explicit Operator decision in `docs/CURRENT_STATE.md` |
| Severity | `BLOCKING` for any path that would invent rounding |
| Blocking/nonblocking | Blocking for that economic path; nonblocking for unrelated docs-only lanes |
| Resolution authority | `OPERATOR` (`CROSS_WORKSTREAM_CONTRACT_CONFLICT` if specialist branches diverge) |
| Current state | `OPEN` — `UNRESOLVED` on main after Group 4A integration |

### DEP-CORE-002

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-CORE-002` |
| Requesting lane | Shared (`LANE-3`, future scheduling/broker session logic) |
| Providing lane | Operator with coordinator ADR drafting |
| Required contract or artifact | Market calendar and timezone policy |
| Exact blocking question | Which market calendar and timezone policy are accepted for session dates and relative calendar language? |
| Required evidence | Accepted ADR or explicit Operator decision in `docs/CURRENT_STATE.md` |
| Severity | `BLOCKING` for calendar-dependent economic acceptance |
| Blocking/nonblocking | Blocking for that path; nonblocking for unrelated docs-only lanes |
| Resolution authority | `OPERATOR` (`CROSS_WORKSTREAM_CONTRACT_CONFLICT` if specialist branches diverge) |
| Current state | `OPEN` — timezone `UNSTATED`; market calendar `UNRESOLVED` on main |

## Conflict return token

When overlapping specialist edits to coordination-sensitive files cannot be
reconciled without choosing between incompatible contracts, Lane 1 must return:

`CROSS_WORKSTREAM_CONTRACT_CONFLICT`

and stop silent selection. See `docs/WORKSTREAM_OWNERSHIP.md` shared-file list.
