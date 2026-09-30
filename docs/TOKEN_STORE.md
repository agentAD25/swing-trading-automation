# TokenStore contract (proposed C1/U-10 resolution)

- Status: **PROPOSED**
- Date: 2026-09-30
- Baseline: `a03c7372fe08b6b42618e72958892154ffebb511`
- Sole acceptance decider: Human Operator
- Scope: Documentation-only contract for runtime mutable token state
- Supersedes: None. Does not accept an ADR and does not close C1 in
  `CURRENT_STATE.md` (that file is intentionally unchanged by this proposal)

## Decision

`C1_U10_PROPOSED_RESOLUTION`. This is not
`P2_G2_CONTRACT_DECISION_REQUIRED`.

The carried conflict was plan Gate G1 naming Cursor Dashboard start-time
secrets versus the proposed workload-writable compare-and-swap store
(`AUTH_ARCHITECTURE.md` U-10). This document proposes the resolution that
the 2026-09-30 slice authorization directed:

1. Production must not depend on Cursor, including Dashboard start-time
   secret injection.
2. Bootstrap static secrets are a different class from runtime mutable
   token state.
3. Runtime mutable token state uses a provider-neutral PostgreSQL-backed
   TokenStore with versioned atomic compare-and-swap, fencing, rotation,
   authorized revocation, stale-writer rejection, and redaction.

No cloud provider, AWS API, or Supabase API is selected. No credential,
schema migration, or network action is created here. The Operator still
must accept or reject this proposal at H2. Until that acceptance, and
until `CURRENT_STATE.md` separately authorizes implementation, no runtime
implementation is unblocked.

## What this does not change

- `DRY_RUN` remains the only authorized execution mode.
- Phase 2, credentials, TradeStation `SIM`, order submission, and `LIVE`
  stay unauthorized.
- Phase 1 `DATA_MODEL.md` still contains no credentials. The TokenStore is
  a future relation, not a change to the accepted ledger schema, and this
  slice adds no migration.
- `SIM_CERTIFICATION.md` still requires an approved secret manager for
  issued credentials. That requirement stays on **bootstrap static
  secrets**. This proposal does not rewrite that contract.
- Human Decision Gate 2 is unchanged. Local PostgreSQL remaining sufficient
  for ledger evidence through `P2-I` is not a decision that the SIM
  TokenStore host is local docker-compose.
- `DB_DEPLOYMENT.md` is unchanged. Database-password handling and provider
  comparison stay where that research left them.

## Two secret classes

| Class | Examples | Where it lives | Production rule |
| --- | --- | --- | --- |
| Bootstrap static secrets | Client secret, if the accepted flow has one; opaque database-credential references; encryption-key references | A start-time holder outside the TokenStore | Must not be Cursor Dashboard injection. Exact injector product is an Operator residual. Not copied into environment files, images, or the repository |
| Runtime mutable token state | Refresh-token generation, version, fence, owner, lifecycle state, revocation metadata | TokenStore only | Writable after process start by the current fence owner. Not a Cursor-injected environment value |

Access-token bearer values stay in bounded process memory. They are not a
TokenStore column. Workers never read refresh material or bootstrap secrets.
DEV and TEST have no broker-token namespace.

Cursor remains an engineering tool. A production workload that cannot
obtain, rotate, or revoke token state without a Cursor agent start is
non-conforming.

## Provider-neutral PostgreSQL contract

The future persistence path is the already-stated
Python → SQLAlchemy 2.x → PostgreSQL path. The contract is ordinary
PostgreSQL conditional-update semantics. It does not call AWS Secrets
Manager, AWS KMS, RDS APIs, Supabase Vault, Supabase Auth, Realtime,
PostgREST, or Edge Functions, and it does not require a vendor SDK.

Host selection is not this contract:

- DEV, TEST, adversarial, and migration checks of the CAS rules may use
  isolated local PostgreSQL and synthetic fixtures that are not OAuth
  material.
- A future SIM deployment must not fall back to that local instance.
- `LIVE` is unconfigured and must not fall back to SIM. No `LIVE` row is
  valid.
- Supabase PostgreSQL remains a candidate for a remotely available SIM
  ledger, not an accepted TokenStore host.
- RDS remains historical future-paid evidence, not the current target.

Whether a future SIM TokenStore shares an instance with the SIM ledger is
an Operator residual. This proposal does not move Human Decision Gate 2
and does not provision a database.

### Logical record

One current row per credential family. Names below are contract fields,
not a migration.

