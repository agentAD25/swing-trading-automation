# Workstream Status Registry

Authoritative four-lane status for concurrent Phase 2 specialist work.
Conversation claims are never authoritative by themselves. Resolve conflicts
using `docs/INTEGRATION_PROTOCOL.md` and the operating hierarchy in
`docs/WORKSTREAM_OWNERSHIP.md`.

Last attestation date: 2026-10-11
Canonical main baseline at the start of this TradeStation registry edit (attested): `8a17bec501df94238fe7588f84f7f1f51fee8baf`
Canonical main tree at the start of this edit (attested): `03d48c9ae453bdfc6a1cdf9cdc43a359e76efb1b`
Attestation method: `git fetch` of `main` and draft PR #22 on 2026-10-11. This descendant commit cannot embed its own hash.
Classification: PR #22 remains OPEN, draft, and `CONFLICTING`. Its Lane 2 row below is re-attested. Lane 3 and Lane 4 rows are not re-certified by this edit.
Historical classification, retained from 2026-10-11: the sentence above that PR #22 remains OPEN, draft, and `CONFLICTING`. Current correction: PR #22 is MERGED and is an ancestor of canonical main `9703efa9d7842e22337c85f7b616bbe21f0c1e2b`, tree `eb23947a05988e8334bda555aa4840a90853543b`. The Lane 2 table below remains the 2026-10-11 attestation. Its next-permitted-action sentence is historical and is not an instruction to merge PR #22 again. Lane 3 and Lane 4 rows are not rewritten by this correction.
Historical 2026-10-10 authorization baseline, now an ancestor: `5a04c5eadd5b61dcf7153cc46fdf363c6ff8029d` / `38c29d18be5930bda628bc32947d484fccb860dc`.
Historical pre-correction record from `7fe37e8e4b89a303856662b9a6333e64fe6df640`: ADR-0007 implementation-authorization preparation, 2026-10-11, said item 16 was not in effect and that Lane 4 must not code yet. That sentence is not operative authority once current-state item 17 is effective.
Operative status: item 17 is the sole ADR-0007 implementation authority when this correction commit is canonical `main` after an Operator decision authorizing integration of this independently verified candidate. Lane 4 stays `READY_FOR_VERIFICATION`. PR #24 is not re-certified here. This descendant cannot embed its own hash.
Item 20 proposal, 2026-10-13. Parent main `a1ce02e33b7cfaeaa9f96968e7ee940a4cb1a01e`, tree `f3bc56ca66bd972db84d9e670313a205b3eca117`. Item 20 is not effective on this branch. When current-state item 20 is effective, Lane 3 may add only `src/swingtrade/group4_email/synthetic_ingestion.py` and `tests/group4_email/test_synthetic_ingestion.py`. Until that activation, Lane 3 must not add those paths. The Lane 3 table below remains the historical attestation. Its next-permitted-action sentence is not an instruction to implement this composition. Lane 2 outcome A is that existing offline broker-report evidence is sufficient and that no new Lane 2 component is authorized. Lane 4 receipt modules are not rewritten. Handoffs `LANE2_PHASE3_BROKER_EVIDENCE_SCOPE_READY`, `LANE3_ITEM20_COMPOSITION_CONTRACT_READY`, and `LANE4_ITEM20_RECEIPT_CONTRACT_READY` are contract-readiness records, not independent verification of an implementation. This descendant cannot embed its own hash.

Item 21 proposal, 2026-10-14. Parent main `1614cbb7060b31bacc59f1687a0c68d91474ed67`, tree `725bc9e78a0d530c6c91163cffda8a83fae57a82`. Item 21 is not effective on this branch. When current-state item 21 is effective, Lane 3 may add only `src/swingtrade/group4_email/local_oauth_probe.py` and `tests/group4_email/test_local_oauth_probe.py`. Those paths are an offline Desktop OAuth and profile-probe client and its tests. Until that activation, Lane 3 must not add those paths. The Lane 3 table below remains the historical attestation. Its Gate B prohibition is the corpus-connection gate from that attestation and is not an instruction created by item 21. Item 21 does not authorize a live provider call. Its Gate C stays blocked until a separate Operator execution decision. `DEP-GMAIL-001` stays OPEN. ADR-0004 stays Proposed. This descendant cannot embed its own hash.

Item 22 proposal, 2026-10-16. Parent main `b313e581eca7fa2265aa10b53f15dc31d7e408be`, tree `356511fa933f953dd1f255946fd951be5158d1fa`. Item 22 is not effective on this branch. When current-state item 22 is effective, Lane 1 may change only `tests/group4_email/test_attacks.py`, and only to exclude the top-level file `local_oauth_probe.py` from the parser substring scan in `test_parser_does_not_use_network_broker_or_credentials`. Until that activation, that file must not be edited for this purpose. The Lane 3 table below remains the historical attestation. PR #48 stays open and unmerged. Its recorded verifier result `INDEPENDENT_EXACT_TREE_FAIL` stays a FAIL. This paragraph does not authorize a live provider call or integration of PR #48. `DEP-GMAIL-001` stays OPEN. ADR-0004 stays Proposed. This descendant cannot embed its own hash.

Item 23 proposal, 2026-10-16. Parent main `fcafaded6dc06d56af256afe244e604b150fcf81`, tree `9653ad4535346d30bfe5a4f07a2d07e77bb6687a`. Item 23 is not effective on this branch. When current-state item 23 is effective, Lane 3 may add only `src/swingtrade/gmail_local_connect.py` and `tests/unit/test_gmail_local_connect.py`. Until that activation, those paths must not be added. The Lane 3 table below remains the historical attestation. Gate B stays the integrated offline probe. `run_attended_profile_probe` stays an unconditional refusal. This paragraph does not authorize a live provider call, Google Cloud provisioning, or integration of a future implementation pull request. `DEP-GMAIL-001` stays OPEN. ADR-0004 stays Proposed. This descendant cannot embed its own hash.

Item 24 proposal, 2026-10-16. Parent main `71ba48283af88fca9e553cca993c5b9c27a1d08e`, tree `9d4e6f974a97c694987033d4bcd82c87b71222f1`. Item 24 is not effective on this branch. When current-state item 24 is effective, Lane 2 may add only `src/swingtrade/alpaca_paper.py` and `tests/unit/test_alpaca_paper.py`. Until that activation, those paths must not be added. The Lane 2 table below remains the historical TradeStation attestation and is not an instruction to connect Alpaca. Item 23 Decision A remains Lane 3's Gmail paths. This paragraph does not authorize an API key, a paper order, or a network call. `DEP-TS-001` through `DEP-TS-004` stay OPEN. ADR-0005 stays Proposed. This descendant cannot embed its own hash.

Item 25 proposal, 2026-10-16. Parent main `ca146e67652bd45583d1472be370a989f451099f`, tree `ecc0b9421717e8ec0727fd1a7f0687898b4dd43d`. Item 25 is not effective on this branch. When current-state item 25 is effective, Lane 1 may change only `tests/failure_injection/test_fail_closed.py`, and only to exclude the top-level filename `gmail_local_connect.py` from the runtime substring scan in `test_runtime_package_has_no_network_or_live_order_client`. Until that activation, that file must not be edited for this purpose. Lane 3 is not granted that path. The Lane 3 table below remains the historical attestation. PR #52 stays open and unmerged. Its recorded verifier result `INDEPENDENT_EXACT_TREE_FAIL` stays a FAIL. Item 23 Decision A remains Lane 3's two Gmail paths. Item 24 remains Lane 2's two offline Alpaca paths and is not an instruction to connect Alpaca. This paragraph does not authorize a live provider call or integration of PR #52. `DEP-GMAIL-001` stays OPEN. ADR-0004 stays Proposed. This descendant cannot embed its own hash.

Item 26 proposal, 2026-10-26. Parent main `5e8d1628c472f420cc8f1ee7d18e6ffa2a1e7f8b`, tree `827fef7fe0b667ca4e0bcaca2cf4bf5a509f45e5`. Item 26 is not effective on this branch. When current-state item 26 is effective, Lane 2 may add only `src/swingtrade/alpaca_paper_boundary.py` and `tests/unit/test_alpaca_paper_boundary.py`. Until that activation, those paths must not be added. The module is an offline policy classifier with `connect_allowed` false. It is not an Alpaca connection, a paper order, or a live route. The Lane 2 table below remains the historical TradeStation attestation. Item 24 remains the integrated offline Alpaca classifier and is not rewritten. Item 25 remains the Gmail runtime-scan exclusion. This paragraph does not authorize an API key, a Windows credential call, a provider call, or integration of a future implementation pull request. All nine dependencies stay OPEN. ADR-0005 stays Proposed. ADR-0006 is not extended. This descendant cannot embed its own hash.

