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

### Final validation evidence

Validation ran against pushed correction commit `f5e23a4`, followed by the
document-only review fixes included in the final validation commit:

- `git diff --check cursor/phase-1a-governance-e1ba...HEAD` and
  `git diff --check` passed.
- A Python 3 standard-library fixture procedure verified all four manifest
  SHA-256 values:
  - `bars.csv`:
    `e194cdef7ca448a8ceadb64d06699f35ef4c59da131786d7835099861df5e3bc`
  - `scenario.json`:
    `bd7af4205b9896bfd7fbe52bbf80ab0b4979c81116b2c8d8ce2520a49a91a501`
  - `expected-events.jsonl`:
    `9664c75e2e27bfdd39d40bc9aeaa7772cad21f799797e5a6be0ae611549a20bd`
  - `expected-report.json`:
    `e7255f12616beabdde6269501bf52d234c99e987e6f5ffd96605bc1fb39eeb99`
- The same procedure parsed every CSV/JSON/JSONL artifact; verified 19
  canonical, unique events and contiguous per-aggregate versions; recomputed
  all three idempotency keys from `scenario.json`; required each intent's four
  events and versions 1–4; recomputed the report content digest; tied the report
  digest and `evt_wdc_018` high-water mark to `report.generated.v1`; verified
  the shared non-account trade scope and `DRY_RUN — LOCAL NON-NETWORK`; and
  printed `P1D fixture: 4 manifest hashes, 19 canonical unique events,
  contiguous versions, 3 SHA-256 keys, 2 complete intent paths, report
  digest/HWM, non-account scope PASS`.
- The independently recomputed key digests were
  `c4131ccda4608e4604adf5f36a49265ccf5e57e4f1754f1b6ff2f2403f180b0f`
  (entry),
  `92949cf1b3481ce27b71360ccf67ae3580dc03d913088aee60fedefd5c2bbfa3`
  (exit), and
  `54b3b57426148284b3ca7f7423902f6218f7b2813dfd743ce4d6ee9d7a4e989f`
  (report). The recomputed report content digest was
  `96191e0646f7c2db231c44a3925eec620102ffeb94903f132f70338bf327c06b`.
- A Python Markdown procedure inspected 29 Markdown files and confirmed every
  relative target exists; it printed `Markdown links: 29 files, all relative
  targets PASS`.
- Authority assertions confirmed sole-Operator semantics, explicit
  `PHASE1_ACCEPTED` denial, `DRY_RUN` authorization, the non-overridable rule,
  concurrent `LIVE` prerequisites, one entry for each P1D-C01 through P1D-C04,
  and four instances of every required contradiction evidence field; they
  printed `Authority/acceptance/LIVE conjunction and P1D-C01..C04 audit fields
  PASS`.
- Searches excluding explicitly identified historical snapshots found no
  active stale `SIM`-only authorization. Diff-extension inspection found no
  implementation file. Sensitive-pattern inspection outside documentation and
  fixtures found no private-key marker, GitHub token pattern, or AWS access-key
  pattern. The procedure printed `scope, stale-active-SIM, sensitive-pattern,
  and whitespace assertions PASS`.
- An independent read-only cross-document review verified P1D-C01–P1D-C04 and
  found no substantive active safety contradiction. It identified stale
  current-state, ADR evidence, and test-plan wording; those three findings were
  corrected before final validation.
- Two early assertion-harness invocations failed on case-sensitive expected
  text (`Every` and bold `Sole`) even though the required text was present.
  They changed no fixture or contract. The assertions were corrected to test
  the intended semantics and the final fail-fast procedures above passed.

This evidence proves document/fixture/hash/link/safety-assertion conformance
only. It does not mark `PHASE1_ACCEPTED`, accept ADR-0001, authorize
implementation or connectivity, use credentials, begin Phase 1E or Phase 2,
or authorize `LIVE`.

## 2026-09-25 — Phase 1D surgical verifier remediation

### Authorized scope and pre-edit findings

Limited this pass to four verifier failures:

1. P1D-C02 intent transition events lacked required prior/next state, reason
   code, and explicit initiating cause even though lifecycle/event contracts
   required complete transition evidence.
2. `DECISIONS.md` declared one Operator decider but also said plural human
   owners accept material ADRs; ADR-0001 similarly said named humans review
   before acceptance.
3. `CURRENT_STATE.md` lacked an explicit 1A→1D history, Phase 1E status, and
   exact freeze-candidate identity/status.
4. `SIM_CERTIFICATION.md` prohibited credentials/account dependency in its
   future entry criteria even though authenticated TradeStation SIM
   certification may require controlled OAuth, SIM account/endpoint, query,
   and simulated order tests.

