# ADR-0009: Standing specialist development authority

- Status: Accepted
- Date: 2026-11-14
- Sole Phase 1 decider: Human Operator
- Scope: Development administration for Lanes 2, 3, and 4, and the shape of later standing provider grants
- Supersedes: None
- Superseded by: None

## Context

Canonical `main` at authoring is `afc6b76ec679b269e89e5478c5a8bf938a0dad2e`, tree `acc32eec762c1789254bbfa2c1515b32413cff29`. Parents are `09aa937464b5e35bd97ae0001c649dde2da2447d` and `3066d25f9eaa9d9430faa2e0955e05c3a0186019`. This proposal does not embed its own hash.

The Operator directed one governance restructuring on 2026-11-14. Ordinary specialist engineering is currently gated as if each edit were a new financial authorization. That practice is recorded in the per-item sentences of `docs/CURRENT_STATE.md`, the per-item paragraphs of `docs/WORKSTREAM_STATUS.md`, and the repeated exact-tree reconciliations of open specialist branches. The direction authorizes this proposal. It does not activate a provider call, a credential read, a database modification, or an order.

Accepted safety text remains in force while this status is Proposed. `docs/AGENT_AUTHORITY.md` makes credentials, broker or account or network activity, TradeStation `SIM`, order submission, real capital, and `LIVE` unauthorized while `docs/CURRENT_STATE.md` denies them. Changing this file cannot grant a denied capability. `.cursor/rules/10-trading-safety.mdc` keeps `DRY_RUN` as the only authorized execution mode. `.cursor/rules/80-workstream-coordination.mdc` keeps Lane 1 as the only proposer of canonical integration and forbids specialist self-certification.

### Audit classification

Each row is a current requirement. Nothing in this table is discarded by publication of this proposal.

| Requirement | Where recorded | Class |
| --- | --- | --- |
| `DRY_RUN` only; no `LIVE`, live host, or real capital | `docs/AGENT_AUTHORITY.md`; `.cursor/rules/10-trading-safety.mdc`; ADR-0008 | 1. Retained |
| No credential in Git, logs, argv, or chat; no live Alpaca target | ADR-0008 Decision; `docs/AGENT_AUTHORITY.md` | 1. Retained |
| Seven Gate C2 execution flags stay false | ADR-0008; current-state Gate D record | 1. Retained until a separate paper-order grant names any change |
| Alembic target guard: `127.0.0.1`, port `5433`, database `swingtrade_receipt_test`, role `swingtrade_migrator`, system identifier `7707684291752896980`; fail closed | Item 39, effective on `e52ad5e6e40e228ffba20199707a6c39d7fd4f5e` | 1. Retained |
| No port `5432`, no `localhost` alias, no development database `swingtrade`, no bootstrap superuser | Item 39 guard | 1. Retained |
| Gmail has no send, modify, delete, or `client_secret` authority | ADR-0004; ADR-0006; Item 38 | 1. Retained |
| Campaign `GMAIL-METADATA-CAMPAIGN-0D571DEC` stays stopped; attempt 1 consumed; attempts 2 and 3 unused | Item 36 and Item 38 records | 1. Retained |
| Stage E is not `PASS`; Stage F is not authorized; Item 30 source paths stay closed | Current-state Item 37 reconciliation | 1. Retained |
| `DEP-CORE-001` and `DEP-CORE-002` block economic acceptance | `docs/WORKSTREAM_DEPENDENCIES.md` | 1. Retained |
| Lane 1 proposes integration; specialists do not self-certify or self-integrate | `docs/INTEGRATION_PROTOCOL.md`; `.cursor/rules/80-workstream-coordination.mdc` | 2. Retained at integration |
| Exact non-forced fast-forward; no force-push, rebase, squash, or cherry-pick of certified history | `docs/INTEGRATION_PROTOCOL.md` | 2. Retained at integration |
| Independent verifier distinct from the implementer for a material candidate | `docs/INTEGRATION_PROTOCOL.md` step 8 | 2. Retained for milestone and security-sensitive candidates |
| Shared-file conflict returns `CROSS_WORKSTREAM_CONTRACT_CONFLICT` | `docs/WORKSTREAM_OWNERSHIP.md` | 2. Retained |
| Separate worktrees; preserve PR #19 and historical specialist branches | `docs/WORKSTREAM_OWNERSHIP.md` | 2. Retained |
| One new current-state item and one fresh verification before each ordinary source edit | Repeated Item 20–40 practice | 3. Consolidate into a work package after this ADR is effective |
| A governance pull request after each failed authorized provider attempt | Item 31, Item 36, and Item 38 campaign practice | 3. Consolidate only inside a later standing provider budget |
| Reconcile every open specialist branch after every canonical commit | 2026-11-13 queue practice | 3. Consolidate to the next integration candidate |
| A second record whose only job is to declare an earlier record effective | Steps 18 and 19 practice after an already authorized fast-forward | 3. Consolidate: one integration record per milestone is sufficient |
| Per-file grants that are already effective | Items 32, 35, 38, 39, and the Gate D probe grant, among others | 4. Preserve; do not revoke |
| Pending exact-file proposals on open PR #66 and PR #88 | Those pull requests | 4. Preserve as Operator choices; prospective packages do not close them |
| Draft PR #80 and PR #90, which no longer contain current `main` | Those pull requests | 4. Preserve until designated; do not reconcile them for this proposal |

