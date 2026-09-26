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

### Acceptance metadata validation results

Metadata commit `402a4fb` and the annotated tag were pushed before validation.

1. Tag verification:

   ```sh
   git cat-file -t phase1-accepted-abc1fb6
   git rev-parse phase1-accepted-abc1fb6^{commit}
   git rev-parse phase1-accepted-abc1fb6^{tree}
   git ls-remote origin refs/tags/phase1-accepted-abc1fb6 \
     'refs/tags/phase1-accepted-abc1fb6^{}'
   ```

   Result:

   ```text
   tag
   abc1fb6a9cc3554e7ad13f438685ba3c3c044dab
   cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808
   197d22b06cf6a96bad8c4b1a49ad1b928b147ac0 refs/tags/phase1-accepted-abc1fb6
   abc1fb6a9cc3554e7ad13f438685ba3c3c044dab refs/tags/phase1-accepted-abc1fb6^{}
   local/remote annotated tag resolves exactly to accepted candidate/tree: PASS
   ```

2. A Python procedure parsed all 45 manifest rows, compared their paths/blob
   OIDs to `git ls-tree -r abc1fb6`, read every candidate blob, recomputed every
   SHA-256, checked set equality, and printed:

   ```text
   atomic 45-file candidate inventory, blob OIDs, and SHA-256 values: PASS
   ```

3. Exact accepted-tree and scope checks:

   ```sh
   python3 tests/validate_phase1_contracts.py
   git rev-parse abc1fb6^{tree}
   git diff --name-only abc1fb6..HEAD
   git diff --exit-code abc1fb6 -- <all non-metadata paths>
   ```

   Result:

   ```text
   Phase 1 contracts: manifest, C01, C02, C03, C04 PASS; required-field omission regression PASS; reconciliation evidence negative/positive regressions PASS
   accepted tree unchanged; metadata-only three-file delta; regressions PASS
   ```

   The only paths changed after the accepted candidate were
   `docs/CURRENT_STATE.md`, `docs/ENGINEERING_JOURNAL.md`, and
   `docs/PHASE_1_ACCEPTANCE_MANIFEST.md`.

4. A link/status procedure verified all relative links in 30 Markdown files,
   all 12 unresolved broker groups, exact candidate/tree/evidence identities,
   `REPORT_OVERCLAIMS_EVIDENCE`, bounded meaning, and Phase 1E/2,
   TradeStation SIM, and LIVE non-authorizations. Result:

   ```text
   links (30 Markdown files), 12 unresolved groups, bounded acceptance/non-authorizations: PASS
   ```

5. Commands:

   ```sh
   git diff --check cursor/phase-1a-governance-e1ba...HEAD
   git status --porcelain | test ! -s /dev/stdin
   ```

   Result:

   ```text
   whitespace and clean Git metadata head: PASS
   ```

These checks establish only immutable evidence metadata for the accepted
offline baseline. They do not alter the accepted tree, resolve any deferred
question, authorize implementation or later phases, or permit broker/LIVE
activity.

## 2026-09-25 — Phase 1E bounded remediation baseline

### Human authorization and immutable baseline

The human Operator authorized one surgical remediation on draft PR #6,
strictly limited to P1E-01 through P1E-05. This is valid implementation
authority for that bounded local offline work only. It does not authorize
Phase 2, broker access, credentials/OAuth, account access, TradeStation `SIM`,
queries, confirmations, order actions, deployment, real capital, or `LIVE`.

The immutable accepted reference remains:

```text
commit  abc1fb6a9cc3554e7ad13f438685ba3c3c044dab
tree    cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808
tag     phase1-accepted-abc1fb6
files   45
```

Phase 1D is closed. Phase 1E does not rewrite that accepted commit, tree, tag,
manifest, contracts, fixture bytes, governance, or broker research.

### Pre-edit record

The remediation began from clean pushed branch
`cursor/phase-1e-foundation-1b77` at
`70346f3459efa20c20d6f0d33c82f6254052b1c0`, merge base
`e06b5b26fba5ae1f9283f5bffb676d40332fe297`, on Python `3.12.3`.
Docker and PostgreSQL executables were initially absent. Baseline commands
returned 35 passing strict tests, contract-validator PASS, Ruff PASS, and mypy
PASS over 11 source files. The P1E findings were missing assurance rather than
pre-existing test failures:

- P1E-01 lacked durable atomic canonical-intent creation and engine-backed
  concurrency/reconnect evidence.
- P1E-02 checked only a subset of required reconciliation evidence.
- P1E-03 did not explicitly enforce every calendar cardinality/order invariant.
- P1E-04 did not enforce transition event types or nondecreasing event times.
- P1E-05 status text still said Phase 1E was unauthorized and unstarted.

Expected edits were limited to `src/swingtrade/persistence.py`,
`src/swingtrade/reconciliation.py`, `src/swingtrade/state_machine.py`,
`src/swingtrade/wdc.py`, a new Alembic revision, adversarial tests under the
already authorized offline test directories, and status/evidence updates to
`docs/CURRENT_STATE.md` and this journal. No accepted fixture or contract file
was an expected edit.

### Remediation and verification evidence

P1E-01 now stores one canonical intent payload and SHA-256 input digest behind
PostgreSQL unique constraints on idempotency key and intent id. Creation uses
one transaction with `INSERT ... ON CONFLICT DO NOTHING`, then compares the
durable row to the requested canonical identity. Identical requests converge;
key or intent-id reuse with different content raises a conflict and rolls back.
Engine-backed tests cover repeated creation, mixed concurrent creators,
single-row convergence, conflict rollback, pool disposal, persistence, and
reconnect.

P1E-02 validates the complete reconciliation completion envelope and payload,
same-run earlier checked event, exact required-check set, aggregate sequence,
causation, zero critical/high discrepancies, and identical-versus-conflicting
duplicate evidence. Missing, partial, contradictory, duplicate-conflicting, or
wrong-run evidence derives only `UNRECONCILED`; repeated identical evidence
and repeated derivation are idempotent.

P1E-03 requires exact session cardinality, unique strictly ascending calendar
sessions, and ordered equality with bars. Tests cover unsorted, duplicate,
cardinality mismatch, weekend/holiday gaps defined only by the supplied
calendar, prior/next-session selection, intraday non-trigger, and deterministic
replay. No weekday or holiday policy was invented.

P1E-04 enforces the accepted event type/state sequence, contiguous aggregate
versions, immediate causation, stable initiating identity, and nondecreasing
effective and recorded times without collapsing those distinct timestamps.
Tests cover equal times, backward times, microsecond-separated rapid events,
multi-transition chains, identical replay, and contradictory replay.

The environment initially lacked Docker and PostgreSQL. A local-only
PostgreSQL package was installed for verification; no broker or external
service was contacted by the implementation or tests. The actual engine was:

```text
PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) on x86_64-pc-linux-gnu,
compiled by gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, 64-bit
```

The first PostgreSQL-backed suite exposed three row-materialization failures;
after correction it exposed one test-only unhashable assertion. Both were
corrected before final verification. Final results:

```text
SWINGTRADE_TEST_POSTGRES_URL=postgresql+psycopg://.../swingtrade_test \
  python3 -m pytest -W error
62 passed in 0.65s

python3 tests/validate_phase1_contracts.py
Phase 1 contracts: manifest, C01, C02, C03, C04 PASS; required-field
omission regression PASS; reconciliation evidence negative/positive
regressions PASS

python3 -m ruff check .
All checks passed!

python3 -m mypy src
Success: no issues found in 11 source files
```

Alembic offline SQL rendering passed through revisions 0001 and 0002. Against
the actual PostgreSQL engine, downgrade-to-base removed the foundation tables,
upgrade-to-head recreated all four foundation tables plus Alembic metadata,
and rollback/upgrade completed successfully. Compile/import checks passed.
Secret, credential, broker-network, and live-order-path scans returned no
matches.

The annotated tag still resolves to tag object
`197d22b06cf6a96bad8c4b1a49ad1b928b147ac0`, accepted commit
`abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`, and tree
`cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`. Its 45 paths remain unchanged;
only the two explicitly authorized status/evidence files among those paths
changed on the Phase 1E descendant branch. This is implementation evidence,
not self-certification. Phase 2 and all broker/SIM/LIVE capabilities remain
unstarted and unauthorized.

## 2026-09-26 — P1E-F01/F02/F03 bounded follow-up pre-edit record