The requirements were mutually satisfiable, so `CONTRACT_CONFLICT` was not
triggered.

### Authority occurrence audit

Every repository occurrence returned by searches for `sole decider`, human
approval/direction/decision/decider/owner, `Operator`, `Accepted`, and
acceptance was inspected:

- **Canonical Phase 1 decision authority corrected:** `DECISIONS.md` status
  vocabulary, D-009, dependencies, and disposition;
  `AGENT_AUTHORITY.md` hierarchy and acceptance gate;
  `.cursor/rules/00-governance.mdc`; `CURRENT_STATE.md`; ADR-0001 metadata and
  decision; `docs/adr/README.md`; `docs/adr/ADR-TEMPLATE.md`;
  `PHASE_1D_CORRECTIONS.md`; the governance-coordinator role; and the
  architecture adapter gate now consistently identify the **human Operator as
  sole Phase 1 decider**.
- **Future LIVE authority preserved:** `LIVE_PROMOTION.md` keeps independent
  technical/risk/security/compliance/operations attestations as mandatory
  evidence, not additional Phase 1 deciders, and keeps the human Operator's
  final explicit bounded authorization plus every conjunctive gate.
  `SIM_LIVE_BOUNDARY.md` remains aligned.
- **Operational ownership is not acceptance authority:** owner/waiver language
  in reconciliation, metrics, architecture unknowns, and future SIM
  certification remains responsibility or evidence language, not a Phase 1
  acceptance path.
- **Historical evidence preserved:** prior journal entries,
  `PHASE_1C_RECONCILIATION.md`, `FAILURE_MODEL.md`, and
  `BROKER_CONTRACT.md` retain point-in-time human/authority wording and do not
  control current authority.
- **Non-authority uses:** lifecycle “acceptance” means broker order acceptance;
  broker research uses API acceptance semantics; test “acceptance” means test
  criteria. These were inspected and left unchanged.

### Changes

- Added complete transition payload evidence to all eight fixture intent
  events without weakening lifecycle or event contracts.
- Added `tests/validate_phase1_contracts.py`, which validates the fixture and
  negatively mutates each of `prior_state`, `next_state`, and `reason_code` to
  prove omission is rejected.
- Reconciled sole-human-Operator wording across canonical authority artifacts.
- Added phase history/current-candidate semantics to current state.
- Split current SIM prohibition from future explicitly authorized,
  authenticated TradeStation SIM certification requirements.

No credential, account, broker connection, query, order, Phase 1E/2, freeze,
certification, acceptance, or `LIVE` action occurred.

### Validation

Pending against the pushed surgical freeze-candidate commit. Exact commands,
hashes, and results will be appended in a follow-up evidence commit.

### Surgical candidate validation evidence

Validated pushed freeze candidate
`42ac8cd2e879732e456a7ed452510e7f5434a03e` without credentials, accounts,
broker/network access, queries, or orders.

1. Command:

   ```sh
   python3 tests/validate_phase1_contracts.py
   ```

   Result:

   ```text
   Phase 1 contracts: manifest, C01, C02, C03 PASS; required-field omission regression PASS
   ```

   The validator checked all four manifest hashes; canonical event structure;
   both four-event intent paths; all transition payload/envelope fields;
   continuity of state, causation, initiating cause, correlation, and aggregate
   sequence; C01 idempotency keys; and C03 report digest/high-water mark. Its
   negative regression removed `prior_state`, `next_state`, and `reason_code`
   one at a time and required `ContractError` for each omission.

2. Command:

   ```sh
   sha256sum tests/fixtures/wdc-reference/expected-events.jsonl \
     tests/fixtures/wdc-reference/scenario.json \
     tests/fixtures/wdc-reference/expected-report.json \
     tests/fixtures/wdc-reference/bars.csv
   ```

   Result:

   ```text
   cda0fb3d537ca0df9330795f49b8743f4736650ce81cc457276dcb3b006b727d  expected-events.jsonl
   bd7af4205b9896bfd7fbe52bbf80ab0b4979c81116b2c8d8ce2520a49a91a501  scenario.json
   e7255f12616beabdde6269501bf52d234c99e987e6f5ffd96605bc1fb39eeb99  expected-report.json
   e194cdef7ca448a8ceadb64d06699f35ef4c59da131786d7835099861df5e3bc  bars.csv
   ```

