# Phase 2 Monitoring Taxonomy

- **Status:** PROPOSED
- **Workstream:** `P2-J/r1` taxonomy design only
- **Baseline:** canonical `main`
  `1ecbbe6d487d97195fde393b05c9499357599bdb`
- **Authority effect:** none; this document does not authorize Phase 2,
  credentials, broker or account access, network activity, provisioning,
  TradeStation `SIM`, order submission, or `LIVE`
- **Implementation status:** no code, tests, migrations, alert wiring,
  dashboards, runbooks, or infrastructure are implemented by this proposal

## 1. Purpose and contract position

This document proposes stable condition codes and reporting semantics for the
future broker, database, worker, and scheduler monitoring contemplated by
`PHASE_2_PLAN.md` §7.10. It extends the concepts in `MONITORING.md`,
`REPORTING.md`, `METRICS.md`, `RECONCILIATION.md`, and `DATA_MODEL.md` without
changing those accepted contracts.

The conditions below are design requirements, not claims about TradeStation,
OAuth configuration, a database provider, runtime behavior, or operational
thresholds. A condition whose detection depends on unresolved broker, auth, or
database behavior remains non-operational until the named dependency is
resolved and accepted at the applicable human gate.

## 2. Vocabulary and fail-closed health semantics

### 2.1 Separate dimensions

Health, evidence certainty, readiness, and run outcome are separate:

| Dimension | Proposed values | Meaning |
| --- | --- | --- |
| Health state | `HEALTHY`, `DEGRADED`, `UNHEALTHY` | Current condition of a component or dependency |
| Assessment certainty | `KNOWN`, `UNKNOWN`, `UNCERTAIN` | Whether complete, consistent, sufficiently fresh evidence supports the health state |
| Readiness | true or false | Whether the affected capability may make progress safely |
| Existing run/effect outcome | includes `BLOCKED` | Existing `MONITORING.md` and lifecycle term; not renamed by this proposal |

`UNKNOWN` means required evidence is absent or cannot be evaluated.
`UNCERTAIN` means evidence exists but is contradictory, partial, stale, or
cannot be tied to one authoritative scope. Neither is a healthy state.
For readiness and external effects, `UNKNOWN` and `UNCERTAIN` are treated as
`UNHEALTHY`: readiness is false and the affected operation is `BLOCKED` or
sent to `OPERATOR_REVIEW` under the governing contract. They must never be
coerced to `HEALTHY` or used as permission to retry an ambiguous submission.

This resolves terminology without silently replacing
`MONITORING.md`'s current run-health set (`HEALTHY`, `DEGRADED`, `BLOCKED`,
`UNKNOWN`): `BLOCKED` remains the observable run/effect outcome. Adoption of
`UNHEALTHY` and `UNCERTAIN` as contract-level values requires reconciliation
and explicit human acceptance at Gate `H1`/`H2`; until then they are proposed
projection vocabulary only.

### 2.2 Aggregation

- `HEALTHY`: every required assessment for the scope is `KNOWN`, within an
  approved bound, and has no active condition that inhibits the scope.
- `DEGRADED`: a known impairment exists, but no failed safety invariant is
  being represented as healthy. A specific dependent operation may still be
  blocked by its contract.
- `UNHEALTHY`: a blocking invariant or required dependency has failed.
- Scope health is the most restrictive active effect. A lower-severity
  condition cannot reduce a more restrictive state.
- Missing telemetry cannot produce `HEALTHY`; it produces `UNKNOWN` certainty
  and fail-closed effects.
- Health recovery requires the condition-specific clear evidence in §6. Time
  passage, alert acknowledgement, silence, process restart, or an empty
  dashboard is not clear evidence.

### 2.3 Severity

| Severity | Proposed meaning |
| --- | --- |
| `CRITICAL` | A safety invariant, durable state, or external-effect identity may be violated or unknowable; immediate human attention and blocking are required. |
| `HIGH` | A required dependency or trustworthy state is unavailable; dependent dispatch and final reports are blocked. |
| `MEDIUM` | A bounded known impairment requires attention and may become blocking at an approved threshold. |
| `LOW` | Informational drift with no current safety or readiness effect. |

These meanings preserve the existing immediate-attention and reconciliation
severity rules. This proposal does not lower any existing severity. Numeric
thresholds, response objectives, paging routes, and recurrence escalation are
unresolved Operator choices and are not invented here.

## 3. Environment, mode, and human gates

Environment and execution mode must be reported as separate typed fields.
`PHASE_2_PLAN.md` uses the proposed environment names `DEV`, `TEST`, `SIM`,
and `LIVE`, and the execution-mode contracts use `DRY_RUN`, `SIM`, and `LIVE`.
No alias such as `prod`, hostname inference, database URL, endpoint, or
fallback may derive either field.

