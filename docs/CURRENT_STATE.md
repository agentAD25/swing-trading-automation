# Current State

- Last updated: 2026-10-09 (Operator offline-custody intent recorded; implementation permission not effective). Governance PR #23 and checkpoint PR #25 remain integrated.
- Current phase: Phase 1 closed (Gate B closure audit); offline Group 2
  foundation implemented on this branch and not merged; C1/U-10 resolved;
  offline Group 4A email contract is on canonical `main` by exact
  fast-forward of `ce045c14b119d882505a947a7826005ff6d99103`; Gmail
  read-only corpus Gate A is proposed and not connected
- Phase status: `PHASE1_COMPLETE` for governance, design, reconciliation,
  acceptance, and the offline `DRY_RUN` foundation; `PHASE1_ACCEPTED` remains
  the bounded meaning of the exact broker-neutral offline deterministic
  candidate within that closure
- Authorized execution mode: `DRY_RUN` only (local, deterministic, non-network)
- TradeStation `SIM`: Reserved for a future connectivity phase; unauthorized
- `LIVE` status: Unauthorized
- Foundation implementation: Minimal local non-network `DRY_RUN` foundation
  implemented, remediated through findings F01–F06, and independently
  verified (Gate A: 218 tests, PostgreSQL 16.15) at SHA
  `eb4b3b550874b4729abf7902cda2df8bf01e70ba`, tree
  `858442c0b2dcf0537072e75e95bb0dd2b001bf49`, in draft PR #6
- Phase 1E: Complete — Gate A independent verification passed with no
  remaining material findings; see `docs/PHASE_1_CLOSURE.md`
- Phase 2: Not generally authorized. `P2-0` Group 1 documentation is on
  canonical `main` by fast-forward of exact evidence HEAD
  `9631de3bd8a6a2e24c6833ca534c5e626fdb7b75`, tree
  `41588e7af631db0213b80d5a02472dd0e4d206ba` (PR #12; no squash, rebase,
  force-push, or merge commit). Independent Gate `H1` verification
  **PASS (C1 carried)** remains for exact commit
  `33110c7c0aa2f385d179a1f66d068daca2c47537`, tree
  `5f45983b19bed47988133c5b832e125d0602133c`. That attestation is
  docs-only contract-draft review. Fast-forward onto `main` does not start
  Phase 2 implementation and grants no credential, broker, TradeStation
  `SIM`, order, deployment, real-capital, or `LIVE` authority.
  Draft PR #14 head `e549ab9e59604abecce0c882c60f845f00f8be09`, tree
  `dee2ef72378bcffa8499bd1d560c8c324a97569e`, matches the independently
  verified TokenStore commit. `docs/TOKEN_STORE.md` at that commit is
  blob `781764f5bbc472378346f6216e07ca6961146e9d` and was fast-forwarded
  unchanged (`git merge --ff-only`). Verification returned **PASS** and
  **OFFLINE_IMPLEMENTATION_UNBLOCKED**. It is not
  `P2_G2_CONTRACT_DECISION_REQUIRED`. That verification recorded
  `C1_U10_PROPOSED_RESOLUTION` while status was **PROPOSED**. Independent
  review `C1_U10_CONTRACT_PASS` of
  `a4213f8356a9e32ca4647865ee98e13660e3d656`, tree
  `c07487c88f24f9432de89df7f574130274d50b4b`, left C1 **PROPOSED**. The
  human Operator accepts ADR-0002. C1/U-10 is **RESOLVED**. Contract
  acceptance is not operational credential certification, key management,
  Supabase selection, or `LIVE` authorization.
  The human Operator authorizes the **offline Group 2 foundation only**.
  The non-Cursor bootstrap injector, key custody, retention, and the SIM
  database host remain later decisions.
  Verified zero-cost database evidence is on `main` by a
  history-preserving merge of exact PR #13 head
  `78f485b33bdd3f859d540458ba170b2353c04c61`, tree
  `28b3ced5663c00f4b8d32828ed2b160344d09805`, recorded as integration
  commit `e0ec755e39c897492fbc8d970bb165d8335d361c`, tree
  `5e687dc37376b1b9c092a2a56a40348e5d36532f`.
  `INITIAL_DATABASE_INCREMENTAL_SERVICE_COST = 0 USD`. The constraint
  supersedes only the initial-deployment effect of the historical RDS
  recommendation. Supabase is **NOT_ACCEPTED**. Historical
  `docs/DB_DEPLOYMENT.md` is unchanged, and this evidence commit does
  not rewrite `docs/P2_C_ZERO_INCREMENTAL_COST.md`.
  Credentials, broker calls, Supabase connections, provisioning, SIM
  orders, and `LIVE` remain unauthorized. `DRY_RUN` remains the sole
  authorized execution mode. See `docs/PHASE_2_RECONCILIATION.md` and
  `docs/TOKEN_STORE.md`.
