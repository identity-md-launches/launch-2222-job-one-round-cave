import json
import subprocess
import sys
import tempfile
import unittest
import random
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

from uncertainty_lens import MAX_EVENTS, MAX_INPUT_BYTES, analyze, load_events


SCRIPT = Path(__file__).with_name("uncertainty_lens.py")


class LensTests(unittest.TestCase):
    def test_decimal_rounding_cannot_invent_order(self):
        payload = ('[{"id":"a","start":0,"end":1.00000000000000003},'
                   '{"id":"b","start":1.00000000000000002,"end":2}]')
        # Reproduce the old failure independently using binary JSON floats.
        self.assertEqual(len(analyze(json.loads(payload))["definite_orders"]), 1)
        out = analyze(load_events(payload))
        self.assertEqual(out["definite_orders"], [])
        self.assertEqual(out["uncertain_pairs"][0]["reason"], "intervals overlap")
        proc = subprocess.run([sys.executable, "-B", str(SCRIPT), "-"],
                              input=payload.encode(), capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), out)

    def test_tiny_large_and_equivalent_points(self):
        for left, right in (("1e-4000", "2e-4000"), ("1e4000", "2e4000"),
                            ("9007199254740992.0", "9007199254740993.0")):
            payload = ('[{"id":"a","start":%s,"end":%s},'
                       '{"id":"b","start":%s,"end":%s}]') % (left, left, right, right)
            self.assertEqual(analyze(load_events(payload))["definite_orders"],
                             [{"before": "a", "after": "b"}])
        out = analyze(load_events('[{"id":"a","start":1.00,"end":1e0},'
                                  '{"id":"b","start":1,"end":1.000}]'))
        self.assertEqual(out["definite_orders"], [])
        self.assertEqual(out["uncertain_pairs"][0]["reason"], "coincident timestamp points")

    def test_decimal_comparisons_ignore_context_precision(self):
        with localcontext() as context:
            context.prec = 2
            values = load_events('[{"id":"a","start":0,"end":1.00000000003},'
                                 '{"id":"b","start":1.00000000002,"end":2}]')
            self.assertEqual(analyze(values)["definite_orders"], [])
        for value in (Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity")):
            with self.assertRaises(ValueError):
                analyze([{"id": "a", "start": value, "end": 2}])

    def test_numeric_resource_limits(self):
        for number in ("1e10001", "1e-10001", "1" * 257, "0." + "1" * 255):
            with self.assertRaises(ValueError):
                load_events('[{"id":"a","start":0,"end":' + number + '}]')
        for number in ("1e10000", "1e-10000", "1" * 256):
            self.assertEqual(len(load_events('[{"id":"a","start":0,"end":' + number + '}]')), 1)

    def test_seeded_decimal_pairs_against_fraction_oracle(self):
        rng = random.Random(37)
        for _ in range(500):
            tokens = [str(rng.randrange(-1000, 1000)) + "e-" + str(rng.randrange(10, 30))
                      for _ in range(4)]
            a, b = sorted(tokens[:2], key=Fraction)
            c, d = sorted(tokens[2:], key=Fraction)
            payload = ('[{"id":"a","start":%s,"end":%s},'
                       '{"id":"b","start":%s,"end":%s}]') % (a, b, c, d)
            out = analyze(load_events(payload))
            av, bv, cv, dv = map(Fraction, (a, b, c, d))
            expected = []
            if not av == bv == cv == dv:
                if bv <= cv:
                    expected = [{"before": "a", "after": "b"}]
                elif dv <= av:
                    expected = [{"before": "b", "after": "a"}]
            self.assertEqual(out["definite_orders"], expected)
            self.assertEqual(len(out["uncertain_pairs"]), 0 if expected else 1)

    def test_touching_is_ordered_and_overlap_is_uncertain(self):
        out = analyze([{"id": "a", "start": 0, "end": 2},
                       {"id": "b", "start": 2, "end": 4},
                       {"id": "c", "start": 1, "end": 3}])
        self.assertIn({"before": "a", "after": "b"}, out["definite_orders"])
        self.assertEqual(out["uncertain_pairs"], [
            {"events": ["a", "c"], "reason": "intervals overlap"},
            {"events": ["b", "c"], "reason": "intervals overlap"}])

    def test_bad_interval(self):
        with self.assertRaises(ValueError):
            analyze([{"id": "bad", "start": 2, "end": 1}])

    def test_coincident_points_never_invent_order(self):
        a = {"id": "a", "start": 4, "end": 4}
        b = {"id": "b", "start": 4, "end": 4}
        for events in ([a, b], [b, a]):
            result = analyze(events)
            self.assertEqual(result["definite_orders"], [])
            self.assertEqual(len(result["uncertain_pairs"]), 1)
            self.assertEqual(result["uncertain_pairs"][0]["reason"],
                             "coincident timestamp points")

    def test_distinct_points_and_point_at_boundary(self):
        a = {"id": "a", "start": 2, "end": 2}
        b = {"id": "b", "start": 3, "end": 3}
        for events in ([a, b], [b, a]):
            self.assertEqual(analyze(events)["definite_orders"],
                             [{"before": "a", "after": "b"}])
        interval = {"id": "interval", "start": 0, "end": 2}
        self.assertEqual(analyze([a, interval])["definite_orders"],
                         [{"before": "interval", "after": "a"}])
        spanning = {"id": "span", "start": 1, "end": 4}
        self.assertEqual(analyze([a, spanning])["definite_orders"], [])

    def test_cli_workspace_paths_and_symlink_escape(self):
        # All fixtures stay in the assignment's explicitly allowed scratch area.
        scratch = Path("test/scratch")
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            root = Path(directory).resolve()
            workspace = root / "workspace"
            workspace.mkdir()
            payload = '[{"id":"local","start":1,"end":2}]'
            (workspace / "events.json").write_text(payload, encoding="utf-8")
            for name in ("events.json", str(workspace / "events.json")):
                proc = subprocess.run([sys.executable, "-B", str(SCRIPT.resolve()), name],
                                      cwd=workspace, capture_output=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(json.loads(proc.stdout)["events"], 1)
            (workspace / "escape.json").symlink_to(root / "absent.json")
            for name in ("../absent.json", str(root / "absent.json"), "escape.json"):
                proc = subprocess.run([sys.executable, "-B", str(SCRIPT.resolve()), name],
                                      cwd=workspace, capture_output=True)
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn(b"inside the current workspace", proc.stderr)

    def test_pair_partition_and_reversal(self):
        # Exhaust all small integer intervals, including exact points.
        intervals = [(a, b) for a in range(4) for b in range(a, 4)]
        for a, b in intervals:
            for c, d in intervals:
                left = {"id": "a", "start": a, "end": b}
                right = {"id": "b", "start": c, "end": d}
                forward = analyze([left, right])
                reverse = analyze([right, left])
                self.assertEqual(forward["definite_orders"], reverse["definite_orders"])
                self.assertEqual(len(forward["definite_orders"]) +
                                 len(forward["uncertain_pairs"]), 1)
                if a == b == c == d:
                    self.assertEqual(forward["definite_orders"], [])

    def test_nonfinite_boolean_and_duplicate_ids_rejected(self):
        for value in (float("nan"), float("inf"), -float("inf"), True, False):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "finite nonboolean"):
                analyze([{"id": "a", "start": value, "end": 2}])
            with self.subTest(end=value), self.assertRaisesRegex(ValueError, "finite nonboolean"):
                analyze([{"id": "a", "start": 0, "end": value}])
        with self.assertRaisesRegex(ValueError, "duplicate event id"):
            analyze([{"id": "same", "start": 0, "end": 1},
                     {"id": "same", "start": 1, "end": 2}])

    def test_array_and_event_limits(self):
        with self.assertRaisesRegex(ValueError, "JSON array"):
            analyze({"id": "a", "start": 1, "end": 2})
        events = [{"id": str(i), "start": i, "end": i + 1} for i in range(MAX_EVENTS)]
        out = analyze(events)
        self.assertEqual(len(out["definite_orders"]), MAX_EVENTS * (MAX_EVENTS - 1) // 2)
        with self.assertRaisesRegex(ValueError, "too many events"):
            analyze(events + [{"id": "extra", "start": 0, "end": 1}])

    def test_cli_rejects_nonfinite_json_and_oversize_input(self):
        for payload in (b'[{"id":"a","start":NaN,"end":2}]',
                        b'[{"id":"a","start":0,"end":Infinity}]',
                        b" " * (MAX_INPUT_BYTES + 1)):
            with self.subTest(payload=payload[:60]):
                proc = subprocess.run([sys.executable, "-B", str(SCRIPT), "-"],
                                      input=payload, capture_output=True, check=False)
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn(b"error:", proc.stderr)

    def test_cli_demo_is_stable(self):
        payload = b'[{"id":"first","start":1,"end":2},{"id":"second","start":2,"end":3}]'
        proc = subprocess.run([sys.executable, "-B", str(SCRIPT), "-"],
                              input=payload, capture_output=True, check=True)
        self.assertEqual(json.loads(proc.stdout)["definite_orders"],
                         [{"before": "first", "after": "second"}])


if __name__ == "__main__":
    unittest.main()
