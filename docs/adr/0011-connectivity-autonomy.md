# ADR-0011: Connectivity autonomy and credential ownership

- Status: Proposed
- Date: 2026-11-14
- Sole Phase 1 decider: Human Operator
- Scope: Development-package expansion for Lanes 2, 3, and 4, and the public shape of attended diagnostic grants
- Supersedes: None
- Superseded by: None

## Context

ADR-0010 Option A development authority is already effective for commit `92ea9527236647773312d0713c76da418bd2fcfc`, tree `2189f520c3b679ef0cfc8688795da1b261cadb92`. This amendment does not reopen that record. `src/swingtrade/gmail_credential/` is already on that main and is outside the ADR-0010 Lane 3 path list. The Operator directed one ownership and connectivity amendment on 2026-11-14. That direction prepares this candidate. It does not issue a provider grant, read a secret, run a migration, or submit an order.

## Safety impact

`DRY_RUN` stays the only authorized trading mode. This candidate contains no mailbox address, account identifier, token, or signing secret. Integrating it does not open Gmail, Alpaca, port `5432`, port `5433`, or an order path. A runtime grant stays inactive until the Operator issues that grant directly to the owning specialist.

## Options considered

### Option A — Expanded packages and direct attended grants

Adopt the package expansions, the public capability registry, and the direct Operator-to-specialist grant procedure below. One later decision can accept this option and authorize integration of the commit that contains it. No second commit is required to repeat the expansion.

### Option B — Leave the ADR-0010 path lists unchanged

Lane 3 continues without explicit ownership of `gmail_credential/`. This option remains the operative limit while this ADR is only a candidate.

## Decision

The Decision stays blank while the status is Proposed. The Operator has not selected Option A or Option B.

## Acceptance and effectiveness

Option A becomes the operating rule only when all three are true for the commit that contains this section:

1. An independent verifier, distinct from the author, returns `INDEPENDENT_EXACT_TREE_PASS` for that commit and tree.
2. The Operator issues `OPERATOR_CONNECTIVITY_AUTONOMY_EXACT_INTEGRATION_AUTHORIZED` for that same commit. That decision selects Option A and authorizes one non-forced fast-forward. It does not issue a runtime grant.
3. That commit is integrated by that fast-forward and remains an ancestor of canonical `main`.

While the header still says Proposed, specialists treat Option A as effective once those three facts are true. No later commit is required only to change this header. The preparation direction does not satisfy item 2.

## Option A text

### Development packages

Ordinary commits, tests, and repairs inside these packages do not need a new Lane 1 ownership decision, a current-state item, or an Operator decision. Security-sensitive candidates still need one independent exact-tree verification before canonical integration. Specialists do not self-merge. A new runtime dependency remains security-sensitive.

The public registry at `docs/connectivity/capability-registry.json` describes these packages and the runtime grants. A field in that file is not authorization. Code must not treat a registry status, an environment-variable boolean, a caller-supplied MAC key, or a self-created permission object as sufficient authority for a real credential read, provider call, migration, or order.

#### Lane 3

The ADR-0010 Lane 3 paths remain owned. This amendment adds:

- `src/swingtrade/gmail_credential/**`
- `tests/unit/test_gmail_credential*.py`
- Gmail-specific Windows OAuth and credential-custody adapters under those trees
- Gmail-local authorization, revocation, and request-budget support
- Gmail-specific attended runtime and operational diagnostics

The package stays where it is. The custody target remains `swing-trading/lane3/gmail/dev/refresh-token`. Lane 3 may implement and mock-test native retrieval and storage on its branch. A real credential read or Google request waits for the Gmail grant below. Lane 3 has no authority to read Lane 2 brokerage secrets or any other lane's secrets. Campaign `GMAIL-METADATA-CAMPAIGN-0D571DEC` stays stopped.

#### Lane 2

