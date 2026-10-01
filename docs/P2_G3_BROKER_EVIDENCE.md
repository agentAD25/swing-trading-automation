# P2 Group 3 broker evidence (documentation only)

## Result

`P2_G3_CONTRACT_DECISION_REQUIRED` is not returned.

Public pages retrieved on 2026-09-30 still leave all 12 behavior groups
unresolved. The conflicts and missing runtime facts below are recorded as
`UNKNOWN`. They do not force a choice inside the offline authorization,
callback, token-form, or read-only request-template contracts, because those
contracts take the unresolved values as explicit inputs and fail closed when
an input is absent. Selecting a scope set, a refresh interval, a revocation
body, a status catalog, or a path-to-scope allowlist remains unresolved and
is outside the unblocked areas.

No TradeStation account, credential, OAuth execution, token request, API
call, Client Experience message, Supabase connection, or order was made.
`DRY_RUN` remains the only authorized execution mode. TradeStation `SIM` and
`LIVE` remain unauthorized. This document does not change ADR-0002, the
TokenStore compare-and-swap contract, or the Group 2 host policy.

## Identity

| Field | Value |
| --- | --- |
| Repository | `agentAD25/swing-trading-automation` |
| Expected and observed `main` | `7c9b994dc41491b6f54f62199833597aada7fbf8` |
| Expected and observed tree | `3b568afaf7b9d4b78a60dd0c61a97325206ee4fb` |
| Prior accepted broker research | `docs/P2_BROKER_RESEARCH.md` (P2-A/r1), left unchanged |
| Retrieval date | 2026-09-30 |
| Spec asset Last-Modified | Thu, 03 Sep 2026 21:08:41 GMT |
| Fundamentals HTML Last-Modified | Thu, 03 Sep 2026 21:08:44 GMT |

`git fetch origin main` on 2026-09-30 returned that commit and tree for
`HEAD`, `main`, and `origin/main`.

## Method

Fundamentals pages were read as published HTML. The specification page is a
client-rendered Redoc shell. Its OpenAPI 3.0.3 document is the `JSON.parse`
argument in the first-party asset
`https://api.tradestation.com/docs/assets/js/42059736.54db3d8f.js`, linked
from `https://api.tradestation.com/docs/specification/`. That asset is
published documentation. It is not the v3 API. The parsed document has 35
paths and one server, `https://api.tradestation.com`.

Statements in the register are limited to text present on the retrieval
date. A missing behavior is `UNKNOWN`. Two published statements that cannot
both be the key contract are recorded as a conflict, and neither is
selected. Comparison of two published enums is a comparison of the text,
not a claim about which codes a stream emits.

Example account identifiers, order identifiers, and token fragments that
appear in the public examples are omitted here.

## Source register

| ID | Title and URL | Retrieved | Last-Modified header |
| --- | --- | --- | --- |
| TS1 | Specification — https://api.tradestation.com/docs/specification/ (OpenAPI asset https://api.tradestation.com/docs/assets/js/42059736.54db3d8f.js) | 2026-09-30 | 2026-09-03 21:08:41 GMT |
| TS2 | HTTP Streaming — https://api.tradestation.com/docs/fundamentals/http-streaming/ | 2026-09-30 | 2026-09-03 21:08:44 GMT |
| TS3 | SIM vs. LIVE — https://api.tradestation.com/docs/fundamentals/sim-vs-live/ | 2026-09-30 | 2026-09-03 21:08:44 GMT |
| TS4 | Authentication overview — https://api.tradestation.com/docs/fundamentals/authentication/auth-overview/ | 2026-09-30 | 2026-09-03 21:08:44 GMT |
| TS5 | Refresh Tokens — https://api.tradestation.com/docs/fundamentals/authentication/refresh-tokens/ | 2026-09-30 | 2026-09-03 21:08:44 GMT |
| TS6 | Scopes — https://api.tradestation.com/docs/fundamentals/authentication/scopes/ | 2026-09-30 | 2026-09-03 21:08:44 GMT |
| TS7 | Rate limiting overview — https://api.tradestation.com/docs/fundamentals/rate-limiting/rate-limiting-overview/ | 2026-09-30 | 2026-09-03 21:08:44 GMT |
| TS8 | Auth Code Flow — https://api.tradestation.com/docs/fundamentals/authentication/auth-code/ | 2026-09-30 | 2026-09-03 21:08:44 GMT |
| TS9 | Auth Code Flow with PKCE — https://api.tradestation.com/docs/fundamentals/authentication/auth-pkce/ | 2026-09-30 | 2026-09-03 21:08:44 GMT |
| TS10 | Logout — https://api.tradestation.com/docs/fundamentals/authentication/logout/ | 2026-09-30 | 2026-09-03 21:08:44 GMT |

