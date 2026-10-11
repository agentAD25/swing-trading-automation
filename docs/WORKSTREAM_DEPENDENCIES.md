# Workstream Dependencies

Cross-lane dependency registry. Identifiers are stable. No specialist may mark
another lane's dependency resolved without cited evidence. Conversation claims
alone are insufficient.

Last attestation date: 2026-10-11
Canonical main baseline at the start of this registry edit: `8a17bec501df94238fe7588f84f7f1f51fee8baf` /
`03d48c9ae453bdfc6a1cdf9cdc43a359e76efb1b`
This descendant commit cannot embed its own hash. `DEP-TS-002`, `DEP-TS-003`,
and `DEP-TS-004` are registered here as `OPEN`. None is closed by public
documentation or by the Operator preference
`OPERATOR_PREFERENCE_OPTION_A_REGULAR_WEB_CONFIDENTIAL_CLIENT`.

## Severity vocabulary

- `BLOCKING` — requesting lane cannot honestly advance past its current gate
- `NONBLOCKING` — tracked residual; does not alone freeze the requesting lane tip

## Resolution authority vocabulary

- `OPERATOR` — human Operator Level 0 decision
- `PROVIDER` — external provider confirmation
- `COORDINATOR` — Lane 1 reconciliation / contract freeze prep
- `SPECIALIST` — owning specialist lane with evidence
- `CROSS_WORKSTREAM_CONTRACT_CONFLICT` — human or architectural resolution required; coordinator must not silently pick a conflicting specialist version

## Dependency records

### DEP-TS-001

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-TS-001` |
| Requesting lane | `LANE-2` TradeStation / Broker |
| Providing lane | External TradeStation / Operator-mediated provider channel |
| Required contract or artifact | Native PKCE callback confirmation for future attended probe design |
| Exact blocking question | What exact callback/redirect behavior does TradeStation require for the native PKCE client path that a future attended probe would use? |
| Required evidence | First-party provider confirmation recorded without credentials or live auth; Proposed ADR-0005 updated only with evidenced bounds |
| Severity | `BLOCKING` for operational probe design closure |
| Blocking/nonblocking | Blocking |
| Resolution authority | `PROVIDER` with Operator recording; coordinator reconciles into contracts |
| Current state | `OPEN` — Recommended narrative `SUPERSEDED_BY_OPTION_A_PENDING_ARCHITECTURE_ACCEPTANCE`. The provider did not answer the native PKCE callback question, so that question is not provider-confirmed. The controlled state `SUPERSEDED` is not applied. Supersession is permitted only after ADR-0005 is Accepted as Option A. ADR-0005 remains Proposed with a blank Decision on draft PR #22 head `330c47c40249fdf4e1f2a1bf3fa61e36e05ae4fc` / `864f0c16891af03bce27b40a4d52b843bb444b5f`. If Option A later becomes infeasible for the issued key, this question is blocking again. Not resolved. |

### DEP-TS-002

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-TS-002` |
| Requesting lane | `LANE-2` TradeStation / Broker |
| Providing lane | External TradeStation / Operator-mediated provider channel |
| Required contract or artifact | Issued API-key application type for the preferred Regular Web confidential client |
| Exact blocking question | Is the existing issued API key configured as a Regular Web application? If it is not, can TradeStation convert it, or configure an equivalent compatible Regular Web application, without doing so in the unanswered draft? |
| Required evidence | Written provider answer to question 1 of the unsent 2026-10-09 draft in `docs/TRADESTATION_CLIENT_EXPERIENCE_QUESTIONS.md` on PR #22, recorded without credentials. Published defaults and key-format rules are not sufficient. |
| Severity | `BLOCKING` for accepting Option A and for any future credential or broker connection |
| Blocking/nonblocking | Blocking for ADR-0005 acceptance and credential onboarding; nonblocking for the already-verified offline parser bytes |
| Resolution authority | `PROVIDER` with Operator recording; coordinator reconciles into contracts |
| Current state | `OPEN` — The 2026-10-09 follow-up is `UNSENT`. The issued key is not confirmed as Regular Web. Not resolved. |

