# Phase 2 Group 1 (`P2-0`) Coordinator Reconciliation

- Date: 2026-09-29
- Baseline: canonical `main` `1ecbbe6d487d97195fde393b05c9499357599bdb`
- Integration branch: `cursor/p2-0-integration-1f76`
- Status: Reconciled for review; **not Gate `H1` passed**; **not Phase 2
  started**; **not credential, `SIM`, or `LIVE` authorization**
- Authorized mode: local, deterministic, fixture/mock-only, non-network
  `DRY_RUN` only
- `LIVE`, TradeStation `SIM`, credentials, accounts, broker/network activity,
  order submission, real capital, ADR acceptance, provider selection, and
  Phase 2 implementation: unauthorized

This document is the coordinator output named by `PHASE_2_PLAN.md` §9. It
does not rewrite specialist evidence, does not accept an ADR, and does not
change phase authority. Independent verification of the four specialist heads
is prior evidence; this file does not re-certify those PRs and does not
self-certify this integration.

## Integrated inputs

| Workstream | PR | Verified head | Isolated merge | Integrated output |
| --- | --- | --- | --- | --- |
| `P2-J/r1` monitoring taxonomy | #8 | `a91bd24ed921d148448338ae1980647f27bf355a` | `--no-ff` `5ac60d5` | `docs/P2_MONITORING_TAXONOMY.md` |
| `P2-A/r1` broker research | #9 | `f0dca4b30ae2f51f54a56d1c073e02e90347847a` | `--no-ff` `c71981e` | `docs/P2_BROKER_RESEARCH.md`, `docs/TRADESTATION_CLIENT_EXPERIENCE_QUESTIONS.md` |
| `P2-C/r1` managed PostgreSQL | #10 | `a7900c253404eeefacfd6cd51416a3e4d4986b1d` | `--no-ff` `fa07532` | `docs/DB_DEPLOYMENT.md` |
| `P2-B/r1` auth architecture | #11 | `595f431473ea136fb4519abda01e004a265ddcb1` | `--no-ff` `7a34ad6` | `docs/AUTH_ARCHITECTURE.md` |

All four heads are ancestors of this branch. Specialist commit lineage is
preserved. This branch is **not** merged to `main`.

Independent verification (read-only, prior runs):

| PR | Verdict | Residual coordinator notes |
| --- | --- | --- |
| #8 | `P2_J_R1_VERIFICATION_PASS` at `a91bd24` | None outstanding from that verifier |
| #9 | `PASS` at `f0dca4b` | N2 dated `BROKER_CONTRACT.md` pointer; N3 `offline_access` conflict coverage |
| #10 | `PASS` at `a7900c2` | N1 ranking vs plan §7.3 |
| #11 | `PASS` at `595f431` (F1–F4 / N1–N9 closed) | N10 journal/`CURRENT_STATE` handoff; residual U-07 wording |

## Authority and non-authorizations

`docs/AGENT_AUTHORITY.md` and `docs/CURRENT_STATE.md` remain governing.
`PHASE1_COMPLETE` / bounded `PHASE1_ACCEPTED` grant no Phase 2, credential,
broker, TradeStation `SIM`, order, deployment, real-capital, or `LIVE`
capability.

`P2-0` is Group 1 of `PHASE_2_PLAN.md` §8/§9: documentation only. This
reconciliation:

- keeps every specialist document `PROPOSED` / research-only;
- does not pass Gate `H1`;
- does not open Group 2, `H2`, `G1`, `G2`, or `G3`;
- does not select a managed PostgreSQL provider;
- does not rewrite `PHASE_2_PLAN.md` Gate G1 text;
- records N10 evidence in `CURRENT_STATE.md` and this journal **without** a
  phase-authorization change.

The Phase 1 tagged candidate (`phase1-accepted-abc1fb6` → `abc1fb6` /
`cb5fc1f9`) and `phase1-complete` (`249b8eb`) are unchanged.

## Agreements

The four inputs agree on these boundaries:

1. `DRY_RUN` is the only currently authorized execution mode. TradeStation
   `SIM` is reserved and unauthorized. `LIVE` is unauthorized and has no
   designed path in these r1 artifacts.
2. Research and taxonomy grant no authority to implement, obtain credentials,
   access accounts, submit orders, provision databases, or begin Phase 2.