The `P2-C` environment-separation contract is not yet accepted, so this
taxonomy does not finalize environment naming. Missing, malformed,
conflicting, or unknown environment or mode produces `UNKNOWN` certainty,
false readiness, and a blocked effect. `DRY_RUN` remains the sole authorized
mode. The mere existence of `SIM` or `LIVE` as a taxonomy value grants no
capability; `LIVE` remains categorically outside Phase 2.

This proposal may be reviewed at Gate `H1`. It cannot be frozen until the
Operator's Gate `H2` decision reconciles it with accepted `P2-B` through
`P2-G` contracts. No alert, clear, environment label, dashboard, or report can
serve as human authorization. Gates `G1`, `G2`, and `G3` remain separate,
conjunctive human-controlled boundaries.

## 4. Required common alert record

Every occurrence and clear is an append-only fact with:

- stable condition code and taxonomy schema version;
- severity, health effect, assessment certainty, environment, mode,
  component/version, and safe bounded scope class;
- occurrence id, first/last observed time from the supplied clock, count,
  run id where applicable, and correlation/causation ids;
- detector version, source high-water mark or observation digest, evidence
  link, and safe reason code;
- alert state (`OPEN`, `ACKNOWLEDGED`, or `RESOLVED`) and runbook id; and
- for resolution, the clearing observation, verifier identity class, and
  invariant recheck result.

The event ledger is authoritative. Logs, metrics, notifications, dashboards,
and reports are projections only. `ACKNOWLEDGED` is not `RESOLVED`.

## 5. Sensitive-data profiles

Every condition in §6 names one of these mandatory profiles:

- **`S-BASE`:** no credential, token, secret, account identifier, personal
  data, raw broker payload, unconstrained exception text, URL, connection
  string, or free-form order field. Use stable reason codes, digests, and
  access-controlled evidence links.
- **`S-AUTH`:** `S-BASE` plus no authorization code, access/refresh token,
  client secret, token claims, callback value, key-specific identity, or raw
  auth response. Report only bounded auth-flow class, safe failure class, and
  policy/version digest.
- **`S-BROKER`:** `S-BASE` plus no broker order/fill/account id, raw status,
  symbol, route, entitlement detail, request/response body, or endpoint URL in
  alerts, metric labels, or general reports. Quarantined raw values, if later
  authorized at all, require a separately approved restricted store; this
  proposal does not authorize one.
- **`S-DB`:** `S-BASE` plus no database hostname, username, provider resource
  id, schema data, query text containing values, backup location, or
  connection material. Use dependency class, operation class, and bounded
  reason code.
- **`S-RUNTIME`:** `S-BASE` plus no host address, process environment, command
  line, infrastructure resource id, queue payload, or job arguments. Use
  component, worker class, scheduler class, and opaque internal evidence
  references.

Run ids, correlation ids, and evidence ids may appear in structured events,
logs, and reports under access control but remain prohibited metric labels
under `METRICS.md`. All metric dimensions must be bounded enumerations.

## 6. Condition catalog

“Approved bound” means a versioned threshold selected through the applicable
contract and human gate. Until one exists, a detector dependent on that bound
has `UNKNOWN` certainty and cannot assert `HEALTHY`.

### 6.1 Broker connectivity and broker-data freshness

