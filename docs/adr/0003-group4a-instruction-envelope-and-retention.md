# ADR-0003: Group 4A instruction envelope and email retention

- Status: Accepted
- Date: 2026-10-05
- Sole Phase 1 decider: Human Operator
- Scope: Offline Group 4A canonical instruction shape and email retention
- Supersedes: None
- Superseded by: None

## Context

Independent review of draft PR #20 at commit
`229a38b4b6f7ab628d1c656974686e7888075302`, tree
`80870e9ec5f2ee2a4c9b29513da6c1ebae8a1fd2`, returned
`P2_G4A_EMAIL_TRADE_INSTRUCTION_BLOCKED`. Two of the seven findings were
contract gaps: the new-trade object could not represent a future amendment,
exit alert, or cancel without becoming a partially optional union, and
`EMAIL_RETENTION_POLICY` was `UNRESOLVED`.

Group 4A remains offline. This record does not authorize Gmail, IMAP, SMTP,
TradeStation, Supabase, credentials, orders, TradeStation `SIM`, or `LIVE`.

## Safety impact

The parser still stops at a typed instruction or reject/quarantine. No order
is submitted. No mailbox is connected. The retention record stores a SHA-256
digest, a fixture provider locator, parser and schema versions, an optional
validated source timestamp, and field-level economic excerpts. It does not
store the raw newsletter or a normalized body. `DRY_RUN` remains the only
authorized execution mode.

## Options considered

### Option A

Keep one `TradeInstruction` and add optional amendment, exit, and cancel
fields.

This preserves today's constructor and forces every future message type to
carry entry, sizing, target, and protective stop, or to make those fields
optional on the new-trade object.

### Option B

Keep a required-field `NewTradeInstruction` and put it in a canonical
envelope beside distinct reserved payload types. Adopt retention as hash
plus provider retrieval reference plus field-level economic evidence.

Future fixtures can use the reserved types without changing the new-trade
object. Group 4A still parses only new trades.

## Decision

The human Operator selected Option B in the 2026-10-05 Group 4A remediation
authorization. This ADR records that decision. The agent did not select it.

`CanonicalInstructionEnvelope` carries `NewTradeInstruction`,
`TradeAmendmentInstruction`, `ExitAlertInstruction`, or
`TradeCancelInstruction`. Only new-trade parsing is implemented. A
recognized amendment, exit alert, or cancel stays quarantined with zero
accepted payloads. `TRADE_AMENDMENT_PARSER`, `EXIT_ALERT_PARSER`, and
`TRADE_CANCEL_PARSER` stay `DEFERRED_FIXTURE_REQUIRED`.

`EMAIL_RETENTION_POLICY` is `HASH_PROVIDER_REF_FIELD_EVIDENCE`. The provider
reference is a locator. It is not the economic instruction id. For local
fixtures the provider type is `FIXTURE` and the reference is the synthetic
message id. No real mailbox address is recorded.

Unlabeled prose such as "Please amend TDAY stop to 6.00 tonight.", "Exit
the TDAY position at the open.", and "Cancel the TDAY order." stays
`INFORMATIONAL` with zero payloads. No grammar was invented for those
sentences.

## Consequences

New economic fields on `NewTradeInstruction` enter the plain-versus-HTML
projection unless they are explicitly listed as non-economic. Quantity
rounding, timezone, and market calendar stay unresolved. Amendment, exit,
and cancel grammars still require real fixtures before they can accept a
payload.

## Validation and rollback

Acceptance evidence is the Group 4A suite, including retention, payload-type,
and deferred-message tests. Rollback is reverting this branch to
`229a38b4b6f7ab628d1c656974686e7888075302`. Rollback does not authorize a
mailbox or an order path.

## Unresolved questions

- Quantity rounding policy remains `UNRESOLVED`.
- Timezone remains `UNSTATED` and the market calendar remains `UNRESOLVED`.
- Amendment, exit-alert, and cancel grammars remain deferred until real
  fixtures exist.
- Gmail retrieval of the provider reference is a later workstream.

## Evidence

- Title: Group 4A remediation authorization
- Canonical reference: Operator instruction for PR #20, branch
  `cursor/p2-g4a-email-contract-f7f7`
- Access date: 2026-10-05
- Claim supported: adopt a typed envelope with distinct new-trade,
  amendment, exit-alert, and cancel payloads, and adopt retention
  `HASH + PROVIDER RETRIEVAL REFERENCE + FIELD-LEVEL ECONOMIC EVIDENCE`.
- Limitation: the authorization is the instruction recorded in this
  repository's journal. It is not a Gmail or broker approval.