3. Unknown, conflicting, or missing authorization, mode, endpoint, scope,
   secret-store health, environment source, or broker behavior fails closed.
4. All twelve `BROKER_BEHAVIOR_UNRESOLVED` groups remain unresolved. Public
   documentation narrows some groups; none are closed.
5. Default non-expiring TradeStation refresh tokens are a documented default
   and are **rejected** by the proposed auth G1 for any `offline_access`
   family. That is agreement on the fact plus a fail-closed control, not a
   source conflict.
6. Database secret-store and network mechanics are deferred to P2-B. Auth
   does not select a cloud database provider. Monitoring does not invent
   numeric alert bounds.
7. Material contracts remain Proposed until the human Operator accepts them
   at a named gate. This author cannot accept them.

## Cross-document reconciliation

### Auth ↔ broker

| Topic | Finding | Disposition |
| --- | --- | --- |
| Refresh rotation 30 vs 40 minutes | `BROKER_CONTRACT.md` finding 9, `P2_BROKER_RESEARCH.md` `BROKER_EVIDENCE_CONFLICT`, `AUTH_ARCHITECTURE.md` U-01, `P2_MONITORING_TAXONOMY.md` `MON-AUT-004` | Agreement. Unresolved. Client Experience before G1. |
| Default API scopes three-way split | Broker finding 10 / research conflict; auth U-02 | Agreement. Unresolved. |
| `offline_access` required-unqualified vs refresh-enabling | Auth U-17 recorded; P2-A/r1 stated the refresh-enabling wording only (verifier N3) | **Clear coverage gap, closed here.** Third `BROKER_EVIDENCE_CONFLICT` plus Client Experience question 72. No winner chosen. |
| Default non-expiring refresh tokens | Broker known default; auth G1 rejects unconstrained non-expiring tokens for `offline_access` | Not a documentation inconsistency. Auth is stricter and fail-closed. |
| Plan §6.3 sequential vs §8 Group 1 parallel | Auth recorded that P2-A/r1 is specified as upstream while the DAG runs both in parallel; auth used `BROKER_CONTRACT.md` only | **Resolved by this integration.** Both heads are now ancestors of this branch. Auth's r1 source choice remains valid prior evidence. |
| Auth still says it does not treat an unmerged P2-A branch as fact | Stale relative to this branch after `--no-ff` merge | Recorded here; specialist file not rewritten. P2-A/r1 is now in-tree evidence. |

### Auth ↔ DB

| Topic | Finding | Disposition |
| --- | --- | --- |
| Connection-string source | `DB_DEPLOYMENT.md` §7.1 proposes opaque `SWINGTRADE_{DEV,TEST,SIM}_DATABASE_URL_REF`; `LIVE` ref must be absent | **Clear P2-0 naming gap, closed here** in `config/README.md` and `.env.example` comments. Local `DRY_RUN` continues to use existing `SWINGTRADE_DATABASE_URL`. No required new variable. |
| Secret store | DB defers store/workload identity to P2-B; auth requires a workload-writable versioned CAS store and forbids env copies for broker secrets | Agreement on deferral. Store product is not selected. |
| Cursor Dashboard start-time secrets vs CAS | Auth U-10 vs plan G1 | **`P2_0_CONTRACT_CONFLICT` C1.** Not an auth↔DB disagreement. See Conflicts. |
| Environment isolation | Both require separate DEV/TEST/SIM identities and reject LIVE configuration | Agreement. |

### DB ↔ monitoring

| Topic | Finding | Disposition |
| --- | --- | --- |
| Environment labels | Monitoring declined to freeze names because P2-C was unaccepted; P2-C now proposes `DEV`/`TEST`/`SIM`/`LIVE` with `LIVE` unconfigured | Complementary. Names remain proposed, not operational. |
| Numeric bounds | `MON-DB-*` require approved bounds and stay `UNKNOWN` until then; DB §3 proposes a five-minute SIM failover **project objective**, labeled non-contractual | Not a conflict. Monitoring correctly does not adopt the proposal as an alert bound. |
| Backup/PITR | DB cites first-party restore-to-new-instance and product caveats; `MON-DB-004/005` require approved policy and restore exercises | Complementary. No bound invented. |
| Provider ranking | DB ranks RDS recommended / Cloud SQL alternative / Supabase+Neon deferred; monitoring remains provider-neutral | Complementary. Ranking is not selection (see verifier N1 overlay). |

