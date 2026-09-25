# Current State

- Last updated: 2026-09-25
- Current phase: Phase 1A — governance bootstrap
- Phase status: Complete on governance branch; pending human review/merge
- Authorized execution mode: `SIM` only
- `LIVE` status: Unauthorized
- Foundation implementation: Not started and not authorized by Phase 1A
- Canonical baseline: `origin/main` at `8b37e20`
- Research workstreams ready: Yes, after adoption of this governance baseline

## Established

- Repository governance and least-authority rules
- Four scoped agent roles: coordinator plus three researchers
- ADR process and research evidence contract
- Skeleton locations for configuration, documentation, source, and tests
- Explicit fail-closed boundary around `LIVE`, credentials, real accounts, and
  real capital

## Not established

No broker capability, API behavior, strategy, data source, risk threshold,
technology stack, architecture, or deployment approach has been validated or
selected. There is no trading, data, backtesting, or integration implementation.

## Research readiness gates

The three workstreams may begin only after Phase 1A validation confirms:

- all required governance artifacts exist;
- exactly four agent definitions exist;
- all mandatory rules are always applied;
- `SIM`-only and `LIVE`-unauthorized language is consistent;
- no secrets or implementation were introduced; and
- the governance branch is reviewable in a draft pull request.

Each workstream must follow `docs/research/README.md`. Research permission does
not authorize implementation or any interaction with an account.

All listed readiness gates passed on 2026-09-25. The broker/API,
strategy/data, and risk/operations workstreams are ready to begin independently
once this governance baseline is adopted through merge or explicit human
direction.

## Unresolved items

1. Human owner(s) and ADR decider(s) are not named.
2. Research acceptance criteria beyond the common evidence contract are not
   yet approved.
3. Broker/API, strategy/data, and risk/operations facts remain unresearched.
4. Legal, regulatory, entitlement, and data-licensing obligations are unknown.
5. Later phase gates, implementation stack, and deployment target are unknown.

## Evidence

Starting-state and change evidence is recorded in
`docs/ENGINEERING_JOURNAL.md`. Phase 1A validation completed successfully on
2026-09-25.
