# Bootstrap Failure Model

- Review date: 2026-09-25
- Review scope: Phase 1A governance baseline at `ae1aa85`
- Reviewer posture: adversarial, read-only with respect to production
- Authorized execution mode: `SIM` only
- `LIVE` status: unauthorized

## Conclusion

The bootstrap is a useful statement of intent, but it is not yet an enforceable
safety system. Its readiness checks prove that documents exist and contain
expected words; they do not prove that identity, authorization, repository
change control, endpoint isolation, credential exclusion, or fail-closed
behavior works. The baseline therefore must not be interpreted as evidence
that order-capable implementation, account access, credentials, deployment, or
`LIVE` activity is safe.

This review does not approve architecture, certify a remedy, or authorize
implementation. Containment and recovery items below are candidate contract
requirements for human decision and later independent verification.

## Method and severity

The review traced every authority layer and bootstrap artifact, then challenged
them under spoofing, tampering, ambiguity, stale state, partial failure,
concurrency, compromised dependencies, operator error, and recovery scenarios.
Repository references are the evidence source; no credentials, accounts,
broker APIs, or order routes were used.

| Severity | Meaning |
| --- | --- |
| Critical | A plausible path can authorize or cause real-account interaction, credential exposure, or an unbounded safety-boundary bypass. |
| High | A likely control gap can hide unsafe state, defeat containment, or make recovery unverifiable. |
| Medium | The gap degrades evidence, accountability, or deterministic operation and can compound a higher-severity failure. |

## Required safety invariants

These are review oracles, not approved designs:

1. No artifact, actor, configuration, dependency, or degraded state can turn a
   research or `SIM` action into a real-account action.
2. Unknown identity, authority, mode, endpoint, account class, environment,
   artifact provenance, or control health fails closed before any side effect.
3. Authorization is authenticated, attributable, scoped, time-bounded, and
   independently reviewable; changing repository text cannot grant authority.
4. Safety controls remain effective under timeout, retry, duplicate delivery,
   stale state, concurrency, partial deployment, and rollback.
5. Evidence is immutable enough to reproduce both a decision and the exact
   artifact tested; existence or keyword checks are not safety proof.
6. Detection, containment, recovery, and independent verification have named
   owners before a capability is introduced.

## Failure scenarios

### FM-01 — Unauthenticated human authority

- **Severity:** Critical
- **Trigger:** A message or repository edit claims to be an explicit human
  instruction or approval. No owner, decider, trusted identity source,
  signature, approval location, scope, expiry, or revocation process is named.
- **Unsafe consequence:** A spoofed, misunderstood, or stale instruction can
  outrank all repository controls under the authority hierarchy.
- **Detection:** There is no deterministic detector; `AGENT_AUTHORITY.md`
  places explicit human instructions first while `CURRENT_STATE.md` lists
  human owners and ADR deciders as unresolved.
- **Containment:** Treat every identity or approval not resolved through a
  human-approved authority registry as absent.
- **Recovery:** Revoke the disputed authorization, inventory actions taken
  under it, and restore the last independently verified authorized state.
- **Verification:** An independent reviewer attempts approval via unregistered,
  stale, delegated, and replayed identities; every attempt must fail closed and
  leave attributable evidence.
- **Unresolved decisions:** Who can approve what, through which trusted system,
  with what quorum, scope, expiry, delegation, revocation, and emergency rules?

### FM-02 — Repository text self-authorizes a phase

- **Severity:** Critical
- **Trigger:** An actor edits `CURRENT_STATE.md`, an ADR status, or authority
  text in the same change that introduces a new capability.
- **Unsafe consequence:** Phase, implementation, or execution authority becomes
  self-issued by changing mutable files rather than receiving independent
  authorization.
- **Detection:** No protected-path ownership, approval policy, signed status
  transition, or machine-enforced separation of duties is specified.
- **Containment:** Treat governance-file changes as proposals only; they must
  not activate capabilities.
