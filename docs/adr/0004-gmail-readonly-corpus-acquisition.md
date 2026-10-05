# ADR-0004: Gmail read-only corpus acquisition

- Status: Proposed
- Date: 2026-10-05
- Sole Phase 1 decider: Human Operator
- Scope: Transport-only Gmail read access for newsletter corpus research
- Supersedes: None
- Superseded by: None

## Context

Group 4A is on canonical `main` at certified commit
`ce045c14b119d882505a947a7826005ff6d99103`, tree
`67a0b57526ea219972fa0574b191562f0f52b598`, and the integration evidence
commit `41218abb2eda5f06001703fb83c2cb9e43e5ec2e`. The offline parser does
not connect to a mailbox. The next authorized work is read-only acquisition
of real newsletter messages so later fixtures and grammars can be based on
evidence.

This record does not accept a Gmail connection, a broader OAuth scope, a
parser-grammar change, Group 4B, Supabase, or TradeStation. The Decision
section stays blank while the status is Proposed. The Operator has not
completed Google OAuth setup. No Gmail call has been made.

## Safety impact

Gmail is a transport source, not trading authority. A future adapter may
list and retrieve messages. It must not send, modify, delete, trash,
archive, move, or mutate labels. It must not follow newsletter links, load
remote images, or execute attachments or HTML. Retrieved messages must not
reach `BrokerAdapter`, order intents, TradeStation, `SIM`, or `LIVE`.

`EMAIL_RETENTION_POLICY` remains `HASH_PROVIDER_REF_FIELD_EVIDENCE` under
ADR-0003. This proposal does not authorize a permanent raw-newsletter
archive. `DRY_RUN` remains the only authorized execution mode. Quantity
rounding, timezone, and the market calendar stay unresolved.

## Options considered

### Option A — Gmail API with `gmail.readonly`

Use the official Gmail API methods `users.messages.list` and
`users.messages.get`. Request only
`https://www.googleapis.com/auth/gmail.readonly`.

First-party scope text says this scope views email messages and settings.
Both list and get accept this scope. List search (`q`) is unavailable under
`gmail.metadata`, and that scope does not include the message body. Corpus
classification needs the body, so `gmail.metadata` is not sufficient.
Add-on scopes apply when an add-on is running, which is not a mailbox
inventory. `gmail.modify`, `gmail.compose`, `gmail.send`, and
`https://mail.google.com/` add send, draft, or delete capability this phase
prohibits.

### Option B — IMAP, SMTP, or browser automation

No first-party Gmail API gap found in this review requires IMAP, SMTP, or
browser automation. Those paths are not selected.

## Decision

## Consequences

If the Operator later accepts this proposal, Gate B can connect only after
OAuth material exists outside Git. Until then the token is
`P2_GMAIL_OPERATOR_OAUTH_SETUP_REQUIRED`. An external OAuth app left in
Testing receives a refresh token that expires in seven days. Publishing the
app is a separate restricted-scope decision and is not part of this
proposal.

## Validation and rollback

Rollback is to make no Gmail call and to keep this ADR Proposed. A future
connection is invalid if any write method is invoked, if any scope other
than `gmail.readonly` is granted, or if a message reaches an order path.

## Unresolved questions

- Whether the dedicated mailbox is a consumer Gmail account or a Google
  Workspace user. That choice selects Internal versus External consent.
  The address is not recorded here.
- The OAuth client type and the exact redirect URI shown by Google Cloud
  Console. This repository does not invent either value.
- Where the Operator will place the refresh token: Cursor environment
  secrets for this cloud agent, or another approved secret manager. The
  value itself is not a repository decision.

## Evidence

- Title: Choose Gmail API scopes. URL:
  https://developers.google.com/workspace/gmail/api/auth/scopes.
  Accessed 2026-10-05. Page last updated 2026-09-10 UTC. Supports:
  `gmail.readonly` is "View your email messages and settings";
  `gmail.metadata` is "View your email message metadata such as labels and
  headers, but not the email body"; `gmail.modify` includes compose and
  send; `https://mail.google.com/` includes permanent delete. Add-on scopes
  are limited to add-on interaction.
- Title: Method: users.messages.list. URL:
  https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list.
  Accessed 2026-10-05. Page last updated 2026-04-15 UTC. Supports: `q`
  "cannot be used when accessing the api using the gmail.metadata scope";
  list results contain only `id` and `threadId`; authorized scopes include
  `gmail.readonly`.
- Title: Method: users.messages.get. URL:
  https://developers.google.com/gmail/api/reference/rest/v1/users.messages/get.
  Accessed 2026-10-05. Page last updated 2026-04-15 UTC. Supports: get is
  authorized for `gmail.readonly` among other broader scopes, and `format`
  selects the returned representation.
- Title: Using OAuth 2.0 to Access Google APIs. URL:
  https://developers.google.com/identity/protocols/oauth2.
  Accessed 2026-10-05. Supports: an external consent screen in Testing
  issues a refresh token expiring in 7 days unless the only scopes are
  basic identity scopes; a refresh token that contains Gmail scopes can
  stop working if the user changes passwords.
- Title: OAuth app state overview. URL:
  https://developers.google.com/identity/protocols/oauth2/production-readiness/overview.
  Accessed 2026-10-05. Supports: Internal apps are organization-only and
  do not use the external test-user cap; External Testing is limited to
  allowlisted test users.
