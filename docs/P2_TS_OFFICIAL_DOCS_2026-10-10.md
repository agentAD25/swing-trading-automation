# TradeStation official documentation research — 2026-10-10

Lane 2 comparison of current published TradeStation documentation with the
Option A preference and the offline contracts on draft PR #22. This note
does not replace the 2026-10-06 Client Experience quotations or the
2026-10-08 intake. The Operator confirmed on 2026-10-10 that the October
2026 correspondence is the final currently available direct provider
response. That confirmation does not close a key-specific dependency.

No API key, client secret, token, or account identifier was read. No
TradeStation request was authenticated. `DRY_RUN` remains the only
authorized execution mode. ADR-0005 stays Proposed.

## Evidence labels

- **PROVIDER_WRITTEN** — the recorded Client Experience correspondence.
- **OFFICIAL_DOCUMENTATION** — a current page on `api.tradestation.com/docs`,
  or the OpenAPI 3.0.3 document embedded in that site's specification
  bundle, accessed 2026-10-10.
- **REPOSITORY_VERIFIED** — behavior read from this branch's source.
- **DESIGN_INFERENCE** — a conclusion drawn from those sources and not
  directly stated.
- **KEY_SPECIFIC_UNVERIFIED** — cannot be established for the issued key
  from public documentation.
- **SECONDARY** — a page the official FAQ links for legacy OAuth2 keys.
  It is not authority for the current Auth0 procedures.

Published defaults are not key-specific confirmation. Where a written
provider sentence and a public page disagree, both stay on the record.

## Source inventory

Accessed 2026-10-10 unless noted.

| ID | Title | URL | Use |
| --- | --- | --- | --- |
| D1 | API docs home | https://api.tradestation.com/docs/ | v3 base URL `https://api.tradestation.com/v3` |
| D2 | Authentication overview | https://api.tradestation.com/docs/fundamentals/authentication/auth-overview/ | Default Regular Web flow, refresh, scopes, callbacks, key actions |
| D3 | Auth Code flow | https://api.tradestation.com/docs/fundamentals/authentication/auth-code/ | Confidential-client parameters and token response example |
| D4 | Auth Code with PKCE | https://api.tradestation.com/docs/fundamentals/authentication/auth-pkce/ | Public-client alternative; not the default |
| D5 | Scopes | https://api.tradestation.com/docs/fundamentals/authentication/scopes/ | Scope names and default/required labels |
| D6 | Refresh tokens | https://api.tradestation.com/docs/fundamentals/authentication/refresh-tokens/ | Lifetime, optional rotation, revocation |
| D7 | FAQ | https://api.tradestation.com/docs/faq/ | Auth0 versus legacy key-format rules; configuration changes |
| D8 | SIM vs LIVE | https://api.tradestation.com/docs/fundamentals/sim-vs-live/ | SIM base URL and shared-interface warning |
| D9 | Rate limiting | https://api.tradestation.com/docs/fundamentals/rate-limiting/rate-limiting-overview/ | Quotas, headers, HTTP 429 |
| D10 | HTTP requests | https://api.tradestation.com/docs/fundamentals/http-requests/ | HTTPS hosts and null-or-omitted fields |
| D11 | Specification bundle | https://api.tradestation.com/docs/specification/ | OpenAPI 3.0.3 embedded in `assets/js/42059736.54db3d8f.js` |
| S1 | Legacy swagger | https://tradestation.github.io/api-docs/swagger.json | SECONDARY. Linked from D7 for OAuth2-format keys |

D2, D3, and D4 say their procedures are for Auth0 API keys and point to D7
for formats. S1 was fetched because D7 links it. S1 is Swagger 2.0, host
`api.tradestation.com`, base path described as `/v2`. It is not the v3
Auth0 contract.

## DEP-TS-002 — issued key application type

Stays **OPEN**. Classification: `KEY_SPECIFIC_UNVERIFIED`.

