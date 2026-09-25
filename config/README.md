# Configuration

This directory is reserved for future non-secret configuration contracts.
Phase 1A defines no runtime configuration.

Do not commit credentials, tokens, account identifiers, or secret-bearing
files. Any future execution-mode configuration must default to `DRY_RUN` and
reject missing, unknown, TradeStation `SIM`, or `LIVE` values. Configuration
cannot grant a denied capability; future broker connectivity requires every
separate governance and promotion gate.
