# TradeStation Client Experience and Operator Questions

## Use and safety

These are draft questions only. No vendor contact, account action, credential,
API call, or probe occurred. Before sending, the human Operator must remove
questions outside the intended asset/account scope and must not insert secrets,
tokens, account numbers, key values, or personal information.

Please request written answers that identify the applicable API version,
environment (`SIM` versus LIVE), key configuration, effective date, and any
behavior that is contractual versus observational. A LIVE answer must not be
treated as authorization to use LIVE.

The factual premises in these questions use the dated first-party source
register and the `BROKER_EVIDENCE_CONFLICT` records in
`docs/P2_BROKER_RESEARCH.md`, accessed 2026-09-26 (third conflict,
`offline_access`, recorded at coordinator integration 2026-09-29 from the
same pages). Questions intentionally ask TradeStation to reconcile those
sources; they do not select one as correct.

## Questions for TradeStation Client Experience

### Authentication, refresh, scopes, and key configuration (group 6)

1. For a newly issued Auth0 API key configured with rotating refresh tokens,
   is the rotation interval 30 minutes or 40 minutes? Your current Refresh
   Tokens page says 30; Authentication Overview says 40.
2. Does the 24-hour absolute refresh-token lifetime apply to every rotating
   configuration? From what event is the 24 hours measured, and can the value
   differ by key?
3. For non-rotating refresh tokens, what expiration, inactivity, revocation,
   and maximum-lifetime rules apply?
4. If two refreshes race with the same rotating token, what responses occur,
   is token reuse detected, and are the token family or all key tokens revoked?
5. Your Authentication Overview lists default API scopes as `MarketData`,
   `ReadAccount`, and `Trade`; the Scopes page also identifies
   `OptionSpreads`, and its table marks `Matrix` as default. What exact scopes
   are default today, and which would be granted to the proposed key?
6. Can the key be provisioned with only `MarketData` and `ReadAccount` before
   any separately approved order phase, with `Trade`, `OptionSpreads`, and
   `Matrix` absent?
7. Does a token's returned `scope` field authoritatively enumerate all granted
   permissions, including permissions omitted from the request?
8. What exact Auth Code/PKCE application type, permitted logins, callback URLs,
   refresh policy, and SIM access would be configured for the proposed key?
9. When one refresh token is revoked, does “all Refresh Tokens for that API
   key” include every permitted login/user and every active token family?

### `offline_access` wording (group 6; coordinator addendum 2026-09-29)

72. Your Auth Code and Refresh Tokens pages say `offline_access` is required
    to obtain refresh tokens. The Scopes table labels `offline_access`
    **required** with no such qualification. For the proposed key, is
    `offline_access` required on every authorization request, or only when a
    refresh token is requested? If a request omits it, does authorization or
    token exchange fail, and with what error?
73. Can a confidential or PKCE key be issued that successfully returns
    access tokens for `openid` plus read-only API scopes with **no**
    refresh token and **no** `offline_access` grant? If not, what is the
    minimum required scope set for a one-shot read-only token?

These two questions do not select a winner between the pages. They exist so
Client Experience can close `AUTH_ARCHITECTURE.md` U-17 before any future
G1. Do not treat a LIVE-keyed answer as LIVE authorization.

### Accounts, SIM entitlement, assets, market data, and routes (groups 5 and 7)

10. Does the proposed key include access to the TradeStation SIM API, and which
    SIM account types and approved logins would `GET /brokerage/accounts`
    return?
11. Are SIM accounts, buying power, positions, market sessions, routes, and
    entitlements reset or reseeded? If so, on what schedule and with what
    notice?
12. Which asset classes and order capabilities are enabled for each intended
    SIM account type: equities, equity options, futures, multi-leg options,
    OCO, bracket, and OSO?
13. For each intended exchange/feed and session, is API market data real-time,
    delayed, snapshot-only, or unavailable in SIM? How is that status exposed
    per response or symbol?
14. Does SIM use the same market-data entitlements as the associated login,
    and can order entitlement differ from market-data entitlement?
15. Are the routes returned by `GET /orderexecution/routes` exhaustive for the
    authenticated SIM account and asset class? Can routes change intraday?
16. What API-supported short-sale/borrow workflow applies in SIM? Does
    `IsStockLocateEligible` or `IsHardToBorrow` establish entitlement, order
    eligibility, locate availability, or only observable account/market-data
    status?
