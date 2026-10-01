# Pre-credential decision

Planning only. This note does not authorize a credential, an OAuth
session, a TradeStation call, a Supabase connection, a SIM order, or
`LIVE`. `DRY_RUN` remains the only authorized execution mode.

## Gate result

`P2_PRE_CREDENTIAL_CONTRACT_DECISION_REQUIRED`

The preferred probe is attended, bounded, read-only, no-refresh, and
no-persistent-token, with requested scopes `openid` and `ReadAccount`
only. Official pages already in the repository conflict with that
preference. `docs/AUTH_ARCHITECTURE.md` U-17 and the
`offline_access` record in `docs/P2_BROKER_RESEARCH.md` leave the Scopes
table's unqualified **required** label in conflict with omitting
`offline_access`. U-02 leaves the documented default scopes in conflict
with omitting `Trade` and `MarketData`. This note does not choose a
winner. ADR-0003 records the choice as Proposed and leaves its Decision
blank.

These tokens do not apply:

- `P2_PRE_CREDENTIAL_BASELINE_MISMATCH` — `origin/main` is
  `12e852c6d523a8fbfe2082a33887e36045ee04ae`, tree
  `99db680fb2a82d594aa4f6b1bbc0de7e47a217b8`.
- `P2_PRE_CREDENTIAL_IMPLEMENTATION_REQUIRED` — no production change is
  required to hold the probe closed.
- `P2_PRE_CREDENTIAL_NETWORK_BOUNDARY_VIOLATION` — this change did not
  request `api.tradestation.com`, `sim-api.tradestation.com`, or
  `signin.tradestation.com`.

PR #18 is merged by ancestry: GitHub records that pull request merged at
this same commit. The recorded regression, not re-run here, is 435 tests,
Phase 1 configured 218, Group 2 offline plus contracts 161, and Group 3
56 (`docs/ENGINEERING_JOURNAL.md` cites the Gate A record).

## What is proposed, and what is not selected

| Topic | Prepared position | Selection |
| --- | --- | --- |
| Authorization Code with client secret, public PKCE, or confidential PKCE | Keep `AUTH_ARCHITECTURE.md` Options A (blocked), B (candidate only after confirmation), and C (`UNKNOWN`). An attended Windows session does not convert the documented default into a selected flow. No fallback between them. | Not selected. Operator, after Client Experience names a supported type. |
| One callback | Future key, if ever requested, uses one Operator-named `https://` callback. Default localhost callbacks, extra logout URLs, and wildcard origins stay a G1 blocker, as `AUTH_ARCHITECTURE.md` already requires. | URI not named. |
| Scopes | Request `openid` and `ReadAccount` only. Omit `Trade`, `MarketData`, `offline_access`, `OptionSpreads`, `Matrix`, `profile`, and `email`. A broader grant is erased and the attempt stops. | Not a provider contract until U-17 and U-02 are answered in writing. |
| Refresh rotation 30 versus 40 | Unresolved. The no-refresh profile does not use the interval. Do not prefer either page. | `PROVIDER_CONFIRMATION_REQUIRED` before any refresh-token gate. |
| Default-scope conflict | Unresolved three ways (U-02). | `PROVIDER_CONFIRMATION_REQUIRED`. |
| Key incapable of LIVE | Not stated by the recorded pages. Documented switch is the base URL. Audience in the auth pages is the live API audience. | `UNKNOWN` / `PROVIDER_CONFIRMATION_REQUIRED`. Until a written denial exists, any future key is `POTENTIALLY_LIVE_CAPABLE` and G1 stays closed. |
| Bootstrap custody | Alternatives below. None provisioned. | Not selected. |
| Memory-only tokens | Authorization code and access token stay in the attended process and are erased at stop. They are not database columns (`docs/TOKEN_STORE.md`). An unexpected refresh token is erased, and the attempt stops. | Local rule proposal. It does not open a probe. |
| Persistent encryption | Deferred until a separate refresh-token gate. ADR-0002 item 3 stays open. The no-persistent-token profile does not need a data key. Deferral does not close `TOKEN_ENCRYPTION_CUSTODY_READY`. | Not selected. |
| Two-step account bootstrap | Step 1: the Operator records an expected SIM inventory outside Git, chat, and logs. Step 2: a later accounts call compares in memory and does not continue into balances. | Not performed. |
| Account-id logging | Do not log raw account ids. Do not substitute an unkeyed hash of a short id. Logs receive reason codes and monitoring codes only (`AUTH_ARCHITECTURE.md` redaction; `P2_MONITORING_TAXONOMY.md` `S-BROKER`). | Local rule proposal. |
| Rate-limit headers | Record presence of the `X-RateLimit-*` family. Do not require `X-Concurrency-*` on non-stream GETs; finding 35 ties that family to streams. On HTTP 429, do not retry; stop. Do not exhaust quota. | Observation policy proposal. Quota identity stays group 10, unresolved. |

