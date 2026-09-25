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