## Findings

Confidence is about the published sentence. High confidence that a page
contains a sentence is not confidence about a future key or a runtime.

### OAuth

| ID | URL | Retrieved | Statement | Confidence | Group |
| --- | --- | --- | --- | --- | --- |
| O1 | TS4 | 2026-09-30 | The procedures are for Auth0 API keys. Default keys are Regular Web App and use the standard Auth Code flow. PKCE for a SPA or native app is a Client Experience change. | High for the default statement. None for a future key. | 6 |
| O2 | TS8, TS9 | 2026-09-30 | Authorization URL is `https://signin.tradestation.com/authorize`. Required query parameters are `response_type=code`, `client_id`, `audience`, `redirect_uri`, and `scope`. `state` is recommended. `prompt` is optional. `prompt=login` is described as forcing a login screen; without it, an existing browser session may skip login. | High for the parameter table. None for whether a future key honors `prompt=login`. | 6 |
| O3 | TS8, TS9 | 2026-09-30 | `audience` is required and the documented value is `https://api.tradestation.com`. | High for the documented value. None for whether a token for that audience is confined to SIM. | 6 |
| O4 | TS8 | 2026-09-30 | Token exchange is `POST https://signin.tradestation.com/oauth/token` with `content-type: application/x-www-form-urlencoded` and `grant_type=authorization_code`. Standard flow required fields are `client_id`, `client_secret`, `code`, and `redirect_uri`. | High for that form. | 6 |
| O5 | TS9 | 2026-09-30 | PKCE adds required `code_challenge` and `code_challenge_method=S256` on the authorization request. The verifier is a random string of 43–128 characters. Token exchange sends `code_verifier` and the page says the server uses that process instead of a `client_secret`. The PKCE token example contains a trailing comma after `expires_in` and is not strict JSON. | High for the parameter table. The trailing comma is a fact about the example text. | 6 |
| O6 | TS8, TS9 | 2026-09-30 | The success redirect includes `code` and `state`. The page says the authorization-code length is variable. Declined consent redirects with `error=access_denied` and an `error_description`. | High for those query shapes. | 6 |
| O7 | TS8, TS9, TS5 | 2026-09-30 | Example token responses include `access_token`, `refresh_token`, `id_token`, `token_type` `Bearer`, `scope`, and `expires_in` 1200. The pages say access tokens expire 20 minutes after issue. | High for the example fields and the 20-minute sentence. None for every production response field. | 6 |
| O8 | TS4 | 2026-09-30 | Default callback and logout URL lists are localhost HTTP ports, including `http://localhost:3000` and `http://localhost:31022`. Changes go through Client Experience. | High for the published default list. None for this system's callbacks. | 6 |
| O9 | TS10 | 2026-09-30 | Logout URL is `https://signin.tradestation.com/v2/logout`. The page says logout does not invalidate the existing access token or refresh token. Default redirect without `returnTo` and `client_id` is `https://www.tradestation.com/`. | High for that sentence. | 6 |
| O10 | TS1 | 2026-09-30 | API requests use a bearer token in the HTTP header. The only documented server URL is `https://api.tradestation.com`. Paths begin with `/v2/` or `/v3/`. | High for the spec text. | 6, 7 |

### Scopes