### Broker ↔ monitoring

| Topic | Finding | Disposition |
| --- | --- | --- |
| 30/40-minute rotation | `MON-AUT-004` cites the already-recorded vendor conflict | Agreement. |
| Rate-limit identity | `MON-RAT-*` treat aggregation as unknown (`BROKER_BEHAVIOR_UNRESOLVED` item 10) | Agreement. |
| Stream heartbeat/replay | `MON-BRK-002/004` blocked on P2-A groups 4 and related unknowns | Agreement. Groups 4, 11, 12 narrowed, not closed. |
| `offline_access` / U-17 | Monitoring §9 P2-B row named scopes/refresh/30/40/revocation/secrets, not the unqualified-required table conflict | **Clear coverage gap, closed here** with a §9 dependency row. Taxonomy still chooses no winner. |
| Worker/scheduler ownership | Monitoring §9 already records that no plan workstream owns `MON-WRK-*`/`MON-SCH-*` producers | Preserved. Operator/coordinator assignment remains due before `P2-J/r2`. |

## Verifier notes addressed

### P2-C ranking vs plan §7.3 (PR #10 N1)

`PHASE_2_PLAN.md` §7.3 acceptance criteria say the matrix contains no ranking
or recommendation of a single winner. `DB_DEPLOYMENT.md` §2 is explicitly
`RECOMMENDED` / `ALTERNATIVE` / `DEFERRED` and states that the **later
assigned P2-0/P2-C task** requested that view.

**Disposition: overlay, not `P2_0_CONTRACT_CONFLICT`, not an H1 blocker.**
The later explicit P2-0 authorization requested an engineering
recommendation. The ranking remains labeled non-ADR, non-selection, and
non-procurement. This coordinator does **not** rewrite plan §7.3 and does
**not** treat merge of this branch as Human Decision Gate 2.

### `offline_access` conflict coverage (PR #9 N3)

P2-A/r1 recorded `offline_access` as required for refresh (TS5/TS8) and did
not record the Scopes table's unqualified **required** label (TS6). P2-B/r1
U-17 already treats that split as material and chooses no winner.

**Disposition: coverage completed in this reconciliation** by adding the
third `BROKER_EVIDENCE_CONFLICT` in `P2_BROKER_RESEARCH.md`, Client
Experience question 72, a dated pointer in `BROKER_CONTRACT.md`, and a
monitoring §9 row. Failure direction remains fail-closed (exchange fails /
G2 profile unused) if the unqualified table is the live key contract.

### N10 coordinator journal / current-state handoff (PR #11)

P2-B/r1 correctly did not edit `CURRENT_STATE.md` or
`ENGINEERING_JOURNAL.md`. Consequences assigned those records to the
coordinator at H1.

**Disposition: evidence-only updates in this commit.** They record that
P2-0 Group 1 documents exist on this isolated branch, name U-10 as an open
contract conflict, and **do not** authorize Phase 2, credentials, SIM, G1,
or `LIVE`.

## Conflicts recorded (`P2_0_CONTRACT_CONFLICT`)

Material disagreement that this coordinator must not silently resolve:

### C1 — `P2_0_CONTRACT_CONFLICT` — plan G1 Cursor Dashboard secrets vs proposed CAS store (U-10)

- **Plan:** Gate G1 says the Operator provisions SIM OAuth credentials “via
  Cursor Dashboard secrets” (`PHASE_2_PLAN.md` §8).
- **Proposal:** `AUTH_ARCHITECTURE.md` U-10 / G1 item 5 require a
  workload-writable, versioned compare-and-swap secret store and forbid
  environment-variable copies. Cursor documents Dashboard secrets as
  start-time injection; running agents do not refresh them.
- **Why material:** the plan-named mechanism cannot satisfy the proposed
  store contract. Substituting a product or silently narrowing plan G1 would
  be an unauthorized architecture decision.
- **Disposition:** unresolved. **Do not amend `PHASE_2_PLAN.md`.** Operator
  decision is required before H2/G1. Agents must not choose a substitute
  store.

No second `P2_0_CONTRACT_CONFLICT` is opened. Residual wording tension
below is fail-closed stricter, not a competing contract.

