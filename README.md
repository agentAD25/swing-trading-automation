# Swing Trading Automation

This repository is governed for incremental development of a swing-trading
automation system. Phase 1A established governance; Phases 1B–1D draft,
reconcile, and correct a broker-neutral foundation design and deterministic
synthetic fixture. The repository does not contain production code or accepted
broker, market-data, strategy, or risk decisions.

## Safety status

- `DRY_RUN` is the only authorized mode: local, deterministic, and non-network.
- TradeStation `SIM`, broker activity, credentials, Phase 2, and `LIVE` are
  unauthorized.
- Safety prohibitions are non-overridable; future capability requires all
  governing gates, not an instruction or ADR alone.
- No current artifact is investment advice or evidence of strategy efficacy.

## Repository map

- `.cursor/rules/` — mandatory project-wide agent rules
- `.cursor/agents/` — scoped agent role definitions
- `config/` — future non-secret configuration contracts
- `docs/` — authority, decisions, state, journal, and research outputs
- `src/` — future implementation (currently intentionally empty)
- `tests/` — deterministic fixtures and future automated verification

Start with [agent authority](docs/AGENT_AUTHORITY.md) and
[current state](docs/CURRENT_STATE.md). The proposed design begins at
[architecture](docs/ARCHITECTURE.md); decisions and unknowns are indexed in
[the Phase 1B register](docs/DECISIONS.md).