3. A separate Python 3 recomputation printed and matched:

   ```text
   entry_dispatch c4131ccda4608e4604adf5f36a49265ccf5e57e4f1754f1b6ff2f2403f180b0f
   exit_dispatch 92949cf1b3481ce27b71360ccf67ae3580dc03d913088aee60fedefd5c2bbfa3
   report 54b3b57426148284b3ca7f7423902f6218f7b2813dfd743ce4d6ee9d7a4e989f
   report_content 96191e0646f7c2db231c44a3925eec620102ffeb94903f132f70338bf327c06b
   manifest, C01 idempotency inputs, and C03 report digest: PASS
   ```

4. A Python Markdown-link procedure iterated
   `docs/**/*.md`, `tests/**/*.md`, `README.md`, and `config/README.md`,
   resolved every non-HTTP target relative to its source, asserted existence,
   and printed:

   ```text
   relative Markdown links (29 files): PASS
   ```

5. Commands:

   ```sh
   git diff --check cursor/phase-1a-governance-e1ba...HEAD
   git status --porcelain | test ! -s /dev/stdin
   ```

   Result:

   ```text
   whitespace and clean Git candidate: PASS
   ```

6. Fail-fast Python assertions inspected the canonical authority files listed
   above, future LIVE promotion, SIM certification, and current-state history.
   `rg` assertions excluded identified historical snapshots and rejected the
   removed plural acceptance phrases and stale active SIM authority. Results:

   ```text
   sole-human-Operator, future-LIVE, SIM temporal, phase-history, and no-acceptance assertions: PASS
   canonical conflict and DRY_RUN regressions: PASS
   ```

   One earlier harness assertion compared an unnormalized line-wrapped current
   state phrase and failed even though the words were present. It changed no
   artifact. The final fail-fast assertion normalized whitespace and passed.

Current state records candidate `42ac8cd2e879732e456a7ed452510e7f5434a03e`.
The evidence commit containing this journal entry is not a replacement
freeze candidate and grants no acceptance or authority. Phase 1E and Phase 2
remain not started; `LIVE` remains unauthorized.

## 2026-09-25 — Candidate provenance and WDC reconciliation remediation

### Surgical scope and pre-edit audit

This single pass is limited to:

1. freeze-candidate identity/provenance; and
2. the WDC source-event/report reconciliation conflict.

Pre-edit files inspected were `CURRENT_STATE.md`, `ENGINEERING_JOURNAL.md`,
`EVENT_MODEL.md`, `RECONCILIATION.md`, `REPORTING.md`, `TEST_PLAN.md`,
`tests/validate_phase1_contracts.py`, and all WDC scenario/event/report/manifest
artifacts.

### Candidate ancestry, completeness, and stale identity

Commands:

```sh
git rev-parse 42ac8cd^{tree}
git rev-parse d459850^{tree}
git merge-base --is-ancestor 42ac8cd d459850
git log --oneline --ancestry-path 42ac8cd..d459850
git diff --name-status 42ac8cd..d459850
git log --format='%H %T %s' 42ac8cd^..d459850
```

Evidence:

- `42ac8cd2e879732e456a7ed452510e7f5434a03e` has tree
  `3ed2b143d5dd0f06a62c0080323142c03da3b7f8`.
- `merge-base --is-ancestor` exited 0, proving `42ac8cd` is an ancestor of
  `d459850`.
- Descendants were `3cbfcaf` (validation evidence) and `d459850` (future
  sign-off authority clarification).
- `d45985023cdfd60f5af9fb3226c483394fd2bb27` has tree
  `873246382a7fb83051fc9e0e90c2681fa481b117`.
- The descendant range changed `CURRENT_STATE.md`, `DECISIONS.md`,
  `ENGINEERING_JOURNAL.md`, `LIVE_PROMOTION.md`, and
  `SIM_CERTIFICATION.md`. Four are normative state/decision/safety contracts.

Therefore the current-state pointer to `42ac8cd` was stale and incomplete for
the normative head. It was true historical provenance, not a complete current
candidate. No history was rewritten or fabricated.

The replacement mechanism is: commit the complete candidate tree first; then
use a descendant evidence-only commit to record the candidate commit/tree,
ancestry, normative diff scope, hashes, and tests. The evidence commit is not
part of the candidate. Any later normative delta invalidates that identity.
This is coherent because it never attempts to embed a commit hash in the tree
that creates the same hash.

### Reconciliation classification

Classification: **`REPORT_OVERCLAIMS_EVIDENCE`**.

Evidence:

- The source ledger through `evt_wdc_018` contains decisions, risk results,
  intent transitions, fills, and `trade.closed.v1`, but no
  `reconciliation.check_completed.v1`.