- Design baseline: Phase 1A governance commit `ae1aa85`
- Contract acceptance: `PHASE1_ACCEPTED` evidence metadata for candidate
  `abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`, tree
  `cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`

## Operator acceptance model

- **Sole decider:** the human Operator. Agents prepare evidence and proposals
  only.
- **Bounded meaning:** `PHASE1_ACCEPTED`, if the Operator later records it,
  accepts only the broker-neutral, offline, deterministic baseline.
- **No implied authority:** that status does not authorize implementation,
  credentials, accounts, broker or network activity, TradeStation `SIM`, order
  submission, Phase 2, real capital, or `LIVE`.
- **Current result:** the human Operator records `PHASE1_ACCEPTED` for the exact
  candidate/tree above after independent verification passed. This is
  evidence-only acceptance and grants none of the prohibited capabilities.

## Phase history and current candidate

| Phase | Durable output/status |
| --- | --- |
| Phase 1A | Governance baseline `ae1aa85`; governance bootstrap complete, not Phase 1 acceptance |
| Phase 1B | Architecture/design contracts and fixture, broker research, and failure model integrated from the recorded specialist commits; all remain proposed inputs |
| Phase 1C | Coordinator reconciliation through `98731e7`; conflicts and freeze blockers recorded, no acceptance |
| Phase 1D | Closed: replacement candidate commit `abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`, exact tree `cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`, independently verified and accepted only within the bounded Phase 1 meaning; immutable tag `phase1-accepted-abc1fb6` |
| Phase 1E | Complete: offline foundation implemented and remediated through findings F01–F06 at SHA `eb4b3b550874b4729abf7902cda2df8bf01e70ba`, tree `858442c0b2dcf0537072e75e95bb0dd2b001bf49`; Gate A independent verification passed with 218 tests (PostgreSQL 16.15); draft PR #6 remains open |
| Phase 1 closure (Gate B) | Complete: evidence-only closure audit recorded in `docs/PHASE_1_CLOSURE.md`; `PHASE1A_COMPLETE` through `PHASE1E_COMPLETE` and `PHASE1_COMPLETE` |
| Phase 2 | Not generally authorized. The Operator authorizes the offline Group 2 foundation only. Credentials, broker calls, Supabase connections, provisioning, SIM orders, and `LIVE` remain unauthorized. |
| P2-0 Group 1 docs | On canonical `main` by fast-forward of PR #12 evidence HEAD `9631de3bd8a6a2e24c6833ca534c5e626fdb7b75`, tree `41588e7af631db0213b80d5a02472dd0e4d206ba`; independently verified Gate `H1` **PASS (C1 carried)** at exact commit `33110c7c0aa2f385d179a1f66d068daca2c47537`, tree `5f45983b19bed47988133c5b832e125d0602133c`; PR #8 `a91bd24`, #9 `f0dca4b`, #10 `a7900c2`, #11 `595f431` lineage preserved; all remain `PROPOSED`. The Group 2 denial previously recorded on this row is superseded by the offline Group 2 foundation authorization below. |
| PR #14 TokenStore | Fast-forward onto `main` of exact commit `e549ab9e59604abecce0c882c60f845f00f8be09`, tree `dee2ef72378bcffa8499bd1d560c8c324a97569e`. Independent verification **PASS** and **OFFLINE_IMPLEMENTATION_UNBLOCKED**. Not `P2_G2_CONTRACT_DECISION_REQUIRED`. The **PROPOSED** sentence on this row is the pre-closure record. |
| PR #13 zero-cost evidence | History-preserving merge of exact commit `78f485b33bdd3f859d540458ba170b2353c04c61`, tree `28b3ced5663c00f4b8d32828ed2b160344d09805`, as `e0ec755e39c897492fbc8d970bb165d8335d361c`, tree `5e687dc37376b1b9c092a2a56a40348e5d36532f`. Versus the PR #14 tip this adds only `docs/P2_C_ZERO_INCREMENTAL_COST.md`. `docs/DB_DEPLOYMENT.md` is unchanged. `INITIAL_DATABASE_INCREMENTAL_SERVICE_COST = 0 USD`. Supersedes only the initial-deployment effect of the historical RDS recommendation. Supabase is **NOT_ACCEPTED**. |
| Offline Group 2 foundation | Operator authorizes the offline Group 2 foundation only. Later decisions: non-Cursor bootstrap injector, key custody, retention, and SIM database host. The authorization commit itself added no application code. The implementation is on this branch at `904a362ac716aa8a7d3c9e830444a19108feed67` and is not merged. |
| C1/U-10 closure | Operator accepts ADR-0002 after independent review `C1_U10_CONTRACT_PASS` on `a4213f8356a9e32ca4647865ee98e13660e3d656`, tree `c07487c88f24f9432de89df7f574130274d50b4b`. C1/U-10 is **RESOLVED**. Non-blocking residuals do not reopen C1. Not operational credential certification, key management, Supabase selection, or `LIVE` authorization. |
| Offline Group 4A email contract | On canonical `main` by exact fast-forward of certified commit `ce045c14b119d882505a947a7826005ff6d99103`, tree `67a0b57526ea219972fa0574b191562f0f52b598`. No squash, rebase, force-push, or merge commit. The pre-fast-forward sentence that this work was unmerged is superseded for location only. Remediation commit `05dfff9f69d27b869dcb1c392d8d103b7f21d6b4`, tree `b25892d7cd6ad43769e44cd67cd53c3dd7cb8602`, parent `229a38b4b6f7ab628d1c656974686e7888075302`, remains an ancestor. The Operator accepted ADR-0003: a `CanonicalInstructionEnvelope` carries a required-field `NewTradeInstruction` or a reserved amendment, exit-alert, or cancel payload. Only new-trade parsing is implemented. `EMAIL_RETENTION_POLICY` is `HASH_PROVIDER_REF_FIELD_EVIDENCE`. Exit-policy negation or same-source conflict quarantines as `CONFLICTING_ECONOMIC_INSTRUCTION` and does not become the positive policy. Quantity rounding, market calendar, and timezone remain unresolved. PR #20. No Gmail, broker, credential, Supabase, order, SIM, or `LIVE` authority. Group 4A status for workstream registry purposes: `INTEGRATED_AND_CERTIFIED` (offline only). |
| Four-lane workstream governance | On canonical `main` by history-preserving fast-forward of PR #23 tip `f5880cfcfaa6d994f369e04d73c844fd1402d74c`, tree `1700b1b442ef72b31b24aa8dcdf65e43525376e4` from prior main `41218abb2eda5f06001703fb83c2cb9e43e5ec2e`, tree `39f0ab05c49b533270964b303601539feeff570f`. No squash, rebase, force-push, or merge commit. Independent PASS at `3676e11` / `2cbbe823…`; post-PASS successors classified `EVIDENCE_ONLY_PLUS_NONSEMANTIC` (verifier `bc-e255e4a7-f783-5ef6-8fc3-f4cbd2d0d926`). Registry activated: `docs/WORKSTREAM_STATUS.md`. Dependencies unchanged IDs. Active specialist drafts remain unmerged and were not rewritten: Gmail PR #21 `a2cef6f3…` (`WAITING_OPERATOR`, ADR-0004 Proposed); TradeStation PR #22 `a6c5f1d7…` (`WAITING_PROVIDER`, ADR-0005 Proposed). PR #19 `SUPERSEDED`. Database lane `NOT_STARTED`. No credential, broker, Supabase, order, SIM, or `LIVE` authority. The specialist SHAs and the database `NOT_STARTED` sentence in this cell are the PR #23 integration-time record. Unresolved item 9 carries the 2026-10-09 identity. |
| Gmail read-only corpus | Gate A proposal text is on canonical `main` by fast-forward of PR #21 merge `2c895291a3b4282f8cf5c7426c705bfdab365c47`, tree `25ebd09e495bb2db7b7f856963a0af876a378457`, parents `a2cef6f3527b2aab7319a2628874fcdcaf03acac` and `7c33d45c0a057d189ad6c5acc288625d57539413`, merged 2026-10-09T15:49:31Z. ADR-0004 remains Proposed. Its Decision section remains blank. No Gmail API call, OAuth grant, or credential is recorded. The researched minimum scope is `https://www.googleapis.com/auth/gmail.readonly`. Broader Gmail scopes are not requested. Supabase and TradeStation are not connected. This merge is not a connection certification. |

