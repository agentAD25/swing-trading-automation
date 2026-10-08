# Workstream Handoff Template

Copy this structure for every lane handoff to Lane 1 or to another lane.
Incomplete handoffs are non-authoritative.

## Identity

- Lane identifier:
- Workstream name:
- Agent role:
- Branch:
- PR number (if any):
- Exact HEAD SHA:
- Exact tree SHA:
- Canonical main baseline SHA/tree used at branch start:
- Handoff date (UTC):

## Objective and scope

- Current objective:
- In-scope paths:
- Explicitly out-of-scope paths:
- Authorization cited from `docs/CURRENT_STATE.md`:

## State claim

- Requested `WORKSTREAM_STATUS` state:
- Certification status claim:
- Integration eligibility claim (`eligible` / `not_eligible` + reason):

## Evidence

- Commands run:
- Outcomes (pass/fail/skip counts):
- Skipped tests and exact skip reasons:
- Independent verification identity (must differ from implementer):
- Artifact paths:

## Dependencies

For each dependency touched, use stable IDs from
`docs/WORKSTREAM_DEPENDENCIES.md`:

| Dependency ID | Change claimed | Evidence | May mark resolved? |
| --- | --- | --- | --- |
| | opened / updated / resolved | | only with evidence and authority |

## Shared-file reconciliation

List every coordination-sensitive file touched (`CURRENT_STATE`, journal,
`docs/adr/`, contracts, `config/`, manifests, migrations, CI):

| Path | Why required | Conflict check |
| --- | --- | --- |
| | | clean / needs Lane 1 reconcile / `CROSS_WORKSTREAM_CONTRACT_CONFLICT` |

## Safety attestation

- `LIVE` unauthorized preserved: yes/no
- No production broker orders: yes/no
- No TradeStation auth performed: yes/no
- No Gmail auth performed: yes/no
- No Supabase connection performed: yes/no
- No credential provisioning: yes/no
- No paid database service: yes/no
- No remote migration: yes/no
- No secrets in Git/chat/logs/PR: yes/no

## Next actions

- Next permitted action:
- Next prohibited action:
- Operator decisions requested (if any):

## Notes

Facts / inferences / assumptions / open questions must be labeled separately.
