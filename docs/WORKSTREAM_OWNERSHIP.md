# Workstream Ownership and Authority Hierarchy

Defines lane boundaries, shared-file sensitivity, worktree isolation, and the
operating hierarchy used to resolve conflicts.

## Operating hierarchy

Conflicts resolve from highest authority to lowest. An agent conversation
(Level 6) may never override an accepted contract (Level 1) or canonical main
(Level 2).

| Level | Name | Authority |
| --- | --- | --- |
| 0 | Operator authority | Human-approved requirements; credential authorization; financial-risk decisions; provider selection; SIM activation; LIVE promotion |
| 1 | Accepted governance | Accepted ADRs; canonical contracts; security and financial-safety rules |
| 2 | Canonical main | Integrated source; integrated tests; accepted migrations; approved operational configuration contracts |
| 3 | Workstream contracts | Broker; signal-ingestion; persistence; integration interface contracts |
| 4 | Isolated specialist branches | TradeStation; Gmail; Database (and coordinator governance branches) |
| 5 | Specialist implementation evidence | Tests; verification artifacts; exact SHA/tree; PR review |
| 6 | Conversations and agent reasoning | Useful working context; never authoritative alone |

This hierarchy complements, and does not weaken, `docs/AGENT_AUTHORITY.md`
non-overridable safety prohibitions. While `docs/CURRENT_STATE.md` denies a
capability, Level 0 human instruction still cannot authorize that capability
through a side-channel that bypasses the conjunctive gates.

## Lane ownership

### Lane 1 — Integration / Coordinator

Owns:

- Workstream registry (`docs/WORKSTREAM_STATUS.md`)
- Dependency graph (`docs/WORKSTREAM_DEPENDENCIES.md`)
- Integration protocol (`docs/INTEGRATION_PROTOCOL.md`)
- Cross-lane contract reconciliation
- Canonical state updates after authorized integration
- PR integration proposals and merge readiness decisions (Operator remains sole
  acceptance authority for material gates)

Does not own:

- TradeStation feature implementation
- Gmail feature implementation
- Database infrastructure implementation
- Self-certification of specialist work followed by self-integration

### Lane 2 — TradeStation / Broker

Owns:

- TradeStation provider evidence
- Broker API adapter (when authorized)
- OAuth architecture for TradeStation (when authorized)
- SIM/LIVE safety boundary documentation and enforcement hooks (when authorized)
- Read-only account probes (only after explicit authorization)
- Broker order-state semantics research/implementation within scope
- Later SIM execution certification evidence (future phase)

Does not own:

- Canonical main integration
- Gmail ingestion
- Database provider selection acceptance

### Lane 3 — Gmail / Signal Ingestion

Owns:

- Gmail OAuth (when Operator-authorized)
- Read-only source adapter
- MIME acquisition
- Source provenance
- Corpus classification
- Sanitized fixtures
- Email grammar research
- `CanonicalInstructionEnvelope` production from email sources

Does not own:

- Broker order submission
- Canonical integration of other lanes
- Database host selection

### Lane 4 — Database / PostgreSQL Infrastructure

Owns:

- PostgreSQL infrastructure evidence and proposals
- Supabase provider suitability research (selection remains Operator)
- SQLAlchemy persistence compatibility
- Database isolation requirements
- Migration execution evidence
- Backup and restore requirements
- TokenStore PostgreSQL certification evidence

Does not own:

- Financial semantic contract acceptance
- Silent override of zero-incremental-cost constraint
- Credential storage in Git

Shared interfaces and financial semantics require Lane 1 review before
integration.

## Shared-file ownership (coordination-sensitive)

Specialists may update these when necessary for their lane, but overlapping
changes require explicit Lane 1 reconciliation. Lane 1 must not silently select
one conflicting specialist version.

Coordination-sensitive paths:

- `docs/CURRENT_STATE.md`
- `docs/ENGINEERING_JOURNAL.md`
- `docs/adr/`
- Canonical domain contracts under `docs/` (for example `BROKER_CONTRACT.md`,
  `TOKEN_STORE.md`, architecture and lifecycle contracts)
- Shared configuration under `config/`
- Shared dependency manifests (`pyproject.toml`, lockfiles if present)
- Database migrations under `migrations/`
- Shared CI workflows under `.github/`

Return `CROSS_WORKSTREAM_CONTRACT_CONFLICT` when human or architectural
resolution is required.

## Worktree isolation

Concurrently writing agents must use separate Git worktrees or isolated Cursor
Cloud checkouts.

Each lane must:

- Start from a proven canonical baseline SHA/tree
- Use its own branch
- Use its own working directory
- Avoid modifying another lane's branch
- Avoid shared uncommitted files across lanes
- Avoid force pushes
- Avoid automatic rebases after certification
- Avoid cross-lane cherry-picks without Lane 1 authorization

Existing specialist histories are preserved:

- PR #21 branch `cursor/p2-g4-gmail-readonly-gate-a-99c1`
- PR #22 branch `cursor/p2-ts-provider-evidence-99c1`

Do not recreate those branches merely to standardize naming.

### Branch naming

Historical and active Phase 2 branches often use `cursor/p2-<slug>` or
`cursor/phase2-<workstream-id>-<slug>` (`docs/PHASE_2_PLAN.md`). Preserve that
lineage.

For new four-lane branches, prefer:

- `cursor/ts-<gate>-<slug>`
- `cursor/gmail-<gate>-<slug>`
- `cursor/db-<gate>-<slug>`
- `cursor/integration-<gate>-<slug>`

Cloud-agent suffix conventions (for example `-8992`) remain allowed when the
environment requires them.

## Relationship to Phase 1 research roles

The Phase 1 research agents (broker/API, strategy/data, risk/operations) and
the governance coordinator remain valid for research-scoped work. The four-lane
model governs concurrent Phase 2 specialist implementation tracks. Lane 1 is
the only lane that may propose integration of certified specialist work into
canonical `main`.