### DEP-TS-003

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-TS-003` |
| Requesting lane | `LANE-2` TradeStation / Broker |
| Providing lane | External TradeStation / Operator-mediated provider channel |
| Required contract or artifact | Restricted scopes for the initial attended read-only profile |
| Exact blocking question | Can an authorization for this issued key request and be granted only `openid` and `ReadAccount`, with `Trade`, `MarketData`, `Matrix`, `OptionSpreads`, and `offline_access` excluded? |
| Required evidence | Written provider answer to question 2 of the unsent 2026-10-09 draft, recorded without credentials. The desired profile is not proof of the issued grant. |
| Severity | `BLOCKING` for accepting the attended read-only profile and for any future authorization request |
| Blocking/nonblocking | Blocking for that profile and for credential onboarding; nonblocking for the already-verified offline parser bytes |
| Resolution authority | `PROVIDER` with Operator recording; coordinator reconciles into contracts |
| Current state | `OPEN` — Granted scopes on the issued key are unverified. Do not assume broader scopes have been removed. Not resolved. |

### DEP-TS-004

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-TS-004` |
| Requesting lane | `LANE-2` TradeStation / Broker |
| Providing lane | External TradeStation / Operator-mediated provider channel |
| Required contract or artifact | One HTTPS callback registration for a future Regular Web confidential client |
| Exact blocking question | Can this issued key use one later-supplied HTTPS callback URL as its only registered callback, with unused callback registrations removed, without a hostname being chosen or registered now? |
| Required evidence | Written provider answer to question 3 of the unsent 2026-10-09 draft, recorded without credentials. No production callback hostname is selected. Documented Regular Web compatibility is not this key's registration. |
| Severity | `BLOCKING` for accepting the HTTPS callback design and for any future OAuth redirect |
| Blocking/nonblocking | Blocking for callback registration and credential onboarding; nonblocking for the already-verified offline parser bytes |
| Resolution authority | `PROVIDER` with Operator recording; coordinator reconciles into contracts |
| Current state | `OPEN` — Registered callbacks for this key are unverified. The follow-up draft is `UNSENT` and asks for no registration now. Not resolved. |

### DEP-GMAIL-001

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-GMAIL-001` |
| Requesting lane | `LANE-3` Gmail / Signal Ingestion |
| Providing lane | Operator (credential/OAuth setup authority) |
| Required contract or artifact | Google OAuth setup for read-only corpus acquisition under Proposed ADR-0004 |
| Exact blocking question | Has the Operator completed the authorized Google OAuth setup required for Gate A read-only corpus work? |
| Required evidence | Operator attestation that setup exists out-of-band; no secrets in Git, chat, logs, or PR text |
| Severity | `BLOCKING` for Gate A progression beyond docs-only proposal |
| Blocking/nonblocking | Blocking |
| Resolution authority | `OPERATOR` |
| Current state | `OPEN` — Gate A proposal text is on main at merged PR #21 `2c895291a3b4282f8cf5c7426c705bfdab365c47` / `25ebd09e495bb2db7b7f856963a0af876a378457`. The Operator has not attested Google OAuth setup. No consent, refresh token, or mailbox access is recorded. Not resolved. |

### DEP-DB-001

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-DB-001` |
| Requesting lane | `LANE-4` Database / PostgreSQL Infrastructure |
| Providing lane | Operator (provider selection) with Lane 4 evidence |
| Required contract or artifact | Zero-cost remotely accessible PostgreSQL selection for autonomous-SIM-era needs |
| Exact blocking question | Which zero-incremental-cost remotely accessible PostgreSQL option, if any, is selected under `INITIAL_DATABASE_INCREMENTAL_SERVICE_COST = 0 USD`? |
| Required evidence | Operator-accepted selection ADR or current-state authorization; Supabase remains candidate and **NOT_ACCEPTED** until then |
| Severity | `BLOCKING` for remote autonomous-SIM database use |
| Blocking/nonblocking | Blocking |
| Resolution authority | `OPERATOR` |
| Current state | `OPEN` — remote autonomous-SIM database not selected. Supabase and Neon Free remain **NOT_ACCEPTED**. Lane 4 research records a disposable local PostgreSQL run; that does not select a remote host and does not close this dependency. |

