# P2-A/r1 TradeStation Broker Research

## Scope and result

This is documentation-only research from canonical `main`
`1ecbbe6d487d97195fde393b05c9499357599bdb`, performed on 2026-09-26.
It does not authorize or perform Phase 2 implementation, credentials, account
access, TradeStation API calls, authenticated probes, vendor contact,
provisioning, migrations, or `SIM`/`LIVE` activity. Local, deterministic,
non-network `DRY_RUN` remains the only authorized execution mode.

All 12 groups in `docs/BROKER_CONTRACT.md` and `docs/PHASE_2_PLAN.md` remain
unresolved. Current public documentation narrows groups 4, 9, 11, and 12, but
does not close any group. Group 6 contains two current first-party conflicts,
recorded below as `BROKER_EVIDENCE_CONFLICT`.

The Phase 1 `BROKER_CONTRACT.md` status paragraph says SIM was the authorized
mode. That sentence is historical and superseded by `docs/CURRENT_STATE.md`:
only local, deterministic, non-network `DRY_RUN` is authorized; TradeStation
`SIM` remains unauthorized. It is prior evidence, not current authority.

The classifications below preserve the taxonomy in `PHASE_2_PLAN.md` §5.
`G2` and `G3` entries are future evidence requirements only; neither gate is
authorized or crossed by this research.

Within each matrix, official-page statements under “Current official evidence”
and explicitly marked “Known” statements are **facts** limited to the cited
text. “Unknown” statements and requested clarification are **open questions**.
Any interpretation is explicitly labeled **inference**. No assumption is
adopted as fact.

## Current first-party source register

All pages are published by TradeStation and were accessed 2026-09-26.

| ID | Exact title and canonical URL | Exact claim used and locator |
| --- | --- | --- |
| TS1 | **Specification \| TradeStation API** — https://api.tradestation.com/docs/specification/ | Endpoint descriptions, request/response schemas, examples, response codes; locators named per row below. |
| TS2 | **HTTP Streaming \| TradeStation API** — https://api.tradestation.com/docs/fundamentals/http-streaming/ | Stream lifecycle, `ERROR`, `EndSnapshot`, `GoAway`, connection ownership, and application-message framing. |
| TS3 | **SIM vs. LIVE \| TradeStation API** — https://api.tradestation.com/docs/fundamentals/sim-vs-live/ | SIM uses fake accounts/fake money and simulated instant fills; interface is described as otherwise identical to LIVE. |
| TS4 | **Overview \| TradeStation API** (Authentication) — https://api.tradestation.com/docs/fundamentals/authentication/auth-overview/ | Default Auth Code flow, non-expiring refresh tokens, stated 40-minute optional rotation, three stated default API scopes, login restrictions, and Client Experience configuration. |
| TS5 | **Refresh Tokens \| TradeStation API** — https://api.tradestation.com/docs/fundamentals/authentication/refresh-tokens/ | 20-minute access tokens, default indefinite refresh tokens, stated 30-minute optional rotation plus 24-hour absolute lifetime, refresh parameters, and all-key revocation effect. |
| TS6 | **Scopes \| TradeStation API** — https://api.tradestation.com/docs/fundamentals/authentication/scopes/ | Scope meanings and conflicting default-scope statements. |
| TS7 | **Overview \| TradeStation API** (Rate Limiting) — https://api.tradestation.com/docs/fundamentals/rate-limiting/rate-limiting-overview/ | Per-user enforcement, per-key quota allocation, standard resource quotas, concurrency limits, headers, rolling replenishment, and Client Experience adjustments. |
| TS8 | **Auth Code Flow \| TradeStation API** — https://api.tradestation.com/docs/fundamentals/authentication/auth-code/ | Required `openid`, `offline_access` for refresh tokens, case-sensitive requested scopes, OAuth endpoints, and 20-minute access-token expiry. |

Public-page review is evidence of what TradeStation currently publishes, not
evidence of a future key's configuration or runtime behavior. The specification
does not expose a publication revision or behavioral guarantee; currentness
here means the canonical pages above were fetched and inspected on the access
date.