`LIVE` remains unauthorized. The candidate-specific annotated tag
`phase1-accepted-abc1fb6` fixes the accepted commit without making the
acceptance metadata part of its tree. Acceptance is not implementation,
certification, deployment, or later-phase authorization.

## Exact-tree candidate mechanism

Git commit identity cannot be embedded in the tree that determines that same
identity. Therefore:

1. a candidate commit contains all normative documents, fixtures, tests, and
   pre-validation audit text, but does not claim its own hash;
2. its immutable Git tree object is the exact candidate content identity;
3. a descendant evidence-only commit records the candidate commit and tree
   hashes plus ancestry, diff-scope, test, and cleanliness results;
4. the evidence commit is not silently part of the candidate tree; and
5. any later normative delta makes the recorded candidate stale and requires a
   new candidate commit/tree and descendant attestation.

This mechanism avoids impossible self-reference while making completeness
auditable. Candidate identity and verification alone did not imply acceptance;
the later explicit human Operator decision recorded here does.

## Established

- Repository governance and least-authority rules
- Four scoped Phase 1 agent roles: coordinator plus three researchers
- Four-lane Phase 2 workstream coordination contracts on canonical `main`
  via PR #23 (status, ownership, dependencies, integration protocol,
  handoff template, `.cursor` coordination rule and integration-coordinator
  agent)