| Code | Condition and severity | Health-state effect | Alert condition | Clear condition | Required evidence | Runbook | Sensitive profile |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MON-BRK-001` | Broker transport or approved endpoint unavailable — `HIGH` | `UNHEALTHY`; broker-dependent readiness false | A request or stream to the independently verified, authorized endpoint class cannot establish or retain transport within the approved policy; wrong/unknown endpoint escalates to `CRITICAL` and authorization denial | A new authorized connectivity check succeeds, endpoint/isolation evidence matches the accepted artifact, and dependent state is reconciled; reconnect alone is insufficient | Detector/version, safe transport reason, endpoint-class policy digest, timestamps, correlation id, isolation-attestation reference, reconciliation result | `RB-MON-BRK-001` must define containment, no-fallback checks, recovery, and escalation before operational use | `S-BROKER` |
| `MON-BRK-002` | Stream heartbeat missing or reconnect state unknown — `HIGH` | `UNHEALTHY`; stream-derived readiness false | Expected heartbeat/fresh record is absent beyond an approved bound, or reconnect/resume/gap state is `UNKNOWN`/`UNCERTAIN` | An authoritative snapshot-to-stream handoff and gap check completes under an accepted broker contract, with no unresolved high/critical discrepancy | Last safe heartbeat time/digest, detector clock, stream-class code, reconnect attempt summary, snapshot/stream high-water marks, gap-check result | `RB-MON-BRK-002` must cover disconnect containment, snapshot recovery, gap detection, and no assumed replay | `S-BROKER` |
| `MON-BRK-003` | Broker snapshot stale or freshness unprovable — `HIGH` | `UNHEALTHY`; affected query/reconciliation readiness false | Snapshot age exceeds an approved source-specific bound, source time is absent/untrusted, or entitlement/session semantics make freshness `UNKNOWN`/`UNCERTAIN` | A new complete snapshot has accepted provenance and time semantics and reconciliation through its high-water mark passes | Retrieval/recorded times, supplied-clock evidence, source-class/schema versions, snapshot digest, freshness-policy version, reconciliation completion reference | `RB-MON-BRK-003` must define source-specific freshness checks, session handling, containment, and escalation | `S-BROKER` |
| `MON-BRK-004` | Snapshot/stream gap, duplicate, or ordering uncertainty — `HIGH` | `UNHEALTHY`; affected broker view blocked | Sequence, cursor, overlap, or identity evidence cannot prove continuity, or a gap/duplicate/order conflict is detected | Accepted recovery procedure establishes a stable snapshot, continuity evidence, duplicate handling, and a passing reconciliation check | Cursor/sequence class where available, observation digests, overlap window policy, first/last safe high-water marks, discrepancy ids, recovery check | `RB-MON-BRK-004` must prohibit guessed ordering and document stable-snapshot recovery | `S-BROKER` |

### 6.2 Authentication, authorization, and refresh

| Code | Condition and severity | Health-state effect | Alert condition | Clear condition | Required evidence | Runbook | Sensitive profile |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MON-AUT-001` | Authentication or authorization denied — `HIGH` | `UNHEALTHY`; affected broker capability readiness false | A broker request receives an accepted auth-denial class, required scope is absent, or authorization state cannot be established; attempted use outside authorized mode/environment is `CRITICAL` | A separately authorized auth check succeeds with the accepted least-privilege policy and the original denial cause is resolved; retry success alone cannot clear a mode/environment violation | Safe response class, auth-policy/version digest, requested capability class, environment/mode decision, timestamps, correlation id, human-gate evidence where required | `RB-MON-AUT-001` must cover immediate containment, scope review, mode/endpoint verification, and security escalation | `S-AUTH` |
| `MON-AUT-002` | Scope or entitlement mismatch — `HIGH` | `UNHEALTHY` for affected data/capability; no fallback | A required accepted capability is denied or returned data indicates incomplete entitlement; undocumented/key-specific behavior is `UNCERTAIN` | The accepted key-specific contract and an authorized check prove the required bounded capability, followed by freshness and reconciliation checks | Capability class, safe entitlement reason, accepted contract reference, check digest, data completeness result, reconciliation result | `RB-MON-AUT-002` must define no-scope-expansion containment and Operator/vendor clarification path | `S-AUTH` |
| `MON-AUT-003` | Access-token expiry risk — `MEDIUM`, becoming `HIGH` when validity is insufficient for a required operation | `DEGRADED` before the accepted renewal boundary; `UNHEALTHY` when validity is absent/insufficient | Trusted expiry metadata crosses an approved renewal bound, is missing, or conflicts with the supplied clock; no duration is defined here | A valid token state is established through the accepted auth flow, clock evidence is trusted, and the next required operation fits the approved validity policy | Token-state digest only, issued/expiry times only if non-secret and approved, supplied-clock status, renewal-policy version, outcome reason | `RB-MON-AUT-003` must define proactive containment without logging token material or continuing on clock uncertainty | `S-AUTH` |
| `MON-AUT-004` | Refresh failed, revoked, rotated ambiguously, or reuse state uncertain — `HIGH` | `UNHEALTHY`; auth-dependent readiness false | Refresh returns an accepted failure class, revocation is observed, stored/latest-token identity is `UNKNOWN`, concurrent rotation conflicts, or the 30/40-minute vendor conflict remains material to the attempted policy | A newly authorized auth ceremony or accepted recovery establishes one current token lineage and invalidates ambiguity; dependent requests and data are revalidated | Safe refresh outcome class, lineage/policy digests, concurrency/correlation ids, revocation class, accepted key-policy reference, recovery attestation | `RB-MON-AUT-004` must address rotation races, revocation scope, storage incident handling, and no blind retry | `S-AUTH` |

### 6.3 DTO quarantine and unknown external values

