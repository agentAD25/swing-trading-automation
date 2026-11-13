# ADR-0008: Alpaca PAPER Windows-Local Credential Custody and Bounded Account-Read Boundary

- Status: Proposed
- Date: 2026-11-13
- Sole Phase 1 decider: Human Operator
- Scope: Future Windows-local custody of two Alpaca paper credential targets and one paper account read
- Supersedes: None
- Superseded by: None

## Context

Gate C2 and the Item 35 offline mock are canonical. The mock stores synthetic bytes and returns seven false execution flags. Alpaca paper and live keys are different credentials. A paper key is not documented as read-only. ADR-0006 covers the Lane 3 Gmail adapter and does not cover Alpaca. No accepted ADR authorizes a Windows credential read or a call to `paper-api.alpaca.markets`.

This record is a proposal. Publishing it does not accept it and does not authorize a credential read or a provider call.

## Safety impact

`DRY_RUN` stays the only authorized trading mode. This proposal puts no secret in Git, logs, command-line arguments, or chat. It does not change the seven Gate C2 flags. A denied capability stays unauthorized. Acceptance of this ADR, if later recorded by the Operator, still would not by itself authorize implementation, a credential read, or a provider call.

## Options considered

### Option A

Permit a later, separately authorized Windows-local custody path for exactly these two targets:

- `swing-trading/lane2/alpaca/paper/key-id`
- `swing-trading/lane2/alpaca/paper/secret`

Disallow every target under `swing-trading/lane2/alpaca/live/`.

A later Operator-local probe may be authorized only for `GET https://paper-api.alpaca.markets/v2/account`. That future probe would require a Windows-local runtime, paper-only credentials, no host fallback, no redirects, no automatic retries, exactly one authorized account GET, no raw account-body disclosure, and no positions, orders, or streaming requests. It would not submit or modify a paper order and would not use a live host. The seven existing Gate C2 flags stay unchanged. Reported output is a reason code, not the key or the raw account body.

This is the recommended minimum scope. It is not selected while this ADR is Proposed.

### Option B

Widen `connect_allowed` or `network_permitted` on the existing Gate C2 classifier. That would treat a connection as a general Gate C2 permission. This option is not recommended. This proposal does not implement it.

## Decision

Blank while status is Proposed.

## Consequences

Publication authorizes no credential access. Before any Gate D call, all of the following remain separately required:

1. The Operator accepts this ADR.
2. A source implementation grant becomes effective.
3. That grant names only `src/swingtrade/alpaca_paper_account_probe.py` and `tests/unit/test_alpaca_paper_account_probe.py`.
4. The probe implementation is independently verified.
5. The source integration and its mandatory record are canonical.
6. A separate exact-source runtime decision authorizes one paper account GET.

No step is implied by completion of an earlier step. Gate D stays closed until that sequence is complete.

## Validation and rollback

Acceptance evidence is a later Operator decision that changes this status to Accepted and records that decision in current state. Until then, this file is a proposal. Rollback is to leave the status Proposed and make no source change. Failure to keep the seven Gate C2 flags false, or any live-target or non-account route, is outside this proposal.

## Unresolved questions

The Operator decides whether to accept Option A. Native Windows credential-store behavior is not certified by this text. This proposal does not choose a secret-manager product.

## Evidence

- Title: Alpaca authentication. Canonical URL: `https://docs.alpaca.markets/us/docs/authentication`. Access date recorded in the canonical engineering journal on 2026-11-13. Supported claim: live and paper accounts have separate credentials and cannot be interchanged. Limitation: this proposal does not re-fetch the page.
- Title: Alpaca paper trading. Canonical URL: `https://docs.alpaca.markets/us/docs/paper-trading`. Access date recorded in the canonical engineering journal on 2026-11-13. Supported claim: the paper key differs from the live key, and the paper base URL shown there is `https://paper-api.alpaca.markets`. That recorded page does not document a read-only Trading API key. Limitation: this proposal does not re-fetch the page. A paper key is therefore treated as capable of simulated account changes.
- Repository reference: canonical main `90ad6fb2f050d3728551e23fec65b17ca3a6705a`, custody blob `86ba61b5bfecc2ec203e36c099face0e15c4068d`. Supported claim: the seven execution flags return false. Limitation: this proposal does not change that blob.