## Evidence conflicts

### `BROKER_EVIDENCE_CONFLICT` — refresh rotation

- **Old evidence preserved:** `BROKER_CONTRACT.md` finding 9 recorded on
  2026-09-25 that TS5 says rotating refresh tokens rotate every 30 minutes
  with a 24-hour absolute lifetime, while TS4 says 40 minutes.
- **New evidence:** the same canonical pages still make those incompatible
  statements on 2026-09-26. TS5, “Refresh Token,” says “expire and rotate
  every 30 minutes”; TS4, “Default API Key Configuration,” says “expire and
  rotate every 40 minutes.”
- **Result:** unresolved. Neither page is preferred. The future key's exact
  policy requires written Client Experience confirmation and later authorized
  observation. Confidence: high that the published conflict exists; none as
  to actual key behavior.

### `BROKER_EVIDENCE_CONFLICT` — default API scopes

- **Old evidence preserved:** `BROKER_CONTRACT.md` finding 10 recorded on
  2026-09-25 that TS4 lists `MarketData`, `ReadAccount`, and `Trade`, while TS6
  identifies additional defaults.
- **New evidence:** TS4 still names only those three. TS6's prose names
  `MarketData`, `ReadAccount`, `Trade`, and `OptionSpreads`; its immediately
  following table marks those four plus `Matrix` as `Default`.
- **Result:** unresolved, including an internal TS6 prose/table inconsistency.
  Actual requested and granted scopes must be key-specific and least-privilege.
  Confidence: high that the published conflict exists; none as to actual key
  configuration.

## Twelve-group resolution matrix

### 1. Idempotency — `OrderConfirmID`

| Field | Record |
| --- | --- |
| Requirement | Establish acceptance, retention, collision, and retry semantics, especially after a timeout or lost response. |
| Evidence classification | Facts and open questions; no inference or assumption. |
| Prior evidence | `BROKER_CONTRACT.md` findings 19, 22, 28 and unresolved item 1: confirmation can return an ID; the place-order schema calls it a unique duplicate-prevention identifier, unique per API key/order/user; no lifetime or retry contract was found. |
| Current official evidence | TS1, “Confirm Order” and “Place Order,” accessed 2026-09-26: `OrderConfirmID` is a 1–22 character string and “used to prevent duplicates”; it “Must be unique per API key, per order, per user.” TS1 provides no retention window, collision response, replay result, or timeout rule. |
| Known / unknown | **Known:** field bounds and stated uniqueness dimensions. **Unknown:** whether the confirmation-generated value and client-supplied value have identical semantics; retention; reuse response; scope across sessions; concurrent duplicate handling; safe retry after unknown outcome. |
| Do docs resolve? | **No.** `SIM_EXPERIMENT` primary; fail-closed `IMPLEMENTATION` contract confirmatory. |
| Future G2 read-only evidence | None can establish duplicate-prevention behavior. At most, confirm whether read models expose the confirm ID; absence would not resolve semantics. |
| Future G3 SIM experiment | With separate authorization: reuse the same value sequentially and concurrently, vary payload/user/key dimensions, and create a lost-response case; retain request identity and every response/order observation. |
| Operator/vendor clarification | Client Experience: define generation authority, acceptance, retention, collision error, scope, and replay result. Operator: approve the exact bounded matrix and fail-closed result for ambiguous outcomes. |
| Downstream blockers | `P2-G` final submission-safety implementation. |
| Confidence | High for published field wording; low for all runtime semantics. |

### 2. Ambiguous place/replace/cancel outcomes

