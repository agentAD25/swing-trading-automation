# Gmail read-only corpus gate

Gate A research record. Gmail is not connected. No OAuth credential is
present in this repository or in the process environment that prepared
this record. The stopping token is
`P2_GMAIL_OPERATOR_OAUTH_SETUP_REQUIRED`.

ADR-0004 is Proposed. It does not authorize a connection by itself.

## Architecture

Use the official Gmail API:

- `GET https://gmail.googleapis.com/gmail/v1/users/me/messages`
- `GET https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}`

`userId` is the literal `me` for the authenticated mailbox. The real
mailbox address is runtime configuration named `SIGNAL_MAILBOX`. It is
not written into source, fixtures, tests, docs, or Git history. Committed
fixtures keep `signals@example.invalid`.

Minimum scope, and the only scope requested:

`https://www.googleapis.com/auth/gmail.readonly`

`gmail.metadata` does not include the message body, and its list method
cannot use the search parameter `q`. Add-on scopes apply only while an
add-on is running. No narrower first-party scope found in this review can
search the mailbox and retrieve MIME bodies. Broader scopes are not
required for list or get. They are not requested.

Allowed adapter operations, when a later gate implements them:

- list or search message ids and thread ids
- get metadata and the full or raw MIME message

Prohibited adapter operations:

- send, draft, insert
- modify, trash, delete, archive, move
- label create, update, or delete
- mailbox administration
- remote-image fetch, link following, attachment execution

The adapter must not expose a generic Gmail client to the rest of the
application. It must not import or call `BrokerAdapter`. Shadow parsing,
if later authorized, calls the existing offline `parse_email` on bytes
already retrieved. Parser output is research evidence only.

IMAP, SMTP, and browser automation are not selected. No first-party gap
in list or get required them.

## Provider record

A later acquisition record can hold: provider `GMAIL`, provider message
id, provider thread id, retrieval time, validated RFC timestamp when the
header parses, From and Subject metadata, MIME content type, plain and
HTML availability, attachment metadata without bytes executed, raw
SHA-256, and retrieval, classification, and sanitization status.

From metadata is not sender authentication. The provider message id is
not an economic instruction id. ADR-0003 retention remains
`HASH_PROVIDER_REF_FIELD_EVIDENCE`. This phase does not create a
permanent raw-newsletter store.

## Temporary handling

Real messages are not committed. `data/` is gitignored. A later Gate B
may place temporary copies only under ignored `data/` or another
untracked local path for the duration of that analysis. This record does
not claim that Cursor Cloud deletion can be proved. Sanitized fixtures,
if produced later, use synthetic Message-IDs and
`signals@example.invalid`, and omit tracking ids, unsubscribe tokens,
recipient data, the real mailbox address, and authentication material.

## OAuth is not established

Checked facts:

- Process environment names containing `GOOGLE`, `GMAIL`, `OAUTH`,
  `GCP`, `CLIENT_SECRET`, or `REFRESH`: none.
- No Gmail client exists under `src/`.
- `.env` and `.env.*` are gitignored. `.env.example` does not contain
  Google credentials.

An external consent screen left in Testing issues a refresh token that
expires in seven days. Moving the app to production would raise
restricted-scope verification. That move is not requested here.

## Operator setup

Do not paste a client secret, access token, refresh token, authorization
code, session cookie, or mailbox password into chat, logs, docs, or Git.

1. Create or choose one Google Cloud project for this mailbox. Do not
   send the project number unless a later gate asks for that non-secret
   identifier.
2. Enable the Gmail API in that project.
3. Configure the OAuth consent screen.
   - If the mailbox is a user in a Google Workspace organization you
     administer, user type Internal is the smaller consent path.
   - Otherwise use user type External and publishing status Testing, and
     add only the dedicated mailbox as a test user. Expect the refresh
     token to expire in seven days.
4. Create one OAuth client.
   - Prefer a Desktop (installed-app) client so consent finishes in a
     browser on a machine you control. Use the redirect URI Google Cloud
     Console displays for that client. This repository does not choose
     one.
   - Use a Web client only if you already control the HTTPS redirect
     endpoint. Do not invent a redirect URI for Cursor.
5. Request only
   `https://www.googleapis.com/auth/gmail.readonly`, with offline access
   so a refresh token is issued. Do not add `gmail.modify`,
   `gmail.compose`, `gmail.send`, or `https://mail.google.com/`.
6. Complete consent yourself. Store the client secret, if the chosen
   client type has one, and the refresh token in Cursor environment
   secrets or an approved secret manager. Suggested names, values absent:
   `GMAIL_OAUTH_CLIENT_ID`, `GMAIL_OAUTH_CLIENT_SECRET`,
   `GMAIL_OAUTH_REFRESH_TOKEN`, and `SIGNAL_MAILBOX`.
7. Tell Cursor only the non-secret facts listed below.

Safe to report afterward:

- that steps 1–6 are complete
- user type and publishing status
- client type
- the redirect URI registered in the console, if any
- confirmation that the granted scope is exactly `gmail.readonly`
- the environment variable names that were populated, not their values

Never supply:

- client secret
- access token
- refresh token
- authorization code
- mailbox password or session cookie
- the real mailbox address in chat or Git

After that report, the next gate is read-only inventory, classification,
clustering, sanitization, and shadow parsing. It still must not send or
modify mail, connect Supabase or TradeStation, or change parser grammar.