Class 1 is financial or security-critical. Class 2 is contract-critical at an integration boundary. Class 3 is development administration. Class 4 is historical or duplicated and stays readable.

## Safety impact

Publication leaves execution mode, credentials, accounts, capital, and network authority unchanged. `DRY_RUN` remains the only authorized trading mode. No secret is added. The Alembic guard is unchanged. The stopped Gmail campaign is unchanged. Stage E remains not `PASS`. A future acceptance of Option A would authorize offline work inside the packages below. It would still leave every provider, credential, migration, and order action unauthorized until a separate current-state activation meets the non-overridable rule in `docs/AGENT_AUTHORITY.md`.

## Options considered

### Option A — Standing packages, with provider grants defined and inactive

Adopt the profiles, package rules, and verification cadence in "Option A text" below. Layer D is offline development authority. Layer P is a set of standing provider and database grants that this option defines and leaves inactive. Acceptance of this ADR, once independently verified, Operator-authorized, and canonical, makes Layer D effective. Layer P stays inactive until a later Operator decision names one grant.

### Option B — Continue per-step grants

Keep the current item-by-item authorization practice. This option is the operative system while this ADR remains Proposed. It preserves every existing control and continues the coordination overhead the Operator directed Lane 1 to reduce.

## Decision

The Operator selected Option A on 2026-11-14 by decision `LANE1_ADR0009_OPTION_A_ACCEPTANCE_PREPARATION_AUTHORIZED`. Option B is not selected.

The selected text is the Layer D and Layer P text in this record. Layer D becomes effective only when an independent verifier has returned `INDEPENDENT_EXACT_TREE_PASS` for the commit that contains this Decision and the current-state acceptance record, an Operator decision has authorized integration of that same commit, and that commit is canonical `main`. The pass of proposal `010acfa2ddd3aecc3889d8aae885a5717132323b` does not certify that commit. Until those three conditions are met, existing item grants remain the only implementation authority.

Layer P stays inactive. This Decision authorizes no provider call, credential read, migration, paper order, or `LIVE` route. Class 1 and class 2 controls stay in force. `DRY_RUN` remains the only authorized trading mode. Open PR #66, PR #80, PR #88, and PR #90 are not closed or rewritten. This Decision does not embed the acceptance commit hash.

## Option A text

This text governs Layer D only after the acceptance commit that contains the Decision meets the three conditions in the Decision. Until then, existing item grants remain the implementation authority. Layer P stays inactive.

### Layer D — offline development packages

Layer D becomes effective only when all three are true: an independent verifier has returned `INDEPENDENT_EXACT_TREE_PASS` for the commit that sets this ADR to Accepted and records that acceptance in `docs/CURRENT_STATE.md`; an Operator decision has authorized integration of that commit; and that commit is canonical `main`. Until then, existing item grants remain the only implementation authority.

After Layer D is effective, a specialist may continue implementation, debugging, and non-destructive local tests across multiple commits inside the one open package for that lane. Ordinary commits do not need a new Lane 1 authorization, a new item number, or an independent verifier. The specialist keeps the existing branch and pull request. Evidence of ordinary commits lives in the pull request and the test output. The specialist does not edit `docs/CURRENT_STATE.md`, `docs/ENGINEERING_JOURNAL.md`, `docs/WORKSTREAM_STATUS.md`, `docs/WORKSTREAM_DEPENDENCIES.md`, `docs/INTEGRATION_PROTOCOL.md`, `docs/WORKSTREAM_OWNERSHIP.md`, `docs/adr/`, `pyproject.toml`, `.github/`, or `.cursor/rules/` for ordinary package work.

