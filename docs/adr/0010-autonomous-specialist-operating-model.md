# ADR-0010: Autonomous specialist operating model

- Status: Proposed
- Date: 2026-11-14
- Sole Phase 1 decider: Human Operator
- Scope: Standing development authority for Lanes 2, 3, and 4, and the shape of later standing isolated-test grants
- Supersedes: None
- Superseded by: None

## Context

Canonical `main` at authoring is `6d50b3eb292d78fd6396fc6f0d35023d24b3290e`, tree `89f648d862f8831d78ba2b9de565934d4a8a7112`. ADR-0009 is Accepted and its prospective Layer D boundary is the current development rule. The Operator directed one operating-model change on 2026-11-14 by `OPERATOR_AUTONOMOUS_LANES_2_3_4_RESTRUCTURING_PREPARATION_AUTHORIZED`. That direction authorizes this candidate. It does not authorize integration, a provider call, a credential read, a migration, or an order.

Pull request #92, branch `cursor/alpaca-paper-account-read`, head `cb19c0d965f623aa8292cc0c1826f6ee7787c677`, is the open offline account-read candidate. Pull request #94, branch `cursor/lane3-gmail-offline-package-8992`, head `70ef653ddd0fe550e76f51f063d6f6e509bbfc6b`, is the open mocked Gmail pilot. Pull request #80 and pull request #90 stay open. This candidate does not merge or rewrite them. Pull request #91 and pull request #93 are not reopened.

## Safety impact

`DRY_RUN` stays the only authorized trading mode. This candidate puts no secret in Git. It does not open a live host, a paper-order path, port `5432`, or a Gmail write scope. A denied capability stays unauthorized until the specific standing-access decision in this record is actually issued. Preparation does not issue those decisions.

## Options considered

### Option A — Standing packages and delegated isolated-test grants

Adopt the development packages, delegation rule, and inactive standing-access definitions below. One later Operator decision can accept this option and authorize integration of the commit that contains it. Development authority then becomes effective without a second governance commit. Standing provider and database access stay inactive until their own decisions.

### Option B — Keep ADR-0009 per-package micro-grants

Leave the current Layer D file lists and per-commit integration cycle unchanged. This option is the operative system while this ADR remains only a candidate.

## Decision

The Decision stays blank while the status is Proposed. The Operator has not selected Option A or Option B.

## Acceptance and effectiveness

Option A becomes the operating rule only when all three are true for the commit that contains this section:

1. An independent verifier, distinct from the author, returns `INDEPENDENT_EXACT_TREE_PASS` for that commit and tree.
2. The Operator issues `OPERATOR_AUTONOMOUS_LANES_2_3_4_EXACT_INTEGRATION_AUTHORIZED` for that same commit. That decision selects Option A and authorizes one non-forced fast-forward. It does not by itself issue a standing-access decision.
3. That commit is integrated by that fast-forward and remains an ancestor of canonical `main` until a later Operator decision revokes or supersedes it.

While the header still says Proposed, specialists treat Option A as effective once those three facts are true. No later commit is required only to change this header or to repeat the activation. `OPERATOR_AUTONOMOUS_LANES_2_3_4_RESTRUCTURING_PREPARATION_AUTHORIZED` does not satisfy item 2.

## Option A text

### Standing development authority

After the three acceptance facts, Lanes 2, 3, and 4 may implement, test, debug, and refactor on their own branches inside the packages below. Ordinary commits, test runs, and draft pull requests do not need a new current-state item, a new Operator decision, a governance pull request, or a Lane 1 progress review. A failed provider attempt inside an already effective standing budget does not need a governance pull request.

Specialists do not edit `docs/CURRENT_STATE.md`, `docs/ENGINEERING_JOURNAL.md`, `docs/WORKSTREAM_STATUS.md`, `docs/WORKSTREAM_DEPENDENCIES.md`, `docs/INTEGRATION_PROTOCOL.md`, `docs/adr/`, `pyproject.toml`, `.github/`, or `.cursor/rules/` for ordinary package work. They may add a workstream-local test or diagnostics module inside the package. A new runtime dependency is security-sensitive and needs independent verification before integration. Lane 1 remains the only proposer of canonical integration. Specialists do not self-merge to `main`.

