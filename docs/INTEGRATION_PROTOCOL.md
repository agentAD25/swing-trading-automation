# Integration Protocol

Lane 1 (Integration / Coordinator) is the only lane authorized to propose
integration of certified specialist work into canonical `main`. No automatic
merge is permitted merely because CI is green. No specialist may self-certify
and self-integrate.

## Preconditions

- `docs/CURRENT_STATE.md` still denies credentials, broker/account/network
  activity, TradeStation `SIM`, and `LIVE` unless a later explicit Operator
  authorization expands those gates.
- Safety prohibitions in `docs/AGENT_AUTHORITY.md` and `.cursor/rules/` remain
  non-overridable.
- Candidate work respects lane ownership in `docs/WORKSTREAM_OWNERSHIP.md`.

## Mandatory steps before integration

1. **Fetch current GitHub state.** Refresh `origin/main` and the candidate PR
   refs. Do not trust chat-reported SHAs alone.
2. **Attest canonical main SHA/tree.** Record exact commit and tree hashes.
3. **Attest candidate PR SHA/tree.** Record exact head commit and tree hashes.
4. **Verify workstream ownership.** Candidate changes must belong to the
   claiming lane; shared-file edits need reconciliation notes.
5. **Verify no unauthorized scope expansion.** Reject credential, broker auth,
   paid infra, remote migration, or LIVE-capable paths unless explicitly
   authorized in current state.
6. **Verify accepted contract compatibility.** Proposed ADRs are not Accepted.
   Accepted ADRs on main remain authoritative.
7. **Verify required tests.** Record commands and outcomes; skipped tests stay
   skipped and are never reported as passed.
8. **Verify independent adversarial verification.** Implementer and verifier
   must be distinct.
9. **Verify environmental skips and inherited evidence.** Cloud/local Postgres
   gaps and inherited PASS artifacts must be labeled honestly.
10. **Verify secret and safety scans.** No secrets in Git, chat, logs, or PR
    descriptions; no LIVE path; no unauthorized network auth.
11. **Verify dependency closure.** Open `BLOCKING` dependencies in
    `docs/WORKSTREAM_DEPENDENCIES.md` that apply to the candidate must be
    resolved with evidence or explicitly waived by Operator authority.
12. **Determine ancestry.** Prefer candidates that contain current main.
13. **Prefer exact fast-forward where possible.** Preserve certified trees.
14. **Never silently rewrite a certified tree.** No squash/rebase/force-push of
    certified evidence to manufacture a clean merge.
15. **If main diverged, stop for reconciliation.** Classify the difference;
    never overwrite unexpected changes.
16. **Integrate only after explicit authorization.** Operator authorization is
    required for material merges affecting safety or architecture.
17. **Verify local/origin/GitHub identity.** Local tip, `origin`, and GitHub API
    must agree after push.
18. **Record integration evidence.** Append `docs/ENGINEERING_JOURNAL.md` and
    update `docs/CURRENT_STATE.md` with exact SHAs/trees and mechanism.
19. **Update workstream status.** Set lane state and certification fields in
    `docs/WORKSTREAM_STATUS.md`.
20. **Preserve historical auditability.** Keep superseded PRs (for example PR
    #19) readable; do not reconstruct them as current authority.

## Conflict handling

- Shared-file collisions across lanes → reconcile explicitly or return
  `CROSS_WORKSTREAM_CONTRACT_CONFLICT`.
- ADR number collisions → accepted main ADR wins; conflicting Proposed numbers
  on stale branches remain non-authoritative (PR #19 vs accepted ADR-0003).
- Conversation vs contract → contract wins.

## Specialist reconciliation contract

Shared files on canonical `main` (`docs/CURRENT_STATE.md`, `docs/ENGINEERING_JOURNAL.md`, `docs/WORKSTREAM_STATUS.md`, `docs/WORKSTREAM_DEPENDENCIES.md`, `docs/adr/`, and this protocol) stay coordinator-owned. Branch-local evidence stays specialist-owned until Lane 1 accepts it onto `main`.

Each specialist owner must:

1. Keep the existing branch and PR. Do not recreate the branch, force-push, or rebase away certified history.
2. Merge the then-current `main` with a normal merge commit or an equivalent descendant that preserves both parents. Do not force-push.
3. Resolve only that lane's conflicts. Keep main's governance sentences. Append specialist evidence. Do not drop ADR-0003 Accepted, `DRY_RUN`-only, or `LIVE` unauthorized statements.
4. Do not accept Proposed ADRs and do not mark another lane's `DEP-*` resolved.
5. Obtain a fresh independent verification of the exact reconciled SHA and tree before asking Lane 1 to integrate.
6. Avoid writing the branch while Lane 1 is writing that same branch. Lane 1 does not edit specialist branches during coordination checkpoints.

Current owners:

- Lane 2: reconcile draft PR #22 (`cursor/p2-ts-provider-evidence-99c1`) head `16aa5788a17ac77291530bb836af256a6f79f89f`. It contains `af0d69b` and does not contain attested main `8cef3d7`. `DEP-TS-001` stays open.
- Lane 3: reconcile draft PR #21 (`cursor/p2-g4-gmail-readonly-gate-a-99c1`). `DEP-GMAIL-001` stays open.
- Lane 4: draft PR #24 (`cursor/db-dep-db-002-verify-c385`) tip `d491c3434872fac88b1c5be28281dce94ea11a8b` contains attested main `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829`. If a later coordinator commit advances `main` past that attestation, merge that tip without opening a second PR. `DEP-DB-001` and `DEP-DB-002` stay open. Do not self-merge.

Documentation-only eligibility is not operational authorization.

## Non-goals

- Automatic merging of draft PRs #21 or #22 from this protocol document alone
- TradeStation, Gmail, or Supabase authentication during governance bootstrap
- Paid database provisioning
- Custom runners that hide skips or invent evidence