| Code | Condition and severity | Health-state effect | Alert condition | Clear condition | Required evidence | Runbook | Sensitive profile |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MON-DTO-001` | Schema-invalid or unmappable payload quarantined — `HIGH` when it affects trusted state; otherwise `MEDIUM` | `UNHEALTHY` for the affected fact; aggregate may be `DEGRADED` only when completeness is proven unaffected | Mapper rejects a payload, required field is missing/invalid, coercion would be required, or provenance/schema is unknown | A corrected, versioned mapper reprocesses the immutable quarantined digest without coercion and reconciliation proves affected state complete; deletion or manual editing cannot clear | Payload digest, endpoint/schema/mapper versions, bounded validation codes, observed/recorded times, quarantine record id, affected-state and reconciliation results | `RB-MON-DTO-001` must cover quarantine access, triage, mapper rollback, reprocessing, and evidence preservation | `S-BROKER` |
| `MON-DTO-002` | Quarantine persistence or review backlog unavailable/over bound — `HIGH` | `UNHEALTHY`; ingestion trust and dependent readiness false | A quarantine write/read fails, record/digest linkage is broken, or unresolved entries exceed an approved age/count bound | Quarantine integrity is verified, every affected observation is accounted for, backlog is within approved bounds, and dependent projections are rebuilt/reconciled | Store operation class, integrity digest/check, bounded backlog counts/age, affected high-water marks, rebuild and reconciliation references | `RB-MON-DTO-002` must define fail-closed ingestion, durable recovery, ownership, and no payload exposure | `S-BROKER` |
| `MON-DTO-003` | Unknown external enum or status observed — `MEDIUM`, escalating to `HIGH` when lifecycle/finality/completeness is affected | `DEGRADED`; `UNHEALTHY` for dependent lifecycle or dispatch when semantics matter | A closed enum receives an unrecognized raw value, which must map to `UNKNOWN`; any attempted coercion is `CRITICAL` | An accepted mapping contract explicitly handles the value, preserved raw evidence is reprocessed, and impacted lifecycle/reconciliation checks pass | Raw-value digest rather than value in alert/report, field/schema/mapper versions, mapped `UNKNOWN`, affected-record count, contract decision and reprocessing evidence | `RB-MON-DTO-003` must cover quarantine, vendor/contract escalation, mapper update review, and prohibition on guessed mappings | `S-BROKER` |
| `MON-DTO-004` | Broker status finality or transition is uncertain — `HIGH` | `UNHEALTHY`; affected intent/order scope in `OPERATOR_REVIEW`, dependent dispatch blocked | A status is `UNKNOWN`, transitions conflict, REST/stream observations disagree, or apparent terminality lacks accepted evidence | Authoritative subsequent observations and an accepted transition contract resolve the state, with a passing reconciliation check | Observation digests and ordering evidence, mapped states, transition-contract version, discrepancy id, final reconciliation completion reference | `RB-MON-DTO-004` must forbid inferred cancellation/fill/finality and define observation/reconciliation recovery | `S-BROKER` |

### 6.4 Reconciliation drift

| Code | Condition and severity | Health-state effect | Alert condition | Clear condition | Required evidence | Runbook | Sensitive profile |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MON-REC-001` | Unexplained order/fill, position disagreement, duplicate effect, or ledger integrity drift — `CRITICAL` | `UNHEALTHY`; all affected dispatch stopped and final reports withheld | A corresponding `CRITICAL` reconciliation case opens or required integrity cannot be established | Named human review plus append-only resolution evidence and a qualifying `reconciliation.check_completed.v1` event with zero open critical/high cases; waiver cannot auto-clear | Case id, safe check/scope class, source digests/high-water marks, first/last seen, resolution evidence, qualifying completion event | `RB-MON-REC-001` must define immediate containment, evidence preservation, investigation, recovery, and independent verification | `S-BROKER` |
| `MON-REC-002` | Missing/stale execution observation or report mismatch — `HIGH` | `UNHEALTHY`; dependent dispatch and final reports withheld | A corresponding `HIGH` reconciliation case opens, an expected observation exceeds an approved bound, or report ties fail | Append-only case resolution and qualifying completion event prove the observation/report ties through the same high-water mark | Case id, expected/observed digests, freshness-policy version, report/source high-water marks, resolution and completion events | `RB-MON-REC-002` must cover stable-snapshot recovery, projection rebuild, report withholding, and escalation | `S-BROKER` |
| `MON-REC-003` | Non-position data-quality or timing drift — `MEDIUM` | `DEGRADED`; affected fact may be blocked | A corresponding `MEDIUM` case opens or an approved quality/timing invariant fails | The original case is append-only resolved after invariant recheck; any impact on execution state is separately escalated | Case id, bounded check/reason code, source digests, policy version, rerun result, impact assessment | `RB-MON-REC-003` must define triage, promotion to higher severity, and no auto-repair beyond ledger rebuild | `S-BROKER` |
| `MON-REC-004` | Reconciliation cannot run or completion evidence is absent — `HIGH` | `UNHEALTHY`; final report withheld | Required check cannot execute, source high-water mark is unstable, or no qualifying completion event exists | Required layers complete against a stable source and append a qualifying completion event | Attempt ids, required-check set, source high-water marks, safe failure reason, completion-event id/digest | `RB-MON-REC-004` must define retry budget, stable-source acquisition, report withholding, and human escalation | `S-BASE` |