The authorized follow-up starts from clean remote head
`622a20f965e265707d0197d72f92c7133387d724`, tree
`b04d7edfe8c579c1bfc8faaf3fb4a0870de0ea91`. The immutable accepted reference
remains commit `abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`, tree
`cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`, annotated tag
`phase1-accepted-abc1fb6`, and its exact 45-file inventory.

Pre-edit inspection found:

- `PostgresIntentRepository.create_or_get` trusted the supplied idempotency key
  and persisted it without recomputing the accepted dispatch key. The accepted
  canonical dispatch input is the fixture-bound object containing
  `decision_id`, `intent_id`, `mode`, decimal-string `quantity`, and `side`;
  the existing primitive is
  `idempotency_key("dispatch", intent_id, canonical_input)`.
- `DryRunAdapter` defaulted to `InMemoryIdempotencyStore`; the active dispatch
  path therefore did not require durable PostgreSQL identity and could split
  authority between process-local and durable stores.
- Reconciliation already required a completion event at the report high-water
  mark, same-run earlier checked event, exact required checks, zero critical or
  high discrepancies, immediate checked-event causation, contiguous
  reconciliation aggregate versions, and conflict-safe duplicate event ids.
  Its timestamp parser nevertheless accepted noncanonical fractional
  precision, and checked-event envelope, correlation, aggregate, and temporal
  relationships were not fully validated.

The contracts are coherent for this bounded work. `IDEMPOTENCY.md` requires
canonical business-input-derived keys and durable uniqueness;
`RECONCILIATION.md` requires the checked-through relation and canonical event
envelope; `EVENT_MODEL.md` permits late effective facts generally, while a
qualifying reconciliation completion can still be required not to precede the
specific checkpoint it claims to cover. No `CONTRACT_CONFLICT` is present.

Expected changed files are limited to
`src/swingtrade/persistence.py`, `src/swingtrade/broker.py`,
`src/swingtrade/reconciliation.py`,
`tests/integration/test_postgres_intent_identity.py`,
`tests/broker_sim/test_dry_run_adapter.py`,
`tests/reconciliation/test_evidence.py`, and this evidence journal. No
contract, accepted fixture, acceptance manifest, calendar/WDC implementation,
event-state implementation, status, migration, broker-network, SIM, or LIVE
file is expected to change.

### P1E-F01/F02/F03 implementation and verification evidence

The implementation candidate before this evidence-only journal update is
commit `b06faad0c54b5d83cc3919992b9bef1afdbf37e5`, tree
`96b6b281988f5c0fdfea3d20d61df2118cd1a4f6`. It descends from the authorized
starting head through three ordinary commits; no history was amended, rebased,
squashed, cherry-picked, or force-pushed.

P1E-F01 centralizes the accepted dispatch business input and derives its key
with the existing `idempotency_key` primitive at
`PostgresIntentRepository.create_or_get`. A supplied mismatch raises the typed
`NonCanonicalIntentKey` before a transaction. Durable rows are independently
re-derived and malformed or noncanonical rows fail closed. Tests cover every
key field, forged direct and concurrent calls, changed economic content,
identical replay, malformed durable JSON, conflict rollback, cardinality, and
reconnect.

P1E-F02 removes `InMemoryIdempotencyStore` from `DryRunAdapter` and requires an
explicit `PostgresIntentRepository`. Authorization runs before persistence;
the repository transaction atomically creates or returns both canonical intent
identity and the original local observation. Replay after reconnect returns
the durable original observation even when the new adapter clock differs.
Missing repositories, malformed observations, authorization denial, identity
conflict, and retry all fail closed. DRY_RUN remains local and non-network.

Adversarial review showed that durable original-observation replay could not be
met by the initially expected files alone. Migration
`0003_durable_dry_run_observation` was therefore the minimum necessary F02
change: it adds one nullable JSON column so pre-existing rows remain
migratable; authoritative dispatch requires a canonical value and fails closed
on a legacy null. No accepted contract or fixture was changed.