The ADR-0010 `alpaca_paper` paths remain owned. They include the account reader, PAPER Credential Manager integration, the account GET runtime, grant verification, budget protection, Windows deployment, transport and TLS corrections, synthetic order lifecycle, acknowledgement and reconciliation adapters, and matching tests. PAPER execution-adapter code may exist behind the inactive order gate. The seven Gate C2 flags stay false in committed code. No live host, order placement, cancellation, replacement, positions, or streaming is included.

Pull request #92 remains the existing runtime candidate. This amendment does not replace it. For one attended account-read campaign, a Windows-local grant binding may be used when an independent verification accepts it. That binding must name the Operator decision, the Windows identity, the paper account, `GET https://paper-api.alpaca.markets/v2/account`, the expiry, the revocation condition, and the 30-request ceiling. The candidate must state its clock-rollback and same-user file-rewrite limits. It must not claim tamper resistance. Unattended recurring access is outside this amendment.

#### Lane 4

The ADR-0010 receipt paths remain owned. This amendment adds workstream-local development of receipt persistence, database-local transaction tests, order-intent persistence, the durable outbox and event history, broker-event and fill schema, idempotent replay, and receipt or execution-ledger adapters, with their tests. Shared economic contracts stay as they are unless Lane 1 records a conflict. Port `5432` and database `swingtrade` stay outside the package.

The dedicated cluster identity remains `127.0.0.1` port `5433`, database `swingtrade_receipt_test`, role `swingtrade_migrator`, system identifier `7707684291752896980`. Writing revision `0004` does not run it. Immutable commit `92ea9527236647773312d0713c76da418bd2fcfc` remains the source checkout for revisions `0001` through `0003`, because a tree that contains `0004` makes the current guard reject the whole directory.

A later security-sensitive commit may add exactly `0004_instruction_receipts` to the guard allowlist. That commit is eligible only after `LANE1_POSTGRES_REVISION_0004_EXECUTION_AUTHORIZED` and after revisions `0001` through `0003` have been applied from the immutable checkout. This amendment does not make that edit and does not remove the guard.

### Attended diagnostic grants

These grants stay inactive. Development ownership does not activate them. The Operator may issue a grant directly to the owning specialist. Lane 1 is not a required messenger. The specialist may then repeat the permitted operation until the ceiling, host, method, account, or expiry is crossed. A failed attempt inside an effective budget does not need a governance commit. The private mailbox, the paper account binding, and every secret stay on the attended Windows machine and out of Git.

An attended grant expires and is revoked on the Operator's stated condition. It does not authorize unattended repetition. Unattended access would need a separate stronger decision that this amendment does not supply.

#### Gmail read-only connection

Decision name: `LANE1_GMAIL_STANDING_READONLY_CONNECTION_AUTHORIZED`.

Designated campaign: `GMAIL-READONLY-SIGNAL-DISCOVERY-20261114-R1`.

When issued, the Operator privately approves one mailbox and performs consent or MFA if Google requires it. The decision names the expiry, the revocation condition, and the approved sender or label selector. The scope is `https://www.googleapis.com/auth/gmail.readonly`. The budget is 20 token-endpoint attempts and 50 read-only GETs per America/New_York calendar day, at most 10 messages per list. Send, modify, delete, attachment download, and economic dispatch are excluded. `DEP-GMAIL-001` stays open until the Operator attests the out-of-band OAuth setup. This candidate does not issue the grant and does not record a mailbox address.

#### Alpaca paper account read

Decision name: `LANE1_ALPACA_STANDING_PAPER_ACCOUNT_READ_AUTHORIZED`.

When issued, it permits `GET https://paper-api.alpaca.markets/v2/account` only, at most 30 requests per America/New_York calendar day, on an attended Windows-local runtime, using only the two ADR-0008 paper credential targets. The decision names the paper account, the Windows identity, the expiry, and the revocation condition. No live host, order, streaming, or positions request is included. This candidate does not issue the grant.

#### PostgreSQL receipt-test cluster

Decision name: `LANE1_POSTGRES_STANDING_RECEIPT_CLUSTER_AUTHORIZED`.

