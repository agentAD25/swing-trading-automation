# Current State

- Last updated: 2026-09-25
- Current phase: Phase 1E — bounded offline foundation remediation
- Phase status: `PHASE1_ACCEPTED` for the exact broker-neutral offline
  deterministic candidate only
- Authorized execution mode: `DRY_RUN` only (local, deterministic, non-network)
- TradeStation `SIM`: Reserved for a future connectivity phase; unauthorized
- `LIVE` status: Unauthorized
- Foundation implementation: Minimal local non-network `DRY_RUN` foundation
  authorized by the human Operator and under review in draft PR #6
- Phase 1E: Started; bounded to P1E-01 through P1E-05 remediation only
- Phase 2: Unstarted and unauthorized
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
| Phase 1E | Human-authorized minimal offline foundation under review in draft PR #6; current remediation is limited to P1E-01 through P1E-05 |
| Phase 2 | Not started and not authorized |

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
- Four scoped agent roles: coordinator plus three researchers
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

The three workstreams may begin only after Phase 1A validation confirms:

- all required governance artifacts exist;
- exactly four agent definitions exist;
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

## Unresolved items

1. The acceptance instruction identifies the human Operator by role; no
   additional personal or service identifier is recorded in repository
   evidence.
2. Individual ADR statuses remain unchanged; bounded Phase 1 acceptance does
   not expand any ADR or authorize implementation.
3. Twelve production-critical broker behavior groups remain unresolved;
   strategy/data and risk/operations facts remain unresearched.
4. Legal, regulatory, entitlement, security, and data-licensing obligations
   are unknown.
5. Technology, persistence, deployment, operating thresholds, recovery
   objectives, and risk limits are unknown.
6. Phase 2 entry criteria and authority are not granted.
7. External governance enforcement and authenticated Operator identity are not
   established. `DRY_RUN` remains structurally non-network; future broker
   connectivity and zero-order-attempt controls are not authorized.

## Evidence

Starting-state and change evidence is recorded in
`docs/ENGINEERING_JOURNAL.md`. Phase 1A validation completed successfully on
2026-09-25. Phase 1B design and fixture validation passed within their stated
scope. Phase 1C integrated-content validation is recorded in the journal.
Independent verification passed the exact Phase 1 candidate, and bounded
Operator acceptance is recorded in `PHASE_1_ACCEPTANCE_MANIFEST.md`. The human
Operator later authorized only the bounded Phase 1E offline implementation and
P1E-01 through P1E-05 remediation recorded in the journal. No Phase 2, broker,
TradeStation `SIM`, credential, account, order, deployment, real-capital, or
`LIVE` authority follows.