| ID | URL | Retrieved | Statement | Confidence | Group |
| --- | --- | --- | --- | --- | --- |
| S1 | TS4 | 2026-09-30 | Default API scopes named on this page are `MarketData`, `ReadAccount`, and `Trade`. | High that this page says those three. | 6 |
| S2 | TS6 | 2026-09-30 | Prose says keys are configured by default with `MarketData`, `ReadAccount`, `Trade`, and `OptionSpreads`. | High that this prose says those four. | 6 |
| S3 | TS6 | 2026-09-30 | The API-scope table marks `MarketData`, `ReadAccount`, `Trade`, `OptionSpreads`, and `Matrix` as `Default`. | High that the table marks all five. | 6 |
| S4 | TS6 | 2026-09-30 | Scope sentences: `MarketData` requests lookup or stream of market data; `ReadAccount` requests view of brokerage accounts of the current user; `Trade` requests execute orders; `OptionSpreads` requests execute options-related endpoints; `Matrix` requests execute market-depth endpoints. The page does not name a path for each scope. | High for those sentences. None for path-to-scope assignment. | 6, 7 |
| S5 | TS6 | 2026-09-30 | Other-scopes table: `openid` is `required` and returns the `sub` claim; `offline_access` is `required` and "Allows for use of Refresh Tokens"; `profile` and `email` are `optional`. | High that the table labels `offline_access` required. | 6 |
| S6 | TS8, TS9, TS5 | 2026-09-30 | Auth-code and PKCE pages say `openid` is always required and `offline_access` is required for refresh tokens. The refresh page says `offline_access` must be included in the authorization scope "to allow for Refresh Tokens." | High that those pages qualify `offline_access` as the refresh-token scope. | 6 |
| S7 | TS8 | 2026-09-30 | Requested scopes are a case-sensitive space-separated list. | High. | 6 |

`S1`, `S2`, and `S3` conflict. `S5` and `S6` conflict on whether
`offline_access` is required on every authorization request. Neither
conflict is resolved here.

### Refresh

| ID | URL | Retrieved | Statement | Confidence | Group |
| --- | --- | --- | --- | --- | --- |
| R1 | TS5 | 2026-09-30 | Default refresh tokens are valid indefinitely. Optional configuration, requested through Client Experience, makes them "expire and rotate every 30 minutes", with a 24-hour absolute lifetime. | High that this page says 30 minutes. | 6 |
| R2 | TS4 | 2026-09-30 | The overview says Client Experience can change the refresh setting to "expire and rotate every 40 minutes". The same sentence spells the setting "Refresh Roken". | High that this page says 40 minutes. | 6 |
| R3 | TS5 | 2026-09-30 | Refresh is `POST https://signin.tradestation.com/oauth/token`, form-urlencoded, `grant_type=refresh_token`, required `client_id` and `refresh_token`. `client_secret` is optional in the table, required for the standard flow, and not required for PKCE. A rotating key's response includes a new refresh token. | High for the parameter table. | 6 |
| R4 | TS5 | 2026-09-30 | The refresh example response `scope` is `openid offline_access` and the example has no API scopes. | High that the example text is that string. None for whether a live refresh omits API scopes. | 6 |
| R5 | TS5 | 2026-09-30 | Revoking one refresh token revokes all refresh tokens for that API key. The parameter table names `refresh_token`. The example is `content-type: application/json` and the JSON field is `token`. | High that the page contains both shapes. None for which shape a server accepts. | 6 |
| R6 | TS4 | 2026-09-30 | Disabling a key blocks new access tokens from authentication or refresh. Re-enabling makes previously issued non-expiring refresh tokens usable again. Rotating the client secret leaves previously issued non-expiring refresh tokens usable. | High for those sentences. | 6 |
| R7 | TS5, TS10 | 2026-09-30 | Lost-response, replay, and family-recovery behavior for rotating refresh tokens is absent from these pages. | None for recovery behavior. The absence is the finding. | 6 |

`R1` and `R2` conflict. The interval stays `UNKNOWN`. `R5` leaves the
revocation request body `UNKNOWN`.

### Rate limit

| ID | URL | Retrieved | Statement | Confidence | Group |
| --- | --- | --- | --- | --- | --- |
| L1 | TS7 | 2026-09-30 | Each API key is allocated quota settings, applied and enforced per user. Exceeding quota returns HTTP 429. | High for that wording. None for the quota identity across processes, tokens, accounts, or keys. | 10 |
| L2 | TS7 | 2026-09-30 | Published standard table: Accounts, Order Details, Balances, and Positions are 320 per 5 minutes; Quote Change Stream, Barchart Stream, TickBar Stream, and Quote Snapshot are 500 per 5 minutes; Each Option Endpoint is 90 per 1 minute; MarketDepth Stream is 30 per 1 minute and 10 concurrent, combined across quotes and aggregates; Option Quote Stream and Option Chain Stream are 10 concurrent; Order Stream, Order Stream by Order Id, and Positions Stream are 40 concurrent. | High for the table. None for a future key's actual allocation. | 10 |
| L3 | TS7 | 2026-09-30 | Documented request headers are `X-RateLimit-Limit`, `X-RateLimit-Period`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and `X-RateLimit-Resource`. Documented concurrency headers are `X-Concurrency-Limit`, `X-Concurrency-Remaining`, and `X-Concurrency-Resource`. `X-RateLimit-Reset` is described as seconds until full reset. | High for the header names and that description. | 10 |
| L4 | TS7 | 2026-09-30 | A 429 example body is `{"Error":"TooManyRequests","Message":"Rate quota exceeded"}`. A stream 429 example message is `Stream quota exceeded`. One stream example shows `x-ratelimit-limit: 251` on resource `streaming-positions`. 251 does not appear in the standard table. | High that the examples contain those values. None that 251 is a standard quota. | 10 |

