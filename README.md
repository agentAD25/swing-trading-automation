# Swing Trading Automation

This repository is governed for incremental development of a swing-trading
automation system. Phase 1A establishes structure and safety boundaries only;
it does not contain a trading foundation or validated broker, market-data, or
strategy decisions.

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
- `tests/` — future automated verification (currently intentionally empty)

Start with [agent authority](docs/AGENT_AUTHORITY.md) and
[current state](docs/CURRENT_STATE.md).