P1E-F03 now requires complete canonical envelopes for both checkpoint and
completion, exact UTC six-digit-microsecond strings, positive non-boolean
schema/aggregate versions, exact integer discrepancy counts, same-run and
same-correlation linkage, immediate checked-event causation, an earlier
checked event, run-level nondecreasing `recorded_at`, per-event
`recorded_at >= effective_at`, exact checks, zero high/critical discrepancies,
and contiguous reconciliation aggregate versions. Conflicting duplicates fail
closed. The contract expressly permits late effective facts, so no invalid
global monotonic-effective-time rule was added; a valid late-effective matrix
case proves that boundary.

Fresh verification used:

```text
PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) on x86_64-pc-linux-gnu,
compiled by gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, 64-bit

SWINGTRADE_TEST_POSTGRES_URL=postgresql+psycopg://.../swingtrade_test \
  python3 -m pytest -W error
109 passed in 1.37s (shell elapsed 1.646s)

P1E-F01 targeted: 22 passed in 0.78s (elapsed 1.028s)
P1E-F02 targeted: 12 passed in 0.57s (elapsed 0.811s)
P1E-F03 targeted: 43 passed in 0.09s (elapsed 0.279s)
unchanged WDC/state/domain/fail-closed/idempotency/schema regressions:
32 passed in 0.38s
```

The contract validator passed manifest and C01–C04 plus omission and
reconciliation regressions. Ruff passed; strict mypy reported no issues in 11
source files; compile/import checks passed. Alembic downgrade-to-base and
upgrade-to-head passed online on PostgreSQL through revisions 0001, 0002, and
0003; head is `0003_durable_dry_run_observation`. Offline SQL rendered all
three revisions in 57 lines.

Runtime network-import, credential/secret-literal, and
broker-network/LIVE-order-path scans returned zero matches. Strict Git object,
whitespace, ancestry, and clean-worktree checks passed before this evidence
append. The immutable tag still resolves to object
`197d22b06cf6a96bad8c4b1a49ad1b928b147ac0`, accepted commit
`abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`, and tree
`cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`; all 45 manifest blob OIDs and
SHA-256 values matched.

This is bounded implementation and test evidence for independent verification,
not self-certification. It does not start Phase 2 or authorize credentials,
broker access, TradeStation SIM, order activity, deployment, real capital, or
LIVE.

## 2026-09-26 — P1E-F04/F05 final micro-remediation pre-edit record

This single micro-remediation starts from fetched local/remote/PR head
`c5851471a26c89283469176fd76103dba253c971`, tree
`97d44c46b344bc65c41e1325388a255526b6f9bb`, with a clean worktree. The
immutable accepted reference remains annotated tag object
`197d22b06cf6a96bad8c4b1a49ad1b928b147ac0`, commit
`abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`, tree
`cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`, and 45 files. The prior
F01–F03 verifier evidence records PostgreSQL 16.15, 109 warnings-strict tests,
22/12/43 targeted F01/F02/F03 tests, contract-validator/Ruff/mypy/Alembic
passes, zero prohibited scan matches, and readiness only for independent
verification.

Pre-edit inspection found:

- Dispatch key input, durable canonical intent, and durable observation each
  serialized `Decimal` with separate `str()` calls. Python preserves Decimal
  scale in those strings, so economically equal `2`, `2.0`, and `2.00` could
  produce different payloads, digests, and keys.
- `PostgresIntentRepository.create_or_get` remains the authoritative direct
  key-verification boundary. Existing durable rows are checked rather than
  rewritten, but a row whose quantity and key were consistently generated
  with the old scale-sensitive representation was not identified as stale.
- Reconciliation deduplicated global event IDs and required only the
  completion reconciliation stream to have versions `1..N`. It did not apply
  ledger-integrity sequencing to every relevant same-run stream or explicitly
  reject two different event IDs occupying one stream/version coordinate.
- `EVENT_MODEL.md` defines ordered aggregate streams and globally unique event
  IDs; `DATA_MODEL.md` requires uniqueness of
  `(aggregate_type, aggregate_id, aggregate_version)`; the accepted validator
  and fixture establish the initial aggregate version as exactly `1` and
  contiguous increments thereafter. Canonical decimal strings, no binary
  float, and no implicit rounding are already required. These rules are
  coherent; no `CONTRACT_CONFLICT` or scope violation is present.

