# SIM Certification Contract

## Status

This is a proposed evidence gate, not a certification result. Phase 1B contains
no implementation to certify.

## Entry criteria

- named human owner, risk owner, security owner, and release decider;
- accepted architecture, safety, data, event, and test ADRs;
- approved strategy/data/risk research contracts;
- deterministic implementation and pinned build artifact;
- no live adapter, credentials, account dependency, or live network route;
- resolved licensing and legal/compliance obligations applicable to SIM.

## Required evidence packs

1. **Build:** source commit, dependency lock digest, toolchain, artifact digest,
   software inventory, and vulnerability/license results.
2. **Determinism:** repeated clean runs and replay produce byte-identical
   canonical events and reports from the WDC fixture.
3. **Correctness:** lifecycle, decimal/rounding, data-quality, state-machine,
   event evolution, and report calculation tests pass.
4. **Safety:** all mode-denial tests pass; inspection proves no live route or
   live-capable dependency.
5. **Resilience:** crash, duplicate, timeout, restart, lag, stale data, and
   dependency fault scenarios preserve invariants.
6. **Reconciliation:** all required mismatch scenarios are detected and block
   dependent activity; clean runs have no unresolved critical/high cases.
7. **Operations:** dashboards, alerts, runbooks, backup/restore, and incident
   exercises are demonstrated with named owners.
8. **Research:** input provenance, bias controls, cost assumptions, and
   limitations are documented; no efficacy claim is inferred from the fixture.

## Exit criteria

Certification requires zero safety blockers, zero unresolved critical/high
reconciliation cases, complete required evidence, reproducibility in an
independent clean environment, and signed approval by the named owners. Any
waiver is explicit, scoped, expiring, and cannot waive `LIVE` denial or ledger
integrity.

Quantitative reliability and performance thresholds are unresolved operator
choices; they must be set before certification based on approved requirements,
not selected after observing favorable results.

## Validity and revocation

Certification binds exact source, configuration schema, dependencies, artifact
digest, data/calendar versions, and evidence. A material change triggers a
declared subset or full recertification. Safety regression, unexplained
execution effect, integrity failure, or unreconciled position immediately
revokes certification and blocks dispatch.

## Explicit non-consequence

SIM certification authorizes neither Phase 2 nor `LIVE`. It supplies evidence
to a separate human decision process only.
