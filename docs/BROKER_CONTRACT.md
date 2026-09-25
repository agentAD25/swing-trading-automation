# TradeStation Broker Contract Research

## Status and scope

This is a Phase 1B research handoff, not an architecture decision or
implementation specification. It records the public TradeStation API contract
that a later production design would need to reconcile. No account, credential,
or API call was used. `SIM` is the only authorized execution mode for this
repository; `LIVE` is unauthorized.

Research was performed on 2026-09-25 from current public TradeStation
documentation. Every material claim below is classified and cites a source with
an access timestamp. Candidate implications are explicitly non-decisions.

## Sourced findings

### Environment and API version

1. **Fact:** TradeStation recommends API v3 for new features; the documented
   v3 live base URL is `https://api.tradestation.com/v3`. [S1; accessed
   2026-09-25T18:05:40Z; "API Versions"]
2. **Fact:** The simulator base URL is
   `https://sim-api.tradestation.com/v3`. TradeStation describes SIM as
   interface-identical to LIVE except that accounts and money are fake and
   executions are simulated with instant fills. [S2; accessed
   2026-09-25T18:05:40Z; "SIM vs. LIVE"]
3. **Inference (high confidence):** SIM can validate request/response
   integration but cannot, by itself, establish realistic latency, queue
   position, partial-fill, slippage, or venue behavior because the documented
   fill model is instantaneous. [S2; accessed 2026-09-25T18:05:40Z; limitation
   inferred from "instant fills"]
4. **Candidate implication, not a decision:** Any future implementation should
   make the SIM host an explicit fail-closed invariant rather than treating the
   host as a freely switchable runtime option. This follows repository
   governance and TradeStation's warning that applications allowing SIM/LIVE
   switching can cause mistakes. [S2; accessed 2026-09-25T18:05:40Z; `danger`
   admonition]

### Authentication and authorization

5. **Fact:** The documented default is OAuth 2.0 Authorization Code flow for a
   regular web application. PKCE for SPA/native applications requires a
   TradeStation configuration change through Client Experience. [S3; accessed
   2026-09-25T18:05:40Z; "Default API Key Configuration"]
6. **Fact:** Authorization occurs at
   `https://signin.tradestation.com/authorize`; token exchange occurs at
   `https://signin.tradestation.com/oauth/token`; API requests use a bearer
   token. Access tokens expire after 20 minutes. [S4, S7; accessed
   2026-09-25T18:05:40Z; "Implementation Guide" and "Bearer-Token"]
7. **Fact:** `openid` is required in an authorization request and
   `offline_access` is required to obtain refresh tokens. API access is
   separated into scopes including `MarketData`, `ReadAccount`, `Trade`,
   `OptionSpreads`, and `Matrix`. [S4, S6; accessed
   2026-09-25T18:05:40Z; "scope" and "TradeStation API Scopes"]
8. **Fact:** TradeStation says refresh tokens must be stored securely. Standard
   authorization-code refresh requires the client secret; PKCE refresh does
   not. Revoking one refresh token revokes all refresh tokens for that API key.
   [S5; accessed 2026-09-25T18:05:40Z; `danger`, "Refresh Token", and
   "Revoking Refresh Tokens"]
9. **Fact with source conflict:** The refresh-token page says optional rotating
   refresh tokens rotate every 30 minutes with a 24-hour absolute lifetime,
   while the authentication overview says the configurable rotation interval
   is 40 minutes. [S5, S3; accessed 2026-09-25T18:05:40Z; "Refresh Token" and
   "Default API Key Configuration"]
10. **Fact with source conflict:** The scopes page says default keys include
    `MarketData`, `ReadAccount`, `Trade`, `OptionSpreads`, and `Matrix`; the
    authentication overview lists only `MarketData`, `ReadAccount`, and
    `Trade` as defaults. [S6, S3; accessed 2026-09-25T18:05:40Z;
    "TradeStation API Scopes" and "Default API Key Configuration"]
11. **Limitation:** Actual key type, permitted logins, callback URLs, scopes,
    entitlements, and refresh-token policy are key-specific and cannot be
    established without Client Experience confirmation and later authorized
    account setup. [S3, S5, S6; accessed 2026-09-25T18:05:40Z]

### Brokerage read model

12. **Fact:** v3 exposes account discovery, balances, beginning-of-day balances,
    current orders, historical orders, positions, and streams for orders and
    positions. The account response can include account type/status and details
    such as buying-power-warning and day-trading flags. [S7; accessed
    2026-09-25T18:05:40Z; "Brokerage" / "Get Accounts"]