Expected edits are limited to `src/swingtrade/persistence.py`,
`src/swingtrade/reconciliation.py`,
`tests/integration/test_postgres_intent_identity.py`,
`tests/reconciliation/test_evidence.py`, and this journal. No contract,
migration, accepted fixture/manifest, WDC/calendar, state-machine, safety,
adapter, status, broker-network, SIM, LIVE, or Phase 2 file is expected to
change.

### P1E-F04/F05 implementation and verification evidence

The implementation candidate before this evidence-only update is commit
`71d3176887caa3ccadea647004f9badc593dbd86`, tree
`38ca232390190cba37274332cf679619fff29b47`. It contains two ordinary
fast-forward commits from the recorded start; no history was rewritten.

P1E-F04 introduces one fixed-notation `canonical_decimal` representation and
one `canonical_economic_intent` materialization. The repository materializes
that economic object once, then uses it for the supplied-key check, canonical
payload, digest, and durable observation. No float, locale, quantization,
rounding, or scientific-format conversion participates. Scale-equivalent
positive values, zero variants, and supported negative Decimal values collapse
to one string; nearby unequal values remain distinct.

The PostgreSQL boundary still verifies every supplied key directly before
persistence and independently re-derives durable rows. A legacy
scale-sensitive supplied key fails before a transaction. A stale durable row
whose payload and key consistently contain the old scaled quantity is reported
with typed `NonCanonicalIntentKey`; it is neither aliased nor rewritten.
PostgreSQL tests cover scaled replay, 24 concurrent equivalent-scale calls,
different economic values, reconnect using a scale variant, direct invocation,
forged legacy keys, stale rows, durable cardinality, and all prior F01/F02
cases.

P1E-F05 fixes the accepted initial aggregate version at `1`, as established by
the accepted validator/fixture, and validates every relevant stream through
the reconciliation checkpoint. Stream identity is exactly
`(aggregate_type, aggregate_id)`; each stream keeps one run, starts at `1`,
and increments contiguously in ledger order. Global
`(aggregate_type, aggregate_id, aggregate_version)` coordinates map to one
event identity, and global event-ID deduplication still permits only an
identical canonical duplicate as a no-op. Interleaved streams are partitioned
without losing global coordinate/run integrity.

The table-driven matrix covers valid interleaving, starts below and above one,
middle gaps, identical and different-ID duplicates, conflicting global event
IDs and coordinates, decreasing order, cross-run stream-coordinate reuse,
cross-aggregate substitution, and one valid plus one invalid stream. A final
adversarial review returned `PASS`; no contract conflict or scope violation
was found.

Fresh verification:

```text
PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) on x86_64-pc-linux-gnu,
compiled by gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, 64-bit

SWINGTRADE_TEST_POSTGRES_URL=postgresql+psycopg://.../swingtrade_test \
  python3 -m pytest -W error
130 passed in 1.55s (shell elapsed 1.830s)

P1E-F04 PostgreSQL target: 31 passed in 1.03s (elapsed 1.321s)
P1E-F05 stream matrix target: 55 passed in 0.09s (elapsed 0.283s)
```

The Phase 1 contract validator passed manifest/C01–C04, omission, and
reconciliation regressions. Ruff passed; strict mypy reported no issues in 11
source files; compile/import checks passed. PostgreSQL downgrade-to-base and
upgrade-to-head passed through unchanged Alembic revisions 0001–0003; offline
SQL rendered all three revisions in 57 lines.

Runtime network-import, credential/secret-literal, and
broker-network/LIVE-order-path scans returned zero matches. The exact diff is
limited to the five expected files. Whitespace, strict Git object, ancestry,
and clean-worktree checks passed. The accepted tag object, commit, and tree
remain `197d22b06cf6a96bad8c4b1a49ad1b928b147ac0`,
`abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`, and
`cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`; all 45 accepted manifest blob OIDs
and SHA-256 values matched.

This is implementation evidence for independent verification, not
self-certification. Phase 2, credentials, broker connectivity, SIM, order
activity, deployment, real capital, and LIVE remain unstarted and
unauthorized.

## 2026-09-26 — Gate A F06-A/B pre-edit record

