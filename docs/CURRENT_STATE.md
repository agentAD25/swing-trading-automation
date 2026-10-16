# Current State

- Last updated: 2026-10-16 (item 24 proposal, Alpaca Paper execution direction). Item 24 becomes effective only when an independent verifier has passed this exact commit, an Operator decision has authorized integration of this exact commit, and this exact commit is canonical `main`. While any condition is unmet, item 24 does not authorize coding or a provider call. When all three are met, the only new authority is Lane 2's offline synthetic contract in the two paths named in item 24. That authority is not an Alpaca credential, a paper order, a network call, or a change to TradeStation, Gmail, or PostgreSQL. Items 18 through 23 stay effective and are not revised. This proposal does not close a dependency, accept ADR-0004 or ADR-0005, choose a database provider, or authorize credentials, network access, a real database, `SIM`, or `LIVE`.
- Last updated: 2026-10-16 (item 23 proposal, local Windows Gmail Gate C one-shot connectivity). Item 23 becomes effective only when an independent verifier has passed this exact commit, an Operator decision has authorized integration of this exact commit, and this exact commit is canonical `main`. While any condition is unmet, item 23 does not authorize coding or a provider call. When all three are met, the only new authority is Lane 3's offline implementation of the two paths named in item 23. That authority is not integration of the implementation, a live OAuth login, a Gmail API call, Google Cloud provisioning, or a change to the Gate B refusal. Items 18, 19, 20, 21, and 22 stay effective and are not revised. This proposal does not close a dependency, accept ADR-0004 or ADR-0005, choose a database provider, or authorize credentials, network access, a real database, `SIM`, or `LIVE`.
- Last updated: 2026-10-16 (item 22 proposal, parser security-scan scope for the authorized OAuth module). Item 22 becomes effective only when an independent verifier has passed this exact commit, an Operator decision has authorized integration of this exact commit, and this exact commit is canonical `main`. While any condition is unmet, item 22 does not authorize editing `tests/group4_email/test_attacks.py` or any other path. When all three are met, the only new authority is the one-file test-scope correction named in item 22. That authority is not a change to the OAuth module, a live OAuth login, a Gmail API call, or integration of PR #48. Items 18, 19, 20, and 21 stay effective and are not revised. This proposal does not close a dependency, accept ADR-0004 or ADR-0005, choose a database provider, or authorize credentials, network access, a real database, `SIM`, or `LIVE`.
- Last updated: 2026-10-14 (item 21 proposal, local Windows Gmail OAuth connectivity governance). Item 21 becomes effective only when an independent verifier has passed this exact commit, an Operator decision has authorized integration of this exact commit, and this exact commit is canonical `main`. While any condition is unmet, item 21 does not authorize coding. When all three are met, the only new authority is offline implementation of the two paths named in item 21. That authority is not a live OAuth login, a Gmail API call, native Credential Manager access, or the corpus connection described by Proposed ADR-0004. Items 18, 19, and 20 stay effective and are not revised. This proposal does not close a dependency, accept ADR-0004 or ADR-0005, choose a database provider, or authorize credentials, network access, a real database, `SIM`, or `LIVE`.
- Last updated: 2026-10-13 (item 20 proposal, one synthetic ingestion composition). Item 20 becomes effective only when an independent verifier has passed this exact commit, an Operator decision has authorized integration of this exact commit, and this exact commit is canonical `main`. While any condition is unmet, item 20 does not authorize coding. Item 19 stays the operative grant for the three modules already integrated under that item. This proposal does not reopen, revise, or expand item 18 or item 19. It does not close a dependency, accept ADR-0004 or ADR-0005, choose a database provider, authorize a Gmail API call, or authorize credentials, network access, a real database, `SIM`, or `LIVE`.
- Last updated: 2026-10-12 (item 19 proposal, three further non-economic `DRY_RUN` implementation grants). Item 19 becomes effective only when an independent verifier has passed this exact commit, an Operator decision has authorized integration of this exact commit, and this exact commit is canonical `main`. While any condition is unmet, item 19 does not authorize coding. Item 18 stays the operative grant for the three modules already named there. Its activation sentence in the next bullet is the historical record of integrated commit `d4e7aeb1f7cd7c16c81b1f026295ad91319041cc`, which is an ancestor of canonical main. This proposal does not reopen, revise, or expand item 18. It does not close a dependency, accept ADR-0004 or ADR-0005, choose a database provider, authorize an acquisition-to-receipt orchestrator, or authorize credentials, network access, a real database, `SIM`, or `LIVE`.
- Last updated: 2026-10-12 (item 18, three non-economic `DRY_RUN` implementation grants). Item 18 becomes effective only when an independent verifier has passed this exact commit, an Operator decision has authorized integration of this exact commit, and this exact commit is canonical `main`. No further activation step is required after that incorporation. While any of those conditions is unmet, item 18 does not authorize coding. When all three are met, item 18 is the operative grant for the three bounded modules named in that item. Item 17 remains the operative ADR-0007 persistence-exception grant. Item 13 remains the offline Gmail credential-adapter grant. This record does not close a dependency, accept ADR-0004 or ADR-0005, choose a database provider, or authorize credentials, network access, a real database, `SIM`, or `LIVE`.
- This branch adds the item 18 Lane 2 classifier in `src/swingtrade/group3_auth/order_report.py`. Its labels are local synthetic report evidence and are not order instructions. `src/swingtrade/group3_auth/brokerage_read.py` is unchanged. The branch is not merged. ADR-0005 stays Proposed. `DEP-TS-001` through `DEP-TS-004` stay OPEN.
- Prior canonical header, retained as the PR #22 integration record: 2026-10-12 (history-preserving merge of canonical main `b35b301bdb582d8c537c1f511f1e3c30de98920b`, tree `a209fb5f0fd9d770d5e6142ee31e4fce2b30a5fd`). That main integrates PR #24 documentation, the offline Gmail credential adapter, and the ADR-0007 persistence remediation. Item 17 remains the sole operative Lane 4 implementation authority for Accepted ADR-0007. Items 15 and 16 remain the historical pre-correction record and do not prohibit that bounded implementation. Item 17 is not a TradeStation authorization. `DEP-TS-001` through `DEP-TS-004` stay OPEN. Real credentials, OAuth, Gmail access, TradeStation SIM, and LIVE remain unauthorized. Governance PR #23 and checkpoint PR #25 remain integrated. The verified parser blobs remain those of `227db721944dc0a470046fdec4b60f581ff28d38`.
- This branch also records the 2026-10-08 Lane 2 provider-evidence intake and the 2026-10-09 Operator preference `OPERATOR_PREFERENCE_OPTION_A_REGULAR_WEB_CONFIDENTIAL_CLIENT`. That preference is not ADR acceptance.
- Current phase: Phase 1 closed (Gate B closure audit); offline Group 2
  foundation implemented on this branch and not merged; C1/U-10 resolved;
  offline Group 4A email contract is on canonical `main` by exact
  fast-forward of `ce045c14b119d882505a947a7826005ff6d99103`; Gmail
  read-only corpus Gate A is proposed and not connected. On this
  branch, 2026-10-06 TradeStation Client Experience answers are recorded
  in `docs/P2_TS_PROVIDER_EVIDENCE.md`. They are not on canonical `main`
  until this branch lands. They do not authorize a credential, a SIM call,
  or `LIVE`. The 2026-10-08 intake in
  `docs/P2_TS_PROVIDER_EVIDENCE_2026-10-08.md` proposes a Regular Web
  confidential client in ADR-0005 and leaves that ADR Proposed. It does
  not verify the issued key's application type, onboard a credential, or
  authorize SIM or `LIVE`. Native PKCE callback confirmation remains
  unclosed by the provider. The 2026-10-09 preference does not close it
  and does not accept ADR-0005. `DEP-TS-002`, `DEP-TS-003`, and
  `DEP-TS-004` stay open. The consolidated Client Experience follow-up is
  unsent. The 2026-10-10 comparison in
  `docs/P2_TS_OFFICIAL_DOCS_2026-10-10.md` uses public documentation only.
  It does not confirm the issued key, onboard a credential, or authorize
  SIM or `LIVE`. The same-day parser remediation accepts a documented
  order `Spread` string, keeps economic nulls fail-closed, classifies
  HTTP 400 and 404, and reads `OrderID` only on order-by-id errors. It
  does not connect, retry, or submit an order.
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
| TradeStation provider evidence (2026-10-06) | Recorded on this branch. Not on canonical `main` until this branch lands. Draft PR #19 (`bc6ab7ea92310ffa133b75b498f7f245af11f166`) is not an ancestor of `main` and is not updated. ADR-0005 is Proposed; its Decision is blank. A SIM-only API key is not available. Default personal-use refresh tokens are non-rotating and long-lived. `offline_access` may be omitted for an attended probe. Groups 6, 7, and 10 advance and stay open. Groups 1–5, 8, 9, 11, and 12 are unchanged. Native PKCE was an engineering preference and was not selected. No credential, authorization, SIM call, LIVE call, order, Gmail change, or Supabase connection. |
| TradeStation provider evidence (2026-10-08) | Same branch, draft PR #22. The Operator's written clarification is reconciled in `docs/P2_TS_PROVIDER_EVIDENCE_2026-10-08.md` without replacing the 2026-10-06 quotations. ADR-0005 proposes Regular Web Option A and remains Proposed with a blank Decision. `DEP-TS-001` is not closed by the provider. DRY_RUN destination denial, scope checks, fake 1,200-second sessions, fixture reads, and per-login 429 stops are local and non-network. No credential onboarding, SIM call, LIVE call, or order. |
| TradeStation Option A preference (2026-10-09) | Same branch, draft PR #22. Preference documentation commit `c32052832900360ec0993be29d989141e71cb214`, tree `7b7c1a7a9f08b03d7693439d3a98fac661fa6c07`. Operator preference `OPERATOR_PREFERENCE_OPTION_A_REGULAR_WEB_CONFIDENTIAL_CLIENT` is recorded for planning and provider clarification. ADR-0005 stays Proposed with a blank Decision. Recommended `DEP-TS-001` narrative is `SUPERSEDED_BY_OPTION_A_PENDING_ARCHITECTURE_ACCEPTANCE`; registry state stays `OPEN` until Lane 1 records it, and the provider did not close it. `DEP-TS-002`, `DEP-TS-003`, and `DEP-TS-004` stay open. The 2026-10-09 Client Experience draft is `UNSENT`. No credential, OAuth login, broker request, SIM call, LIVE call, order, or Phase 2 authorization. |
| TradeStation official documentation (2026-10-10) | Same branch, draft PR #22. Research documentation commit `00b6e7ede7fdae99710bd4e82129902cde244237`, tree `f3f92d19d96ddd15d1d0dd530da11f054ade580a`. `docs/P2_TS_OFFICIAL_DOCS_2026-10-10.md` records current public pages. Regular Web is the published default and is not proof of the issued key. Key format does not prove application type. Scope and refresh-rotation page conflicts remain. One HTTPS callback is compatible with documented Regular Web and is not a registered callback. ADR-0005 stays Proposed. `DEP-TS-002`, `DEP-TS-003`, and `DEP-TS-004` stay open. No credential, OAuth, SIM call, LIVE call, or order. |
| TradeStation read-only parser compatibility (2026-10-10) | Same branch, draft PR #22. Implementation `227db721944dc0a470046fdec4b60f581ff28d38`, tree `980ec01635c5e4eb0abec297fe8bbf37f12d18fa`, independently verified by `bc-0a306c68-0d69-5aee-a999-736cff1a54d8`. Offline fixtures only. Order `Spread` is a string. Economic nulls fail closed and are not coerced to zero. HTTP 400 and 404 have their own non-retryable reasons. Order-by-id errors may carry an opaque `OrderID`. DRY_RUN denial is unchanged. ADR-0005 stays Proposed. `DEP-TS-002`, `DEP-TS-003`, and `DEP-TS-004` stay open. |

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
3. Twelve production-critical broker behavior groups remain unresolved.
   The 2026-10-06 Client Experience answers advance groups 6, 7, and 10
   and do not close them. Groups 1–5, 8, 9, 11, and 12 are unchanged.
   Strategy/data and risk/operations facts remain unresearched.
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
   TradeStation PR #22 still awaits provider clarification
   (`DEP-TS-001` is not closed by the 2026-10-08 reply); Database branch `cursor/db-zero-cost-bootstrap-51f4`
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
    `DRY_RUN` remains the only authorized execution mode.     Lane 3 must
    not receive coding instructions from this item.
