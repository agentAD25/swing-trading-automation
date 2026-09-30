# ADR-0002: Provider-neutral TokenStore

- Status: Proposed
- Date: 2026-09-30
- Sole Phase 1 decider: Human Operator
- Scope: C1/U-10 runtime mutable token state
- Supersedes: None
- Superseded by: None

## Context

Phase 1 accepted a broker-neutral, offline, deterministic baseline. Its data
model contains no credentials. `P2-0` carried conflict C1 (U-10): plan Gate
G1 had named Cursor Dashboard start-time secrets, while the authentication
proposal required a workload-writable compare-and-swap store.
`docs/TOKEN_STORE.md` at `e549ab9e59604abecce0c882c60f845f00f8be09` records
`C1_U10_PROPOSED_RESOLUTION` and remains **PROPOSED**.

The offline Group 2 foundation at
`904a362ac716aa8a7d3c9e830444a19108feed67`, tree
`4a6af24ebc82786a5d8c0e6d35f9744be14d9e14`, implements a local PostgreSQL
compare-and-swap path for synthetic fixture bytes. This ADR records the
architecture that path implements. It does not accept that architecture.
`docs/CURRENT_STATE.md` is unchanged, so its statement that H2 acceptance
remains open stays the current-state record.

Verified facts, inspected 2026-09-30:

- Cursor documents Dashboard secrets as values injected when an agent
  starts. That mechanism is not a workload-writable store. The citation is
  E15 in `docs/AUTH_ARCHITECTURE.md`, accessed 2026-09-29.
- Bootstrap static secrets and runtime mutable token state are separate
  classes in `docs/TOKEN_STORE.md` and `docs/AUTH_ARCHITECTURE.md`.
- `docs/SIM_CERTIFICATION.md` still requires an approved secret manager for
  issued credentials. That sentence stays on bootstrap static secrets.
- Phase 1 `docs/DATA_MODEL.md` still contains no credentials. The offline
  token table is not part of Phase 1 Alembic metadata.
- `docs/PHASE_2_PLAN.md` keeps persistence as Python → SQLAlchemy →
  PostgreSQL and provider-neutral. Supabase is **NOT_ACCEPTED**. RDS
  remains historical future-paid evidence. No AWS, Supabase, RDS, or
  Cloud SQL API is selected.
- The implementation at the commit above uses one conditional PostgreSQL
  update. It matches version, fence, state, environment, and owner, and
  sets version to the expected version plus one. Zero rows reject the
  stale writer. The same attempt is not retried. Ciphertext is empty or
  `fixture:` bytes. SIM cannot connect. LIVE initialization is denied.
  Dial targets outside localhost, `127.0.0.1`, and `::1` are refused.
  Host markers for TradeStation, Supabase, AWS, and Neon are refused.
  The module does not import Cursor or a cloud secret SDK.

Assumption: the human Operator has not accepted this ADR. This author
cannot accept it.

## Safety impact

`DRY_RUN` remains the only authorized execution mode. This record does not
authorize credentials, OAuth, token exchange, TradeStation `SIM`, order
submission, operational key management, provisioning, broker or account
activity, or `LIVE`. A denied capability stays unauthorized. This ADR
cannot override `docs/CURRENT_STATE.md` or the conjunctive promotion gates.

The intended fail-closed effects, if a later Operator decision accepts a
descendant of this proposal, are: production must not depend on Cursor;
bootstrap secrets stay outside the token row; runtime token state uses a
durable compare-and-swap store; an unavailable store blocks refresh and
broker requests; there is no fallback to Cursor, a file, an environment
variable, a cached refresh token, local PostgreSQL for SIM, or `LIVE`.

## Options considered

### Option A — Cursor as the runtime secret store

Use Dashboard start-time injection as the production token store.

Benefits: already an engineering-tool control for agent environments.
Costs and risks: secrets are injected at agent start; a running workload
cannot rotate or revoke through that mechanism. It is not a compare-and-swap
store and would make production depend on Cursor. Rejected by
`docs/TOKEN_STORE.md`.

### Option B — Provider-neutral durable compare-and-swap TokenStore

Keep Cursor as an engineering tool only. Hold bootstrap static secrets
outside the token row. Hold runtime mutable token state in a
provider-neutral durable compare-and-swap TokenStore. Treat the current
local PostgreSQL code as one implementation of that contract.

Benefits: matches the proposed C1 resolution and the passing offline
implementation. Ordinary PostgreSQL conditional update does not require a
vendor secret API. Costs and risks: host, key custody, retention, workload
identity, and lease duration remain Operator residuals. The offline code
is a DEV/TEST fixture store, not a SIM deployment.

### Option C — Bind the contract to Supabase, AWS, RDS, or Cloud SQL

Select one of those products as the TokenStore.

Benefits: none established for this decision. Costs and risks: current
state records Supabase as **NOT_ACCEPTED** and RDS as historical
future-paid evidence. A product binding would be a provider selection and
a Human Decision Gate 2 move. Rejected here.