### 6.5 Submission ambiguity

| Code | Condition and severity | Health-state effect | Alert condition | Clear condition | Required evidence | Runbook | Sensitive profile |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MON-SUB-001` | Place outcome ambiguous — `CRITICAL` | `UNHEALTHY`; intent enters `OPERATOR_REVIEW`; no automatic resubmission | Timeout, disconnect, 503/504, mixed response, crash boundary, or lost acknowledgement prevents proof of whether one logical effect occurred | Authoritative broker observations, idempotency evidence, and reconciliation prove exactly one known outcome or a named human resolves the case under an accepted contract; elapsed time is insufficient | Intent/correlation ids in restricted evidence, request digest, idempotency-key digest, attempt chronology, safe transport outcome, broker-observation digests, case/completion evidence | `RB-MON-SUB-001` must define freeze, query-before-action, duplicate prevention, human decision, and incident escalation | `S-BROKER` |
| `MON-SUB-002` | Replace or cancel outcome ambiguous — `CRITICAL` | `UNHEALTHY`; original and replacement/cancel scopes blocked | Acknowledgement or final state cannot be established after timeout, disconnect, mixed response, or conflicting observations | Accepted broker-state evidence establishes the actual final state and reconciliation passes; command acknowledgement alone cannot clear | Command/request digest, original observation high-water mark, attempt chronology, subsequent observation digests, discrepancy and completion evidence | `RB-MON-SUB-002` must prohibit assumed cancel/replace and define state-query and escalation sequence | `S-BROKER` |
| `MON-SUB-003` | Batch/group result partial or atomicity unknown — `CRITICAL` | `UNHEALTHY`; entire logical group blocked | Success and error entries coexist, members are missing, or accepted atomicity/relationship semantics cannot establish group state | Every member is authoritatively accounted for under an accepted group contract and group reconciliation passes | Group/request digest, expected/observed member counts without identifiers, per-member outcome digests, contract version, reconciliation evidence | `RB-MON-SUB-003` must contain the full group, prohibit compensating orders, and require human escalation | `S-BROKER` |

### 6.6 Rate limits and concurrency quotas

| Code | Condition and severity | Health-state effect | Alert condition | Clear condition | Required evidence | Runbook | Sensitive profile |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MON-RAT-001` | Request quota exhausted or HTTP 429 observed — `MEDIUM`, becoming `HIGH` when required freshness/reconciliation cannot be maintained | `DEGRADED`; `UNHEALTHY` when a required operation misses an approved bound | Accepted 429 class, quota remaining at/below an approved bound, or required operation deferred beyond its bound | Broker-advertised reset has passed, a bounded authorized probe succeeds, and freshness/reconciliation obligations are restored; reset time alone does not clear | Resource-class code, safe response class, sanitized quota/reset values if approved, policy version, deferred-operation count, freshness/reconciliation result | `RB-MON-RAT-001` must define broker-directed backoff, priority, no retry storm, and escalation | `S-BROKER` |
| `MON-RAT-002` | Stream concurrency quota exhausted — `HIGH` when required stream unavailable; otherwise `MEDIUM` | `UNHEALTHY` for required stream; otherwise `DEGRADED` | Connection is denied for quota/concurrency, or required stream cannot be established within accepted policy | Required stream is established and snapshot/stream continuity and freshness checks pass | Stream/resource class, safe response class, sanitized concurrency values if approved, connection chronology, continuity/freshness evidence | `RB-MON-RAT-002` must define connection ownership, bounded reconnect, snapshot fallback only if contractually sufficient, and escalation | `S-BROKER` |
| `MON-RAT-003` | Quota identity or rate-limit headers unknown/inconsistent — `HIGH` when safe budgeting depends on them; otherwise `MEDIUM` | `UNHEALTHY`; affected scheduling readiness false | Required headers are absent/malformed/conflicting, or aggregation across processes/keys/users is unresolved for the intended topology | Accepted broker/auth/deployment contract establishes quota identity and an authorized observation confirms consistent bounded metadata | Header-presence/result codes without raw headers, topology-policy digest, resource class, observation digests, accepted contract reference | `RB-MON-RAT-003` must prohibit guessed quota sharing and define conservative containment and Operator/vendor escalation | `S-BROKER` |

### 6.7 Database connectivity, latency, storage, and backup