12. Operator acceptance of ADR-0006, design only, recorded 2026-10-10.
    The accepted artifact is the Proposed file at commit
    `5855d5bb7380be49422671aeecd870589d38b8c1`, tree
    `13a3d644b9136b1fcda739e7035fd40bdfa51e9b`, blob
    `c3fd7516211d338226af3d531d56c8a030dfef3b`, verification token
    `LANE3_ADR0006_REVERIFIED_PASS`. Lane 3 authored that proposal.
    Lane 1 records the Operator's acceptance and does not author the
    design. The accepted scope is the Gmail-only offline synthetic and
    mocked Windows Credential Manager adapter: `CRED_TYPE_GENERIC` = 1,
    `CRED_PERSIST_LOCAL_MACHINE` = 2, the current operator-controlled
    Windows user, target
    `swing-trading/lane3/gmail/dev/refresh-token`, no Enterprise
    roaming, no TradeStation TokenStore integration, zero incremental
    credential-storage service cost, and no deployment host. Credential
    Manager is not hardware-backed isolation and cannot stop retrieval
    by code running as the same Windows user.
    This acceptance does not authorize implementation, native credential
    API calls, real credential storage or retrieval, OAuth, Gmail API
    access, mailbox access, cloud deployment, TradeStation
    authentication, broker orders, `SIM`, `LIVE`, or any economic
    action. ADR-0004 stays Proposed. ADR-0003 stays Accepted.
    `DEP-GMAIL-001` stays OPEN. `DRY_RUN` remains the only authorized
    execution mode. The Accepted ADR text is a new blob and is not
    certified by `LANE3_ADR0006_REVERIFIED_PASS`. Fast-forward of
    `5a04c5e` placed this design acceptance on canonical `main`. That
    fast-forward did not authorize implementation.
13. Offline Gmail credential-adapter implementation, authorized
    2026-10-10. Lane 3 may implement and test the Gmail-specific
    Windows Credential Manager adapter using only synthetic values and
    mocked Windows native API responses, in a strictly offline
    development environment, under Accepted ADR-0006. This commit adds
    no application source. The authorization is the Gmail-only scope in
    ADR-0006: `CRED_TYPE_GENERIC` = 1, `CRED_PERSIST_LOCAL_MACHINE` = 2,
    the current operator-controlled Windows user, and target identifier
    `swing-trading/lane3/gmail/dev/refresh-token`. Tests must keep real
    native API execution disabled and must fail if an unmocked Windows
    credential call or any external network call is attempted.
    Credential Manager is not hardware-backed isolation.
    This sentence does not authorize real Credential Manager calls,
    unmocked `CredWriteW`, `CredReadW`, or `CredDeleteW`, real token
    generation, storage, retrieval, or deletion, OAuth consent,
    redirects, callbacks, or token exchange, Gmail API or mailbox
    access, TradeStation or TokenStore changes, remote database
    activity, operational deployment, `SIM` or `LIVE` trading, broker
    orders, or Gmail Gate B. ADR-0006 stays Accepted as that design.
    ADR-0004 stays Proposed. ADR-0002 and ADR-0003 stay Accepted.
    `DEP-GMAIL-001` stays OPEN. `DRY_RUN` remains the only authorized
    execution mode. A later integration gate is required before any
    resulting adapter commit may enter canonical `main`. Lane 3 must
    not self-merge that work.
14. TradeStation dependency registration, recorded 2026-10-11, against
    canonical main `8a17bec501df94238fe7588f84f7f1f51fee8baf` / tree
    `03d48c9ae453bdfc6a1cdf9cdc43a359e76efb1b`. Draft PR #22 head
    `330c47c40249fdf4e1f2a1bf3fa61e36e05ae4fc` / tree
    `864f0c16891af03bce27b40a4d52b843bb444b5f` is not merged.
    `DEP-TS-001` stays `OPEN`. Its recommended narrative is
    `SUPERSEDED_BY_OPTION_A_PENDING_ARCHITECTURE_ACCEPTANCE`. The
    provider did not confirm the native PKCE callback, and the
    controlled state `SUPERSEDED` is not applied. `DEP-TS-002`,
    `DEP-TS-003`, and `DEP-TS-004` are registered `OPEN` for the issued
    key's application type, the `openid ReadAccount` grant, and one
    later HTTPS callback. Public documentation and the Operator
    preference `OPERATOR_PREFERENCE_OPTION_A_REGULAR_WEB_CONFIDENTIAL_CLIENT`
    do not close them. ADR-0005 stays Proposed on PR #22 with a blank
    Decision and is not on this main. Offline parser `src/` and `tests/`
    trees at that PR head match verified implementation
    `227db721944dc0a470046fdec4b60f581ff28d38`. That match is not
    integration eligibility, merge authorization, credential
    onboarding, SIM access, or LIVE access. `DRY_RUN` remains the only
    authorized execution mode.
15. Operator acceptance of ADR-0007, architectural design only,
    recorded 2026-10-11. When item 17 is effective, every
    implementation-withholding sentence in this item is historical.
    That includes the statement that a later implementation sentence
    is not in effect. Those sentences do not prohibit the bounded
    implementation in item 17. The accepted artifact is the Proposed file at
    commit `38534bc4416adbaec37983e00e4736ece80acc25`, tree
    `00ef85ac23841d41d71716daea3045a5ea8d7bc9`, blob
    `25621163ca06d9532b7641fd6a58eb3d76fa1bbb`. Lane 4 authored that
    proposal. Lane 1 records the Operator's acceptance and does not
    author the design. The accepted classification is Option A only:
    `IntentRepositoryUnavailable("DATABASE_UNAVAILABLE")`. A later
    implementation, if separately authorized, may catch `psycopg.Error`
    and `sqlalchemy.exc.SQLAlchemyError` inside
    `PostgresIntentRepository.create_or_get` and raise that exception
    with `from None`. `from None` suppresses normal chaining and does
    not erase traceback frame locals or driver and pool DEBUG logs.
    `DryRunAdapter.dispatch` stays unchanged unless a separate
    shared-contract decision authorizes an edit.
    This acceptance does not authorize implementation, tests,
    migrations, TokenStore changes, Gmail changes, broker-adapter
    edits, a merge of PR #31 or PR #24, Supabase or other remote
    PostgreSQL provisioning, a database connection, credentials,
    TradeStation `SIM`, `LIVE`, or any economic action. `DEP-DB-001`
    and `DEP-DB-002` stay OPEN. Supabase Free stays preferred and
    **NOT_ACCEPTED**. ADR-0002, ADR-0003, and ADR-0006 stay Accepted.
    ADR-0004 and ADR-0005 stay Proposed. `DRY_RUN` remains the only
    authorized execution mode. The Accepted ADR text is a new blob and
    is not certified by the Proposed-tree verifier
    `bc-53ed5be3-37a2-5973-a69c-3807d96d37ec`. This item is on the
    coordinator draft, not on canonical `main`, until a separate
    integration authorization. Implementation permission still requires
    that integration and a later current-state sentence whose commit
    adds no application source. That sentence is not in effect.
16. Historical pre-correction record of the offline implementation
    authorization for Accepted ADR-0007 Option A. When item 17 is
    effective, this item neither authorizes nor prohibits the bounded
    implementation. The original contradictory text follows and is
    not operative: its conditional grant, its statement that it is
    not in effect, and its statement that Lane 4 must not start from
    the draft. Original text: prepared 2026-10-11 and not in effect. The Accepted ADR is on
    canonical main `557d9b1a7afe30e98cacb9ef1f6f47fe8a7922d0`, tree
    `7b8eddf2a6118d2c3c7a51610a5d53439f5ec899`, blob
    `c210976233f7bdba97cb12b5c7e1a1b599e2036d`. The fast-forward that
    placed item 15 on main did not authorize coding. The sentence in
    item 15 that calls the acceptance record a coordinator draft is
    the pre-integration record.
    Once an Operator-authorized fast-forward places this item on
    canonical main, and not before, Lane 4 may implement and test only
    the Option A boundary in `PostgresIntentRepository.create_or_get`
    inside `src/swingtrade/persistence.py`, plus new or existing
    persistence-focused tests. This commit adds no application source.
    The permitted behavior is: catch `psycopg.Error` and
    `sqlalchemy.exc.SQLAlchemyError` at that driver boundary; raise
    `IntentRepositoryUnavailable("DATABASE_UNAVAILABLE")` with
    `from None`; keep driver text, credentials, database URLs, and
    connection parameters out of the new exception's message, `args`,
    and `repr`. `from None` suppresses normal chaining. It does not
    erase `__context__`, traceback frame locals, or driver and pool
    DEBUG logs. Preserve `AuthorizationDenied`,
    `IntentIdentityConflict`, `NonCanonicalIntentKey`,
    `DurableObservationError`, `DurableRepositoryRequired`, the
    existing non-`DRY_RUN` guard, successful `OrderObservation`
    results, canonical identity, idempotency, compare-and-swap, and
    the `begin()` transaction boundary. Do not retry, replay,
    resubmit, or fall back to memory. An ambiguous transaction outcome
    stays unknown, not proof of rollback. Leave
    `DryRunAdapter.dispatch` and shared broker interfaces unchanged.
    Tests may use synthetic database URLs and injected SQLAlchemy or
    psycopg exceptions only. They must not open a real PostgreSQL
    connection, use a real credential, or contact a remote host.
    This sentence does not authorize TokenStore changes, Gmail
    changes, broker-adapter edits, schema migrations, Supabase or
    other remote provisioning, PR #24 integration, automatic merge of
    a later implementation pull request, TradeStation `SIM`, `LIVE`,
    order submission, or any economic action. `DEP-DB-001` and
    `DEP-DB-002` stay OPEN. Supabase Free stays preferred and
    **NOT_ACCEPTED**. ADR-0007 stays Accepted as Option A. ADR-0002,
    ADR-0003, and ADR-0006 stay Accepted. ADR-0004 and ADR-0005 stay
    Proposed. `DRY_RUN` remains the only authorized execution mode.
    Lane 4 must not start this work from the draft. A later
    integration gate is required before the sentence is effective,
    and a further integration gate is required before any resulting
    implementation commit may enter canonical `main`.
