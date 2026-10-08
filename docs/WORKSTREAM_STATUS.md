# Workstream Status Registry

Authoritative four-lane status for concurrent Phase 2 specialist work.
Conversation claims are never authoritative by themselves. Resolve conflicts
using `docs/INTEGRATION_PROTOCOL.md` and the operating hierarchy in
`docs/WORKSTREAM_OWNERSHIP.md`.

Last attestation date: 2026-10-08
Canonical main baseline (attested): `af0d69b1dfc2046899db05a2f12767fc20b623ae`
Canonical main tree (attested): `4e1ed263e745b9896bf9384a2a9453566ebd6e0b`
Attestation method: coordination checkpoint `gh api`/`git fetch` on 2026-10-08.
Classification versus the prior reported tip: `BASELINE_MATCH` (no commits after
`af0d69b`). Governance fast-forward tip remains
`f5880cfcfaa6d994f369e04d73c844fd1402d74c` / `1700b1b442ef72b31b24aa8dcdf65e43525376e4`.

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
| Last attested SHA | Governance FF tip `f5880cfcfaa6d994f369e04d73c844fd1402d74c`; current main evidence tip `24466ab9e551c6bb13dc1af67c6b33f148ac854a` |
| Last attested tree | Governance `1700b1b442ef72b31b24aa8dcdf65e43525376e4`; current main `74ef01fd9ae067e29ae7ecc97c466a39104da2f1` |
| Canonical main baseline | `24466ab9e551c6bb13dc1af67c6b33f148ac854a` / `74ef01fd9ae067e29ae7ecc97c466a39104da2f1` |
| Current objective | Maintain four-lane registry, dependencies, and integration authority; coordinate specialists without implementing their features |
| Current blocker | None for governance presence on main; specialist blockers remain on their lanes |
| Next permitted action | Reconcile specialist handoffs; open/review DB draft PR when authorized; propose later integrations only after protocol gates |
| Next prohibited action | Implementing TradeStation, Gmail, or database specialist features; merging PR #21/#22/#19; authorizing credentials or LIVE |
| Contract dependencies | `DEP-CORE-001`, `DEP-CORE-002` (tracked; not owned as specialist work) |
| Certification status | Governance bootstrap integrated on main after independent PASS and Operator-authorized FF |
| Integration eligibility | Already integrated |
| Last verification date | 2026-10-08 (integration + specialist delegation) |
| Evidence references | PR https://github.com/agentAD25/swing-trading-automation/pull/23 MERGED; independent verifiers `bc-3289987e-ba29-5c68-a93e-fd3b27b71e9e` and `bc-e255e4a7-f783-5ef6-8fc3-f4cbd2d0d926`; specialist agents `bc-d4b7c1e4-6ba3-542d-abb3-54ba045f0f93`, `bc-f47aa4eb-faff-54ed-8dd0-9d738fab7bc4`, `bc-f38dad08-03c5-5ee8-9b28-8701f8b051f4` |

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
| Canonical main baseline | `24466ab9e551c6bb13dc1af67c6b33f148ac854a` / `74ef01fd9ae067e29ae7ecc97c466a39104da2f1` (specialist branch may predate this tip) |
| Current objective | Reconcile TradeStation Client Experience answers and provider-evidence constraints for a future attended probe; keep ADR-0005 Proposed |
| Current blocker | `DEP-TS-001` — native PKCE callback confirmation / provider callback clarification |
| Next permitted action | Docs-only provider-evidence clarification; update Proposed ADR-0005; retain PR #22 history |
| Next prohibited action | TradeStation authentication; broker network calls; SIM/LIVE orders; automatic merge; reconstructing or merging stale PR #19 |
| Contract dependencies | `DEP-TS-001`, `DEP-CORE-001`, `DEP-CORE-002` |
| Certification status | Not certified. ADR-0005 remains Proposed. Provider confirmation is not operational certification. |
| Integration eligibility | Not eligible. Waiting on provider clarification and later certification gates. |
| Last verification date | 2026-10-08 (continuity bootstrap; agent `bc-d4b7c1e4-6ba3-542d-abb3-54ba045f0f93`) |
| Evidence references | https://github.com/agentAD25/swing-trading-automation/pull/22 ; token `LANE2_WAITING_PROVIDER_CONTINUITY_VERIFIED`; ADR-0005 Proposed; PR #19 `SUPERSEDED` |

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
| Canonical main baseline | `24466ab9e551c6bb13dc1af67c6b33f148ac854a` / `74ef01fd9ae067e29ae7ecc97c466a39104da2f1` (specialist branch may predate this tip) |
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
| Canonical main baseline | `24466ab9e551c6bb13dc1af67c6b33f148ac854a` / `74ef01fd9ae067e29ae7ecc97c466a39104da2f1` (specialist branch may predate this tip) |
| Current objective | Propose Gmail read-only corpus Gate A; keep ADR-0004 Proposed until Operator OAuth setup |
| Current blocker | `DEP-GMAIL-001` — Google OAuth setup by Operator |
| Next permitted action | Docs-only Gate A preparation; sanitized fixture planning; retain PR #21 history |
| Next prohibited action | Gmail authentication in coordinator bootstrap; mailbox access; secret material in Git/chat/PR; self-integration |
| Contract dependencies | `DEP-GMAIL-001`, `DEP-CORE-001`, `DEP-CORE-002` |
| Certification status | Not certified. ADR-0004 remains Proposed. Offline Group 4A on `main` is separately `INTEGRATED` (see below). |
| Integration eligibility | Not eligible while waiting on Operator OAuth setup and later verification |
| Last verification date | 2026-10-08 (continuity bootstrap; agent `bc-f47aa4eb-faff-54ed-8dd0-9d738fab7bc4`) |
| Evidence references | https://github.com/agentAD25/swing-trading-automation/pull/21 ; token `LANE3_WAITING_OPERATOR_OAUTH_CONTINUITY_VERIFIED`; ADR-0004 Proposed; docs conflict vs post-governance main needs Lane 1 reconcile before later integration |