Lane 1 reviews a package at three points: a cross-lane contract conflict, a security-sensitive change presented for integration, and the completed milestone candidate. Lane 1 does not require a progress review of an in-package commit.

#### Lane 2 package

Owned paths:

- `src/swingtrade/alpaca_paper.py`
- `src/swingtrade/alpaca_paper_boundary.py`
- `src/swingtrade/alpaca_paper_custody.py`
- `src/swingtrade/alpaca_paper_account_probe.py`
- `src/swingtrade/alpaca_paper_account_read.py`
- `tests/unit/test_alpaca_paper.py`
- `tests/unit/test_alpaca_paper_boundary.py`
- `tests/unit/test_alpaca_paper_custody.py`
- `tests/unit/test_alpaca_paper_account_probe.py`
- `tests/unit/test_alpaca_paper_account_read.py`

The account-read pair may be created under Layer D. Committed code keeps all seven Gate C2 flags false: `connect_allowed`, `network_permitted`, `submit_permitted`, `cancel_permitted`, `replace_permitted`, `resubmit_permitted`, and `safe_to_retry`. Any function that would read a credential or perform HTTP stays uncalled by import and uncalled by the offline tests. Tests use synthetic bytes and a mocked transport. The module stays free of the Item 25 scan tokens `requests.`, `httpx.`, `socket.`, `tradestation`, `place_order`, and `cancel_order`. Credential targets remain the two ADR-0008 paper targets. Every `swing-trading/lane2/alpaca/live/` target stays rejected. No dependency is added.

#### Lane 3 package

Owned paths:

- `src/swingtrade/gmail_local_connect.py`
- `src/swingtrade/group4_email/`
- `tests/unit/test_gmail_local_connect.py`
- `tests/group4_email/`

Item 32's two files, `src/swingtrade/group4_email/gmail_readonly_pilot.py` and `tests/group4_email/test_gmail_readonly_pilot.py`, stay inside this package. The mocked pilot uses an injected transport, scope `https://www.googleapis.com/auth/gmail.readonly`, a maximum of 10 messages, local selectors, `durable_state = UNAVAILABLE`, and `economic_dispatch = false`. It has no send, modify, delete, broker, or live-read behavior.

One security-sensitive edit is inside the package: `test_parser_does_not_use_network_broker_or_credentials` in `tests/group4_email/test_attacks.py` may exclude `gmail_readonly_pilot.py` in addition to the existing exclusion of `local_oauth_probe.py`, and `tests/unit/test_gmail_local_connect.py` may update only its pinned blob of `tests/group4_email/test_attacks.py` to the new blob. Every other assertion, forbidden token, and monkeypatch stays. A disposable check must show that a forbidden token in a non-excluded parser file still fails. That edit is security-sensitive under the verification cadence below. The Item 25 exclusion list is unchanged. `client_secret` stays absent. Campaign `GMAIL-METADATA-CAMPAIGN-0D571DEC` stays stopped.

#### Lane 4 package

Owned paths already granted by effective Item 39:

- `alembic.ini`
- `migrations/env.py`
- `tests/unit/test_alembic_target_guard.py`

Maintenance must keep the fail-closed target. The committed URL stays `postgresql+psycopg://invalid.invalid:1/refused`. Allowed revisions stay `0001_offline_foundation`, `0002_canonical_order_intents`, and `0003_durable_dry_run_observation`. Revision `0004` stays refused. Item 30's three paths stay closed until Stage E and Stage F are `PASS` and a separate decision opens them. Layer D includes offline tests that do not connect. It does not include a migration, a connection, a role change, or a cluster change.

#### Prohibited for every package

A package does not authorize a credential read, a provider call, a paper or live order, a port `5432` connection, a remote database, a paid service, a new runtime dependency, an edit to a shared economic contract, or a change to another lane's files. Security-critical behavior is bounded by these prohibitions. A filename allowlist does not permit a prohibited action inside an allowed file.

#### Verification cadence