17. Operative ADR-0007 implementation authority. This item becomes
    effective only when both of these are true: an Operator decision
    has authorized integration of this independently verified
    correction candidate, and this exact commit is canonical `main`.
    No further activation step is required after that incorporation.
    While either condition is unmet, this item does not authorize
    coding. The prohibitions on the prior canonical commit stay
    there; they are not restated here as authority over this commit
    once this item is effective.
    When this item is effective, Lane 4 is authorized to implement
    only `IntentRepositoryUnavailable("DATABASE_UNAVAILABLE")`, a
    `RuntimeError`, inside `PostgresIntentRepository.create_or_get`
    in `src/swingtrade/persistence.py`, together with new or existing
    persistence-focused tests that use synthetic URLs and injected
    `psycopg` or SQLAlchemy failures. This commit adds no application
    source. The implementation may catch `psycopg.Error` and
    `sqlalchemy.exc.SQLAlchemyError` at that boundary and raise
    `IntentRepositoryUnavailable("DATABASE_UNAVAILABLE")` with
    `from None`. The new exception's message, `args`, and `repr`
    must not contain driver text, connection URLs, credentials, or
    connection parameters. `from None` suppresses normal chaining.
    It does not erase `__context__`, traceback frame locals, or
    driver and pool DEBUG logs. Preserve `AuthorizationDenied`,
    `IntentIdentityConflict`, `NonCanonicalIntentKey`,
    `DurableObservationError`, `DurableRepositoryRequired`, the
    existing non-`DRY_RUN` guard, successful `OrderObservation`
    results, canonical identity, idempotency, compare-and-swap, and
    the `begin()` transaction boundary. Do not retry, replay,
    resubmit, or fall back to memory. An ambiguous transaction
    outcome stays unknown, not proof of rollback. Leave
    `DryRunAdapter.dispatch` and shared broker interfaces unchanged.
    Do not redesign logging or make any other shared-contract change.
    When this item is effective, it does not authorize real
    PostgreSQL credentials, a real or remote database connection,
    Supabase provisioning or provider acceptance, schema migrations,
    TokenStore changes, broker changes, Gmail changes, `SIM`,
    `LIVE`, order submission, economic execution, integration of
    PR #24, or automatic integration of a later implementation
    pull request. `DEP-DB-001` and `DEP-DB-002` stay OPEN. Supabase
    Free stays preferred and **NOT_ACCEPTED**. ADR-0007 stays
    Accepted as Option A. `DRY_RUN` remains the only authorized
    execution mode. Lane 4 stays `READY_FOR_VERIFICATION`.
    Authorization to implement is not authorization to merge the
    implementation.
    Accepted ADR-0007 already requires one later explicit
    implementation sentence in this file on canonical `main` before
    code, and requires that sentence's commit to add no application
    source. This item is that sentence when it is effective. The ADR
    statements that acceptance itself does not authorize coding, and
    that Lane 4 must not change `create_or_get` until that sentence
    is on canonical `main`, are satisfied by this item. They are not
    a further prohibition after this item is effective. The ADR is
    unchanged.
    Once this item is effective, these are historical pre-correction
    records. They are not a second grant and they are not operative
    prohibitions of that bounded implementation: the 2026-10-11
    last-updated line on
    `7fe37e8e4b89a303856662b9a6333e64fe6df640` that said the
    authorization was not in effect; item 15's statement that the
    implementation sentence is not in effect; the whole of item 16,
    including its conditional grant and its statements that it is not
    in effect, that Lane 4 must not start from the draft, and that a
    later gate is required before that sentence is effective; and the
    workstream and journal sentences from that same commit. Those
    include the acceptance entry's sentence that no implementation
    sentence is in effect, the preparation entry's sentence that
    item 16 is ineffective until a fast-forward, and the instruction
    that Lane 4 must not code `create_or_get`. Those sentences
    document why implementation was blocked. Item 17 is the only
    operative implementation grant after it is effective.

18. Three non-economic `DRY_RUN` implementation grants, recorded
    2026-10-12. This item becomes effective only when all three of
    these are true: an independent verifier has passed this exact
    commit, an Operator decision has authorized integration of this
    exact commit, and this exact commit is canonical `main`. No
    further activation step is required after that incorporation.
    While any condition is unmet, this item does not authorize
    coding. When all three are met, the three grants below are
    operative. No second implementation-approval cycle applies to
    this same scope. Authorization to implement is not authorization
    to merge a later specialist pull request. Each specialist
    implementation still needs its own offline tests and a distinct
    independent exact-tree verification, and a separate Operator
    decision on that exact candidate, before Lane 1 may integrate it.
    No specialist may self-merge.
    This commit adds no application source. The parent main is
    `9f4cab32361c39d88c75eaf53866e0e60df3a680`, tree
    `07f2eb71988e28e32d48a7a9dd18904623d9081f`.
    When this item is effective, Lane 3 may add one pure view
    function over an existing `ParseOutcome` in a new module
    `src/swingtrade/group4_email/disposition.py`, with focused
    synthetic tests. The function reuses `Disposition`, `MessageType`,
    reason strings, `instruction_id`, `content_digest`, fixture
    `message_id`, and `ParseProvenance`. Its view labels are:
    `RECORDED_NOT_EXECUTABLE` for `ACCEPT` plus `NEW_TRADE` plus at
    least one instruction envelope; `DEFERRED` for `QUARANTINE` whose
    reason is `PARSER_DEFERRED` or `CANCEL_FORMAT_UNSPECIFIED`;
    `QUARANTINED` for every other `QUARANTINE`, including
    `CONFLICTING_DUPLICATE`; and `DUPLICATE` only as a replay view,
    not as a stored parser disposition. `REJECT` stays `REJECT`.
    `ACCEPT` plus `INFORMATIONAL` stays informational and carries no
    instruction envelope. An unrecognized disposition or message type
    fails closed. These labels do not replace `Disposition` and are
    not a new shared economic enum. The function must not read a
    mailbox, touch credentials, derive a quantity, construct an
    `OrderIntent`, call `authorize_dispatch` or
    `DryRunAdapter.dispatch`, mutate persistence, or use the network.
    When this item is effective, Lane 4 may add one synthetic receipt
    boundary in a new module `src/swingtrade/instruction_receipt.py`,
    with tests that use synthetic inputs and injected failures only.
    The receipt may store the identity key, raw-byte content digest,
    existing parser disposition, message type, reason codes,
    instruction identifiers, fixture message identifier, provider type
    `FIXTURE`, parser version, schema version, and the accepted
    non-secret provenance references already on `ParseProvenance`.
    The identity key is the validated fixture message identifier when
    present, and otherwise the raw-byte digest. The same key and the
    same digest return the original receipt unchanged. A conflicting
    digest returns a fail-closed conflict result and does not replace
    the stored receipt. Durable storage must not copy the in-memory
    `MessageIdentityRegistry` poison replacement. The receipt must not
    store a raw message, a normalized body, field-evidence text, order
    quantity, price, equity, session date, account identifier, token,
    or credential, and must not construct an `OrderIntent`. This grant
    does not authorize an Alembic migration, a real or local
    operational PostgreSQL connection, or a new shared public enum.
    If a migration or a new shared type is required, that portion
    stops and returns to Lane 1.
    When this item is effective, Lane 2 may add one pure classifier
    in a new module `src/swingtrade/group3_auth/order_report.py`, with
    synthetic tests. It maps in-memory fixture evidence to
    `ACKNOWLEDGMENT`, `PARTIAL_FILL`, `FILL`, `REJECTION`,
    `CANCELLATION`, or `UNKNOWN`. Those names are local outputs. They
    do not replace `OutcomeCode`. A report may retain a supplied
    synthetic `OrderID` and must not invent one or disclose an account
    identifier. Missing, conflicting, or unsupported evidence yields
    `UNKNOWN` or fails closed. `UNKNOWN` does not request a retry or a
    new submission. The classifier must not create an order request,
    promote an intent, open a socket, or use a credential. The
    certified file `src/swingtrade/group3_auth/brokerage_read.py`
    stays unchanged.
    Lane 3 owns the view function. Lane 4 consumes the existing
    `ParseOutcome` fields and does not invent a disposition enum.
    Lane 2's classifier is independent of Gmail processing. Lane 1
    coordinates any later shared-contract change and every material
    integration. Lane 3 and Lane 4 do not edit the same shared type.
    This item does not authorize an `OrderIntent` projection, quantity
    rounding or promotion, `DryRunAdapter.dispatch` changes, broker
    submission, Gmail or TradeStation access, OAuth, credentials, a
    real database connection, infrastructure provisioning, acceptance
    of ADR-0004 or ADR-0005, closure of any dependency, `SIM`, or
    `LIVE`. `DEP-CORE-001` and `DEP-CORE-002` stay `OPEN`. All nine
    dependencies stay `OPEN`. `DRY_RUN` remains the only authorized
    execution mode. Supabase Free stays preferred and
    **NOT_ACCEPTED**. ADR-0002, ADR-0003, ADR-0006, and ADR-0007 stay
    Accepted. ADR-0004 and ADR-0005 stay Proposed.
    Item 13 remains the credential-adapter grant. Item 17 remains the
    ADR-0007 persistence-exception grant. Their statements that those
    grants do not themselves authorize further Gmail, broker, or
    persistence work limit those earlier grants. The retained prior
    header's statement that item 17 is the sole operative Lane 4
    implementation authority for Accepted ADR-0007 limits that
    exception.
    Once item 18 is effective, four groups of standing sentences do
    not prohibit `src/swingtrade/group4_email/disposition.py`,
    `src/swingtrade/instruction_receipt.py`, or
    `src/swingtrade/group3_auth/order_report.py`. Group one is item
    17's sentence that item 17 is the only operative implementation
    grant after it is effective, and the retained header's sentence
    that item 17 is the sole operative Lane 4 implementation authority
    for Accepted ADR-0007. Group two is every current-state occurrence
    of the statement that the Operator authorizes the offline Group 2
    foundation only. Group three is the Evidence sentence that no
    Phase 2, broker, TradeStation `SIM`, credential, account, order,
    deployment, real-capital, or `LIVE` authority follows the Phase 1
    closure. Group four is the Lane 3 and Lane 4 rows in
    `docs/WORKSTREAM_STATUS.md` that say Lane 3 may implement only the
    offline credential adapter, that Lane 4 may implement only the
    bounded `create_or_get` change, and that Lane 4's next permitted
    action is: when item 17 is effective, implement only that boundary
    with synthetic URLs and injected failures. This commit does not
    edit those rows. Those four groups remain in force for every
    capability this
    item does not grant. No sentence in this item prohibits these
    three modules after the activation condition is met. Unrelated
    deny states, including credentials, network access, `SIM`, and
    `LIVE`, remain in force.