Gate A starts from fetched local/remote/PR head
`6c84c3a1d5029a128ab51b8324449e7be86d7dc3`, tree
`f7fbfafc26dd660db40b1d67e67b83d486c447a8`, with a clean worktree. The
immutable accepted reference remains tag object
`197d22b06cf6a96bad8c4b1a49ad1b928b147ac0`, commit
`abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`, tree
`cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`, and 45 files. Prior F06 evidence
records PostgreSQL 16.15, 177 warnings-strict tests, 48 targeted F06 tests, 90
intent/DryRun tests, and validator/Ruff/mypy/Alembic/scans/integrity passes.

Pre-edit inspection found:

- The declared `decimal_value` input boundary is `Decimal | str`, but runtime
  `isinstance`/fallback construction admitted bool, int, float subclasses,
  `None`, Decimal/str subclasses, and arbitrary coercible objects.
- String input reached `Decimal(raw)` before any lexical resource limit.
  F06's tuple guard bounded fixed rendering after construction, but could not
  prevent oversized coefficient, fraction, exponent-token, malformed, or
  whitespace input from entering the Decimal parser.
- Durable observation materialization also called `Decimal(string)` directly
  rather than reusing the guarded declared boundary.

No contract explicitly admits numeric primitives or custom coercion. Exact
runtime `Decimal` and exact runtime `str` therefore implement the declared
boundary without changing economic semantics. Gate A retains the accepted
1000-digit canonical structural bound and adds lexical limits of **1024 raw
characters**, **1000 coefficient digits**, **6 exponent digits**, and exponent
magnitude at most **999999**. These limits admit every value allowed by the
existing canonical output bound while ensuring preparse work is a single
bounded linear scan. They are computational/input safety limits only: no
rounding, quantization, locale, tick, lot, or economic precision is selected.
No `CONTRACT_CONFLICT` exists.

Expected edits are limited to `src/swingtrade/domain.py`,
`src/swingtrade/persistence.py`, `tests/unit/test_domain_config.py`,
`tests/integration/test_postgres_intent_identity.py`,
`tests/broker_sim/test_dry_run_adapter.py`, and this journal. Any governance,
contract, migration, WDC/state/safety behavior, adapter implementation,
broker, cloud/Supabase, Phase 2, SIM, or LIVE change is outside Gate A.

### Gate A implementation and verification evidence

The implementation candidate before this evidence-only update is commit
`31ada5759de8fe37d32f29711303d7cc9a27b40d`, tree
`8d797adad2e576c17c9200c8e589e37731df3d7c`. It contains five ordinary
fast-forward commits from the recorded start; no history was rewritten.

The runtime boundary now accepts only `type(value) is Decimal` or
`type(value) is str`. Bool, int, float, `None`, Decimal/str subclasses, and
custom coercible objects raise bounded `DomainValidationError` before any
conversion. In particular, bool can no longer become Decimal `0`/`1` or reach
canonical payload, key, repository, or adapter logic.

For exact strings, the deterministic preparser:

1. checks the 1024-character raw limit before inspecting content;
2. explicitly rejects nonfinite tokens;
3. scans each character once without regex, whitespace normalization, locale,
   or raw-value interpolation;
4. permits only optional sign, decimal digits, at most one point, and optional
   `e`/`E` with optional sign;
5. requires at least one coefficient digit and at least one exponent digit
   when an exponent marker exists;
6. rejects above 1000 coefficient digits or six exponent digits; and
7. converts the at-most-six-digit exponent token to int and rejects magnitude
   above 999999 before calling `Decimal(raw)`.

Only after those bounded checks does the exact string enter Decimal. Both exact
string and exact Decimal paths then converge into the existing authoritative
finite/tuple/projected-rendering canonicalizer with its 1000-position bound.
Errors contain only static reason codes and constant limits, never the raw
value or a user-controlled type name.

Adversarial review found five WDC CSV fields that performed `Decimal(raw)`
before `Bar` validation. The minimal corrective change routes only those
fields through `decimal_value`; accepted WDC bytes and valid behavior are
unchanged. WDC tests prove malformed, whitespace, nonfinite, and million-byte
coefficient/fraction/exponent fields are rejected before Decimal—either by the
CSV parser's own field cap or by Gate A. The final adversarial review returned
`PASS`; this required boundary routing is not a scope violation.