### Entitlement

| ID | URL | Retrieved | Statement | Confidence | Group |
| --- | --- | --- | --- | --- | --- |
| E1 | TS4 | 2026-09-30 | Non-partner access is restricted to accounts under the TradeStation login. The stated default login limit is 15 per application. | High for that sentence. None for a future login set. | 7 |
| E2 | TS1 | 2026-09-30 | `AccountType` valid values are `Cash`, `Margin`, `Futures`, and `DVP`. `Account.Status` lists Active, Closed, Closing Transaction Only, Margin Call - Closing Transactions Only, Inactive, Liquidating Transactions Only, Restricted, and 90 Day Restriction-Closing Transaction Only. | High for the published lists. None for a future account's values. | 7 |
| E3 | TS1 | 2026-09-30 | `AccountDetail` includes `IsStockLocateEligible`, `OptionApprovalLevel` with documented values 0 through 5, `DayTradingQualified`, and `PatternDayTrader`. | High for the fields. None for whether a field value is an entitlement grant. | 7 |
| E4 | TS1 | 2026-09-30 | `GET /v3/orderexecution/routes` "returns a list of valid routes that a client can specify when posting an order." | High for that sentence. None for the route list of a future account. | 7 |
| E5 | TS1 | 2026-09-30 | `MarketFlags` includes `IsDelayed` and `IsHardToBorrow`. The descriptions are "Is delayed" and "Is hard to borrow." | High for the field names. None for latency bounds or locate workflow. | 7 |
| E6 | TS3 | 2026-09-30 | SIM base URL is `https://sim-api.tradestation.com/v3`. LIVE base URL is `https://api.tradestation.com/v3`. The page says SIM is identical to LIVE except fake accounts, fake money, and instant simulated fills. | High that the page says that. | 5, 7 |
| E7 | TS1 | 2026-09-30 | Historical-order `since` says the query is limited to 730 days, and that SIM does not yet provide a full two years of history. It says simulated history is available back to around early November 2024, and that a full two years of simulated history will not be available until around early November 2026. It says Live can access a full two years. | High that the current spec text says this. See the retention conflict below. | 5, 12 |

### Streaming

| ID | URL | Retrieved | Statement | Confidence | Group |
| --- | --- | --- | --- | --- | --- |
| T1 | TS2 | 2026-09-30 | Orders and positions streams use `Content-Type: application/vnd.tradestation.streams.v3+json`. Other described streams use `application/vnd.tradestation.streams.v2+json`. `Transfer-Encoding` is `chunked`. | High. | 4 |
| T2 | TS2, TS1 | 2026-09-30 | `{"StreamStatus":"EndSnapshot"}` is sent after the initial snapshot. `{"StreamStatus":"GoAway"}` is sent before server termination and the client must restart. An `ERROR` object requires the client to terminate. The client may add a delay before re-requesting. | High for those sentences. None for a required delay or a loss-free restart. | 4 |
| T3 | TS1 | 2026-09-30 | Heartbeat, Heartbeat1, Heartbeat2, and Heartbeat3 each say a heartbeat is sent after 5 seconds on an idle stream. The heartbeat value is an integer. | High for that sentence. None for the meaning of a missing heartbeat. | 4 |
| T4 | TS1 | 2026-09-30 | Stream Positions `changes` defaults to false. When a stream is first opened with `changes=true`, the page says it returns the full snapshot first and then changes, and that `PositionID` is returned with each change. Stream Orders has no `changes` parameter in this spec. | High for those schema facts. None for reconnect or for an order-stream equivalent. | 4 |
| T5 | TS2 | 2026-09-30 | JSON objects are application-framed, may span HTTP chunks, and a newline is written at the end of each JSON object. The client owns connection lifetime. | High. | 4 |