| Field | Record |
| --- | --- |
| Requirement | Establish the authoritative recovery procedure after 503/504, disconnect, or client timeout during place, replace, and cancel. |
| Evidence classification | Facts, one labeled inference, and open questions; no assumption. |
| Prior evidence | `BROKER_CONTRACT.md` findings 24–26, 36–37 and unresolved item 2: replace says “Cancel/Replace order sent”; cancel says “Cancel request sent”; documented errors include 503/504; retry safety is unstated. |
| Current official evidence | TS1, “Place Order,” “Replace Order,” and “Cancel Order,” accessed 2026-09-26: replace modifies an active order and its example says “Cancel/Replace order sent”; cancel “Sends a cancellation request to the relevant exchange”; endpoint responses include 503/504. No recovery or safe-retry algorithm is documented. |
| Known / unknown | **Inference (high confidence):** “sent” responses acknowledge a request rather than proving final order state. **Unknown:** commit point, lookup key, retry safety, race outcomes, and authoritative REST/stream recovery sequence. |
| Do docs resolve? | **No.** `SIM_EXPERIMENT` primary; fail-closed `IMPLEMENTATION` recovery contract confirmatory. |
| Future G2 read-only evidence | Read endpoints can validate lookup/reconciliation mechanics only; they cannot establish what happened during an ambiguous write. |
| Future G3 SIM experiment | After authorization, induce client-side disconnect/timeout around each command, then reconcile by order ID and account state without blind retry. A simulated result cannot prove LIVE venue behavior. |
| Operator/vendor clarification | Client Experience: document commit points and the supported lookup/retry procedure for each command. Operator: select the fail-closed disposition when no authoritative state is obtainable. |
| Downstream blockers | `P2-G` final implementation. |
| Confidence | High that documentation does not supply a recovery contract. |

### 3. Order state machine

| Field | Record |
| --- | --- |
| Requirement | Obtain complete status codes, terminal states, allowed transitions, correction/bust semantics, and REST/stream ordering guarantees. |
| Evidence classification | Facts and open questions; no inference or assumption. |
| Prior evidence | `BROKER_CONTRACT.md` findings 17–18 and unresolved item 3: examples include `ACK`, `OPN`, and `FLL`, but no complete enumeration or transition graph. |
| Current official evidence | TS1, “Get Historical Orders,” “Get Orders,” “Stream Orders,” and “Stream Orders by Order Id,” accessed 2026-09-26: examples still show `ACK`/Received, `OPN`/Sent, and `FLL`/Filled and expose quantities/timestamps. No normative status catalog or transition/ordering contract is present. |
| Known / unknown | **Known:** shapes and three example codes. **Unknown:** complete set, terminality, regressions/corrections/busts, partial-fill codes, transition validity, duplicate/out-of-order delivery, and REST-versus-stream authority. |
| Do docs resolve? | **No.** `READ_ONLY_AUTHENTICATED_PROBE` initial; `SIM_EXPERIMENT` confirmatory for reachable transitions. |
| Future G2 read-only evidence | Capture raw current/historical order snapshots and order-stream records; enumerate only observed raw codes and ordering. Observations cannot prove completeness. |
| Future G3 SIM experiment | Exercise bounded place/fill/replace/cancel/reject cases to collect transitions; retain unknown codes raw. |
| Operator/vendor clarification | Client Experience: provide the normative code catalog, terminal flags, transition/correction rules, and ordering authority. Operator: approve unknown-code fail-closed handling. |
| Downstream blockers | `P2-E` DTO mapping completeness. |
| Confidence | High that the public docs are incomplete. |

### 4. Stream recovery