- `expected-report.json` nevertheless claimed
  `reconciliation_result=PASS`.
- `evt_wdc_019` likewise used `report.generated.v1` and claimed `PASS`.
- `EVENT_MODEL.md` names reconciliation completion as a source event;
  `RECONCILIATION.md` requires checks at finalization; `ARCHITECTURE.md`
  permits report finalization only after required reconciliation checks pass;
  and `REPORTING.md` requires an unreconciled preliminary marker when final
  evidence is unavailable.

`SOURCE_EVENT_MISSING` is not selected because no independent artifact proves
that a reconciliation check actually ran or that a completion event was
constructed and lost. Adding one would fabricate history.
`CONTRACT_CONFLICT` is not selected because `REPORTING.md` already supports the
weaker `UNRECONCILED — DO NOT USE FOR EXECUTION` state. `OTHER` is therefore
unnecessary.

### Contract-supported resolution and expected result

- Define qualifying durable completion evidence precisely.
- Require report `PASS` to derive from that event at the report high-water
  mark.
- Change the WDC report to `UNRECONCILED`, emit `report.withheld.v1`, preserve
  the event history, and recompute report/manifest digests.
- Add a negative regression proving no qualifying completion evidence can
  yield `PASS`.
- Add a positive regression proving a complete valid reconciliation event can
  derive `PASS`.
- Preserve all prior C01–C04, DRY_RUN, idempotency, SIM/LIVE, link, and
  cleanliness checks.

No freeze, acceptance, Phase 1E/2, credential, broker connection, query, order,
or `LIVE` activity is authorized or performed.

### Validation

Pending against the replacement candidate commit/tree. Exact results and the
immutable candidate identity will be recorded by its descendant evidence-only
commit.

### Replacement candidate identity and validation results

The complete replacement candidate is:

- commit:
  `abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`;
- exact Git tree:
  `cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`;
- parent chain:
  `abc1fb6` → `3f7c22a` → `d459850` → `3cbfcaf` → `42ac8cd`;
- base target: `cursor/phase-1a-governance-e1ba`.

The candidate is complete because both
`git merge-base --is-ancestor 42ac8cd abc1fb6` and
`git merge-base --is-ancestor d459850 abc1fb6` exited 0. The normative delta
from `d459850` is exactly the following 11 files:

```text
docs/CURRENT_STATE.md
docs/ENGINEERING_JOURNAL.md
docs/EVENT_MODEL.md
docs/RECONCILIATION.md
docs/REPORTING.md
docs/TEST_PLAN.md
tests/fixtures/wdc-reference/README.md
tests/fixtures/wdc-reference/expected-events.jsonl
tests/fixtures/wdc-reference/expected-report.json
tests/fixtures/wdc-reference/manifest.json
tests/validate_phase1_contracts.py
```

This descendant evidence commit updates only current state and this append-only
journal. It attests the candidate but is not part of candidate tree
`cb5fc1f9...`. Its own SHA cannot coherently be embedded in its own tree; the
full pushed evidence-commit SHA is returned by Git/PR metadata. Any later
normative change invalidates the candidate under the recorded mechanism.

#### Exact regression command

```sh
python3 tests/validate_phase1_contracts.py
```

Result:

```text
Phase 1 contracts: manifest, C01, C02, C03, C04 PASS; required-field omission regression PASS; reconciliation evidence negative/positive regressions PASS
```

The reconciliation negative test proves a source ledger with no qualifying
`reconciliation.check_completed.v1` cannot yield report `PASS`. The positive
test supplies a complete in-memory source event with same-run identity,
checked-through causation, all required checks, and zero open critical/high
discrepancies, and proves that evidence derives `PASS`. It does not append that
synthetic regression event to WDC history.

#### Event → derivation → report → digest evidence

The persisted WDC source ledger contains no reconciliation completion event.
Derivation therefore returns `UNRECONCILED`; `expected-report.json` records
that value and the mandatory warning; `evt_wdc_019` is
`report.withheld.v1` with the same value, source high-water mark, reason, and
content digest.

Recomputed hashes:

```text
bars.csv             e194cdef7ca448a8ceadb64d06699f35ef4c59da131786d7835099861df5e3bc
scenario.json         bd7af4205b9896bfd7fbe52bbf80ab0b4979c81116b2c8d8ce2520a49a91a501
expected-events.jsonl 7b50e2475326283832df77a23e03b6e46e97eaf98342c88cd9dbdcc332e6447a
expected-report.json  95585e7b1ba762a95719a154b02b5c06eeea5b1ff9e1428b80bb36e3ebdd909c
report content digest f9a969c5f151133bad5d14f39a7cd17fafb033f9da87a1b5d8f53de04b2b3f46
```