An ordinary package commit is verified by the specialist's relevant local tests. An independent verifier is required before integration for the milestone candidate and for any security-sensitive commit. A change is security-sensitive when it touches credential custody, a network client, an execution-mode flag, an order path, the migration target guard, a scanner exclusion, a scope or host allowlist, a shared economic contract, or a dependency manifest. The verifier is not the implementer and returns a result for the exact commit and tree. One passing verification of that commit is enough. A pass of an ancestor does not certify a descendant.

Integration into canonical `main` remains a Lane 1 proposal. The preferred mechanism remains one non-forced fast-forward after an Operator decision names that exact commit. One current-state and journal record of that integration is sufficient. A further record whose only content is that the first record is effective is not required.

### Layer P — standing grants, defined and inactive

Each grant below is inactive. Effectiveness requires Layer D to be effective, a later Operator decision that names the grant, a current-state record of that decision, and every conjunctive gate in `docs/AGENT_AUTHORITY.md`. A failure inside an active budget does not create a new governance item. Crossing the budget, the allowlist, the account binding, or the expiry stops the grant until a new Operator decision.

#### Lane 2 read-only paper connectivity

Later decision name: `LANE1_ALPACA_STANDING_PAPER_ACCOUNT_READ_AUTHORIZED`.

When activated, the grant permits repeated `GET` requests to `https://paper-api.alpaca.markets/v2/account` only, using the two ADR-0008 paper credential targets, on an Operator-attended Windows-local runtime. The proposed budget is 30 requests per America/New_York calendar day. Redirects are refused. A retry must use the same method and host. Logs contain a reason code and omit the key, the secret, and the raw account body. The seven Gate C2 flags stay false. Positions, orders, and streaming are outside this grant. A paper key is treated as capable of simulated account changes, so this grant still does not submit an order.

#### Lane 2 paper-order lifecycle

Later decision name: `LANE1_ALPACA_STANDING_PAPER_ORDER_AUTHORIZED`.

This grant is separate from the account-read grant. It cannot be activated until `DEP-CORE-001` and `DEP-CORE-002` are resolved with evidence or explicitly waived by the Operator, and until the activation names every one of: the paper account binding, allowed symbols, allowed order types, maximum notional per order, maximum quantity, maximum open orders, maximum orders per America/New_York day, the session duration, and the revocation condition. This proposal selects none of those values. No live host and no real-capital action is included. Any change to a Gate C2 flag must be named in that same decision. Expiry or revocation returns every execution flag to false.

#### Lane 3 read-only Gmail connectivity

Later decision name: `LANE1_GMAIL_STANDING_READONLY_CONNECTION_AUTHORIZED`.

When activated, the grant permits token refresh, profile checks, and read-only message acquisition for the single mailbox named in the activation. This proposal does not name a mailbox. The only scope is `https://www.googleapis.com/auth/gmail.readonly`. The custody target remains the ADR-0006 identifier `swing-trading/lane3/gmail/dev/refresh-token`. The proposed budget is 20 token-endpoint attempts and 50 read-only GETs per America/New_York calendar day, with at most 10 messages per list call. Send, modify, delete, and `client_secret` stay prohibited. The grant does not resume campaign `GMAIL-METADATA-CAMPAIGN-0D571DEC`. The activation must name a new campaign identifier. `durable_state` stays `UNAVAILABLE` and `economic_dispatch` stays false until a later persistence integration. The grant contains no brokerage authority.

#### Lane 4 isolated local PostgreSQL

Later decision name: `LANE1_POSTGRES_STANDING_RECEIPT_CLUSTER_AUTHORIZED`.

Activation requires a recorded Stage E `PASS` for the existing receipt-test identity: host `127.0.0.1`, port `5433`, database `swingtrade_receipt_test`, role `swingtrade_migrator`, and system identifier `7707684291752896980`. Stage E is not `PASS` at authoring, so this grant cannot be activated by accepting this ADR. When activated, routine migrations and tests may repeat against that cluster for revisions `0001` through `0003` without a new Lane 1 approval. The same-connection identity check stays mandatory. Port `5432`, the `localhost` alias, database `swingtrade`, a bootstrap superuser, a remote host, a paid service, and revision `0004` stay refused. Recovery is limited to restoring that same cluster from a dump taken from that cluster. Item 30's source paths open only after Stage E and Stage F are `PASS` and a separate decision names them.

