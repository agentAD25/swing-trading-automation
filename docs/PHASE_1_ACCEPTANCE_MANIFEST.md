# Phase 1 Acceptance Manifest

- Status: `PHASE1_ACCEPTED`
- Acceptance scope: evidence-only metadata for the exact candidate below
- Candidate commit: `abc1fb6a9cc3554e7ad13f438685ba3c3c044dab`
- Candidate tree: `cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808`
- Evidence head independently verified:
  `b3291a030b165315846b6703805afe9d28120bd8`
- Immutable reference: `refs/tags/phase1-accepted-abc1fb6`
- Annotated tag object: `197d22b06cf6a96bad8c4b1a49ad1b928b147ac0`
- Verifier identity: independent verifier, as attested by the human Operator;
  no personal or service identifier was supplied
- Verifier result: `PASSED`
- Acceptance date: 2026-09-25

## Bounded meaning

`PHASE1_ACCEPTED` accepts only the exact broker-neutral, offline,
deterministic baseline identified by the candidate commit and tree above. Its
only execution context is local, deterministic, non-network `DRY_RUN`.

Acceptance does **not** authorize implementation, Phase 1E, Phase 2,
credentials, OAuth, account access, broker connectivity, TradeStation `SIM`,
queries, confirmations, orders, replacement/cancellation, streams, real
capital, deployment, or `LIVE`. It does not certify strategy efficacy,
production readiness, operational safety, broker compatibility, or legal,
regulatory, entitlement, and licensing compliance.

This manifest, `CURRENT_STATE.md`, and the acceptance journal entry are
evidence metadata created after verification. They do not alter or silently
join the accepted candidate tree.

## Immutable reference rationale

No repository tag convention existed before acceptance. The annotated tag
`phase1-accepted-abc1fb6` is candidate-specific rather than a moving alias. It
points directly to the accepted candidate commit, carries the bounded
acceptance statement, and must never be moved or recreated. Any later
acceptance requires a new candidate-specific tag.

Verification:

```sh
git cat-file -t phase1-accepted-abc1fb6
git rev-parse phase1-accepted-abc1fb6^{commit}
git rev-parse phase1-accepted-abc1fb6^{tree}
```

Result:

```text
tag
abc1fb6a9cc3554e7ad13f438685ba3c3c044dab
cb5fc1f9bd476d7154e07439f2bf2fcccb7fa808
```

The annotated tag object's SHA is
`197d22b06cf6a96bad8c4b1a49ad1b928b147ac0`.

## Atomic 45-file artifact inventory

The candidate commit/tree atomically binds exactly 45 files. `Blob OID` is the
Git blob identity; `SHA-256` is independently computed from the candidate's
file bytes.