| Code | Condition and severity | Health-state effect | Alert condition | Clear condition | Required evidence | Runbook | Sensitive profile |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MON-DB-001` | Required PostgreSQL connectivity unavailable — `HIGH`; `CRITICAL` if durable outcome is uncertain | `UNHEALTHY`; ledger/intent/report readiness false | A required connection or transaction cannot be established within accepted retry policy, wrong/unknown environment source is detected, or commit outcome is ambiguous | Correct environment-bound connectivity succeeds, transaction/durability state is established, replay completes, and integrity/reconciliation checks pass | Environment/config digest, dependency/operation class, attempt chronology, safe SQLSTATE class if approved, transaction outcome class, replay/integrity results | `RB-MON-DB-001` must cover no cross-environment fallback, ambiguous commit recovery, replay, and escalation | `S-DB` |
| `MON-DB-002` | Database operation latency above approved bound — `MEDIUM`, becoming `HIGH` when a safety/freshness deadline is threatened | `DEGRADED`; `UNHEALTHY` for operations whose approved deadline cannot be met | Versioned operation-class latency exceeds its approved bound or latency evidence is missing for a required operation | A new approved observation window is within bound and queued work, freshness, and reconciliation obligations are recovered | Operation class, histogram/window policy, supplied-clock status, bounded latency summary, backlog/freshness/reconciliation results | `RB-MON-DB-002` must define load containment, no unsafe timeout retry, and escalation by affected invariant | `S-DB` |
| `MON-DB-003` | Storage capacity, WAL, or growth margin below approved bound — `HIGH` | `UNHEALTHY`; new effect-producing work blocked before durability is endangered | Approved capacity/growth forecast crosses its bound, allocation cannot be measured, or write durability risk is `UNKNOWN` | Capacity and growth margin are verified above accepted clear bounds and ledger/integrity checks pass | Capacity-policy version, bounded utilization/growth values, observation times, maintenance/action evidence, integrity result | `RB-MON-DB-003` must define admission stop, evidence preservation, capacity recovery, and no destructive cleanup of immutable records | `S-DB` |
| `MON-DB-004` | Backup missing, failed, stale, or integrity unknown — `HIGH` | `UNHEALTHY` for certification/recovery readiness; does not claim primary data loss | Scheduled backup evidence is absent/failed, age exceeds an approved bound, or digest/encryption/access evidence cannot be established | A new backup completes under accepted policy and its integrity metadata is verified; backup completion alone does not prove restore | Backup-policy/version digest, schedule occurrence id, start/end times, safe outcome, backup artifact digest/reference, integrity-check result | `RB-MON-DB-004` must cover failure containment, retention/access review, retry ownership, and escalation | `S-DB` |
| `MON-DB-005` | Restore verification absent, failed, or recovery objectives unproven — `HIGH` | `UNHEALTHY` for recovery/certification readiness | Required restore exercise is missing/overdue under approved policy, fails, or cannot reproduce the required high-water mark and integrity checks | An isolated, authorized restore verification passes the accepted recovery procedure and records exact high-water-mark/integrity evidence | Backup/reference digest, restore-procedure version, isolated target class, recovered high-water mark, integrity/replay/reconciliation results, verifier attestation | `RB-MON-DB-005` must define isolated non-production restore, validation, cleanup, and failure escalation | `S-DB` |

### 6.8 Worker heartbeat and scheduler

| Code | Condition and severity | Health-state effect | Alert condition | Clear condition | Required evidence | Runbook | Sensitive profile |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MON-WRK-001` | Required worker heartbeat missed or stale — `HIGH` | `UNHEALTHY`; worker-owned capability readiness false | Heartbeat age exceeds an approved worker-class bound, generation/lease identity conflicts, or heartbeat evidence is missing | One authoritative worker generation is established, heartbeat and progress resume, abandoned leases/work are reconciled, and duplicate ownership is excluded | Worker-class/generation token digest, last heartbeat/progress times, lease-policy version, queue/high-water marks, recovery/reconciliation result | `RB-MON-WRK-001` must cover fencing, abandoned work, duplicate-worker prevention, restart, and escalation | `S-RUNTIME` |
| `MON-WRK-002` | Worker alive but not making progress — `HIGH` | `UNHEALTHY`; affected queue/stage blocked | Heartbeats continue while progress high-water mark is unchanged beyond an approved bound, retry budget exhausts, or poison work repeats | The blocking item is safely quarantined or processed, progress advances, retry/lease state is consistent, and affected work reconciles | Heartbeat and progress high-water marks, bounded queue age/count, retry-policy version, safe reason codes, quarantine/reconciliation evidence | `RB-MON-WRK-002` must define poison-item isolation, retry exhaustion, no evidence deletion, and escalation | `S-RUNTIME` |
| `MON-SCH-001` | Required schedule occurrence missed or late — `HIGH` when safety/reconciliation/reporting cadence is affected; otherwise `MEDIUM` | `UNHEALTHY` for required cadence; otherwise `DEGRADED` | A versioned schedule occurrence has no uniquely correlated start/completion within its approved window, or clock state is not trusted | The missed occurrence is explicitly accounted for, safe catch-up policy is applied, dependent checks/reports complete, and clock health is known | Schedule/version digest, occurrence id, intended/actual times, supplied-clock status, catch-up decision, dependent completion high-water marks | `RB-MON-SCH-001` must define missed-run accounting, safe catch-up, no time inference, and escalation | `S-RUNTIME` |
| `MON-SCH-002` | Duplicate or overlapping schedule occurrence — `HIGH` | `UNHEALTHY`; duplicate scope fenced before effects | More than one owner claims an occurrence, idempotency/lease identity conflicts, or overlap violates accepted policy | One owner/outcome is established, duplicates are fenced, every attempted effect is accounted for, and reconciliation passes | Occurrence and owner-token digests, lease/idempotency policy version, attempt chronology, effect counts, reconciliation evidence | `RB-MON-SCH-002` must define fencing, duplicate suppression, ambiguous-effect handling, and escalation | `S-RUNTIME` |
| `MON-SCH-003` | Scheduler or supplied-clock state unknown/uncertain — `HIGH` | `UNHEALTHY`; time-dependent effects blocked | Clock source is unavailable, skew exceeds an approved bound, timezone/session/calendar version conflicts, or next-fire computation is not reproducible | Trusted supplied-clock evidence and versioned schedule/calendar inputs reproduce the intended occurrences, followed by missed/duplicate checks | Clock-source class, skew result, schedule/calendar/timezone version digests, computed occurrence set digest, missed/duplicate check results | `RB-MON-SCH-003` must define time-source containment, no wall-clock fallback, recomputation, and escalation | `S-RUNTIME` |