## Custody alternatives

None selected. Production must not depend on Cursor. Rejected holders:
Cursor Dashboard injection (`AUTH_ARCHITECTURE.md` E15), a repository
file, `.env`, chat, logs, and images.

For a later attended Windows probe only:

1. The Operator's OS credential store, read into the attended process,
   with a presence check that prints `SET` or `UNSET` and never the value.
   A 2026-10-01 planning note named the Python `keyring` library as a
   candidate for that read. This repository does not accept that library.
   `docs/SIM_CERTIFICATION.md` still requires an approved secret manager
   before issued credentials. This alternative does not meet that bar.
2. A dedicated secret manager named at a later gate. AWS and Supabase are
   not selected. ADR-0002 rejects binding the TokenStore to those APIs.

The client id, and a client secret only if a later accepted flow is
confidential Authorization Code, are the only bootstrap materials. The
authorization code, access token, and refresh token do not go in that
holder under the memory-only proposal. A KEK is out of scope until a
refresh token is separately authorized.

## Probe stages

These stages are not C1/U-10. C1/U-10 remains the resolved TokenStore
contract. The stages below are closed.

1. **C1 setup.** Operator names the flow, the one callback, the scope
   string, the holder, and the expected account inventory. Client
   Experience answers are on file. No broker URL is called.
2. **C2 accounts only.** After a separate authorization: one
   authorization-code exchange, then `GET /v3/brokerage/accounts` on the
   SIM host only. Stop before balances.
3. **C3 balances, positions, and orders.** After C2 is accepted for that
   exact run: one balances GET, one positions GET, and one unpaginated
   orders GET for the accepted ids. No historical orders. No `nextToken`.
   No stream.

Stop on the first failure. Do not continue to see what else works.

## Future allowlist and denylist

Not authorized. Not implemented. `src/swingtrade/group3_auth/readonly.py`
joins a well-formed `/v3` GET onto the SIM base and keeps
`connect_allowed` false. That generic join is not this allowlist.

Host construction is from this table only. The caller does not supply a
URL. Resource host is `sim-api.tradestation.com`, port 443, scheme
`https`, path canonical. `https://api.tradestation.com` is denied on every
port and path.

| Stage | Method | Canonical target | Purpose | Economic mutation |
| --- | --- | --- | --- | --- |
| C2 | `POST` | `https://signin.tradestation.com/oauth/token` | One authorization-code exchange. No refresh grant. | No. Token issue, not order entry. |
| C2 | `GET` | `/v3/brokerage/accounts` | Enumerate accounts. | No. |
| C3 | `GET` | `/v3/brokerage/accounts/{accounts}/balances` | Read balances for ids accepted at C2. Batch at most 10. | No. |
| C3 | `GET` | `/v3/brokerage/accounts/{accounts}/positions` | Read positions for that list. | No. |
| C3 | `GET` | `/v3/brokerage/accounts/{accounts}/orders` | Today's orders and open orders. One unpaginated GET. | No. Fetch, not placement. |

The browser authorization redirect to
`https://signin.tradestation.com/authorize` is an attended browser step,
not an application-egress row. Application egress for a later authorized
run would be the token `POST` and the resource GETs above.

Required scope for every row: `openid` and `ReadAccount`. Expected
monitoring: `MON-AUT-001` for auth denial or scope mismatch;
`MON-DTO-001` for a body that does not match the expected top-level
shape; `MON-DTO-003` when raw order status is held `UNKNOWN`;
`MON-RAT-001` on HTTP 429; `MON-RAT-003` when the `X-RateLimit-*` family
is absent or inconsistent; `MON-BRK-001` when the host is not the
authorized SIM host. Codes are the taxonomy in
`docs/P2_MONITORING_TAXONOMY.md`. They are not implemented here.

