# Swing Trading Automation

This repository is governed for incremental development of a swing-trading
automation system. Phase 1A established governance; Phase 1B drafts a
broker-neutral foundation design and deterministic synthetic fixture. It does
not contain production code or validated broker, market-data, strategy, or risk
decisions.

## Safety status

- `SIM` is the only authorized execution mode.
- `LIVE` order routing, live credentials, and live-capital deployment are
  unauthorized until a later ADR explicitly approves them.
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
