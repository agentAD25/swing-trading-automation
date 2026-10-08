# Workstream Status Registry

Authoritative four-lane status for concurrent Phase 2 specialist work.
Conversation claims are never authoritative by themselves. Resolve conflicts
using `docs/INTEGRATION_PROTOCOL.md` and the operating hierarchy in
`docs/WORKSTREAM_OWNERSHIP.md`.

Last attestation date: 2026-10-08
Canonical main baseline (attested): `f5880cfcfaa6d994f369e04d73c844fd1402d74c`
Canonical main tree (attested): `1700b1b442ef72b31b24aa8dcdf65e43525376e4`
Attestation method: post-integration `gh api`/`git` after history-preserving
fast-forward of PR #23 tip `f5880cfcfaa6d994f369e04d73c844fd1402d74c` onto prior main `41218abb2eda5f06001703fb83c2cb9e43e5ec2e`.

## Controlled states

Only these values are permitted for `Current state`:

`NOT_STARTED` · `READY` · `ACTIVE` · `WAITING_OPERATOR` · `WAITING_PROVIDER` ·
`BLOCKED` · `READY_FOR_VERIFICATION` · `VERIFIED` · `READY_FOR_INTEGRATION` ·
`INTEGRATED` · `SUPERSEDED`

Do not treat a Proposed ADR as Accepted. Do not treat passing tests as
integration approval. Do not treat provider confirmation as operational
certification.