19. Three further non-economic `DRY_RUN` implementation grants,
    proposed 2026-10-12. This item becomes effective only when all
    three of these are true: an independent verifier has passed this
    exact commit, an Operator decision has authorized integration of
    this exact commit, and this exact commit is canonical `main`. No
    further activation step is required after that incorporation.
    While any condition is unmet, this item does not authorize
    coding. When all three are met, the three grants below are
    operative for their named paths only. Authorization to implement
    is not authorization to merge a later specialist pull request.
    Each specialist implementation still needs its own offline tests,
    a distinct independent exact-tree verification, and a separate
    Operator decision on that exact candidate before Lane 1 may
    integrate it. No specialist may self-merge. This item does not
    revise item 18. Item 18 remains the grant for
    `src/swingtrade/group4_email/disposition.py`,
    `src/swingtrade/instruction_receipt.py`, and
    `src/swingtrade/group3_auth/order_report.py`. This commit adds no
    application source. The parent main is
    `9703efa9d7842e22337c85f7b616bbe21f0c1e2b`, tree
    `eb23947a05988e8334bda555aa4840a90853543b`. Certified blobs that
    this item requires to stay unchanged are
    `src/swingtrade/group3_auth/order_report.py`
    `7ddf267e707d0c7aabe7106eebfc24d090ed6648`,
    `src/swingtrade/group4_email/disposition.py`
    `e6a089244300489374e21ef2b7188c16ac44966c`,
    `src/swingtrade/instruction_receipt.py`
    `537991932d216baa58b076b22acdcbef2f73595f`, and
    `src/swingtrade/group3_auth/brokerage_read.py`
    `ecbf5a0d06c6db3c839407df341ee407eac05dcf`.
    When this item is effective, Lane 2 may add one pure function,
    `evaluate_report_sequence(reports: object) -> SequenceEvidence`,
    in a new module
    `src/swingtrade/group3_auth/order_report_sequence.py`, with
    focused tests in
    `tests/group3_auth/test_order_report_sequence.py`. Lane 2 owns
    that function. `SequenceEvidence` is local. Its classifications
    are `CONSISTENT`, `DUPLICATE`, `OUT_OF_ORDER`, `CONFLICT`,
    `MISSING`, and `UNKNOWN`. They are synthetic evidence-quality
    labels. They are not `OutcomeCode`, not `ReportLabel`, and not
    execution, cancellation, retry, resubmission, or settlement
    states. No accepted contract defines a legal transition among
    acknowledgment, partial fill, fill, rejection, and cancellation.
    Different supported labels for one identity are `CONFLICT` with
    reason `INCONSISTENT_EVIDENCE`, not a lifecycle progression. A
    shared lifecycle contract is not decided here and stays
    `BLOCKED`.
    Each element may contain only `facts`, `order_id`, and optional
    `sequence`. `facts` and `order_id` use the existing classifier
    rules. The new function may call `classify_report` only with
    those two keys. It must not change `classify_report`,
    `ReportEvidence`, `ReportLabel`, `OutcomeCode`, or
    `AuthDecision`. `sequence` is local synthetic metadata, not a
    TradeStation wire field. When present it is an `int`, not a
    `bool`, and is greater than or equal to zero. Its absence is not
    zero and is not a fabricated number. Dictionary insertion order
    and object identity do not affect equivalence. Equivalence uses
    the validated `order_id`, the fact strings as a multiset, and
    the sequence value when that key is present on both elements.
    One present sequence and one absent sequence are not equivalent.
    If any element has `sequence` and another does not, the primary
    classification is `UNKNOWN` and the reasons include
    `PARTIAL_SEQUENCE`.
    The primary classification is the first match below. `reasons`
    retains every defect that was actually established, so a primary
    label does not drop another established identity conflict,
    inconsistency, duplicate, gap, or ordering defect. Malformed
    input stops evaluation: its reasons are only the malformation
    codes.
    1. `UNKNOWN` for a non-list, a non-dict element, a key outside
       the allowlist, a malformed identity, a malformed sequence, or
       partial sequence metadata.
    2. `CONFLICT` for differing validated order identifiers
       (`CONFLICTING_IDENTITY`), contradictory facts inside one
       element, unequal fact multisets for one identity
       (`INCONSISTENT_EVIDENCE`), or the same sequence number on
       unequal canonical bodies.
    3. `DUPLICATE` when at least two elements are exactly equivalent
       and no conflict was established.
    4. `OUT_OF_ORDER` when every element has a sequence and those
       numbers are not strictly increasing in caller order.
    5. `MISSING` for an empty list (`NO_REPORTS`), a missing order
       identifier, facts that are only insufficient or missing, or a
       sequence gap in an otherwise strictly increasing series.
    6. `CONSISTENT` only when the elements share one validated order
       identifier and one supported fact multiset, and their
       sequences are either all absent on a single element or
       strictly increasing without a gap or an exact duplicate.
    `safe_to_retry`, `resubmit_permitted`, `submit_permitted`,
    `cancel_permitted`, `network_permitted`, and `connect_allowed`
    stay false. The function does not mutate its input. Its `repr`
    omits order identifiers and report bodies. Tests must cover each
    label, the precedence above, equivalence despite dictionary
    order and object identity, a missing sequence versus zero,
    deterministic replay, immutability, and the absence of network,
    credential, and persistence imports.
    When this item is effective, Lane 3 may add
    `deliver_synthetic_fixtures` in a new module
    `src/swingtrade/group4_email/synthetic_acquisition.py`, with
    focused tests in
    `tests/group4_email/test_synthetic_acquisition.py`. Lane 3 owns
    that function. The frozen types `SyntheticFixture` and
    `SyntheticDelivery` live in that module. A fixture carries
    `delivery_ref: str` and `mime: bytes`. A delivery carries those
    two fields plus `content_digest: str`. The input is a tuple of
    `SyntheticFixture`. The function validates the whole tuple before
    returning. Failure raises one stable code and returns no partial
    delivery. The stable codes are `INVALID_FIXTURE`,
    `DUPLICATE_DELIVERY_REF`, and `INVALID_DELIVERY_REF`. The
    exception text is that code only. It does not include MIME bytes
    or the rejected reference.
    `delivery_ref` must match `^syn-delivery-[1-9][0-9]{0,5}$`. Any
    other reference, including a mailbox-shaped reference, is
    `INVALID_DELIVERY_REF`. Duplicate references in one tuple are
    `DUPLICATE_DELIVERY_REF`. A value that is not a
    `SyntheticFixture`, or whose `mime` is not `bytes`, is
    `INVALID_FIXTURE`. An empty tuple returns an empty tuple. A
    non-tuple fails closed. Caller order is preserved. MIME bytes are
    copied unchanged. `content_digest` is the accepted
    `content_digest` raw-byte SHA-256 function. `delivery_ref` is
    non-authoritative transport metadata. It is not a Message-ID, not
    a receipt key, and not a second identity authority. This function
    does not parse, rewrite, or sanitize MIME headers. Real mailbox
    identities inside preserved bytes remain subject to the existing
    parser, which this grant does not change. Tests may compose the
    existing parser, disposition view, and in-memory receipt. Those
    tests do not authorize a production orchestrator. The function
    must not modify the Group 4A parser, `ParseOutcome`, disposition,
    receipt identity, or retention policy, and it must not read
    Gmail, use OAuth or Credential Manager, open a socket, or write
    persistence.
    When this item is effective, Lane 4 may add one pure function,
    `evaluate_receipt_commit(events: object) -> CommitEvidence`, in a
    new module `src/swingtrade/receipt_commit.py`, with focused tests
    in `tests/unit/test_receipt_commit.py`. Lane 4 owns that
    function. This is the offline synthetic transaction-decision
    model for a future receipt commit. It is not a database adapter.
    Option B, a real PostgreSQL adapter, and disposable database
    certification remain separately gated. The function reads
    allowlisted synthetic events. It does not modify
    `InstructionReceipt`, `admit_instruction_receipt`,
    `PostgresIntentRepository`, `IntentRepositoryUnavailable`, or
    TokenStore. An event dict may contain only `event`,
    `receipt_key`, `content_digest`, and optional `detail`. `detail`
    is discarded and is never copied into the result or the
    exception. `event` is one of `insert_ok`, `commit_confirmed`,
    `insert_returning_empty`, `authoritative_read`, `lost_ack`,
    `missing_row`, `timeout`, `serialization_uncertain`, `read_only`,
    and `unavailable`. A non-list, an unknown key, an unknown event,
    or an empty list raises `ReceiptCommitRejected` with message
    `RECEIPT_COMMIT_INVALID` and no other text.
    The function folds events in caller order. The first digest
    recorded for a key is the first writer and is never replaced.
    `CommitEvidence.classification` is the first match below.
    `reasons` retains every recognized condition that was present so
    a primary label does not hide another established uncertainty or
    conflict. No success label is primary while a higher uncertainty
    is present. `INSERTED` and `COMMITTED` are not `ReceiptKind.NEW`.
    An unconfirmed commit is never reported as a successful new
    receipt.
    1. `UNAVAILABLE` when an `unavailable` event is present.
    2. `READ_ONLY` when a `read_only` event is present.
    3. `TIMEOUT` when a `timeout` event is present.
    4. `SERIALIZATION_UNCERTAIN` when a `serialization_uncertain`
       event is present.
    5. `CONFLICT` when one key is paired with two digests. The result
       keeps the first digest.
    6. `MISSING_ROW` when a `lost_ack` for a key is followed by
       `missing_row` for that key and no later `authoritative_read`
       of that key and its first digest.
    7. `AUTHORITATIVE_READ` when a `lost_ack` is followed by an
       `authoritative_read` of that key and its first digest. That
       read is not `INSERTED`, `COMMITTED`, or `REPLAY`.
    8. `LOST_ACK` when a `lost_ack` has no later `missing_row` and no
       later `authoritative_read` of that key and its first digest.
    9. `REPLAY` when the same key and its first digest are observed
       more than once by `insert_ok`, `commit_confirmed`, or
       `authoritative_read`, and no `lost_ack` applies.
    10. `AUTHORITATIVE_READ` when one `authoritative_read` is the
        establishing observation.
    11. `EMPTY_RETURNING` when `insert_returning_empty` is present and
        no confirmed row was established.
    12. `COMMITTED` when `commit_confirmed` is present for one key and
        its first digest and no earlier match applied.
    13. `INSERTED` when `insert_ok` is present and `commit_confirmed`
        is not.
    There is no automatic retry and no fallback into
    `InMemoryReceiptStore` after an ambiguous event. The function
    does not open a database connection, execute SQL, import a
    database driver, run Alembic, create a schema, or provision
    Supabase. Synthetic results are not evidence of PostgreSQL
    durability, isolation, or cross-process atomicity. Tests must
    cover each label, first-writer preservation, lost
    acknowledgment, missing row, sanitized `detail`, and the absence
    of a retry or a memory fallback.
    Lane 1 coordinates shared-contract conflicts and every material
    integration. No grant in this item authorizes a production
    function that chains acquisition, disposition, and receipt
    admission. The three grants do not add a shared identity
    authority, a shared disposition enum, a broker execution state,
    a parser-grammar change, a persistence-contract change, an
    `OrderIntent`, or a database authority.
    This item does not close `DEP-TS-001`, `DEP-TS-002`,
    `DEP-TS-003`, `DEP-TS-004`, `DEP-GMAIL-001`, `DEP-DB-001`,
    `DEP-DB-002`, `DEP-CORE-001`, or `DEP-CORE-002`. All nine stay
    `OPEN`. ADR-0002, ADR-0003, ADR-0006, and ADR-0007 stay Accepted.
    ADR-0004 and ADR-0005 stay Proposed. ADR-0005's Decision stays
    blank. Supabase Free stays preferred and **NOT_ACCEPTED**.
    `DRY_RUN` remains the only authorized execution mode. `SIM` and
    `LIVE` remain unauthorized. Credentials, OAuth, Gmail, native
    Credential Manager, TradeStation connectivity, operational
    PostgreSQL, migrations, quantity derivation, and orders remain
    unauthorized.
    Once this item is effective, the following standing sentences do
    not prohibit the three new paths named above. Item 18's statement
    that its four standing groups remain in force for every capability
    item 18 does not grant does not prohibit these three paths. Item
    17 remains the only ADR-0007 grant, and the sentence that item 17
    is the only operative implementation grant does not prohibit
    `src/swingtrade/receipt_commit.py`. The Lane 2 historical
    next-action sentence that tells Lane 2 to merge PR #22 is not an
    instruction to implement or to merge that PR again. The Lane 3
    status sentence that Lane 3 may implement only the offline
    credential adapter, and the Lane 4 status sentences that Lane 4
    may implement only the bounded `create_or_get` change, do not
    prohibit the three new paths. The current-state sentences that
    the Operator authorizes the offline Group 2 foundation only, and
    the Evidence sentence that no Phase 2 authority follows the Phase
    1 closure, do not prohibit these three paths. Those sentences
    remain in force for every capability this item does not grant.
    This item does not edit the Lane 3 or Lane 4 status rows.