## Conflicts left unresolved

1. Refresh rotation is 30 minutes on TS5 and 40 minutes on TS4. Interval is `UNKNOWN`.
2. Default API scopes are three names on TS4, four in TS6 prose, and five in the TS6 table. The granted set is `UNKNOWN`.
3. `offline_access` is unqualified-required in the TS6 table and is the refresh-enabling scope on TS5, TS8, and TS9. Whether a request that omits it is accepted is `UNKNOWN`.
4. Revocation parameter table uses `refresh_token`. The example body uses JSON field `token`. The accepted body is `UNKNOWN`.
5. Schema `Status` and schema `HistoricalStatus` share one 37-code enum and the same category text. Schema `Status1`, used by stream `Order1`, is a 20-code enum. Every `Status1` code also appears in `Status`. `Status` lists additional codes. Whether a stream can emit a code that is only in `Status` is `UNKNOWN`.
6. `Status` description marks `CSN` deprecated. `CSN` is absent from the enum. `UCN` is in the enum as Cancel Sent.
7. Get Orders `status` filter valid values are Open, Filled, Cancelled (or Canceled), and Rejected. Mapping those words onto the `Status` categories is `UNKNOWN`.
8. TS3 says SIM is identical to LIVE except fake accounts, fake money, and instant fills. TS1 historical orders describe a SIM history limit that Live does not share. Both sentences are published. Unstated SIM differences remain `UNKNOWN`.
9. Repository evidence in `docs/BROKER_CONTRACT.md`, `docs/P2_BROKER_RESEARCH.md`, and the 2026-09-29 verification recorded historical `since` as limited to 90 days. The specification retrieved 2026-09-30 says 730 days and includes the SIM history note in E7. The asset Last-Modified header is 2026-09-03. This file does not decide which text was on the page on 2026-09-26. The current retrieved sentence is the 730-day sentence. Observed retention is `UNKNOWN`.

`Status` codes: `ACK`, `ASS`, `BRC`, `BRF`, `BRO`, `CHG`, `CND`, `COR`,
`DIS`, `DOA`, `DON`, `ECN`, `EXE`, `FPR`, `LAT`, `OPN`, `OSO`, `OTHER`,
`PLA`, `REC`, `RJC`, `RPD`, `RSN`, `STP`, `STT`, `SUS`, `UCN`, `CAN`,
`EXP`, `OUT`, `RJR`, `SCN`, `TSC`, `UCH`, `REJ`, `FLL`, `FLP`.

`Status1` codes: `ACK`, `BRO`, `CAN`, `EXP`, `FLL`, `FLP`, `FPR`, `LAT`,
`OPN`, `OUT`, `REJ`, `UCH`, `UCN`, `TSC`, `RJC`, `DON`, `RSN`, `CND`,
`OSO`, `SUS`.

The `Status` description groups its codes as Open, Canceled, Rejected, and
Filled, with the labels in the schema text (Received, Option Assignment,
Bracket Canceled, Bracket Filled, Broken, Change, Condition Met, Fill
Corrected, deprecated `CSN`, Dispatched, Dead, Queued, Expiration Cancel
Request, Option Exercise, Partial Fill (Alive), Too Late to Cancel, Sent,
OSO Order, OrderStatus not mapped, Sending, Big Brother Recall Request,
Cancel Request Rejected, Replace Pending, Replace Sent, Stop Hit,
OrderStatus Message, Suspended, Cancel Sent, Canceled, Expired, UROut,
Change Request Rejected, Big Brother Recall, Trade Server Canceled,
Replaced, Rejected, Filled, Partial Fill (UROut)). Terminality and allowed
transitions are `UNKNOWN`.

## Twelve-behavior matrix

Taxonomy matches `docs/PHASE_2_PLAN.md` §5. Prior evidence is
`docs/P2_BROKER_RESEARCH.md` and `docs/BROKER_CONTRACT.md`. G2 and G3 below
are future evidence classes. This research does not cross either gate.

### 1. Idempotency — `OrderConfirmID`