- ADR process and research evidence contract
- Skeleton locations for configuration, documentation, source, and tests
- Explicit fail-closed boundary around `LIVE`, credentials, real accounts, and
  real capital
- Phase 1B architecture, lifecycle, data, event, idempotency, reconciliation,
  monitoring, metrics, reporting, test, SIM certification, and promotion
  contracts are drafted for review
- Deterministic synthetic WDC conformance fixture is documented
- Public TradeStation documentation establishes scoped API facts recorded in
  `BROKER_CONTRACT.md`; twelve production-critical behavior groups remain
  unresolved
- Phase 1A governance failure scenarios and the Phase 1B design and broker
  outputs are reconciled in `PHASE_1C_RECONCILIATION.md`
- Four verified contract/fixture contradictions are corrected and audited in
  `PHASE_1D_CORRECTIONS.md`
- Exact Phase 1 acceptance evidence, the 45-file inventory, tag identity,
  hashes, unresolved broker behaviors, and non-authorizations are recorded in
  `PHASE_1_ACCEPTANCE_MANIFEST.md`
- A typed Python 3.12 foundation now implements local `DRY_RUN` safety,
  broker-neutral domain/state contracts, deterministic fixture evaluation,
  reconciliation derivation, and local PostgreSQL development persistence.

## Not established