OFFICIAL_DOCUMENTATION from D7, section "What version of API key do I have?":

- Auth0 keys are described as mixed uppercase and lowercase characters
  without dashes.
- Legacy OAuth2 keys are described as all-capitals with multiple dashes.
- D7 shows illustrative examples. Those strings are not recorded here and
  were not compared with any local secret.

That format test separates Auth0 documentation from the legacy OAuth2
documentation. It does not identify Regular Web, Native, or SPA.

OFFICIAL_DOCUMENTATION from D2, "Default API Key Configuration":

- Unless Client Experience was already given different requirements, the
  published default application type is Regular Web, using standard
  Authorization Code.
- PKCE for a SPA or Native app is a requested change. After that change,
  the PKCE page applies.
- D7 says configuration changes are requested by email to Client
  Experience. It does not promise that every existing key can be converted.

OFFICIAL_DOCUMENTATION endpoints:

- Auth0 authorization: `https://signin.tradestation.com/authorize` (D3, D4).
- Auth0 token: `https://signin.tradestation.com/oauth/token` (D3, D6).
- Standard Authorization Code requires `client_secret` on the token POST
  (D3). PKCE sends `code_verifier` and the PKCE page does not list
  `client_secret` on that exchange (D4). D6 says `client_secret` is
  required for standard Auth Code refresh and not required for PKCE refresh.
- SECONDARY S1 uses `https://api.tradestation.com/v2/security/authorize`
  for both its access-code authorization URL and its token URL. Its scopes
  are lowercase `marketdata`, `readaccount`, and `trade`. It does not
  document `openid`, `offline_access`, `Matrix`, `OptionSpreads`, or
  `profile`.

No page describes a non-secret query that returns the application type.
Seeing the key string would be required even to apply the D7 format test.
This research did not do that.

PROVIDER_WRITTEN answers use Regular Web, Native, SPA, `client_secret`,
and PKCE language. That vocabulary matches D2–D4. DESIGN_INFERENCE: the
correspondence is about the Auth0 model rather than S1. That inference
does not prove the issued key's format or that the key is Regular Web.
The Operator preference for Option A is not provider confirmation.

## DEP-TS-003 — least-privilege scopes

Stays **OPEN**. The desired attended set remains exactly `openid` and
`ReadAccount`. `scopes.py` still rejects any other set, including `Trade`,
`MarketData`, `Matrix`, `OptionSpreads`, `offline_access`, `profile`, and
`email`.

OFFICIAL_DOCUMENTATION, and the conflicts that remain:

| Topic | What the pages say | Label |
| --- | --- | --- |
| D2 default API scopes | `MarketData`, `ReadAccount`, `Trade`. Additional scopes are requested from Client Experience | OFFICIAL_DOCUMENTATION |
| D5 prose | Keys are configured by default with `MarketData`, `ReadAccount`, `Trade`, and `OptionSpreads` | OFFICIAL_DOCUMENTATION |
| D5 table | Those four plus `Matrix` are marked Default | OFFICIAL_DOCUMENTATION |
| D5 other scopes | `openid` required. `offline_access` required, unqualified. `profile` and `email` optional ID-token scopes | OFFICIAL_DOCUMENTATION |
| D3 | `openid` always required. `offline_access` required for refresh tokens. Scope text is case sensitive. Example token JSON includes a `scope` string | OFFICIAL_DOCUMENTATION |
| PROVIDER_WRITTEN | `offline_access` may be omitted; the session is then at most 20 minutes | PROVIDER_WRITTEN |

The D2/D5 default-scope disagreement recorded on 2026-09-26 is still on
the pages. The unqualified D5 "required" label for `offline_access` still
disagrees with D3's "required for refresh tokens" wording and with the
written provider sentence. The written sentence controls the attended
profile. It does not prove this key will grant only `openid ReadAccount`.