Security-sensitive commits and completed milestones still need one independent exact-tree verification before integration. A change is security-sensitive when it touches credential custody, a network client, an execution-mode flag, an order path, the migration target guard, a scanner exclusion, an allowlist, a shared economic contract, or a dependency manifest. One verification of the finished candidate is enough. Related milestones may share one integration window, one verification, and one Operator decision.

The Operator may grant a later bounded task directly to the owning specialist by using the decision name written in this ADR. Lane 1 is not a required messenger for that task. The grant cannot exceed this ADR. It cannot authorize `LIVE`, real capital, port `5432`, a Gmail write scope, or an unnamed host. The specialist cites the decision in the milestone pull request. The next batched integration records it in current state. Until the named standing-access decision exists, older current-state sentences that deny that provider call or migration remain in force.

### Lane 2 package

Owned paths are the existing `src/swingtrade/alpaca_paper*.py` modules, their `tests/unit/test_alpaca_paper*.py` files, and new offline Alpaca support modules whose names start with `alpaca_paper` under `src/swingtrade/` and `tests/unit/`. Pull request #92 and pull request #80 stay valid history. Neither must merge before further authorized support code.

The package includes the account adapter, a network client that stays uncalled until the standing read grant is effective, Windows-local custody limited to the two ADR-0008 paper targets, transport and TLS checks, timeouts, retries that stay on the same host, request-budget accounting, synthetic responses, and order-lifecycle simulation with no external submission. The seven Gate C2 flags stay false in committed code. The Item 25 scan tokens stay absent. No live host, order placement, cancellation, replacement, positions, or streaming is included.

### Lane 3 package

Owned paths are `src/swingtrade/gmail_local_connect.py`, `src/swingtrade/group4_email/`, `tests/unit/test_gmail_local_connect.py`, and `tests/group4_email/`. Pull request #94 stays valid history.

The package includes the read-only transport, the existing Desktop authorization-code flow, the ADR-0006 custody target `swing-trading/lane3/gmail/dev/refresh-token`, refresh-token handling, token-request encoding, redirect and state validation, sanitized diagnostics, profile and message requests, bounded retries, restart-safe accounting, real Message-ID shapes, MIME parsing, provenance, duplicate and replay protection, and quarantine. The mocked pilot bounds remain an injected transport, scope `https://www.googleapis.com/auth/gmail.readonly`, at most 10 messages, `durable_state = UNAVAILABLE`, and `economic_dispatch = false` until a later persistence integration.

The scanner edit may exclude `gmail_readonly_pilot.py` beside `local_oauth_probe.py` and may update that one pinned blob. No other exclusion is added. That edit is security-sensitive before integration. `client_secret` stays absent unless a later Operator decision approves it for the selected application type. Campaign `GMAIL-METADATA-CAMPAIGN-0D571DEC` stays stopped. Attempt 1 stays consumed. Attempts 2 and 3 stay unused. The package includes no Gmail send, modify, or delete, and no brokerage action.

### Lane 4 package

Owned paths are the effective Item 39 guard files, `alembic.ini`, `migrations/env.py`, and `tests/unit/test_alembic_target_guard.py`, plus, for offline authorship and synthetic tests only:

- `src/swingtrade/postgres_receipt_store.py`
- `tests/integration/test_postgres_receipt_store.py`
- `migrations/versions/0004_instruction_receipts.py`

This amends Item 30 for authorship only. Stage E and Stage F are not required to write, review, or mock-test those files. Writing revision `0004` does not permit running it. The guard stays fail-closed. Port `5432`, database `swingtrade`, a bootstrap superuser, and a remote host stay refused. The package may also hold future outbox and execution-ledger modules under `src/swingtrade/` whose names start with `postgres_receipt` or `execution_ledger`, together with their tests. Those modules do not open an order path.

### Standing isolated-test grants

Each grant below stays inactive. Development authority does not activate it. A grant becomes effective when the Operator issues its decision with every missing fact named here. The specialist may then repeat the permitted operation inside the budget without a new approval. Crossing the budget, host, scope, or cluster stops the grant.