Quarantine and stop: wrong token type, `expires_in` missing or above
1200, scope missing or broader than requested, unexpected refresh token,
any host other than the SIM resource host, any method outside this table,
HTTP 401 or 403, a non-empty batch `Errors` array, an account id outside
the pre-declared inventory, or a clock that is unknown. The 1200-second
ceiling is the documented example lifetime in `BROKER_CONTRACT.md`
finding 6 (20 minutes), not a new measurement.

### Denied

| Denied call | Why |
| --- | --- |
| `POST /v3/orderexecution/orders` | Places an order. |
| `POST /v3/orderexecution/orderconfirm` | Order-execution preview. Excluded even though it does not place. |
| `PUT /v3/orderexecution/orders/{orderID}` | Replace. |
| `DELETE /v3/orderexecution/orders/{orderID}` | Cancel. |
| `POST /v3/orderexecution/ordergroups` | Group place. |
| `POST /v3/orderexecution/ordergroupconfirm` | Group confirm. |
| OSO on a place or confirm body | Already denied by those methods. |
| `GET /v3/orderexecution/activationtriggers` | Excluded so the probe is not confused with arming an order. |
| Refresh grant, revoke, logout | Not part of the no-refresh profile. Revoke request shape stays ambiguous (auth U-06). |
| Beginning-of-day balances, streams, quotes, symbol details, routes | Documented reads, and outside this probe. |
| Any caller-supplied URL, host, or path | Construction is from the table only. |
| `https://api.tradestation.com` on every port and path | LIVE. |
| Generic `POST` | The only `POST` is the exact token URL. |

## Readiness

`YES` means the prerequisite is specified for a later Operator decision.
`YES` does not open the gate.

| Gate | Value | Owner of each NO |
| --- | --- | --- |
| `TRADESTATION_API_ACCESS_REQUEST_READY` | YES | The draft message is in `docs/TRADESTATION_CLIENT_EXPERIENCE_QUESTIONS.md`. YES does not send it. |
| `BOOTSTRAP_SECRET_CUSTODY_READY` | NO | Human Operator. No holder is accepted. |
| `TOKEN_ENCRYPTION_CUSTODY_READY` | NO | Human Operator. ADR-0002 item 3. Deferred until a refresh-token gate. |
| `TRADESTATION_CREDENTIAL_GATE_READY` | NO | Human Operator, using written Client Experience answers. U-17, U-02, flow, callback, and LIVE denial are open. |
| `AUTHENTICATED_READONLY_PROBE_READY` | NO | Human Operator. Blocked by the credential gate and by `P2_PRE_CREDENTIAL_CONTRACT_DECISION_REQUIRED`. |
| `READONLY_PROBE_DATABASE_READY` | YES | The no-persistent-token profile writes no broker token. YES does not authorize a connection or a schema change. |
| `AUTONOMOUS_SIM_DATABASE_READY` | NO | Human Operator. SIM host unselected. Supabase is **NOT_ACCEPTED**. Local PostgreSQL is not the SIM host. |
| `PROBE_C1_SETUP` | NO | Human Operator. Client Experience answers are an input, not a substitute. |
| `PROBE_C2_ACCOUNTS_ONLY` | NO | Human Operator. Blocked by C1. |
| `PROBE_C3_BALANCES_POSITIONS_ORDERS` | NO | Human Operator. Blocked by C2. |

## Facts, inferences, and open questions

**Facts.** The baseline commit and tree match the values above. The
scope, refresh-interval, and default-scope conflicts are already recorded
repository evidence. ADR-0002 does not close custody. This change adds no
application code.

**Inferences.** A future token should be treated as
`POTENTIALLY_LIVE_CAPABLE` until Client Experience writes that the exact
key cannot use the LIVE host. `readonly.py` is not the allowlist above.
These are not broker guarantees.

**Assumptions.** None adopted. This note does not assume that omitting
`offline_access` succeeds, that 30 or 40 minutes is correct, or that one
bearer token is rejected by the LIVE host.

**Open questions.** U-02, U-04 (LIVE restriction), U-06, U-07, U-08,
U-16, and U-17. The callback value. The login list. The bootstrap holder.
The KEK holder. Organizational retention.

The unsent Operator message and questions 74–77 are in
`docs/TRADESTATION_CLIENT_EXPERIENCE_QUESTIONS.md`. Do not send them from
this repository.
