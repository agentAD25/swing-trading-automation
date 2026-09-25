# Tests

No implementation or test framework has been selected. The proposed coverage
is in [`docs/TEST_PLAN.md`](../docs/TEST_PLAN.md).

`fixtures/wdc-reference/` is deterministic, synthetic architecture-conformance
data. It does not contain historical market observations or a production
strategy.

Future tests must run without brokerage credentials, real accounts, broker
network access, or live order submission. Safety-boundary tests must fail
closed.
