# Configuration

This directory is reserved for future non-secret configuration contracts.
Phase 1A defines no runtime configuration.

Do not commit credentials, tokens, account identifiers, or secret-bearing
files. Any future execution-mode configuration must default to `DRY_RUN` and
reject missing, unknown, TradeStation `SIM`, or `LIVE` values. Configuration
cannot grant a denied capability; future broker connectivity requires every
separate governance and promotion gate.

## P2-0 proposed environment naming (documentation only)

`docs/DB_DEPLOYMENT.md` §7.1 proposes one opaque secret-store **reference**
per future environment. These names are not required runtime variables in
the current `DRY_RUN` foundation. Do not put URLs, passwords, hosts, or
other secret values in the repository under these names.

| Environment | Proposed sole source name | P2-0 status |
| --- | --- | --- |
| Local `DRY_RUN` (authorized) | `SWINGTRADE_DATABASE_URL` in `.env.example` | Existing local docker-compose PostgreSQL only |
| `DEV` | `SWINGTRADE_DEV_DATABASE_URL_REF` | Unconfigured; documentation name only |
| `TEST` | `SWINGTRADE_TEST_DATABASE_URL_REF` | Unconfigured; documentation name only |
| `SIM` | `SWINGTRADE_SIM_DATABASE_URL_REF` | Unconfigured and unauthorized |
| `LIVE` | `SWINGTRADE_LIVE_DATABASE_URL_REF` | **Must remain absent**; `LIVE` is unauthorized |

`*_REF` means an opaque pointer to an approved secret store decided later
by the P2-B architecture and an Operator gate. It is not a connection
string. Generic `DATABASE_URL`, cross-environment fallback, inheritance,
and a configured `LIVE` source are rejected by the proposed contract.

These `*_REF` names are bootstrap references, not runtime token state.
The proposed runtime contract is `docs/TOKEN_STORE.md`: production must
not depend on Cursor, and mutable OAuth token state is a provider-neutral
PostgreSQL TokenStore. The database-URL reference product is not selected
here. This file does not accept that contract or choose a database host.