| Field | Rule |
| --- | --- |
| `family_id` | Opaque non-secret primary key |
| `environment` | `DEV`, `TEST`, or `SIM`. A `LIVE` value is rejected. DEV/TEST rows must not hold broker token material |
| `version` | Monotonic integer. First successful commit is version 1. Every successful CAS increases it by exactly 1 |
| `fence` | Monotonic integer, distinct from `version`. Identifies the single refresh owner |
| `owner_id` | Opaque workload identity of the current fence owner |
| `lease_expires_at` | Owner-lease deadline. The duration is U-11 and is not chosen here |
| `state` | `ACTIVE`, `REFRESHING`, `REVOKED`, `REAUTH_REQUIRED`, or `AUTH_UNKNOWN` |
| `scope_set` | Non-secret capability labels |
| `refresh_ciphertext` | Refresh-token ciphertext only, or empty when the committed policy is sender-constraint without rotation. Never an access token, client secret, authorization code, or PKCE verifier |
| `revocation_reason_code` | Non-secret reason code, or empty |
| `updated_at` | Store clock of the last successful CAS |

Encryption keys are not stored in this row. Key custody, KMS product, and
key rotation are Operator residuals. Ciphertext at rest is required.
Plaintext token columns are forbidden.

## Compare-and-swap semantics

A mutation is one PostgreSQL `UPDATE` of the single family row in one
transaction. The statement commits only when it changes exactly one row.
The predicate is evaluated against the latest committed row, which is
PostgreSQL `READ COMMITTED` update behavior. A stronger isolation level is
not required. A read-modify-write that omits the predicate is
non-conforming. Advisory locks and vendor lock APIs are not the fence.

The writer presents the version, fence, state, environment, and owner it
observed. The update matches only when all of these still hold:

- `family_id` is the writer's family;
- `version` equals the expected version;
- `fence` equals the expected fence;
- `state` equals the expected state;
- `environment` equals the writer's environment;
- `owner_id` equals the writer, except for an authorized fence takeover
  defined below.

On match, the same statement sets `version` to the expected version plus
one and applies the new fence, owner, state, ciphertext, and redacted
metadata together. There is no second writer step that can publish an
access-token lease before this commit is known to have succeeded.

Outcomes:

| Result | Meaning | Required behavior |
| --- | --- | --- |
| Exactly one row updated | CAS succeeded | Publish an in-memory access-token lease only after this outcome, and only for a refresh that returned a usable access token |
| Zero rows updated | Lost race, stale writer, or revoked/unknown family | Reject. Do not retry the attempt with a newly read version. Do not send or replay the old refresh token |
| More than one row | Contract break (the primary key forbids this) | Fail closed to `AUTH_UNKNOWN`. No lease |
| Commit result unknown to the writer | Ambiguous local outcome | Do not replay the old refresh token. Re-read redacted metadata. Continue only if version, owner, and state show this writer's commit landed. Otherwise `AUTH_UNKNOWN / BLOCKED` |

A failed CAS is not retried inside the same refresh attempt. Adopting the
winner's new version and writing again would launder a stale writer into
the owner.

## Fencing

Ownership is a CAS. The current owner, or an authorized takeover, sets
`fence` to the observed fence plus one, sets `owner_id`, and sets
`lease_expires_at`, while also incrementing `version`.

Only that fence owner may read refresh material or initiate a
token-endpoint call. Other workers wait for a newer in-memory access-token
lease. They do not refresh.

The TradeStation token endpoint cannot enforce the fence. The owner
re-reads redacted fence and version immediately before send. If either
differs from the leased values, the owner does not send (existing U-08
rule). Lease duration stays U-11. An expired lease is not ownership.

## Rotation

When the broker-confirmed policy is rotation, the CAS that commits the
token response replaces `refresh_ciphertext` in the same statement that
increments `version`. The previous ciphertext is not readable after that
commit. This contract does not keep a ciphertext history. Retention of
non-secret tombstones, backups, and deletion windows is an Operator
residual. A backup that restores a prior refresh token into use is
non-conforming.

When the confirmed policy is sender-constraint without rotation, the CAS
still increments `version` and fence metadata. `refresh_ciphertext` stays
empty. An unconstrained non-expiring refresh token is never stored.

Client-secret rotation is a bootstrap-secret action, not a TokenStore CAS.
TradeStation's statement that client-secret rotation does not revoke
existing non-expiring refresh tokens is unchanged, and those unconstrained
tokens remain rejected for `offline_access` families.

An access-token lease is published only after the rotation CAS commits.
If persistence fails after a token response, the response is discarded and
reauthorization is required. The family does not continue with an
untracked token.

## Authorized revocation

Revocation is a CAS into `REVOKED`. It is not browser logout, not an API-key
disable/enable cycle, and not a worker-local cache drop.