17. Which market-hours, holiday, early-close, overnight, and extended-session
    rules does SIM enforce for each intended asset class?
18. Beyond instant fills, which SIM behaviors intentionally differ from LIVE
    for partial fills, rejects, cancels, replace races, buying power, corporate
    actions, and data entitlements?

### Quotas and rate-limit identity (group 10)

19. What exact tuple identifies a quota bucket: API key, TradeStation
    user/login, OAuth subject, access token, account, source process/IP,
    application, resource category, or a combination?
20. Do multiple access tokens or processes for the same login and key share
    `X-RateLimit-*` and stream concurrency counters?
21. Do multiple approved logins on one key share any quota or concurrency
    counters? Do multiple keys used by one login share them?
22. What quotas and concurrent-stream limits would apply to the proposed key,
    and may they differ between SIM and LIVE?
23. Are the response headers authoritative for the current key and user? Can
    limits change without notice, and is `X-RateLimit-Reset` always relative
    seconds?
24. Does reconnecting a stream consume request quota, concurrency quota, or
    both, and when is a disconnected stream's concurrency slot released?

### `OrderConfirmID` and confirmation (groups 1 and 8)

25. Is `OrderConfirmID` generated only by Confirm Order, or may a client
    generate it? If client-generated, what character set and generation rules
    apply beyond the documented 1–22 character length?
26. What does “unique per API key, per order, per user” mean as an exact
    uniqueness key?
27. How long is an `OrderConfirmID` retained for duplicate prevention, and
    when may it be safely reused?
28. If the same ID and identical order payload are submitted twice, what exact
    HTTP/body response is returned and can more than one order be created?
29. If the same ID is submitted with a different payload, account, user,
    session, or token, what exact result occurs?
30. Is duplicate prevention atomic for concurrent submissions using the same
    ID?
31. After a client timeout or lost place-order response, is resubmitting the
    identical request with the same ID supported? If not, what exact lookup
    procedure identifies whether an order was created?
32. Is confirmation required for any account, asset, order type, buying-power
    warning, group, or OSO case?
33. How long is a confirmation and its returned ID valid, and what invalidates
    it: time, quote change, buying-power change, payload change, session, or
    token change?
34. Does successful confirmation guarantee later syntactic validation,
    acceptance, buying power, route availability, price, cost, or commission?
    If none are guaranteed, please state that explicitly.
35. Is a confirmation bound to the exact canonical order payload? Which fields
    may differ when the ID is supplied to Place Order?

### Command acknowledgement and ambiguous outcomes (group 2)

36. For Place Order, what is the server-side commit point after which an order
    may exist even if the client receives 503, 504, disconnect, or timeout?
37. What authoritative read endpoint and correlation value should be used
    after an ambiguous place outcome if no `OrderID` was received?
38. Is any place retry safe after an ambiguous response? If yes, identify the
    required ID, retention window, and exact response for a prior success.
39. For Replace Order, does “Cancel/Replace order sent” mean only request
    acceptance? Can the original fill while replacement is pending, and how
    are original and replacement identities related?
40. After an ambiguous replace outcome, which states prove that the original,
    replacement, both, or neither are active?
41. For Cancel Order, does “Cancel request sent” mean only request acceptance?
    Which status or event is authoritative for final cancellation?
42. After an ambiguous cancel outcome, is retry supported, and what results
    distinguish already filled, already cancelled, unknown order, and
    cancellation still pending?
43. Are place, replace, and cancel acknowledgements ordered relative to order
    stream events or REST observations? If not, what reconciliation procedure
    do you support?

### Status catalog and corrections (group 3)

44. Please provide the complete current v3 order-status code catalog with
    descriptions, terminal/non-terminal classification, and applicable asset
    and order types.
45. Please provide allowed transitions, including partial fill, pending
    cancel, cancelled, rejected, expired, replaced, corrected, busted, and
    trade-cancelled cases.
46. Can a terminal status later change because of correction or bust? How is
    that represented in REST and order streams?
47. Are order events delivered at least once, at most once, or with no delivery
    guarantee? Is ordering guaranteed per account, order, connection, or not
    at all?
48. When REST and stream disagree, which source is authoritative and after
    what delay should the discrepancy be escalated?

### Stream lifecycle, replay, and snapshot handoff (group 4)

49. What is the heartbeat cadence for every v3 account/order/position and
    market-data stream, and after what silence should a client reconnect?
