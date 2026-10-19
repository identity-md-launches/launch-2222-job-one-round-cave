# Python Unicode

Review Unicode hidden behind Python-style `\u`, `\U` and `\N{...}` escapes
before trusting or publishing text. Reports cite the original UTF-8 byte span,
source hex and SHA-256, one-based line/byte column, escape form, code point,
Unicode name/category and decoded UTF-8. Unknown names, malformed hex and
out-of-range values retain their evidence with an explicit issue. Lone
surrogates remain separate code units with no invented UTF-8 encoding.

Python 3.9+; standard library only. Copy this folder for standalone use.
No network, installation, input execution, rewrite or transaction is needed.
From the repository root, run:

```sh
python3 -B line-2/tools/python-unicode/python_unicode.py --demo
```

Observed: three candidates, U+0456 (Cyrillic small i in a synthetic `admin`
lookalike), U+202E RIGHT-TO-LEFT OVERRIDE, and U+1F438 FROG FACE. These are
labeled examples, not an observed attack. Output is ASCII JSON; the bidi
control is never emitted raw.

Review a selected actual workspace file:

```sh
python3 -B line-2/tools/python-unicode/python_unicode.py --file line-2/tools/python-unicode/python_unicode.py --max-details 10
```

The file must resolve to a regular file within the current working directory.
Input is strict UTF-8, at most 2 MiB. File reviews exit 1 when candidates exist,
0 when none exist, 2 on input errors. The demo exits 0. Details are capped at
0–1000; counts and analysis remain complete. Byte ranges are zero-based,
half-open original-source coordinates, never decoded-output coordinates.
Lines/byte columns are one-based and LF-only. Hashes establish byte identity,
not authenticity. Path checks are not an OS sandbox against concurrent changes.

This is a **lexical candidate reviewer**, not a Python parser or safety verdict.
Raw strings, comments, bytes literals and non-Python text are intentionally
included; their matches need not be interpreted by Python. String prefixes,
quoting, f-string grammar, literal Unicode, identifier validity, fonts and
other escape syntaxes need separate review. Zero candidates cannot establish
safety or intent. Use the line's literal-Unicode tools as a separate layer.

Hex forms require exactly 4 or 8 digits, without CSS whitespace termination.
Named aliases use the runtime Unicode database, whose version is recorded.
Named sequences are rejected: Python named escapes require one code point.
Names longer than 256 bytes are reported without a lookup. No surrogate pair
combining, replacement, normalization or recursive decoding occurs. Other
backslash pairs are skipped once, so `\\u202e` does not masquerade as a
Unicode escape. Malformed names stop before a backslash/newline, and malformed
hex stops before a nonhex byte, leaving later candidates visible. ASCII JSON
protects terminal display; HTML embedding still requires appropriate escaping.

Local checks: 15 tests cover named aliases/sequences, malformed recovery,
surrogates, exact citations, backslash parity/non-recursion, 600 seeded code
points against Python's standard Unicode decoder, available reverse-name
lookups, bounded counts and CLI statuses:

```sh
python3 -B -m unittest discover -s line-2/tools/python-unicode -v
```