| # | Path | Blob OID | SHA-256 |
| ---: | --- | --- | --- |
| 1 | `.cursor/agents/broker-api-researcher.md` | `99f1c635809ce3e25b7e9d464235e2df65eb402b` | `1369ba2cdba61be525bf11f3a7fdd54ded5c73f81a2b4123132b38f78fdcfd87` |
| 2 | `.cursor/agents/governance-coordinator.md` | `c677f4b12b2e9f7b7e44cbb91c7975449b6af880` | `3e13cc2f52d7009fbe413e4f8a7479e5a356481b2aab7c2744efa9a0b8cf5c52` |
| 3 | `.cursor/agents/risk-operations-researcher.md` | `19c107aa0a592b3e33cc9bb7d3ea4c528bc8cb6f` | `cc99648e8bf791655bf82e00fb3c8f1796420a41da13c9dd795aaaf67af7004f` |
| 4 | `.cursor/agents/strategy-data-researcher.md` | `95349fb0a4af1c6aa81b7f11feffbdd66f804c1d` | `7ca274715ec41220e83e7f9624a2779a450f9c51afbfebbc0efd688241e0fe84` |
| 5 | `.cursor/rules/00-governance.mdc` | `e4932c9743c52f8b911e7667a2b54161b25eacdd` | `71c4fce8b049ded8781c519b48d2a25f16f47c88719b769354863a9f0cfd488c` |
| 6 | `.cursor/rules/10-trading-safety.mdc` | `ccf042953c5f6d573ead24282c090b55772f751a` | `54538db14223b3d93c4e528fa47a36fb24e4bfa05246ead4c9b0813835dbfa60` |
| 7 | `.cursor/rules/20-evidence-and-quality.mdc` | `0cb1d466b7351f5653d24fa3115cc06d0d85ca9a` | `f89071434627466395db5d3eaf984d8eb6b955d684e6615663c27bfd4ab53bfb` |
| 8 | `.gitignore` | `36a6a825fbfdac982bbaa79247c85ee46125cb63` | `601c845bb63053aabb94039aead092ec1d1b4b2e52993bdd3f180b660d27ab89` |
| 9 | `README.md` | `268a71fb841bc6f6cad7a4b0942de3cf75977e63` | `d81c3f0a562f018e4f2af26222e6bd40ee7ae70b3ca44a1410567e1a169f09d1` |
| 10 | `Test` | `345e6aef713208c8d50cdea23b85e6ad831f0449` | `c9d04c9565fc665c80681fb1d829938026871f66e14f501e08531df66938a789` |
| 11 | `config/README.md` | `152c10d2eaa3ad199086ea2f5fd7fa35e7194f4e` | `3364353bb6298a100a59daea04de7f09dc5c59c30ff81e9c6e1fd4e8b3417669` |
| 12 | `docs/AGENT_AUTHORITY.md` | `629aff714d5e2ad86aaf4a90a3ce6e36dbb3d43e` | `995a489d798509deb24fa81a242aeae84c97dfa086e9e763903e450056527b6e` |
| 13 | `docs/ARCHITECTURE.md` | `55a3611bc53c8573d06c7ec11298244e1c03e8dd` | `f8fe28257c01459d38ffad99bc2d1717974b40e95b8796e848008722f7117a6b` |
| 14 | `docs/BROKER_CONTRACT.md` | `bd408faccaa76bd0ad496f6e8e81bbadffe55569` | `78be99cbd69c77fc82ed374c95ecc77d7c906b16717c62bc6c0e28f38f9f7a5a` |
| 15 | `docs/CURRENT_STATE.md` | `7371d7a0addbd28147d8d2155a166fc7d4bf246c` | `bf852f64a2cc16c390c22a65463d6a442832d5c319ec74eea533a0205366b8d5` |
| 16 | `docs/DATA_MODEL.md` | `b33a0b48e6e53a3ec2d478d84d476244e828eced` | `e2121bf5b27b4d718e8a96abac6c93fca426c49027d60e600741c5b657504a2f` |
| 17 | `docs/DECISIONS.md` | `22a8d0bd465a2cff3c179789de46ca11c2e5d80e` | `823d45b967a56fe58e179131772d429db81ac04dfd4fbdc452aa519188047f67` |
| 18 | `docs/ENGINEERING_JOURNAL.md` | `75e3e2c41902a118b3cfb55ae180d141ea1083b1` | `69a3a17e534d877e7b72ddd0baf6babca2439eca1184a87670ed0014f3226035` |
| 19 | `docs/EVENT_MODEL.md` | `bdbb1950c8cbd5ab9e41d6972a80a4d1b2fec8a5` | `71e0df6c3062b8711f5a9ec17cf789293b5d2b0f3a4627f369ec46fa74b30809` |
| 20 | `docs/FAILURE_MODEL.md` | `00fc076e51a4f3f64df2f3b2a66d0cf793e60d93` | `9f250623d31bab8829a81e1f771ea237006012d3029bd0bc3f016aaac9e5fad4` |
| 21 | `docs/IDEMPOTENCY.md` | `791757f46ec6743d7c2df527cba16641c6f6817d` | `c6b5f3edc4922e589eae3b56cb1c8b08cce8473b413a2410988e588be209d28b` |
| 22 | `docs/LIVE_PROMOTION.md` | `b58e13f61053f755b376b4431cd641fd22dcbe51` | `a48c41ab42d07c13e7e5930793af5ac2a5ed810205c548c21fc3a39db0eabce6` |
| 23 | `docs/METRICS.md` | `2d3f75d9a9cd43ec7b4c6b1a20196c2ee892fb02` | `506e09689d55f140b8d494f49116ee8eb4f6f33ba1f0d27cda54b9d9241ac74c` |
| 24 | `docs/MONITORING.md` | `45fba187669eae7609e94f8cd0281ea60f309f75` | `85c03150ef82e34c18afc75c25f4e48e202c7cae1ab1b9f2149816c25ebbb522` |
| 25 | `docs/PHASE_1C_RECONCILIATION.md` | `ab3406d0fd0d81286f80d86391127dddc62985e3` | `c726d0eeecae92d2c8ce9f85e9b87a98b49697ddd0b36f7dc016ed6925713ea3` |
| 26 | `docs/PHASE_1D_CORRECTIONS.md` | `ae54edfb1328c0a090e3153e94c8378a04d7eb30` | `d07ba008bd51e632b068dadca3131ea66460348b00b05012ce3cc02a4e548c27` |
| 27 | `docs/RECONCILIATION.md` | `b88095bac612e312504aef1a044f33f52bcd1058` | `969b8d48d05f6c57f0e199d78d23aafeb1c1b5e33a68fa4e692c3f21dbd760dd` |
| 28 | `docs/REPORTING.md` | `119daa11f240344cbc156fff45d0ba15910dd414` | `3b713fbf051d4a2e9f59fee34062b9bade77e94104897fd2e90c04a6f89e5185` |
| 29 | `docs/SIM_CERTIFICATION.md` | `e09ceee3e32a13af8e85045348a791ae33ecd908` | `3707f7900bab4056bf166b642370123f0c6116e858e122c04350ab085e4cb1f5` |
| 30 | `docs/SIM_LIVE_BOUNDARY.md` | `4bcd7419c7abef6ac2361bf2f25b03238feeb3fb` | `ca0a2dd2a69a6c5ba77ec443cfc429702d3905a01af6c0c364beea71b90d11fa` |
| 31 | `docs/TEST_PLAN.md` | `74c8c96d30deca950907147690bf0d4986a6fa91` | `f79bae1b00fb1c19aac1381f4249d75f29d65f91d7b3f0113f94665da76ec1e8` |
| 32 | `docs/TRADE_LIFECYCLE.md` | `f6d15399c8a43b3e1be182e9238ac5970a0922f5` | `25bb97c8dd232a3879de402ea88784269f1accda173b1de74ef997dea169cdff` |
| 33 | `docs/adr/0001-phase-1b-foundation-contracts.md` | `8f3af730440664ab7027a8b9e6936ca65a01bab2` | `d5a26fd0a977d4a2509c45fb47e1eeb5c8ef7e3b76dd5e0fe97ecd3d780b7ba3` |
| 34 | `docs/adr/ADR-TEMPLATE.md` | `4afa3ff431c6055dd22cc8b79ea3659e8a15ba00` | `708bd823b178de6ef5bf6419a0b99ae8d0c2c52cf8cb664b441e18ca33bcbdc5` |
| 35 | `docs/adr/README.md` | `9649b1e7986f61959e106715d3b90438fa011f9c` | `1946a7cf02a64d3e47a0a2e250af2edb7bf3b829af310644d97ef1d5a2fa81cb` |
| 36 | `docs/research/README.md` | `0ed6b254fba2df9cdc4fb19b5de0a29221c95db5` | `60036c76fb1004325ae6f980d38f573c808e343d60119fd64f090bcf1d194f55` |
| 37 | `src/README.md` | `036b87dbd3f8174659d5b471a812a435ba0bb329` | `30dc6e3a9c01b1cfbf0299d6b787a98bb43814b42cb8d9f948c86ea78c313989` |
| 38 | `tests/README.md` | `cdfb0db8b8fd7c3238fea3451cd3a097e8d3e524` | `eb552c35f2011aa3506488e24fa3e15085edc9dec3f2ac13a091b39c7b04924f` |
| 39 | `tests/fixtures/wdc-reference/README.md` | `a0c46d6854c0490fb42b1d3f67fe5940e1b5ba57` | `54a247454dd3486dc11bae693718b9278b201fcb8200508e682f2824d95b5dd9` |
| 40 | `tests/fixtures/wdc-reference/bars.csv` | `172384976469eba2a839d52c0072e3858432271e` | `e194cdef7ca448a8ceadb64d06699f35ef4c59da131786d7835099861df5e3bc` |
| 41 | `tests/fixtures/wdc-reference/expected-events.jsonl` | `7a60ae80b0782e2427e3584ba562d7d38c85f509` | `7b50e2475326283832df77a23e03b6e46e97eaf98342c88cd9dbdcc332e6447a` |
| 42 | `tests/fixtures/wdc-reference/expected-report.json` | `61976d9563351958fa38879ebd800042b10dc758` | `95585e7b1ba762a95719a154b02b5c06eeea5b1ff9e1428b80bb36e3ebdd909c` |
| 43 | `tests/fixtures/wdc-reference/manifest.json` | `0fab3f18f1f154fc75506bc59bc026878fecf337` | `17e32990d551ec6b72285d6e78a49006dfbd5e10ba580b329ab0460f4a6d20b7` |
| 44 | `tests/fixtures/wdc-reference/scenario.json` | `a061415bc0b3b927765b729222f5642d0def67b9` | `bd7af4205b9896bfd7fbe52bbf80ab0b4979c81116b2c8d8ce2520a49a91a501` |
| 45 | `tests/validate_phase1_contracts.py` | `291dfeaec34e7ace462b4f24cbe44ab1630b596b` | `e2dc67736159c85a6c8f485901f77ee703fdac2081e098f36d6957b8c9c308f5` |