D3 shows a token response field named `scope`. D6's refresh example shows
a different, shorter `scope` string. Neither page states that the field
is a complete list of granted scopes, or that a requested subset is what
the key will allow. Requesting a subset is possible in the sense that the
client supplies the `scope` parameter. Grant behavior for a subset is
`KEY_SPECIFIC_UNVERIFIED`.

D5 defines `ReadAccount` as access to view brokerage accounts of the
current user. D11 does not attach `ReadAccount`, `Trade`, or any other
scope to individual operations. Its only security scheme is an HTTP
bearer token. DESIGN_INFERENCE that `ReadAccount` alone authorizes
balances, positions, or order reads is not a documented endpoint contract.
A token cannot be confirmed read-only from public documentation. The
local rule remains fail-closed on unexpected scopes.

D2 discusses adding scopes. D7 discusses configuration changes through
Client Experience. A specific scope-removal control for this key is
`KEY_SPECIFIC_UNVERIFIED`.

No-refresh attended sessions: D3 says access tokens expire 20 minutes
after issue, and D6 repeats the 20-minute lifetime. A session without
refresh is the mechanical result of a grant that omits `offline_access`,
if that grant succeeds. Success without `offline_access` is the retained
conflict above, not a new documentation proof.

## DEP-TS-004 — callback configuration

Stays **OPEN** for the issued key's registrations. A single HTTPS
callback is compatible with the documented Regular Web flow. No hostname
is selected.

OFFICIAL_DOCUMENTATION from D2 and D3:

- Allowed Callback URLs are the required URI setting. The server calls
  back only to URLs in that list. `redirect_uri` must be one of them.
- Multiple callback URLs may be configured, including separate environment
  URLs.
- Deployed applications are told to specify `https://`. Except for custom
  URI schemes for native clients, callbacks should use `https://`.
- The published default list is localhost HTTP ports. This note does not
  copy that list into a deployment choice.
- Logout URL text allows a subdomain wildcard and says query and hash are
  ignored for logout URLs. The callback paragraphs do not grant that
  exception. Exact string match beyond "must be in the configured list"
  is not further specified.
- Add, update, or delete of callback, logout, origin, and login URIs is
  requested through Client Experience.

D3 and D4 carry the Auth0-key banner. S1 does not document those callback
lists. Callback handling for a legacy OAuth2 key is not established by
D2. Which family this key belongs to remains `KEY_SPECIFIC_UNVERIFIED`.

Option A, one registered HTTPS callback on a cloud backend, fits the
documented confidential-client redirect. Whether this key already has one
callback, and whether its default localhost entries can be removed, is
`KEY_SPECIFIC_UNVERIFIED`. Nothing was registered.

## Token lifecycle

| Item | Record | Label |
| --- | --- | --- |
| Authorization | Browser redirect to `https://signin.tradestation.com/authorize` with `response_type=code`, `client_id`, `audience=https://api.tradestation.com`, `redirect_uri`, and `scope` | OFFICIAL_DOCUMENTATION D3 |
| Confidential secret | Standard token exchange requires `client_secret`. PKCE uses `code_verifier` instead | OFFICIAL_DOCUMENTATION D3, D4 |
| Token endpoint | `POST https://signin.tradestation.com/oauth/token`, form-urlencoded, `grant_type=authorization_code` | OFFICIAL_DOCUMENTATION D3 |
| Access expiry | 20 minutes. Example `expires_in` is 1200 | OFFICIAL_DOCUMENTATION D3, D6 |
| `offline_access` | Required for refresh tokens on D3 and D6. Unqualified required on D5. Omission allowed by the written provider reply, with a 20-minute session | Conflict retained |
| Refresh grant | `grant_type=refresh_token` to the same token URL. Rotating configuration returns a new refresh token | OFFICIAL_DOCUMENTATION D6 |
| Default refresh lifetime | Non-expiring / valid indefinitely | OFFICIAL_DOCUMENTATION D2 and D6, and PROVIDER_WRITTEN for default personal-use keys |
| Optional rotation | D2 says expire and rotate every 40 minutes. D6 says every 30 minutes, with a 24-hour absolute lifetime | OFFICIAL_DOCUMENTATION conflict. Neither interval is inferred for this key |
| Revocation | `POST https://signin.tradestation.com/oauth/revoke` revokes all refresh tokens for the API key. D6's parameter table names `refresh_token`; its example body uses JSON field `token` | OFFICIAL_DOCUMENTATION, encoding unresolved |
| Secret rotation and disable | D2: rotating the client secret does not invalidate existing non-expiring refresh tokens. Disabling and re-enabling a key can make those refresh tokens usable again | OFFICIAL_DOCUMENTATION, consistent with PROVIDER_WRITTEN |
| `state` | Recommended opaque value echoed on the redirect to mitigate CSRF. Not labeled required | OFFICIAL_DOCUMENTATION D3 |
| Redirect | `redirect_uri` must be a configured callback. Declined consent returns `error=access_denied` | OFFICIAL_DOCUMENTATION D3 |
| Reauthorization | Local attended session accepts only `expires_in` 1200, rejects a refresh token, and returns `REAUTHORIZATION_REQUIRED` after restart | REPOSITORY_VERIFIED `session.py` |