## Lane 1 — Integration / Coordinator

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-1` |
| Workstream name | Integration / Coordinator |
| Current state | `INTEGRATED` |
| Current branch | `main` (via PR #23 history-preserving fast-forward) |
| PR number | PR #23 (MERGED) |
| Last attested SHA | Integrated tip `f5880cfcfaa6d994f369e04d73c844fd1402d74c` (includes independently verified `3676e11` ancestry plus evidence/whitespace successors) |
| Last attested tree | `1700b1b442ef72b31b24aa8dcdf65e43525376e4` |
| Canonical main baseline | `f5880cfcfaa6d994f369e04d73c844fd1402d74c` / `1700b1b442ef72b31b24aa8dcdf65e43525376e4` |
| Current objective | Maintain four-lane registry, dependencies, and integration authority; coordinate specialists without implementing their features |
| Current blocker | None for governance presence on main; specialist blockers remain on their lanes |
| Next permitted action | Coordinate specialist bootstrap/handoffs; propose later specialist integrations only after protocol gates |
| Next prohibited action | Implementing TradeStation, Gmail, or database specialist features; merging PR #21/#22/#19; authorizing credentials or LIVE |
| Contract dependencies | `DEP-CORE-001`, `DEP-CORE-002` (tracked; not owned as specialist work) |
| Certification status | Governance bootstrap integrated on main after independent PASS and Operator-authorized FF |
| Integration eligibility | Already integrated |
| Last verification date | 2026-10-08 (integration attestation) |
| Evidence references | PR https://github.com/agentAD25/swing-trading-automation/pull/23 MERGED; independent verifiers `bc-3289987e-ba29-5c68-a93e-fd3b27b71e9e` and `bc-e255e4a7-f783-5ef6-8fc3-f4cbd2d0d926`; journal 2026-10-08 integration entry |

## Lane 2 — TradeStation / Broker

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-2` |
| Workstream name | TradeStation / Broker |
| Current state | `WAITING_PROVIDER` |
| Current branch | `cursor/p2-ts-provider-evidence-99c1` |
| PR number | Draft PR #22 |
| Last attested SHA | `a6c5f1d7109e156eb0e9257216c3b5dbed17f653` |
| Last attested tree | `3d19daec787e5796af55a98de36a54d0d1f77a79` |
| Canonical main baseline | `f5880cfcfaa6d994f369e04d73c844fd1402d74c` / `1700b1b442ef72b31b24aa8dcdf65e43525376e4` (specialist branch may predate this tip) |
| Current objective | Reconcile TradeStation Client Experience answers and provider-evidence constraints for a future attended probe; keep ADR-0005 Proposed |
| Current blocker | `DEP-TS-001` — native PKCE callback confirmation / provider callback clarification |
| Next permitted action | Docs-only provider-evidence clarification; update Proposed ADR-0005; retain PR #22 history |
| Next prohibited action | TradeStation authentication; broker network calls; SIM/LIVE orders; automatic merge; reconstructing or merging stale PR #19 |
| Contract dependencies | `DEP-TS-001`, `DEP-CORE-001`, `DEP-CORE-002` |
| Certification status | Not certified. ADR-0005 remains Proposed. Provider confirmation is not operational certification. |
| Integration eligibility | Not eligible. Waiting on provider clarification and later certification gates. |
| Last verification date | 2026-10-08 (GitHub attestation of PR #22 head/tree) |
| Evidence references | https://github.com/agentAD25/swing-trading-automation/pull/22 ; `docs/adr/0005-tradestation-provider-evidence.md` on PR head (Proposed); historical stale PR #19 marked `SUPERSEDED` below |

### Historical TradeStation PR #19 (not an active lane tip)

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-2-HIST-19` |
| Workstream name | TradeStation pre-credential stop (historical) |
| Current state | `SUPERSEDED` |
| Current branch | `cursor/pre-credential-decision-3a31` |
| PR number | Draft PR #19 (OPEN, merge conflicts with `main`) |
| Last attested SHA | `bc6ab7ea92310ffa133b75b498f7f245af11f166` |
| Last attested tree | `4cd4768c34bf82a5bfb97189c38fbd79ae99fbcf` |
| Canonical main baseline | `f5880cfcfaa6d994f369e04d73c844fd1402d74c` / `1700b1b442ef72b31b24aa8dcdf65e43525376e4` (specialist branch may predate this tip) |
| Current objective | Preserve audit history only |
| Current blocker | ADR numbering conflicts with accepted ADR-0003 on `main`; PR is conflicting and pre-credential |
| Next permitted action | Leave open for audit or Operator-directed close; never auto-merge |
| Next prohibited action | Automatic merge; reconstruction into a new branch as if current; treating its ADR-0003 as authoritative |
| Contract dependencies | Superseded by Lane 2 active work and accepted ADR-0003 on `main` |
| Certification status | Not certified; do not integrate |
| Integration eligibility | Not eligible |
| Last verification date | 2026-10-08 |
| Evidence references | https://github.com/agentAD25/swing-trading-automation/pull/19 ; accepted ADR-0003 on `main` remains Group 4A envelope/retention |

## Lane 3 — Gmail / Signal Ingestion

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-3` |
| Workstream name | Gmail / Signal Ingestion |
| Current state | `WAITING_OPERATOR` |
| Current branch | `cursor/p2-g4-gmail-readonly-gate-a-99c1` |
| PR number | Draft PR #21 |
| Last attested SHA | `a2cef6f3527b2aab7319a2628874fcdcaf03acac` |
| Last attested tree | `557b4c939d7ac570f20b2fa69176b24234189d76` |
| Canonical main baseline | `f5880cfcfaa6d994f369e04d73c844fd1402d74c` / `1700b1b442ef72b31b24aa8dcdf65e43525376e4` (specialist branch may predate this tip) |
| Current objective | Propose Gmail read-only corpus Gate A; keep ADR-0004 Proposed until Operator OAuth setup |
| Current blocker | `DEP-GMAIL-001` — Google OAuth setup by Operator |
| Next permitted action | Docs-only Gate A preparation; sanitized fixture planning; retain PR #21 history |
| Next prohibited action | Gmail authentication in coordinator bootstrap; mailbox access; secret material in Git/chat/PR; self-integration |
| Contract dependencies | `DEP-GMAIL-001`, `DEP-CORE-001`, `DEP-CORE-002` |
| Certification status | Not certified. ADR-0004 remains Proposed. Offline Group 4A on `main` is separately `INTEGRATED` (see below). |
| Integration eligibility | Not eligible while waiting on Operator OAuth setup and later verification |
| Last verification date | 2026-10-08 (GitHub attestation of PR #21 head/tree; parent is current main) |
| Evidence references | https://github.com/agentAD25/swing-trading-automation/pull/21 ; `docs/adr/0004-gmail-readonly-corpus-acquisition.md` on PR head (Proposed) |

### Offline Group 4A (canonical, already on main)

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-3-G4A` |
| Workstream name | Offline email instruction contract (Group 4A) |
| Current state | `INTEGRATED` |
| Current branch | `main` (via merged PR #20 lineage) |
| PR number | PR #20 (MERGED; fast-forward evidence on main) |
| Last attested SHA | Certified implementation `ce045c14b119d882505a947a7826005ff6d99103`; main evidence tip `41218abb2eda5f06001703fb83c2cb9e43e5ec2e` |
| Last attested tree | Certified `67a0b57526ea219972fa0574b191562f0f52b598`; main tip `39f0ab05c49b533270964b303601539feeff570f` |
| Canonical main baseline | `f5880cfcfaa6d994f369e04d73c844fd1402d74c` / `1700b1b442ef72b31b24aa8dcdf65e43525376e4` (specialist branch may predate this tip) |
| Current objective | Preserve integrated offline parser; no Gmail authority |
| Current blocker | Quantity rounding, market calendar, and timezone remain unresolved (`DEP-CORE-001`, `DEP-CORE-002`) |
| Next permitted action | Consume as canonical offline contract; Gmail work stays on Lane 3 PR #21 |
| Next prohibited action | Inferring Gmail, broker, credential, Supabase, order, SIM, or `LIVE` authority from this integration |
| Contract dependencies | `DEP-CORE-001`, `DEP-CORE-002` |
| Certification status | `INTEGRATED_AND_CERTIFIED` for offline Group 4A only; ADR-0003 Accepted |
| Integration eligibility | Already integrated |
| Last verification date | 2026-10-05 (recorded on main); re-attested 2026-10-08 |
| Evidence references | `docs/CURRENT_STATE.md`; ADR-0003 Accepted; PR #20 |

## Lane 4 — Database / PostgreSQL Infrastructure

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-4` |
| Workstream name | Database / PostgreSQL Infrastructure |
| Current state | `NOT_STARTED` |
| Current branch | None dedicated |
| PR number | None |
| Last attested SHA | N/A (no active database-lane tip) |
| Last attested tree | N/A |
| Canonical main baseline | `f5880cfcfaa6d994f369e04d73c844fd1402d74c` / `1700b1b442ef72b31b24aa8dcdf65e43525376e4` (specialist branch may predate this tip) |
| Current objective | Establish a dedicated infrastructure lane for zero-incremental-cost remotely accessible PostgreSQL selection evidence and TokenStore PostgreSQL certification planning — without connecting or provisioning in this bootstrap |
| Current blocker | `DEP-DB-001` (provider selection), `DEP-DB-002` (TokenStore PostgreSQL execution evidence). Local PostgreSQL is inaccessible from Cursor Cloud. Supabase remains a candidate and is **NOT_ACCEPTED**. |
| Next permitted action | Docs-only suitability research and evidence planning on a new `cursor/db-<gate>-*` branch after Operator/coordinator dispatch |
| Next prohibited action | Paid database service; remote migration; Supabase connection in this bootstrap; claiming TokenStore PostgreSQL tests passed without accepted evidence |
| Contract dependencies | `DEP-DB-001`, `DEP-DB-002` |
| Certification status | Not certified. Twelve TokenStore PostgreSQL tests lack accepted execution evidence. |
| Integration eligibility | Not eligible |
| Last verification date | 2026-10-08 (absence of dedicated lane attested) |
| Evidence references | `docs/P2_C_ZERO_INCREMENTAL_COST.md`; `docs/DB_DEPLOYMENT.md` (historical); `docs/TOKEN_STORE.md`; `INITIAL_DATABASE_INCREMENTAL_SERVICE_COST = 0 USD` on main |

## Baseline difference classification

| Claimed/prior baseline | Attested GitHub `main` | Classification |
| --- | --- | --- |
| Pre-integration SHA `41218abb2eda5f06001703fb83c2cb9e43e5ec2e` | Superseded by FF of PR #23 | `SUPERSEDED_BY_AUTHORIZED_INTEGRATION` |
| Integrated SHA `f5880cfcfaa6d994f369e04d73c844fd1402d74c` | Identical | `BASELINE_MATCH` |
| Integrated tree `1700b1b442ef72b31b24aa8dcdf65e43525376e4` | Identical | `BASELINE_MATCH` |

PR #23 was integrated by history-preserving fast-forward. Specialist PR #21/#22
branches predate this tip and were not rewritten. Unexpected future divergence
must be classified, never overwritten or reset.
