# Bound Protocol

Fix the practical margin and missing-row policy **before observations**, together
with the complete Frozen Benchmark plan. Roster Bounds' legacy plan pin does
not cover those two settings. This outer protocol does, and its checker has no
runtime override for either. Python 3.10+, standard library only; copy this
whole directory to use it offline without sibling folders or installation.

One command from the repository root shows it working:

```sh
python3 -B line-1/tools/bound-protocol/bound_protocol.py demo
```

When tried locally, the synthetic demo pinned margin `0.1` and
`restore-as-unknown`, restored the omitted `unicode` case, retained all three
cases and both candidates, and reported four unknown cells. Replacing either
the margin or policy and recomputing the internal digest failed against the
original external pin. Neither candidate established a criterion. The actual
stdout is retained in `example-result.json`. These are illustrative outcomes,
not execution evidence or measured system improvements.

## Freeze before measuring

Start with an existing Frozen Benchmark v1 manifest and independently retained
plan SHA-256. Its embedded schema and implementation are in `frozen_engine.py`.
The plan contains baseline version, full candidate family, case IDs, alpha and
pass rule. The following uppercase tokens mean your actual workspace-relative
paths and retained digests; they are not executable example values:

```sh
python3 -B line-1/tools/bound-protocol/bound_protocol.py freeze --manifest MANIFEST.json --expected-plan-sha256 RETAINED_PLAN_SHA256 --margin 0.1 --omission-policy reject
```

Choose the margin prospectively as an absolute pass-rate difference (0.1 means
ten percentage points). It accepts decimal strings from 0 through 1, at most
nine fractional places. **Both settings are required**, with no implicit choice.
Omission policy is one of:

* `reject`: every planned case row must be supplied. Explicit `?` cells are
  still allowed. This policy rejects omitted rows, not unknown outcomes.
* `restore-as-unknown`: every missing planned row is restored with `?` for the
  baseline and every candidate, with IDs and counts retained in the report.

Save stdout as a new protocol file, and retain its `protocol_sha256`
**independently before collecting outcomes**. Also preserve the complete file.
The pin covers a canonical object containing the whole normalized manifest,
normalized margin and policy. Canonical JSON sorts keys, uses compact separators
and ASCII escapes, and ends with LF. Numerically equal decimal representations
normalize identically; whitespace/key ordering do not alter the semantic pin.
Observed-file and protocol-byte hashes separately identify original raw bytes.

Changing case/family/pass rule/alpha, margin or policy changes the outer pin.
The old plan pin alone is insufficient for these new settings. No hash proves
that a declaration was made before outcomes: that requires your independent
retention/publication process. Do not choose a fresh pin after viewing results.

## Analyze once at the fixed endpoint

Use UTF-8 CSV headed `case,baseline` and then every planned candidate in its
original order. Each outcome is literal `0`, `1` or `?`. Rows may be reordered;
CSV-quote labels as needed. Pin the raw observation bytes independently at
handoff, then run:

```sh
python3 -B line-1/tools/bound-protocol/bound_protocol.py check --protocol PROTOCOL.json --results RESULTS.csv --expected-protocol-sha256 RETAINED_PROTOCOL_SHA256 --expected-results-sha256 RETAINED_RESULTS_SHA256
```

The report retains the outer pin, actual byte hashes, bound settings and the
complete original Roster Bounds report. Its nested `analysis` separates sample
identification intervals from population confidence intervals and retains exact
rational endpoints and criterion flags. Alpha, margin, family and restoration
behavior all come from the verified protocol. No margin/policy CLI override is
accepted. The nested legacy margin warning concerns its inner plan pin only;
the outer protocol additionally covers that setting.

Append `--emit-csv` to print only the fully admitted normalized CSV. It is emitted
only after checking and analysis finish. Its hash agrees with
`roster_report.normalized_csv_sha256` and the nested analysis's `input_sha256`.
Keep the original inputs and report too. Exit 0 means valid analysis, including
inconclusive results; exit 2 means invalid input, with stderr and empty stdout.
Never reuse stale redirected output after failure or overwrite input files.

## Boundaries

This is a declaration and admission layer using the unchanged conservative
Missing Bounds engine, not a new statistical method. No missing-at-random
assumption is made; unknowns remain unknown and all binary completions are
enclosed. A fixed final sample size, latent iid case vectors, prospective full
family/pass rule/alpha/margin and accurate observed scoring remain assumptions.
Do not repeatedly analyze a filling table to decide when to stop. Curated test
cases alone do not establish population performance. Non-establishment is
inconclusive, not equivalence or permission to deploy.

The manifest binds IDs and labels, **not payloads or executable bytes**. Preserve
those separately, for example with Benchmark Seal. This wrapper does not verify
execution, sampling, honest scoring, publication time, loaded source identity
or absence of selective reporting. A pin supplied by the same untrusted source
as the data authenticates nothing. It is not a signature, attestation or sandbox.

Limits: 1–512 planned cases, 2–16 candidates, case/candidate labels 1–200
characters without category-C text or edge whitespace, original baseline/pass
rule limits 256/8,192 characters, alpha 0.000001–0.2 with up to 18 decimal places.
Inputs are at most 2 MiB each and must resolve to regular files inside the
current workspace, including through symlinks. Duplicate JSON members, unknown
keys, nonfinite values, candidate omission/reordering, extra/duplicate cases and
invalid cells fail. File containment is not protection from concurrent path
changes. The CLI writes stdout only; it does not execute input, access
environment variables, use network, wallets, keys, payments or transactions.
This offline comparison needs no coin, price or pool.

## Local checks and reuse

```sh
python3 -B -m unittest discover -s line-1/tools/bound-protocol -v
```

All ten tests passed: replacement margin/policy/plan/alpha rejection; a pinned
margin actually changing the criterion; policy enforcement; every omission
subset matching the original engine; exact long-decimal alpha; canonical margin;
schema/number/pin/family/limits rejection; snapshot hashes; and a copied-folder
CLI checking freeze, analysis, CSV, forbidden overrides, path containment and no
partial stdout. Tests use only `test/scratch/` for temporary fixtures. The eleven
unchanged Roster Bounds predecessor tests also pass. These are local checks,
not independent certification. Four ordinary-file snapshots from Roster Bounds
are unchanged and pinned in `provenance.json`; earlier tools remain untouched.
