#!/usr/bin/env python3
"""Bind incomplete paired-binary bounds to the whole independently pinned roster."""
import argparse
import csv
import hashlib
import io
import json
import re
from fractions import Fraction as F
import frozen_engine as frozen
import missing_bounds as missing

InputError = ValueError


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require_pin(raw, pin):
    if not isinstance(pin, str) or not re.fullmatch('[0-9a-f]{64}', pin):
        raise InputError('retained results pin must be 64 lowercase hex characters')
    if digest(raw) != pin:
        raise InputError('results SHA-256 mismatch')


def check(manifest_raw, results_raw, plan_pin, results_pin, margin=F(1, 10),
          restore_omitted_cases=False):
    """Return a complete report and normalized CSV; never infer observed outcomes."""
    if type(restore_omitted_cases) is not bool:
        raise InputError('restore_omitted_cases must be boolean')
    if not isinstance(plan_pin, str):
        raise InputError('retained plan pin required')
    plan = frozen.verify_manifest(manifest_raw, plan_pin)
    if len(plan['cases']) > missing.engine.MAX_CASES:
        raise InputError('Missing Bounds supports at most 512 planned cases')
    if any(not missing.engine.label(x) for x in plan['cases'] + plan['candidates']):
        raise InputError('case and candidate labels must satisfy Missing Bounds: 1–200 characters, no category-C text')
    if not isinstance(results_raw, bytes) or len(results_raw) > frozen.MAX_BYTES:
        raise InputError('results must be bytes, at most 2 MiB')
    require_pin(results_raw, results_pin)
    header = ['case', 'baseline'] + plan['candidates']
    planned = set(plan['cases'])
    observations = {}
    try:
        reader = csv.reader(io.StringIO(results_raw.decode('utf-8-sig'), newline=''), strict=True)
        if next(reader, None) != header:
            raise InputError('CSV header must retain the entire planned candidate family in order')
        for row in reader:
            if len(row) != len(header):
                raise InputError('CSV row has missing or extra fields')
            case = row[0]
            if case not in planned or case in observations:
                raise InputError('unplanned or duplicate case ID')
            if any(x not in ('0', '1', '?') for x in row[1:]):
                raise InputError('outcomes must be literal 0, 1 or ?')
            observations[case] = row
    except (UnicodeError, csv.Error) as exc:
        raise InputError('invalid UTF-8 CSV') from exc
    absent = [case for case in plan['cases'] if case not in observations]
    if absent and not restore_omitted_cases:
        raise InputError(f'{len(absent)} planned cases omitted; provide explicit ? rows or opt into --restore-omitted-cases')
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(header)
    for case in plan['cases']:
        writer.writerow(observations.get(case, [case] + ['?'] * (len(header)-1)))
    normalized = output.getvalue().encode('utf-8')
    # Alpha comes from the verified prospective protocol, never from a CLI override.
    analysis = missing.analyze(normalized, F(plan['alpha']), margin)
    return {
        'schema': 'roster-bounds-v1',
        'status': 'pinned_roster_retained_with_explicit_unknowns',
        'plan_sha256': plan_pin,
        'manifest_bytes_sha256': digest(manifest_raw),
        'observation_bytes_sha256': digest(results_raw),
        'normalized_csv_sha256': digest(normalized),
        'baseline_version': plan['baseline'], 'pass_rule': plan['pass_rule'],
        'planned_case_order': plan['cases'], 'candidate_order': plan['candidates'],
        'supplied_case_count': len(observations),
        'restoration_authorized': restore_omitted_cases,
        'restored_all_unknown_case_ids': absent,
        'restored_unknown_cell_count': len(absent) * (len(header)-1),
        'supplied_unknown_cell_count': sum(x == '?' for r in observations.values() for x in r[1:]),
        'analysis': analysis,
        'limits': [
            'Unknowns are not measured outcomes. Restored rows are explicitly recorded, never scored as failures.',
            'Retain the plan pin before observations; hashes prove byte identity, not timing, execution or honesty.',
            'This legacy plan binds case IDs and labels, not case payloads or system code.',
            'Margin is caller-supplied and NOT covered by the legacy plan pin; choose and retain it prospectively.',
            'Use once at the fixed endpoint. Completing missing observations is not permission for optional stopping.',
            'The enclosed analysis retains its iid latent-case, fixed-family and accurate-scoring assumptions.',
        ],
    }, normalized


def demo():
    plan = {'schema': frozen.SCHEMA, 'baseline': 'synthetic-base-v1',
            'candidates': ['synthetic-a-v1', 'synthetic-b-v1'],
            'pass_rule': 'Synthetic fixture only: exact expected answer.',
            'alpha': '0.05', 'cases': ['empty', 'unicode', 'truncated']}
    manifest = frozen.freeze(frozen.canonical(plan))
    raw = b'case,baseline,synthetic-a-v1,synthetic-b-v1\ntruncated,0,1,?\nempty,1,1,1\n'
    args = (frozen.canonical(manifest), raw, manifest['plan_sha256'], digest(raw))
    try:
        check(*args)
    except ValueError as exc:
        rejection = str(exc)
    else:
        raise RuntimeError('demo did not reject omitted planned case')
    report, normalized = check(*args, restore_omitted_cases=True)
    return {'data_kind': 'synthetic_demonstration', 'default_rejection': rejection,
            'report': report, 'normalized_csv': normalized.decode('utf-8')}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo')
    run = sub.add_parser('check')
    run.add_argument('--manifest', required=True)
    run.add_argument('--results', required=True)
    run.add_argument('--expected-plan-sha256', required=True)
    run.add_argument('--expected-results-sha256', required=True)
    run.add_argument('--margin', default='0.1')
    run.add_argument('--restore-omitted-cases', action='store_true')
    run.add_argument('--emit-csv', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        else:
            margin = missing.engine.decimal(args.margin, 'margin', F(0), F(1))
            result, normalized = check(frozen.read_workspace(args.manifest),
                frozen.read_workspace(args.results), args.expected_plan_sha256,
                args.expected_results_sha256, margin, args.restore_omitted_cases)
            if args.emit_csv:
                import sys
                sys.stdout.buffer.write(normalized)
                return 0
    except (ValueError, OSError, RecursionError) as exc:
        parser.exit(2, 'error: ' + str(exc)[:240] + '\n')
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