20. One synthetic ingestion composition, proposed 2026-10-13.
    This item becomes effective only when all three of these are
    true: an independent verifier has passed this exact commit, an
    Operator decision has authorized integration of this exact
    commit, and this exact commit is canonical `main`. No further
    activation step is required after that incorporation. While any
    condition is unmet, this item does not authorize coding. When
    all three are met, Lane 3 may add one function,
    `record_synthetic_ingestion(fixtures: object, store: ReceiptStore, registry: MessageIdentityRegistry | None = None) -> tuple[SyntheticIngestionRecord, ...]`,
    in a new module
    `src/swingtrade/group4_email/synthetic_ingestion.py`, with
    focused tests in
    `tests/group4_email/test_synthetic_ingestion.py`. Lane 3 owns
    those two paths. No other new implementation path is granted.
    Authorization to implement is not authorization to merge the
    later implementation pull request. That pull request still needs
    its own offline tests, a distinct independent exact-tree
    verification by an agent other than the implementer, and a
    separate Operator decision on that exact candidate before Lane 1
    may integrate it by a history-preserving fast-forward. No
    specialist may self-merge. This item does not revise item 18 or
    item 19. This commit adds no application source. The parent main
    is `a1ce02e33b7cfaeaa9f96968e7ee940a4cb1a01e`, tree
    `f3bc56ca66bd972db84d9e670313a205b3eca117`.
    The function reuses, without modification,
    `deliver_synthetic_fixtures`, `parse_email`,
    `derive_disposition_view`, and `admit_instruction_receipt`.
    Blobs that stay unchanged are
    `src/swingtrade/group4_email/synthetic_acquisition.py`
    `6fd37978a839b5b4d5e4ce046d4feeba067764b6`,
    `src/swingtrade/group4_email/parse.py`
    `4119ffe03758380e0a284cc3514721201fac34c9`,
    `src/swingtrade/group4_email/disposition.py`
    `e6a089244300489374e21ef2b7188c16ac44966c`,
    `src/swingtrade/instruction_receipt.py`
    `537991932d216baa58b076b22acdcbef2f73595f`,
    `src/swingtrade/receipt_commit.py`
    `f8093ae3d6ac874b898a037b234692a7881e9473`, and
    `src/swingtrade/group3_auth/order_report_sequence.py`
    `e9169cb2704e9cfac4504be727c50a35e090bcf7`.
    `SyntheticIngestionRecord` is frozen and exposes exactly these
    nine fields: `delivery_ref: str`, `content_digest: str`,
    `parser_disposition: Disposition`,
    `parser_message_type: MessageType`,
    `parser_reasons: tuple[str, ...]`,
    `view_label: DispositionViewLabel`, `receipt_kind: ReceiptKind`,
    `receipt_key: str`, and `conflict_reason: str | None`. Those
    names are the accepted types from the existing modules.
    `content_digest` is the current `SyntheticDelivery` digest, even
    when a receipt conflict preserves an earlier stored digest. The
    record does not include MIME, an instruction envelope, a
    provenance object, an economic quantity, an `OrderIntent`, or an
    execution permission. Ordinary `repr` and `str` omit
    `receipt_key` and raw MIME. Public errors and any log line this
    function emits omit them as well. The function adds no
    general-purpose serializer and no raw-payload log.
    The order is fixed. First, accept `registry` only when it is
    `None` or its exact type is `MessageIdentityRegistry`. Any other
    value raises `SyntheticIngestionRejected("INGESTION_INVALID")`
    before acquisition and before any store call. Second, call
    `deliver_synthetic_fixtures` unchanged. Its
    `INVALID_FIXTURE`, `INVALID_DELIVERY_REF`, and
    `DUPLICATE_DELIVERY_REF` errors propagate as that adapter raises
    them. Third, create a new `MessageIdentityRegistry` for this
    call when none was supplied, and reuse the injected registry
    when one was supplied. Fourth, for each delivery in caller
    order, call `parse_email`, then `derive_disposition_view`, then
    `admit_instruction_receipt`, then build one frozen record.
    Return the tuple only when every delivery finishes. On a
    downstream exception, stop immediately, do not process later
    items, do not retry, do not roll back earlier receipt
    admissions, and do not return a partial or complete result
    tuple. Propagate the accepted public exception. Do not add raw
    MIME, a delivery reference, or the store's private text to that
    surface. This item does not claim that Python's implicit
    exception context is erased.
    Parser disposition is taken from the current `ParseOutcome`.
    The view label is taken from the current `DispositionView`.
    Receipt kind and `conflict_reason` are taken from the current
    `ReceiptDecision`. The current parser result is not replaced by
    a previously stored receipt disposition. A conflicting message
    does not replace the original stored receipt. `QUARANTINED`,
    `CONFLICT`, and `REPLAY` stay distinct. Receipt `NEW` is not
    evidence of parser acceptance or of trading authorization.
    `delivery_ref` stays transport metadata. Receipt identity stays
    the existing rule: the fixture Message-ID when that id is
    present, and the accepted raw-content digest when it is absent.
    A shared in-memory store can distinguish `NEW`, `REPLAY`, and
    `CONFLICT`. A new process-local store may admit previously
    observed MIME as `NEW`. No durable restart guarantee is
    established. The parser registry may already have recorded the
    current item before that item's receipt-store call fails. The
    function does not roll back that registry mutation and does not
    describe the registry and the store as one transaction. The
    receipt store is not batch-atomic.
    The function does not call `evaluate_receipt_commit` or
    `evaluate_report_sequence`. An `INSERTED` or `COMMITTED` label
    from that separate model is not evidence of PostgreSQL
    durability. This grant does not add an HTTP endpoint, a
    scheduler, a queue, a Gmail adapter, a persistence
    implementation, or a production orchestration framework.
    Focused tests must cover: a valid `NEW_TRADE` with the three
    statuses kept distinct; identical MIME under another
    `delivery_ref`; the same Message-ID with a changed digest;
    deferred amendment, exit, and cancellation; a quarantined
    non-fixture Message-ID; malformed MIME with parser `REJECT` and
    the accepted receipt result; an empty batch; a wrong fixture
    input type; an invalid `delivery_ref` on a later member; a
    duplicate `delivery_ref`; a second-item store failure that keeps
    the first receipt and does not touch a third item; frozen
    records, unchanged caller input, and `repr` privacy; reversed
    caller order; a fresh in-memory store after a simulated restart;
    the absence of forbidden imports, provider connectivity, and
    executable economic output; rejection of an invalid registry
    type before acquisition or store use; registry advancement when
    receipt admission fails, without rollback; current parser
    evidence kept separate from first-writer receipt evidence; no
    completed result tuple when a later item fails; and a sanitized
    public exception surface that does not claim Python's internal
    exception context was erased.
    Lane 2 outcome A, recorded with this proposal, is that existing
    offline broker-report evidence is sufficient and that no new
    Lane 2 component is authorized. Lane 3 handoff
    `LANE3_ITEM20_COMPOSITION_CONTRACT_READY` and Lane 4 handoff
    `LANE4_ITEM20_RECEIPT_CONTRACT_READY` say the certified
    interfaces accept this call sequence without modifying
    `ReceiptStore` or `InstructionReceipt`. Those handoffs are
    contract-readiness records. They are not independent
    verification of an implementation. Lane 2 handoff
    `LANE2_PHASE3_BROKER_EVIDENCE_SCOPE_READY` is the same kind of
    record.
    Item 19's statement that item 19 itself authorizes no function
    chaining acquisition, disposition, and receipt admission does
    not prohibit the two paths named in this item once this item is
    effective. Until then, that statement remains in force. The
    Lane 3 status sentence that Lane 3 may implement only the
    offline credential adapter does not prohibit these two paths
    once this item is effective. This item does not edit the Lane 3
    or Lane 4 status tables. It does not close `DEP-TS-001`,
    `DEP-TS-002`, `DEP-TS-003`, `DEP-TS-004`, `DEP-GMAIL-001`,
    `DEP-DB-001`, `DEP-DB-002`, `DEP-CORE-001`, or `DEP-CORE-002`.
    All nine stay `OPEN`. ADR-0002, ADR-0003, ADR-0006, and
    ADR-0007 stay Accepted. ADR-0004 and ADR-0005 stay Proposed.
    ADR-0005's Decision stays blank. Supabase Free stays preferred
    and **NOT_ACCEPTED**. `DRY_RUN` remains the only authorized
    execution mode. `SIM` and `LIVE` remain unauthorized.
    Credentials, OAuth, Gmail, native Credential Manager,
    TradeStation connectivity, operational PostgreSQL, migrations,
    quantity derivation, and orders remain unauthorized.