13. **Fact:** Multi-account brokerage requests accept 1–25 account IDs, and the
    specification recommends batches of 10. Order-by-ID requests accept 1–50
    order IDs. [S7; accessed 2026-09-25T18:05:40Z; "Get Orders" and
    "Get Orders By Order ID"]
14. **Fact:** `GET /v3/brokerage/accounts/{accounts}/orders` covers today's and
    open orders. Without pagination it returns at most 600 orders; pagination
    tokens have a documented one-hour lifetime. [S7; accessed
    2026-09-25T18:05:40Z; "Get Orders"]
15. **Fact:** Historical-order lookup excludes open orders, is limited to the
    prior 90 days, and has the same 600-order unpaginated maximum and one-hour
    pagination-token lifetime. [S7; accessed 2026-09-25T18:05:40Z;
    "Get Historical Orders"]
16. **Fact:** Batch brokerage responses can contain both successful objects and
    an `Errors` array, as illustrated by the documented balance examples.
    Therefore an HTTP success alone does not establish complete batch success.
    [S7; accessed 2026-09-25T18:05:40Z; "Get Balances" response example]
17. **Fact:** The order read model exposes `OrderID`, status code and
    description, quantities ordered/executed/remaining, timestamps, prices,
    route, and conditional-order relationships. [S7; accessed
    2026-09-25T18:05:40Z; "Get Orders" response example]
18. **Limitation:** The specification examples show status values such as
    `ACK`, `OPN`, and `FLL`, but the reviewed official material does not provide
    a complete status enumeration or transition graph. [S7; accessed
    2026-09-25T18:05:40Z; "Get Orders" response example]

### Order lifecycle

19. **Fact:** `POST /v3/orderexecution/orderconfirm` estimates price, cost,
    commission, and related fields without placing an order. Its response can
    include an `OrderConfirmID`. [S7; accessed 2026-09-25T18:05:40Z;
    "Confirm Order"]
20. **Fact:** `POST /v3/orderexecution/orders` places an order. Required
    top-level fields are account ID, symbol, quantity, order type,
    time-in-force, and trade action. The documented order types at this
    endpoint are `Market`, `Limit`, `StopMarket`, and `StopLimit`; trade actions
    differ for equities/futures and options. [S7; accessed
    2026-09-25T18:05:40Z; "Place Order" request schema]
21. **Fact:** For stocks and options, an omitted route defaults to
    `Intelligent`; currently valid routes are discoverable through
    `GET /v3/orderexecution/routes`. [S7; accessed
    2026-09-25T18:05:40Z; "Place Order" / "Get Routes"]
22. **Fact:** The order request's `OrderConfirmID` is described as a unique
    identifier used to prevent duplicates and must be unique per API key,
    order, and user. [S7; accessed 2026-09-25T18:05:40Z; "Place Order" request
    schema]
23. **Fact:** Order placement can return an `Orders` array and an `Errors`
    array in one HTTP 200 response, so transport success does not imply every
    requested order succeeded. [S7; accessed 2026-09-25T18:05:40Z; "Place
    Order" response example]
24. **Fact:** Replace uses
    `PUT /v3/orderexecution/orders/{orderID}`. A filled order cannot be
    replaced, and if order type is changed it can only be changed to `Market`.
    The successful example says "Cancel/Replace order sent", which acknowledges
    a request rather than documenting final venue state. [S7; accessed
    2026-09-25T18:05:40Z; "Replace Order"]
25. **Fact:** Cancel uses
    `DELETE /v3/orderexecution/orders/{orderID}` and sends a cancellation
    request to the relevant exchange. The successful example says "Cancel
    request sent", not "cancelled". [S7; accessed
    2026-09-25T18:05:40Z; "Cancel Order"]
26. **Inference (high confidence):** After place, replace, or cancel
    acknowledgement, final state must be determined from subsequent order
    state rather than inferred from the command response. [S7; accessed
    2026-09-25T18:05:40Z; command response wording and "Get Orders"]
27. **Fact:** Group orders support `BRK`, `OCO`, and `NORMAL`. For OCO, a full
    or partial fill of one sibling cancels the others. A bracket is a
    closing-only OCO with same symbol and side; partial fills auto-decrement the
    remaining sibling. TradeStation also says siblings are handled as
    individual orders, sibling quantities are not validated equal, and a
    bracket cannot be updated atomically. [S7; accessed
    2026-09-25T18:05:40Z; "Confirm Group Order" and "Place Group Order"]