### Milestone completion

A lane reaches its completion milestone when its package evidence is one commit, independently verified, containing the tests and security attestations for that package. The completion criteria are:

- Lane 2: offline account-read and offline order-lifecycle code are tested with mocks; a standing account-read grant, if separately active, has one attested paper account read; a paper-order grant remains a later decision.
- Lane 3: the mocked read-only pilot and the single scanner exclusion are tested; a standing Gmail grant, if separately active, has one attested read-only acquisition. The stopped campaign stays stopped.
- Lane 4: the target guard remains fail-closed; Stage E is `PASS` before any standing cluster use; execution-ledger paths stay closed until their own gate is `PASS`.

Lane 1 performs one integration review of each completed milestone. End-to-end integration of the three milestones waits until each has that review.

## Consequences

Acceptance records Option A and amends no cursor rule. Layer D is not effective until the acceptance commit is independently verified, integration-authorized, and canonical `main`. Layer P stays inactive. Existing effective grants continue. Open PR #66 at `de742e59b171bf85b5a31f61148b186347c641ed` and open PR #88 at `8e84f0511cffe310c76b8aeaa2b2a7c067fe9145` remain fast-forward candidates of current `main` and remain Operator choices. This proposal does not integrate or close them. After Layer D is effective, the scanner edit described for Lane 3 and the offline account-read files described for Lane 2 may proceed inside those packages, so those two pull requests do not need to be integrated first. Their text stays historical and is not revoked.

PR #80 and PR #90 do not contain current `main`. They stay open and are not reconciled by this proposal.

Acceptance would consolidate class 3 administration. It would not weaken class 1 or class 2. A later accepted edit may align `docs/INTEGRATION_PROTOCOL.md` step 8 and step 16 with the milestone cadence. That alignment is not part of this proposal.

## Validation and rollback

Acceptance evidence is an Operator decision selecting Option A, a status change to Accepted, a filled Decision, and a current-state record, all in one commit that then follows the existing exact-commit integration gate. Rollback of this proposal is to leave the status Proposed and the Decision blank. Rollback after acceptance is a new Operator decision that revokes Layer D and any active Layer P grant, recorded in current state, without rewriting this file's history.

Failure signals are a provider call, a credential read, a migration, an order, a Gate C2 flag set true, a scanner exclusion beyond `gmail_readonly_pilot.py`, or a claim that Layer P is effective, made under this proposal alone.

## Unresolved questions

The Operator selected Option A. Layer D is not effective until the acceptance commit is canonical. The paper-order numeric limits are unset on purpose. The Gmail mailbox and the new campaign identifier are unset on purpose. Stage E has no `PASS` record. Native Windows credential-store behavior is not certified here. The proposed daily budgets are proposals the activation decision may replace.

## Evidence

- Repository reference: canonical `main` `afc6b76ec679b269e89e5478c5a8bf938a0dad2e`, tree `acc32eec762c1789254bbfa2c1515b32413cff29`, inspected 2026-11-14. Supported claim: this is the authoring baseline. Limitation: this proposal is not that commit.
- Repository reference: `docs/AGENT_AUTHORITY.md` and `.cursor/rules/10-trading-safety.mdc` on that baseline. Supported claim: denied capabilities stay denied, and `DRY_RUN` is the only authorized execution mode. Limitation: this proposal does not edit those files.
- Repository reference: ADR-0008 on that baseline, status Accepted. Supported claim: Option A names two paper credential targets, rejects live targets, and does not authorize a credential read or a provider call. Limitation: this proposal does not change ADR-0008.
- Repository reference: current-state Item 39 effectiveness for `e52ad5e6e40e228ffba20199707a6c39d7fd4f5e`. Supported claim: the target guard is effective and a migration is not authorized. Limitation: Stage E is not `PASS`.
- Repository reference: open pull requests inspected 2026-11-14. PR #66 head `de742e59b171bf85b5a31f61148b186347c641ed` and PR #88 head `8e84f0511cffe310c76b8aeaa2b2a7c067fe9145` contain current `main`. PR #80 head `49a38a0802eae2464ba4d48a79c8d4bc8d303510` and PR #90 head `e3ea2af594582003f4cd218d34a913a0ff2100ac` do not. Limitation: this proposal does not merge any of them.