| Field | Record |
| --- | --- |
| Current official evidence | TS1, 2026-09-30. `OrderRequest.OrderConfirmID` is a string of 1–22 characters: "used to prevent duplicates. Must be unique per API key, per order, per user." It is absent from the required list `AccountID`, `TimeInForce`, `OrderType`, `Quantity`, `Symbol`, `TradeAction`. `OrderConfirmResponse.OrderConfirmID` repeats the uniqueness sentence and has no length bounds in that schema. |
| Known | Field bounds on the request property, and the uniqueness sentence. |
| UNKNOWN | Retention, collision response, replay, timeout, session scope, and whether the confirmation value and a client-supplied value share semantics. |
| Docs resolve? | No. Primary `SIM_EXPERIMENT`. Confirmatory fail-closed `IMPLEMENTATION`. Gate `G3`. |
| Downstream | `P2-G`. |
| Confidence | High for the published wording. None for runtime semantics. |

### 2. Ambiguous place, replace, and cancel outcomes

| Field | Record |
| --- | --- |
| Current official evidence | TS1, 2026-09-30. Replace description: replaces an active order; a filled order cannot be updated. Replace example message: "Cancel/Replace order sent." Cancel description: "Sends a cancellation request to the relevant exchange." Cancel example message: "Cancel request sent". Place, replace, and cancel responses include 503 and 504. |
| Known | Those sentences and the listed status codes. |
| UNKNOWN | Whether "sent" is final state, the commit point, the lookup key, retry safety, and the recovery sequence. |
| Docs resolve? | No. Primary `SIM_EXPERIMENT`. Confirmatory fail-closed `IMPLEMENTATION`. Gate `G3`. |
| Downstream | `P2-G`. |
| Confidence | High that the pages contain no recovery algorithm. |

### 3. Order state machine

| Field | Record |
| --- | --- |
| Current official evidence | TS1, 2026-09-30. `Orders` references `Order`, whose status is `Status`. `HistoricalOrders` uses `HistoricalStatus`, same enum and description as `Status`. Stream order payloads use `Order1`, whose status is `Status1`. The two enums are conflict 5. Get Orders and Get Historical Orders filter text lists Open, Filled, Cancelled (or Canceled), and Rejected. |
| Known | The two published enums, their schema assignments, and the filter words. |
| UNKNOWN | Which enum is complete, whether unlisted codes occur, terminality, transitions, corrections, busts, duplicate or out-of-order delivery, and REST-versus-stream authority. |
| Docs resolve? | Partly narrowed, not closed. Primary `READ_ONLY_AUTHENTICATED_PROBE`. Confirmatory `SIM_EXPERIMENT`. Gates `G2` then `G3`. |
| Downstream | `P2-E`. |
| Confidence | High that both enums are published. None for a single runtime catalog. |

### 4. Stream recovery

| Field | Record |
| --- | --- |
| Current official evidence | T1–T5. |
| Known | Content types, `EndSnapshot`, `GoAway`, error termination, the idle-heartbeat sentence, the first-open `changes=true` position sequence, and chunk framing. |
| UNKNOWN | Loss-free delivery, reconnect snapshot, order-stream handoff, heartbeat absence threshold, backoff, replay cursor, sequence numbers, and gap or duplicate detection. |
| Docs resolve? | Partly narrowed, not closed. Primary `READ_ONLY_AUTHENTICATED_PROBE`. Gate `G2`. No G3 experiment is assigned by the plan. |
| Downstream | `P2-E`, `P2-F`. |
| Confidence | High for the quoted sentences. None for unstated recovery. |

### 5. SIM fidelity

| Field | Record |
| --- | --- |
| Current official evidence | E6 and E7. |
| Known | The identical-except sentence, instant simulated fills, fake accounts and fake money, and the historical-order SIM history sentence. |
| UNKNOWN | Partial fills, rejects, cancel and replace races, market hours, buying power, corporate actions, and any difference the pages do not state. |
| Docs resolve? | No. Primary `SIM_EXPERIMENT`. Gate `G3`. |
| Downstream | `P2-I` through `P2-H`. |
| Confidence | High for the two published sentences. None for unstated dimensions. |

### 6. Authentication conflicts

| Field | Record |
| --- | --- |
| Current official evidence | O1–O10, S1–S7, R1–R7. |
| Known | Default Auth Code flow, required `openid`, 20-minute access tokens, default indefinite refresh tokens, all-key refresh revocation, and the documented audience literal. |
| UNKNOWN | 30 versus 40 minutes, the granted scope set, whether `offline_access` may be omitted, key type, callbacks, login set, SIM entitlement, and revocation request shape. |
| Docs resolve? | No. Primary `OPERATOR_DECISION` before `G1`. Confirmatory `READ_ONLY_AUTHENTICATED_PROBE` at `G2`. No G3 experiment. |
| Downstream | `P2-B` and `G1`. |
| Confidence | High that the conflicts are on the pages. None for a future key. |