Inventory commands:

```sh
git ls-tree -r abc1fb6 | wc -l
git ls-tree -r abc1fb6
while IFS=$'\t' read -r meta path; do
  sha=$(git show "abc1fb6:$path" | sha256sum | cut -d' ' -f1)
  blob=$(printf '%s' "$meta" | awk '{print $3}')
  printf '%s\t%s\t%s\n' "$blob" "$sha" "$path"
done < <(git ls-tree -r abc1fb6)
```

Result: exactly `45` entries; every row above matched.

## Verification evidence

Independent verification passed candidate/tree/evidence-head exactly as
identified above. Repository re-verification used:

```sh
python3 tests/validate_phase1_contracts.py
git merge-base --is-ancestor 42ac8cd abc1fb6
git merge-base --is-ancestor d459850 abc1fb6
git diff --check cursor/phase-1a-governance-e1ba...abc1fb6
git status --porcelain
```

Results:

```text
Phase 1 contracts: manifest, C01, C02, C03, C04 PASS; required-field omission regression PASS; reconciliation evidence negative/positive regressions PASS
ancestry checks: exit 0
diff check: exit 0
candidate worktree at verification: clean
```

Relative-link verification checked 29 Markdown files and passed. Active
DRY_RUN/SIM-LIVE assertions and WDC no-overclaim assertions passed.