50. Does any v3 stream support a replay cursor, resume token, sequence number,
    event ID, or `Last-Event-ID` equivalent? If not, please confirm there is no
    replay guarantee.
51. For positions opened with `changes=true`, does the documented full
    snapshot-then-changes sequence—and its `EndSnapshot` marker—establish a
    loss-free boundary? Can updates be duplicated, omitted, or reordered
    around it, and does the same contract apply after reconnect?
52. After `GoAway`, `ERROR`, network interruption, or token expiry, what
    reconnect delay/backoff is required?
53. On reconnect, is a fresh complete snapshot always sent before updates?
    Are records ordered or deduplicated across old and new connections?
54. Are `GoAway` and `ERROR` always delivered before server termination, or
    must clients handle silent EOF?
55. How should clients detect gaps when records contain no documented sequence
    number, and what REST snapshot procedure is authoritative for recovery?
56. What token-renewal behavior is supported for an indefinitely open stream:
    continue with the original token, reconnect before expiry, or another
    mechanism?

### Group, multi-leg, OCO, bracket, and OSO behavior (group 9)

57. For NORMAL group, OCO, bracket, multi-leg option, and OSO submissions,
    which operations are atomic and which siblings/legs are committed
    independently?
58. If a response contains both `Orders` and `Errors`, are successful orders
    active even when a sibling failed? Is any automatic rollback attempted?
59. For OSO, what happens if the parent succeeds but one or more child orders
    fail validation or submission?
60. Can an OCO sibling fill while another sibling's cancel is pending, and how
    are resulting overfills represented?
61. What authoritative recovery procedure applies after a timeout during a
    group submission when only some order IDs are returned?

### Decimal, increment, timestamp, and session semantics (group 11)

62. Are `PriceFormat.Increment` and `QuantityFormat.Increment` order-validation
    constraints or display metadata only?
63. For each intended asset class, are off-increment prices/quantities rejected
    or rounded? If rounded, specify direction, tie-breaking rule, and whether
    the normalized value is returned before submission.
64. What maximum precision and numeric range are accepted for quantity, limit,
    stop, trailing-stop amount/percent, and option-leg ratio?
65. Are all `...DateTime`, `Timestamp`, `TimeStamp`, and `TimeUtc` fields UTC
    despite naming differences? What precision and ordering guarantees apply?
66. Which timestamp is authoritative for order acceptance, execution,
    correction, and cancellation, and what maximum clock skew should a client
    tolerate?
67. What calendars/time zones define session boundaries, good-till dates,
    holidays, early closes, and daylight-saving transitions by asset class?

### Historical retention and export (group 12)

68. How long are orders, executions, corrections, cancellations, and account
    statements retained by TradeStation outside the v3 90-day historical-order
    query window?
69. Is there a supported API, report, statement, or export channel for records
    older than 90 days? State format, correction/bust coverage, limits, and
    availability latency.
70. Does the 90-day limit use UTC calendar days, account-local trading days, or
    another boundary?
71. Can pagination tokens become invalid before the documented one-hour
    lifetime because of account changes, and is a restarted paginated query a
    consistent snapshot?

## Decisions required from the human Operator

These cannot be delegated to TradeStation or inferred from documentation.

1. **Intended scope:** name the allowed asset classes, sessions, order/group
   types, and number of logins/accounts without recording identifiers here.
2. **Least privilege:** decide whether round-one credentials, if later
   authorized, must omit `Trade`, `OptionSpreads`, and `Matrix` and permit only
   authenticated read-only evidence.
3. **OAuth posture:** choose confidential Auth Code versus PKCE, rotating
   versus non-expiring refresh tokens, reauthentication expectations, callback
   environments, and permitted-login count after Client Experience resolves
   the conflicts.
4. **Market-data acceptance:** define whether delayed data is ever acceptable
   for each workflow and which entitlement gaps fail closed.
5. **Quota topology:** define intended processes, applications, users, and
   keys, then set headroom and backpressure policy after actual aggregation is
   confirmed.
6. **Unknown status/stream behavior:** approve fail-closed handling,
   reconciliation staleness thresholds, and the disposition requiring human
   review; do not select numeric thresholds before evidence exists.
7. **Confirmation policy:** decide whether the system will require a fresh
   confirmation even if TradeStation says it is optional.
