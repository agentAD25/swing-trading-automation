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

Validated after committing and pushing the review draft:

- `git diff --check cursor/phase-1a-governance-e1ba...HEAD` and a clean-tree
  assertion passed.
- A Python 3 standard-library fixture procedure recalculated every manifest
  SHA-256, parsed all CSV/JSON/JSONL, verified canonical UTF-8 JSON bytes, 15
  unique event ids, contiguous per-aggregate versions, report/event
  high-water-mark ties, reconciliation status, and entry/exit arithmetic; it
  printed `fixture integrity, canonical bytes, arithmetic, and event
  sequences: PASS`.
- A Python 3 Markdown procedure verified all 14 required contract documents
  and every relative Markdown link; it printed `required documents (14) and
  relative Markdown links: PASS`.
- A Python 3 boundary procedure asserted `SIM`-only, Phase 2/`LIVE`
  unauthorized, no production code, and explicit TradeStation uncertainty
  language; it printed `safety, phase, and broker-uncertainty language: PASS`.
- `git diff --name-only cursor/phase-1a-governance-e1ba...HEAD` plus an
  implementation-extension allowlist check confirmed documentation/fixture-
  only scope.
- `rg` sensitive-pattern scanning outside documentation and fixtures passed.

The first fixture documentation check exposed that this environment provides
`python3`, not `python`; the documented command was corrected and all listed
checks then passed.

## 2026-09-25 — Phase 1B TradeStation broker research

### Scope

Researched the current public TradeStation API contract for environment
separation, OAuth, brokerage state, market data, rate limits, and order
lifecycle. Findings are recorded in `docs/BROKER_CONTRACT.md`. This was
documentation-only work: no credentials, account access, API calls, orders, or
production implementation were used.

`SIM` remains the only authorized execution mode. `LIVE` remains unauthorized.
No risk, analytics, persistence, execution, or signal semantics were designed
or changed.

### Material findings

- **Fact:** TradeStation documents separate v3 hosts for LIVE and SIM and says
  SIM uses fake accounts and simulated instant fills. Source: TradeStation,
  "SIM vs. LIVE,"
  https://api.tradestation.com/docs/fundamentals/sim-vs-live/, accessed
  2026-09-25T18:05:40Z.
- **Fact:** OAuth access tokens last 20 minutes; refresh-token behavior is
  key-configuration-dependent and token material must be stored securely.
  Sources: TradeStation, "Auth Code Flow" and "Refresh Tokens,"
  https://api.tradestation.com/docs/fundamentals/authentication/auth-code/ and
  https://api.tradestation.com/docs/fundamentals/authentication/refresh-tokens/,
  accessed 2026-09-25T18:05:40Z.
- **Fact:** Official pages conflict on rotating refresh-token interval (30
  versus 40 minutes) and stated default scopes. Sources: TradeStation,
  "Authentication Overview," "Refresh Tokens," and "Scopes,"
  https://api.tradestation.com/docs/fundamentals/authentication/auth-overview/,
  https://api.tradestation.com/docs/fundamentals/authentication/refresh-tokens/,
  and https://api.tradestation.com/docs/fundamentals/authentication/scopes/,
  accessed 2026-09-25T18:05:40Z.
- **Fact:** Confirmation estimates an order without placing it. Place, replace,
  and cancel are separate endpoints; documented replace/cancel responses
  acknowledge requests rather than prove terminal state. Source: TradeStation,
  "TradeStation API Specification,"
  https://api.tradestation.com/docs/specification/, accessed
  2026-09-25T18:05:40Z.
- **Fact:** Successful batch and order responses can include item-level
  `Errors`; an HTTP 200 is therefore not proof of complete success. Source:
  TradeStation, "TradeStation API Specification," response examples, same URL
  and access timestamp.
- **Fact:** Request quotas use rolling intervals and some streams also have
  concurrent limits; HTTP 429 and response headers communicate throttling.
  Source: TradeStation, "Rate Limiting Overview,"
  https://api.tradestation.com/docs/fundamentals/rate-limiting/rate-limiting-overview/,
  accessed 2026-09-25T18:05:40Z.
- **Inference:** SIM is suitable for interface contract testing but its
  documented instant-fill behavior does not establish execution realism.
  Source/limitation: TradeStation, "SIM vs. LIVE," same URL and access
  timestamp.

### Unresolved

`docs/BROKER_CONTRACT.md` marks twelve
`BROKER_BEHAVIOR_UNRESOLVED` groups. The highest-impact gaps are order-command
idempotency, ambiguous timeout recovery, the complete order state machine,
stream replay/gap behavior, SIM fidelity, key-specific entitlements and quotas,
and conflicting official authentication statements. These remain open
questions; no behavior was guessed.

### Validation

Validation evidence will be appended before handoff. Planned checks are
Markdown/source-reference inspection, safety/scope assertions,
`git diff --check`, and repository diff review.

### Final validation evidence

- `git diff --check cursor/phase-1a-governance-e1ba...HEAD` passed with no
  whitespace errors.
- `git diff --name-only cursor/phase-1a-governance-e1ba...HEAD` returned only
  `docs/BROKER_CONTRACT.md` and `docs/ENGINEERING_JOURNAL.md`, confirming
  documentation-only scope.
- Eight first-party source URLs listed in `docs/BROKER_CONTRACT.md` were
  requested without authentication using `curl -L`; every URL returned HTTP
  200 on 2026-09-25.
