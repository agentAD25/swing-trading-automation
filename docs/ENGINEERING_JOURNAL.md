# Engineering Journal

Append-only record of material repository work. Correct prior entries with a
new entry rather than rewriting history.

## 2026-09-25 — Phase 1A governance bootstrap

### Scope

Established repository structure, agent authority, mandatory rules, four agent
roles, decision records, research handoff requirements, and factual current
state. No TradeStation research or foundation implementation was performed.

### Starting evidence

- `git fetch origin main` completed successfully.
- Canonical `origin/main` was commit `8b37e20` (`Add new Test file`).
- `git ls-tree -r --name-only origin/main` returned only `Test`.
- Existing `Test` content was the single line `Test`; it was preserved.

### Decisions and boundaries

- `SIM` is the sole authorized execution mode.
- `LIVE`, real-account interaction, credentials, and real-capital deployment
  are unauthorized.
- Three research workstreams are scoped as broker/API, strategy/data, and
  risk/operations.
- Durable architecture decisions require human acceptance of an ADR.

### Unresolved

- Broker and market-data requirements are not researched.
- Strategy, universe, timeframe, and data requirements are not selected.
- Risk limits, operating controls, and compliance obligations are not selected.
- Technology stack, package layout, deployment target, and test tooling are
  not selected.
- Human owners/deciders and criteria for later phase transitions are not named.

### Validation

Pending at the time of this entry; exact commands and outcomes will be added
before Phase 1A is handed off.

## 2026-09-25 — Phase 1A validation

### Evidence

- `git diff --check origin/main...HEAD` passed with no whitespace errors.
- Structure validation passed: all required placeholders exist, exactly four
  `.cursor/agents/*.md` files and three `.cursor/rules/*.mdc` files are tracked,
  every rule declares `alwaysApply: true`, and every agent declares `name` and
  `description`.
- Scope validation passed: all 19 tracked files are the preserved `Test` file
  or governance Markdown/MDC/ignore files; no implementation file was added.
- Secret-pattern validation found no tracked private-key marker, GitHub token
  pattern, or AWS access-key pattern.
- Safety-language validation confirmed tracked governance includes `SIM`-only
  and `LIVE`-unauthorized statements.
- `git status --short --branch` showed a clean branch synchronized with
  `origin/cursor/phase-1a-governance-e1ba` before this evidence update.
- `gh pr view 1 --json url,isDraft,state,headRefName,baseRefName,title`
  confirmed an open draft PR from the governance branch to `main`.

### Outcome

All Phase 1A readiness gates passed. The three research workstreams are ready
after this baseline is adopted by merge or explicit human direction. This does
not authorize foundation implementation, account access, credentials, order
submission, real capital, or `LIVE`.

## 2026-09-25 — Phase 1B architecture/design contracts

### Scope

Under explicit human direction, drafted the broker-neutral architecture,
lifecycle, data, event, idempotency, reconciliation, operations, reporting,
test, SIM certification, and future promotion contracts. Added a deterministic
synthetic WDC conformance fixture. No production code, credentials, broker
access, order submission, or external broker claim was introduced.

### Decisions and boundaries

- Ports-and-adapters with append-only events, rebuildable projections, an
  atomic intent/outbox boundary, stable idempotency, and fail-closed
  reconciliation is the proposed foundation.
- Material decisions are recorded in Proposed ADR-0001; no human decider is
  named and nothing is Accepted.
- The WDC fixture is invented contract-test data with a prohibited-for-
  production mechanical rule; it is neither market data nor strategy evidence.
- `SIM` remains the only authorized mode. Phase 2 and `LIVE` remain unstarted
  and unauthorized.

### Unresolved

All TradeStation-specific behavior; strategy and market-data selection; risk
limits; operating thresholds and owners; technology and deployment choices;
security, legal, compliance, entitlement, and licensing obligations; and
human decision authority.

### Validation

Pending. Exact commands, commit, and outcomes will be recorded after the
draft is committed for review.