- **Recovery:** Disable the affected capability, revert to the last accepted
  governance state, and review all changes made after the invalid transition.
- **Verification:** Attempt a one-author change that updates authorization and
  capability together; merge and activation must both be rejected.
- **Unresolved decisions:** Which controls exist outside the repository, which
  files are protected, and who independently attests a phase transition?

### FM-03 — Authority precedence permits safety override

- **Severity:** Critical
- **Trigger:** An explicit human request conflicts with `SIM`-only or
  no-credentials language. The hierarchy ranks explicit human instructions
  above the global boundaries, while other text requires an ADR, current-state
  authorization, and human approval.
- **Unsafe consequence:** Different actors can reasonably choose opposite
  interpretations; one may treat a single instruction as authority for `LIVE`.
- **Detection:** A policy linter cannot derive one answer from the current
  documents because the conflict is semantic, not syntactic.
- **Containment:** Interpret all conflicts in favor of no side effect and keep
  `LIVE` unauthorized.
- **Recovery:** Quarantine work produced under the broader interpretation and
  re-evaluate it against a clarified, non-overridable safety constitution.
- **Verification:** Table-test every combination of human instruction, ADR
  state, phase state, and role authority; all conflicting or incomplete cases
  must deny.
- **Unresolved decisions:** Are any prohibitions non-overridable, and what exact
  conjunction of approvals could ever change them?

### FM-04 — Governance is advisory, not enforced

- **Severity:** Critical
- **Trigger:** A tool, script, CI job, contributor, alternate agent, or
  compromised process does not load `.cursor/rules/` or ignores Markdown.
- **Unsafe consequence:** All stated boundaries can be bypassed without a
  control failure because no runtime or repository enforcement is defined.
- **Detection:** The Phase 1A validation checks file presence and metadata, not
  effective enforcement by every actor and execution path.
- **Containment:** Keep the repository non-order-capable and deny deployment or
  secret access until controls independent of agent compliance exist.
- **Recovery:** Remove unauthorized artifacts, rotate any exposed secret
  through its external owner, and audit all ungoverned actors and writes.
- **Verification:** Exercise each supported actor and entry point without
  Cursor rule loading; prohibited changes and effects must still be blocked.
- **Unresolved decisions:** What is the policy-enforcement point for humans,
  bots, CI, local tooling, deployments, and runtime?

### FM-05 — Branch, merge, and stale-state drift

- **Severity:** High
- **Trigger:** Research or later work starts from an unmerged, stale,
  superseded, or divergent governance branch, or a merge omits a control.
- **Unsafe consequence:** Actors operate under different authority baselines
  while each believes it is compliant.
- **Detection:** `CURRENT_STATE.md` names a commit on `origin/main` as canonical
  but also declares readiness on a governance branch; no baseline digest,
  merge-attestation, or freshness check is required.
- **Containment:** Bind every task and artifact to one immutable governance
  commit and reject unknown or non-descendant baselines.
- **Recovery:** Stop affected work, rebase its evidence—not its authority—onto
  the accepted baseline, and repeat review.
- **Verification:** Test stale branch, partial merge, force-updated reference,
  and concurrent governance-change cases.
- **Unresolved decisions:** What event adopts a baseline, how is ancestry
  checked, and how are in-flight tasks invalidated?

### FM-06 — Role and scope controls are bypassable

- **Severity:** High
- **Trigger:** An agent uses a different role file, no role file, nested
  delegation, or a task that spans nominally independent workstreams.
- **Unsafe consequence:** One actor researches, reconciles, decides, and
  effectively approves its own conclusion despite stated separation.
- **Detection:** Counting exactly four role definitions does not identify the
  executing role, delegated descendants, or accumulated authority.
- **Containment:** Default unbound and multi-role actors to read-only evidence
  collection with no decision authority.
- **Recovery:** Reclassify affected conclusions as unreviewed proposals and
  obtain independent specialist and decider review.
- **Verification:** Attempt cross-role actions, nested delegation, role
  switching, and combined-task prompts; authority must not accumulate.
