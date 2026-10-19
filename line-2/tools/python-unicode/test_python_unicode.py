import contextlib
import codecs
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import random
import subprocess
import sys
import unicodedata
import unittest

spec = importlib.util.spec_from_file_location('python_unicode', Path(__file__).with_name('python_unicode.py'))
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class PythonUnicodeTests(unittest.TestCase):
    def details(self, data):
        return engine.scan(data)['details']

    def test_demo(self):
        self.assertEqual([d['decoded_codepoint']['codepoint'] for d in self.details(engine.DEMO)],
                         ['U+0456', 'U+202E', 'U+1F438'])

    def test_fixed_width(self):
        ds = self.details(br'\u0041b\U00000042c')
        self.assertEqual([bytes.fromhex(d['source_escape_hex']) for d in ds], [br'\u0041', br'\U00000042'])
        self.assertEqual([d['decoded_codepoint']['utf8_hex'] for d in ds], ['41', '42'])

    def test_names_aliases_and_case(self):
        ds = self.details(br'\N{LATIN CAPITAL LETTER A}\N{NULL}\N{right-to-left override}')
        self.assertEqual([d['decoded_codepoint']['codepoint'] for d in ds], ['U+0041', 'U+0000', 'U+202E'])

    def test_named_sequence_not_scalar(self):
        self.assertGreater(len(unicodedata.lookup('KEYCAP DIGIT ONE')), 1)
        d = self.details(br'\N{KEYCAP DIGIT ONE}')[0]
        self.assertEqual(d['issue'], 'named-sequence-not-a-python-scalar-escape')
        self.assertIsNone(d['decoded_codepoint'])

    def test_surrogates_remain_separate(self):
        ds = self.details(br'\uD83D\uDC38')
        self.assertEqual([d['kind'] for d in ds], ['surrogate-code-unit'] * 2)
        self.assertEqual([d['decoded_codepoint']['codepoint'] for d in ds], ['U+D83D', 'U+DC38'])
        self.assertTrue(all(d['decoded_codepoint']['utf8_hex'] is None for d in ds))

    def test_malformed_hex_and_recovery(self):
        for bad in [br'\u12', br'\U1234567', br'\UFFFFFFFF', br'\u', br'\U00110000']:
            ds = self.details(bad + br'\u0456')
            self.assertEqual(ds[0]['kind'], 'malformed')
            self.assertEqual(ds[1]['decoded_codepoint']['codepoint'], 'U+0456')
        self.assertEqual(self.details(br'\u12Z')[0]['source_byte_range'], [0, 4])

    def test_malformed_names_and_recovery(self):
        for bad in [br'\N', br'\Nx', br'\N{', br'\N{}', br'\N{NO SUCH NAME}',
                    b'\\N{bad\n', b'\\N{bad\r', b'\\N{' + b'A' * 257 + b'}', '\\N{é}'.encode()]:
            ds = self.details(bad + br'\u0456')
            self.assertEqual(ds[0]['kind'], 'malformed', bad)
            self.assertEqual(ds[-1]['decoded_codepoint']['codepoint'], 'U+0456', bad)

    def test_backslash_parity_and_non_recursion(self):
        self.assertEqual(self.details(br'\\u202e'), [])
        self.assertEqual(len(self.details(br'\\\u202e')), 1)
        ds = self.details(br'\u005cu202e\N{REVERSE SOLIDUS}u202e\x5cu202e')
        self.assertEqual([d['decoded_codepoint']['codepoint'] for d in ds], ['U+005C', 'U+005C'])
        self.assertEqual(self.details(b'trailing\\'), [])

    def test_literal_unicode_not_an_escape(self):
        self.assertEqual(self.details('é🐸\u202e'.encode()), [])

    def test_exact_source_coordinates(self):
        data = 'é\n🐸 '.encode() + br'\u0456' + b'\r\n' + br'\N{NULL}'
        ds = self.details(data)
        self.assertEqual(ds[0]['source_byte_range'], [8, 14])
        self.assertEqual((ds[0]['source_line'], ds[0]['source_byte_column']), (2, 6))
        self.assertEqual((ds[1]['source_line'], ds[1]['source_byte_column']), (3, 1))
        for d in ds:
            a, b = d['source_byte_range']
            self.assertEqual(data[a:b].hex(), d['source_escape_hex'])
            self.assertEqual(hashlib.sha256(data[a:b]).hexdigest(), d['source_span_sha256'])

    def test_seeded_codepoints(self):
        rng = random.Random(39)
        for _ in range(600):
            cp = rng.randrange(0x110000)
            raw = ('\\U%08X' % cp).encode()
            d = self.details(raw)[0]
            self.assertEqual(codecs.decode(raw, 'unicode_escape'), chr(cp))
            self.assertEqual(d['decoded_codepoint'], engine.scalar(cp))
            self.assertEqual(d['source_escape_hex'], raw.hex())
            if not 0xd800 <= cp <= 0xdfff:
                self.assertEqual(bytes.fromhex(d['decoded_codepoint']['utf8_hex']).decode(), chr(cp))
                name = unicodedata.name(chr(cp), None)
                if name:
                    named_raw = ('\\N{' + name + '}').encode()
                    self.assertEqual(codecs.decode(named_raw, 'unicode_escape'), chr(cp))
                    named = self.details(named_raw)[0]
                    self.assertEqual(named['decoded_codepoint']['codepoint'], f'U+{cp:04X}')

    def test_complete_capped_counts(self):
        report = engine.scan(br'\u0456\uD800\UFFFFFFFF' * 500, 1)
        self.assertEqual(report['candidate_count'], 1500)
        self.assertEqual(report['omitted_details'], 1499)
        self.assertEqual(report['counts_by_kind'], {'non-ascii-or-control': 500, 'surrogate-code-unit': 500, 'malformed': 500})
        self.assertEqual(engine.scan(engine.DEMO, 0)['details'], [])

    def test_validation(self):
        for data in [b'\xff', b'x' * (engine.MAX_BYTES + 1), 'text', bytearray(b'x')]:
            with self.assertRaises(ValueError):
                engine.scan(data)
        for cap in [-1, 1001, True, 0.5]:
            with self.assertRaises(ValueError):
                engine.scan(b'', cap)
        self.assertEqual(engine.scan(b'x' * engine.MAX_BYTES)['candidate_count'], 0)

    def test_cli_ascii_and_statuses(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(engine.main(['--demo']), 0)
        out.getvalue().encode('ascii')
        self.assertEqual(json.loads(out.getvalue())['source_kind'], 'synthetic-demo')
        cmd = [sys.executable, '-B', str(Path(engine.__file__))]
        result = subprocess.run(cmd + ['--file', str(Path(__file__))], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertGreater(json.loads(result.stdout)['candidate_count'], 0)
        result = subprocess.run(cmd + ['--demo', '--max-details', '-1'], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')

    def test_file_restriction(self):
        with self.assertRaises(ValueError):
            engine.read_selected(Path.cwd().parent)
        with self.assertRaises(ValueError):
            engine.read_selected(Path.cwd())
        self.assertEqual(engine.read_selected(Path(__file__)), Path(__file__).read_bytes())


if __name__ == '__main__':
    unittest.main()
