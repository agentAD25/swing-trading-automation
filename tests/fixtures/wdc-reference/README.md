# Deterministic WDC Reference Fixture

This is synthetic conformance data labeled `WDC` solely to provide a stable,
recognizable instrument key. Prices, volumes, dates, decisions, and results are
invented. They are not historical WDC observations, investment advice, a
strategy recommendation, or evidence of efficacy.

## Contract

- `bars.csv` contains five synthetic daily bars in ascending session order.
- `scenario.json` fixes schema, clock, ids, mechanical test rule, and
  assumptions.
- `expected-events.jsonl` contains one canonical JSON object per line.
- `expected-report.json` is canonical JSON with no trailing whitespace except
  one final newline.
- `manifest.json` supplies SHA-256 digests for all four files.

The test-only rule enters two units at the next bar open after the first bar
whose close is above its open, then exits at the open of the third session
after the signal session. It exists only to force an intent, two fills, an open
trade, and an exactly flat close. No production or research strategy may
import or cite this rule.

The fixture assumes zero fees and exact fills because it tests data/event/report
wiring, not execution realism. No TradeStation behavior is represented.

## Expected arithmetic

- Entry: `2 × 51.0000`
- Exit: `2 × 55.0000`
- Ending quantity: `0`
- Synthetic realized difference before costs: `8.0000 USD`
- Reconciliation: `PASS`

## Verification

From the repository root, verify bytes using only Python's standard library:

```sh
python - <<'PY'
import hashlib, json, pathlib
root = pathlib.Path("tests/fixtures/wdc-reference")
manifest = json.loads((root / "manifest.json").read_text())
for name, expected in manifest["sha256"].items():
    actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
    assert actual == expected, (name, actual, expected)
print("fixture digests: PASS")
PY
```

The conformance procedure in `docs/TEST_PLAN.md` additionally requires
byte-identical events/report, the fixed clock, and zero network access.