21. Local Windows Gmail OAuth connectivity governance, proposed
    2026-10-14. This item becomes effective only when all three of
    these are true: an independent verifier has passed this exact
    commit, an Operator decision has authorized integration of this
    exact commit, and this exact commit is canonical `main`. No
    further activation step is required after that incorporation.
    While any condition is unmet, this item does not authorize
    coding. When all three are met, the only new authority is Gate B
    below: Lane 3 may add one offline module,
    `src/swingtrade/group4_email/local_oauth_probe.py`, and focused
    tests in `tests/group4_email/test_local_oauth_probe.py`. Lane 3
    owns those two paths. No other new implementation path is
    granted. Authorization to implement is not authorization to merge
    the later implementation pull request. That pull request still
    needs its own offline tests, a distinct independent exact-tree
    verification by an agent other than the implementer, and a
    separate Operator decision on that exact candidate before Lane 1
    may integrate it by a history-preserving fast-forward. No
    specialist may self-merge. This commit adds no application
    source. The parent main is
    `1614cbb7060b31bacc59f1687a0c68d91474ed67`, tree
    `725bc9e78a0d530c6c91163cffda8a83fae57a82`.
    The adopted planning record is
    `LANE3_GMAIL_LOCAL_OAUTH_CONNECTIVITY_GATE_READY` together with
    `LANE3_GMAIL_LOCAL_OAUTH_DISCOVERY_ADOPTED`. Those records are
    contract readiness for this governance text. They are not an
    implementation PASS and they are not a live connectivity PASS.
    This item separates four gates. Gate A is this governance text.
    Gate B is the offline module and tests named above, followed by
    independent exact-tree verification and a separate Operator
    integration decision. Gate C is a later explicit Operator
    decision that identifies the local Windows runtime, the Desktop
    OAuth client type, the single scope, the one Gmail API
    operation, one attended execution, the approved redacted evidence
    fields, and the prohibition on persistent token storage and on
    any further API request. Gate D is a later assessment of
    sanitized evidence from that one execution. Gate A does not
    approve Gate B's merge. Gate B does not approve Gate C. Gate C
    does not close a dependency by itself.
    The future runtime is the Operator's local Windows computer.
    Cursor cloud agents are not the OAuth callback host, token
    custodian, or mailbox reader. The OAuth client type is a Google
    Desktop application. The flow is Authorization Code with PKCE
    S256. The callback is an ephemeral listener bound to `127.0.0.1`
    on a port assigned by the operating system. The redirect URI is
    exactly `http://127.0.0.1:{port}/` for that bound port. The
    module rejects `localhost`, `::1`, `0.0.0.0`, any non-loopback
    host, a public listener, a cloud callback, and the deprecated
    out-of-band flow. Required protections are a cryptographic
    random `state`, a cryptographic random per-request PKCE verifier
    of 43 to 128 unreserved characters, an S256 challenge, state
    validation before any code exchange, exact redirect validation,
    and a callback timeout of at most 120 seconds. Missing,
    duplicate, mismatched, and malformed callback parameters are
    rejected before token exchange. `code_challenge_method=plain` is
    rejected. RFC 7636 appendix B remains the deterministic S256
    vector: verifier
    `dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk` and challenge
    `E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM`.
    The only permitted scope is
    `https://www.googleapis.com/auth/gmail.metadata`. The only
    permitted Gmail API request is `GET
    https://gmail.googleapis.com/gmail/v1/users/me/profile` with an
    empty body. The authorization endpoint is only
    `https://accounts.google.com/o/oauth2/v2/auth`. The token
    endpoint is only `https://oauth2.googleapis.com/token`. No other
    host or path is permitted. The authorization request uses
    `response_type=code`, that exact scope, S256, and `state`. It
    omits `access_type`, an offline-access prompt, and any parameter
    that widens scope. The token form sends `grant_type`, `code`,
    `code_verifier`, `client_id`, and `redirect_uri`. It omits
    `client_secret`, `refresh_token`, and `access_type`. A granted
    scope other than that exact metadata scope is rejected,
    including `gmail.readonly`, `gmail.labels`, `gmail.modify`, and
    any additional scope. No message, thread, attachment, label, or
    history API request is permitted. Mailbox listing and message
    content reads are outside this item.
    A successful profile response is HTTP 200 and a JSON object that
    contains `emailAddress` as a string, `messagesTotal` as an
    integer, `threadsTotal` as an integer, and `historyId` as a
    string. Boolean values are not integers. The module checks that
    shape and then discards the values. The returned evidence is a
    frozen `LocalOAuthProbeEvidence` with exactly these fields:
    `callback_result: str`, `scope_result: str`,
    `token_exchange_result: str`, `profile_result: str`, and
    `content_retained: bool`. `content_retained` is false. Ordinary
    `repr` and `str` of the evidence, errors, and logs omit the
    profile values, the authorization code, the PKCE verifier, the
    access token, any refresh token, the callback query, and
    `Authorization` headers. `profile_result` on that success path
    is `GMAIL_OAUTH_PROFILE_SHAPE_PASS`. That code is an offline
    shape result. It is not `GMAIL_CONNECTIVITY_PASS`. Failures
    raise `LocalOAuthProbeRejected` with one of these codes and do
    not return a success evidence object: `GMAIL_OAUTH_STATE_REJECTED`,
    `GMAIL_OAUTH_PKCE_REJECTED`, `GMAIL_OAUTH_CALLBACK_REJECTED`,
    `GMAIL_OAUTH_REDIRECT_REJECTED`, `GMAIL_OAUTH_SCOPE_REJECTED`,
    `GMAIL_OAUTH_TOKEN_REJECTED`, `GMAIL_OAUTH_PROFILE_REJECTED`,
    `GMAIL_OAUTH_ENDPOINT_REJECTED`, and
    `GMAIL_OAUTH_LIVE_UNAUTHORIZED`. Public `repr` is the code.
    The module imports no network implementation. It does not open a
    socket, launch a browser, or read the environment on import or
    during test discovery. HTTP, the loopback listener, the clock,
    and the browser launcher are injected by the caller.
    `orchestrate_profile_probe` performs the sequence only through
    those injected objects and enforces the endpoint and scope
    allowlists before each call. `run_attended_profile_probe` takes
    no arguments and raises
    `LocalOAuthProbeRejected("GMAIL_OAUTH_LIVE_UNAUTHORIZED")`
    before binding a socket, opening a browser, exchanging a code,
    or calling Gmail. No environment variable, command flag, file,
    or test fixture disables that refusal. Gate B therefore ships no
    live transport. A network-capable tree remains inert toward the
    real provider. Gate C, even after a later Operator decision,
    still requires a separate explicit change before any live call.
    This item does not define that change.
    For the first attended proof, Desktop client JSON stays on the
    Operator's Windows system, outside the repository and outside
    Cursor cloud. Gate B tests use fixture client identifiers only.
    They do not read a downloaded client file. Authorization codes,
    PKCE verifiers, access tokens, and refresh tokens are not
    printed or persisted. Offline access and persistent
    refresh-token issuance are not requested. If a token response
    contains `refresh_token`, the module drops that field before
    logging or returning and does not send a refresh grant. Access
    material used inside `orchestrate_profile_probe` stays in
    process memory and is discarded before the function returns.
    Provider response content is not persisted. The Operator
    revocation instruction for any later attended execution is to
    remove the app at `https://myaccount.google.com/permissions` and
    delete the local client JSON. This module does not call a token
    revoke endpoint. Provider credentials are never copied into Git,
    pull-request text, Cursor chats, screenshots, or verification
    artifacts. Desktop client JSON is not uploaded to an independent
    verifier. An OAuth library whose defaults persist tokens, widen
    scope, or open a network connection on import is not adopted
    under this item. That incompatibility requires a design change
    and a separate review.
    Gate B does not implement native Windows Credential Manager and
    does not modify the synthetic credential adapter. These blobs
    stay unchanged:
    `src/swingtrade/gmail_credential/__init__.py`
    `0e8eed5244e6966740f5b0d9af877f8193a6f2b1`,
    `src/swingtrade/gmail_credential/adapter.py`
    `984b7781d88f28b4fd2888ba3f8a9e12475448c0`,
    `src/swingtrade/gmail_credential/errors.py`
    `32a446eb059635bcd2f44db34f6ac1385ef4df85`,
    `src/swingtrade/gmail_credential/identity.py`
    `30c7dd8056e195dc98d02dfc1057662c170f0811`,
    `src/swingtrade/gmail_credential/mock_port.py`
    `9a76189be5cdc7cb9e4652e276f58ec86abfcd74`,
    `src/swingtrade/gmail_credential/secret.py`
    `0acc491ee29e1133f73e451636da9d9747726230`,
    `src/swingtrade/group4_email/__init__.py`
    `44d73a8b92f05fbf941eb6c6b1383e52a2913104`,
    `src/swingtrade/group4_email/synthetic_acquisition.py`
    `6fd37978a839b5b4d5e4ce046d4feeba067764b6`,
    `src/swingtrade/group4_email/parse.py`
    `4119ffe03758380e0a284cc3514721201fac34c9`, and
    `src/swingtrade/group4_email/synthetic_ingestion.py`
    `73165d7ccaecc94dd930943f820436af3940168b`.
    The new module is not imported by `group4_email/__init__.py`.
    It does not call `record_synthetic_ingestion`, `parse_email`,
    `deliver_synthetic_fixtures`, `admit_instruction_receipt`,
    `evaluate_receipt_commit`, or `evaluate_report_sequence`. It
    constructs no `OrderIntent`. It adds no HTTP service, scheduler,
    queue, webhook, or refresh worker. It does not connect Item 20
    to a provider.
    Focused tests must cover: no network on import; the forbidden
    imports and the absence of a live client; the hard
    `GMAIL_OAUTH_LIVE_UNAUTHORIZED` refusal with zero socket and
    browser calls; the RFC 7636 S256 vector and rejection of
    `plain`; absence of verifier and state from ordinary `repr`;
    state mismatch before token exchange; missing, duplicate, and
    malformed callback parameters; a non-loopback redirect; callback
    timeout before token exchange; a wrong or extra scope, including
    `gmail.readonly`; a non-allowlisted token or profile endpoint;
    a profile fixture whose four fields validate and then disappear
    from the evidence object; a non-200 profile response whose body
    is absent from the error; a `refresh_token` field that is absent
    from evidence and logs; an authorization request without
    `access_type=offline`; and no import of Item 20, the parser, the
    receipt modules, or the credential adapter. Tests use fixtures
    only.
    The historical Lane 3 status row that prohibits Gate B remains
    the 2026-10-09 corpus-connection attestation. This item does not
    rewrite that row and does not start that corpus Gate B. The
    sentence in `docs/GMAIL_READONLY_CORPUS_GATE.md` that names
    Cursor environment secrets is historical research. The
    clarification added beside it keeps that sentence and states the
    present custody rule: provider tokens are not placed in Cursor
    Cloud environment secrets. Current state prevails over that
    historical setup list. ADR-0004 is not edited. Its Decision
    stays blank. Its `gmail.readonly` corpus option is a separate
    later decision. A metadata profile probe does not satisfy it.
    This item does not revise items 18, 19, or 20. It does not close
    `DEP-TS-001`, `DEP-TS-002`, `DEP-TS-003`, `DEP-TS-004`,
    `DEP-GMAIL-001`, `DEP-DB-001`, `DEP-DB-002`, `DEP-CORE-001`, or
    `DEP-CORE-002`. All nine stay `OPEN`. `DEP-GMAIL-001` remains
    the corpus-setup question under Proposed ADR-0004. ADR-0002,
    ADR-0003, ADR-0006, and ADR-0007 stay Accepted. ADR-0004 and
    ADR-0005 stay Proposed. ADR-0005's Decision stays blank.
    Supabase Free stays preferred and **NOT_ACCEPTED**. `DRY_RUN`
    remains the only authorized execution mode. `SIM` and `LIVE`
    remain unauthorized. Credentials, live OAuth, Gmail API
    execution, native Credential Manager, TradeStation connectivity,
    operational PostgreSQL, migrations, and orders remain
    unauthorized.

