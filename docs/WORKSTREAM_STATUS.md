# Workstream Status Registry

Authoritative four-lane status for concurrent Phase 2 specialist work.
Conversation claims are never authoritative by themselves. Resolve conflicts
using `docs/INTEGRATION_PROTOCOL.md` and the operating hierarchy in
`docs/WORKSTREAM_OWNERSHIP.md`.

Last attestation date: 2026-10-09
Canonical main baseline (attested): `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829`
Canonical main tree (attested): `fc97582f22ebf2d24f132c9afe2720430b197f9f`
Attestation method: governance-version and registry synchronization via `gh`/`git fetch` on 2026-10-09.
Classification versus the prior registry tip: `REGISTRY_IDENTITY_STALE` for PR #22 and PR #24 heads. Prior checkpoint main `af0d69b1dfc2046899db05a2f12767fc20b623ae` is an ancestor (PR #25 MERGED). Governance fast-forward tip remains `f5880cfcfaa6d994f369e04d73c844fd1402d74c` / `1700b1b442ef72b31b24aa8dcdf65e43525376e4`.
This attestation names the pre-sync main. A descendant documentation commit cannot embed its own hash.

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
| Current branch | `main` (PR #23 and checkpoint PR #25 history-preserving fast-forwards) |
| PR number | PR #23 (MERGED); checkpoint PR #25 (MERGED) |
| Last attested SHA | Governance FF tip `f5880cfcfaa6d994f369e04d73c844fd1402d74c`; attested main `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` |
| Last attested tree | Governance `1700b1b442ef72b31b24aa8dcdf65e43525376e4`; attested main `fc97582f22ebf2d24f132c9afe2720430b197f9f` |
| Canonical main baseline | `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` / `fc97582f22ebf2d24f132c9afe2720430b197f9f` |
| Current objective | Maintain four-lane registry, dependencies, and integration authority; coordinate specialists without implementing their features |
| Current blocker | None for governance presence on main; specialist blockers remain on their lanes |
| Next permitted action | Reconcile specialist handoffs; open/review DB draft PR when authorized; propose later integrations only after protocol gates |
| Next prohibited action | Implementing TradeStation, Gmail, or database specialist features; merging PR #21/#22/#24/#19; authorizing credentials or LIVE |
| Contract dependencies | `DEP-CORE-001`, `DEP-CORE-002` (tracked; not owned as specialist work) |
| Certification status | Governance bootstrap integrated on main after independent PASS and Operator-authorized FF. Checkpoint PR #25 is integrated evidence, not a new specialist certification. |
| Integration eligibility | Already integrated |
| Last verification date | 2026-10-09 (identity reattestation of main `8cef3d7`) |
| Evidence references | PR https://github.com/agentAD25/swing-trading-automation/pull/23 MERGED; independent verifiers `bc-3289987e-ba29-5c68-a93e-fd3b27b71e9e` and `bc-e255e4a7-f783-5ef6-8fc3-f4cbd2d0d926`; specialist agents `bc-d4b7c1e4-6ba3-542d-abb3-54ba045f0f93`, `bc-f47aa4eb-faff-54ed-8dd0-9d738fab7bc4`, `bc-f38dad08-03c5-5ee8-9b28-8701f8b051f4` |

## Lane 2 — TradeStation / Broker

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-2` |
| Workstream name | TradeStation / Broker |
| Current state | `WAITING_PROVIDER` |
| Current branch | `cursor/p2-ts-provider-evidence-99c1` |
| PR number | Draft PR #22 |
| Last attested SHA | `16aa5788a17ac77291530bb836af256a6f79f89f` |
| Last attested tree | `74ce64cb17585fd1aefc58970ef4850cfc40c948` |
| Canonical main baseline | `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` / `fc97582f22ebf2d24f132c9afe2720430b197f9f` (merge-base `af0d69b1dfc2046899db05a2f12767fc20b623ae`; does not contain attested main) |
| Current objective | Reconcile TradeStation Client Experience answers and provider-evidence constraints for a future attended probe; keep ADR-0005 Proposed |
| Current blocker | `DEP-TS-001` — native PKCE callback confirmation / provider callback clarification |
| Next permitted action | Docs-only provider-evidence clarification; update Proposed ADR-0005; retain PR #22 history |
| Next prohibited action | TradeStation authentication; broker network calls; SIM/LIVE orders; automatic merge; reconstructing or merging stale PR #19 |
| Contract dependencies | `DEP-TS-001`, `DEP-CORE-001`, `DEP-CORE-002` |
| Certification status | Not certified. ADR-0005 remains Proposed. Continuity token `LANE2_WAITING_PROVIDER_CONTINUITY_VERIFIED` (`bc-d4b7c1e4-6ba3-542d-abb3-54ba045f0f93`) applies to ancestor `a6c5f1d7109e156eb0e9257216c3b5dbed17f653` only. Intake commit `19154eae43990df1d83a78be7b6dac3710a28804` changes `src/swingtrade/group3_auth/` and `tests/group3_auth/test_lane2_readiness.py`. Descendant `16aa5788a17ac77291530bb836af256a6f79f89f` says it records verification of tree `19154ea` and does not change `src/` or `tests/`. Lane 1 has not independently re-verified that claim. Provider confirmation is not operational certification. |
| Integration eligibility | Not eligible. `DEP-TS-001` stays OPEN. New independent verification is required before any integration proposal for head `16aa578`. |
| Last verification date | 2026-10-09 identity reattestation. Continuity verification 2026-10-08 covers `a6c5f1d` only. |
| Evidence references | https://github.com/agentAD25/swing-trading-automation/pull/22 ; prior token `LANE2_WAITING_PROVIDER_CONTINUITY_VERIFIED` on `a6c5f1d`; ADR-0005 Proposed; PR #19 `SUPERSEDED` |

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
| Canonical main baseline | `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` / `fc97582f22ebf2d24f132c9afe2720430b197f9f` (merge-base `12e852c6d523a8fbfe2082a33887e36045ee04ae`; head unchanged) |
| Current objective | Preserve audit history only |
| Current blocker | ADR numbering conflicts with accepted ADR-0003 on `main`; PR is conflicting and pre-credential |
| Next permitted action | Leave open for audit or Operator-directed close; never auto-merge |
| Next prohibited action | Automatic merge; reconstruction into a new branch as if current; treating its ADR-0003 as authoritative |
| Contract dependencies | Superseded by Lane 2 active work and accepted ADR-0003 on `main` |
| Certification status | Not certified; do not integrate |
| Integration eligibility | Not eligible |
| Last verification date | 2026-10-09 identity reattestation (head unchanged; still OPEN and `CONFLICTING`) |
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
| Canonical main baseline | `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` / `fc97582f22ebf2d24f132c9afe2720430b197f9f` (merge-base `41218abb2eda5f06001703fb83c2cb9e43e5ec2e`; head unchanged; does not contain attested main) |
| Current objective | Propose Gmail read-only corpus Gate A; keep ADR-0004 Proposed until Operator OAuth setup |
| Current blocker | `DEP-GMAIL-001` — Google OAuth setup by Operator |
| Next permitted action | Docs-only Gate A preparation; sanitized fixture planning; retain PR #21 history |
| Next prohibited action | Gmail authentication in coordinator bootstrap; mailbox access; secret material in Git/chat/PR; self-integration |
| Contract dependencies | `DEP-GMAIL-001`, `DEP-CORE-001`, `DEP-CORE-002` |
| Certification status | Not certified. ADR-0004 remains Proposed. Offline Group 4A on `main` is separately `INTEGRATED` (see below). |
| Integration eligibility | Not eligible while waiting on Operator OAuth setup and later verification |
| Last verification date | 2026-10-09 identity reattestation (head unchanged). Continuity verification 2026-10-08 covers `a2cef6f` only and is not a post-main reconcile. |
| Evidence references | https://github.com/agentAD25/swing-trading-automation/pull/21 ; token `LANE3_WAITING_OPERATOR_OAUTH_CONTINUITY_VERIFIED`; ADR-0004 Proposed; docs conflict vs post-governance main needs Lane 1 reconcile before later integration |

### Offline Group 4A (canonical, already on main)

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-3-G4A` |
| Workstream name | Offline email instruction contract (Group 4A) |
| Current state | `INTEGRATED` |
| Current branch | `main` (via merged PR #20 lineage) |
| PR number | PR #20 (MERGED; fast-forward evidence on main) |
| Last attested SHA | Certified implementation `ce045c14b119d882505a947a7826005ff6d99103`; attested main `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` |
| Last attested tree | Certified `67a0b57526ea219972fa0574b191562f0f52b598`; attested main `fc97582f22ebf2d24f132c9afe2720430b197f9f` |
| Canonical main baseline | `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` / `fc97582f22ebf2d24f132c9afe2720430b197f9f` |
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
| Last attested SHA | `d491c3434872fac88b1c5be28281dce94ea11a8b` (parents `5e748ad9b5738c5fe8b1ea02f96cde2d677c102f` and attested main `8cef3d7`) |
| Last attested tree | `ac228e7342c8f75868cc0a683920e26d75cea31f` |
| Canonical main baseline | `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` / `fc97582f22ebf2d24f132c9afe2720430b197f9f` (PR tip contains this attested main) |
| Current objective | Preserve zero-cost research and independent local TokenStore PostgreSQL evidence; no provider acceptance and no integration |
| Current blocker | `DEP-DB-001` OPEN (Supabase/Neon Free **NOT_ACCEPTED**). `DEP-DB-002` has independent local PASS but stays OPEN until coordinator certification review and Operator acceptance of any certification claim. |
| Next permitted action | Lane 4 owner merges later coordinator main updates without force-push; Operator host-selection path remains separate |
| Next prohibited action | Set `READY_FOR_INTEGRATION`; close `DEP-DB-002` from verifier PASS alone; Supabase/Neon connection; paid provisioning; self-integration; LIVE |
| Contract dependencies | `DEP-DB-001`, `DEP-DB-002` |
| Certification status | Independent verifier PASS for twelve local nodes applies only to executable `src/` and `tests/` bytes of `d949ce0197bc51ceef0b627eea325e9c4d13aaaf`. Those paths, plus `migrations/`, `pyproject.toml`, and `docker-compose.yml`, are identical at PR #24 tip `d491c34`. Docs commits `5e748ad` and `d491c34` are outside that PASS. Not Operator-accepted certification. Not integration approval. |
| Integration eligibility | Not eligible. Fresh independent verification of tip `d491c34` is `NOT_RUN`. |
| Last verification date | 2026-10-09 identity reattestation. Executable-byte PASS remains 2026-10-08 (`bc-6040b738-314c-499a-96c2-7383ac84c385`). |
| Evidence references | Draft PR #24; `docs/LANE4_DEP_DB_002_INDEPENDENT_VERIFICATION.md`; token `LANE4_DEP_DB_002_INDEPENDENT_PASS` for unchanged executable bytes; certification-packet docs are not closed evidence |

## Baseline difference classification

| Claimed/prior baseline | Attested GitHub `main` | Classification |
| --- | --- | --- |
| Pre-integration SHA `41218abb2eda5f06001703fb83c2cb9e43e5ec2e` | Superseded by FF of PR #23 | `SUPERSEDED_BY_AUTHORIZED_INTEGRATION` |
| Governance FF tip `f5880cfcfaa6d994f369e04d73c844fd1402d74c` | Ancestor of current main | `GOVERNANCE_FF_TIP` |
| Prior registry tip `24466ab9e551c6bb13dc1af67c6b33f148ac854a` | Ancestor of attested main | `SUPERSEDED_BY_REGISTRY_COMMIT` |
| Checkpoint main `af0d69b1dfc2046899db05a2f12767fc20b623ae` | Ancestor of attested main (PR #25) | `SUPERSEDED_BY_CHECKPOINT_INTEGRATION` |
| Attested main `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` | Identical to `origin/main` on 2026-10-09 | `BASELINE_MATCH` |
| Attested main tree `fc97582f22ebf2d24f132c9afe2720430b197f9f` | Identical | `BASELINE_MATCH` |

PR #23 was integrated by history-preserving fast-forward. Specialist PR #21/#22
branches predate the governance tip and were not rewritten. Lane 4 research
branch `cursor/db-zero-cost-bootstrap-51f4` is not integrated. Unexpected
future divergence must be classified, never overwritten or reset.

## Coordination checkpoint (identity refreshed 2026-10-09)

The 2026-10-08 checkpoint narrative remains in `docs/ENGINEERING_JOURNAL.md`.
This section records current integration-readiness conditions. It does not merge
specialist work and does not close dependencies.

### Specialist compatibility with attested main `8cef3d7`

| Lane | Tip | Contains attested main? | GitHub merge state | Conflicting paths |
| --- | --- | --- | --- | --- |
| LANE-2 PR #22 | `16aa5788a17ac77291530bb836af256a6f79f89f` | No (merge-base `af0d69b`) | `CONFLICTING` / `DIRTY` | `docs/CURRENT_STATE.md`, `docs/ENGINEERING_JOURNAL.md` |
| LANE-3 PR #21 | `a2cef6f3527b2aab7319a2628874fcdcaf03acac` | No (merge-base `41218abb`) | `CONFLICTING` / `DIRTY` | `docs/CURRENT_STATE.md`, `docs/ENGINEERING_JOURNAL.md` |
| LANE-4 PR #24 | `d491c3434872fac88b1c5be28281dce94ea11a8b` | Yes (contains `8cef3d7`) | `MERGEABLE` / `CLEAN` | None versus attested main. Older tips `d949ce0` and `db570fa` remain ancestors and are not a second PR. |
| LANE-2-HIST-19 | `bc6ab7ea92310ffa133b75b498f7f245af11f166` | No (merge-base `12e852c6`) | OPEN / `CONFLICTING` / superseded | Do not reconcile as current authority |

Non-conflicting specialist additions on PR #21: `docs/GMAIL_READONLY_CORPUS_GATE.md`, Proposed ADR-0004. On PR #22: broker/auth evidence docs and Proposed ADR-0005. Those files are not the conflict set.

### Reconciliation instructions (specialist owners; Lane 1 does not edit those branches here)

1. Start from a fresh worktree of the existing branch. Do not recreate the branch and do not force-push.
2. Rebase or merge is **not** automatic. Prefer a new descendant commit that merges attested `main` (`8cef3d7`) and resolves only shared-file conflicts. A descendant of this registry commit is a later main and needs the same merge.
3. For `docs/CURRENT_STATE.md` and `docs/ENGINEERING_JOURNAL.md`, keep canonical main governance text and append the specialist evidence. Do not drop ADR-0003 Accepted, four-lane registry facts, or `DRY_RUN` / `LIVE` unauthorized statements.
4. Do not accept ADR-0004 or ADR-0005 during reconciliation.
5. Do not mark `DEP-*` resolved.
6. After reconciliation, request independent verification of the new SHA/tree before any integration proposal.
7. The pre-PR #24 sentence that Lane 4 still lacked a distinct verifier is superseded for execution evidence only. Draft PR #24 already records independent PASS `LANE4_DEP_DB_002_INDEPENDENT_PASS`. That PASS does not close `DEP-DB-002` and does not make the lane integration-eligible.

### Lane 4 draft PR eligibility

Draft PR #24 already exists and is the review target. Do not create a replacement PR. Integration remains `NOT_ELIGIBLE`:

- Independent local execution is **PASS** (12 passed, 32 deselected; unset URL: 12 skipped). It applies to executable `src/` and `tests/` bytes of `d949ce0`. Those bytes, plus `migrations/`, `pyproject.toml`, and `docker-compose.yml`, are unchanged at tip `d491c34`. Docs commits `5e748ad` and `d491c34` are outside that PASS. Fresh verification of tip `d491c34` is `NOT_RUN`.
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
| Contains attested main `8cef3d7` | FAIL | FAIL | PASS (PR #24 tip `d491c34`) |
| Exact SHA/tree attested | PASS (`16aa578` / `74ce64cb`) | PASS (`a2cef6f` / `557b4c93`; unchanged) | PASS (`d491c34` / `ac228e73`) |
| Governance compliance (no LIVE/auth) | PASS (fail-closed deny language in the intake diff; not certification) | PASS (docs inspection of unchanged head) | PASS (research text; packet docs not certified) |
| Scope isolation | PASS (docs and fail-closed boundary diff) | PASS (docs) | PASS (docs) |
| Shared-file compatibility vs `8cef3d7` | BLOCKED | BLOCKED | PASS vs attested main; re-merge required if a descendant advances main |
| Dependency closure | BLOCKED (`DEP-TS-001`) | BLOCKED (`DEP-GMAIL-001`) | BLOCKED (`DEP-DB-001` OPEN; `DEP-DB-002` OPEN despite local executable-byte PASS) |
| Independent verification of tip | NOT_RUN for `16aa578` (continuity PASS does not transfer from `a6c5f1d`) | NOT_RUN for post-main reconcile | PASS for twelve local nodes on unchanged `src/`/`tests/`; `NOT_RUN` for docs commits `5e748ad` and `d491c34`; not certification closure |
| Automated tests | NOT_RUN this audit | NOT_RUN this audit | Prior verifier: 161 passed offline+contracts; 0 skips in that run. Not rerun here. |
| PostgreSQL-backed tests | NOT_RUN | NOT_RUN | Prior PASS 12 / deselected 32 on unchanged executable bytes; unset URL SKIPPED 12 (not passes). Not rerun here. |
| Secret/credential handling | PASS (no new secrets observed) | PASS | PASS (fixture URL only in research text) |
| Regression vs main | NOT_RUN | NOT_RUN | NOT_RUN |
| Merge readiness | BLOCKED | BLOCKED | BLOCKED |

### Local isolation note

Local checkouts observed on 2026-10-09 and not rewritten: `/workspace/.worktrees/lane2-ts` detached at `a6c5f1d` (not PR #22 tip `16aa578`); `lane3-gmail` detached at PR #21 tip `a2cef6f`; `lane4-db` on local `cursor/db-zero-cost-bootstrap-8992` at `24466ab`, which is not PR #24 tip `d491c34`. Do not treat those checkouts as the remote PR tips.

## ChatGPT advisory version audit (2026-10-09)

Accepted repository governance remains authoritative. This audit does not copy ChatGPT advisory files into Git and does not install them as Cursor rules.

Uploads inspected in this session are references, not active configuration:

| File role | Declared version | SHA-256 | Classification |
| --- | --- | --- | --- |
| Governance upload | 1.1.0 | `44267e30691d4f73dcbb7440c0111e2ecc2a6c4e46fd1c854489076e86cbc026` | `CURRENT_CHATGPT_ADVISORY_V1_1` uploaded reference |
| Instructions upload | 1.1 | `b6223d1ac067eb55d47fb37786b861b5b756c898666a58eab72d82193f9a237b` | `CURRENT_CHATGPT_ADVISORY_V1_1` uploaded reference |
| Governance upload | 1.0.0 | `61db48cdfc058ea4f7e7562ddfbab0748ec79fa01e3bbb675c379c747066dbc9` | `SUPERSEDED_CHATGPT_ADVISORY` historical reference |
| Instructions upload | 1.0 | `b3b7b3d1e5d75d87e815cda7660811a04d51dc00c0eed889ade67180cec6f5b7` | `SUPERSEDED_CHATGPT_ADVISORY` historical reference |

No `SWING_TRADING_PROJECT_GOVERNANCE.md` or `CHATGPT_PROJECT_INSTRUCTIONS.txt` blob exists on attested main or on PR #19, #21, #22, or #24 tips. Active `.cursor/rules/` and `.cursor/agents/` on attested main do not embed v1.0 advisory text. Prior semantic decision `CHATGPT_GOVERNANCE_COMPATIBLE_NO_REPO_CHANGE` is compatibility evidence for the inspected v1.1 text. ChatGPT Project settings and other Cursor Cloud VMs are `NOT_INSPECTABLE` from this session.
