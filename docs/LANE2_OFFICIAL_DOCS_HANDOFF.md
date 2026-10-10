# Lane 2 handoff — official documentation research

Copied from `docs/WORKSTREAM_HANDOFF_TEMPLATE.md`. This handoff asks Lane 1
not to close TradeStation dependencies from public documentation. It does
not edit `docs/WORKSTREAM_DEPENDENCIES.md` or `docs/WORKSTREAM_STATUS.md`.
It does not accept ADR-0005.

## Identity

- Lane identifier: `LANE-2`
- Workstream name: TradeStation / Broker
- Agent role: Lane 2 specialist documentation
- Branch: `cursor/p2-ts-provider-evidence-99c1`
- PR number (if any): Draft PR #22
- Exact HEAD SHA: `00b6e7ede7fdae99710bd4e82129902cde244237` (research
  documentation commit). The pre-change parent was
  `daae1e179b00c7166003b50121f325cfed909b1b`. A descendant identity note
  records this SHA and does not embed its own hash. Lane 1 should read
  the PR head for the branch tip.
- Exact tree SHA: `f3f92d19d96ddd15d1d0dd530da11f054ade580a` (research
  documentation tree). Pre-change tree was
  `c14001b8bee36a95ae0811d56859ca9d4c7a3798`
- Canonical main baseline SHA/tree used at branch start:
  `2c895291a3b4282f8cf5c7426c705bfdab365c47` /
  `25ebd09e495bb2db7b7f856963a0af876a378457`
- Handoff date (UTC): 2026-10-10

## Objective and scope

- Current objective: record what official TradeStation documentation
  supports for authentication and read-only brokerage contracts, without
  treating published defaults as key-specific confirmation.
- In-scope paths: `docs/P2_TS_OFFICIAL_DOCS_2026-10-10.md`, this file,
  pointers in `docs/adr/0005-tradestation-provider-evidence.md`,
  `docs/P2_TS_PROVIDER_EVIDENCE_2026-10-08.md`, `docs/CURRENT_STATE.md`,
  and `docs/ENGINEERING_JOURNAL.md`.
- Explicitly out-of-scope paths: `docs/WORKSTREAM_DEPENDENCIES.md`,
  `docs/WORKSTREAM_STATUS.md`, `src/`, `tests/`, Gmail, PostgreSQL,
  shared economic contracts, and the 2026-10-06 quotations.
- Authorization cited from `docs/CURRENT_STATE.md`: `DRY_RUN` only.
  TradeStation `SIM` unauthorized. `LIVE` unauthorized.

## State claim

- Requested `WORKSTREAM_STATUS` state: `WAITING_PROVIDER` remains
  appropriate for the key-specific residue. Do not set Lane 2 to
  `SUPERSEDED` or `VERIFIED` from this research.
- Certification status claim: not certified. ADR-0005 remains Proposed.
  Prior implementation verification of
  `19154eae43990df1d83a78be7b6dac3710a28804` still covers `src/` and
  `tests/` only while those trees are unchanged.
- Integration eligibility claim: `not_eligible`. PR #22 stays draft.

## Evidence

- Commands run: public documentation fetches listed in
  `docs/P2_TS_OFFICIAL_DOCS_2026-10-10.md`, then local document checks
  recorded in the journal.
- Outcomes: no new implementation suite. PostgreSQL skips from the prior
  verification stay skips.
- Independent verification identity: not applicable to this documentation
  commit. Implementation verifier remains
  `bc-e2d7b87b-2d7e-55d1-8dd8-631005b76379` for tree
  `de97145c7278afbfe432463733a02b5e8a74ced9` only.
- Artifact path: `docs/P2_TS_OFFICIAL_DOCS_2026-10-10.md`.

## Dependencies

| Dependency ID | Change claimed | Evidence | May mark resolved? |
| --- | --- | --- | --- |
| `DEP-TS-001` | no closure | Native callback still unanswered. Supersession still waits on architecture acceptance | No |
| `DEP-TS-002` | no closure | Regular Web is the published default. Key format does not prove application type. This key was not inspected | No. Stay `OPEN` |
| `DEP-TS-003` | no closure | Desired scopes and local fail-closed checks are documented. The grant is not | No. Stay `OPEN` |
| `DEP-TS-004` | no closure | One HTTPS callback fits documented Regular Web. Registrations for this key are unknown. No hostname chosen | No. Stay `OPEN` |

No new dependency ID.

## Shared-file reconciliation

| Path | Why required | Conflict check |
| --- | --- | --- |
| `docs/CURRENT_STATE.md` | Point at the research without expanding runtime authority | needs Lane 1 reconcile on the next main merge |
| `docs/ENGINEERING_JOURNAL.md` | Record the research and the unchanged source tree | needs Lane 1 reconcile on the next main merge |
| `docs/adr/0005-tradestation-provider-evidence.md` | Cite the research. Status stays Proposed | clean for Lane 2; acceptance is not requested |
| `docs/WORKSTREAM_DEPENDENCIES.md` | Not edited | Lane 1 leaves the IDs `OPEN` |

## Safety attestation

- `LIVE` unauthorized preserved: yes
- No production broker orders: yes
- No TradeStation auth performed: yes
- No Gmail auth performed: yes
- No Supabase connection performed: yes
- No credential provisioning: yes
- No paid database service: yes
- No remote migration: yes
- No secrets in Git/chat/logs/PR: yes

## Next actions

- Next permitted action: Lane 1 leaves `DEP-TS-002`, `DEP-TS-003`, and
  `DEP-TS-004` `OPEN` and does not treat this research as key-specific
  authorization.
- Next prohibited action: accepting ADR-0005, credential onboarding,
  OAuth, SIM or LIVE connectivity, orders, parser expansion, and merging
  PR #22.
- Operator decisions requested: none. The unsent follow-up stays unsent
  unless the Operator later chooses to ask a key-specific question.

## Notes

Fact: official pages accessed 2026-10-10 still conflict on default scopes
and on 30-minute versus 40-minute optional refresh rotation.

Fact: the October 2026 Client Experience correspondence remains the
provider-written record and is not rewritten.

Inference: Option A is compatible with the documented Regular Web flow if
the issued key is that application type.

Open question: the issued key's format, application type, granted scopes,
and callback list.