Future unattended refresh remains design-only. Custody and single-flight
refresh synchronization are requirements in `docs/AUTH_ARCHITECTURE.md`.
Profile B raises `PROFILE_B_NOT_AUTHORIZED`. No refresh token was created.

## SIM and LIVE hosts

OFFICIAL_DOCUMENTATION:

- LIVE v3 base: `https://api.tradestation.com/v3` (D1).
- SIM v3 base: `https://sim-api.tradestation.com/v3` (D8).
- D8 says the simulator is identical except fake accounts, fake money, and
  simulated instant fills, and warns that TradeStation is not liable for
  applications that switch environments.
- D11 `servers` contains only `https://api.tradestation.com`. The SIM host
  is not in that array. SIM compatibility of each path is the D8
  same-interface statement, not a second OpenAPI server entry.
- PROVIDER_WRITTEN: the same key is used for both environments and the
  base URL differs. The credential does not enforce SIM isolation.

REPOSITORY_VERIFIED `boundary.py`: the only boot posture is `DRY_RUN`.
LIVE host forms are denied. SIM URLs are classified and then denied with
`SIM_CONNECT_DENIED`. Auth URLs are denied with
`AUTH_ENDPOINT_CONNECT_DENIED` before write-method handling. Redirects
are `REDIRECT_DENIED`. Header and configured hosts are
`HOST_OVERRIDE_DENIED`. Paths containing `orderexecution` or ending in
`/orderconfirm`, and non-GET write methods, are `ORDER_PLACEMENT_DENIED`.
A read path such as `/v3/brokerage/accounts` on the SIM host is still
denied. `connect_allowed` stays false.

## Read-only brokerage contracts

Source: D11, accessed 2026-10-10. Account-number examples in parameter
text are not copied. Per-operation OAuth scopes are not declared.

