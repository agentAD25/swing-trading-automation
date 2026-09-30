# C1/U-10 contract status

- Status: **PROPOSED**
- Date: 2026-09-30
- Decision name: `C1_U10_PROPOSED_RESOLUTION`
- ADR: [ADR-0002](adr/0002-provider-neutral-token-store.md) remains Proposed
- Not: `ACCEPTED`, `P2_G2_CONTRACT_DECISION_REQUIRED`, or
  `P2_G2_IMPLEMENTATION_REMEDIATION_REQUIRED`

## Identity checked before this commit

Fetched from GitHub on 2026-09-30. Each claimed commit and tree matched.

| Ref | Commit | Tree |
| --- | --- | --- |
| `main` | `525abe348662495f16958ea6a8e576ebee2ecc50` | `84049874ae0b0e94b3f225c7fe5d58b5f5739f54` |
| PR #15 head | `598fe5218e3f904914cc45e9e8f932a119724e9d` | `1926c07117394e502b361bcc7600b9e34b6e2f62` |
| PR #16 head before this commit | `904a362ac716aa8a7d3c9e830444a19108feed67` | `4a6af24ebc82786a5d8c0e6d35f9744be14d9e14` |
| `phase1-complete` | `249b8eb341b56d596f07b28723b37ddff96eb86c` | `d5ceeab6817e5986e02de3ff7bee63eb611a4aa8` |
| `phase1-accepted-abc1fb6` | `abc1fb6a9cc3554e7ad13f438685ba3c3c044dab` | `cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808` |
| Phase 1 implementation certification | `eb4b3b550874b4729abf7902cda2df8bf01e70ba` | `858442c0b2dcf0537072e75e95bb0dd2b001bf49` |

Those commits are ancestors of `904a362ac716aa8a7d3c9e830444a19108feed67`.
This parent was that exact PR #16 head. No source, test, or
`docs/CURRENT_STATE.md` change is part of this evidence.

## Coherence

The architecture in ADR-0002 is coherent with Phase 1, `P2-0`, and the
implementation inspected at `904a362ac716aa8a7d3c9e830444a19108feed67`.

- Phase 1 data model still has no credentials. The offline token table is
  not a Phase 1 ledger migration.
- `P2-0` still records `C1_U10_PROPOSED_RESOLUTION` as proposed. Supabase
  is not accepted. RDS is not the current target. Persistence stays
  provider-neutral PostgreSQL.
- The implementation is one local PostgreSQL compare-and-swap store for
  synthetic DEV/TEST fixtures. Cursor is not a runtime dependency.
  Bootstrap reference names stay outside the token row. SIM cannot
  connect. LIVE is denied. No Supabase, AWS, RDS, or Cloud SQL client is
  imported.

No implementation contradiction was found. Remediation is not required.

## What remains PROPOSED

`docs/TOKEN_STORE.md` is not changed from **PROPOSED** to Accepted.
ADR-0002 is not Accepted. H2 acceptance is still an Operator decision.
`docs/CURRENT_STATE.md` and `docs/ENGINEERING_JOURNAL.md` are not edited.

This evidence does not authorize credentials, OAuth, TradeStation `SIM`,
`LIVE`, or operational key management.