- Source-marker inspection found 37 classified material findings in
  `docs/BROKER_CONTRACT.md`; each cites a source identifier and the
  `2026-09-25T18:05:40Z` access timestamp.
- Safety/scope inspection confirmed explicit `SIM`-only,
  `LIVE`-unauthorized, no-credentials/no-orders, and no production
  implementation statements.
- `git status --short --branch` was clean and synchronized with
  `origin/cursor/phase-1b-broker-research-e23f` before this validation evidence
  was appended.

## 2026-09-25 — Phase 1C coordinator reconciliation

### Scope

Integrated the complete Phase 1B architecture series, the two broker-research
commits, and the failure-model commit onto the Phase 1A governance baseline.
Compared agreements, conflicts, unsupported assumptions, broker limitations,
safety blockers, unresolved risks, and human/operator decisions. The durable
disposition is `docs/PHASE_1C_RECONCILIATION.md`.

No foundation code, credential, account access, API interaction, order,
deployment, `LIVE` authorization, or Phase 2 work was introduced.

### Decisions and boundaries

- `SIM` remains the sole authorized mode; the documented SIM host is not proof
  of runtime isolation.
- The broker-neutral design is coherent enough for human review but remains
  Proposed.
- Twelve broker behavior groups and the governance/enforcement failure
  scenarios remain safety blockers.
- The exact status is `PROPOSED / FREEZE_BLOCKED`, not `PHASE1_ACCEPTED`.
- Historical input documents are preserved; stale point-in-time statements are
  reconciled explicitly rather than used as current claims.

### Validation

Pending for the integrated Phase 1C revision. Results will be appended after
the review commit is pushed.

### Final validation evidence

Validation ran against pushed review commit `f0ec3b3`:

- `git diff --check cursor/phase-1a-governance-e1ba...HEAD` passed with no
  whitespace errors.
- `git status --short --branch` showed a clean branch synchronized with
  `origin/cursor/phase-1c-reconciliation-3eee`.
- The diff inventory contained only Markdown, MDC, CSV, JSON, and JSONL
  governance/design/fixture files; an implementation-extension allowlist check
  passed.
- A Python 3 standard-library check found all 18 required integrated documents
  and validated every relative Markdown link; it printed `required documents
  (18) and relative Markdown links: PASS`.
- The deterministic fixture check verified manifest SHA-256 values, parsed all
  CSV/JSON/JSONL, canonical JSONL bytes, 15 unique event ids, contiguous
  aggregate versions, source high-water mark, reconciliation, flat ending
  position, and `8.0000` arithmetic; it printed `fixture digests, canonical
  events, sequences, and arithmetic: PASS`.
- The first invocation of that custom fixture check referenced nonexistent
  report fields (`event_high_water_mark`) and exited with `KeyError`; inspection
  showed the fixture contract uses `source_high_water_mark` and nested trade
  fields. The corrected check above passed without changing the fixture.
- A Phase 1C boundary check confirmed explicit `PHASE1_ACCEPTED` denial,
  `PROPOSED / FREEZE_BLOCKED`, all FM-01–FM-24 coverage, twelve broker blocker
  groups, and no `LIVE` decision; it printed `acceptance, freeze, safety, and
  blocker language: PASS`.
- Sensitive-pattern scanning outside documentation and fixtures found no
  private-key marker, GitHub token pattern, or AWS access-key pattern.
- All eight unique first-party TradeStation documentation URLs in
  `BROKER_CONTRACT.md` returned HTTP 200 via unauthenticated `curl -L`.
- `git diff --exit-code` proved `BROKER_CONTRACT.md` is byte-identical to
  source commit `f5e23b0` and `FAILURE_MODEL.md` is byte-identical to source
  commit `fd5e37d`.
- Integrated history contains architecture mappings `fd5adc3`→`7dfac71`,
  `ba41e14`→`7c1efa4`, `edf2d96`→`caefbff`, `032794e`→`6ac4158`; broker
  mappings `f5e23b0`→`177c58c`, `c12a3ca`→`2da5efc`; and failure-model mapping
  `fd5e37d`→`749038d`.

These checks establish integrated documentation, link, fixture, safety-language,
and scope conformance only. They do not close a freeze blocker, accept an ADR,
certify implementation, authorize credentials/accounts/orders, start Phase 2,
or authorize `LIVE`.

## 2026-09-25 — Phase 1D approved corrections

### Scope

Implemented the Operator-approved acceptance model and four verified
contract/fixture contradiction corrections. The Operator is the sole decider;
any future `PHASE1_ACCEPTED` status is bounded to the broker-neutral, offline,
deterministic baseline. `DRY_RUN` is local/non-network; TradeStation `SIM` is a
future connectivity capability. Broker activity, credentials, Phase 2, order
submission, real capital, and `LIVE` remain unauthorized.

Added a non-overridable authority rule and conjunctive future TradeStation
`SIM`/`LIVE` promotion gates. Corrected fixture idempotency keys, intent
transitions, report metadata/digest semantics, and offline trade grouping.
Exact contradictions, evidence, rationale, files, and affected validation are
recorded in `docs/PHASE_1D_CORRECTIONS.md`.

This work does not mark `PHASE1_ACCEPTED`, accept ADR-0001, implement code, use
credentials, connect to a broker, or begin Phase 1E or Phase 2.

### Validation

Pending for the pushed Phase 1D review revision. Exact commands and outcomes
will be appended after validation.