8. **Ambiguous outcomes:** approve that no blind write retry occurs and select
   the operational stop/review procedure when authoritative state cannot be
   obtained.
9. **G2 scope:** approve an exact read-only endpoint/field/evidence matrix only
   after the credential and connectivity phase is explicitly authorized.
10. **G3 scope:** approve an exact, expiring SIM experiment matrix only after
    all G3 prerequisites; SIM evidence must never be represented as LIVE
    fidelity.
11. **Retention:** set required local retention, correction history,
    recoverability, access, and deletion policy after TradeStation identifies
    available export channels.
12. **Residual unknowns:** decide which unanswered vendor questions block
    contract freeze, G1, G2, G3, and SIM certification. No unanswered item is
    closed by assumption.
13. **`offline_access` / one-shot G2 (U-17):** after Client Experience
    answers questions 72–73, decide whether a refresh-less, no-
    `offline_access` G2 profile is acceptable or whether G2 cannot proceed
    without a separately gated refresh family. Do not infer the answer.

## Operator-supplied answers (2026-10-06)

The human Operator supplied written Client Experience replies. This section
records them. It does not send a new message, create a key, or call an API.
Questions 1–73 above are not rewritten. A partial answer does not close
every sub-question.

Historical questions touched, and what stays open:

- Question 3, for the stated default personal-use configuration only:
  refresh tokens are non-rotating, non-expiring, and long-lived. Questions
  1, 2, and 4 stay open. The 30-versus-40-minute rotating interval and
  concurrent refresh were not answered.
- Questions 6, 72, and 73, in part: a generated key "could be configured,"
  and `offline_access` may be omitted. Questions 5 and 7 stay open. Returned
  `scope`, default-scope mechanics, capitalization, and dynamic omission of
  `Trade` independent of key configuration were not answered.
- Question 8, in part: the provider described Regular Web versus Native or
  Single Page and refused to choose. Permitted logins, the exact callback,
  and confidential Authorization Code plus PKCE stay open.
- Question 10, in part: the key sees accounts accessible under that login,
  and no additional entitlement is required to view that login's own
  accounts or data subscriptions. Which accounts exist was not answered.
- SIM-only key, as answered in the 2026-10-06 reply: a SIM-only API key is
  not available. The same key is used for both environments. Only the base
  URL differs. Draft PR #19 asked this as its unmerged question 75. That
  draft is not in this file and is not revived here.
- Callbacks, in part: additional callback URLs may be requested by email.
  Loopback support, a fixed versus variable port, and removal of default or
  wildcard localhost callbacks were not answered. Draft PR #19 asked a
  broader callback question as its unmerged question 77. That draft is not
  closed by this partial reply.

Verbatim replies, with footer boilerplate omitted:

1. Application type. "We are unable to choose which application type would
   work best for you, and this may require personal review of the type of
   application you wish to create, we can confirm that based on the
   application type, auth code flow may be affected. A Regular Web
   Application will require the use of the standard auth code flow, with it
   requiring the incorporation of the provided client_secret within your
   request. Should a Native or Single Page application type be used, the
   client_secret could then be negated as they can utilize auth code flow
   with PKCE, instead using a session generated secret named the Code
   Verifier within their respective requests."
2. SIM-only key. "We are unable to provide a SIM only API key, as the same
   key is used for both environments, with only the base-URL being different
   within your requests."
3. Minimum scopes. "Once a key has been generated and provided, this could
   be configured."
4. `offline_access`. "Scope offline_access may be omitted, but please be
   advised sessions will be limited to a maximum lifetime of 20 minutes
   before re-authorization will be required."
5. Refresh tokens. "With our default configuration for personal use API
   keys, refresh tokens are Non-Rotating / Non-Expiring and are long-lived.
   New Access Tokens generated by the Refresh Token have a maximum lifespan
   of 20 Minutes."
6. Callbacks. "Any additional callback URLs a client may wish to use may be
   requested by email to ClientExperience@TradeStation.com."
7. Accounts. "API key access is limited to the accounts accessible under
   your login, as the key is linked to your specific login credentials.
   Other clients may not login or have their accounts be accessible by your
   key without prior authorization. No Additional entitlements are required
   to view your own accounts or data subscriptions."
8. Rate limits. "Rate limits are enforced per Login used to access a key.
   Should you wish to increase your rate/streaming limits, additional logins
   could be provisioned for your record and could then be configured for
   your key. Each login would be able to use the same key, secret, and
   refresh token, but would have their own rate and streaming limits."