## Reconciliation root cause and stable fixture digests

Root-cause classification is `REPORT_OVERCLAIMS_EVIDENCE`. The source ledger
contains no qualifying reconciliation-completion event; therefore the accepted
report is `UNRECONCILED`, its event is `report.withheld.v1`, and no history was
fabricated.

Stable fixture/digest values:

```text
bars.csv             e194cdef7ca448a8ceadb64d06699f35ef4c59da131786d7835099861df5e3bc
scenario.json         bd7af4205b9896bfd7fbe52bbf80ab0b4979c81116b2c8d8ce2520a49a91a501
expected-events.jsonl 7b50e2475326283832df77a23e03b6e46e97eaf98342c88cd9dbdcc332e6447a
expected-report.json  95585e7b1ba762a95719a154b02b5c06eeea5b1ff9e1428b80bb36e3ebdd909c
manifest.json         17e32990d551ec6b72285d6e78a49006dfbd5e10ba580b329ab0460f4a6d20b7
report content        f9a969c5f151133bad5d14f39a7cd17fafb033f9da87a1b5d8f53de04b2b3f46
entry idempotency     c4131ccda4608e4604adf5f36a49265ccf5e57e4f1754f1b6ff2f2403f180b0f
exit idempotency      92949cf1b3481ce27b71360ccf67ae3580dc03d913088aee60fedefd5c2bbfa3
report idempotency    54b3b57426148284b3ca7f7423902f6218f7b2813dfd743ce4d6ee9d7a4e989f
```

## Twelve unresolved TradeStation behavior groups

These remain unresolved and outside accepted Phase 1 capability:

1. Idempotency: `OrderConfirmID` acceptance, retention, collision, and retry
   semantics, especially after timeout or lost response.
2. Ambiguous outcomes: recovery after 503/504, disconnect, or client timeout
   during place, replace, and cancel.
3. Order state machine: complete statuses, terminal states, transitions,
   correction/bust handling, and REST/stream ordering.
4. Stream recovery: heartbeat, reconnect, replay/resume, gaps, duplicates, and
   snapshot/stream reconciliation.
5. SIM fidelity: partial fills, rejects, cancels, replace races, market hours,
   buying power, corporate actions, and entitlements.
6. Authentication conflicts: 30-versus-40-minute rotation and actual default
   scopes.
7. Account and entitlement contract: account types, assets, latency, sessions,
   routes, short locate, and key-specific quotas.
8. Confirmation semantics: requirement, lifetime, and acceptance/price-binding
   meaning of `OrderConfirmID`.
9. Batch atomicity: multi-leg, OSO, and group transaction boundaries,
   including mixed orders/errors.
10. Rate-limit identity: aggregation across processes, tokens, logins,
    accounts, and applications.
11. Decimal and time semantics: precision, rounding, ticks, timestamp
    precision, sessions/timezones, and clock skew.
12. Retention: availability beyond 90-day history and 600-item unpaginated
    limits.

## Deferred empirical questions and decisions

Acceptance does not resolve:

- authenticated Operator identity and future acceptance mechanism;
- technology stack, persistence/queue products, deployment/network topology,
  environment ownership, retention, backup/recovery, and service objectives;
- strategy, universe, data vendor, calendar, revisions, bias controls, and
  validation protocol;
- risk/capital/kill limits, cost/fee model, rounding/tick/lot rules, operating
  thresholds, alert routes/staffing, incident/change processes, waiver
  authority, and report recipients;
- future SIM owners/sign-offs, credential/OAuth/account/endpoint handling, and
  all twelve broker behavior groups;
- legal, regulatory, tax, market-data entitlement/licensing, privacy,
  security, and record-retention obligations; and
- every Phase 1E, Phase 2, TradeStation SIM, and LIVE authorization decision.

All empirical broker questions require later first-party clarification and/or
separately authorized non-LIVE testing. No item is resolved by acceptance or
assumption.