## Decision

Proposed: Option B. Not Accepted.

Cursor is an engineering tool only. It is not the production secret store,
runtime TokenStore, runtime dependency, or broker credential authority.
Bootstrap static secrets are distinct from runtime mutable token state.
Mutable token state requires a provider-neutral durable compare-and-swap
TokenStore. The PostgreSQL implementation at
`904a362ac716aa8a7d3c9e830444a19108feed67` is one implementation of that
contract. It is not a permanent provider selection and not a Supabase,
AWS, RDS, or Cloud SQL dependency. Recording this proposal does not
authorize credentials, OAuth, TradeStation `SIM`, `LIVE`, or operational
key management.

`docs/TOKEN_STORE.md` stays **PROPOSED**. This ADR does not change that
status to Accepted. Only the human Operator can accept it, and that
acceptance is not recorded in this commit.

## Consequences

Positive, if later accepted: the Cursor-versus-CAS conflict has a single
recorded architecture; the offline PostgreSQL path is identified as one
implementation rather than a cloud selection.

Negative: availability is lost when the store is unavailable or the
compare-and-swap outcome is ambiguous. H2, the bootstrap injector, key
custody, retention, lease duration (U-11), and the SIM database host stay
open. `docs/CURRENT_STATE.md` still describes C1 as a proposed resolution
until a later evidence commit.

Operational: no schema migration, credential, network path, or runtime
change is created by this ADR. The offline table remains a local fixture
relation for DEV and TEST. SIM must not use that local instance.

## Validation and rollback

Acceptance evidence for a future Operator decision would be an explicit
record in `docs/CURRENT_STATE.md` plus this ADR moved to Accepted by the
Operator. This commit is not that evidence.

Failure signals: a production dependency on Cursor; bootstrap secret
material copied into the token row; a vendor SDK or host selection for
Supabase, AWS, RDS, or Cloud SQL; or any reading of this ADR as
credential, OAuth, SIM, LIVE, or key-management authority.

Rollback is supersession or removal of this document. No runtime, account,
or secret state is created here.

## Unresolved questions

Owned by the human Operator, not chosen here:

1. Accept or reject this proposal at H2.
2. Bootstrap injector for static secrets.
3. Workload identity and the auth-coordinator role mapping.
4. Encryption-key custody and rotation.
5. Retention, backup, and deletion of non-secret tombstones.
6. Lease TTL, clock skew, and refresh margin (U-11).
7. SIM database host at Human Decision Gate 2, including whether it is
   shared with the SIM ledger.

## Evidence

- Repository: `docs/TOKEN_STORE.md`, commit
  `e549ab9e59604abecce0c882c60f845f00f8be09`, inspected 2026-09-30.
  Supports `C1_U10_PROPOSED_RESOLUTION`: Cursor is not the production
  store; bootstrap secrets are separate; runtime state is a
  provider-neutral PostgreSQL compare-and-swap contract; no cloud API is
  selected. Limitation: status remains PROPOSED and is not Operator
  acceptance.
- Repository: `docs/AUTH_ARCHITECTURE.md` U-10 and E15, inspected
  2026-09-30. E15 cites Cursor, “Cloud Agents”,
  https://cursor.com/docs/cloud-agent, accessed 2026-09-29, for
  agent-start secret injection. Limitation: this ADR does not re-fetch
  that page; it relies on the citation already in that document.
- Repository: `docs/AGENT_AUTHORITY.md` and `docs/CURRENT_STATE.md`,
  inspected 2026-09-30. Supports DRY_RUN-only authority, sole Operator
  acceptance, and that C1 remains a proposed resolution with H2 open.
  Limitation: current state was not edited by this commit.
- Repository: `docs/DATA_MODEL.md` sensitive-data section and
  `docs/SIM_CERTIFICATION.md` secret-manager entry criterion, inspected
  2026-09-30. Supports no Phase 1 credentials, and an approved secret
  manager for future issued credentials. Limitation: neither document
  selects the TokenStore host.
- Repository: `docs/PHASE_2_PLAN.md` persistence row and
  `docs/PHASE_2_RECONCILIATION.md` C1 section, inspected 2026-09-30.
  Supports provider-neutral PostgreSQL and the proposed, unaccepted C1
  resolution. Limitation: historical H1 text still records the carried
  conflict; this ADR does not rewrite it.
- Repository implementation: `src/swingtrade/offline/token_store.py`,
  `src/swingtrade/offline/database.py`,
  `src/swingtrade/offline/environment.py`, and
  `src/swingtrade/contracts/secret_refs.py` at
  `904a362ac716aa8a7d3c9e830444a19108feed67`, inspected 2026-09-30.
  Supports one local PostgreSQL conditional update, synthetic fixture
  material, DEV/TEST-only connection, LIVE denial, and no Cursor or cloud
  secret SDK. Limitation: inspection of that tree, not a new test run;
  the offline store is not a SIM TokenStore and does not implement key
  custody.