## Residual notes (not conflicts)

| ID | Note | Why not a conflict |
| --- | --- | --- |
| R1 | Auth U-07 last sentence (“if rotation/expiry is absent, G1 stays closed”) vs G1 item 3 allowing confirmed sender-constraint without rotation | Fail direction is closed (stricter). Align wording at P2-B/r2 so RFC 9700 either/or is consistent. Residual-*acceptance* of U-07 without rotation remains forbidden. |
| R2 | Plan §7.3 “no ranking” vs DB §2 ranking | Overlay from a later explicit P2-0 task request; ranking is not selection. |
| R3 | Auth r1 validation checklist still says the diff creates only `AUTH_ARCHITECTURE.md` | True of PR #11; false of this integration branch. Checklist is specialist-scoped prior evidence. |
| R4 | `BROKER_CONTRACT.md` Phase 1B status still says `SIM` is the authorized mode | Historical. Pointer added; original sentence not rewritten. Current authority is `CURRENT_STATE.md`. |
| R5 | Worker/scheduler event ownership has no plan workstream | Already recorded in monitoring §9; assignment is future coordinator/Operator work before `P2-J/r2`. |

## Clear inconsistencies resolved in this commit

1. Dated additive pointer from `BROKER_CONTRACT.md` to P2-A/r1 (plan §9
   deliverable 1; PR #9 verifier N2) without rewriting 2026-09-25 findings.
2. Third `offline_access` evidence conflict plus Client Experience question
   72 (PR #9 verifier N3; auth U-17).
3. P2-0 `config/README.md` / `.env.example` naming comments for future
   `*_REF` sources (plan §9 deliverable 4). Local `SWINGTRADE_DATABASE_URL`
   for authorized `DRY_RUN` is unchanged. `LIVE` remains absent.
4. Monitoring §9 rows for U-17 and U-10 so auth and broker conflicts are
   visible to `MON-AUT-*`.
5. N10 evidence-only `CURRENT_STATE.md` / journal records (no phase grant).

`PHASE_2_PLAN.md` is not edited.

## Gate `H1` status

This pull request is **integration evidence for Gate `H1` review**. It does
**not** pass `H1`.

`H1` remains unpassed because:

1. the human Operator has not reviewed these drafts;
2. an independent verifier has not attested this integration commit;
3. C1 (`P2_0_CONTRACT_CONFLICT` U-10) is open and must be carried, not
   closed, at `H1` review.

**H1 blockers (prevent declaring `H1` passed): items 1–3 above.** None of
the four specialist heads is independently blocked. C1 blocks later G1 /
plan-literal credential provisioning, not the existence of this docs-only
integration PR.

Group 2 (`P2-B/r2` ADR, `P2-D`–`P2-G` design, `P2-C/r2`) must not start from
this document.

## Unsupported assumptions prohibited

The integrated set does not support any assumption that:

- ranking Amazon RDS is provider selection, procurement, or Human Decision
  Gate 2;
- Cursor Dashboard secrets satisfy the proposed CAS store (C1);
- omitting `offline_access` is accepted by TradeStation for the future key
  (U-17);
- default non-expiring refresh tokens are an acceptable `offline_access`
  control;
- any of the twelve broker groups is resolved;
- proposed SIM database objectives are monitoring alert bounds;
- `UNHEALTHY`/`UNCERTAIN` have replaced `MONITORING.md`'s run-health set;
- this branch, SHA, or PR authorizes Phase 2, credentials, SIM, orders, or
  `LIVE`; or
- a repository edit can grant denied authority.

## Operator decisions still required (not requested here)

Carry-forward, not a new grant: Client Experience answers for group 6
including `offline_access`; Operator store decision that does not silently
amend plan G1 (C1); residual-risk records for U-07/U-14 only at a future G1;
P2-C provider ADR at Human Decision Gate 2; worker/scheduler producer
assignment before `P2-J/r2`; and every other Operator item already listed in
the specialist documents.

## Validation

Commands and outcomes for this integration commit are recorded in
`docs/ENGINEERING_JOURNAL.md` for 2026-09-29. They cover ancestry of the
four heads, diff scope versus `1ecbbe6`, whitespace, secret/credential
pattern scan, and confirmation that `src/`, `migrations/`, `tests/`, and
`pyproject.toml` are untouched.
