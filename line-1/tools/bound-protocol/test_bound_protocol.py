"""Prospective controls, downstream equality and portable CLI regression tests."""
import copy
import itertools
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
import bound_protocol as b


def fixture(cases=('x', 'y', 'z'), margin='0.1', policy='restore-as-unknown', alpha='0.05'):
    manifest = b.frozen.freeze(b.frozen.canonical({
        'schema': b.frozen.SCHEMA, 'baseline': 'base-v1', 'candidates': ['a', 'c'],
        'pass_rule': 'Synthetic exact match.', 'alpha': alpha, 'cases': list(cases)}))
    pack = b.freeze(b.frozen.canonical(manifest), manifest['plan_sha256'], margin, policy)
    return pack


def run(pack, raw):
    return b.check(b.frozen.canonical(pack), raw, pack['protocol_sha256'], b.frozen.digest(raw))


class ProtocolTests(unittest.TestCase):
    def test_demo(self):
        out = b.demo()
        self.assertEqual(set(out['rejected']), {'changed_margin', 'changed_policy'})
        report = out['report']['roster_report']
        self.assertEqual(report['restored_all_unknown_case_ids'], ['unicode'])
        self.assertEqual(report['analysis']['missing_cells'], 4)
        self.assertEqual(report['analysis']['planned_cases_retained'], 3)

    def test_self_consistent_replacement_cannot_use_original_pin(self):
        original = fixture()
        for replacement in [fixture(margin='0.2'), fixture(policy='reject'),
                            fixture(cases=('x', 'y')), fixture(alpha='0.1')]:
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                b.verify(b.frozen.canonical(replacement), original['protocol_sha256'])

    def test_pinned_margin_reaches_real_criterion(self):
        cases = tuple('case-' + str(i) for i in range(40))
        raw = ('case,baseline,a,c\n' + ''.join(x + ',0,1,1\n' for x in cases)).encode()
        low = run(fixture(cases, margin='0', policy='reject'), raw)[0]
        high = run(fixture(cases, margin='1', policy='reject'), raw)[0]
        for report, expected in [(low, True), (high, False)]:
            analysis = report['roster_report']['analysis']
            self.assertTrue(all(c['candidate_exceeds_positive_margin'] is expected
                                for c in analysis['candidates']))
        self.assertEqual(low['roster_report']['analysis']['candidates'][0]['candidate_minus_baseline_bounds'],
                         high['roster_report']['analysis']['candidates'][0]['candidate_minus_baseline_bounds'])

    def test_policy_is_enforced_not_only_recorded(self):
        raw = b'case,baseline,a,c\nx,0,1,?\n'
        with self.assertRaisesRegex(ValueError, 'omitted'):
            run(fixture(policy='reject'), raw)
        out, csv = run(fixture(), raw)
        self.assertEqual(out['roster_report']['restored_unknown_cell_count'], 6)
        self.assertIn(b'y,?,?,?\nz,?,?,?\n', csv)
        # Explicit unknown rows remain legal even under reject-omission policy.
        run(fixture(policy='reject'), csv)

    def test_every_omission_subset_matches_original_engine(self):
        pack = fixture(alpha='0.050000000000000001', margin='0.123456789')
        value = pack['protocol']
        rows = ['x,0,1,?', 'y,?,0,1', 'z,1,1,0']
        for n in range(4):
            for selected in itertools.combinations(rows, n):
                raw = ('case,baseline,a,c\n' + ''.join(x+'\n' for x in selected)).encode()
                report, csv = run(pack, raw)
                direct, direct_csv = b.roster.check(b.frozen.canonical(value['manifest']), raw,
                    value['manifest']['plan_sha256'], b.frozen.digest(raw),
                    Fraction('0.123456789'), True)
                self.assertEqual(report['roster_report'], direct)
                self.assertEqual(csv, direct_csv)

    def test_numeric_normalization_preserves_pin(self):
        self.assertEqual(fixture(margin='0.1'), fixture(margin='0.100000000'))
        self.assertEqual(fixture(margin='1.000')['protocol']['margin'], '1')
        self.assertEqual(fixture(margin='0.000')['protocol']['margin'], '0')

    def test_strict_schema_and_values(self):
        pack = fixture()
        variants = [None, [], {}, {'protocol': pack['protocol']},
                    dict(pack, extra=1)]
        for key, value in [('margin', True), ('margin', 'NaN'), ('margin', '1.1'),
                           ('margin', '0.0000000001'), ('margin', '1/10'),
                           ('omission_policy', None), ('omission_policy', 'drop'),
                           ('schema', 'future'), ('manifest', []), ('extra', 1)]:
            bad = copy.deepcopy(pack)
            bad['protocol'][key] = value
            variants.append(bad)
        for bad in variants:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                b.verify(b.frozen.canonical(bad), pack['protocol_sha256'])
        raw = b.frozen.canonical(pack).replace(b'"margin":', b'"margin":"0.2","margin":')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            b.verify(raw, pack['protocol_sha256'])
        for bad_pin in [None, '', 'X'*64, '0'*64]:
            with self.assertRaises(ValueError):
                b.verify(b.frozen.canonical(pack), bad_pin)

    def test_results_pin_family_and_limits(self):
        pack = fixture()
        raw = b'case,baseline,a,c\nx,0,1,1\n'
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            b.check(b.frozen.canonical(pack), raw + b'\n', pack['protocol_sha256'], b.frozen.digest(raw))
        for bad in [raw.replace(b'a,c', b'c,a'), raw + b'extra,0,1,1\n', raw+raw.split(b'\n')[1]+b'\n']:
            with self.assertRaises(ValueError):
                run(pack, bad)
        for cases in [tuple(str(i) for i in range(513)), ('a'*201,)]:
            with self.assertRaises(ValueError):
                fixture(cases)

    def test_portable_cli_and_no_partial_output(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as name:
            root = Path(name).resolve()
            for source in Path(__file__).parent.glob('*.py'):
                if not source.name.startswith('test_'):
                    shutil.copyfile(source, root/source.name)
            pack = fixture()
            (root/'manifest.json').write_bytes(b.frozen.canonical(pack['protocol']['manifest']))
            (root/'protocol.json').write_bytes(b.frozen.canonical(pack))
            raw = b'case,baseline,a,c\nx,0,1,?\n'
            (root/'results.csv').write_bytes(raw)
            def cli(*args):
                return subprocess.run([sys.executable, '-B', 'bound_protocol.py', *args],
                    cwd=root, capture_output=True, timeout=30)
            frozen = cli('freeze', '--manifest', 'manifest.json', '--expected-plan-sha256',
                         pack['protocol']['manifest']['plan_sha256'], '--margin', '0.10',
                         '--omission-policy', 'restore-as-unknown')
            self.assertEqual(frozen.returncode, 0, frozen.stderr)
            self.assertEqual(json.loads(frozen.stdout), pack)
            args = ['check', '--protocol', 'protocol.json', '--results', 'results.csv',
                    '--expected-protocol-sha256', pack['protocol_sha256'],
                    '--expected-results-sha256', b.frozen.digest(raw)]
            checked = cli(*args)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(json.loads(checked.stdout), run(pack, raw)[0])
            self.assertEqual(cli(*args, '--emit-csv').stdout, run(pack, raw)[1])
            for tail in [['--margin', '0'], ['--restore-omitted-cases']]:
                failed = cli(*args, *tail)
                self.assertEqual(failed.returncode, 2)
                self.assertEqual(failed.stdout, b'')
            (root/'protocol.json').write_text('{}')
            failed = cli(*args, '--emit-csv')
            self.assertEqual(failed.returncode, 2)
            self.assertEqual(failed.stdout, b'')
            self.assertEqual((root/'results.csv').read_bytes(), raw)
            # Workspace containment uses real paths, including symlinks.
            (root/'escape.json').symlink_to(Path(__file__).resolve())
            args[2] = 'escape.json'
            self.assertEqual(cli(*args).returncode, 2)

    def test_snapshot_provenance(self):
        root = Path(__file__).parent
        for item in json.loads((root/'provenance.json').read_text())['snapshots']:
            self.assertEqual(b.frozen.digest((root/item['snapshot']).read_bytes()), item['sha256'])


if __name__ == '__main__':
    unittest.main()