The attended probe omits `offline_access` because omission is confirmed and
the existing probe profile already excluded it. That is not acceptance of
ADR-0005. ADR-0005 stays Proposed, with a blank Decision.

### Unsent callback follow-up

Not sent. This is the only new question. It does not ask TradeStation to
choose an application type and does not reopen the answers above.

```text
Subject: Native PKCE callback form only

Hello,

Please answer only this callback question, in writing, for a Native
application that would use Authorization Code with PKCE (a Code Verifier)
and would not send a client_secret. The authorization would request only
openid and ReadAccount. It would omit offline_access. We are not asking
you to choose the application type.

1. Is an explicit loopback callback supported, for example
   http://127.0.0.1:<port>/callback or http://localhost:<port>/callback?
2. Must that port be fixed in the client registration, or may it vary on
   each authorization?
3. Can that one explicit callback be the only registered callback, with
   every default localhost callback and every wildcard callback removed?

Please do not include a client id, client secret, authorization code,
access token, refresh token, password, or account number in the reply.
```

### Unsent 2026-10-08 follow-up

Not sent. Retained as history. It is not the active draft. The 2026-10-09
consolidated follow-up below is the draft prepared after the Operator
recorded an architectural preference for Option A. Neither draft has been
sent. The native question above is not the active question unless Option A
later becomes infeasible. This 2026-10-08 draft does not ask for a secret
or an account number. Its third question asks the provider to name an
exact callback URL; the active draft does not, because no production
hostname is selected.

```text
Subject: Key type, read-only scope, and one HTTPS callback

Hello,

Please answer only these three questions, in writing, about the API key
already issued to this login. Please do not change the key unless a
separate request asks for that change.

1. Is this key configured as a Regular Web application, a Native
   application, or a Single Page application?
2. Can an authorization request for only openid and ReadAccount be
   granted with no Trade, MarketData, Matrix, OptionSpreads, or
   offline_access scope, and does the token response scope field list
   every granted scope?
3. For a confidential Regular Web client, what exact HTTPS callback URL
   can be the only registered callback, and can every other registered
   callback be removed?

Please do not include a client id, client secret, authorization code,
access token, refresh token, password, or account number in the reply.
```

### Unsent 2026-10-09 consolidated follow-up

Status: `UNSENT`. This is a draft only. It has not been sent. It does not
record a provider reply and it does not confirm `DEP-TS-002`,
`DEP-TS-003`, or `DEP-TS-004`. It covers those three dependencies. It does
not ask the native PKCE callback question. It does not name a production
callback hostname. It asks for no change to the existing key.

```text
Subject: Regular Web key type, read-only scopes, and one HTTPS callback

Hello,

This follows your written replies about our issued API key. Those replies
explained Authorization Code behavior for Regular Web, Native, and Single
Page application types; that the same key is used for both the SIM and
LIVE base URLs; that scopes can be configured after a key is issued; that
offline_access may be omitted with a session lifetime of at most 20
minutes; and that additional callback URLs can be requested by email to
Client Experience.

Our architectural preference, which is not a request to change the key, is
a cloud-hosted Regular Web confidential client using Authorization Code
with a client secret held only on the server. We are not asking you to
select a different architecture unless the issued key cannot support that
one.

Please answer only these questions, in writing. Please do not change the
existing key, its application type, its scopes, or its callback
registrations unless a later request asks for that change.

1. Is the existing issued API key configured as a Regular Web application?
   If it is not, can TradeStation convert it, or configure an equivalent
   compatible Regular Web application, without doing so now?

2. Can an authorization for this key request and be granted only these
   scopes: openid and ReadAccount? We want Trade, MarketData, Matrix,
   OptionSpreads, and offline_access excluded. Does the scope field
   returned with the token list every granted scope, so a restriction is
   visible in that response?

3. Can this key use one specifically registered HTTPS callback URL as its
   only callback, with unused callback registrations removed? We have not
   chosen the hostname. Please do not propose or register a production
   hostname for us, and please do not make the registration now. A yes or
   no on whether a single later-supplied HTTPS callback can be the sole
   registered callback is enough.

Please do not include a client id, client secret, authorization code,
access token, refresh token, password, account number, or other
identifying secret in ordinary email. If you must verify the login or the
key before answering, please describe a secure provider-approved process
for that verification instead of requesting those values here.
```