Tests instrument the domain Decimal constructor and prove it is never entered
for oversized coefficient, fraction, exponent, malformed, signed, whitespace,
or empty string attacks. Exact `Decimal` and ordinary exact strings remain
accepted; `2`/`2.0`, `426.59`, `1E±2`, negative values, and signed zero retain
their existing canonical equivalence. PostgreSQL/DryRun tests prove direct
`True`, `False`, and million-byte inputs leave zero `order_intents` rows while
ordinary scale-equivalent dispatch converges to one durable row.

Fresh verification:

```text
PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) on x86_64-pc-linux-gnu,
compiled by gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, 64-bit

SWINGTRADE_TEST_POSTGRES_URL=postgresql+psycopg://.../swingtrade_test \
  python3 -m pytest -W error
218 passed in 1.94s (shell elapsed 2.245s)

Gate A adversarial selection:
87 passed, 60 deselected in 0.68s (elapsed 0.954s)
domain/intent/DryRun/WDC focused files:
147 passed in 1.78s
```

The Phase 1 contract validator passed manifest/C01–C04, omission, and
reconciliation regressions. Ruff passed; strict mypy reported no issues in 11
source files; compile/import passed. PostgreSQL downgrade-to-base and
upgrade-to-head passed through unchanged Alembic revisions 0001–0003; offline
SQL rendered all three in 57 lines.

The exact diff is limited to the domain/canonicalizer, the five WDC parsing
expressions, their tests, and this journal: eight files total. Secret,
credential, runtime-network, cloud/Supabase, broker, and LIVE/order-path scans
returned zero matches. Whitespace, strict Git object, ancestry, and clean
worktree checks passed. The accepted tag object, commit, and tree remain
`197d22b06cf6a96bad8c4b1a49ad1b928b147ac0`,
`abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`, and
`cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`; all 45 accepted manifest blob OIDs
and SHA-256 values matched.

This is Gate A implementation evidence for independent verification, not
self-certification. Governance, Phase 2, cloud/Supabase, credentials, broker
connectivity, SIM, order activity, deployment, real capital, and LIVE remain
unchanged and unauthorized.

## 2026-09-26 — P1E-F06 bounded Decimal resource remediation pre-edit record

This F06-only pass starts from fetched local/remote/PR head
`ea3ba1ab83605743cef08bfcc42de52eed6964c2`, tree
`099dcf0926d5b75c4276103e99725b3eaf7d8ce1`, with a clean worktree. The
immutable accepted reference remains annotated tag object
`197d22b06cf6a96bad8c4b1a49ad1b928b147ac0`, commit
`abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`, tree
`cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`, and its exact 45-file inventory.
Prior F04/F05 verifier evidence records PostgreSQL 16.15, 130 warnings-strict
tests, 31/55 targeted tests, validator/Ruff/mypy/Alembic/scans/integrity
passes, and independent-verification readiness without self-certification.

Pre-edit inspection found one authoritative Decimal-to-economic-intent path:
`canonical_decimal` feeds the single `canonical_economic_intent`
materialization used by repository key verification, payload/digest, and
observation. It rejects binary float and nonfinite Decimal values through
`decimal_value`, but calls `format(number, "f")` without first bounding the
coefficient/exponent expansion. Values such as `1E+1000000` can therefore
allocate an enormous fixed-point string before any persistence boundary.

No accepted contract, domain type, migration, or PostgreSQL `NUMERIC` column
defines a precision or exponent bound; persisted economic values are canonical
JSON strings. An unlimited expansion is not required by the contracts.
F06 therefore adopts a narrow computational input limit of **1000 canonical
fixed-point digit positions**, inspected from `Decimal.as_tuple()` before
formatting. The limit is intentionally much larger than every accepted fixture
value and is solely a deterministic memory/CPU safety boundary. It does not
round, quantize, select tick/lot precision, or assign economic meaning.
Coefficient length is rejected before any trailing-zero scan, making all
subsequent canonicalizer work bounded by the same limit. Zero remains a
constant `"0"` without expansion.

This is consistent with the existing requirements for finite base-10
canonical strings, no float, and no implicit rounding; no `CONTRACT_CONFLICT`
exists. Expected edits are limited to `src/swingtrade/persistence.py`,
`tests/integration/test_postgres_intent_identity.py`,
`tests/broker_sim/test_dry_run_adapter.py`, and this journal. Any contract,
domain, migration, WDC/state/safety, adapter implementation, broker, cloud,
Supabase, Phase 2, SIM, or LIVE change is a scope violation.