### DEP-DB-002

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-DB-002` |
| Requesting lane | `LANE-4` Database / PostgreSQL Infrastructure |
| Providing lane | `LANE-4` with coordinator certification review |
| Required contract or artifact | Accepted execution evidence for twelve TokenStore PostgreSQL tests |
| Exact blocking question | Where is the accepted, reproducible execution evidence for the twelve TokenStore PostgreSQL tests? |
| Required evidence | Exact command, environment identity, pass count, and SHA/tree; skips must remain skips |
| Severity | `BLOCKING` for TokenStore PostgreSQL certification |
| Blocking/nonblocking | Blocking |
| Resolution authority | `SPECIALIST` evidence + coordinator certification review; Operator for acceptance of certification claims |
| Current state | `OPEN` — independent verifier `bc-6040b738-314c-499a-96c2-7383ac84c385` recorded `LANE4_DEP_DB_002_INDEPENDENT_PASS` (12 passed, 32 deselected; URL unset: 12 skipped) against executable bytes of `d949ce0`. Those `src/` and `tests/` bytes are unchanged at PR #24 tip `d491c3434872fac88b1c5be28281dce94ea11a8b`. The later certification-packet docs are outside that PASS. Not closed. Operator certification acceptance is still required. Fresh verification of tip `d491c34` is `NOT_RUN`. |

### DEP-CORE-001

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-CORE-001` |
| Requesting lane | Shared (`LANE-3` offline parser consumers; future broker sizing) |
| Providing lane | Operator with coordinator ADR drafting |
| Required contract or artifact | Quantity rounding policy |
| Exact blocking question | What quantity rounding policy is accepted for canonical economic instructions? |
| Required evidence | Accepted ADR or explicit Operator decision in `docs/CURRENT_STATE.md` |
| Severity | `BLOCKING` for any path that would invent rounding |
| Blocking/nonblocking | Blocking for that economic path; nonblocking for unrelated docs-only lanes |
| Resolution authority | `OPERATOR` (`CROSS_WORKSTREAM_CONTRACT_CONFLICT` if specialist branches diverge) |
| Current state | `OPEN` — `UNRESOLVED` on main after Group 4A integration |

### DEP-CORE-002

| Field | Value |
| --- | --- |
| Dependency ID | `DEP-CORE-002` |
| Requesting lane | Shared (`LANE-3`, future scheduling/broker session logic) |
| Providing lane | Operator with coordinator ADR drafting |
| Required contract or artifact | Market calendar and timezone policy |
| Exact blocking question | Which market calendar and timezone policy are accepted for session dates and relative calendar language? |
| Required evidence | Accepted ADR or explicit Operator decision in `docs/CURRENT_STATE.md` |
| Severity | `BLOCKING` for calendar-dependent economic acceptance |
| Blocking/nonblocking | Blocking for that path; nonblocking for unrelated docs-only lanes |
| Resolution authority | `OPERATOR` (`CROSS_WORKSTREAM_CONTRACT_CONFLICT` if specialist branches diverge) |
| Current state | `OPEN` — timezone `UNSTATED`; market calendar `UNRESOLVED` on main |

## Conflict return token

When overlapping specialist edits to coordination-sensitive files cannot be
reconciled without choosing between incompatible contracts, Lane 1 must return:

`CROSS_WORKSTREAM_CONTRACT_CONFLICT`

and stop silent selection. See `docs/WORKSTREAM_OWNERSHIP.md` shared-file list.