| Field | Record |
| --- | --- |
| Requirement | Define heartbeat thresholds, reconnect/backoff, replay/resume, gap and duplicate detection, and snapshot-to-stream reconciliation. |
| Evidence classification | Facts and open questions; no inference or assumption. |
| Prior evidence | `BROKER_CONTRACT.md` findings 30–31 and unresolved item 4: schemas included heartbeats/status/error/deletion records but no recovery guarantee. |
| Current official evidence | TS2, “HTTP Streaming” and “How to handle HTTP Chunked Encoded Streams,” accessed 2026-09-26: an `ERROR` requires the client to terminate; optional delay before re-request; v3 emits `EndSnapshot` after initial snapshot and `GoAway` before server termination, requiring restart; clients own connection-lifetime handling; JSON objects are application-framed and may cross HTTP chunks. TS1 stream schemas show heartbeat/status variants. |
| Known / unknown | **Known:** initial-snapshot boundary marker, server restart signal, error termination, and framing constraints. **Unknown:** heartbeat cadence/timeout, backoff policy, replay cursor, resume guarantee, sequence number, gap/duplicate detection, ordering across connections, and loss-free snapshot handoff. |
| Do docs resolve? | **Partly, not enough to close.** Primary remains `READ_ONLY_AUTHENTICATED_PROBE`. |
| Future G2 read-only evidence | Capture `EndSnapshot`, heartbeats, `GoAway`/disconnect behavior, reconnect snapshots, duplicates, and timing under bounded read-only observation. No observation proves a universal guarantee. |
| Future G3 SIM experiment | None assigned by the canonical plan; stream transport is read-only evidence. |
| Operator/vendor clarification | Client Experience: specify heartbeat SLA, reconnect/backoff, replay/resume support, ordering, gap detection, and authoritative snapshot/stream handoff. Operator: approve fail-closed staleness thresholds only after evidence. |
| Downstream blockers | `P2-E`; `P2-F` stream-sourced reconciliation. |
| Confidence | High for TS2's explicit markers; low for undocumented recovery behavior. |

### 5. SIM fidelity

| Field | Record |
| --- | --- |
| Requirement | Characterize partial fills, rejects, cancels, replace races, market hours, buying power, corporate actions, and data entitlements without treating SIM as LIVE evidence. |
| Evidence classification | Facts, one labeled inference, and open questions; no assumption. |
| Prior evidence | `BROKER_CONTRACT.md` findings 2–3 and unresolved item 5: fake accounts/fake money and instant simulated fills; realistic venue behavior not established. |
| Current official evidence | TS3, accessed 2026-09-26: SIM is described as identical to LIVE except fake accounts/fake money and instant simulated fills; it is for experimentation without real-account effects. No detailed simulator model is published. |
| Known / unknown | **Known:** documented instant-fill and fake-account model. **Unknown:** all listed edge behavior and whether data/account entitlements mirror any future configuration. |
| Do docs resolve? | **No.** Primary `SIM_EXPERIMENT`. The broad “identical” sentence does not override the explicit instant-fill exception or prove fidelity. |
| Future G2 read-only evidence | Inventory only the authorized SIM accounts, data flags, balances, positions, and existing orders; this does not establish order behavior. |
| Future G3 SIM experiment | Bounded lifecycle matrix for fills/rejects/cancels/replaces/hours/buying power. Corporate-action and entitlement cases require controlled availability and may remain untestable. |
| Operator/vendor clarification | Client Experience: enumerate simulator differences and deterministic controls, if any. Operator: define which fidelity gaps block certification; never infer LIVE parity. |
| Downstream blockers | `P2-I` certification evidence through `P2-H`. |
| Confidence | High for instant fills; low for every unstated fidelity dimension. |

### 6. Authentication conflicts

| Field | Record |
| --- | --- |
| Requirement | Establish exact refresh-token policy and least-privilege granted scopes for the future key. |
| Evidence classification | Facts and open questions, including two factual source conflicts; no inference or assumption. |
| Prior evidence | `BROKER_CONTRACT.md` findings 5–11 and unresolved item 6 recorded 30-vs-40-minute rotation and default-scope conflicts. |
| Current official evidence | TS4–TS6 and TS8, accessed 2026-09-26. The two `BROKER_EVIDENCE_CONFLICT` records above remain current. TS5 confirms 20-minute access tokens, default indefinite refresh tokens, and all-key revocation. |
| Known / unknown | **Known:** default Auth Code flow; `openid` required; `offline_access` required for refresh; key configuration is adjustable by Client Experience. **Unknown/conflicted:** 30 vs 40 minutes; exact defaults; actual requested/granted scopes; key type; permitted logins; SIM entitlement; callback URLs; revocation/rotation configuration. |
| Do docs resolve? | **No.** `OPERATOR_DECISION`/vendor confirmation before `G1`; `READ_ONLY_AUTHENTICATED_PROBE` confirmation at `G2`. |
| Future G2 read-only evidence | Record token response expiry/scope fields and actual read-only authorization failures/successes; observe only an approved refresh lifecycle. Do not infer policy from one sample. |
| Future G3 SIM experiment | None; authentication policy must not require an order experiment. |
| Operator/vendor clarification | Client Experience: answer the exact key-configuration questions in `TRADESTATION_CLIENT_EXPERIENCE_QUESTIONS.md`. Operator: choose flow, requested scopes, login set, callback set, and refresh policy before `G1`. |
| Downstream blockers | `P2-B` ADR finalization and `G1`. |
| Confidence | High for the documented conflicts; none for a future key. |