No broker behavior has been accepted or verified against an account or broker
runtime. No production strategy, market-data source, risk threshold, deployment
approach, or operational threshold has been selected. The accepted contracts
remain broker-neutral. The Phase 1E implementation is a local offline
foundation, not trading, backtesting, broker integration, deployment, or
production certification.

## Research readiness gates

The three Phase 1B research workstreams may begin only after Phase 1A
validation confirms:

- all required governance artifacts exist;
- exactly four Phase 1 agent definitions exist
  (`governance-coordinator`, `broker-api-researcher`,
  `strategy-data-researcher`, `risk-operations-researcher`);
- all mandatory rules are always applied;
- the then-current `SIM`-only and `LIVE`-unauthorized Phase 1A language was
  consistent (superseded for active authority by Phase 1D `DRY_RUN`);
- no secrets or implementation were introduced; and
- the governance branch is reviewable in a draft pull request.

Each workstream must follow `docs/research/README.md`. Research permission does
not authorize implementation or any interaction with an account.

All listed readiness gates passed on 2026-09-25. The broker/API,
strategy/data, and risk/operations workstreams are ready to begin independently
once this governance baseline is adopted through merge or explicit human
direction.

Additive four-lane coordination (2026-10-08, Lane 1 branch, not yet on
`main`) introduces `integration-coordinator` and
`.cursor/rules/80-workstream-coordination.mdc` without removing the four
Phase 1 agents or rewriting the Phase 1 acceptance manifest. The historical
"exactly four" gate remains the Phase 1A research-readiness record; it is not
a prohibition on later additive coordination roles.

## Unresolved items

1. The acceptance instruction identifies the human Operator by role; no
   additional personal or service identifier is recorded in repository
   evidence.
2. Bounded Phase 1 acceptance does not expand ADR-0001 or authorize
   implementation. ADR-0001 remains Proposed. ADR-0002 is Accepted for
   C1/U-10 only and does not expand `PHASE1_ACCEPTED`.
3. Twelve production-critical broker behavior groups remain unresolved;
   strategy/data and risk/operations facts remain unresearched.
4. Legal, regulatory, entitlement, security, and data-licensing obligations
   are unknown.
5. Technology, persistence, deployment, operating thresholds, recovery
   objectives, and risk limits are unknown.
6. Phase 2 is not generally authorized. P2-0 documentation on `main`
   and Gate `H1` PASS at `33110c7` do not grant a general Phase 2
   entry. The Operator authorizes the offline Group 2 foundation only.
   C1 (U-10) is **RESOLVED** by Operator acceptance of ADR-0002 after
   `C1_U10_CONTRACT_PASS` on `a4213f8`. That acceptance is not operational
   credential certification, key management, Supabase selection, or `LIVE`
   authorization, and it does not open G1. The non-Cursor
   bootstrap injector, key custody, retention, and the SIM database
   host remain later decisions. The 0 USD constraint supersedes only
   the initial-deployment effect of the historical RDS recommendation.
   Supabase is not accepted. Credentials, broker calls, Supabase
   connections, provisioning, SIM orders, and `LIVE` remain
   unauthorized.
7. External governance enforcement and authenticated Operator identity are not
   established. `DRY_RUN` remains structurally non-network; future broker
   connectivity and zero-order-attempt controls are not authorized.
8. Offline Group 4A on this branch selects email retention as
   `HASH_PROVIDER_REF_FIELD_EVIDENCE` (ADR-0003). It does not select
   quantity rounding, a market calendar, or a timezone. Amendment,
   exit-alert, and cancel grammars remain `DEFERRED_FIXTURE_REQUIRED`.
   Relative weekday and month-day-without-year dates are unresolved.
   Numeric and timestamp dates in an economic sentence quarantine as
   unsupported. Negated or conflicting first-exit and sibling-cancel
   wording does not become the positive policy. The certified parser is
   on canonical `main` by exact fast-forward of
   `ce045c14b119d882505a947a7826005ff6d99103`. The sentence that the
   parser is not merged is pre-fast-forward. It grants no Gmail, broker,
   credential, Supabase, order, SIM, or `LIVE` authority.
