"""Check that a reporting handoff cannot silently change the frozen protocol."""
from fractions import Fraction as F
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import protocol_bounds_display as app


def fixture(policy='restore-as-unknown', margin='0.10'):
    manifest = app.frozen.freeze(app.frozen.canonical({
        'schema': app.frozen.SCHEMA, 'baseline': 'base', 'candidates': ['a', 'b'],
        'pass_rule': 'Exact synthetic fixture match', 'alpha': '0.050000000000000001',
        'cases': ['first', 'second', 'third'],
    }))
    return app.protocol.freeze(app.frozen.canonical(manifest), manifest['plan_sha256'], margin, policy)


def summarize(raw, pack=None, **kwargs):
    pack = fixture() if pack is None else pack
    return app.summarize(app.frozen.canonical(pack), raw, pack['protocol_sha256'],
                         app.roster.digest(raw), **kwargs)


class ProtocolDisplayTests(unittest.TestCase):
    def test_original_report_exact_alpha_margin_and_separate_hashes_survive(self):
        pack = fixture()
        raw = b'case,baseline,a,b\nthird,1,1,0\nfirst,0,1,?\n'
        result = summarize(raw, pack)
        original, normalized = app.protocol.check(app.frozen.canonical(pack), raw,
            pack['protocol_sha256'], app.roster.digest(raw))
        self.assertEqual(result['protocol_evidence'], original)
        self.assertEqual(result['normalized_csv'].encode(), normalized)
        roster = original['roster_report']
        self.assertEqual(roster['analysis'], result['reading_view']['analysis'])
        self.assertEqual(roster['analysis']['familywise_alpha'],
                         app.display.bounds.fraction(F('0.050000000000000001')))
        self.assertEqual(original['bound_settings'],
                         {'practical_margin': '0.1', 'omission_policy': 'restore-as-unknown'})
        self.assertEqual(roster['observation_bytes_sha256'], app.roster.digest(raw))
        self.assertEqual(roster['normalized_csv_sha256'], result['reading_view']['input_sha256'])
        self.assertNotEqual(roster['observation_bytes_sha256'], roster['normalized_csv_sha256'])

    def test_rehashed_replacement_margin_policy_and_plan_rejected(self):
        original = fixture()
        raw = b'case,baseline,a,b\nfirst,0,1,?\n'
        alternatives = [fixture(margin='0.2'), fixture(policy='reject')]
        manifest = original['protocol']['manifest']
        plan = dict(manifest['plan'], alpha='0.1')
        other = app.frozen.freeze(app.frozen.canonical(dict(plan, schema=app.frozen.SCHEMA)))
        alternatives.append(app.protocol.freeze(app.frozen.canonical(other), other['plan_sha256'],
                                                 '0.1', 'restore-as-unknown'))
        for replacement in alternatives:
            with self.assertRaises(ValueError):
                app.summarize(app.frozen.canonical(replacement), raw,
                              original['protocol_sha256'], app.roster.digest(raw))

    def test_pinned_reject_policy_cannot_be_relaxed(self):
        raw = b'case,baseline,a,b\nfirst,0,1,?\n'
        with self.assertRaises(ValueError):
            summarize(raw, fixture(policy='reject'))
        result = summarize(raw)
        roster = result['protocol_evidence']['roster_report']
        self.assertEqual(roster['restored_all_unknown_case_ids'], ['second', 'third'])
        self.assertEqual(roster['restored_unknown_cell_count'], 6)
        self.assertEqual(roster['supplied_unknown_cell_count'], 1)
        self.assertEqual(roster['analysis']['planned_cases_retained'], 3)

    def test_all_row_omissions_and_all_completions_stay_inside_display(self):
        rows = [b'first,0,1,1\n', b'second,1,0,1\n', b'third,0,1,0\n']
        for included in itertools.product((False, True), repeat=3):
            raw = b'case,baseline,a,b\n' + b''.join(r for r, keep in zip(rows, included) if keep)
            result = summarize(raw)
            normalized = result['normalized_csv'].encode()
            # Sample identification bounds are sharp for all binary completions.
            # Independently enumerate every possible unknown cell in this fixture.
            for completion in itertools.product((b'0', b'1'), repeat=normalized.count(b'?')):
                pieces = normalized.split(b'?')
                completed = pieces[0] + b''.join(v + tail for v, tail in zip(completion, pieces[1:]))
                data = [r.split(b',')[1:] for r in completed.splitlines()[1:]]
                for col, candidate in enumerate(result['reading_view']['candidates'], 1):
                    mean = sum(F(int(r[col]) - int(r[0]), 3) for r in data)
                    shown = candidate['sample_identification_percentage_points']
                    self.assertLessEqual(F(shown['lower']) / 100, mean)
                    self.assertGreaterEqual(F(shown['upper']) / 100, mean)

    def test_display_precision_cannot_create_population_criterion(self):
        for places in range(7):
            report = summarize(b'case,baseline,a,b\nfirst,0,1,?\n', places=places)
            for row in report['reading_view']['candidates']:
                for name, value in row['displayed_interval_criteria'].items():
                    self.assertFalse(value and not row['exact_criteria'][name])
                original = next(c for c in report['reading_view']['analysis']['candidates']
                                if c['name'] == row['candidate'])
                lo, hi = map(app.display.rational, original['candidate_minus_baseline_bounds'])
                shown = row['population_confidence_percentage_points']
                self.assertLessEqual(F(shown['lower']) / 100, lo)
                self.assertGreaterEqual(F(shown['upper']) / 100, hi)
        for places in (True, -1, 7, 1.0):
            with self.assertRaises(ValueError):
                summarize(b'case,baseline,a,b\n', places=places)

    def test_pin_and_family_errors_propagate(self):
        pack = fixture(); raw = b'case,baseline,a,b\nfirst,0,1,?\n'
        with self.assertRaises(ValueError):
            app.summarize(app.frozen.canonical(pack), raw, pack['protocol_sha256'], 'f' * 64)
        for bad in (b'case,baseline,a\nfirst,0,1\n', b'case,baseline,b,a\nfirst,0,1,1\n',
                    raw + raw.splitlines(keepends=True)[1], b'case,baseline,a,b\nother,0,1,1\n'):
            with self.assertRaises(ValueError):
                summarize(bad)

    def test_snapshots_are_pinned(self):
        here = Path(app.__file__).parent
        for row in json.loads((here / 'provenance.json').read_text()):
            self.assertEqual(hashlib.sha256((here / row['copy']).read_bytes()).hexdigest(), row['sha256'])

    def test_portable_cli_freeze_check_and_failures_without_partial_output(self):
        scratch = Path('test/scratch').resolve(); scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            folder = Path(tmp) / 'portable'
            shutil.copytree(Path(app.__file__).parent, folder, ignore=shutil.ignore_patterns('__pycache__'))
            pack = fixture(); raw = b'case,baseline,a,b\nfirst,0,1,?\n'
            (folder / 'manifest.json').write_bytes(app.frozen.canonical(pack['protocol']['manifest']))
            (folder / 'protocol.json').write_bytes(app.frozen.canonical(pack))
            (folder / 'results.csv').write_bytes(raw)
            def run(args):
                return subprocess.run([sys.executable, '-B', 'protocol_bounds_display.py', *args],
                                      cwd=folder, capture_output=True, timeout=30)
            freeze = run(['freeze', '--manifest', 'manifest.json', '--expected-plan-sha256',
                pack['protocol']['manifest']['plan_sha256'], '--margin', '0.10',
                '--omission-policy', 'restore-as-unknown'])
            self.assertEqual(freeze.returncode, 0, freeze.stderr)
            self.assertEqual(json.loads(freeze.stdout), pack)
            args = ['check', '--protocol', 'protocol.json', '--results', 'results.csv',
                    '--expected-protocol-sha256', pack['protocol_sha256'],
                    '--expected-results-sha256', app.roster.digest(raw)]
            good = run(args)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertEqual(json.loads(good.stdout), dict(summarize(raw, pack), data_kind='user_supplied_benchmark'))
            for extra in (['--margin', '0.2'], ['--restore-omitted-cases'], ['--alpha', '0.1'], ['--places', '7']):
                bad = run(args + extra)
                self.assertEqual(bad.returncode, 2)
                self.assertEqual(bad.stdout, b'')
            (folder / 'results.csv').write_bytes(raw + b'\n')
            bad = run(args); self.assertEqual(bad.returncode, 2); self.assertEqual(bad.stdout, b'')
            outside = Path(tmp) / 'outside.csv'; outside.write_bytes(raw)
            (folder / 'escape').symlink_to(outside)
            bad = run(args + ['--results', 'escape'])
            self.assertEqual(bad.returncode, 2); self.assertEqual(bad.stdout, b'')
            self.assertEqual((folder / 'protocol.json').read_bytes(), app.frozen.canonical(pack))


if __name__ == '__main__':
    unittest.main()
