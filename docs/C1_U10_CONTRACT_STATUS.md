# C1/U-10 contract status

- Status: **RESOLVED**
- Date: 2026-09-30
- Decision name: `C1_U10_RESOLVED`
- Prior proposal name: `C1_U10_PROPOSED_RESOLUTION`
- Review: `C1_U10_CONTRACT_PASS` on
  `a4213f8356a9e32ca4647865ee98e13660e3d656`, tree
  `c07487c88f24f9432de89df7f574130274d50b4b`
- ADR: [ADR-0002](adr/0002-provider-neutral-token-store.md) is Accepted
- Not: `P2_G2_CONTRACT_DECISION_REQUIRED` or
  `P2_G2_IMPLEMENTATION_REMEDIATION_REQUIRED`

The independent review of the proposal commit left C1 **PROPOSED**. The
human Operator accepts ADR-0002 in this commit. C1/U-10 is resolved.

Contract acceptance is not operational credential certification, key
management, Supabase selection, or `LIVE` authorization.

## Identity checked before the proposal commit

Fetched from GitHub on 2026-09-30. Each claimed commit and tree matched.
The review re-fetched the same identities.

| Ref | Commit | Tree |
| --- | --- | --- |
| `main` | `525abe348662495f16958ea6a8e576ebee2ecc50` | `84049874ae0b0e94b3f225c7fe5d58b5f5739f54` |
| PR #15 head | `598fe5218e3f904914cc45e9e8f932a119724e9d` | `1926c07117394e502b361bcc7600b9e34b6e2f62` |
| Implementation parent | `904a362ac716aa8a7d3c9e830444a19108feed67` | `4a6af24ebc82786a5d8c0e6d35f9744be14d9e14` |
| Proposal reviewed | `a4213f8356a9e32ca4647865ee98e13660e3d656` | `c07487c88f24f9432de89df7f574130274d50b4b` |
| `phase1-complete` | `249b8eb341b56d596f07b28723b37ddff96eb86c` | `d5ceeab6817e5986e02de3ff7bee63eb611a4aa8` |
| `phase1-accepted-abc1fb6` | `abc1fb6a9cc3554e7ad13f438685ba3c3c044dab` | `cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808` |
| Phase 1 implementation certification | `eb4b3b550874b4729abf7902cda2df8bf01e70ba` | `858442c0b2dcf0537072e75e95bb0dd2b001bf49` |

No source or test file changes in this acceptance commit.

## Coherence

`C1_U10_CONTRACT_PASS` found the proposed architecture coherent with
Phase 1, `P2-0`, and the implementation at
`904a362ac716aa8a7d3c9e830444a19108feed67`.

- Phase 1 data model still has no credentials. The offline token table is
  not a Phase 1 ledger migration.
- Supabase is not accepted. RDS is not the current target. Persistence
  stays provider-neutral PostgreSQL.
- The implementation is one local PostgreSQL compare-and-swap store for
  synthetic DEV/TEST fixtures. Cursor is not a runtime dependency.
  Bootstrap reference names stay outside the token row. SIM cannot
  connect. LIVE is denied. No Supabase, AWS, RDS, or Cloud SQL client is
  imported.

## Non-blocking residuals

These do not reopen C1. Source and tests are unchanged.

1. Same-attempt tracking is process-local and is not durable across a new
   store instance. The durable reject path is the compare-and-swap
   predicate.
2. Fence monotonicity is not forced. A matching writer can present a new
   fence that is not the expected fence plus one.
3. `read_redacted` is not environment-scoped. It selects by `family_id`
   only. Writes still require the environment match.
4. Stale "not implemented" wording remains in historical proposal text:
   `docs/AUTH_ARCHITECTURE.md` U-10 ("not implemented"),
   `docs/TOKEN_STORE.md` ("Implementation stays blocked"),
   `docs/PHASE_2_RECONCILIATION.md` ("not unblocked"), and
   `docs/PHASE_2_PLAN.md` ("not accepted"). Those sentences are
   pre-acceptance records. They are not current status.

Bootstrap injector, key custody, retention, U-11 lease duration, and the
SIM database host remain later Operator decisions.