22. Parser security-scan scope for the authorized OAuth module,
    proposed 2026-10-16. This item becomes effective only when all
    three of these are true: an independent verifier has passed this
    exact commit, an Operator decision has authorized integration of
    this exact commit, and this exact commit is canonical `main`.
    While any condition is unmet, this item does not authorize the
    test edit or any other coding. When all three are met, Lane 1
    may change only `tests/group4_email/test_attacks.py`. Lane 1
    owns that one future edit. No other path is granted.
    Authorization to make that edit is not authorization to merge
    PR #48 or any later implementation candidate. This commit adds
    no application source and no test change. The parent main is
    `b313e581eca7fa2265aa10b53f15dc31d7e408be`, tree
    `356511fa933f953dd1f255946fd951be5158d1fa`.
    The planning record is
    `LANE1_ITEM21_SECURITY_TEST_REMEDIATION_SCOPE_READY`. It is not
    an implementation PASS and it does not convert the historical
    verifier result below into a PASS. Items 18, 19, 20, and 21 stay
    effective. Item 21's Gate A, Gate B, Gate C, and Gate D stay as
    item 21 states them. This item does not revise those gates and
    does not authorize Gate C.
    The only permitted behavioral change, after this item is
    effective, is inside
    `test_parser_does_not_use_network_broker_or_credentials`. When
    that test builds the concatenated Group 4A package source for
    its forbidden-substring scan, it excludes exactly the top-level
    file named `local_oauth_probe.py`. The scan continues to read
    top-level `src/swingtrade/group4_email/*.py` and then drops only
    that filename. Every other top-level `.py` file remains in the
    scan, including files added later. The existing forbidden-pattern
    list stays unchanged and still applies to every file that remains
    in the scan. The socket-blocked `parse_email` assertion stays.
    The test must not switch to a shorter fixed file list, exclude
    another filename or directory, or change any other security test.
    This exclusion is only that parser-source assertion. It is not a
    general exemption for the OAuth module.
    This item does not authorize a change to
    `src/swingtrade/group4_email/local_oauth_probe.py`,
    `tests/group4_email/test_local_oauth_probe.py`, any other Group
    4A source file, synthetic acquisition, synthetic ingestion, the
    existing parser, the synthetic credential adapter,
    `group4_email/__init__.py`, broker or economic contracts, runtime
    settings, database schema, ADRs, or dependency state. It does not
    authorize Google Cloud setup, OAuth consent, token exchange, a
    Gmail API call, credential handling, mailbox access, Windows
    Credential Manager access, PostgreSQL, TradeStation, an
    `OrderIntent`, or a broker operation. It does not authorize
    integration of PR #48.
    The eventual test correction must show all of the following
    before any integration decision. `local_oauth_probe.py` is absent
    from only that substring scan. Every other current top-level
    Group 4A Python file remains in the scan. A future top-level
    Group 4A Python file would enter the scan automatically. The
    prohibited substring list is unchanged. A forbidden substring
    deliberately placed in a protected parser file still fails the
    test. A forbidden substring deliberately placed in another
    protected Group 4A file still fails the test. Those injections
    happen only in a disposable worktree and are discarded, not
    committed. The OAuth module's own security tests stay active.
    `run_attended_profile_probe` still raises
    `GMAIL_OAUTH_LIVE_UNAUTHORIZED` with no alternate live entry
    point. `GMAIL_OAUTH_PROFILE_SHAPE_PASS` stays an offline shape
    result and is not a real connectivity pass. The full repository
    tests, Ruff, Mypy, the Phase 1 validator, and `git diff --check`
    pass as applicable. A green result of the previously failing
    test is not sufficient by itself.
    PR #48, https://github.com/agentAD25/swing-trading-automation/pull/48,
    branch `cursor/gmail-local-oauth-probe-9f45`, is unchanged by
    this commit. Its recorded head is
    `4911617684fc1dba726f8a383d4c3c9298a9cae1`, tree
    `768b6144fa4c7233a171d0d717eaebf78753d764`, parent
    `b313e581eca7fa2265aa10b53f15dc31d7e408be`. Independent verifier
    `bc-3cbfb445-befb-536c-8492-580e49eeb182` returned
    `INDEPENDENT_EXACT_TREE_FAIL` for that tree. That result remains
    a FAIL. Lane 1 does not edit that specialist branch. After this
    item is effective, the history-preserving sequence is an ordinary
    merge, not a rebase, squash, cherry-pick, amend, or force-push.
    First confirm that the PR #48 head is still the recorded SHA, and
    stop if it has moved. Then merge that exact head into the
    effective main with a normal merge commit that keeps both
    parents. On that merge result, add one commit whose only changed
    path is `tests/group4_email/test_attacks.py` and whose only
    behavioral change is the exclusion named here. An independent
    verifier who authored neither this governance commit nor that
    test commit must pass that exact final SHA and tree. PR #48 stays
    open until a separate Operator decision authorizes integration of
    that verified tip. The tip must still contain the PR #48 commits
    as ancestors. If the specialist head has moved, this sentence
    does not authorize merging the old SHA.
    This item does not close `DEP-TS-001`, `DEP-TS-002`,
    `DEP-TS-003`, `DEP-TS-004`, `DEP-GMAIL-001`, `DEP-DB-001`,
    `DEP-DB-002`, `DEP-CORE-001`, or `DEP-CORE-002`. All nine stay
    `OPEN`. ADR-0002, ADR-0003, ADR-0006, and ADR-0007 stay Accepted.
    ADR-0004 and ADR-0005 stay Proposed. ADR-0005's Decision stays
    blank. Supabase Free stays preferred and **NOT_ACCEPTED**.
    `DRY_RUN` remains the only authorized execution mode. `SIM` and
    `LIVE` remain unauthorized.

23. Local Windows Gmail Gate C one-shot connectivity, proposed
    2026-10-16. This item becomes effective only when all three of
    these are true: an independent verifier has passed this exact
    commit, an Operator decision has authorized integration of this
    exact commit, and this exact commit is canonical `main`. While
    any condition is unmet, this item does not authorize coding, a
    provider call, or Google Cloud provisioning. When all three are
    met, the only new authority is Decision A below. Decision A is
    not Decision B and is not Decision C. This commit adds no
    application source and no test change. The parent main is
    `fcafaded6dc06d56af256afe244e604b150fcf81`, tree
    `9653ad4535346d30bfe5a4f07a2d07e77bb6687a`. Items 18, 19, 20,
    21, and 22 stay effective and are not revised. Their sentences
    that describe PR #48 as open are the record of those earlier
    commits. Gate B is already canonical at the parent above. This
    item does not reopen it and does not treat that integration as
    Gate C.

    Item 21 remains the Gate A and Gate B contract. Gate B's
    certified source blob `777db628ebe0f55aa529b26c9ad5692799121090`
    and certified test blob
    `86d99b6269d1c14238c5b240b7998428a206d59f` stay unchanged. The
    Item 22 security-test blob
    `14b911ba29f16161f179c272c2e2f5e1be50922e` stays unchanged.
    Independent verifier `bc-10b13d65-4063-5611-a775-a133d7579cf9`
    returned `INDEPENDENT_EXACT_TREE_PASS` for the parent tree. That
    PASS certifies the offline probe and the parser-scan correction.
    It is not a real connectivity PASS. The earlier verifier
    `bc-3cbfb445-befb-536c-8492-580e49eeb182` remains
    `INDEPENDENT_EXACT_TREE_FAIL` for tree
    `768b6144fa4c7233a171d0d717eaebf78753d764`. This item does not
    relabel that FAIL.

    The reusable Gate B surface is `orchestrate_profile_probe`
    together with its PKCE S256, state, loopback, callback,
    token-form, scope, and profile-shape helpers. Those helpers
    already reject a non-metadata scope, a second conceptual profile
    target, an offline-access parameter, and a retained profile
    body. `DesktopClientConfig.network_permitted` must stay `False`;
    `validate_desktop_client` rejects any other value with
    `GMAIL_OAUTH_LIVE_UNAUTHORIZED`. `run_attended_profile_probe`
    takes no arguments and raises that same code before any socket,
    browser, token exchange, or Gmail call. No environment variable,
    flag, file, or fixture disables it. The module imports no
    socket, HTTP client, or browser launcher. Import and test
    discovery do not connect. The orchestrator will call whatever
    transport a caller injects, and this tree injects none.

    The missing capability is one attended local mechanism that
    constructs the real transports. It is not compatible with
    editing `local_oauth_probe.py`. Adding a live client there would
    change the certified Gate B contract, would give the refusal a
    live path, and would put provider literals in a package whose
    parser scan excludes only `local_oauth_probe.py`. A second file
    inside `src/swingtrade/group4_email/` would be scanned for
    `gmail`, `oauth`, and `import socket`. This item therefore does
    not authorize that edit and does not authorize another exclusion
    from `test_attacks.py`.

    Decision A, and only after this item is effective, permits Lane
    3 to add exactly two paths:
    `src/swingtrade/gmail_local_connect.py` and
    `tests/unit/test_gmail_local_connect.py`. Lane 3 owns those
    paths. No other path is granted. The module lives outside
    `group4_email` so the existing parser scan stays intact. It must
    call the existing orchestrator and builders rather than
    reimplement PKCE, state comparison, redirect matching, scope
    checks, or profile-shape checks. It must pass
    `network_permitted=False` into the existing client validator. It
    must not change that validator, the refusal, the two certified
    OAuth blobs, or the security-test blob. It must not modify
    parser, acquisition, ingestion, receipt, credential-adapter,
    broker, economic, database, ADR, dependency, or configuration
    files. It adds no third-party OAuth or Gmail library and no
    dependency entry.

    The new module imports no socket, HTTP client, or browser
    launcher at import time. Those imports occur only inside
    `run_local_windows_profile_proof`. That function is reached only
    from `if __name__ == "__main__"`, through `python -m
    swingtrade.gmail_local_connect` and one explicit local path
    argument to the Desktop client JSON. The path is not an
    environment variable, not a repository file, and not a Cursor
    Cloud secret. Import, pytest collection, a generic application
    start, and any environment variable do not call it. Its first
    action on a non-Windows platform is to raise
    `GMAIL_OAUTH_LIVE_UNAUTHORIZED` before a socket, a browser, a
    file read of client JSON, a token request, or a Gmail request.
    Missing, unreadable, non-Desktop, or secret-bearing
    configuration fails closed before those effects. `client_secret`
    is never sent, logged, or retained. The token form stays the
    existing five-field form.

    On the authorized Windows command, the mechanism binds
    `127.0.0.1` to an operating-system-assigned port, opens the
    Operator's system browser, and waits at most 120 seconds. It
    uses the existing cryptographic state and PKCE verifier. The
    authorization endpoint, token endpoint, metadata scope, and one
    empty-body profile GET stay exactly the Item 21 values. Each
    HTTP call times out at most 30 seconds. The profile GET may
    occur once. A second Gmail request, or any other Gmail path,
    raises `GMAIL_OAUTH_ENDPOINT_REJECTED` and sends nothing
    further. An unexpected `refresh_token` is discarded and is not
    stored. The loopback socket closes on success, failure, timeout,
    and cancellation. No background thread, scheduler, poller, or
    refresh worker remains. No database and no Windows Credential
    Manager are used.

    `orchestrate_profile_probe` continues to return
    `GMAIL_OAUTH_PROFILE_SHAPE_PASS` for a shape-valid profile. That
    code remains an offline or in-process shape result. It is not
    real connectivity. Only the Windows `__main__` path, after the
    real transports have completed that shape result, may print
    `GMAIL_GATE_C_REAL_CONNECTIVITY_PASS`. A local failure prints
    `GMAIL_GATE_C_REAL_CONNECTIVITY_BLOCKED` or an existing
    rejection code. Public output omits the account address, mailbox
    counts, history ID, raw body, authorization code, verifier,
    access token, refresh token, client JSON, and `Authorization`
    header. Offline tests must not print the real-connectivity code.

    Decision A requires the new tests to stay offline and to use
    synthetic client identifiers and mocked transports. They cover
    PKCE S256, fresh state and verifier, loopback URI construction,
    callback state mismatch, duplicate or missing callback
    parameters, timeout, OAuth error, redirect mismatch, token
    rejection, malformed token response, insufficient and excessive
    scope, discarded refresh token, the exact profile method and
    endpoint, an empty profile body, prohibition of a second Gmail
    request and of other Gmail endpoints, no provider call on
    import, no background network, fail-closed local configuration,
    absence of credential and token values from logs, errors, and
    results, listener cleanup, profile-shape validation, no retained
    profile values, cancellation, no Google contact, no Item 20 or
    receipt coupling, no TradeStation or PostgreSQL import, no
    broker or economic operation, and preservation of the existing
    refusal and parser scan. An AST check shows the live call sits
    under `__name__ == "__main__"` and that the non-Windows refusal
    precedes any socket use. The tests do not call
    `run_local_windows_profile_proof`. A green offline run is not
    `GMAIL_GATE_C_REAL_CONNECTIVITY_PASS`.

    Decision B is a later Operator integration decision. Lane 3
    publishes one draft pull request containing only the two paths.
    An independent verifier other than the implementer must return
    `INDEPENDENT_EXACT_TREE_PASS` for that exact SHA and tree,
    including the offline tests, Ruff, Mypy, the Phase 1 validator,
    and `git diff --check`. Lane 1 may then fast-forward that exact
    candidate only after a separate Operator decision names it. No
    self-merge, rebase, squash, cherry-pick, amend, or force-push.
    Decision B does not authorize executing the module.

    Decision C remains Item 21 Gate C and stays unauthorized by this
    item and by Decision B. It is a later Operator decision naming
    the canonical implementation SHA, the Operator's local Windows
    computer, one attended execution of `python -m
    swingtrade.gmail_local_connect`, the metadata scope, the single
    profile GET, the redacted evidence fields, and immediate discard
    of tokens and profile content. One approval authorizes one
    execution. An inconclusive or failed result does not authorize a
    retry. Cursor cloud agents must not run the command, hold the
    client JSON, or receive tokens, authorization codes, or profile
    bodies. Google Cloud project setup, the Desktop client, and
    revocation at `https://myaccount.google.com/permissions` are
    Operator-local steps under Decision C, not steps under Decision
    A. Gate D stays a later assessment of sanitized evidence and is
    not opened here.

    This item does not close `DEP-TS-001`, `DEP-TS-002`,
    `DEP-TS-003`, `DEP-TS-004`, `DEP-GMAIL-001`, `DEP-DB-001`,
    `DEP-DB-002`, `DEP-CORE-001`, or `DEP-CORE-002`. All nine stay
    `OPEN`. A metadata profile proof does not satisfy Proposed
    ADR-0004. ADR-0002, ADR-0003, ADR-0006, and ADR-0007 stay
    Accepted. ADR-0004 and ADR-0005 stay Proposed. ADR-0005's
    Decision stays blank. Supabase Free stays preferred and
    **NOT_ACCEPTED**. `DRY_RUN` remains the only authorized trading
    execution mode. `SIM` and `LIVE` remain unauthorized. Lane 4
    local PostgreSQL work stays independent. This item authorizes no
    database connection and no Gmail token table.