Item 27 proposal, 2026-11-12. Parent main `0c3d3d6714407f27ae2e0ff130b6e2590883e43f`, tree `3aedc40346d1062700220be95961fe56682c15ee`. Item 27 is not effective on this branch. When current-state item 27 is effective, Lane 3 may change only the Desktop JSON declaration check in `src/swingtrade/gmail_local_connect.py` and `tests/unit/test_gmail_local_connect.py`, and only to accept the exact declarations `http://localhost`, `http://localhost/`, and `https://accounts.google.com/o/oauth2/auth` without changing the approved runtime request. Until that activation, those files must not be edited for this purpose. The Lane 3 table below remains the historical attestation. This paragraph does not authorize a Gmail or Google call, a credential change, a rewrite of a downloaded client file, or integration of a future implementation pull request. Item 26 remains Lane 2's offline Alpaca boundary grant. Open draft PR #56 is not authorized or merged by this paragraph. All nine dependencies stay OPEN. ADR-0004 stays Proposed. This descendant cannot embed its own hash.

Item 28 proposal, 2026-11-12. Parent main `cb32938225783ce0677823cebb85943edfa88b36`, tree `d8ce6cea470243bb8eea1828ce03aad476cc692d`. Item 28 is not effective on this branch. When current-state item 28 is effective, Lane 3 may change only `src/swingtrade/group4_email/synthetic_acquisition.py`, `synthetic_ingestion.py`, `parse.py`, `extract.py`, `normalize.py`, `disposition.py`, and the six named tests `test_synthetic_acquisition.py`, `test_synthetic_ingestion.py`, `test_disposition_view.py`, `test_exit_policy_negation.py`, `test_remediation.py`, and `test_tday.py`. Until that activation, those files must not be edited for this purpose. No new file is granted. The Lane 3 table below remains the historical attestation. Item 27 remains the integrated Desktop JSON declaration grant and is not an instruction to call Gmail. This paragraph does not authorize a provider call, a credential change, a database change, or integration of a future implementation pull request. All nine dependencies stay OPEN. ADR-0004 stays Proposed. ADR-0006 is not extended. This descendant cannot embed its own hash.

Item 29 proposal, 2026-11-12. Parent main `0016b89b31a2d05c80c66e67962cf9ac20bbd437`, tree `48d2e01be375588d0c54c576efe905a5e6725900`. Item 29 is not effective on this branch. When current-state item 29 is effective, an attended Cursor Local Windows session may create only `postgresql-swingtrade-16` on `127.0.0.1` and a verified free port, with a new data directory, without changing `postgresql-x64-16` or port 5432. Until that activation, no cluster, service, role, or connection is authorized. The Lane 4 table below remains the historical attestation. Path A is not a fallback. All nine dependencies stay OPEN. ADR-0006 is not extended. This descendant cannot embed its own hash.

Item 30 proposal, 2026-11-12. Parent main `0016b89b31a2d05c80c66e67962cf9ac20bbd437`, tree `48d2e01be375588d0c54c576efe905a5e6725900`. Item 30 is not effective on this branch. When current-state item 30 is effective and item 29 Stage E and Stage F have passed for the new cluster, Lane 4 may add only `src/swingtrade/postgres_receipt_store.py`, `tests/integration/test_postgres_receipt_store.py`, and `migrations/versions/0004_instruction_receipts.py`. Until both of those gates are met, those paths must not be added. Sharing a commit with item 29 does not open them. This paragraph does not authorize a connection to port 5432 or integration of a future implementation pull request. All nine dependencies stay OPEN. ADR-0007 stays Accepted and is not widened. This descendant cannot embed its own hash.

PR #61 integration record, 2026-11-12. The two paragraphs above are the historical proposal text. Operative record: commit `a9333b5c92628981eacdf6ae091780dcd27313f5`, tree `17c04894d2385bfae153de41febafc048e799cbf`, is canonical main. Verifier `bc-e583af06-ed8e-51e0-b0a7-cdeb35881ef2` returned `INDEPENDENT_EXACT_TREE_PASS`. Operator decision `LANE1_PR61_ITEMS29_30_OPERATOR_INTEGRATION_AUTHORIZED` authorized the non-forced fast-forward. GitHub PR #61 is MERGED at `2026-11-12T21:43:06Z` with that merge commit. Item 29's attended Windows sequence is the effective infrastructure authority. Item 30 governance is effective and its three source paths stay closed until Stage E and Stage F are PASS. The Lane 4 table below remains the historical attestation. The Item 29 execution fields in the later correction are the step 19 status. All nine dependencies stay OPEN. This descendant cannot embed its own hash.

PR #60 integration record, 2026-11-13. Commit `dde81ba402a285b6d48e2f08b5e01bfb361f7f5b`, tree `6c9d108e02a5a94c8279cd844c39d15d9da13859`, is canonical main. Parents are `af08da047bc7a04b66c04d93e5c86fd9886f5933` and `4e1d7266c8d33bef64f039d66c74d3115a1659b9`. Verifier `bc-468d0867-1059-507d-a3dd-457148b23433` returned `INDEPENDENT_EXACT_TREE_PASS`. Operator decision `LANE1_PR60_CONDITIONAL_EXACT_COMMIT_INTEGRATION_AUTHORIZED` authorized the non-forced fast-forward. GitHub PR #60 is MERGED at `2026-11-13T13:31:30Z` with that merge commit. Lane 3 Milestone F is the integrated offline recovery classifier in `disposition.py` and `test_synthetic_ingestion.py`. It is not a Gmail call, an OAuth exchange, or durable receipt storage. `DEP-GMAIL-001` stays OPEN. The Lane 3 table below remains the historical attestation. Item 29 stages stay `NOT_RUN`. Item 30 source paths stay closed. All nine dependencies stay OPEN. This descendant cannot embed its own hash.

Items 31 and 32 proposal, 2026-11-13. Parent main `f4fda11c6132da4101698e04f980612bd6d8efd6`, tree `fabb5727eb513b9af8dc04750ff8c590c405fe68`. Neither item is effective on this branch. When item 31 is effective, Lane 3 may run one attended Windows `run_local_windows_profile_proof` against connector blob `0a6901a82512100aff41a0494fa185b154f55527`, metadata scope, one profile GET, and no token file. When item 32 is effective, Lane 3 may add only `gmail_readonly_pilot.py` and `test_gmail_readonly_pilot.py`. A live message read stays closed until that implementation is integrated and a separate Operator runtime decision names it. The Lane 3 table below remains the historical attestation. `DEP-GMAIL-001` stays OPEN. This descendant cannot embed its own hash.

PR #64 integration record, 2026-11-13. The proposal paragraph above is historical. Commit `885d0b405109285a4f44b2f48247b9e7c4ad7348`, tree `20e1d540b48234970ec60f1dc9a2de3fc7ca5c00`, sole parent `f4fda11c6132da4101698e04f980612bd6d8efd6`, is canonical main. Verifier `bc-82336778-602d-53dd-87a5-97e4efc1ff38` returned `INDEPENDENT_EXACT_TREE_PASS`. Operator decision `LANE1_PR64_ITEMS31_32_CONDITIONAL_INTEGRATION_AUTHORIZED` authorized the non-forced fast-forward. GitHub PR #64 is MERGED at `2026-11-13T14:03:34Z` with that merge commit. Item 31 is effective for one attended Windows metadata profile proof. Item 32 is effective for the two named files, and the live message read stays closed. This record does not delay the Item 31 Windows session. The Lane 3 table below remains the historical attestation. `DEP-GMAIL-001` stays OPEN. Item 29 stages stay `NOT_RUN`. Item 30 source paths stay closed. All nine dependencies stay OPEN. This descendant cannot embed its own hash.