| Need | Method and path | Parameters | Response | Pagination | Rate category | Errors |
| --- | --- | --- | --- | --- | --- | --- |
| Account discovery | `GET /v3/brokerage/accounts` | None | `Accounts[]` of `Account` | Not described | Name "Accounts", 320 per 5 minutes. The page's narrative uses this path with that quota | 400, 401, 403, 404, 429, 503, 504 as `ErrorResponse` (`Error`, `Message`) |
| Balances | `GET /v3/brokerage/accounts/{accounts}/balances` | Path `accounts`, 1 to 25 comma-separated IDs. Valid for Cash, Margin, Futures, and DVP | `Balances[]` plus `Errors[]` | Not described | Name "Balances", 320 per 5 minutes. Path mapping is by category name | Same status set |
| Positions | `GET /v3/brokerage/accounts/{accounts}/positions` | Path `accounts`. Optional query `symbol` | `Positions[]` using `PositionResponse`, plus `Errors[]` | Not described | Name "Positions", 320 per 5 minutes. Path mapping is by category name | Same status set |
| Open and today's orders | `GET /v3/brokerage/accounts/{accounts}/orders` | Path `accounts`. Optional `status` (`Open`, `Filled`, `Cancelled` or `Canceled`, `Rejected`), `symbol`, `pageSize`, `nextToken` | `Orders[]`, `Errors[]`, `NextToken` | `pageSize` paginates; otherwise at most 600. `nextToken` lifetime 1 hour | Name "Order Details", 320 per 5 minutes. Path mapping is by category name | Same status set |
| Order status by id | `GET /v3/brokerage/accounts/{accounts}/orders/{orderIds}` | Path `accounts` and `orderIds` (1 to 50) | `Orders[]` and `Errors[]`. Error objects add `OrderID` | Not described on this operation | Same category inference | Same status set |
| Historical orders | `GET /v3/brokerage/accounts/{accounts}/historicalorders` | Required query `since`, limited to 730 days. Optional status, symbol, page size, next token | Historical order collection plus `NextToken` | Same pagination description | Not separately named | Same status set |

`Account` fields match the parser allowlist, including nested
`AccountDetail`. `Balance`, `BalanceDetail`, and `CurrencyDetail` match.
`PositionResponse` matches the positions allowlist. A different component
named `Position` includes `Deleted` and is not the REST positions item.
`Order` matches the parser except `Spread`, which D11 types as a string,
"the spread type for an option order." Components named `Spread` and
`SpreadLeg` are separate objects and are not the type of that order field.

Stream paths exist for orders and positions. They are not part of the
initial REST read profile. D9 assigns them concurrency limits.

SIM use of these paths is the D8 same-interface statement plus the SIM
base URL. It is not a tested SIM call.

## Rate limits and errors

OFFICIAL_DOCUMENTATION D9:

- Quota is allocated per API key and applied per user. Exceeding it
  returns HTTP 429.
- Default intervals are rolling. Accounts, Order Details, Balances, and
  Positions are each 320 requests per 5 minutes.
