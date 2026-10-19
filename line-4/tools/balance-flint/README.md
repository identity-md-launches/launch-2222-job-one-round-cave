# Balance Flint

Check simultaneous linear balances with exact arithmetic and explicit unit
dimensions. Python 3.10+, standard library only; copy this entire folder for
standalone offline use. It reads bounded JSON from stdin and writes JSON to
stdout, with no file, environment, wallet, network or transaction access.

From the repository root, one command shows it working:

```sh
python3 -B line-4/tools/balance-flint/balance_flint.py demo
```

Tried locally: the demo exits **0**, finding exactly **4 kg** of material a and
**6000 g** of material b, satisfying both a 10 kg mass balance and a 26000 J
energy balance. Both residuals are exactly zero and all four claims pass.
The quantities are synthetic examples, not measured material properties.
All ten tests passed here and in an independent folder copy, including 300
seeded two-variable trials (singular draws skipped) against Cramer's rule,
pivoting, redundant equations, mixed dimensions, inconsistent/underdetermined
systems, dimensioned zero coefficients, resource limits and actual CLI statuses.

## Your own balances

```sh
printf '%s\n' '{"schema":"balance-flint/1","unknowns":{"distance":{"unit":"m","expect":"6 m"},"time":{"unit":"s"}},"equations":[{"terms":{"distance":"1","time":"-2 m/s"},"rhs":"0 m"},{"terms":{"time":"1"},"rhs":"3 s"}]}' | python3 -B line-4/tools/balance-flint/balance_flint.py run
```

The result is exactly 6 m and 3 s, exit 0. Each equation means
`sum(coefficient * unknown) = rhs`. Every coefficient and right side is an
exact quantity expression. An unknown's `unit` declares its dimensions and the
scale of its output magnitude. Thus an unknown in g and one in kg can occur
in the same balance. Coefficients may have dimensions: multiplying `m/s` by
an unknown in s contributes length. All included terms, even a zero
coefficient, must have the right side's dimensions. Omit a term to express
an untyped zero. Each equation may use different dimensions from other rows.

`unknowns` contains 1–12 named objects. Names match
`[A-Za-z][A-Za-z0-9_]{0,31}`; every object requires `unit` and optionally accepts
`expect`, `at_least`, `at_most`. Claims are quantity strings with the unknown's
dimensions; bounds are inclusive and reversed bounds are invalid. Negative
answers are permitted unless a supplied bound excludes them. A failed claim
does not replace the calculated answer. `equations` has 1–32 objects, each
containing exactly `terms` (a nonempty map of declared names to coefficient
strings) and `rhs`. Unknown fields, duplicate JSON keys and JSON numbers are
rejected. Unknown names are separate from the quantity grammar; they never
execute as expressions or Python code.

The solver first validates dimensions, then performs exact rational elimination
on the numerical magnitudes in the declared units. Row normalization implicitly
rescales each physical equation; it does not equate incompatible dimensions.
It requires a unique solution, allows consistent redundant equations, and
refuses inconsistent or underdetermined systems. It recomputes every original
equation and reports its left side, right side, dimension and zero residual.
Solutions include exact output and base-unit values; nonterminating decimals
remain fractions. No tolerance, approximation, least-squares fit, rounding,
automatic positivity constraint or measurement uncertainty is inferred.

Exit **0**: a unique exact solution, all supplied claims passed (including none).
Exit **1**: unique solution, at least one failed claim. Exit **2**: invalid
input, incompatible dimensions, no unique solution, inconsistency or resource
limit. Invalid late equations produce no partial stdout.

## Grammar, bounds and limitations

Uses Unit Flint's parser without modification: `+ - * / ^ **`, parentheses,
decimal/scientific numbers and integer powers -12..12. Supported units:
m, cm, mm, km, in, ft, mi; kg, g, mg, t; s, ms, min, h, day;
B, KiB, MiB, GiB; L, mL; N, J, W. Dimensionless unknowns use `"unit":"1"`.
Use explicit multiplication: `(1/8) * ms` is time; `1/8 ms` is inverse time.
Likewise `2 * m^2` is two square metres; `2 m^2` squares the two as well.
No offsets/temperatures, currencies, symbolic nonlinear equations or custom
units are supported. No coin is needed for this numerical tool.

Stdin is at most 65536 bytes, valid UTF-8 JSON with at most five nesting levels.
Expressions are at most 4096 characters, 256 tokens and 32 nesting levels.
Parsed values and each elimination, residual and claim operation are limited
to 2048-bit numerators/denominators. Dimensions stay within -256..256.
Some mathematically solvable systems can exceed that arithmetic budget;
the solver refuses rather than rounding. Exact residuals prove consistency
with the supplied equations, not physical accuracy, model completeness,
good conditioning under uncertain measurements or safe engineering design.

Run the regression suite:

```sh
python3 -B -m unittest discover -s line-4/tools/balance-flint -v
```

`engine.py` is an ordinary-file byte-identical snapshot of
`line-4/tools/unit-flint/unit_flint.py`, SHA-256
`c683e558cdbdf6cf73d4b32572b6fa498b80e7816483b882bf2d51adfff3062e`.
No ancestor tool is modified and no external dependency is required.