Item 34 proposal, 2026-11-13. Parent main `3d49dbcdbb25ad1d39688323ea9b5f7948cf6ace`, tree `6f6de3380403cd6bcf430846d697520b1f804798`. Item 34 is not effective on this branch. When the four effectiveness conditions in current-state item 34 are met, including the later steps 18 and 19 record, Lane 3 may change only `validate_callback` in `src/swingtrade/group4_email/local_oauth_probe.py`, `tests/group4_email/test_local_oauth_probe.py`, and the two probe blob constants in `tests/unit/test_gmail_local_connect.py`. Until that activation, those files must not be edited for this purpose. The connector blob `0a6901a82512100aff41a0494fa185b154f55527` stays unchanged. Item 33 stays a separate open draft and is not amended here. PR #56 is not integrated by this paragraph. The Lane 3 table below remains the historical attestation. `DEP-GMAIL-001` stays OPEN. Item 29 stages stay `NOT_RUN`. Item 30 source paths stay closed. All nine dependencies stay OPEN. This descendant cannot embed its own hash.
Reconciliation note, 2026-11-13. The sentence above that says PR #56 is not integrated is authoring text. Canonical main `fb9ab787464bd05131c5ead2be8c5ef5bf552b53` contains that integration and the record below. The pass of `8d21fbaf5097873e265e44d25840a0697ade00b8` does not certify this merge. The Item 34 grant is unchanged.

PR #56 integration record, 2026-11-13. Commit `4d519730bb56ddf255fdda406caf014a66d558ca`, tree `63157384d1e0742c82e26cd8d22739c71b269478`, parents `c6c5ad000c874c9f192986470e2e301bc83bf5be` and `3d49dbcdbb25ad1d39688323ea9b5f7948cf6ace`, is canonical main. Verifier `bc-60651ea8-7488-59cb-8926-fe421d0a4bf0` returned `INDEPENDENT_EXACT_TREE_PASS`. Operator decision `LANE1_PR56_4D519730_CONDITIONAL_INTEGRATION_AUTHORIZED` authorized the non-forced fast-forward. GitHub PR #56 is MERGED at `2026-11-13T16:12:06Z` with that merge commit. The net change is the two Alpaca Gate C2 files at blobs `854e6adb5c1c2d20370f724d3a7e6d4f32970509` and `8e5d89ac0a3f33463d518e62ccaefdadcdf2cdd1`. All seven boundary permissions stay false. This is not Gate C3. The Lane 2 table below remains the historical attestation. `DEP-GMAIL-001` stays OPEN. Item 29 stages stay `NOT_RUN`. Item 30 source paths stay closed. All nine dependencies stay OPEN. This descendant cannot embed its own hash.

Item 35 proposal, 2026-11-13. Parent main `fb9ab787464bd05131c5ead2be8c5ef5bf552b53`, tree `8c079b9c81c325bebbe0dead8aa6fee1f85e685b`. Item 35 is `DRAFT` and is not effective on this branch. Gate C2 is implementation-complete, independently verified, integrated, and post-merge attested by the paragraph above. Item 26 sentences that call Item 26 inactive are authoring text. When Item 35 is `INDEPENDENTLY_VERIFIED`, `INTEGRATED`, and `POST_MERGE_ATTESTED` for the same commit, Lane 2 may add only `src/swingtrade/alpaca_paper_custody.py` and `tests/unit/test_alpaca_paper_custody.py`. Until that activation, those files must not be added. The module is an offline synthetic mock. It is not a provider call, a paper order, or a native Windows credential call. ADR-0006 is not extended. A separate Alpaca custody ADR remains required before any native credential access. Gate D stays closed. The Lane 2 table below remains the historical TradeStation attestation. PR #66 and PR #67 are not amended. All nine dependencies stay OPEN. ADR-0005 stays Proposed. This descendant cannot embed its own hash.
Reconciliation note, 2026-11-13. The sentence above that says PR #67 is not amended is authoring text. Canonical main `b0ce11e4fd0eaf37f84a8b2a9291fec9c76ee298` contains that integration and the Item 34 record below. Item 34 is effective. The pass of `f4d1638cbb401de4a85e00d7d53b3f70d231e1aa` does not certify this merge. The Item 35 grant is unchanged.

PR #67 integration record, 2026-11-13. The Item 34 proposal paragraph above is historical. Commit `fc01765af77d469fcaccca2ed570f987d4d1e892`, tree `abddf196bfe219a6b012dec3aa05fef0209c6951`, parents `8d21fbaf5097873e265e44d25840a0697ade00b8` and `fb9ab787464bd05131c5ead2be8c5ef5bf552b53`, is canonical main. Verifier `bc-dd8e2c0a-3a43-505b-8918-8da9563c878f` returned `INDEPENDENT_EXACT_TREE_PASS`. Operator decision `LANE1_PR67_ITEM34_EXACT_INTEGRATION_CONDITIONALLY_AUTHORIZED` authorized the non-forced fast-forward. GitHub PR #67 is MERGED at `2026-11-13T16:47:24Z` with that merge commit. The pass of `8d21fbaf5097873e265e44d25840a0697ade00b8` does not certify this merge. Item 34's implementation grant is effective for `validate_callback` in `src/swingtrade/group4_email/local_oauth_probe.py`, `tests/group4_email/test_local_oauth_probe.py`, and the two probe blob constants in `tests/unit/test_gmail_local_connect.py`. The connector blob `0a6901a82512100aff41a0494fa185b154f55527` stays unchanged. This record does not authorize a Windows OAuth attempt. Item 33 and PR #66 are not amended. The Lane 3 table below remains the historical attestation. `DEP-GMAIL-001` stays OPEN. Item 29 stages stay `NOT_RUN`. Item 30 source paths stay closed. All nine dependencies stay OPEN. This descendant cannot embed its own hash.

PR #69 integration record, 2026-11-13. The Item 35 proposal paragraph above is historical. Commit `182884702b419484c40348124e1b67f17d06b1eb`, tree `bf82dd4fa556a24fcf5883ae136c445a37368f87`, parents `f4d1638cbb401de4a85e00d7d53b3f70d231e1aa` and `b0ce11e4fd0eaf37f84a8b2a9291fec9c76ee298`, is canonical main. Verifier `bc-929dbcb3-9c2f-54f4-901c-57beab99a00d` returned `INDEPENDENT_EXACT_TREE_PASS`. Operator decision `LANE1_PR69_ITEM35_EXACT_INTEGRATION_AUTHORIZED` authorized the non-forced fast-forward. GitHub PR #69 is MERGED at `2026-11-13T17:08:58Z` with that merge commit. The pass of `f4d1638cbb401de4a85e00d7d53b3f70d231e1aa` does not certify this merge. Item 35's implementation grant is effective for `src/swingtrade/alpaca_paper_custody.py` and `tests/unit/test_alpaca_paper_custody.py`. The module is an offline synthetic mock. It is not a provider call or a native Windows credential call. Gate D stays closed. Item 34 stays effective. The Lane 2 table below remains the historical TradeStation attestation. Item 33 and PR #66 are not amended. All nine dependencies stay OPEN. ADR-0005 stays Proposed. This descendant cannot embed its own hash.

PR #71 integration record, 2026-11-13. Commit `142c07dfac520e84e1bb6ffcc7468256cce17b0e`, tree `8bd10be2ce286783e9956d2c2407f8b644b97907`, parents `7a3ed977a1661ec8fb5218afd5adb944701f6e3f` and `8efb264165fd992d62e68365784b1ed70eb6d48c`, is canonical main. Verifier `bc-f03012d9-881d-506c-b537-81b04be77878` returned `INDEPENDENT_EXACT_TREE_PASS`. The inaccessible identifier `026cb805-f912-41c5-8b75-d0087ddb9acc` is not controlling evidence. Operator decision `LANE1_PR71_FRESH_INDEPENDENT_EXACT_TREE_VERIFICATION_AUTHORIZED` commissioned that verifier, and Operator decision `LANE1_ITEM34_PR71_EXACT_INTEGRATION_AUTHORIZED` authorized the non-forced fast-forward. GitHub PR #71 is MERGED at `2026-11-13T17:48:43Z` with `mergeCommit.oid` equal to that SHA. The integrated blobs are probe `0337e979b9328ab7cb079b2e7aa06a15e6cd2080`, probe tests `4f405e88a840c63e7e84f3b34e803fc4a13a3a2b`, and connector tests `8ce471bdf2233be34cc57782e8a0fddf6626ba3e`. Connector blob `0a6901a82512100aff41a0494fa185b154f55527` and attack-test blob `14b911ba29f16161f179c272c2e2f5e1be50922e` stay unchanged. The corrected callback source is integrated. This record does not authorize a Windows OAuth attempt or a Gmail message read. Item 35 stays effective. Gate D stays closed. Item 33 and PR #66 are not amended. The Lane 3 table below remains the historical attestation. `DEP-GMAIL-001` stays OPEN. Item 29 stages stay `NOT_RUN`. Item 30 source paths stay closed. All nine dependencies stay OPEN. This descendant cannot embed its own hash.