## 7. Deduplication, correlation, and escalation

### 7.1 Deduplication

An alert episode deduplicates only on:

`(condition_code, environment, mode, component, safe_scope_class,`
`detector_policy_version, active_episode)`

The safe scope class is a bounded category, not a broker account, order, fill,
symbol, database resource, host, or raw external value. Scope-specific detail
belongs behind the access-controlled evidence link. A new episode begins only
after the prior episode has condition-specific clear evidence. Restarts,
acknowledgements, notification retries, and repeated observations increment
the occurrence count; they do not create a false clear or erase first-seen
time.

Related conditions remain separate codes. For example, a refresh failure may
cause auth denial and stale data; deduplication must not collapse those facts
into one alert or hide the causal chain.

### 7.2 Correlation and causation

- One root occurrence id anchors an incident chain.
- Every derived alert carries the immediate causation id and shared
  correlation id required by `EVENT_MODEL.md`.
- Submission attempts use the existing intent/idempotency identity in
  restricted evidence, never as a metric label.
- Database, worker, and scheduler conditions correlate through safe operation
  and occurrence ids, not timestamps alone.
- A report links to alert/reconciliation event ids and source high-water marks.
  Nearby timestamps are not identity evidence.
- Correlation never implies causation. The detector must record
  `cause=UNKNOWN` until evidence establishes a causal edge.

### 7.3 Escalation and de-escalation

- `CRITICAL` conditions require immediate human attention and blocking.
- `HIGH` conditions block the affected dependent dispatch and final report.
- `MEDIUM` conditions route according to an approved owner/response policy;
  they escalate when a catalog row's explicit higher-severity impact occurs.
- Repetition, duration, business hours, owner, paging route, response
  objective, and numeric escalation thresholds remain unresolved. No default
  is proposed.
- Severity is monotonic within an active episode unless append-only evidence
  proves the higher-severity impact no longer applies. Notification
  acknowledgement or silence cannot de-escalate health or authorize effects.
- No alert may auto-submit, replace, cancel, offset, or otherwise repair an
  order. No database or scheduler recovery may replay an ambiguous external
  effect.
- Runbooks and named owners must exist and be independently reviewed before
  any condition is considered operationally ready. Every runbook id in §6 is
  a requirement; no runbook is claimed to exist here.

## 8. Immutable reporting implications

1. Occurrence, acknowledgement, escalation, evidence attachment, and clear are
   distinct append-only events. Original facts are never overwritten.
2. Operations reports are projections at an explicit event high-water mark.
   They contain condition code, severity, health effect, certainty, safe scope
   class, first/last occurrence, count, current alert state, runbook id,
   evidence reference/digest, environment, mode, and taxonomy version.
3. Reports must preserve `REPORTING.md` schema version, supplied-clock
   generation time, producer version, data cutoff, canonical content digest,
   source high-water mark, mode banner, and reconciliation result.
4. A final report is withheld when a relevant `CRITICAL`/`HIGH` condition is
   open, health evidence is `UNKNOWN`/`UNCERTAIN`, a required projection lags,
   or reconciliation completion evidence is absent. Preliminary output carries
   the exact warning `UNRECONCILED — DO NOT USE FOR EXECUTION`.
5. Submission ambiguity is reported as unresolved state, never success,
   rejection, cancellation, replacement, or fill by inference.
