#!/usr/bin/env python3
"""Solve bounded simultaneous linear balances with exact dimensional arithmetic."""
import argparse
from fractions import Fraction
import json
import re
import sys

from engine import Parser, Quantity, UnitError, ZERO, dimensions, exact_decimal

MAX_BYTES = 65536
NAME = re.compile(r'[A-Za-z][A-Za-z0-9_]{0,31}\Z')


def parse(text, target=False):
    if not isinstance(text, str):
        raise ValueError('quantities and units must be expression strings')
    return Parser.bounded(Parser(text, target=target).parse(), 0)


def bounded(value):
    return Parser.bounded(Quantity(value, ZERO), 0).value


def solve(matrix, count):
    """RREF on dimensionless numerical magnitudes, checking every operation."""
    a = [row[:] for row in matrix]
    pivots = []
    for column in range(count):
        row = next((i for i in range(len(pivots), len(a)) if a[i][column]), None)
        if row is None:
            continue
        p = len(pivots)
        a[p], a[row] = a[row], a[p]
        divisor = a[p][column]
        a[p] = [bounded(x / divisor) for x in a[p]]
        for i in range(len(a)):
            if i == p or not a[i][column]:
                continue
            scale = a[i][column]
            a[i] = [bounded(x - bounded(scale * y)) for x, y in zip(a[i], a[p])]
        pivots.append(column)
    if any(not any(row[:count]) and row[count] for row in a):
        raise ValueError('inconsistent equations: no exact solution')
    if len(pivots) != count:
        raise ValueError('underdetermined equations: no unique solution')
    result = [Fraction(0)] * count
    for i, column in enumerate(pivots):
        result[column] = a[i][-1]
    return result


def calculate(request):
    if not isinstance(request, dict) or set(request) != {'schema', 'unknowns', 'equations'}:
        raise ValueError('request requires exactly schema, unknowns, equations')
    if request['schema'] != 'balance-flint/1':
        raise ValueError('unsupported schema')
    unknowns, equations = request['unknowns'], request['equations']
    if not isinstance(unknowns, dict) or not 1 <= len(unknowns) <= 12:
        raise ValueError('unknowns must contain 1..12 named entries')
    if not isinstance(equations, list) or not 1 <= len(equations) <= 32:
        raise ValueError('equations must contain 1..32 entries')
    names, units, checks = list(unknowns), [], []
    for name, spec in unknowns.items():
        if not isinstance(name, str) or not NAME.fullmatch(name):
            raise ValueError('invalid unknown name')
        if (not isinstance(spec, dict) or 'unit' not in spec
                or spec.keys() - {'unit', 'expect', 'at_least', 'at_most'}):
            raise ValueError('unknown requires unit; optional expect, at_least, at_most')
        unit = parse(spec['unit'], target=True)
        if unit.value <= 0:
            raise ValueError('unknown unit must have a positive scale')
        units.append(unit)
        claim = {key: parse(spec[key]) for key in ('expect', 'at_least', 'at_most') if key in spec}
        if any(q.dims != unit.dims for q in claim.values()):
            raise ValueError('claim dimensions do not match unknown ' + name)
        if ('at_least' in claim and 'at_most' in claim
                and claim['at_least'].value > claim['at_most'].value):
            raise ValueError('lower bound exceeds upper bound')
        checks.append(claim)
    matrix, row_dims = [], []
    for equation in equations:
        if not isinstance(equation, dict) or set(equation) != {'terms', 'rhs'}:
            raise ValueError('each equation requires exactly terms and rhs')
        terms = equation['terms']
        if not isinstance(terms, dict) or not terms or terms.keys() - unknowns.keys():
            raise ValueError('terms must name one or more declared unknowns')
        rhs = parse(equation['rhs'])
        row = []
        for name, unit in zip(names, units):
            if name not in terms:
                row.append(Fraction(0))
                continue
            coefficient = parse(terms[name])
            dims = tuple(a + b for a, b in zip(coefficient.dims, unit.dims))
            # Zero coefficients still carry dimensions; omission is the only untyped zero.
            if dims != rhs.dims:
                raise ValueError('coefficient * unknown dimensions do not match rhs: ' + name)
            row.append(bounded(coefficient.value * unit.value))
        matrix.append(row + [rhs.value])
        row_dims.append(rhs.dims)
    values = solve(matrix, len(names))
    residuals = []
    for i, row in enumerate(matrix):
        lhs = Fraction(0)
        for coefficient, value in zip(row[:-1], values):
            lhs = bounded(lhs + bounded(coefficient * value))
        residual = bounded(lhs - row[-1])
        if residual:
            raise ValueError('internal residual check failed')
        residuals.append({'equation': i, 'lhs_base_value': exact_decimal(lhs),
                          'rhs_base_value': exact_decimal(row[-1]),
                          'residual_base_value': exact_decimal(residual),
                          'base_unit': dimensions(row_dims[i])})
    results, passes = {}, True
    for name, unit, value, claim in zip(names, units, values, checks):
        base = bounded(value * unit.value)
        entry = {'value': exact_decimal(value), 'unit': unknowns[name]['unit'],
                 'base_value': exact_decimal(base), 'base_unit': dimensions(unit.dims), 'checks': {}}
        for key, q in claim.items():
            ok = (base == q.value if key == 'expect' else base >= q.value
                  if key == 'at_least' else base <= q.value)
            entry['checks'][key] = {'expression': unknowns[name][key], 'passes': ok,
                                    'difference_base_value': exact_decimal(bounded(base - q.value))}
            passes = passes and ok
        results[name] = entry
    return {'schema': 'balance-flint-result/1', 'method': 'exact-linear-elimination',
            'rank': len(names), 'solution': results, 'equations': residuals, 'passes': passes}


def reject(value):
    raise ValueError('JSON numbers are unsupported; use expression strings')


def unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate JSON key: ' + key)
        obj[key] = value
    return obj


def load(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('input exceeds 65536 bytes')
    text = raw.decode('utf-8')
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '[{':
            depth += 1
            if depth > 5:
                raise ValueError('JSON nesting exceeds five levels')
        elif char in ']}':
            depth -= 1
    return json.loads(text, object_pairs_hook=unique, parse_int=reject,
                      parse_float=reject, parse_constant=reject)


def example():
    # A synthetic blend: masses total 10 kg, with 26 kJ total supplied energy.
    return {'schema': 'balance-flint/1',
            'unknowns': {'a': {'unit': 'kg', 'expect': '4000 g', 'at_least': '0 kg'},
                         'b': {'unit': 'g', 'expect': '6000 g', 'at_least': '0 kg'}},
            'equations': [{'terms': {'a': '1', 'b': '1'}, 'rhs': '10 kg'},
                          {'terms': {'a': '2000 J/kg', 'b': '3000 J/kg'}, 'rhs': '26000 J'}]}


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('command', choices=['run', 'demo'])
    args = cli.parse_args(argv)
    try:
        request = example() if args.command == 'demo' else load(sys.stdin.buffer.read(MAX_BYTES + 1))
        result = calculate(request)
    except (ValueError, TypeError, UnicodeError, UnitError, OverflowError, ZeroDivisionError) as exc:
        print('balance-flint: ' + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result['passes'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
