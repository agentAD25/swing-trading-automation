# Phase 1C Coordinator Reconciliation

- Date: 2026-09-25
- Baseline: `cursor/phase-1a-governance-e1ba` at `ae1aa85`
- Status: Reconciled for review; **not `PHASE1_ACCEPTED`**
- Authorized mode: `SIM` only
- `LIVE`, Phase 2, credentials, accounts, order submission, and foundation
  implementation: unauthorized

## Integrated inputs

| Workstream | Source branch and commits | Integrated output |
| --- | --- | --- |
| Broker research | `cursor/phase-1b-broker-research-e23f`: `f5e23b0`, `c12a3ca` | `BROKER_CONTRACT.md` and journal evidence |
| Architecture | `cursor/phase-1b-architecture-3aa6`: `fd5adc3`, `ba41e14`, `edf2d96`, `032794e` | Proposed contracts, ADR-0001, deterministic fixture, and validation evidence |
| Failure model | `cursor/phase-1b-failure-model-4ca4`: `fd5e37d` | `FAILURE_MODEL.md` |

The four architecture commits are one dependent series; `032794e` validates
documents and fixtures introduced by its three ancestors. All four are
therefore included rather than treating the validation commit as standalone.

## Agreements

All inputs agree on these boundaries:

1. `SIM` is the only named execution mode and does not prove environment
   isolation. `LIVE` remains unauthorized.
2. Research and document validation grant no authority to implement, obtain
   credentials, access accounts, submit orders, deploy, or begin Phase 2.
3. Unknown or ambiguous authorization, mode, state, data quality, dispatch
   result, or reconciliation state must fail closed.
4. Intent, command acknowledgement, order state, and fill are distinct.
   Ambiguous effects require reconciliation, not a retry under a new identity.
5. An append-only event ledger, rebuildable projections, atomic intent/outbox
   boundary, stable internal idempotency, and deterministic evidence are a
   coherent broker-neutral proposal.
6. The WDC fixture is synthetic conformance data. It proves neither strategy
   efficacy, market truth, broker compatibility, nor execution safety.
7. Material contracts remain Proposed until named human deciders accept them.

## Reconciled conflicts and stale statements

| ID | Conflict | Disposition |
| --- | --- | --- |
| RC-01 | The architecture branch's `CURRENT_STATE.md` said all broker facts were unresearched. | Superseded by the scoped public-document findings in `BROKER_CONTRACT.md`; twelve production-critical broker behavior groups remain unresolved. |
| RC-02 | `SIM_LIVE_BOUNDARY.md` made no assertion about TradeStation host separation. | Updated to acknowledge the documented v3 hosts while retaining FM-07: a URL or mode label is not runtime proof of endpoint, account, DNS, proxy, credential, or network isolation. |
| RC-03 | Architecture text deferred any broker adapter until behavior was researched. | “Researched” now means the required behavior is evidenced and accepted, not merely that a research document exists. The current handoff is insufficient for an adapter contract. |
| RC-04 | FM-09 called broker simulation behavior unresearched. | Read as a point-in-time review of Phase 1A. Public documentation now establishes separate hosts, fake accounts/money, and instant simulated fills; isolation guarantees and fidelity remain unverified. |
| RC-05 | The authority hierarchy places explicit human instructions above global boundaries, allowing a possible conflict with `SIM`-only language (FM-03). | Unresolved critical governance conflict. Until a human-approved safety constitution defines non-overridable prohibitions and approval mechanics, the narrowest interpretation applies: no side effect and no `LIVE`. |
| RC-06 | The design defines some fail-closed and idempotency behavior while FM-11/FM-12 say it is undefined. | The design partially answers the logical contract. It does not supply freshness budgets, fencing, external enforcement, broker retry/finality semantics, or verified implementation. FM-11/FM-12 therefore remain blockers, narrowed rather than closed. |
| RC-07 | Architecture validation covered fourteen design contracts, not later broker and failure-model inputs. | Phase 1C validates the complete integrated set separately. Earlier evidence remains evidence only for its stated scope. |
| RC-08 | A `Trade` uses an account scope while the Phase 1B model excludes brokerage account identifiers. | An opaque, non-broker account-scope identifier may be a future domain partition, but its identity, authorization, sensitivity, retention, and mapping are unresolved. No account identifier may be inferred or introduced. |
| RC-09 | The LIVE gate could be read as saying TradeStation research is complete. | “Completed” means every listed production-facing behavior has affirmative evidence. The current twelve unresolved groups fail that prerequisite. |