- **Unresolved decisions:** How are roles bound to authenticated actors, and
  what independence standard applies to author, reconciler, and approver?

### FM-07 — `SIM` is a label, not endpoint isolation

- **Severity:** Critical
- **Trigger:** Configuration says `SIM`, but DNS, base URL, account identifier,
  SDK default, proxy, broker-side mapping, or environment points to a real
  service.
- **Unsafe consequence:** A nominal simulation action can affect a real
  account or expose real-account data.
- **Detection:** The baseline specifies string handling but no positive
  attestation of endpoint, account class, certificate, tenant, or network path.
- **Containment:** Do not introduce any order-capable network path; a mode label
  alone is insufficient authorization.
- **Recovery:** Cut network access, cancel or reconcile externally through an
  authorized human process, preserve evidence, and treat impact as unknown
  until independently established.
- **Verification:** Inject wrong endpoints, DNS responses, account classes,
  proxies, SDK defaults, and mode/endpoint mismatches; every case must stop
  before connection or submission.
- **Unresolved decisions:** What independent signals prove simulation identity,
  and which component enforces their conjunction?

### FM-08 — No order-attempt invariant or choke point

- **Severity:** Critical
- **Trigger:** A future component gains an order API before a verified,
  non-bypassable execution gate exists, or an apparently non-order operation
  has an order side effect.
- **Unsafe consequence:** An order can be attempted even though documents say
  no component may submit one.
- **Detection:** No formal definition of “submit,” side effect, order-capable
  operation, or single enforcement boundary exists.
- **Containment:** Keep all research and validation structurally disconnected
  from order-capable clients and networks.
- **Recovery:** Disable and remove the path, inventory every attempted request,
  and reconcile ambiguous external state before resuming non-order work.
- **Verification:** Use instrumented fakes to assert zero order attempts across
  startup, shutdown, retry, timeout, exception, and malformed-input paths.
- **Unresolved decisions:** What operations count as orders, where is the
  non-bypassable choke point, and what zero-attempt evidence is required?

### FM-09 — Simulation service has live adjacency

- **Severity:** High
- **Trigger:** A broker SDK, shared credential, shared account selector, or
  shared control plane can switch between simulation and live facilities.
- **Unsafe consequence:** Operator error, SDK behavior, or service-side change
  crosses the environment boundary.
- **Detection:** Broker simulation semantics and isolation guarantees remain
  explicitly unresearched.
- **Containment:** Treat simulation facilities as untrusted until public
  evidence and independent isolation tests establish their boundaries.
- **Recovery:** Disconnect the integration, invalidate local state, and require
  external account reconciliation by an authorized human if boundary crossing
  cannot be disproved.
- **Verification:** Test every documented environment selector and failure
  fallback without credentials, using fixtures or mocks until a separately
  authorized test method exists.
- **Unresolved decisions:** Which simulation facility, isolation guarantees,
  fallback behavior, and evidence standard are acceptable?

### FM-10 — Credential policy is contradictory and incomplete

- **Severity:** High
- **Trigger:** Future work follows `.cursor/rules/10-trading-safety.mdc`, which
  both says never use brokerage credentials and anticipates future local secret
  handling in ignored files or an approved manager.
- **Unsafe consequence:** A contributor may infer permission to introduce real
  credentials; ignored files can still leak through logs, processes, caches,
  artifacts, screenshots, or previously tracked files.
- **Detection:** No credential taxonomy, owner, environment distinction,
  scanning coverage, redaction contract, or rotation procedure exists.
- **Containment:** Continue the current task-level prohibition: do not request,
  retrieve, store, or use any brokerage credential.
- **Recovery:** Assume compromise, stop consumers, invoke the credential
  owner’s revocation/rotation process, and audit retained artifacts.
- **Verification:** Seed only synthetic canaries through files, history, logs,
  environment, process arguments, caches, and artifacts; every prohibited
  persistence path must be detected.