- Request headers: `X-RateLimit-Limit`, `X-RateLimit-Period`,
  `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `X-RateLimit-Resource`.
- The 429 example body is `Error` `TooManyRequests` and `Message`
  `Rate quota exceeded`. The example then retries after
  `X-RateLimit-Reset`. The page also recommends exponential backoff.
- Client Experience can adjust quotas. A default table is not this key's
  allocation. `KEY_SPECIFIC_UNVERIFIED`.

PROVIDER_WRITTEN says limits are enforced per login, and that additional
logins can carry separate limits while sharing the key. D9 says per user
on a key's quota. The words are not identical. Both remain. This research
does not treat them as proven to be the same counter.

REPOSITORY_VERIFIED `throttle.py`: HTTP 429 stops that synthetic login,
`retry_budget` is 0, and `retry_permitted` stays false. Unknown
`X-RateLimit-*` names other than Limit, Remaining, and Reset are ignored
rather than applied. The official retry example is not implemented. That
is the repository's fail-closed choice. It is not changed here.

## Documentation versus implementation

| Finding | Class | Safety |
| --- | --- | --- |
| DRY_RUN boot, LIVE denial, SIM denial, auth denial, redirect denial, host-override denial, order-placement denial | ALIGNED | Holds. No relaxation |
| Exact `openid ReadAccount` request and granted-scope rejection | ALIGNED | Holds. Does not prove the issued key |
| 1,200-second attended session, no refresh, profile B refused | ALIGNED with the 20-minute access-token fact and the attended profile | Holds |
| Account, balance, and position REST property names | ALIGNED with D11 | Parser still does not connect |
| Order `Spread` documented as a string; parser comment calls it an unpinned object and rejects it as `UNDOCUMENTED_FIELD` | IMPLEMENTATION_GAP | Fail-closed. A later remediation may accept a string `Spread` and correct the comment. Not done here |
| Null blank fields: D10 says null or omitted. The parser accepts omission and rejects null | IMPLEMENTATION_GAP | Fail-closed `MALFORMED_RESPONSE`. Proposed later fixture change only |
| HTTP 400 and 404 are documented and classified `HTTP_UNEXPECTED` | IMPLEMENTATION_GAP | Still denied. Distinct reason codes can wait |
| Order-by-id error object includes `OrderID`, which the shared error allowlist rejects | IMPLEMENTATION_GAP | Fail-closed if that lookup is later parsed. List-order `OrderError` matches |
| Historical orders are not a `ReadKind` | DOCUMENTATION_GAP for the initial profile | Initial profile needs today's and open orders, which are the non-historical GET |
| D9 retry example versus stop-on-429 | ALIGNED with repository policy | Do not add retries from the example |
| D2 40-minute versus D6 30-minute rotation | PROVIDER_CONFLICT inside official docs | Neither interval applies to this key by inference |
| D5 versus provider omission of `offline_access` | PROVIDER_CONFLICT | Written reply controls the attended profile; grant result stays unverified |
| D11 `servers` lists only the LIVE origin | DOCUMENTATION_GAP for SIM | SIM host remains denied in code |
| Issued key type, granted scopes, and registered callbacks | KEY_SPECIFIC_UNVERIFIED | Dependencies stay open |

No `src/` or `tests/` change is made. The gaps are fail-closed. A separate
remediation gate would be required before changing the parser, and that
gate would need its own exact-tree verification. This research does not
open that gate.

## ADR-0005 and dependencies

ADR-0005 status remains **Proposed**. The Decision section remains blank.
`OPERATOR_PREFERENCE_OPTION_A_REGULAR_WEB_CONFIDENTIAL_CLIENT` remains an
Operator preference, not proof of the issued key.

| ID | After this research |
| --- | --- |
| `DEP-TS-001` | Still `NOT_CLOSED_BY_PROVIDER`. Native PKCE callback text is still absent. Recommended narrative remains `SUPERSEDED_BY_OPTION_A_PENDING_ARCHITECTURE_ACCEPTANCE` only after architectural acceptance. Registry state stays `OPEN` |
| `DEP-TS-002` | `OPEN`. Format rules and the Regular Web default are documented. This key's format and application type are not |
| `DEP-TS-003` | `OPEN`. Desired scopes and the local fail-closed check are unchanged. The grant is not confirmed |
| `DEP-TS-004` | `OPEN`. One HTTPS callback is compatible with documented Regular Web. This key's registrations are not confirmed. No hostname is chosen |

Lane 1 owns the registry. `docs/LANE2_OFFICIAL_DOCS_HANDOFF.md` asks Lane 1
not to close these IDs from this research. No new dependency ID is created.

## Remaining key-specific uncertainties

- Whether the issued key is Auth0-format or legacy OAuth2-format.
- Whether it is Regular Web, Native, or SPA.
- Whether a subset request of `openid ReadAccount` is granted, and whether
  the token `scope` field lists the whole grant.
- Whether `ReadAccount` alone authorizes balances, positions, and order
  reads on this key.
- Which callback URLs are registered, and whether unused ones can be
  removed.
- Whether this key uses the non-expiring refresh default or either
  optional rotation interval.
- This key's actual rate-limit allocation versus the published defaults.
- The wire encoding of refresh revocation.

## Next safe action

Public documentation research for this pass is recorded. The next safe
action is to leave `DEP-TS-002`, `DEP-TS-003`, and `DEP-TS-004` open and
to keep the runtime on `DRY_RUN`. The unsent 2026-10-09 Client Experience
draft stays unsent. Credential onboarding, OAuth, SIM, LIVE, and orders
remain unauthorized. Parser remediation is a separate later gate, not an
automatic follow-on.