PR #73 integration record, 2026-11-13. Commit `472db287f3d7ab62943d016217ac49c5a48a24cc`, tree `2d3d3e3d471861b74a3ef9f2eb2fff8625ba04c2`, parents `a64ad50bb0d8e48da68cf1e87a185053f018b8a7` and `ef88c609e8e4f15f136786257faa2368ea9893bd`, is canonical main. Verifier `bc-69bc8af0-87ee-5cc7-b267-20a52e50abd7` returned `INDEPENDENT_EXACT_TREE_PASS`. Operator decision `LANE1_PR73_RECONCILED_EXACT_INTEGRATION_AUTHORIZED` authorized the non-forced fast-forward. GitHub PR #73 is MERGED at `2026-11-13T18:35:25Z` with `mergeCommit.oid` equal to that SHA. The integrated blobs are custody `86ba61b5bfecc2ec203e36c099face0e15c4068d` and custody tests `81c0a9d5f1cbbd12d9fe8d9fb3bcf07423424a4c`. Gate C2 blobs `854e6adb5c1c2d20370f724d3a7e6d4f32970509` and `8e5d89ac0a3f33463d518e62ccaefdadcdf2cdd1` stay unchanged. The seven execution flags stay false. Gate C3 source is the integrated offline mock. It is not a provider call or a native Windows credential call. Gate D stays closed. Item 34 and PR #74 stay canonical. Item 33 and PR #66 are not amended. The Lane 2 table below remains the historical TradeStation attestation. All nine dependencies stay OPEN. ADR-0005 stays Proposed. This descendant cannot embed its own hash.

PR #76 integration record, 2026-11-13. Commit `4941dc0d30359710b4a7b6160eb874c261d1cf66`, tree `a2946b87449615c5aa33fa7adf29c6e0aed178f9`, sole parent `90ad6fb2f050d3728551e23fec65b17ca3a6705a`, is canonical main. Verifier `bc-1957ff23-21a9-582c-8198-d5f8cfa2d3a6` returned `INDEPENDENT_EXACT_TREE_PASS`. Operator decision `LANE1_ADR0008_PROPOSED_EXACT_INTEGRATION_AUTHORIZED` authorized the non-forced fast-forward. GitHub PR #76 is MERGED at `2026-11-13T18:51:45Z` with `mergeCommit.oid` equal to that SHA. The integrated blob is ADR-0008 `befca5bd775be9f4c1e4d09f8a08ae4584374b27`. ADR-0008 stays Proposed. Its Decision stays blank. Option A is not accepted. This record does not grant `src/swingtrade/alpaca_paper_account_probe.py` or `tests/unit/test_alpaca_paper_account_probe.py`. Gate D stays closed. Item 34, Item 35, PR #74, and PR #75 stay canonical. Item 33 and PR #66 are not amended. All nine dependencies stay OPEN. ADR-0004 and ADR-0005 stay Proposed. This descendant cannot embed its own hash.

ADR-0008 Option A and Gate D grant, 2026-11-13. Operator decision `LANE1_ADR0008_OPTION_A_ACCEPTANCE_AUTHORIZED` selects Option A. Operator decision `LANE1_ALPACA_GATE_D_TWO_FILE_PROBE_GRANT_AUTHORIZED` is separate and names only `src/swingtrade/alpaca_paper_account_probe.py` and `tests/unit/test_alpaca_paper_account_probe.py`. The grant is not effective until an independent verifier has passed this exact commit, an Operator decision has authorized integration of this exact commit, and this exact commit is canonical main. Lane 2 must not edit those files before then. The grant is offline synthetic development of one future `GET https://paper-api.alpaca.markets/v2/account`. It is not a provider call. The seven Gate C2 flags stay false. Item 33 and PR #66 are not amended. All nine dependencies stay OPEN. ADR-0004 and ADR-0005 stay Proposed. This descendant cannot embed its own hash.

PR #78 integration record, 2026-11-13. Commit `0890546d63eaa0e0e5b917675071bc662b1e2d50`, tree `0b17e98773a544a3fb11937fa2e2b7301a331161`, sole parent `9b18eaece2e16f44151da0d1afb0bbb4d654d519`, remains an ancestor. Verifier `bc-01d43b1b-f0ba-5297-bf15-2283bccc895a` returned `INDEPENDENT_EXACT_TREE_PASS`. Operator decision `LANE1_PR78_OPTION_A_AND_GATE_D_GRANT_EXACT_INTEGRATION_AUTHORIZED` authorized the non-forced fast-forward. GitHub PR #78 is MERGED at `2026-11-13T19:21:28Z` with `mergeCommit.oid` equal to that SHA. ADR-0008 is Accepted and Option A is selected. The two-file offline grant is effective. It does not authorize a credential read or a provider call. The seven Gate C2 flags stay false. Item 29 and Item 30 are not amended. Item 33 and PR #66 are not amended. Item 36 and Item 38 stay in force. All nine dependencies stay OPEN. ADR-0004 and ADR-0005 stay Proposed. This descendant cannot embed its own hash.
Item 36 Gmail three-attempt metadata grant, 2026-11-13. Parent main `0890546d63eaa0e0e5b917675071bc662b1e2d50`, tree `0b17e98773a544a3fb11937fa2e2b7301a331161`. Operator decision `LANE1_GMAIL_METADATA_RUNTIME_GRANT_RECONCILIATION_AUTHORIZED` authorizes this draft only. Item 36 is not effective. The future integration decision `LANE1_GMAIL_THREE_ATTEMPT_GRANT_EXACT_INTEGRATION_AUTHORIZED` and the future runtime decision `LANE1_GMAIL_THREE_ATTEMPT_METADATA_CAMPAIGN_AUTHORIZED` are not issued. The two Item 31 execution decisions stay spent. The new budget of three attempts is not authorized. The Lane 3 table below remains the historical attestation. Open draft PR #79 is not mixed into this paragraph. Item 32's live read stays closed. Item 33 and PR #66 are not amended. The Gate D offline grant is not amended. All nine dependencies stay OPEN. ADR-0004 and ADR-0005 stay Proposed. This descendant cannot embed its own hash.

PR #82 integration record, 2026-11-13. Commit `a06363231abb3fb8f0466da1ec79fff35ec28668`, tree `cbcb6e134197575af49ee64bf59c30c594e81645`, sole parent `0890546d63eaa0e0e5b917675071bc662b1e2d50`, is canonical main. Verifier `bc-9481fb1c-0259-5c37-8f96-26dede781fcb` returned `INDEPENDENT_EXACT_TREE_PASS`. Operator decision `LANE1_GMAIL_THREE_ATTEMPT_GRANT_EXACT_INTEGRATION_AUTHORIZED` authorized the non-forced fast-forward. GitHub PR #82 is MERGED at `2026-11-13T19:40:02Z` with `mergeCommit.oid` equal to that SHA. Item 36 is INTEGRATED and is not EFFECTIVE until this record is canonical main. The runtime decision is not issued. The two Item 31 execution decisions stay spent. The protected Gmail import-closure blobs stay unchanged. PR #79 stays pending. Open draft PR #81 proposes a different Item 36 for Stage E and is not amended. The offline Gate D grant stays effective for its two files. Item 33 and PR #66 are not amended. All nine dependencies stay OPEN. ADR-0004 and ADR-0005 stay Proposed. This descendant cannot embed its own hash.