### 7. Account and entitlement contract

| Field | Record |
| --- | --- |
| Requirement | Establish approved account types, symbols/assets, SIM access, market-data latency/sessions, routes, short-locate behavior, and key-specific quotas. |
| Evidence classification | Facts and open questions; no inference or assumption. |
| Prior evidence | `BROKER_CONTRACT.md` findings 11–13, 21, 29, 32–35 and unresolved item 7: schemas and defaults exist, but account/key entitlements are specific. |
| Current official evidence | TS4 says non-partner access is restricted to accounts under approved logins and names a 15-login default limit. TS1 documents account types accepted per endpoint, `Get Routes`, session-template values, and quote `MarketFlags` examples including `IsDelayed`/`IsHardToBorrow`. TS7 says actual quotas are allocated per key/user and may be adjusted. All accessed 2026-09-26. |
| Known / unknown | **Known:** public endpoint capabilities and fields. **Unknown:** future key/login/account set; SIM entitlement; enabled asset classes/symbols/routes; real-time/delayed feeds by market/session; short-sale/locate workflow; actual quotas. |
| Do docs resolve? | **No.** `OPERATOR_DECISION`/vendor confirmation, then `READ_ONLY_AUTHENTICATED_PROBE`. |
| Future G2 read-only evidence | `GET` accounts/balances/positions/routes/symbol details/quotes and inspect entitlement/rate headers and delayed/hard-to-borrow flags for the approved inventory. |
| Future G3 SIM experiment | None assigned by the canonical plan; any order-side entitlement test would require separately scoped `G3` approval. |
| Operator/vendor clarification | Client Experience: confirm exact SIM/account/data/route/short-locate/quota configuration. Operator: state intended accounts, assets, sessions, and data-latency acceptance. |
| Downstream blockers | `G1`. `P2-C` helps resolve environment scoping; it is not the canonical downstream blocker. |
| Confidence | High for schemas; none for future entitlements. |

### 8. Confirmation semantics

| Field | Record |
| --- | --- |
| Requirement | Determine whether confirmation is mandatory, ID validity, and whether confirmation guarantees acceptance or binds price/cost. |
| Evidence classification | Facts and open questions; no inference or assumption. |
| Prior evidence | `BROKER_CONTRACT.md` findings 19 and 28 and unresolved item 8: confirmation estimates without placing; no mandatory-step or guarantee language. |
| Current official evidence | TS1, “Confirm Order” and “Place Order,” accessed 2026-09-26: confirm returns estimated cost/commission “without the order actually being placed”; place creates an order and does not mark `OrderConfirmID` required in the schema. No lifetime, acceptance guarantee, or price-binding statement appears. |
| Known / unknown | **Known:** non-submitting estimate; place schema does not mark the field required. **Unknown:** policy exceptions, ID lifetime, stale-confirm handling, binding effect, and relationship to duplicate prevention. |
| Do docs resolve? | **No.** `DOCS_ONLY` recheck completed without finding the missing contract; primary remains `SIM_EXPERIMENT`. |
| Future G2 read-only evidence | None sufficient. |
| Future G3 SIM experiment | Compare place with/without confirmation, delayed use, changed payload, repeated ID, and changed market price under bounded authorization. |
| Operator/vendor clarification | Client Experience: state mandatory cases, lifetime, payload binding, duplicate semantics, and whether any estimate/acceptance is guaranteed. Operator: decide whether internal policy requires confirmation even if the API does not. |
| Downstream blockers | `P2-G`. |
| Confidence | High for non-submitting behavior; low for unstated semantics. |