#### Alpaca paper account read

Decision name: `LANE1_ALPACA_STANDING_PAPER_ACCOUNT_READ_AUTHORIZED`.

When issued, it permits `GET https://paper-api.alpaca.markets/v2/account` only, at most 30 requests per America/New_York calendar day, on an attended Windows-local runtime, using only `swing-trading/lane2/alpaca/paper/key-id` and `swing-trading/lane2/alpaca/paper/secret`. Redirects are refused. A retry stays on that method and host. Logs omit the key, the secret, and the raw account body. The seven Gate C2 flags stay false. This grant is not issued by this candidate.

#### Gmail read-only connection

Decision name: `LANE1_GMAIL_STANDING_READONLY_CONNECTION_AUTHORIZED`.

When issued, it permits token exchange or refresh, a profile check, and read-only message GETs for one mailbox and one new campaign identifier, both named in the decision. The scope is `https://www.googleapis.com/auth/gmail.readonly`. The custody target is `swing-trading/lane3/gmail/dev/refresh-token`. The budget is 20 token-endpoint attempts and 50 read-only GETs per America/New_York calendar day, with at most 10 messages per list. `DEP-GMAIL-001` stays open until the Operator attests the out-of-band OAuth setup. This candidate does not name a mailbox or a campaign, and it does not resume `GMAIL-METADATA-CAMPAIGN-0D571DEC`. This grant is not issued by this candidate.

#### PostgreSQL receipt-test cluster

Decision name: `LANE1_POSTGRES_STANDING_RECEIPT_CLUSTER_AUTHORIZED`.

Real use of `127.0.0.1` port `5433`, database `swingtrade_receipt_test`, role `swingtrade_migrator`, and system identifier `7707684291752896980` stays closed until this decision. The decision must include a same-connection identity proof for that cluster and a statement that port `5432` was not modified. The Operator's statement that the isolated cluster exists and that the Alembic guard passes its tests does not by itself supply that proof. When the decision is issued, repeatable tests and migrations for revisions `0001` through `0003` may run on that cluster without a new approval. Revision `0004` still needs a separate execution decision, `LANE1_POSTGRES_REVISION_0004_EXECUTION_AUTHORIZED`, after the same identity check. Port `5432` stays out of scope. This grant is not issued by this candidate.

#### Paper orders

Decision name: `LANE1_ALPACA_STANDING_PAPER_ORDER_AUTHORIZED`.

This grant stays closed. `DEP-CORE-001` and `DEP-CORE-002` remain blocking. The decision must name the paper account, symbols, order types, notional, quantity, open-order count, daily count, session duration, and revocation. No value is selected here.

## Consequences

This candidate does not make Option A effective. After the three acceptance facts, ordinary specialist work no longer returns to Lane 1, and Item 30 no longer blocks offline authorship of the three named files. Standing access still waits for its own decision. ADR-0008, ADR-0006, the Alembic guard, and the non-overridable safety rule stay in force.

## Validation and rollback

Acceptance evidence is the independent pass, the named integration decision, and the fast-forward. Rollback is a later Operator decision that revokes the development packages or a standing grant. Failure to keep `DRY_RUN`, the seven flags false, the Gmail write prohibition, or port `5432` closed is outside this proposal.

## Unresolved questions

The Gmail mailbox and new campaign identifier are unset. The same-connection receipt-cluster proof is not in this candidate. Paper-order limits are unset. Native Windows custody behavior is not certified here.

## Evidence

- Repository reference: canonical `main` `6d50b3eb292d78fd6396fc6f0d35023d24b3290e`, tree `89f648d862f8831d78ba2b9de565934d4a8a7112`, inspected 2026-11-14. Supported claim: this is the authoring baseline. Limitation: this candidate is not that commit.
- Repository reference: open pull requests #92 and #94 on that date. Supported claim: the account-read and mocked Gmail pilot heads named above were open. Limitation: this candidate does not merge them.
- Repository reference: `docs/AGENT_AUTHORITY.md` on that baseline. Supported claim: a denied capability stays denied until current state and the conjunctive gates change. Limitation: this candidate does not edit that file.