24. Alpaca Paper execution direction, proposed 2026-10-16. This item
    becomes effective only when all three of these are true: an
    independent verifier has passed this exact commit, an Operator
    decision has authorized integration of this exact commit, and
    this exact commit is canonical `main`. While any condition is
    unmet, this item does not authorize coding or a provider call.
    When all three are met, the only new authority is Decision A
    below. Decision A is not a later integration decision and is not
    paper connectivity. This commit adds no application source and
    no test change. The parent main is
    `71ba48283af88fca9e553cca993c5b9c27a1d08e`, tree
    `9d4e6f974a97c694987033d4bcd82c87b71222f1`. Items 18, 19, 20,
    21, 22, and 23 stay effective and are not revised. Item 23
    Decision A remains Lane 3's two Gmail paths and is not
    redirected here.

    The Operator preference recorded here is that Alpaca Paper is
    the preferred initial execution destination for automated U.S.
    stock swing trades. The preference is architecture direction. It
    is not executable authority. It does not request, store, or use
    an API key. It does not select a paper account, place an order,
    or replace TradeStation. ADR-0005 stays Proposed with a blank
    Decision. `DEP-TS-001`, `DEP-TS-002`, `DEP-TS-003`, and
    `DEP-TS-004` stay `OPEN`. Existing TradeStation modules,
    fixtures, tests, ADRs, branches, and verifier history stay
    byte-unchanged by this commit and by Decision A. TradeStation
    remains operationally disabled: its named SIM host still cannot
    connect, and `SIM` and `LIVE` stay unauthorized.

    Official Alpaca Trading API facts used for this direction,
    accessed 2026-10-16, are these. Paper trading calls
    `paper-api.alpaca.markets`. Live trading calls
    `api.alpaca.markets`. Market data calls `data.alpaca.markets`. A
    paper key cannot be used on the live host, and a live key cannot
    be used on the paper host. Trading API authentication is the key
    id and secret in `APCA-API-KEY-ID` and `APCA-API-SECRET-KEY`, or
    HTTP Basic with those values. `GET /v2/account` is the account
    read. `POST /v2/orders` creates an order. `client_order_id` is
    optional, at most 128 characters, unique for the client, and
    generated by Alpaca when omitted. The same id can later retrieve
    the order. Alpaca rejects a duplicate `client_order_id`. Order
    status values include `new`, `partially_filled`, `filled`,
    `canceled`, `expired`, `rejected`, `pending_new`, and
    `pending_cancel`. `filled_qty` and `filled_avg_price` are order
    fields. Equity order classes include `simple`, `oco`, `oto`, and
    `bracket`. Paper trading is a simulation: it does not route to a
    live exchange, does not model market impact, queue position,
    latency slippage, or dividends, and may partially fill a
    marketable order for a random size. Sources:
    https://docs.alpaca.markets/us/docs/paper-trading ,
    https://docs.alpaca.markets/us/docs/authentication ,
    https://docs.alpaca.markets/us/docs/account-plans ,
    https://docs.alpaca.markets/us/reference/postorder ,
    https://docs.alpaca.markets/us/reference/getorderbyclientorderid
    , and https://docs.alpaca.markets/us/docs/alpacas-cli .

    Decision A, only after this item is effective, permits Lane 2 to
    add exactly `src/swingtrade/alpaca_paper.py` and
    `tests/unit/test_alpaca_paper.py`. Lane 2 owns those paths. No
    other path is granted. The module is additive. It does not edit
    `src/swingtrade/group3_auth/`,
    `src/swingtrade/offline/hosts.py`, `src/swingtrade/broker.py`,
    `src/swingtrade/domain.py`, Group 4 email, the Gmail connector,
    ADRs, or the dependency registry. It imports no socket, HTTP
    client, or Alpaca SDK. Import and pytest discovery open no
    network socket and read no environment variable. It does not
    construct an `OrderIntent`, derive a quantity, choose an order
    class, or apply a risk limit. Those decisions remain unmade.

    The offline module may parse synthetic fixtures only. A fixture
    order carries `client_order_id`, status, `qty` or `filled_qty`
    as strings, and no account identifier. `client_order_id` longer
    than 128 characters is rejected. A second fixture with the same
    id is a local duplicate and is not a second submission. A
    fixture marked submission-unknown must be classified
    reconcile-before-resubmit and must not emit a second id. A
    `partially_filled` fixture preserves filled and remaining
    quantity as decimals and does not invent a fill. The strings
    `paper-api.alpaca.markets` and `api.alpaca.markets` may appear
    only as denied hosts. `connect_allowed` stays false. No function
    in the module accepts a key, a secret, or a base-URL override
    that enables a call. `DRY_RUN` remains the only authorized
    trading mode.

    A later Operator decision is required before Lane 1 integrates
    an independently verified implementation of those two paths.
    That integration still does not authorize credentials or network
    access. A further, separate Operator decision is required before
    any paper-only read of `GET /v2/account`, and another before any
    paper order. This item does not ask the Operator to create or
    paste an Alpaca key. Lane 4 may later design a durable
    order-attempt record that distinguishes not-sent,
    outcome-unknown, and acknowledged, keyed by the local
    idempotency key and one `client_order_id`. This item does not
    add that schema, connect PostgreSQL, or close `DEP-DB-001` or
    `DEP-DB-002`. `DEP-CORE-001` and `DEP-CORE-002` stay `OPEN`
    because quantity rounding, timezone, and calendar remain
    unresolved. `DEP-GMAIL-001` stays `OPEN`.

    This item does not close `DEP-TS-001`, `DEP-TS-002`,
    `DEP-TS-003`, `DEP-TS-004`, `DEP-GMAIL-001`, `DEP-DB-001`,
    `DEP-DB-002`, `DEP-CORE-001`, or `DEP-CORE-002`. All nine stay
    `OPEN`. ADR-0002, ADR-0003, ADR-0006, and ADR-0007 stay
    Accepted. ADR-0004 and ADR-0005 stay Proposed. ADR-0005's
    Decision stays blank. Supabase Free stays preferred and
    **NOT_ACCEPTED**. `DRY_RUN` remains the only authorized trading
    execution mode. `SIM` and `LIVE` remain unauthorized. No Alpaca,
    TradeStation, Gmail, PostgreSQL, `OrderIntent`, or broker
    operation is performed by this commit.

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

On 2026-10-06 the Operator supplied written TradeStation Client Experience
answers. They are recorded in `docs/P2_TS_PROVIDER_EVIDENCE.md` and
reconciled in `docs/P2_PRE_CREDENTIAL_DECISION.md`, with dated addenda on
the broker, authentication, and question documents. ADR-0005 is Proposed
and its Decision is blank. The provider did not select an application
type. A SIM-only key is not available, so LIVE denial cannot depend on
one. Default personal-use refresh tokens are non-rotating and long-lived;
that does not close the published 30-versus-40-minute rotating-token
conflict. The Native PKCE callback form is open, so no API client is
created. No TradeStation authentication, token, SIM call, LIVE call,
order, Gmail change, or Supabase connection follows. Gmail draft PR #21
is not modified. Draft PR #19 is not updated.

On 2026-10-08 the Operator presented the same written clarification for
Lane 2 intake. `docs/P2_TS_PROVIDER_EVIDENCE_2026-10-08.md` records
confirmed, partial, and unresolved claims without replacing the
2026-10-06 quotations. ADR-0005 proposes a Regular Web confidential
client and remains Proposed with a blank Decision. The issued key's
type is not verified. Local DRY_RUN code denies LIVE and SIM
connection, elevated scopes, profile B, and HTTP 429 retries. No
credential was onboarded. No TradeStation call was made. Canonical
`main` at the start of this intake was
`af0d69b1dfc2046899db05a2f12767fc20b623ae`. PR #22 is not merged.
Independent verification of implementation commit
`19154eae43990df1d83a78be7b6dac3710a28804`, tree
`de97145c7278afbfe432463733a02b5e8a74ced9`, passed the local DRY_RUN
suites named in `docs/ENGINEERING_JOURNAL.md`. That pass is not
TradeStation connectivity.