### 9. Batch/group atomicity

| Field | Record |
| --- | --- |
| Requirement | Define transaction boundaries for multi-leg, OSO, OCO/bracket, and group submissions, including mixed success/error responses. |
| Evidence classification | Facts and open questions; no inference or assumption. |
| Prior evidence | `BROKER_CONTRACT.md` findings 23 and 27 and unresolved item 9: mixed `Orders`/`Errors`; siblings handled individually; bracket cannot be updated atomically. |
| Current official evidence | TS1, “Confirm Group Order,” “Place Group Order,” and “Place Order,” accessed 2026-09-26: OCO partial/full fill cancels siblings; sibling orders are treated individually; sibling quantities are not validated equal; bracket updates are not one transaction; examples show `Orders` and `Errors` together. |
| Known / unknown | **Known:** sibling orders are treated individually, bracket updates are not one transaction, and mixed response shapes exist. **Unknown:** submission atomicity, commit/rollback boundary by group type, OSO parent/child failure behavior, ordering, and recovery from mixed/ambiguous outcomes. |
| Do docs resolve? | **No.** Primary `SIM_EXPERIMENT`; docs materially narrow but do not complete the contract. |
| Future G2 read-only evidence | Existing read models may reveal resulting relationships but cannot establish submission atomicity. |
| Future G3 SIM experiment | Controlled per-leg validation failures and ambiguous disconnects for NORMAL/OCO/BRK/OSO; reconcile every returned and observed order independently. |
| Operator/vendor clarification | Client Experience: define transaction and rollback boundaries and mixed-response recovery for each group type. Operator: approve whether unresolved partial groups always require review. |
| Downstream blockers | `P2-G`; `P2-I`. |
| Confidence | High for documented individual-sibling behavior; low for complete atomicity. |

### 10. Rate-limit identity

| Field | Record |
| --- | --- |
| Requirement | Establish how quotas aggregate across processes, tokens, logins/users, accounts, keys, and multiple applications. |
| Evidence classification | Facts and open questions; no inference or assumption. |
| Prior evidence | `BROKER_CONTRACT.md` findings 33–35, 37 and unresolved item 10: per-user application of per-key quotas, rolling/concurrent limits, key-specific variation. |
| Current official evidence | TS7, accessed 2026-09-26: “Each API Key is allocated quota settings”; settings are “applied on a per-user basis”; quotas are enforced per user across resource categories; standard quotas and `X-RateLimit-*`/`X-Concurrency-*` headers are documented. Cross-dimensional aggregation is not. |
| Known / unknown | **Known:** key allocation, per-user enforcement wording, resource categories, rolling/concurrent models, and headers. **Unknown:** precise composite identity and sharing across tokens/processes/accounts/keys/apps/login aliases. |
| Do docs resolve? | **No.** `OPERATOR_DECISION` for deployment topology; `READ_ONLY_AUTHENTICATED_PROBE` for actual headers. |
| Future G2 read-only evidence | Under a separately approved plan, compare headers across controlled read-only requests from intended processes/tokens; do not intentionally exhaust quota. |
| Future G3 SIM experiment | None. |
| Operator/vendor clarification | Client Experience: provide the exact quota-key tuple and actual allocations for the intended key. Operator: declare process/application/key topology and capacity policy. |
| Downstream blockers | `P2-D` retry/backoff design. `P2-B`/`P2-C` help resolve topology; they are not canonical downstream blockers. |
| Confidence | High for published wording; low for aggregation semantics. |

### 11. Decimal and time semantics

