import copy
from fractions import Fraction
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

from balance_flint import calculate, example, load
from engine import UnitError


class BalanceTests(unittest.TestCase):
    def test_demo_mixed_output_scales(self):
        result = calculate(example())
        self.assertTrue(result['passes'])
        self.assertEqual(result['solution']['a']['value'], '4')
        self.assertEqual(result['solution']['b']['value'], '6000')
        self.assertEqual([r['residual_base_value'] for r in result['equations']], ['0', '0'])

    def test_seeded_independent_cramers_rule(self):
        rng = random.Random(737)
        for _ in range(300):
            a, b, c, d = [rng.randint(-20, 20) for _ in range(4)]
            if not a * d - b * c:
                continue
            r, s = [Fraction(rng.randint(-40, 40), rng.randint(1, 20)) for _ in range(2)]
            request = {'schema': 'balance-flint/1',
                       'unknowns': {'x': {'unit': 'cm'}, 'y': {'unit': 'm'}},
                       'equations': [{'terms': {'x': str(a), 'y': str(b)}, 'rhs': f'({r}) * m'},
                                     {'terms': {'x': str(c), 'y': str(d)}, 'rhs': f'({s}) * m'}]}
            result = calculate(request)['solution']
            det = a * d - b * c
            self.assertEqual(Fraction(result['x']['base_value']), (r * d - b * s) / det)
            self.assertEqual(Fraction(result['y']['base_value']), (a * s - r * c) / det)

    def test_pivoting_three_unknowns_and_redundant_row(self):
        request = {'schema': 'balance-flint/1',
                   'unknowns': {name: {'unit': 's'} for name in ('x', 'y', 'z')},
                   'equations': [{'terms': {'y': '2'}, 'rhs': '4 s'},
                                 {'terms': {'x': '1', 'z': '1'}, 'rhs': '4 s'},
                                 {'terms': {'z': '3'}, 'rhs': '9 s'},
                                 {'terms': {'x': '1', 'y': '1', 'z': '1'}, 'rhs': '6 s'}]}
        result = calculate(request)
        self.assertEqual([result['solution'][n]['value'] for n in ('x', 'y', 'z')], ['1', '2', '3'])
        self.assertEqual(len(result['equations']), 4)

    def test_equations_with_different_unknown_dimensions(self):
        request = {'schema': 'balance-flint/1',
                   'unknowns': {'distance': {'unit': 'm'}, 'time': {'unit': 's'}},
                   'equations': [{'terms': {'distance': '1', 'time': '-2 m/s'}, 'rhs': '0 m'},
                                 {'terms': {'time': '1'}, 'rhs': '3 s'}]}
        self.assertEqual(calculate(request)['solution']['distance']['value'], '6')

    def test_singular_and_inconsistent(self):
        request = example()
        request['equations'] = [request['equations'][0]] * 2
        with self.assertRaisesRegex(ValueError, 'underdetermined'):
            calculate(request)
        request['equations'][1] = {'terms': {'a': '1', 'b': '1'}, 'rhs': '11 kg'}
        with self.assertRaisesRegex(ValueError, 'inconsistent'):
            calculate(request)
        request['equations'] = [{'terms': {'a': '0', 'b': '0'}, 'rhs': '1 kg'}]
        with self.assertRaisesRegex(ValueError, 'inconsistent'):
            calculate(request)

    def test_dimension_failures_even_for_zero(self):
        for coefficient in ('0 s', '1 s'):
            request = example()
            request['equations'][0]['terms']['a'] = coefficient
            with self.assertRaisesRegex(ValueError, 'dimensions'):
                calculate(request)
        request = example()
        request['unknowns']['b']['expect'] = '6000 s'
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            calculate(request)

    def test_claims_inclusive_and_failed_claim_keeps_solution(self):
        request = example()
        request['unknowns']['a'].update(at_least='4 kg', at_most='4000 g')
        self.assertTrue(calculate(request)['passes'])
        request['unknowns']['a']['expect'] = '5 kg'
        result = calculate(request)
        self.assertFalse(result['passes'])
        self.assertEqual(result['solution']['a']['value'], '4')
        request['unknowns']['a'].update(at_least='5 kg', at_most='4 kg')
        with self.assertRaisesRegex(ValueError, 'lower bound'):
            calculate(request)

    def test_schema_and_size_limits(self):
        mutations = [lambda r: r.update(schema='other'),
                     lambda r: r.update(extra=True),
                     lambda r: r.update(unknowns={}),
                     lambda r: r.update(equations=[]),
                     lambda r: r['unknowns']['a'].update(unit='-kg'),
                     lambda r: r['unknowns']['a'].update(unit='0'),
                     lambda r: r['unknowns']['a'].update(extra='1'),
                     lambda r: r['equations'][0]['terms'].update(z='1'),
                     lambda r: r['equations'][0]['terms'].update(a=1),
                     lambda r: r['equations'][0].update(extra='1'),
                     lambda r: r.update(unknowns={str(i): {'unit': 's'} for i in range(13)}),
                     lambda r: r.update(equations=r['equations'] * 17)]
        for mutate in mutations:
            request = copy.deepcopy(example())
            mutate(request)
            with self.assertRaises((ValueError, UnitError)):
                calculate(request)
        with self.assertRaises(ValueError):
            load(b' ' * 65537)
        for raw in (b'{"schema":"a","schema":"b"}', b'1', b'1.1', b'NaN',
                    b'[[[[[[]]]]]]', b'\xff'):
            with self.assertRaises((ValueError, UnicodeError)):
                load(raw)

    def test_arithmetic_budget(self):
        request = example()
        request['equations'][0]['terms']['a'] = '(1e100)^12'
        with self.assertRaisesRegex(UnitError, 'budget'):
            calculate(request)

    def test_cli_no_partial_output_and_statuses(self):
        script = str(Path(__file__).with_name('balance_flint.py'))
        requests = [(example(), 0)]
        failed = example()
        failed['unknowns']['b']['expect'] = '1 g'
        requests.append((failed, 1))
        late_invalid = example()
        late_invalid['equations'].append({'terms': {'a': '1'}, 'rhs': '1 s'})
        requests.append((late_invalid, 2))
        for request, status in requests:
            p = subprocess.run([sys.executable, '-B', script, 'run'],
                               input=json.dumps(request).encode(), capture_output=True)
            self.assertEqual(p.returncode, status, p.stderr)
            if status == 2:
                self.assertEqual(p.stdout, b'')
            else:
                self.assertEqual(json.loads(p.stdout)['passes'], status == 0)
                self.assertEqual(p.stderr, b'')


if __name__ == '__main__':
    unittest.main()