Historical statements in `FAILURE_MODEL.md` are preserved because that review
is explicitly scoped to Phase 1A at `ae1aa85`. This document records which
findings are narrowed by later evidence; it does not rewrite the adversarial
input or claim its blockers are remediated.

## Unsupported assumptions prohibited

The integrated set does not support any assumption that:

- `OrderConfirmID` is equivalent to the internal idempotency key, has a known
  retention window, or makes timeout retries safe;
- an HTTP 200, place/replace/cancel acknowledgement, or successful confirmation
  proves complete success or terminal order state;
- the documented SIM URL, fake accounts, or instant fills prove runtime
  isolation, realistic fills, entitlement, or LIVE parity;
- streams provide replay, sequencing, gap-free reconnect, or an authoritative
  snapshot-to-stream handoff;
- public default scopes or quotas describe a future API key;
- a `CONTRACT` decision-register label means an ADR is Accepted;
- fixture, link, keyword, or secret-pattern validation certifies operational
  safety; or
- a repository edit or unauthenticated instruction can grant phase authority.

## Broker limitations carried into design

Any future adapter must explicitly handle or remain blocked by:

- instantaneous documented SIM fills and unknown partial-fill/reject/race
  fidelity;
- incomplete status enumeration, transition, correction, and ordering rules;
- command acknowledgements that do not establish terminal state;
- item-level errors inside HTTP-success responses;
- unknown timeout recovery and `OrderConfirmID` semantics;
- stream replay, gap, heartbeat, ordering, and reconnect uncertainty;
- rolling request quotas, concurrent stream limits, 429 handling, and
  key-specific limits;
- 90-day historical-order and 600-item unpaginated read limits;
- conflicting official refresh-token interval and default-scope statements;
  and
- unresolved account, entitlement, precision, time, group atomicity, and
  retention contracts.

## Exact freeze blockers

The contracts must not be marked `PHASE1_ACCEPTED`, and foundation work remains
frozen, until all affected safety boundaries have affirmative evidence:

1. **Authority:** named authenticated owners and ADR deciders; approval source,
   quorum, scope, expiry, revocation, delegation, and emergency rules; resolution
   of FM-01 through FM-03.
2. **Enforcement and change control:** non-bypassable controls outside Markdown,
   immutable baseline adoption, role binding/separation, protected changes,
   trusted CI/provenance, and assurance ownership (FM-04–FM-06, FM-14, FM-24).
3. **Execution isolation:** independently verified SIM endpoint, account class,
   DNS/proxy/network and artifact identity; a zero-order-attempt choke point;
   safe degraded behavior (FM-07–FM-09, FM-11).
4. **External-effect correctness:** all twelve
   `BROKER_BEHAVIOR_UNRESOLVED` groups, broker state mapping, stable lookup,
   retry/idempotency/finality, fencing, reconciliation, shutdown, rollback, and
   restart contracts (FM-12, FM-13, FM-22).
5. **Credentials and telemetry:** approved credential-exclusion or handling
   contract, comprehensive scanning/redaction/rotation/retention, and
   observability that detects failures without leaking data (FM-10, FM-15,
   FM-23).
6. **Domain requirements:** accepted strategy/data and risk/operations
   research; account-scope model; market calendar, rounding/tick/lot, fees,
   costs, limits, thresholds, incident owners, recovery objectives, and test
   oracles.
7. **Evidence and fixtures:** source preservation/integrity rules,
   untrusted-content controls, conflict acceptance rubric, fixture provenance,
   mutation/fault coverage, and independent verification (FM-16–FM-18, FM-20,
   FM-21).
8. **External obligations:** named legal/security/compliance review of
   jurisdiction, automation, entitlements, licensing, privacy, retention, and
   redistribution (FM-19).
9. **Acceptance:** human acceptance of ADR-0001 and any required dedicated
   ADRs, with a phase transition separately authorized in `CURRENT_STATE.md`.

## Operator and human decisions required

Humans must select and own: the authority/acceptance model; technology,
persistence, queue, deployment, and network topology; data vendor, calendar,
strategy, universe, costs, and revision policy; risk/capital/kill limits;
account-scope and broker-adapter policy; retention, backup, recovery, and
availability objectives; alert routes, staffing, incidents, changes, and
waivers; report recipients; SIM certification deciders; and applicable legal,
security, compliance, and licensing controls.

No `LIVE` decision is requested in Phase 1C.

## Freeze readiness

The integrated documentation is ready for human review as a coherent proposal.
It is **not ready to unfreeze implementation**, certify SIM, authorize an
account-capable adapter, enter Phase 2, or consider `LIVE`. The correct status
is `PROPOSED / FREEZE_BLOCKED`, not `PHASE1_ACCEPTED`.