- **Unresolved decisions:** Will simulation require credentials, who may handle
  them, and what storage, redaction, rotation, and retention controls apply?

### FM-11 — Degraded-state behavior is undefined

- **Severity:** Critical
- **Trigger:** Mode, authorization, policy service, clock, network, storage,
  broker response, or control dependency is missing, stale, split-brain,
  malformed, timed out, or partially available.
- **Unsafe consequence:** A component may retry, fall back, reuse cached
  authority, or proceed inconsistently rather than fail closed.
- **Detection:** “Fail closed” is stated but closed state, timeout budget,
  freshness, cache rules, and side-effect boundary are not defined.
- **Containment:** Treat every degraded or contradictory signal as no authority
  and permit no external side effect.
- **Recovery:** Enter a known quiescent state, reconcile durable and external
  state, then require explicit independently verified restart criteria.
- **Verification:** Fault-inject every dependency before, during, and after a
  prospective side effect, including delayed and contradictory responses.
- **Unresolved decisions:** What is the safe state for each component, how is
  it reached atomically, and who authorizes restart?

### FM-12 — Retry, duplicate, and concurrency hazards

- **Severity:** Critical
- **Trigger:** Timeout ambiguity, process restart, duplicate message, race,
  concurrent agent, or replay causes an operation to execute more than once or
  after authority has changed.
- **Unsafe consequence:** Duplicate or stale actions can escape limits, and
  recovery can create additional effects.
- **Detection:** No idempotency, deduplication, sequencing, fencing,
  cancellation, or authority-version contract is established.
- **Containment:** Introduce no side-effecting asynchronous path until those
  contracts are decided and testable.
- **Recovery:** Freeze processing, reconcile by stable operation identity, and
  resume only from a proven boundary.
- **Verification:** Deterministically inject duplicates, reordered delivery,
  restart, concurrent writers, cancellation races, and ambiguous timeouts.
- **Unresolved decisions:** What are the identity, ordering, idempotency,
  fencing, finality, and replay semantics?

### FM-13 — Shutdown and incident containment are absent

- **Severity:** High
- **Trigger:** Unsafe behavior is suspected, but no named incident commander,
  kill authority, shutdown mechanism, escalation channel, or response runbook
  exists.
- **Unsafe consequence:** Harm continues while actors debate authority, and an
  unsafe restart may erase evidence or repeat effects.
- **Detection:** The baseline says “stop and escalate” without defining who can
  stop what, how stop is confirmed, or who receives escalation.
- **Containment:** Keep capabilities non-order-capable; treat inability to prove
  stop as continuing impact.
- **Recovery:** Preserve evidence, reconcile state, identify cause, and require
  independent restart approval.
- **Verification:** Run tabletop exercises for unavailable owners, failed stop,
  partial shutdown, compromised operator, and false alarm.
- **Unresolved decisions:** Who owns incidents, who can stop and restart, what
  channels and service objectives apply, and how is cessation proven?

### FM-14 — Repository controls and CI are unspecified

- **Severity:** High
- **Trigger:** A direct push, unreviewed merge, disabled check, compromised CI
  job, or path-excluded workflow changes governance or introduces prohibited
  content.
- **Unsafe consequence:** Unsafe changes become canonical while all document
  requirements remain apparently satisfied.
- **Detection:** No branch protection, CODEOWNERS, required checks, trusted
  runner, artifact provenance, or merge-policy evidence is in scope.
- **Containment:** Do not treat mergeability or a passing draft-PR check as
  safety acceptance.
- **Recovery:** Identify the last trusted commit, block affected artifacts, and
  independently reconstruct and verify history.
- **Verification:** Test direct push, administrator bypass, check deletion,
  path filtering, forked PR, compromised dependency, and stale-success reuse.
- **Unresolved decisions:** Which forge controls are mandatory, who administers
  them, and how are their configurations audited and versioned?

### FM-15 — Secret scanning creates false confidence