9. Four-lane specialist tracks are not integrated merely by registry
   existence. After PR #23 integration, continuity/bootstrap agents
   attested: Gmail PR #21 still awaits Operator OAuth (`DEP-GMAIL-001`);
   TradeStation PR #22 still awaits provider callback clarification
   (`DEP-TS-001`); Database branch `cursor/db-zero-cost-bootstrap-51f4`
   holds zero-cost research + implementer-only local TokenStore PG
   evidence (`DEP-DB-001`/`DEP-DB-002` still open). Quantity rounding
   (`DEP-CORE-001`) and market calendar/timezone (`DEP-CORE-002`) remain
   unresolved. Supabase remains **NOT_ACCEPTED**.
   Coordination checkpoint on 2026-10-08 reattested canonical main
   `af0d69b1dfc2046899db05a2f12767fc20b623ae` /
   `4e1ed263e745b9896bf9384a2a9453566ebd6e0b` (`BASELINE_MATCH`).
   PR #21 and PR #22 are `CONFLICTING` with that main on
   `docs/CURRENT_STATE.md` and `docs/ENGINEERING_JOURNAL.md`.
   Newer Lane 4 draft PR #24 tip `db570fac13cb33b84c98afb89c3f4722128ae179`
   contains that main and records independent local TokenStore PostgreSQL
   PASS (`LANE4_DEP_DB_002_INDEPENDENT_PASS`). `DEP-DB-002` stays OPEN.
   Lane 4 stays `READY_FOR_VERIFICATION`, not integration-eligible.
   The earlier sentence that Lane 4 had no draft PR and that independent
   verification was `NOT_RUN` is superseded for those two facts only.
   No specialist branch was rewritten. No specialist PR was merged.
   Governance and registry reattestation on 2026-10-09: canonical main
   `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` /
   `fc97582f22ebf2d24f132c9afe2720430b197f9f` (PR #25 MERGED).
   PR #21 head is unchanged at `a2cef6f3527b2aab7319a2628874fcdcaf03acac`
   and remains `CONFLICTING` (merge-base `41218abb`).
   PR #22 head advanced to `16aa5788a17ac77291530bb836af256a6f79f89f` /
   `74ce64cb17585fd1aefc58970ef4850cfc40c948`, merge-base `af0d69b`,
   and remains `CONFLICTING` on `docs/CURRENT_STATE.md` and
   `docs/ENGINEERING_JOURNAL.md`. `DEP-TS-001` stays OPEN.
   Continuity verification does not cover `16aa578`.
   PR #24 head advanced to `d491c3434872fac88b1c5be28281dce94ea11a8b` /
   `ac228e7342c8f75868cc0a683920e26d75cea31f`, contains attested main,
   and is `MERGEABLE`. Lane 4 stays `READY_FOR_VERIFICATION`.
   `DEP-DB-001` and `DEP-DB-002` stay OPEN. The earlier local PASS
   still describes unchanged executable bytes of `d949ce0` and does not
   certify the later documentation commits. ChatGPT advisory files were
   not added to Git. No specialist branch was rewritten in this sync.
   PR #21 later merged by fast-forward at
   `2c895291a3b4282f8cf5c7426c705bfdab365c47`. The sentences above that
   call PR #21 an open conflicting draft are the pre-merge record.
10. Local Gmail credential custody design, accepted 2026-10-09 as a
    design only. Storage is Windows Credential Manager. Credential type
    is `CRED_TYPE_GENERIC` = 1. Persistence is
    `CRED_PERSIST_LOCAL_MACHINE` = 2. Identity is the current
    operator-controlled Windows user. The proposed target name is
    `swing-trading/lane3/gmail/dev/refresh-token`. Purpose is a future
    local development bootstrap for Lane 3 Gmail OAuth only. Incremental
    service cost is 0 USD. This acceptance does not authorize real Gmail
    OAuth consent, credential provisioning, refresh-token creation,
    storage of a real Gmail token, mailbox access, Gmail API requests,
    cloud deployment, TradeStation credential access, SIM orders, LIVE
    orders, or any other economic action. ADR-0004 stays Proposed.
    `DEP-GMAIL-001` stays OPEN. No offline credential-module
    implementation is authorized by this design record. Current state
    still denies credentials and does not mark a Gmail implementation
    phase authorized. A later explicit Operator authorization, recorded
    in current state, is required before Lane 3 may write that module.
    Synthetic fixtures and mocked Windows API behavior do not remove
    that requirement. ADR-0002 remains the accepted provider-neutral
    TokenStore decision and is not modified. Group 4A remains the
    certified offline parser only.
11. Operator decision of 2026-10-09, recorded as intent only. The
    Operator authorized pursuing an offline-only Lane 3 Windows
    Credential Manager implementation that uses synthetic values and
    mocked Windows API calls, subject to every accepted repository
    authorization gate. The sentence does not authorize real Windows
    Credential Manager provisioning, real credential reads or writes,
    refresh-token creation or storage, Google OAuth consent or callback
    execution, Gmail API calls, mailbox acquisition, TradeStation API
    calls, TokenStore changes, Supabase deployment, `SIM` or `LIVE`
    activity, broker order submission, acceptance of ADR-0004, or
    closure of `DEP-GMAIL-001`.
    The scope that may be considered only after the remaining gates
    pass is a Python credential-storage interface, a Windows Credential
    Manager adapter for future use, synthetic test values, mocked
    `advapi32` calls, deterministic unit tests, explicit failure-path
    tests, unsupported-platform and permission-denied handling, and
    offline use of abstractions that are already authorized. Tests must
    show that real credential APIs and external network calls are not
    invoked. The target name
    `swing-trading/lane3/gmail/dev/refresh-token` stays a design
    constant and is not a provisioning instruction. Credential type
    stays `CRED_TYPE_GENERIC` = 1. Persistence stays
    `CRED_PERSIST_LOCAL_MACHINE` = 2. Identity stays the current
    operator-controlled Windows user. Incremental credential-store cost
    stays 0 USD. Local-machine persistence is not hardware-backed
    security and does not protect a compromised Windows session.
    This record is not implementation permission.
    `docs/AGENT_AUTHORITY.md` requires an Operator-accepted ADR for a
    material architecture or safety decision, and it requires an
    implementation phase to be marked authorized in current state on
    canonical `main`. ADR-0004 stays Proposed. Its scope is Gmail
    acquisition, and accepting it is outside this decision. Lane 1 does
    not author and accept a substitute ADR. `DEP-GMAIL-001` stays OPEN.
    The denials of credentials, broker and network activity,
    TradeStation `SIM`, order submission, and `LIVE` are unchanged.
    `DRY_RUN` remains the only authorized execution mode. Lane 3 must
    not receive coding instructions from this item. The remaining
    Operator decision is whether to accept a later narrow ADR whose
    only decision is the offline synthetic and mocked adapter above.
    Until that ADR is Accepted by the Operator and a separate
    integration gate places the authorization on canonical `main`,
    implementation permission does not exist.

## Evidence

Starting-state and change evidence is recorded in
`docs/ENGINEERING_JOURNAL.md`. Phase 1A validation completed successfully on
2026-09-25. Phase 1B design and fixture validation passed within their stated
scope. Phase 1C integrated-content validation is recorded in the journal.
Independent verification passed the exact Phase 1 candidate, and bounded
Operator acceptance is recorded in `PHASE_1_ACCEPTANCE_MANIFEST.md`. The human
Operator authorized the bounded Phase 1E offline implementation; findings
F01–F06 across all remediation rounds were corrected and independently
re-verified, culminating in the Gate A pass (218 tests, PostgreSQL 16.15) at
SHA `eb4b3b550874b4729abf7902cda2df8bf01e70ba`. The Gate B evidence-only
closure audit in `docs/PHASE_1_CLOSURE.md` records `PHASE1A_COMPLETE` through
`PHASE1E_COMPLETE` and `PHASE1_COMPLETE`. No Phase 2, broker, TradeStation
`SIM`, credential, account, order, deployment, real-capital, or `LIVE`
authority follows.

P2-0 Group 1 specialist documents were integrated on 2026-09-29 onto
isolated branch `cursor/p2-0-integration-1f76` from then-canonical `main`
`1ecbbe6d487d97195fde393b05c9499357599bdb`, preserving specialist commit
lineage. Coordinator reconciliation is `docs/PHASE_2_RECONCILIATION.md`.
Independent Gate `H1` verification **PASS (C1 carried)** is recorded for
exact artifact `33110c7c0aa2f385d179a1f66d068daca2c47537` /
`5f45983b19bed47988133c5b832e125d0602133c`. On 2026-09-30 canonical `main`
was fast-forwarded to evidence HEAD
`9631de3bd8a6a2e24c6833ca534c5e626fdb7b75`, tree
`41588e7af631db0213b80d5a02472dd0e4d206ba` (PR #12). This descendant
evidence commit is neither the attested H1 tree nor that fast-forward
tip. C1 remains open. Group 2 remains unauthorized. Phase 2
implementation remains unstarted. No credential, broker, TradeStation
`SIM`, order, deployment, real-capital, or `LIVE` authority follows.

On 2026-09-30, after that evidence commit was already `origin/main`,
canonical `main` fast-forwarded PR #14 commit
`e549ab9e59604abecce0c882c60f845f00f8be09`, tree
`dee2ef72378bcffa8499bd1d560c8c324a97569e`, then history-preserved PR
#13 commit `78f485b33bdd3f859d540458ba170b2353c04c61`, tree
`28b3ced5663c00f4b8d32828ed2b160344d09805`, as merge
`e0ec755e39c897492fbc8d970bb165d8335d361c`, tree
`5e687dc37376b1b9c092a2a56a40348e5d36532f`. No squash, rebase, or
force-push. The prior sentences that C1 remains merely open and that
Group 2 remains unauthorized are **pre-authorization**. Independent
verification of `e549ab9` returned **PASS** and
**OFFLINE_IMPLEMENTATION_UNBLOCKED**, not
`P2_G2_CONTRACT_DECISION_REQUIRED`. C1/U-10 has a verified
**PROPOSED** resolution. The human Operator authorizes the offline
Group 2 foundation only. Bootstrap injector, key custody, retention,
and the SIM host remain later decisions.
`INITIAL_DATABASE_INCREMENTAL_SERVICE_COST = 0 USD` supersedes only
the initial-deployment effect of the historical RDS recommendation.
Supabase is **NOT_ACCEPTED**. Credentials, broker calls, Supabase
connections, provisioning, SIM orders, and `LIVE` remain unauthorized.

On 2026-09-30 the human Operator accepts ADR-0002. Independent review
`C1_U10_CONTRACT_PASS` of
`a4213f8356a9e32ca4647865ee98e13660e3d656`, tree
`c07487c88f24f9432de89df7f574130274d50b4b`, left C1 **PROPOSED**. This
status commit resolves C1/U-10. Earlier sentences that leave C1 proposed,
open, or unclosed are **pre-closure**. Contract acceptance is not
operational credential certification, key management, Supabase selection,
or `LIVE` authorization. Non-blocking residuals, recorded in
`docs/ENGINEERING_JOURNAL.md` and `docs/C1_U10_CONTRACT_STATUS.md`, are
process-local same-attempt tracking, fence monotonicity not forced,
`read_redacted` not environment-scoped, and stale "not implemented"
wording in the historical proposal documents. Those residuals do not
reopen C1. No source or test file changes. This branch is not merged.
