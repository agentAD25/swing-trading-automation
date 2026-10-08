# Current State

- Last updated: 2026-10-08
- Current phase: Phase 1 closed (Gate B closure audit); offline Group 2
  foundation implemented on this branch and not merged; C1/U-10 resolved;
  offline Group 4A email contract is on canonical `main` by exact
  fast-forward of `ce045c14b119d882505a947a7826005ff6d99103`
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
| Four-lane workstream governance | Lane 1 coordinator bootstrap on branch `cursor/integration-four-lane-governance-8992`, draft PR #23 (not on `main` until authorized integration). Attested canonical `main` at bootstrap: `41218abb2eda5f06001703fb83c2cb9e43e5ec2e`, tree `39f0ab05c49b533270964b303601539feeff570f` (`BASELINE_MATCH`). Independently verified tip `3676e116591087c0cbf979b7929a2fb964415862`, tree `2cbbe8232063d75c83333850a32bd40c2b24a46d` (**PASS**; verifier `bc-3289987e-ba29-5c68-a93e-fd3b27b71e9e`). Registry: `docs/WORKSTREAM_STATUS.md`. Ownership/hierarchy: `docs/WORKSTREAM_OWNERSHIP.md`. Dependencies: `docs/WORKSTREAM_DEPENDENCIES.md` (`DEP-TS-001`, `DEP-GMAIL-001`, `DEP-DB-001`, `DEP-DB-002`, `DEP-CORE-001`, `DEP-CORE-002`). Integration gates: `docs/INTEGRATION_PROTOCOL.md`. Active specialist drafts remain unmerged: Gmail PR #21 head `a2cef6f3527b2aab7319a2628874fcdcaf03acac` (`WAITING_OPERATOR`, ADR-0004 Proposed); TradeStation PR #22 head `a6c5f1d7109e156eb0e9257216c3b5dbed17f653` (`WAITING_PROVIDER`, ADR-0005 Proposed). Historical TradeStation PR #19 is `SUPERSEDED` (ADR number conflicts with accepted ADR-0003; do not auto-merge). Database lane `NOT_STARTED`. This bootstrap implements no TradeStation, Gmail, or database functionality and grants no credential, broker, Supabase, order, SIM, or `LIVE` authority. |

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
- Four-lane Phase 2 workstream coordination contracts on the Lane 1
  governance branch (status, ownership, dependencies, integration protocol,
  handoff template, `.cursor` coordination rule and integration-coordinator
  agent); not authoritative on `main` until integrated
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
   existence. Gmail PR #21 awaits Operator OAuth setup (`DEP-GMAIL-001`).
   TradeStation PR #22 awaits provider callback clarification
   (`DEP-TS-001`). Database lane awaits zero-cost remote PostgreSQL
   selection (`DEP-DB-001`) and TokenStore PostgreSQL execution evidence
   (`DEP-DB-002`). Quantity rounding (`DEP-CORE-001`) and market
   calendar/timezone (`DEP-CORE-002`) remain unresolved. Supabase remains
   **NOT_ACCEPTED**.

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