When issued, the decision includes a same-connection identity proof for the cluster named above and a statement that port `5432` was not modified. Lane 4 may then repeat tests and migrations for revisions `0001` through `0003` from the immutable checkout. Revision `0004` still needs `LANE1_POSTGRES_REVISION_0004_EXECUTION_AUTHORIZED`. This candidate does not issue either decision.

#### Paper orders

`LANE1_ALPACA_STANDING_PAPER_ORDER_AUTHORIZED` stays closed. `DEP-CORE-001` and `DEP-CORE-002` remain blocking. No order value is selected here.

### Attended setup

Lane 3 asks the Operator for `LANE1_GMAIL_STANDING_READONLY_CONNECTION_AUTHORIZED` with the designated campaign, an expiry, and a revocation condition. The mailbox stays on the Windows machine. After the grant is effective, Lane 3 runs the attended OAuth exchange or refresh, one profile check, and one bounded message retrieval, then retries failures inside the same budget.

Lane 2 finishes the attended account reader on its existing branch and obtains independent verification of that security-sensitive candidate. It then asks the Operator for `LANE1_ALPACA_STANDING_PAPER_ACCOUNT_READ_AUTHORIZED` bound to one paper account. The first live operation is the single account GET. Order-adapter code stays inactive.

Lane 4 asks the Operator to run the same-connection identity check and to issue `LANE1_POSTGRES_STANDING_RECEIPT_CLUSTER_AUTHORIZED`. Receipt durability tests on port `5433` follow that grant. Revision `0004` waits for its own decision and the separate guard commit.

## Consequences

This candidate does not make Option A effective. After the three acceptance facts, the expanded packages and the direct-grant procedure are effective, and no activation-only pull request is required. Runtime grants remain inactive until the Operator issues each one. ADR-0010, ADR-0008, and ADR-0006 stay in force.

## Validation and rollback

Acceptance evidence is the independent pass, the named integration decision, and the fast-forward. Rollback is a later Operator decision. A real provider call, credential read, migration, or order made under this candidate alone is outside the proposal.

## Unresolved questions

The Gmail mailbox, the sender or label selector, the Alpaca paper account, the Windows runtime identity, and the receipt-cluster same-connection proof are not in this candidate. Pull request #92 is not a fast-forward of current main. Pull request #96's current tip is later than the commit verified as `d8436026ccc26b6d9cc5e50e5f8413d5bf8ee8c0`.

## Evidence

- Repository reference: canonical `main` `92ea9527236647773312d0713c76da418bd2fcfc`, inspected 2026-11-14. Supported claim: `src/swingtrade/gmail_credential/` and its unit test are already on that main. Limitation: ADR-0010 does not name that directory.
- Repository reference: pull request #94 head `ce822e4eeed8ce4d85bc11f75658de3411d122c2`, tree `9715a64a6c7ffbb9986d112b637d917061ee7b5a`, merge-base `92ea9527236647773312d0713c76da418bd2fcfc`. Supported claim: the head is a fast-forward of current main. Limitation: this candidate does not merge it.
- Repository reference: pull request #92 head `1e013e7bdc23027b1d273980245a43f8887792ee`, merge-base `80b5437c5296ba07e3f4f9f149c11629b6dfa497`. Supported claim: the head is not a fast-forward of current main. Limitation: the reported verifier `e206a577-021d-47d0-822c-f00afab4f4ff` was not a retrieved transcript.
- Repository reference: pull request #96 head `da545f23ab25db7066fd8b5de8316af553d6e807`, tree `8d72e088e473d097d5f56b867a557d0c71cdc425`, parent `d8436026ccc26b6d9cc5e50e5f8413d5bf8ee8c0`. Supported claim: the parent was independently verified and the tip adds the UTF-8 byte-length check. Limitation: the reported verifier `de5a4378-c5ba-4b29-b409-6142fe5321e6` was not a retrieved transcript, so the tip is not treated as verified by this candidate.