### Offline Group 4A (canonical, already on main)

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-3-G4A` |
| Workstream name | Offline email instruction contract (Group 4A) |
| Current state | `INTEGRATED` |
| Current branch | `main` (via merged PR #20 lineage) |
| PR number | PR #20 (MERGED; fast-forward evidence on main) |
| Last attested SHA | Certified implementation `ce045c14b119d882505a947a7826005ff6d99103`; current main tip `24466ab9e551c6bb13dc1af67c6b33f148ac854a` |
| Last attested tree | Certified `67a0b57526ea219972fa0574b191562f0f52b598`; current main tip `74ef01fd9ae067e29ae7ecc97c466a39104da2f1` |
| Canonical main baseline | `24466ab9e551c6bb13dc1af67c6b33f148ac854a` / `74ef01fd9ae067e29ae7ecc97c466a39104da2f1` (specialist branch may predate this tip) |
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
| Current state | `READY_FOR_VERIFICATION` |
| Current branch | Review target `cursor/db-dep-db-002-verify-c385` (contains ancestor `cursor/db-zero-cost-bootstrap-51f4`) |
| PR number | Draft PR #24 (do not open a second PR from the older tip) |
| Last attested SHA | `db570fac13cb33b84c98afb89c3f4722128ae179` (parents `13d6a93` verification record and main `af0d69b`) |
| Last attested tree | `d754a9b28dfcf77a25a32f114c5882767fac8e59` |
| Canonical main baseline | `af0d69b1dfc2046899db05a2f12767fc20b623ae` / `4e1ed263e745b9896bf9384a2a9453566ebd6e0b` |
| Current objective | Preserve zero-cost research and independent local TokenStore PostgreSQL evidence; no provider acceptance and no integration |
| Current blocker | `DEP-DB-001` OPEN (Supabase/Neon Free **NOT_ACCEPTED**). `DEP-DB-002` has independent local PASS but stays OPEN until coordinator certification review and Operator acceptance of any certification claim. |
| Next permitted action | Lane 4 owner merges later coordinator main updates without force-push; Operator host-selection path remains separate |
| Next prohibited action | Set `READY_FOR_INTEGRATION`; close `DEP-DB-002` from verifier PASS alone; Supabase/Neon connection; paid provisioning; self-integration; LIVE |
| Contract dependencies | `DEP-DB-001`, `DEP-DB-002` |
| Certification status | Independent verifier PASS for twelve local nodes on code identical to main `af0d69b`. Not Operator-accepted certification. Not integration approval. |
| Integration eligibility | Not eligible |
| Last verification date | 2026-10-08 (independent verifier `bc-6040b738-314c-499a-96c2-7383ac84c385`; implementer `bc-f38dad08-03c5-5ee8-9b28-8701f8b051f4`) |
| Evidence references | Draft PR #24; `docs/LANE4_DEP_DB_002_INDEPENDENT_VERIFICATION.md`; token `LANE4_DEP_DB_002_INDEPENDENT_PASS`; executable bytes attested at `d949ce0` / `d54619c3` and identical `src/` `tests/` on main `af0d69b` |

## Baseline difference classification

| Claimed/prior baseline | Attested GitHub `main` | Classification |
| --- | --- | --- |
| Pre-integration SHA `41218abb2eda5f06001703fb83c2cb9e43e5ec2e` | Superseded by FF of PR #23 | `SUPERSEDED_BY_AUTHORIZED_INTEGRATION` |
| Governance FF tip `f5880cfcfaa6d994f369e04d73c844fd1402d74c` | Ancestor of current main | `GOVERNANCE_FF_TIP` |
| Prior registry tip `24466ab9e551c6bb13dc1af67c6b33f148ac854a` | Ancestor of current main | `SUPERSEDED_BY_REGISTRY_COMMIT` |
| Current main `af0d69b1dfc2046899db05a2f12767fc20b623ae` | Identical | `BASELINE_MATCH` |
| Current main tree `4e1ed263e745b9896bf9384a2a9453566ebd6e0b` | Identical | `BASELINE_MATCH` |

PR #23 was integrated by history-preserving fast-forward. Specialist PR #21/#22
branches predate the governance tip and were not rewritten. Lane 4 research
branch `cursor/db-zero-cost-bootstrap-51f4` is not integrated. Unexpected
future divergence must be classified, never overwritten or reset.

## Coordination checkpoint (2026-10-08)

This section records integration-readiness conditions. It does not merge
specialist work and does not close dependencies.

### Specialist compatibility with current main

| Lane | Tip | Contains current main? | GitHub merge state | Conflicting paths |
| --- | --- | --- | --- | --- |
| LANE-2 PR #22 | `a6c5f1d7109e156eb0e9257216c3b5dbed17f653` | No (merge-base `41218abb`) | `CONFLICTING` / `DIRTY` | `docs/CURRENT_STATE.md`, `docs/ENGINEERING_JOURNAL.md` |
| LANE-3 PR #21 | `a2cef6f3527b2aab7319a2628874fcdcaf03acac` | No (merge-base `41218abb`) | `CONFLICTING` / `DIRTY` | `docs/CURRENT_STATE.md`, `docs/ENGINEERING_JOURNAL.md` |
| LANE-4 PR #24 | `db570fac13cb33b84c98afb89c3f4722128ae179` | Yes (contains `af0d69b`) | `MERGEABLE` / `CLEAN` versus `af0d69b` | None versus that main tip. Older tip `d949ce0` remains an ancestor and is not a second PR. |
| LANE-2-HIST-19 | `bc6ab7ea92310ffa133b75b498f7f245af11f166` | No | OPEN / superseded | Do not reconcile as current authority |

Non-conflicting specialist additions on PR #21: `docs/GMAIL_READONLY_CORPUS_GATE.md`, Proposed ADR-0004. On PR #22: broker/auth evidence docs and Proposed ADR-0005. Those files are not the conflict set.

### Reconciliation instructions (specialist owners; Lane 1 does not edit those branches here)

1. Start from a fresh worktree of the existing branch. Do not recreate the branch and do not force-push.
2. Rebase or merge is **not** automatic. Prefer a new descendant commit that merges current `main` (`af0d69b`) and resolves only shared-file conflicts.
3. For `docs/CURRENT_STATE.md` and `docs/ENGINEERING_JOURNAL.md`, keep canonical main governance text and append the specialist evidence. Do not drop ADR-0003 Accepted, four-lane registry facts, or `DRY_RUN` / `LIVE` unauthorized statements.
4. Do not accept ADR-0004 or ADR-0005 during reconciliation.
5. Do not mark `DEP-*` resolved.
6. After reconciliation, request independent verification of the new SHA/tree before any integration proposal.
7. The pre-PR #24 sentence that Lane 4 still lacked a distinct verifier is superseded for execution evidence only. Draft PR #24 already records independent PASS `LANE4_DEP_DB_002_INDEPENDENT_PASS`. That PASS does not close `DEP-DB-002` and does not make the lane integration-eligible.

### Lane 4 draft PR eligibility

Draft PR #24 already exists and is the review target. Do not create a replacement PR. Integration remains `NOT_ELIGIBLE`:

- Independent local execution is **PASS** (12 passed, 32 deselected; unset URL: 12 skipped). It applies to executable `src/` and `tests/` bytes shared by `d949ce0` and main `af0d69b`. The later merge commit `db570fa` changes docs only (`CURRENT_STATE`, journal, status) relative to verification commit `13d6a93`.
- `DEP-DB-002` stays OPEN. Verifier PASS is not Operator-accepted certification.
- `DEP-DB-001` stays OPEN. Supabase and Neon Free stay **NOT_ACCEPTED**.
- State stays `READY_FOR_VERIFICATION`, not `READY_FOR_INTEGRATION`.

### Recommended future integration sequence

Preconditions apply before each step. No step authorizes credentials, SIM, or `LIVE`.

1. Keep governance on `main` (already integrated). Do not re-merge PR #23.
2. Lane 4 draft PR #24 may be integrated only after a later explicit authorization, dependency review, and a fresh shared-doc reconcile if main moves. Independent PASS does not authorize that merge in this task. Provider selection stays closed.
3. Lane 3 PR #21 only after Operator OAuth attestation (`DEP-GMAIL-001`), shared-doc reconciliation, and independent verification. ADR-0004 stays Proposed until Operator acceptance.
4. Lane 2 PR #22 only after provider callback evidence (`DEP-TS-001`) or an explicit Operator decision to integrate docs-only bounds without closing `DEP-TS-001`, plus shared-doc reconciliation and independent verification. ADR-0005 stays Proposed until Operator acceptance.
5. `DEP-CORE-001` and `DEP-CORE-002` before any economic quantity, calendar, or timezone acceptance. They do not block docs-only conflict reconciliation.

### Acceptance gate vocabulary for future specialist integration

Use `PASS`, `FAIL`, `BLOCKED`, `SKIPPED`, or `NOT_RUN`. Skipped tests are not passes.

| Gate | LANE-2 PR #22 | LANE-3 PR #21 | LANE-4 research |
| --- | --- | --- | --- |
| Branch identity attested | PASS | PASS | PASS |
| Contains current main `af0d69b` | FAIL | FAIL | PASS (PR #24 tip `db570fa`) |
| Exact SHA/tree attested | PASS | PASS | PASS |
| Governance compliance (no LIVE/auth) | PASS (docs inspection) | PASS (docs inspection) | PASS (research text) |
| Scope isolation | PASS (docs) | PASS (docs) | PASS (docs) |
| Shared-file compatibility vs `af0d69b` | BLOCKED | BLOCKED | PASS vs `af0d69b`; re-merge required if coordinator main advances |
| Dependency closure | BLOCKED (`DEP-TS-001`) | BLOCKED (`DEP-GMAIL-001`) | BLOCKED (`DEP-DB-001` OPEN; `DEP-DB-002` OPEN despite local PASS) |
| Independent verification of tip | NOT_RUN for post-main reconcile | NOT_RUN for post-main reconcile | PASS for twelve local nodes on identical `src/`/`tests/`; not certification closure |
| Automated tests | NOT_RUN this checkpoint | NOT_RUN this checkpoint | Verifier: 161 passed offline+contracts; 0 skips in that run |
| PostgreSQL-backed tests | NOT_RUN | NOT_RUN | PASS 12 / deselected 32; unset URL SKIPPED 12 (not passes) |
| Secret/credential handling | PASS (no new secrets observed) | PASS | PASS (fixture URL only in research text) |
| Regression vs main | NOT_RUN | NOT_RUN | NOT_RUN |
| Merge readiness | BLOCKED | BLOCKED | BLOCKED |

### Local isolation note

Worktrees present: `/workspace/.worktrees/lane2-ts` at PR #22 tip; `lane3-gmail` at PR #21 tip; `lane4-db` on local `cursor/db-zero-cost-bootstrap-8992` at `24466ab`, which is **not** remote research tip `d949ce0`. Do not treat the local Lane 4 worktree as the research branch. Do not rewrite those checkouts from this checkpoint.
