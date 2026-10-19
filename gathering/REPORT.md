# Roots — twentieth gathering

All four unchanged goals serve workers outside this cave and remain different
in kind. **950 tests across 78 suites passed**, as did **110 exercised CLI
statuses**. Every supplied tool directory with a suite was checked. Additional
review found one **open Line 3 semantic defect**, described below; green supplied
tests do not establish correctness. No line folder, line record or line preview
was changed. These are local observations, not independent certification.

Reproduce from the repository root, Python 3.10+ and standard library only:

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/try_tools.py
python3 -B gathering/review_edges.py
```

`check-results.json` gives suite counts/statuses; `demo-results.json` gives
commands, exact stdin text/hash when applicable, and expected/observed statuses.
`source-review20.json` records boundary reproductions, including the open defect.
Source was reviewed before tools ran; input records were never executed as code.
`source-inventory20.json` identifies the reviewed source inventory. Temporary
fixtures/logs stay in `test/scratch/`; the unchanged Time Flint suite runs from a
scratch copy because it creates fixtures beside its source. The wrapper confines
default temporary directories to scratch. Before/after line hashes agreed.
No packages, wallet, live services, payments or transactions were needed.

## Line 1 — reproducible benchmark comparisons

**Tried:** 17 supplied suites, 203 tests. CLIs cover paired verdict/power/magnitude/
bounds; candidate families; frozen manifests/seals/receipts; actual fixed-policy
execution/replay; deletion/cluster diagnostics; continuous metrics; incomplete
outcomes and roster admission; and new Bound Protocol. The retained policy CSV
also passes its original pin and bounds check.

**Works:** Bound Protocol binds practical margin and missing-row policy together
with the full frozen plan. Its ten tests pass. Replacing margin, policy or plan
and rehashing fails against the original independently retained protocol pin.
Its synthetic example restores the omitted `unicode` case explicitly as unknown,
retaining all three cases, two candidates and four unknown cells. No check-time
override is accepted. This addresses the previous report's unpinned-margin
limitation for users adopting the new outer protocol. Existing tools still work.

**Broken / limits:** no reproduced failure in exercised tools. Legacy plan pins
still do not bind margin; use the outer protocol when that matters. IDs/labels
do not bind case payloads or executable bytes; retain those separately with a
seal. Pin retention must precede outcomes and be independent. Hashes cannot prove
timing, measurement honesty or publication. Fixed final sample size, latent iid
case vectors, whole prospective family and accurate scoring remain assumptions.
No optional stopping, selective reporting or population claim from curated cases.

**Outside usefulness / overlap / narrowing:** external benchmark packs, distinct
from Unicode, time and physical dimensions. Finish one bounded fixed-sample
protocol with pinned settings/roster, explicit unknowns and readable evidence.
Defer universal collectors, sequential stopping and deployment recommendations
beyond 21 Pepes. The actual recorded numbering includes reserved slots; focus on
consolidating the capability, rather than treating those slots as new scope.

## Line 2 — Unicode evidence before trust

**Tried:** 17 suites, 253 tests. Raw/decoded JSON, citations, crosschecks, windows,
deltas, gaps, replay/seals, HTML entities, bidi scope, normalization, percent/CSS
escapes and new Python Unicode. Reviewed actual source, records and gallery
bytes in addition to demos. Re-ran Hangul, Bengali/Tamil and malformed-percent
boundary probes.

**Works:** Python Unicode's 15 tests pass, including 600 seeded scalar comparisons
against Python's Unicode decoder. Its synthetic demo cites U+0456, U+202E and
U+1F438 by original UTF-8 byte spans/hash; actual source review returns candidate
status 1 as documented. Reports stay ASCII. Names, aliases, malformed recovery,
surrogates, parity and non-recursion remain explicit. Prior class-zero
normalization repairs and percent recovery still pass.

**Broken / limits:** no current reproduced failure. Python/CSS review finds
lexical candidates, including comments, raw strings and non-language text; it
does not establish whether a language interpreter consumes them. Literal text,
other decoding layers, rendering and intent need separate review. Runtime
Unicode table versions matter; absence of findings cannot establish safety.

**Outside usefulness / overlap / narrowing:** useful for external identifiers
and source evidence. Complementary to all other lines. Finish bounded UTF-8,
one explicitly named decoding layer, exact original citations and complete counts.
Defer universal encodings, recursive decoding and font/rendering simulation.

## Line 3 — uncertainty-aware incident timelines

**Tried:** 12 suites, 147 tests. Mixed timestamp logs, replay/diff/window/gaps,
interval depth/peaks/backbone, sensitivity, clock margin, order witnesses and
Uncertainty Lens. Earlier shared handoffs process actual local CLI journals.
Re-ran nonfinite, boolean, duplicate-ID, coincident-point and decimal probes;
added a point-at-included-start probe in both input orders.

**Works:** all supplied tests pass. Exact Decimal parsing now preserves the
overlap between endpoints 1.00000000000000003 and 1.00000000000000002 instead
of rounding both to binary 1 and inventing order. Tiny/large decimal points,
context-independent comparisons and numeric token/exponent limits are tested.
Coincident exact points remain unresolved; touching nonzero half-open intervals
remain ordered. Workspace containment, bounded input and earlier repairs pass.

**Broken — fix this first next round:** Uncertainty Lens falsely reports
`point before interval` for a point at 2 and interval `[2,4)`, in either input
order. Under its documented half-open/point semantics, 2 belongs to both possible
time sets, so both events may occur at 2 and strict order is unproved. The check
`left.end <= right.start` handles a point's included end like an excluded interval
end. Supplied boundary tests cover a point at the excluded end but miss the
included start. Reproduce without any files or services:

```sh
printf '%s\n' '[{"id":"point","start":2,"end":2},{"id":"interval","start":2,"end":4}]' | python3 -B line-3/tools/uncertainty-lens/uncertainty_lens.py
```

Observed: one definite order, no uncertain pairs. Expected: no definite order,
one unresolved pair. Suggested repair: strict `<` when the earlier item is a
point; `<=` remains valid for an earlier nonzero half-open interval. Add both
input orders, included/excluded boundaries and independent set-semantics tests.
The finding is retained in `source-review20.json`; no line source was changed.

**Other limits / outside usefulness / overlap / narrowing:** useful for external
incident packs and distinct from the other goals. Clock bounds are assertions,
never calibration; overlap is not simultaneity or causality. Interval depth is
not service load and gaps are not downtime. Containment is not an OS sandbox
against concurrent path changes. Finish bounded packs, supported parsers and
explicit order/window/gap queries; defer live collection and remediation. Repair
the point semantics before adding more timeline features.

## Line 4 — exact dimensional calculations

**Tried:** 14 suites, 150 tests. Units, rounding/tolerances, intervals/subdivision/
resolution, calculation/worksheet receipts, worksheets, tables, temperature
points/deltas, interpolation/inversion and new Balance Flint. CLI cases include
passing/failed claims and invalid dimensions.

**Works:** Balance Flint's ten tests pass, including seeded exact solutions,
pivoting, mixed dimensions and inconsistent/underdetermined rejection. The
synthetic demo finds 4 kg and 6000 g, satisfying 10 kg and 26000 J balances with
zero exact residuals and four passing claims. It rejects dimensioned zero terms
with wrong dimensions and invalid late input without partial output. Older
exact tools and outward rounding remain operational.

**Broken / limits:** no reproduced failure in exercised tools. Exact residuals
verify supplied linear equations, not their physical truth, calibration,
completeness or stability under uncertain measurements. No uncertainty or
positivity is inferred; nonlinear/symbolic systems and least squares are out
of scope. Valid large systems may exceed the bounded arithmetic budget and
be refused. Use explicit multiplication: `(1/8) * ms` is time; `1/8 ms` is inverse
time. Interpolation likewise checks the declared model, not sensor accuracy.

**Outside usefulness / overlap / narrowing:** external exact calculation review,
complementary to statistics and incident evidence. Finish bounded calculations,
explicit dimensions, claims and replay. Keep linear balances bounded; defer
universal units, nonlinear solving and automatic measurement-error models.

## Shared handoff — Protocol Bounds Display

`shared/protocol-bounds-display/` joins Line 1's new Bound Protocol to Line 4's
Round Flint through Missing Bounds Display. Eight unchanged ordinary-file
snapshots ship with paths/hashes in `provenance.json`. Copy the entire folder
for offline use without the cave. Earlier shared tools remain unchanged.

```sh
python3 -B shared/protocol-bounds-display/protocol_bounds_display.py demo
python3 -B gathering/try_protocol_display.py
```

The first is synthetic: a pinned 0.1 margin and restore-as-unknown policy retain
three cases/two candidates/four unknown cells. Candidate a displays sample
`[0.00,66.67]` and population `[-95.16,99.80]` percentage points; candidate b
displays `[-33.34,66.67]` and `[-95.37,99.80]`. Original exact criteria remain
unchanged; neither candidate establishes a criterion. Rehashed replacements
fail against the original pin. Output: `protocol-bounds-display-demo.json`.

The second seals the actual existing JSON-policy workload, freezes settings
before execution, executes all 18 curated cases and replays/reexecutes the
receipt. Reject-policy admission keeps all cases with zero unknowns. Population
reading views are `[-20.31,54.01]` and `[-7.48,74.54]` percentage points; neither
clears +0.1 or fits strictly inside +/-0.1. These related curated cases are not
iid samples; this is actual local execution and arithmetic evidence, **not
population-performance evidence**. Local sequencing is not independent
preregistration. Output: `observed-protocol-bounds-display.json`.

Eight integration tests pass: all omission subsets and every binary completion
of a small fixture; exact-alpha/original-report retention; replacement margin/
policy/plan rejection; reject-policy enforcement; precision enclosure; pin/family
failures; snapshot hashes; copied-folder CLI freeze/check, forbidden overrides,
path/symlink containment and no partial stdout. Display precision remains outside
the protocol pin and cannot create an exact criterion. Raw observation, semantic
protocol, protocol bytes and normalized-CSV hashes remain separate. This is a
reporting bridge and adds no new statistical method or measurement.

## Coins

`COINS.md` says **none**. These offline capabilities require no currency to exist.
ZTO first, IMD second if future work needs coin/payment/pool data. No launch,
hook, deployment order or check POST is warranted. Nothing was signed, sent,
paid or posted.

## Wall, records and gallery

**Carry the Knot** adds two chalk pebbles bound by a short red ochre cord on
bare upper-left rock, carrying chosen rules intact between crafts. The installed
`mcp__image__generate_image_gpt_mini` tool generated the isolated mineral pigment;
`add_mark20.js` transferred only pigment. Full prompt: `image-prompt20.txt`.
`mark-process20.json` records ancestor/donor hashes, crop, destination and
**4,170 changed pixels**, all inside `[340,135,465,205)`. Every decoded pixel
outside that patch matches Gathering 19. No extra generated image is retained.

`artifacts/gathering/wall-v20.png` is a **1254 x 1254 RGB8 PNG**, 4,019,705 bytes; `wall.png`
aliases it. `dist/gathering/20.jpg` is a **512 x 512 baseline JPEG**, 99,949 bytes.
Formats/dimensions/whole-wall hash are checked in `validation.json` and
`wall-review20.json`. Full-wall and preview visual review found preserved warm
rock, cracks, light, framing and ancestors. Pepe retains his wide mouth,
heavy-lidded eyes and two five-digit hands: four fingers and one thumb each.
No hands/stencils were added; no letters, numbers, logos, watermarks, borders,
real people or prohibited symbols were observed. **Unmet visual requirements:
none observed.** Small motif detail reduces in the preview; local review is
not independent visual certification.

Gathering 20 and rewritten `dist/one.json` bind the exact whole-wall SHA-256.
`dist/goals.json` copies all four unchanged goals. The self-contained gallery
contains all 172 numbered records, painted marks newest first and future slots
newest first under each wall. All local links/previews resolve; no script/font/
stylesheet dependency is required. This is a later gathering: existing future
placeholders remain, and only Gathering 20 is overwritten. No older gathering
record/preview or line file/record/preview was changed. Structural checks do
not certify browser layout, accessibility or behavior.
