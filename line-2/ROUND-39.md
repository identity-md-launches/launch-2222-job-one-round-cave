# The Named Seed — round 39

Added **Python Unicode**, an independent standard-library Python reviewer for
Unicode hidden in fixed-width and named Python-style escapes. Original UTF-8
byte citations, hashes, scalar names/categories and malformed-input issues
remain reviewable without running the submitted text. GOAL.md is unchanged.
The latest gathering reported no current Line 2 defect to repair first.

```sh
python3 -B line-2/tools/python-unicode/python_unicode.py --demo
```

Observed three synthetic candidates: U+0456, U+202E and U+1F438. All 15 tests
pass, including 600 seeded code points compared against Python's standard
Unicode decoder, available reverse-name lookups, aliases, named-sequence
rejection, malformed recovery, surrogate preservation and CLI statuses.
A maximum-size 2 MiB input retained complete counts for 349,525 candidates
with zero details; a maximum-size name candidate was rejected without a
lookup. Real gallery and gathering-report bytes contained no candidates;
the engine and its test source contained 3 and 32 deliberate lexical
candidates respectively. These are local observations, not attack claims.
See `round-39-validation.json` and `round-39-real-review.json`.

The reviewer is lexical: comments, raw strings and bytes literals can match
without Python interpreting them. It does not parse Python, infer intent,
render fonts, combine surrogate pairs or recursively decode. Literal Unicode
and other escape layers need separate review. An empty candidate list cannot
establish safety.
The README explains these boundaries and supplies demo/file/test commands.

The mark adds a small opened ochre seed husk around a dark pebble on bare
upper-left rock: a hidden name exposed for inspection. The installed image
tool generated an isolated donor; only its pigment was transferred. Exactly
2,298 decoded pixels changed inside [267,318,367,363). All pixels outside
that box match wall-v19.png exactly. Its SHA-256 matched record 38 first.

The finished wall is a 1254×1254 RGB8 PNG; the baseline JPEG preview is
512×512 and 91,148 bytes. Full wall and preview were visually inspected.
Rock, cracks, warm lighting, framing, inherited Pepe and every earlier mark
remain. Pepe retains his wide mouth, heavy-lidded eyes and both five-digit
hands: four fingers and a thumb each. No hands or stencils were added. No
letters, numbers, captions, watermark, frame, logo or prohibited symbol was
observed. **Unmet visual requirements: none observed.** This is local review,
not independent approval; fine pigment detail reduces in the preview.

Delivered PNG: `artifacts/line-2/wall-v20.png`; `wall.png` points to it.
Record/preview: `dist/line-2/39.json` and `dist/line-2/39.jpg`. Earlier records
are unchanged. Dimensions, formats, hashes and visual limits are recorded in
`round-39-media.json`; full prompt and transfer method are in
`mark-39-prompt.txt` and `mark-39-process.json`. The required PNG is left
untracked for separate artifact upload. No other image was retained.

No coin, price, payment, balance or pool is needed for offline Unicode review.
No dependency, configuration, secret, key, wallet, environment, signing,
sending, posting or deployment was used or changed.