28. **Limitation:** Confirmation is expressly non-submitting, but the reviewed
    documentation does not state that a confirmation is mandatory before
    placement or that successful confirmation guarantees later acceptance.
    [S7; accessed 2026-09-25T18:05:40Z; "Confirm Order" / "Place Order"]

### Market data and streaming

29. **Fact:** v3 provides snapshots and streams for bars and quotes, option
    endpoints, symbol details, and market-depth streams. Historical bars allow
    minute, daily, weekly, and monthly units; minute interval is capped at
    1,440, and `barsback` is mutually exclusive with `firstdate`. [S7;
    accessed 2026-09-25T18:05:40Z; "MarketData" / "Get Bars"]
30. **Fact:** Stream responses use TradeStation-specific streaming JSON media
    types and documented stream schemas include data records, heartbeats,
    status records, deletion records where applicable, and error records.
    [S7; accessed 2026-09-25T18:05:40Z; streaming endpoint response schemas]
31. **Limitation:** The reviewed specification documents stream record shapes
    but does not establish replay cursors, sequence numbers, a reconnect/resume
    guarantee, ordering across connections, heartbeat timeout requirements, or
    an authoritative snapshot-to-stream handoff procedure. [S7; accessed
    2026-09-25T18:05:40Z]
32. **Open question:** Whether data is real-time, delayed, or unavailable for a
    particular user/symbol is entitlement-specific and is not resolved by the
    public endpoint schema alone. [S3, S6, S7; accessed
    2026-09-25T18:05:40Z]

### Rate limits and failures

33. **Fact:** Limits are applied per user, with quotas allocated to each API
    key. They use rolling request intervals and, for some streams, concurrent
    connection limits. Exceeding either returns HTTP 429. [S8; accessed
    2026-09-25T18:05:40Z; "Understanding Rate Limits"]
34. **Fact:** Default documented quotas include 320 requests per five minutes
    for accounts, order details, balances, and positions; 500 per five minutes
    for quote, barchart, and tick-bar streams/snapshots as listed; 90 per minute
    for each option endpoint; and explicit concurrent limits for market depth,
    option, order, and position streams. [S8; accessed
    2026-09-25T18:05:40Z; "Resource Categories"]
