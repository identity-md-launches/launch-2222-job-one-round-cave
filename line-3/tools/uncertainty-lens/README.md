# Uncertainty Lens

Uncertainty Lens turns a small JSON array of timestamp intervals into a reproducible summary of definite pairwise order and unresolved overlaps. It is a local, read-only incident-evidence helper using only Python's standard library. It never runs the services described by the events.

From the repository root, run this one command:

```sh
printf '%s\n' '[{"id":"ingest","start":1,"end":3},{"id":"alert","start":3,"end":4},{"id":"retry","start":2,"end":5}]' | python3 -B line-3/tools/uncertainty-lens/uncertainty_lens.py
```

Tried locally: it reported `ingest` before `alert`, and the two pairs involving `retry` as uncertain. Fifteen focused tests passed, including CLI rejection of nonfinite JSON numbers, oversized input and paths escaping the workspace, all 100 pairs of small integer intervals in both input orders, and 500 seeded decimal interval pairs checked against an independent Fraction oracle. No real incident or measured clock error is claimed.

Input is a JSON array of objects with a unique, nonempty string `id` and finite, nonboolean numeric `start` and `end`, with `start <= end`. Nonzero intervals are half-open: an end exactly equal to another start gives definite order. A zero-width interval represents an exact timestamp point. Two coincident points remain unresolved with reason `coincident timestamp points`, independent of input order. Distinct points remain ordered; a point inside a nonzero interval remains unresolved. Overlap or coincident readings do not establish simultaneity or causality. Extra object fields are ignored.

The CLI accepts stdin by default or a JSON file path **inside the current working directory**, treated as the workspace root. Absolute paths, `..` paths and symlinks are resolved and rejected before opening if they escape that root. Run from your selected evidence workspace; this path check is not an OS sandbox against concurrent symlink changes. The CLI reads at most 256 KiB and accepts at most 128 events, bounding the report to 8,128 pairs. Malformed input, duplicate IDs, booleans, NaN and infinities fail with an error instead of producing an order claim. The CLI parses JSON number text directly into exact standard-library Decimal values, including integer and exponent notation. Comparisons do not round to binary floats or use context-rounded arithmetic. Each numeric token is limited to 256 characters and its stored decimal exponent to +/-10,000; these limits apply even to ignored fields. Numeric strings remain invalid endpoints. The Python API also accepts finite Decimal, integer and float values; floats supplied by a caller retain any rounding that already occurred. This tool cannot recover precision lost before input, measure clock accuracy, or establish causality.

Try the fixed coincident-point case:

```sh
printf '%s\n' '[{"id":"ingest","start":3,"end":3},{"id":"alert","start":3,"end":3}]' | python3 -B line-3/tools/uncertainty-lens/uncertainty_lens.py
```

Observed: zero definite orders and one unresolved pair, rather than an input-order-dependent claim. To repeat the checks:

```sh
python3 -B -m unittest discover -s line-3/tools/uncertainty-lens -v
```

Round 37 precision regression (synthetic, one command from the repository root):

```sh
printf '%s\n' '[{"id":"a","start":0,"end":1.00000000000000003},{"id":"b","start":1.00000000000000002,"end":2}]' | python3 -B line-3/tools/uncertainty-lens/uncertainty_lens.py
```

Observed: zero definite orders and one `intervals overlap` pair. The old binary-float JSON parser rounded both internal endpoints to 1 and falsely reported a before b. Exact decimal parsing also preserves distinct points at 1e-4000 and 2e-4000, and accepts large finite decimal exponents without converting them to infinity. The original demos and all predecessor regressions still pass. No network, coin, account or service is needed.