The current fence owner may revoke. A separate human revocation path may
revoke only by an authorized fence takeover: one CAS that moves `owner_id`
and increments `fence` and `version` under an explicit revocation
authorization, then a second CAS that sets `REVOKED` and clears
`refresh_ciphertext`. A writer that is not the current owner, or that
presents a stale fence, updates zero rows and is rejected.

On `REVOKED`:

- refresh material is unreadable;
- in-memory access-token leases for the family are discarded;
- host, scope, environment, and operation class do not change;
- no new token is minted as part of revocation.

`REAUTH_REQUIRED` and `AUTH_UNKNOWN` are also CAS transitions. They make
refresh material unreadable to workers and block broker requests. Recovery
is a new human authorization session, not a retry of the old token.

## Stale-writer rejection

The store rejects a writer when any of the following is true:

- expected version, fence, state, environment, or owner does not match the
  committed row;
- the writer's lease is expired or the pre-send recheck failed;
- the committed state is `REVOKED`, `REAUTH_REQUIRED`, or `AUTH_UNKNOWN`;
- the conditional update matches zero rows;
- the writer attempts a second CAS in the same refresh attempt after a
  zero-row result.

Rejection publishes no lease, does not overwrite the winner, and does not
replay the old refresh token. The rejected attempt fails closed.

## Redaction

Readers that are not the current fence owner receive only redacted
metadata: `family_id`, `environment`, `version`, `fence`, `state`,
`scope_set`, `revocation_reason_code`, and `updated_at`.

Logs, metrics, traces, exceptions, application SQL logs, alerts, reports,
and support bundles may carry those same non-secret fields and a stable
reason code. They must not carry refresh tokens, access tokens, client
secrets, authorization codes, PKCE verifiers, ciphertext, decryption keys,
connection URLs, or account identifiers.

The ciphertext column is readable only by the auth-coordinator role that
holds the current fence, and only into process memory. Broker workers have
no privilege on that column. Database platform logs and backups must not
become a second copy of token material; exact backup tooling remains the
Operator residual already recorded for database research and is not
selected here.

## Fail-closed dependencies

An unavailable, stale, split, or unverifiable TokenStore stops refresh and
lease publication and blocks broker requests. There is no fallback to
Cursor, an environment variable, a file, a cached refresh token, another
cloud secret API, local PostgreSQL for SIM, or `LIVE`.

Unknown mode, family, version, fence, owner, or environment is
`AUTH_UNKNOWN / BLOCKED`.

## Residual Operator decisions

These remain open. None is chosen by this document:

1. Accept or reject this proposal at H2, including the bounded
   `PHASE_2_PLAN.md` wording change that removes Cursor Dashboard secrets
   as the production mechanism.
2. Bootstrap injector product for static secrets, satisfying
   `SIM_CERTIFICATION.md` without a Cursor production dependency.
3. Workload identity platform and the auth-coordinator role mapping.
4. Encryption-key custody and rotation. Not an AWS KMS or Supabase API
   decision by default.
5. Retention, backup, RPO/RTO, and deletion of non-secret tombstones.
6. Lease TTL, clock skew, and refresh margin (existing U-11).
7. SIM database host at the existing Human Decision Gate 2, and whether
   that host is shared with the SIM ledger. Local docker-compose is not
   that host. No provider is selected here.
8. A later `CURRENT_STATE.md` evidence update. This slice does not edit
   that file, so its carried-C1 sentence stays the pre-resolution record
   until the Operator or a later authorized evidence commit changes it.

## Implementation boundary

Code, migrations, tests, provisioning, credentials, and network activity
are out of this proposal. Implementation stays blocked until the Operator
accepts the contract and current state authorizes the implementation
phase. Synthetic local CAS checks, if later authorized, must use fixture
bytes rather than token material.

## Evidence

- Cursor, “Cloud Agents” (secrets are injected when an agent starts;
  already-running agents do not pick up new secrets),
  https://cursor.com/docs/cloud-agent, accessed 2026-09-29, as cited by
  `AUTH_ARCHITECTURE.md` E15. Supports rejecting Dashboard injection as
  the runtime store. Limitation: not a PostgreSQL contract and not a
  selected bootstrap product.
- Repository: `AUTH_ARCHITECTURE.md` U-10 and refresh CAS rules;
  `PHASE_2_PLAN.md` Gate G1 as amended only in the Cursor-mechanism
  sentences; `PHASE_2_RECONCILIATION.md` historical C1 record.
  `CURRENT_STATE.md` and `ENGINEERING_JOURNAL.md` were not edited.