- **Severity:** High
- **Trigger:** A secret uses an untested format, encoding, split string, binary,
  history entry, submodule, archive, log, or ignored/untracked file.
- **Unsafe consequence:** Sensitive material persists despite the recorded
  limited pattern scan passing.
- **Detection:** The journal explicitly validates only private-key markers,
  GitHub-token patterns, and AWS access-key patterns in tracked content.
- **Containment:** Interpret that result only as three negative pattern
  checks—not evidence that the repository or workspace is secret-free.
- **Recovery:** Remove exposed material where possible, rotate it externally,
  inspect history and artifacts, and document residual copies.
- **Verification:** Use synthetic canaries across all supported storage and
  transport formats, including commit history and generated artifacts.
- **Unresolved decisions:** What scanners, scopes, canary tests, history policy,
  and response obligations form the credential-exclusion contract?

### FM-16 — Evidence is mutable and weakly reproducible

- **Severity:** High
- **Trigger:** A canonical URL changes, disappears, serves personalized content,
  or is cited without version, quotation, hash, retrieval evidence, or source
  conflict resolution.
- **Unsafe consequence:** Decisions cannot be reproduced; later content can
  appear to support a claim it did not support at review time.
- **Detection:** The research contract asks for access date and locator but not
  immutable version, content digest, archived evidence, or reproduction method.
- **Containment:** Keep mutable-source findings classified as provisional and
  prevent them from independently satisfying a safety gate.
- **Recovery:** Re-research the claim from independently preserved or
  versioned sources and re-open dependent decisions.
- **Verification:** Reproduce each material claim from a clean environment
  using its recorded locator and compare content identity.
- **Unresolved decisions:** What evidence may be preserved legally, how is it
  hashed/versioned, and how many independent sources are required?

### FM-17 — Malicious or compromised research input

- **Severity:** High
- **Trigger:** Public documentation, a repository, package metadata, issue,
  sample code, or fetched content contains prompt injection or malicious
  instructions.
- **Unsafe consequence:** A research agent exceeds scope, leaks data, changes
  files, downloads executable content, or converts untrusted text into a
  decision.
- **Detection:** The evidence contract ranks source quality but defines no
  untrusted-content handling, egress boundary, or tool isolation.
- **Containment:** Treat all fetched content as evidence data, never authority
  or executable instruction; keep research tools credential-free.
- **Recovery:** Stop the affected task, invalidate conclusions and artifacts
  influenced by the content, and review tool activity.
- **Verification:** Present benign prompt-injection fixtures in every supported
  source format and confirm no authority, scope, or tool behavior changes.
- **Unresolved decisions:** What sandbox, egress, content-handling, and
  provenance controls bind research agents?

### FM-18 — Conflicts and unknowns can still advance readiness

- **Severity:** High
- **Trigger:** Specialists report conflicting evidence or material unknowns,
  while the coordinator is permitted to reconcile outputs and readiness has no
  domain-specific acceptance criteria.
- **Unsafe consequence:** A conflict is documented but treated operationally as
  resolved, or missing facts are converted into implicit defaults.
- **Detection:** The baseline requires recording conflict but defines no
  blocking severity, evidence sufficiency, acceptance owner, or decision rule.
- **Containment:** Material safety conflicts and unknowns remain explicit gate
  failures, not backlog items.
- **Recovery:** Reopen dependent decisions and invalidate readiness claims
  reached without the missing acceptance evidence.
- **Verification:** Seed contradictory and absent evidence for every material
  requirement; advancement must be denied with a traceable reason.
- **Unresolved decisions:** Which unknowns are blockers, who adjudicates
  evidence, and what acceptance rubric applies to each workstream?

### FM-19 — Legal, regulatory, entitlement, and licensing breach

- **Severity:** High
- **Trigger:** Research or future data use violates terms, market-data
  entitlements, retention restrictions, redistribution limits, jurisdictional
  rules, or automated-trading obligations.
- **Unsafe consequence:** The platform can be technically controlled yet
  unauthorized to obtain, retain, transform, or use its data or service.