C01 idempotency digests remained:

```text
entry  c4131ccda4608e4604adf5f36a49265ccf5e57e4f1754f1b6ff2f2403f180b0f
exit   92949cf1b3481ce27b71360ccf67ae3580dc03d913088aee60fedefd5c2bbfa3
report 54b3b57426148284b3ca7f7423902f6218f7b2813dfd743ce4d6ee9d7a4e989f
```

Additional exact checks and results:

- `git diff --check cursor/phase-1a-governance-e1ba...abc1fb6` — exit 0.
- `git status --porcelain | test ! -s /dev/stdin` — exit 0.
- relative-link Python procedure over 29 Markdown files —
  `relative Markdown links (29 files): PASS`.
- active-authority `rg` checks found no stale SIM authorization.
- WDC `rg` checks found no persisted report/reconciliation `PASS` claim.
- independent hash assertions printed
  `C01/C03, manifest hashes, event→report→digest, and no-overclaim semantics:
  PASS`.
- contract assertions printed
  `candidate mechanism, root-cause classification, contracts, and phase
  denials: PASS`.
- safety/semantic assertions printed
  `links, DRY_RUN/SIM-LIVE, and WDC no-overclaim regressions: PASS`.

These results validate a replacement freeze candidate only. The candidate is
not frozen, certified, or `PHASE1_ACCEPTED`; Phase 1E and Phase 2 remain not
started; credentials, broker connectivity, queries, and orders were not used;
and `LIVE` remains unauthorized.

## 2026-09-25 — Bounded Phase 1 acceptance metadata

### Acceptance evidence

The human Operator reported that independent verification **PASSED**:

- candidate commit:
  `abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`;
- candidate tree:
  `cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`; and
- evidence head:
  `b3291a030b165315846b6703805afe9d28120bd8`.

The verifier was identified as the independent verifier by the human Operator;
no personal or service identifier was supplied, so none is invented here.

The Operator records `PHASE1_ACCEPTED` as evidence-only metadata for that exact
candidate/tree. Acceptance is bounded to the broker-neutral, offline,
deterministic baseline and local non-network `DRY_RUN`. It does not authorize
implementation, Phase 1E, Phase 2, credentials/OAuth, accounts, broker
connectivity, TradeStation `SIM`, queries, confirmations, orders,
replace/cancel, streams, deployment, real capital, or `LIVE`.

### Candidate tag and immutable reference

The repository had no existing tags or tag naming convention. Created the
candidate-specific annotated tag `phase1-accepted-abc1fb6`, with tag object
`197d22b06cf6a96bad8c4b1a49ad1b928b147ac0`. A candidate-specific name avoids
the ambiguity of a moving `phase1-accepted` alias. The tag must never be moved
or recreated; a later accepted candidate requires a new tag.

Commands and results:

```sh
git cat-file -t phase1-accepted-abc1fb6
# tag
git rev-parse phase1-accepted-abc1fb6^{commit}
# abc1fb6a9cc3554e7ad13f438685ba3c3c044dab
git rev-parse phase1-accepted-abc1fb6^{tree}
# cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808
```

The tag points to the accepted candidate, not this later metadata commit, so
the accepted tree remains byte-for-byte unchanged and self-reference is
avoided.

### Acceptance manifest

Added `docs/PHASE_1_ACCEPTANCE_MANIFEST.md` as evidence metadata outside the
accepted tree. It records:

- the exact candidate/tree/evidence head/tag/tag object;
- verifier identity limitation and `PASSED` result;
- bounded meaning and explicit non-authorizations;
- an atomic 45-file candidate inventory with every Git blob OID and independent
  SHA-256;
- exact validation commands/results;
- root cause `REPORT_OVERCLAIMS_EVIDENCE`;
- stable fixture, report, and idempotency digests;
- all twelve unresolved TradeStation behavior groups; and
- deferred empirical questions and human decisions.

Inventory commands:

```sh
git ls-tree -r abc1fb6 | wc -l
# 45
git ls-tree -r abc1fb6
```

The manifest does not resolve any broker unknown or modify any accepted
contract, test, fixture, or source artifact.

### Acceptance metadata validation

Pending after committing the three authorized metadata files only:
`CURRENT_STATE.md`, `ENGINEERING_JOURNAL.md`, and
`PHASE_1_ACCEPTANCE_MANIFEST.md`. Validation will prove the diff scope, tag
target/tree, 45-file inventory, stable hashes, links, candidate tests, and clean
Git state before handoff.