| Field | Record |
| --- | --- |
| Requirement | Define precision, rounding, tick/quantity validation, timestamp precision/timezone/session boundaries, and clock-skew expectations for intended assets. |
| Evidence classification | Facts and open questions; no inference or assumption. |
| Prior evidence | `BROKER_CONTRACT.md` unresolved item 11; `PHASE_2_PLAN.md` classified further Symbol/Quote cross-reference as `DOCS_ONLY` with G2 confirmation. |
| Current official evidence | TS1, “Get Symbol Details,” accessed 2026-09-26: `PriceFormat` and `QuantityFormat` provide decimal/fraction/subfraction display, increments, decimals, point value, and minimum quantity; examples include `0.01`, `0.25`, and `0.0078125`. “Get Bars” documents US-equity session templates. Examples use ISO-8601 `Z` timestamps and sometimes epoch milliseconds. No order-rounding or clock contract is stated. |
| Known / unknown | **Known:** per-symbol formatting metadata and documented session-template values. **Unknown:** whether increments are validation rules or display only; rounding/rejection policy; decimal bounds; timestamp precision/authority; DST/holiday handling; clock skew; asset-specific order constraints. |
| Do docs resolve? | **Partly, not enough to close.** `DOCS_ONLY` portion narrowed; `READ_ONLY_AUTHENTICATED_PROBE` confirmatory. |
| Future G2 read-only evidence | Capture Symbol Details plus quote/bar/order timestamps for the approved symbol set and preserve strings exactly; compare documented versus observed metadata without coercion. |
| Future G3 SIM experiment | None assigned by the canonical plan; off-increment order validation would need a separately approved experiment if vendor documentation remains insufficient. |
| Operator/vendor clarification | Client Experience: distinguish display metadata from order validation and define timestamp/session/clock rules. Operator: identify intended asset classes, symbols, and sessions. |
| Downstream blockers | `P2-E` canonical-decimal/time mapping. |
| Confidence | High for metadata shapes; low for validation and time semantics. |

### 12. Retention

| Field | Record |
| --- | --- |
| Requirement | Establish availability beyond the API's 90-day historical-order window and the operational retention/export contract. |
| Evidence classification | Facts and open questions; no inference or assumption. |
| Prior evidence | `BROKER_CONTRACT.md` findings 14–15 and unresolved item 12: 90-day historical limit, 600-item unpaginated maximum, one-hour pagination token. |
| Current official evidence | TS1, “Get Historical Orders,” accessed 2026-09-26: required `since` is limited to 90 days before current date; `pageSize` is 1–600; omitted pagination returns at most 600; `nextToken` lives one hour. No public archive/export endpoint was located in the current specification. Absence from the specification does not prove no other retrieval channel exists. |
| Known / unknown | **Known:** API query and pagination limits. **Unknown:** broker-side retention, statements/export access, correction history, legal retention, and the Operator's required local retention. |
| Do docs resolve? | **Partly, not enough to close.** `DOCS_ONLY` search found no public archive contract; organizational retention is `OPERATOR_DECISION`. |
| Future G2 read-only evidence | None assigned by the canonical plan; a bounded historical query can only corroborate the documented window, not prove older data unavailable. |
| Future G3 SIM experiment | None. |
| Operator/vendor clarification | Client Experience: identify supported retrieval/export channels beyond 90 days and correction availability. Operator: set retention, evidence, deletion, and recovery policy. |
| Downstream blockers | `P2-J` reporting retention design. |
| Confidence | High for API limits; low for availability outside the public API. |

## Round-one outcome

- **Fully resolved by public docs:** 0/12.
- **Narrowed but unresolved:** groups 4, 9, 11, and 12.
- **Current published conflicts:** group 6 (refresh rotation and default
  scopes).
- **Needs future G2 evidence:** groups 3, 4, 6, 7, 10, and 11. Read-only
  evidence may corroborate observations but cannot turn an undocumented
  behavior into a guarantee.
- **Needs future G3 evidence:** groups 1, 2, 3, 5, 8, and 9.
- **Needs Operator and/or Client Experience clarification:** every group;
  the exact, non-leading questions are in
  `docs/TRADESTATION_CLIENT_EXPERIENCE_QUESTIONS.md`.

No claim here establishes profitability, production readiness, SIM
certification, LIVE fidelity, or authorization to cross any gate.