- **Detection:** These obligations are listed as unknown; no qualified owner or
  pre-use gate is assigned.
- **Containment:** Do not acquire restricted data, create accounts, accept
  terms, or interpret legal obligations in this workstream.
- **Recovery:** Stop use and distribution, preserve decision evidence without
  further copying restricted content, and escalate to a qualified human owner.
- **Verification:** An authorized legal/compliance review traces jurisdiction,
  user, account, dataset, purpose, retention, and redistribution before use.
- **Unresolved decisions:** Applicable jurisdictions, regulated roles,
  entitlement owners, licenses, retention, audit, and legal-review gates.

### FM-20 — Data and fixtures can conceal unsafe behavior

- **Severity:** High
- **Trigger:** Synthetic data, mocks, or fixtures omit broker errors, corporate
  actions, market calendars, malformed events, delayed data, or side-effect
  behavior—or are tampered with.
- **Unsafe consequence:** Tests pass while the real integration would violate
  safety invariants or attempt orders.
- **Detection:** Tests are required to be deterministic, but fixture
  provenance, fidelity, mutation coverage, and independent oracle are undefined.
- **Containment:** Do not infer integration or execution safety from mock-only
  success.
- **Recovery:** Reclassify affected test claims, replace suspect fixtures from
  approved evidence, and rerun independent adversarial tests.
- **Verification:** Mutation, property, malformed-input, boundary, and
  fault-injection tests must demonstrate that tests fail when each invariant is
  deliberately broken.
- **Unresolved decisions:** Who owns fixture provenance, realism, review,
  versioning, and the independent test oracle?

### FM-21 — Audit trail lacks integrity and lifecycle rules

- **Severity:** High
- **Trigger:** Decisions, approvals, tool activity, configuration, or evidence
  are edited, deleted, reordered, generated with skewed clocks, or retained for
  an unknown duration.
- **Unsafe consequence:** Investigators cannot establish who authorized what,
  which artifact ran, or whether containment and recovery succeeded.
- **Detection:** The append-only journal is a convention in an editable Git
  file; no immutable event schema, trusted clock, actor identity, retention, or
  external preservation is defined.
- **Containment:** Treat repository history as useful evidence, not a complete
  tamper-evident audit system.
- **Recovery:** Preserve all available sources, document gaps, and avoid
  declaring impact bounded when records are incomplete.
- **Verification:** Attempt authorized edits, deletion, clock skew, history
  rewrite, actor spoofing, partial-log loss, and restore from backup.
- **Unresolved decisions:** Required events, trusted identity and time,
  integrity mechanism, retention, access, privacy, export, and audit owner.

### FM-22 — Recovery and rollback can repeat harm

- **Severity:** High
- **Trigger:** A rollback restores code but not queues, external effects,
  configuration, authority state, schema, or deduplication state.
- **Unsafe consequence:** The system resumes from an inconsistent boundary,
  repeats actions, or falsely reports recovery.
- **Detection:** The ADR template asks for rollback but defines no recovery
  point, external reconciliation, backup integrity, or restart proof.
- **Containment:** Rollback alone must not imply safe recovery; remain stopped
  until all relevant state is reconciled.
- **Recovery:** Restore a coherent versioned state, reconcile external effects,
  fence stale workers, and independently approve restart.
- **Verification:** Restore under in-flight, partially committed, stale-worker,
  corrupted-backup, and incompatible-schema scenarios.
- **Unresolved decisions:** Recovery objectives, authoritative state, backup
  scope, reconciliation owner, fencing, and restart acceptance criteria.

### FM-23 — Observability either misses danger or leaks data

- **Severity:** High
- **Trigger:** Logs and alerts omit order-attempt, authorization, endpoint, or
  control-health signals—or record credentials, identifiers, proprietary data,
  or personal information.
- **Unsafe consequence:** Unsafe behavior is invisible, while diagnostics
  create a separate disclosure incident.