6. Unknown broker enum/status values remain mapped to `UNKNOWN`. General
   reports carry a bounded field/reason code and digest, not the raw value.
7. A clear event does not remove an incident from later reports. Reports
   distinguish active and historically resolved episodes and retain the
   resolution evidence link.
8. Alert absence is not proof of health. A `HEALTHY` report requires explicit,
   current, `KNOWN` assessments for every required detector in its declared
   coverage manifest.
9. Reporting, retention, immutable archive, signing, access controls, and
   deletion policies remain unresolved. This taxonomy requires immutability of
   evidence semantics but does not select storage or claim regulatory
   sufficiency.
10. Sensitive-data profiles in §5 apply to events, logs, metrics, alerts,
    notifications, dashboards, reports, screenshots, and exported evidence.

## 9. Unresolved dependencies and non-assumptions

| Dependency | Blocks | Required resolution path |
| --- | --- | --- |
| `P2-A` broker research: complete status transitions, stream heartbeat/replay/gap behavior, entitlement/data latency, rate-limit identity, ambiguous outcomes, batch atomicity, retention | Operational detectors and clear evidence for `MON-BRK-*`, `MON-DTO-003/004`, `MON-SUB-*`, `MON-RAT-*`; broker-data freshness bounds | First-party documentation and later separately authorized evidence at the plan's applicable gates; never infer behavior |
| `P2-B` auth architecture: key-specific scopes, token/refresh policy, 30/40-minute conflict, revocation and concurrency behavior, secret handling | `MON-AUT-*` detector policy, evidence handling, and runbooks | Proposed auth ADR, independent review, Operator gate; no credential use by this task |
| `P2-C` DB/deployment research: provider/topology, environment naming, connection source, backup/PITR/restore capabilities, latency/capacity/recovery objectives | `MON-DB-*` bounds, environment labels, evidence source, backup/restore runbooks | Provider-neutral contract and later Operator selection; no provisioning or connection material |
| `P2-D` through `P2-G` frozen event/DTO/reconciliation/idempotency contracts | Exact event schemas, safe fields, detector inputs, and wiring for broker conditions | Gate `H2` contract freeze after independent verification |
| Human operations decisions | Owners, routes, paging hours, response objectives, maintenance windows, numeric alert/clear/escalation bounds, runbook acceptance, retention/access policy | Explicit Operator decisions; absence means not operationally ready |

No threshold, broker guarantee, token policy, database capability, retry safety,
backup property, worker lease behavior, or scheduler guarantee is resolved by
this taxonomy.

## 10. Design-validation checklist

| Validation | Result and evidence |
| --- | --- |
| Requested domains covered | `MON-BRK-*` connectivity/freshness; `MON-AUT-*` auth/refresh; `MON-DTO-*` quarantine/unknown values; `MON-REC-*` drift; `MON-SUB-*` ambiguity; `MON-RAT-*` limits; `MON-DB-*` connectivity/latency/storage/backup; `MON-WRK-*` heartbeat/progress; `MON-SCH-*` scheduler |
| Per-condition fields complete | Every §6 row contains stable code, severity, health effect, alert condition, clear condition, evidence, runbook id/requirement, and sensitive-data profile |
| Health compatibility | §2 separates health, certainty, readiness, and existing `BLOCKED` run/effect outcome; `UNKNOWN`/`UNCERTAIN` fail closed |
| Contract compatibility | No auto-repair; report withholding and qualifying reconciliation completion preserved; alert acknowledgement does not authorize dispatch |
| Phase/gate compatibility | §3 preserves `DRY_RUN`-only current authority, separates environment from mode, and requires `H1`/`H2` human review without claiming either passed |
| Safety compatibility | No credential, broker/account/network action, provisioning, `SIM`, order submission, or `LIVE`; wrong/unknown authority fails closed |
| Sensitive-data review | §5 forbids secrets, tokens, account ids, raw broker payloads, connection material, raw statuses, and unbounded labels/fields throughout |
| Threshold integrity | All numeric thresholds, owners, routes, and response objectives remain unresolved; no behavior is invented |
| Immutable reporting | §8 requires append-only lifecycle evidence, high-water-marked projections, canonical digest semantics, and preserved incident history |
| Implementation boundary | Proposal only: no code, tests, migrations, wiring, credentials, network, or provisioning |

## 11. Acceptance boundary

This document remains `PROPOSED`. Passing document review would establish only
that the taxonomy is sufficiently complete for contract reconciliation. It
would not establish that any detector, alert, clear, runbook, dashboard,
report, broker integration, authentication flow, database service, worker, or
scheduler exists or works. Only the human Operator can make the plan's named
acceptance decisions, and none can override `CURRENT_STATE.md` while it denies
Phase 2, credentials, broker/network activity, TradeStation `SIM`, order
submission, and `LIVE`.
