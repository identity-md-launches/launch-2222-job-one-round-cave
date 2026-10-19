#!/usr/bin/env python3
"""Cite Python-style Unicode escape candidates without executing source text."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import stat
import sys
import unicodedata

MAX_BYTES = 2 * 1024 * 1024
HEX = b'0123456789abcdefABCDEF'
DEMO = br'user = "adm\u0456n"; direction = "\N{RIGHT-TO-LEFT OVERRIDE}"; frog = "\U0001F438"'


def scalar(value):
    char = chr(value)
    return {
        'codepoint': f'U+{value:04X}',
        'name': unicodedata.name(char, 'UNNAMED'),
        'category': unicodedata.category(char),
        'utf8_hex': None if 0xd800 <= value <= 0xdfff else char.encode('utf-8').hex(),
    }


def scan(data, max_details=100):
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise ValueError('input must be bytes of at most 2 MiB')
    if type(max_details) is not int or not 0 <= max_details <= 1000:
        raise ValueError('max_details must be an integer from 0 to 1000')
    data.decode('utf-8', 'strict')
    counts, details = Counter(), []
    i, previous, line, line_start = 0, 0, 1, 0
    while i < len(data):
        lo = data.find(b'\\', i)
        if lo < 0 or lo + 1 == len(data):
            break
        form = chr(data[lo + 1])
        i = lo + 2
        # Consume other backslash pairs once, so doubled backslashes do not
        # create spurious Unicode escapes. Never scan decoded output again.
        if form not in ('u', 'U', 'N'):
            continue
        line += data.count(b'\n', previous, lo)
        lf = data.rfind(b'\n', previous, lo)
        if lf >= 0:
            line_start = lf + 1
        previous = lo
        value, issue = None, None
        if form in ('u', 'U'):
            width = 4 if form == 'u' else 8
            start = i
            while i < len(data) and i - start < width and data[i] in HEX:
                i += 1
            if i - start != width:
                issue = 'incomplete-hex-escape'
            else:
                value = int(data[start:i], 16)
                if value > 0x10ffff:
                    issue, value = 'out-of-range', None
        elif i == len(data) or data[i] != ord('{'):
            issue = 'missing-name-brace'
        else:
            i += 1
            start = i
            while i < len(data) and data[i] not in b'}\\\r\n':
                i += 1
            if i == len(data) or data[i] != ord('}'):
                issue = 'unterminated-name'
            else:
                name = data[start:i]
                i += 1
                # Unicode character names and aliases are shorter than 256
                # bytes. Avoid passing huge adversarial names to lookup().
                if len(name) > 256:
                    issue = 'name-too-long'
                else:
                    try:
                        decoded = unicodedata.lookup(name.decode('ascii'))
                    except (KeyError, UnicodeError):
                        issue = 'unknown-name'
                    else:
                        if len(decoded) != 1:
                            issue = 'named-sequence-not-a-python-scalar-escape'
                        else:
                            value = ord(decoded)
        if issue:
            kind = 'malformed'
        elif 0xd800 <= value <= 0xdfff:
            kind = 'surrogate-code-unit'
        else:
            kind = 'ascii' if 0x20 <= value <= 0x7e else 'non-ascii-or-control'
        counts[kind] += 1
        if len(details) < max_details:
            raw = data[lo:i]
            details.append({
                'source_byte_range': [lo, i],
                'source_line': line, 'source_byte_column': lo - line_start + 1,
                'source_escape_hex': raw.hex(),
                'source_span_sha256': hashlib.sha256(raw).hexdigest(),
                'form': form, 'kind': kind, 'issue': issue,
                'decoded_codepoint': None if value is None else scalar(value),
            })
    total = sum(counts.values())
    return {
        'schema_version': 1, 'tool': 'python-unicode/1',
        'source_sha256': hashlib.sha256(data).hexdigest(), 'source_bytes': len(data),
        'unicode_version': unicodedata.unidata_version,
        'analysis_complete': True, 'candidate_count': total,
        'counts_by_kind': dict(sorted(counts.items())),
        'detail_cap': max_details, 'retained_details': len(details),
        'omitted_details': total - len(details), 'details': details,
        'limitations': [
            'Lexical candidates only, not a Python tokenizer/parser: comments, raw strings, bytes literals and non-Python text are included.',
            'No assertion that a candidate is interpreted by Python; string prefixes, quoting, f-strings, identifier grammar and rendering are outside scope.',
            'Only backslash-u (4 hex), backslash-U (8 hex) and backslash-N names are reviewed; other backslash pairs are skipped, not decoded.',
            'Named aliases use runtime Unicode tables; named sequences are rejected because Python named escapes require one code point.',
            'Surrogates are preserved as code units, have no UTF-8 bytes and are not combined; no replacement or recursive decoding occurs.',
            'Malformed hex stops before the first nonhex byte; malformed names stop before a backslash/newline. Later candidates remain visible.',
            'Ranges are zero-based half-open original UTF-8 bytes. Lines and byte columns are one-based, LF-only.',
            'Literal Unicode, other escape syntaxes and confusable fonts need separate review. No findings does not establish safety or benign intent.',
            'ASCII JSON is safe for terminal display, not HTML embedding. Hashes establish byte identity, not authenticity.',
        ],
    }


def read_selected(path):
    selected = Path(path).resolve(strict=True)
    if not selected.is_relative_to(Path.cwd().resolve()):
        raise ValueError('file must resolve within the current working directory')
    if not stat.S_ISREG(selected.stat().st_mode):
        raise ValueError('input must be a regular file')
    with selected.open('rb') as handle:
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('input exceeds 2 MiB')
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--demo', action='store_true')
    group.add_argument('--file', type=Path)
    parser.add_argument('--max-details', type=int, default=100)
    args = parser.parse_args(argv)
    try:
        report = scan(DEMO if args.demo else read_selected(args.file), args.max_details)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2
    report['source_kind'] = 'synthetic-demo' if args.demo else 'selected-file'
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if args.demo or not report['candidate_count'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