- **Detection:** Monitoring and audit are research topics, not current
  contracts; no event schema, redaction, alert owner, or health signal exists.
- **Containment:** Introduce neither sensitive telemetry nor claims of
  detectability until a redacted minimum event contract is approved.
- **Recovery:** Restrict and purge exposed telemetry where authorized, rotate
  affected secrets, reconstruct missing events, and document uncertainty.
- **Verification:** Synthetic canaries and forced control failures must produce
  actionable alerts without sensitive-value disclosure.
- **Unresolved decisions:** Required signals, redaction boundary, access,
  retention, alert routing, acknowledgment, escalation, and health semantics.

### FM-24 — Safety claims outpace validation

- **Severity:** High
- **Trigger:** “All readiness gates passed,” “fail closed,” or consistent
  `SIM` wording is interpreted as proof of operational safety.
- **Unsafe consequence:** Stakeholders authorize implementation or deployment
  based on document conformance rather than tested safety properties.
- **Detection:** Phase 1A evidence consists of structure, keyword, file-scope,
  limited secret-pattern, status, and PR-state checks.
- **Containment:** Label those checks as governance-bootstrap conformance only;
  they confer no execution-safety assurance.
- **Recovery:** Withdraw overstated assurance, identify decisions relying on
  it, and repeat acceptance with tests tied to explicit invariants.
- **Verification:** Every future claim must map to a falsifiable property,
  negative test, exact artifact digest, environment, command, and independent
  result.
- **Unresolved decisions:** Who owns the assurance case, what confidence level
  is required per phase, and who independently verifies it?

## Coverage and validation

| Failure class | Scenarios |
| --- | --- |
| Identity, authorization, separation of duties | FM-01–FM-03, FM-06 |
| Policy enforcement and repository change control | FM-04, FM-05, FM-14 |
| Execution isolation and side effects | FM-07–FM-09 |
| Credentials and confidential data | FM-10, FM-15, FM-23 |
| Partial failure, concurrency, containment, recovery | FM-11–FM-13, FM-22 |
| Evidence, research inputs, conflicts, test oracles | FM-16–FM-18, FM-20 |
| Legal/compliance and auditability | FM-19, FM-21 |
| Assurance-claim integrity | FM-24 |

Validation for this document must remain non-operational:

1. Confirm each scenario contains severity, trigger, unsafe consequence,
   detection, containment, recovery, verification, and unresolved decisions.
2. Confirm every Critical scenario preserves `LIVE` as unauthorized and does
   not require credentials, accounts, broker access, or order submission.
3. Confirm each required invariant is challenged by at least one scenario.
4. Confirm repository changes are limited to this document.
5. Treat passing validation as coverage evidence only, never certification that
   a proposed containment or recovery control is sufficient.

## Contract implications and blocking decisions

Before any order-capable foundation is authorized, later requirements need
human-approved, independently testable contracts for:

- authenticated authority, non-overridable prohibitions, separation of duties,
  phase transitions, revocation, and emergency action;
- immutable baseline identity, protected changes, trusted CI, provenance, and
  governance enforcement outside agent instructions;
- positive simulation identity, endpoint/account isolation, zero-order-attempt
  boundaries, network denial, and degraded-state behavior;
- idempotency, ordering, retries, finality, shutdown, reconciliation, rollback,
  recovery, restart, and incident ownership;
- credential and sensitive-data taxonomy, exclusion or handling, scanning,
  redaction, rotation, retention, and response;
- source integrity, untrusted-content isolation, evidence sufficiency, conflict
  adjudication, fixture provenance, and independent verification;
- legal/compliance, market-data entitlement, licensing, jurisdiction, privacy,
  audit, and record-retention gates; and
- claim language that distinguishes document conformance, implementation,
  verification, simulation evidence, and authorization.

Until those decisions are accepted and externally enforced, the safe contract
remains: public, credential-free, non-order-capable research only; `SIM` is the
sole named mode, but its label is not proof of isolation; `LIVE` remains
unauthorized.