PR #84 integration record, 2026-11-13. Commit `77b2e64f0ad83307758be138aa2d748accf2f7cf`, tree `18e7fa89524c72b9d3a475f0ecee76c7df4d96a4`, sole parent `0d571dec1d60e9e1c50ac2fb6593d100edc6e42c`, is canonical main. Verifier `bc-c6651348-cac2-507d-8bdb-84866d0a4690` returned `INDEPENDENT_EXACT_TREE_PASS`. Operator decision `LANE1_GMAIL_TOKEN_DIAGNOSTIC_GRANT_EXACT_INTEGRATION_AUTHORIZED` authorized the non-forced fast-forward. GitHub PR #84 is MERGED at `2026-11-13T20:27:22Z` with `mergeCommit.oid` equal to that SHA. Item 38 is INTEGRATED and is not EFFECTIVE until this record is canonical main. Lane 3 must not edit the three granted paths before then. Campaign `GMAIL-METADATA-CAMPAIGN-0D571DEC` stays stopped. Attempt 1 is consumed. Attempts 2 and 3 are unused and are not exercisable. Profile GET count stays 0. This record does not resume OAuth. Item 36 stays the campaign grant. Item 37 stays the open Stage E proposal. Item 32, Item 33, and PR #66 are not amended. All nine dependencies stay OPEN. ADR-0004 and ADR-0005 stay Proposed. This descendant cannot embed its own hash.

Item 38 Gmail token-diagnostic grant, 2026-11-13. Parent main `0d571dec1d60e9e1c50ac2fb6593d100edc6e42c`, tree `ab33d9172c7c4ed2583b7de9afc2499dbaa30abb`. Operator decision `LANE1_GMAIL_TOKEN_DIAGNOSTIC_GOVERNANCE_PREPARATION_AUTHORIZED` authorizes this draft only. Item 38 is not effective. The future integration decision `LANE1_GMAIL_TOKEN_DIAGNOSTIC_GRANT_EXACT_INTEGRATION_AUTHORIZED` is not issued. When the grant is later effective, Lane 3 may change only `src/swingtrade/gmail_local_connect.py`, `tests/unit/test_gmail_local_connect.py`, and the `_CODES` allowlist in `src/swingtrade/group4_email/local_oauth_probe.py`. The stopped campaign is not resumed. The missing-Content-Type theory is unsupported. Item 36 stays the campaign grant. Item 37 stays the open Stage E proposal. Item 32, Item 33, and PR #66 are not amended. The Lane 3 table below remains the historical attestation. All nine dependencies stay OPEN. ADR-0004 and ADR-0005 stay Proposed. This descendant cannot embed its own hash.

Item 39 Alembic target-guard grant, 2026-11-13. Parent main `bfcdec0c2a28a57bbbf373eb3b9bc854f9ae7744`, tree `459f72955cbe1114a9bba121836fa4c4386e5345`. This draft is not effective. Until it is verified, authorized, and canonical, Lane 4 must not edit `alembic.ini`, `migrations/env.py`, or `tests/unit/test_alembic_target_guard.py`. The future guard accepts only `127.0.0.1`, port `5433`, database `swingtrade_receipt_test`, role `swingtrade_migrator`, and system identifier `7707684291752896980`, and it fails closed without a same-connection identity proof. No migration, port 5432 connection, Stage F execution, or Item 30 edit is authorized. The reported Windows suite of 703 passed, 11 failed, 15 errors, and 111 skipped is not PASS. Open PR #81 is the separate Item 37 candidate and is not amended. All nine dependencies stay OPEN. ADR-0004 and ADR-0005 stay Proposed. This descendant cannot embed its own hash.

Item 39 is effective, 2026-11-13. Commit `e52ad5e6e40e228ffba20199707a6c39d7fd4f5e`, tree `40de41cca9dfad6c485270430b84d4c54dcae0e6`, sole parent `bfcdec0c2a28a57bbbf373eb3b9bc854f9ae7744`, is on canonical main. Verifier `bc-5a71318b-51be-512a-ae34-3638d620d2e2` returned `INDEPENDENT_EXACT_TREE_PASS`. Operator decision `LANE1_ITEM39_ALEMBIC_GUARD_GRANT_EXACT_INTEGRATION_AUTHORIZED` authorized the fast-forward. GitHub PR #87 is MERGED at `2026-11-13T21:11:03Z`. The three-file grant is effective. It does not authorize a migration. Item 37 stays inactive in this reconciliation. Stage E is not certified. All nine dependencies stay OPEN. ADR-0004 and ADR-0005 stay Proposed. This descendant cannot embed its own hash.

ADR-0009 proposal, 2026-11-14. Parent main `afc6b76ec679b269e89e5478c5a8bf938a0dad2e`, tree `acc32eec762c1789254bbfa2c1515b32413cff29`. ADR-0009 is Proposed and its Decision is blank. Lanes 2, 3, and 4 must not treat the proposed packages as authority. Layer D and Layer P are inactive. Existing effective grants stay in force. All nine dependencies stay OPEN. ADR-0004 and ADR-0005 stay Proposed. ADR-0008 stays Accepted and is not widened. This descendant cannot embed its own hash.

## Controlled states

Only these values are permitted for `Current state`:

`NOT_STARTED` · `READY` · `ACTIVE` · `WAITING_OPERATOR` · `WAITING_PROVIDER` ·
`BLOCKED` · `READY_FOR_VERIFICATION` · `VERIFIED` · `READY_FOR_INTEGRATION` ·
`INTEGRATED` · `SUPERSEDED`

Do not treat a Proposed ADR as Accepted. Do not treat passing tests as
integration approval. Do not treat provider confirmation as operational
certification.

## Lane 1 — Integration / Coordinator

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-1` |
| Workstream name | Integration / Coordinator |
| Current state | `INTEGRATED` |
| Current branch | `main` (PR #23 and checkpoint PR #25 history-preserving fast-forwards) |
| PR number | PR #23 (MERGED); checkpoint PR #25 (MERGED) |
| Last attested SHA | Governance FF tip `f5880cfcfaa6d994f369e04d73c844fd1402d74c`; attested main `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` |
| Last attested tree | Governance `1700b1b442ef72b31b24aa8dcdf65e43525376e4`; attested main `fc97582f22ebf2d24f132c9afe2720430b197f9f` |
| Canonical main baseline | `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` / `fc97582f22ebf2d24f132c9afe2720430b197f9f` |
| Current objective | Maintain four-lane registry, dependencies, and integration authority; coordinate specialists without implementing their features |
| Current blocker | None for governance presence on main; specialist blockers remain on their lanes |
| Next permitted action | Reconcile specialist handoffs; open/review DB draft PR when authorized; propose later integrations only after protocol gates |
| Next prohibited action | Implementing TradeStation, Gmail, or database specialist features; merging PR #22/#24/#19; treating merged PR #21 as OAuth or credential authority; authorizing credentials or LIVE |
| Contract dependencies | `DEP-CORE-001`, `DEP-CORE-002` (tracked; not owned as specialist work) |
| Certification status | Governance bootstrap integrated on main after independent PASS and Operator-authorized FF. Checkpoint PR #25 is integrated evidence, not a new specialist certification. |
| Integration eligibility | Already integrated |
| Last verification date | 2026-10-09 (identity reattestation of main `8cef3d7`) |
| Evidence references | PR https://github.com/agentAD25/swing-trading-automation/pull/23 MERGED; independent verifiers `bc-3289987e-ba29-5c68-a93e-fd3b27b71e9e` and `bc-e255e4a7-f783-5ef6-8fc3-f4cbd2d0d926`; specialist agents `bc-d4b7c1e4-6ba3-542d-abb3-54ba045f0f93`, `bc-f47aa4eb-faff-54ed-8dd0-9d738fab7bc4`, `bc-f38dad08-03c5-5ee8-9b28-8701f8b051f4` |

## Lane 2 — TradeStation / Broker

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-2` |
| Workstream name | TradeStation / Broker |
| Current state | `WAITING_PROVIDER` |
| Current branch | `cursor/p2-ts-provider-evidence-99c1` |
| PR number | Draft PR #22 |
| Last attested SHA | `330c47c40249fdf4e1f2a1bf3fa61e36e05ae4fc` |
| Last attested tree | `864f0c16891af03bce27b40a4d52b843bb444b5f` |
| Canonical main baseline | `8a17bec501df94238fe7588f84f7f1f51fee8baf` / `03d48c9ae453bdfc6a1cdf9cdc43a359e76efb1b` (merge-base `5a04c5eadd5b61dcf7153cc46fdf363c6ff8029d`; does not contain attested main; `CONFLICTING` on `docs/CURRENT_STATE.md` and `docs/ENGINEERING_JOURNAL.md`) |
| Current objective | Preserve the verified offline read-only parser and Proposed ADR-0005; keep key-specific provider questions open |
| Current blocker | `DEP-TS-002`, `DEP-TS-003`, and `DEP-TS-004` are `OPEN`. `DEP-TS-001` stays `OPEN` with recommended narrative `SUPERSEDED_BY_OPTION_A_PENDING_ARCHITECTURE_ACCEPTANCE` and is not provider-confirmed |
| Next permitted action | Lane 2 may merge current main into PR #22 without rewriting history. Do not accept ADR-0005. Do not close `DEP-TS-*` |
| Next prohibited action | TradeStation authentication; broker network calls; SIM/LIVE orders; credential onboarding; automatic merge; reconstructing or merging stale PR #19 |
| Contract dependencies | `DEP-TS-001`, `DEP-TS-002`, `DEP-TS-003`, `DEP-TS-004`, `DEP-CORE-001`, `DEP-CORE-002` |
| Certification status | Offline parser `src/` tree `4005e26d3744030efdefd61262b096a0f12de6fd` and `tests/` tree `d15d674a5f55e9e45bf4f41d4f6d162727a89274` match verified implementation `227db721944dc0a470046fdec4b60f581ff28d38` / `980ec01635c5e4eb0abec297fe8bbf37f12d18fa`. Independent verifier `bc-0a306c68-0d69-5aee-a999-736cff1a54d8`. Lane 1 compared those trees to PR #22 head `330c47c` on 2026-10-11 and found no `src/` or `tests/` delta. That inheritance does not certify later documentation commits, does not accept ADR-0005, and does not authorize a merge. |
| Integration eligibility | Not eligible. Shared-doc conflict with main `8a17bec`. ADR-0005 remains Proposed. Key-specific dependencies stay `OPEN`. No Operator merge authorization. |
| Last verification date | 2026-10-11 tree comparison of `src/` and `tests/` against `227db72`. Parser test execution remains the prior verifier's, not a new Lane 1 run. |
| Evidence references | https://github.com/agentAD25/swing-trading-automation/pull/22 ; verifier `bc-0a306c68-0d69-5aee-a999-736cff1a54d8`; ADR-0005 Proposed; PR #19 `SUPERSEDED` |