### 7. Account and entitlement

| Field | Record |
| --- | --- |
| Current official evidence | E1–E6 and L1. |
| Known | Published account-type and status lists, detail field names, route endpoint sentence, market-flag names, and the 15-login sentence. |
| UNKNOWN | Future account, symbol, route, data-latency, locate, quota, and SIM entitlement values, and whether a published field grants that entitlement. |
| Docs resolve? | No. Primary `OPERATOR_DECISION`. Confirmatory `READ_ONLY_AUTHENTICATED_PROBE`. Gate before `G1`, confirm at `G2`. |
| Downstream | `G1`. |
| Confidence | High for the schemas. None for future entitlements. |

### 8. Confirmation semantics

| Field | Record |
| --- | --- |
| Current official evidence | TS1, 2026-09-30. Confirm Order returns estimated cost and commission "without the order actually being placed." The confirm `requestBody.required` boolean in the parsed document is false. Place Order `requestBody.required` is true. `OrderConfirmID` is not in the place-order required list. |
| Known | The non-submitting sentence, and those two required-boolean values. |
| UNKNOWN | Whether confirmation is mandatory under any policy, ID lifetime, stale-confirm handling, and price or cost binding. The meaning of `requestBody.required: false` is `UNKNOWN`. |
| Docs resolve? | No. Primary `SIM_EXPERIMENT`. The docs re-check found no lifetime or binding sentence. Gate `G3`. |
| Downstream | `P2-G`. |
| Confidence | High for the non-submitting sentence. None for unstated semantics. |

### 9. Batch and group atomicity

| Field | Record |
| --- | --- |
| Current official evidence | TS1, 2026-09-30. OCO: if one order is filled or partially filled, the other orders in the group are cancelled. Bracket orders are described as same symbol, same side, and closing transactions. The note says each sibling is treated as an individual order, quantities are not validated equal, and a bracket cannot be updated as one transaction. `OrderResponses` has `Orders` and `Errors` arrays. |
| Known | Those sentences and the mixed response shape. |
| UNKNOWN | Submission atomicity, rollback, OSO parent or child failure, and mixed-response recovery. |
| Docs resolve? | No. Primary `SIM_EXPERIMENT`. Gate `G3`. |
| Downstream | `P2-G`, `P2-I`. |
| Confidence | High for the sibling-order sentences. None for full atomicity. |

### 10. Rate-limit identity

| Field | Record |
| --- | --- |
| Current official evidence | L1–L4. |
| Known | Per-key allocation wording, per-user enforcement wording, the standard table, and the header names. |
| UNKNOWN | The composite identity across processes, tokens, logins, accounts, keys, and applications, and whether example value 251 is normative. |
| Docs resolve? | No. Primary `OPERATOR_DECISION`. Confirmatory `READ_ONLY_AUTHENTICATED_PROBE`. No G3 experiment. |
| Downstream | `P2-D`. |
| Confidence | High for the published wording. None for aggregation. |

### 11. Decimal and time semantics

| Field | Record |
| --- | --- |
| Current official evidence | TS1, 2026-09-30. Get Symbol Details says to use formatting objects "to display provided prices and quantities." `PriceFormat.Format` is `Decimal`, `Fraction`, or `SubFraction`. `QuantityFormat` includes `MinimumTradeQuantity`, described as the minimum quantity that can be traded. Get Bars `sessiontemplate` values are `USEQPre`, `USEQPost`, `USEQPreAndPost`, `USEQ24Hour`, and `Default`. Timestamp descriptions include RFC3339 `Z` examples. |
| Known | Those formatting fields, the display sentence, the minimum-quantity sentence, and the session-template values. |
| UNKNOWN | Whether increments reject orders, rounding, clock skew, DST, and which timestamp is authoritative. |
| Docs resolve? | Partly narrowed, not closed. Primary docs portion remains incomplete. Confirmatory `READ_ONLY_AUTHENTICATED_PROBE` at `G2`. |
| Downstream | `P2-E`. |
| Confidence | High for the field text. None for order validation. |

### 12. Retention

