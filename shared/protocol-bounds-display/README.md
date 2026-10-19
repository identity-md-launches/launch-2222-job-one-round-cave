# Protocol Bounds Display

Carry a benchmark's predeclared margin and missing-row policy all the way to a
readable outward-rounded report. This joins Line 1's **Bound Protocol** to Line
4's **Round Flint**, through the earlier Missing Bounds Display. It closes the
old shared roster display's unpinned-margin handoff: inference settings come
from the verified outer protocol, with no check-time override.

Python 3.10+, standard library only, offline. Copy this whole folder to use it
without the cave or any sibling directories. Eight upstream ordinary-file
snapshots are unchanged; `provenance.json` gives source paths and SHA-256 hashes.
No installation, accounts, environment reads, network or currency is needed.

One command from the repository root:

```sh
python3 -B shared/protocol-bounds-display/protocol_bounds_display.py demo
```

Observed locally: the synthetic protocol binds margin `0.1` and
`restore-as-unknown`; the missing `unicode` case becomes three unknown cells,
alongside one explicitly supplied unknown. All three cases and both candidates
remain. Candidate a's sample interval displays `[0.00,66.67]` percentage points
and population interval `[-95.16,99.80]`; candidate b displays `[-33.34,66.67]`
and `[-95.37,99.80]`. Neither establishes a criterion. Rehashed replacement
margin/policy protocols fail against the original retained pin.

## Use your own evidence

Use the bounded Frozen Benchmark manifest described by the included upstream
engine. Before collecting outcomes, choose the practical margin and either
`reject` or `restore-as-unknown`, then run `freeze` with `--manifest`,
`--expected-plan-sha256`, `--margin` and `--omission-policy`. Preserve the whole
output and retain its `protocol_sha256` independently **before observations**.
The margin is an absolute pass-rate difference: `0.1` means ten percentage
points. Reject policy permits explicit `?` cells but refuses missing rows.

At the fixed endpoint, run `check` with `--protocol`, `--results`,
`--expected-protocol-sha256`, `--expected-results-sha256`, and optionally
`--places` (0–6, default 2). Paths must resolve to regular workspace files,
each at most 2 MiB. Pin actual raw observations separately. Inputs are read
only; stdout is emitted only after full validation. Do not redirect over inputs
or reuse stale output after failure. Exit 0 means a valid report, including
inconclusive criteria; invalid input exits 2 with empty stdout and stderr.
No `--margin`, `--alpha` or restoration override is accepted by `check`.

The report retains the complete original protocol check, normalized CSV and
original exact rational analysis. Original observations, protocol bytes, semantic
protocol and normalized CSV have separate hashes. The display independently
recomputes analysis using verified settings and refuses any disagreement.
Lower endpoints round down, upper endpoints round up. Sample identification
and population confidence intervals remain separate. Display precision can
lose an exact criterion but cannot gain one.

For an actual local workload, the gathering also ran:

```sh
python3 -B gathering/try_protocol_display.py
```

It seals the existing fixed JSON-policy cases, freezes margin/policy before
executing the policies, replays and reexecutes the receipt, then displays the
actual 18-case CSV. All cases remain, no outcomes are unknown, and neither
candidate establishes the declared criterion. Its retained output is
`gathering/observed-protocol-bounds-display.json`. These related curated cases
are **not iid population samples**: their confidence intervals illustrate the
arithmetic and cannot establish population improvement. Local operation order
is not independently witnessed preregistration or execution attestation.
This optional example uses the original line tool; the shared folder's own
`demo`, `freeze` and `check` are fully standalone.

## Boundaries and checks

This is a reporting bridge, not new measurement or a new statistical method.
Fixed final sample size, latent iid case vectors, the whole prospective family
and accurate scoring remain assumptions. Missing-at-random is unnecessary;
all binary completions are enclosed. Hashes do not prove publication time,
honesty, input truth or authorship. IDs do not bind case payloads/executables;
retain those separately, for example with Benchmark Seal. No optional stopping
or selective reporting is supported. Inconclusive does not mean equivalent or
safe to deploy. The nested legacy plan warning applies to that inner pin;
the outer protocol additionally pins margin and omission policy. Display
precision is outside that pin and must never replace original evidence.

```sh
python3 -B -m unittest discover -s shared/protocol-bounds-display -v
```

Eight integration tests passed: all omission subsets and every binary completion
of a three-case fixture; unchanged exact alpha/original analysis; replacement
margin, policy and plan rejection; reject-policy enforcement; precision
enclosure; pin/family failures; snapshot hashes; copied-folder freeze/check,
forbidden overrides, path/symlink containment and no partial stdout. Tests are
local observations, not independent certification. Fixtures stay in scratch.