### Lane 2 status correction (2026-10-12)

The table above stays the 2026-10-11 attestation, including its historical next action to merge PR #22. Operative correction: the offline parser from merged PR #22 and the synthetic classifier from merged PR #38 are on canonical main. `DEP-TS-001` through `DEP-TS-004` stay `OPEN`. ADR-0005 stays Proposed with a blank Decision. This correction does not itself authorize a new module. When current-state item 19 is effective, its Lane 2 grant is the only additional Lane 2 implementation. Until that activation, Lane 2 must not add `order_report_sequence.py`.

### Historical TradeStation PR #19 (not an active lane tip)

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-2-HIST-19` |
| Workstream name | TradeStation pre-credential stop (historical) |
| Current state | `SUPERSEDED` |
| Current branch | `cursor/pre-credential-decision-3a31` |
| PR number | Draft PR #19 (OPEN, merge conflicts with `main`) |
| Last attested SHA | `bc6ab7ea92310ffa133b75b498f7f245af11f166` |
| Last attested tree | `4cd4768c34bf82a5bfb97189c38fbd79ae99fbcf` |
| Canonical main baseline | `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` / `fc97582f22ebf2d24f132c9afe2720430b197f9f` (merge-base `12e852c6d523a8fbfe2082a33887e36045ee04ae`; head unchanged) |
| Current objective | Preserve audit history only |
| Current blocker | ADR numbering conflicts with accepted ADR-0003 on `main`; PR is conflicting and pre-credential |
| Next permitted action | Leave open for audit or Operator-directed close; never auto-merge |
| Next prohibited action | Automatic merge; reconstruction into a new branch as if current; treating its ADR-0003 as authoritative |
| Contract dependencies | Superseded by Lane 2 active work and accepted ADR-0003 on `main` |
| Certification status | Not certified; do not integrate |
| Integration eligibility | Not eligible |
| Last verification date | 2026-10-09 identity reattestation (head unchanged; still OPEN and `CONFLICTING`) |
| Evidence references | https://github.com/agentAD25/swing-trading-automation/pull/19 ; accepted ADR-0003 on `main` remains Group 4A envelope/retention |

## Lane 3 — Gmail / Signal Ingestion

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-3` |
| Workstream name | Gmail / Signal Ingestion |
| Current state | `WAITING_OPERATOR` |
| Current branch | `main` (PR #21 history-preserving fast-forward of the Gate A proposal; ADR-0006 design acceptance is main `5a04c5e`) |
| PR number | PR #21 (MERGED 2026-10-09T15:49:31Z). PR #27 (MERGED 2026-10-10T15:19:28Z) carries the Accepted ADR-0006 design. |
| Last attested SHA | `5a04c5eadd5b61dcf7153cc46fdf363c6ff8029d` |
| Last attested tree | `38c29d18be5930bda628bc32947d484fccb860dc` |
| Canonical main baseline | `5a04c5eadd5b61dcf7153cc46fdf363c6ff8029d` / `38c29d18be5930bda628bc32947d484fccb860dc` |
| Current objective | Implement and test only the offline synthetic and mocked Gmail Windows Credential Manager adapter under Accepted ADR-0006 and current-state item 13. Do not start Gate B or OAuth. |
| Current blocker | `DEP-GMAIL-001` stays OPEN for Google OAuth. ADR-0004 stays Proposed. Those do not block the offline mocked adapter. |
| Next permitted action | On a new branch from canonical main, implement the offline adapter with synthetic values and mocked native API responses. Do not self-merge. Retain PR #21 history. |
| Next prohibited action | Real Credential Manager calls; unmocked `CredWriteW`, `CredReadW`, or `CredDeleteW`; real tokens; OAuth; Gmail API or mailbox access; TradeStation or TokenStore changes; remote database activity; deployment; `SIM`; `LIVE`; broker orders; Gate B; self-integration |
| Contract dependencies | `DEP-GMAIL-001`, `DEP-CORE-001`, `DEP-CORE-002` |
| Certification status | Gate A proposal text is on main. ADR-0006 design is Accepted. ADR-0004 remains Proposed. Offline adapter code is not yet present and is not certified. Offline Group 4A on `main` is separately `INTEGRATED` (see below). |
| Integration eligibility | The design acceptance is integrated. Adapter implementation is not eligible for integration until a later authorized gate. |
| Last verification date | 2026-10-09. Pre-merge verifier `bc-c3ebf977-b66a-5fac-80ac-93c7416edf31` returned `LANE3_RECONCILE_VERIFY_PASS` on this exact SHA before the fast-forward. That result was not copied into the journal at integration time. |
| Evidence references | https://github.com/agentAD25/swing-trading-automation/pull/21 MERGED; parents `a2cef6f3527b2aab7319a2628874fcdcaf03acac` and `7c33d45c0a057d189ad6c5acc288625d57539413`; ADR-0004 Proposed; `DEP-GMAIL-001` OPEN |

### Offline Group 4A (canonical, already on main)

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-3-G4A` |
| Workstream name | Offline email instruction contract (Group 4A) |
| Current state | `INTEGRATED` |
| Current branch | `main` (via merged PR #20 lineage) |
| PR number | PR #20 (MERGED; fast-forward evidence on main) |
| Last attested SHA | Certified implementation `ce045c14b119d882505a947a7826005ff6d99103`; attested main `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` |
| Last attested tree | Certified `67a0b57526ea219972fa0574b191562f0f52b598`; attested main `fc97582f22ebf2d24f132c9afe2720430b197f9f` |
| Canonical main baseline | `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` / `fc97582f22ebf2d24f132c9afe2720430b197f9f` |
| Current objective | Preserve integrated offline parser; no Gmail authority |
| Current blocker | Quantity rounding, market calendar, and timezone remain unresolved (`DEP-CORE-001`, `DEP-CORE-002`) |
| Next permitted action | Consume as canonical offline contract; Gmail work stays on Lane 3 PR #21 |
| Next prohibited action | Inferring Gmail, broker, credential, Supabase, order, SIM, or `LIVE` authority from this integration |
| Contract dependencies | `DEP-CORE-001`, `DEP-CORE-002` |
| Certification status | `INTEGRATED_AND_CERTIFIED` for offline Group 4A only; ADR-0003 Accepted |
| Integration eligibility | Already integrated |
| Last verification date | 2026-10-05 (recorded on main); re-attested 2026-10-08 |
| Evidence references | `docs/CURRENT_STATE.md`; ADR-0003 Accepted; PR #20 |

## Lane 4 — Database / PostgreSQL Infrastructure

| Field | Value |
| --- | --- |
| Lane identifier | `LANE-4` |
| Workstream name | Database / PostgreSQL Infrastructure |
| Current state | `READY_FOR_VERIFICATION` |
| Current branch | Review target `cursor/db-dep-db-002-verify-c385` (contains ancestor `cursor/db-zero-cost-bootstrap-51f4`) |
| PR number | Draft PR #24 (do not open a second PR from the older tip) |
| Last attested SHA | `d491c3434872fac88b1c5be28281dce94ea11a8b` (parents `5e748ad9b5738c5fe8b1ea02f96cde2d677c102f` and attested main `8cef3d7`) |
| Last attested tree | `ac228e7342c8f75868cc0a683920e26d75cea31f` |
| Canonical main baseline | `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` / `fc97582f22ebf2d24f132c9afe2720430b197f9f` (PR tip contains this attested main) |
| Current objective | Preserve zero-cost research and independent local TokenStore PostgreSQL evidence. When current-state item 17 is effective, Lane 4 may implement only the bounded `PostgresIntentRepository.create_or_get` change and synthetic persistence tests. PR #24 is not certified. |
| Current blocker | `DEP-DB-001` OPEN (Supabase/Neon Free **NOT_ACCEPTED**). `DEP-DB-002` stays OPEN. Those open dependencies do not prohibit the item 17 implementation. |
| Next permitted action | When item 17 is effective, implement only that boundary with synthetic URLs and injected failures. Do not merge PR #24. Do not open a real database connection. |
| Next prohibited action | Set `READY_FOR_INTEGRATION`; close `DEP-DB-002` from verifier PASS alone; Supabase/Neon connection; paid provisioning; self-integration; LIVE |
| Contract dependencies | `DEP-DB-001`, `DEP-DB-002` |
| Certification status | Independent verifier PASS for twelve local nodes applies only to executable `src/` and `tests/` bytes of `d949ce0197bc51ceef0b627eea325e9c4d13aaaf`. Those paths, plus `migrations/`, `pyproject.toml`, and `docker-compose.yml`, are identical at PR #24 tip `d491c34`. Docs commits `5e748ad` and `d491c34` are outside that PASS. Not Operator-accepted certification. Not integration approval. |
| Integration eligibility | Not eligible. Fresh independent verification of tip `d491c34` is `NOT_RUN`. |
| Last verification date | 2026-10-09 identity reattestation. Executable-byte PASS remains 2026-10-08 (`bc-6040b738-314c-499a-96c2-7383ac84c385`). |
| Evidence references | Draft PR #24; `docs/LANE4_DEP_DB_002_INDEPENDENT_VERIFICATION.md`; token `LANE4_DEP_DB_002_INDEPENDENT_PASS` for unchanged executable bytes; certification-packet docs are not closed evidence |

### Lane 4 Item 29 execution status (2026-11-12)

The table above stays the historical PR #24 attestation. This correction is Integration Protocol step 19 for merged PR #61. It does not certify infrastructure that has not run.

| Field | Value |
| --- | --- |
| Governance authorization | PR #61 commit `a9333b5c92628981eacdf6ae091780dcd27313f5`, tree `17c04894d2385bfae153de41febafc048e799cbf`, is on canonical main. Verifier `bc-e583af06-ed8e-51e0-b0a7-cdeb35881ef2` returned `INDEPENDENT_EXACT_TREE_PASS`. Operator decision `LANE1_PR61_ITEMS29_30_OPERATOR_INTEGRATION_AUTHORIZED` authorized the fast-forward. GitHub state `MERGED`, `mergedAt` `2026-11-12T21:43:06Z`. |
| Infrastructure execution state | `NOT_STARTED`. No `postgresql-swingtrade-16` service is claimed to exist. |
| Stage A protected baseline | `NOT_RUN` |
| Stage B service identity | `NOT_RUN` |
| Stage C cluster initialization | `NOT_RUN` |
| Stage D roles and databases | `NOT_RUN` |
| Stage E security certification | `NOT_RUN` |
| Stage F isolated test certification | `NOT_RUN` |
| Item 30 implementation eligibility | `CLOSED`. Governance text is effective. The three source paths stay closed until Stage E and Stage F are `PASS` for the same new cluster. |
| Current state for this execution track | `READY` for the attended Item 29 Windows sequence after this record is the canonical text. The historical table value `READY_FOR_VERIFICATION` remains the PR #24 attestation. |
| Certification status | Governance integration of PR #61 is recorded. Security and test certification are `NOT_RUN`. |
| Next permitted action | After this record is on canonical main, an attended Cursor Local session may begin Item 29 Stage A. A local checkout behind main fast-forwards with a non-destructive fetch. |
| Next prohibited action | Connecting to port 5432, changing `postgresql-x64-16`, applying revision 0004, creating the three Item 30 files, or recording Stage E or Stage F as `PASS` before those stages run. |

## Baseline difference classification

| Claimed/prior baseline | Attested GitHub `main` | Classification |
| --- | --- | --- |
| Pre-integration SHA `41218abb2eda5f06001703fb83c2cb9e43e5ec2e` | Superseded by FF of PR #23 | `SUPERSEDED_BY_AUTHORIZED_INTEGRATION` |
| Governance FF tip `f5880cfcfaa6d994f369e04d73c844fd1402d74c` | Ancestor of current main | `GOVERNANCE_FF_TIP` |
| Prior registry tip `24466ab9e551c6bb13dc1af67c6b33f148ac854a` | Ancestor of attested main | `SUPERSEDED_BY_REGISTRY_COMMIT` |
| Checkpoint main `af0d69b1dfc2046899db05a2f12767fc20b623ae` | Ancestor of attested main (PR #25) | `SUPERSEDED_BY_CHECKPOINT_INTEGRATION` |
| Attested main `8cef3d7fe3fa57ec5138e64fc96ee2dbeb0f3829` | Identical to `origin/main` on 2026-10-09 | `BASELINE_MATCH` |
| Attested main tree `fc97582f22ebf2d24f132c9afe2720430b197f9f` | Identical | `BASELINE_MATCH` |

PR #23 was integrated by history-preserving fast-forward. Specialist PR #21/#22
branches predate the governance tip and were not rewritten. Lane 4 research
branch `cursor/db-zero-cost-bootstrap-51f4` is not integrated. Unexpected
future divergence must be classified, never overwritten or reset.

## Coordination checkpoint (identity refreshed 2026-10-09)

The 2026-10-08 checkpoint narrative remains in `docs/ENGINEERING_JOURNAL.md`.
This section records current integration-readiness conditions. It does not merge
specialist work and does not close dependencies.

### Specialist compatibility with attested main `8cef3d7`

| Lane | Tip | Contains attested main? | GitHub merge state | Conflicting paths |
| --- | --- | --- | --- | --- |
| LANE-2 PR #22 | `16aa5788a17ac77291530bb836af256a6f79f89f` | No (merge-base `af0d69b`) | `CONFLICTING` / `DIRTY` | `docs/CURRENT_STATE.md`, `docs/ENGINEERING_JOURNAL.md` |
| LANE-3 PR #21 | `2c895291a3b4282f8cf5c7426c705bfdab365c47` | Yes (this commit is main) | MERGED 2026-10-09T15:49:31Z | None. The earlier `a2cef6f` conflict row is historical. |
| LANE-4 PR #24 | `d491c3434872fac88b1c5be28281dce94ea11a8b` | Yes (contains `8cef3d7`) | `MERGEABLE` / `CLEAN` | None versus attested main. Older tips `d949ce0` and `db570fa` remain ancestors and are not a second PR. |
| LANE-2-HIST-19 | `bc6ab7ea92310ffa133b75b498f7f245af11f166` | No (merge-base `12e852c6`) | OPEN / `CONFLICTING` / superseded | Do not reconcile as current authority |

Non-conflicting specialist additions on PR #21: `docs/GMAIL_READONLY_CORPUS_GATE.md`, Proposed ADR-0004. On PR #22: broker/auth evidence docs and Proposed ADR-0005. Those files are not the conflict set.

### Reconciliation instructions (specialist owners; Lane 1 does not edit those branches here)

1. Start from a fresh worktree of the existing branch. Do not recreate the branch and do not force-push.
2. Rebase or merge is **not** automatic. Prefer a new descendant commit that merges attested `main` (`8cef3d7`) and resolves only shared-file conflicts. A descendant of this registry commit is a later main and needs the same merge.
3. For `docs/CURRENT_STATE.md` and `docs/ENGINEERING_JOURNAL.md`, keep canonical main governance text and append the specialist evidence. Do not drop ADR-0003 Accepted, four-lane registry facts, or `DRY_RUN` / `LIVE` unauthorized statements.
4. Do not accept ADR-0004 or ADR-0005 during reconciliation.
5. Do not mark `DEP-*` resolved.
6. After reconciliation, request independent verification of the new SHA/tree before any integration proposal.
7. The pre-PR #24 sentence that Lane 4 still lacked a distinct verifier is superseded for execution evidence only. Draft PR #24 already records independent PASS `LANE4_DEP_DB_002_INDEPENDENT_PASS`. That PASS does not close `DEP-DB-002` and does not make the lane integration-eligible.

### Lane 4 draft PR eligibility

Draft PR #24 already exists and is the review target. Do not create a replacement PR. Integration remains `NOT_ELIGIBLE`:

- Independent local execution is **PASS** (12 passed, 32 deselected; unset URL: 12 skipped). It applies to executable `src/` and `tests/` bytes of `d949ce0`. Those bytes, plus `migrations/`, `pyproject.toml`, and `docker-compose.yml`, are unchanged at tip `d491c34`. Docs commits `5e748ad` and `d491c34` are outside that PASS. Fresh verification of tip `d491c34` is `NOT_RUN`.
- `DEP-DB-002` stays OPEN. Verifier PASS is not Operator-accepted certification.
- `DEP-DB-001` stays OPEN. Supabase and Neon Free stay **NOT_ACCEPTED**.
- State stays `READY_FOR_VERIFICATION`, not `READY_FOR_INTEGRATION`.

### Recommended future integration sequence

Preconditions apply before each step. No step authorizes credentials, SIM, or `LIVE`.

1. Keep governance on `main` (already integrated). Do not re-merge PR #23.
2. Lane 4 draft PR #24 may be integrated only after a later explicit authorization, dependency review, and a fresh shared-doc reconcile if main moves. Independent PASS does not authorize that merge in this task. Provider selection stays closed.
3. Lane 3 Gate A proposal text is already on main at `2c89529`. ADR-0004 stays Proposed. `DEP-GMAIL-001` stays open. That merge does not start Gate B, OAuth, or a credential module.
4. Lane 2 PR #22 stays not eligible. The offline parser bytes at head `330c47c` match verified implementation `227db72`, and that match is not merge authorization. Integration still requires a normal merge of current main, preservation of `DRY_RUN`-only text, an explicit Operator integration decision, and either closure or an explicit Operator waiver of each open `DEP-TS-*` that the integration protocol treats as blocking for that merge. ADR-0005 stays Proposed until a separate Operator acceptance. `DEP-TS-001` is not superseded by the Option A preference.
5. `DEP-CORE-001` and `DEP-CORE-002` before any economic quantity, calendar, or timezone acceptance. They do not block docs-only conflict reconciliation.

### Acceptance gate vocabulary for future specialist integration

Use `PASS`, `FAIL`, `BLOCKED`, `SKIPPED`, or `NOT_RUN`. Skipped tests are not passes.

| Gate | LANE-2 PR #22 | LANE-3 PR #21 | LANE-4 research |
| --- | --- | --- | --- |
| Branch identity attested | PASS | PASS | PASS |
| Contains attested main `8cef3d7` | FAIL | FAIL | PASS (PR #24 tip `d491c34`) |
| Exact SHA/tree attested | PASS (`16aa578` / `74ce64cb`) | PASS (`a2cef6f` / `557b4c93`; unchanged) | PASS (`d491c34` / `ac228e73`) |
| Governance compliance (no LIVE/auth) | PASS (fail-closed deny language in the intake diff; not certification) | PASS (docs inspection of unchanged head) | PASS (research text; packet docs not certified) |
| Scope isolation | PASS (docs and fail-closed boundary diff) | PASS (docs) | PASS (docs) |
| Shared-file compatibility vs `8cef3d7` | BLOCKED | BLOCKED | PASS vs attested main; re-merge required if a descendant advances main |
| Dependency closure | BLOCKED (`DEP-TS-001`) | BLOCKED (`DEP-GMAIL-001`) | BLOCKED (`DEP-DB-001` OPEN; `DEP-DB-002` OPEN despite local executable-byte PASS) |
| Independent verification of tip | NOT_RUN for `16aa578` (continuity PASS does not transfer from `a6c5f1d`) | NOT_RUN for post-main reconcile | PASS for twelve local nodes on unchanged `src/`/`tests/`; `NOT_RUN` for docs commits `5e748ad` and `d491c34`; not certification closure |
| Automated tests | NOT_RUN this audit | NOT_RUN this audit | Prior verifier: 161 passed offline+contracts; 0 skips in that run. Not rerun here. |
| PostgreSQL-backed tests | NOT_RUN | NOT_RUN | Prior PASS 12 / deselected 32 on unchanged executable bytes; unset URL SKIPPED 12 (not passes). Not rerun here. |
| Secret/credential handling | PASS (no new secrets observed) | PASS | PASS (fixture URL only in research text) |
| Regression vs main | NOT_RUN | NOT_RUN | NOT_RUN |
| Merge readiness | BLOCKED | BLOCKED | BLOCKED |

### Local isolation note

Local checkouts observed on 2026-10-09 and not rewritten: `/workspace/.worktrees/lane2-ts` detached at `a6c5f1d` (not PR #22 tip `16aa578`); `lane3-gmail` detached at PR #21 tip `a2cef6f`; `lane4-db` on local `cursor/db-zero-cost-bootstrap-8992` at `24466ab`, which is not PR #24 tip `d491c34`. Do not treat those checkouts as the remote PR tips.

## ChatGPT advisory version audit (2026-10-09)

Accepted repository governance remains authoritative. This audit does not copy ChatGPT advisory files into Git and does not install them as Cursor rules.

Uploads inspected in this session are references, not active configuration:

| File role | Declared version | SHA-256 | Classification |
| --- | --- | --- | --- |
| Governance upload | 1.1.0 | `44267e30691d4f73dcbb7440c0111e2ecc2a6c4e46fd1c854489076e86cbc026` | `CURRENT_CHATGPT_ADVISORY_V1_1` uploaded reference |
| Instructions upload | 1.1 | `b6223d1ac067eb55d47fb37786b861b5b756c898666a58eab72d82193f9a237b` | `CURRENT_CHATGPT_ADVISORY_V1_1` uploaded reference |
| Governance upload | 1.0.0 | `61db48cdfc058ea4f7e7562ddfbab0748ec79fa01e3bbb675c379c747066dbc9` | `SUPERSEDED_CHATGPT_ADVISORY` historical reference |
| Instructions upload | 1.0 | `b3b7b3d1e5d75d87e815cda7660811a04d51dc00c0eed889ade67180cec6f5b7` | `SUPERSEDED_CHATGPT_ADVISORY` historical reference |

No `SWING_TRADING_PROJECT_GOVERNANCE.md` or `CHATGPT_PROJECT_INSTRUCTIONS.txt` blob exists on attested main or on PR #19, #21, #22, or #24 tips. Active `.cursor/rules/` and `.cursor/agents/` on attested main do not embed v1.0 advisory text. Prior semantic decision `CHATGPT_GOVERNANCE_COMPATIBLE_NO_REPO_CHANGE` is compatibility evidence for the inspected v1.1 text. ChatGPT Project settings and other Cursor Cloud VMs are `NOT_INSPECTABLE` from this session.