| Field | Record |
| --- | --- |
| Current official evidence | E7. `pageSize` is an integer, minimum 1, maximum 600, default 600. Omitted pagination returns at most 600 orders. `nextToken` lifetime is one hour. No archive or export path is present in the 35-path document. |
| Known | The current `since` sentence, the pagination bounds, and the absence of an archive path from this document. |
| UNKNOWN | Why the current sentence differs from the repository's 90-day record, broker-side retention, statements, correction history, and the Operator's retention duty. Absence of an archive path does not establish that no other channel exists. |
| Docs resolve? | Partly narrowed, not closed. Organizational retention remains `OPERATOR_DECISION`. |
| Downstream | `P2-J`. |
| Confidence | High for the current spec sentence. None for availability outside that sentence. |

## Matrix summary

- Resolved by public docs: 0 of 12.
- Narrowed and still unresolved: groups 3, 4, 5, 9, 11, and 12.
- Published conflicts inside group 6: refresh interval, default scopes, and `offline_access`.
- Future read-only evidence class, not authorized here: groups 3, 4, 6, 7, 10, and 11.
- Future SIM-experiment class, not authorized here: groups 1, 2, 3, 5, 8, and 9.
- Operator or Client Experience clarification remains open for every group.

Group 3 is newly narrowed relative to `docs/P2_BROKER_RESEARCH.md` because
status enums are now in the specification. Group 4 is further narrowed by
the idle-heartbeat sentence. Group 12's current `since` sentence differs
from the 90-day repository record. None of those changes closes a group.

## URL join preserved from Group 2

Group 2 names one API URL, `https://sim-api.tradestation.com/v3`, and
`connect_allowed` is false. The LIVE resource host
`https://api.tradestation.com/v3` stays prohibited.

TS1's server is `https://api.tradestation.com` and its paths already include
`/v3`. TS3's SIM base is `https://sim-api.tradestation.com/v3`. The
documented join is one `/v3` segment:
`https://sim-api.tradestation.com/v3` plus the path suffix after `/v3`.
Whether SIM serves each path is `UNKNOWN` except for the history sentence
in E7. This research did not request either host.

The OAuth audience literal `https://api.tradestation.com` is a required
authorization query value on TS8 and TS9. It is a different string from the
prohibited resource host `https://api.tradestation.com/v3`.

## Unblocked implementation areas

These areas can be implemented offline, with no socket, no credential, and
no default for an unknown value. An absent explicit input fails closed.

1. Authorization-request assembly for the standard flow and for PKCE, using
   the documented parameter names. `client_id`, `redirect_uri`, `scope`, and
   the flow mode are explicit inputs. The documented audience literal may be
   copied into the query string. `state` may be required by local policy
   even though TS8 calls it recommended. No request is sent.
2. Callback classification of `code` plus `state`, and of
   `error=access_denied`. A missing or mismatched `state` fails closed.
   Code length stays variable.
3. Token-exchange form templates: standard flow includes `client_secret`;
   PKCE includes `code_verifier` and omits `client_secret` on the terms of
   TS9. Unknown mode fails closed. Response field names are read from a
   fixture. Secret values are not logged.
4. Refresh-request form parameter names from R3. No 30-minute timer and no
   40-minute timer. `expires_in` comes from the response fixture.
5. Read-only request templates for the v3 GET paths in TS1, joined to the
   SIM base with a single `/v3`, `connect_allowed` false. Response bytes
   stay raw. Status strings stay raw. An unrecognized status is `UNKNOWN`.
6. A local stream-frame reader for newline-delimited JSON that may span
   chunks, recognizing the documented `EndSnapshot`, `GoAway`, and `ERROR`
   markers. No reconnect schedule and no heartbeat timeout.

## Not unblocked

- Choosing requested scopes, or treating any default list as the grant.
- Omitting or requiring `offline_access` as a settled rule.
- A refresh rotation interval, lost-refresh recovery, or revocation HTTP body.
- Logout as token invalidation.
- A path-to-scope allowlist.
- A closed status mapper that picks `Status` or `Status1`.
- Rate-limit retry timing, quota identity, and the example value 251.
- Account, route, symbol, and data entitlements.
- Order place, replace, cancel, confirm, and group behavior.
- Any network call, credential, TradeStation `SIM` session, or `LIVE` path.

ADR-0002, TokenStore compare-and-swap, Group 2 host denial, and the existing
tests are unchanged.