### P1E-F06 implementation and verification evidence

The implementation candidate before this evidence-only update is commit
`31ba1cb92f68194080cf50f15c4db0411501f940`, tree
`a76f03eeeef93b8218405e2d498daca976025488`. It contains three ordinary
fast-forward commits from the recorded start; no history was rewritten.

The exact resource bound is
`MAX_CANONICAL_DECIMAL_DIGIT_POSITIONS = 1000`. The authoritative algorithm:

1. applies existing `decimal_value` parsing and float rejection;
2. converts any Decimal subclass to an exact base `Decimal`, then explicitly
   rejects NaN, sNaN, and positive/negative Infinity;
3. returns every signed or scaled zero as `"0"` without expansion;
4. inspects `as_tuple()` and rejects a raw coefficient longer than 1000 digits
   before any trailing-zero loop;
5. strips trailing coefficient zeros while adjusting the exponent, with at
   most 1000 iterations;
6. computes projected fixed-point digit positions as `digits + exponent` for a
   nonnegative exponent, otherwise `max(digits, 1 - exponent)`, and rejects a
   result above 1000; and
7. reconstructs an exact base `Decimal` from the bounded canonical tuple and
   only then calls `format(..., "f")`.

This guarantees the formatted operand itself is bounded; it does not merely
bound the eventual stripped result. The typed failure is
`DomainValidationError`. Its message contains only the constant maximum,
either a bounded coefficient count or `over-limit`, and exponent direction. It
never formats, interpolates, hashes, logs, or persists the rejected value.

Tests cover boundary-minus-one/exact/plus-one for positive and negative
exponents, 999/1000/1001-digit coefficients, signs, signed/scaled zero,
leading/trailing zeros, `1E±100`, `1E±1000`, `1E±100000`,
`1E±1000000`, `9.99E±N`, negative values, all nonfinite forms, ordinary scale
equivalence, and nearby unequal values. A Decimal subclass that lies through
`as_tuple` and `__format__` cannot bypass either rejected or accepted paths.
An instrumented formatting test proves the formatter receives a 502-position
canonical tuple rather than the original 1501-position trailing-zero form.

PostgreSQL repository and active DryRun tests prove `2`, `2.0`, and `2.00`
converge durably. Extreme values raise before insert and leave zero
`order_intents` rows. All prior concurrency, replay, reconnect, rollback,
canonical-key, stale-row, F05 stream, P1E03–05, WDC, state, Decimal, and safety
tests remain in the full suite.

Fresh verification:

```text
PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) on x86_64-pc-linux-gnu,
compiled by gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, 64-bit

SWINGTRADE_TEST_POSTGRES_URL=postgresql+psycopg://.../swingtrade_test \
  python3 -m pytest -W error
177 passed in 1.60s (shell elapsed 1.884s)

F06 boundary/resource/PostgreSQL/DryRun selection:
48 passed, 42 deselected in 0.38s (elapsed 0.632s)
full PostgreSQL intent plus DryRun files:
90 passed in 1.48s
```

The Phase 1 contract validator passed manifest/C01–C04, omission, and
reconciliation regressions. Ruff passed; strict mypy reported no issues in 11
source files; compile/import passed. PostgreSQL downgrade-to-base and
upgrade-to-head passed through unchanged Alembic revisions 0001–0003; offline
SQL rendered all three in 57 lines. Final adversarial review returned `PASS`.

The exact diff is limited to the four expected files. Secret/credential,
runtime network, cloud/Supabase, broker, and LIVE/order-path scans returned
zero matches. Whitespace, strict Git object, ancestry, and clean-worktree
checks passed. The accepted tag object, commit, and tree remain
`197d22b06cf6a96bad8c4b1a49ad1b928b147ac0`,
`abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`, and
`cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`; every one of the 45 accepted
manifest blob OIDs and SHA-256 values matched.

This is implementation evidence for independent verification, not
self-certification. Phase 2, cloud/Supabase, credentials, broker connectivity,
SIM, order activity, deployment, real capital, and LIVE remain unstarted and
unauthorized.