35. **Fact:** Responses expose `X-RateLimit-*` and, for streams,
    `X-Concurrency-*` headers. TradeStation directs clients to use
    `X-RateLimit-Reset` when handling 429 and recommends streaming where
    available. [S8; accessed 2026-09-25T18:05:40Z; "Rate Limit Response
    Headers" and "Handling a 429 Response"]
36. **Fact:** The v3 specification documents 400, 401, 403, 404, 429, 503, and
    504 error responses across the reviewed brokerage and order endpoints.
    [S7; accessed 2026-09-25T18:05:40Z; endpoint "Responses"]
37. **Limitation:** Published quotas are defaults and can vary by key; the
    documentation does not promise that a retry after an ambiguous timeout is
    safe or duplicate-free. [S8, S7; accessed
    2026-09-25T18:05:40Z]

## Production-facing candidate constraints

These are research implications for later ADR review, not approved design:

- Bind any future execution client to v3 SIM only and fail closed on any other
  host or unknown environment. Evidence: findings 1–4.
- Treat token material as secret, request only required scopes, and design
  token renewal around the documented 20-minute access-token lifetime only
  after key policy is confirmed. Evidence: findings 5–11.
- Treat HTTP 200 as transport-level success only; inspect per-item `Errors`.
  Evidence: findings 16 and 23.
- Treat place/replace/cancel responses as acknowledgements and reconcile final
  state through the broker read model. Evidence: findings 24–26.
- Consume advertised throttling headers and distinguish request quota from
  stream concurrency. Evidence: findings 33–35.
- Do not derive execution realism from SIM instant fills. Evidence: finding 3.

No retry policy, persistence model, risk rule, analytics behavior, signal
meaning, order policy, or execution algorithm is selected here.

## `BROKER_BEHAVIOR_UNRESOLVED`

The following items block a production contract from being considered complete:

1. **BROKER_BEHAVIOR_UNRESOLVED — idempotency:** Exact acceptance, retention
   window, collision behavior, and retry semantics of `OrderConfirmID`,
   especially after timeout or lost response.
2. **BROKER_BEHAVIOR_UNRESOLVED — ambiguous outcomes:** Authoritative recovery
   procedure after 503/504, disconnect, or client timeout during place,
   replace, and cancel.
3. **BROKER_BEHAVIOR_UNRESOLVED — order state machine:** Complete status-code
   enumeration, terminal states, allowed transitions, correction/bust handling,
   and ordering guarantees between REST and streams.
4. **BROKER_BEHAVIOR_UNRESOLVED — stream recovery:** Heartbeat thresholds,
   reconnect backoff, replay/resume support, gap detection, duplicate delivery,
   and snapshot/stream reconciliation.
5. **BROKER_BEHAVIOR_UNRESOLVED — SIM fidelity:** Partial fills, rejects,
   cancels, replace races, market hours, buying power, corporate actions, and
   data entitlements beyond the documented instant-fill statement.
6. **BROKER_BEHAVIOR_UNRESOLVED — authentication conflicts:** Whether rotating
   refresh tokens rotate at 30 or 40 minutes, and which API scopes are actually
   default for the future key.
7. **BROKER_BEHAVIOR_UNRESOLVED — account and entitlement contract:** Approved
   account types, symbols/assets, market-data latency, sessions, routes, short
   locate behavior, and key-specific quotas.
8. **BROKER_BEHAVIOR_UNRESOLVED — confirmation semantics:** Whether
   confirmation is required, how long `OrderConfirmID` remains valid, and
   whether confirmation has any acceptance or price-binding guarantee.
9. **BROKER_BEHAVIOR_UNRESOLVED — batch atomicity:** Exact transaction boundary
   for multi-leg, OSO, and group submissions, including behavior when the
   response contains both orders and errors.
10. **BROKER_BEHAVIOR_UNRESOLVED — rate-limit identity:** How quotas aggregate
    across processes, tokens, logins, accounts, and multiple applications in
    the intended deployment.
11. **BROKER_BEHAVIOR_UNRESOLVED — decimal and time semantics:** Precision,
    rounding, tick-size validation, timestamp precision, timezone/session
    boundaries, and clock-skew expectations for every intended asset class.
12. **BROKER_BEHAVIOR_UNRESOLVED — retention:** Availability beyond the
    documented 90-day historical-order window and 600-item unpaginated limits.

Resolution requires later first-party clarification and/or authorized,
non-LIVE contract testing. No item may be resolved by assumption.

## Sources

All sources are first-party TradeStation API documentation published by
TradeStation and accessed at `2026-09-25T18:05:40Z`.

- **S1 — TradeStation API Docs.**
  https://api.tradestation.com/docs/
  Supports API purpose, version recommendation, asset coverage, and base URLs.
  Limitation: overview, not endpoint behavior.
- **S2 — SIM vs. LIVE.**
  https://api.tradestation.com/docs/fundamentals/sim-vs-live/
  Supports SIM host and stated fake-account/instant-fill behavior.
  Limitation: no simulator fidelity specification.
- **S3 — Authentication Overview.**
  https://api.tradestation.com/docs/fundamentals/authentication/auth-overview/
  Supports default key configuration, account restrictions, URI configuration,
  and key administration. Limitation: conflicts with S5 and S6 as noted.
- **S4 — Auth Code Flow.**
  https://api.tradestation.com/docs/fundamentals/authentication/auth-code/
  Supports OAuth endpoints, parameters, scopes, and 20-minute token lifetime.
  Limitation: covers Auth0 keys and standard confidential-client flow.
- **S5 — Refresh Tokens.**
  https://api.tradestation.com/docs/fundamentals/authentication/refresh-tokens/
  Supports refresh/revocation behavior and token-security warning. Limitation:
  rotation interval conflicts with S3.
- **S6 — Scopes.**
  https://api.tradestation.com/docs/fundamentals/authentication/scopes/
  Supports scope meanings and stated defaults. Limitation: defaults conflict
  with S3 and do not prove a particular key's configuration.
- **S7 — TradeStation API Specification.**
  https://api.tradestation.com/docs/specification/
  Supports v3 endpoint paths, request/response schemas, examples, streaming
  media types, and documented response codes. Limitation: examples are not a
  complete behavioral state machine or guarantee.
- **S8 — Rate Limiting Overview.**
  https://api.tradestation.com/docs/fundamentals/rate-limiting/rate-limiting-overview/
  Supports default quotas, rolling/concurrent models, headers, and 429
  behavior. Limitation: quotas are key-specific and subject to adjustment.
