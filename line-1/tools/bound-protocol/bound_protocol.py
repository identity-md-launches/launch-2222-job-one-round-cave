#!/usr/bin/env python3
"""Pin the practical margin and omission policy before a binary benchmark."""
import argparse
from decimal import Decimal
from fractions import Fraction
import json
import re
import sys
import roster_bounds as roster

frozen = roster.frozen
SCHEMA = 'bound-benchmark-protocol-v1'
POLICIES = ('reject', 'restore-as-unknown')


def pin(value, name):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError(name + ' must be 64 lowercase hex characters')
    return value


def body(manifest_raw, plan_pin, margin, omission_policy):
    pin(plan_pin, 'plan pin')
    plan = frozen.verify_manifest(manifest_raw, plan_pin)
    if (len(plan['cases']) > 512 or
            any(not roster.missing.engine.label(x) for x in plan['cases'] + plan['candidates'])):
        raise ValueError('plan exceeds Roster Bounds case or label limits')
    roster.missing.engine.decimal(margin, 'margin', Fraction(0), Fraction(1))
    if omission_policy not in POLICIES:
        raise ValueError('omission_policy must be reject or restore-as-unknown')
    return {'schema': SCHEMA,
            'manifest': {'schema': 'frozen-benchmark-manifest-v1',
                         'plan': plan, 'plan_sha256': plan_pin},
            'margin': format(Decimal(margin).normalize(), 'f'),
            'omission_policy': omission_policy}


def freeze(manifest_raw, plan_pin, margin, omission_policy):
    value = body(manifest_raw, plan_pin, margin, omission_policy)
    result = {'protocol': value, 'protocol_sha256': frozen.digest(frozen.canonical(value))}
    if len(frozen.canonical(result)) > frozen.MAX_BYTES:
        raise ValueError('protocol exceeds 2 MiB')
    return result


def verify(protocol_raw, protocol_pin):
    pin(protocol_pin, 'protocol pin')
    pack = frozen.parse_json(protocol_raw)
    if not isinstance(pack, dict) or set(pack) != {'protocol', 'protocol_sha256'}:
        raise ValueError('invalid protocol envelope')
    value = pack['protocol']
    if (not isinstance(value, dict) or
            set(value) != {'schema', 'manifest', 'margin', 'omission_policy'} or
            value['schema'] != SCHEMA):
        raise ValueError('invalid protocol shape')
    manifest = value['manifest']
    if not isinstance(manifest, dict):
        raise ValueError('invalid manifest')
    normalized = body(frozen.canonical(manifest), manifest.get('plan_sha256'),
                      value['margin'], value['omission_policy'])
    actual = frozen.digest(frozen.canonical(normalized))
    if actual != protocol_pin or pack['protocol_sha256'] != actual:
        raise ValueError('protocol digest mismatch; use the independently retained pre-outcome pin')
    return normalized


def check(protocol_raw, results_raw, protocol_pin, results_pin):
    # All analysis controls come from the pinned protocol; no runtime override.
    value = verify(protocol_raw, protocol_pin)
    manifest = value['manifest']
    report, normalized = roster.check(
        frozen.canonical(manifest), results_raw, manifest['plan_sha256'], results_pin,
        Fraction(value['margin']), value['omission_policy'] == 'restore-as-unknown')
    return {'schema': 'bound-benchmark-check-v1',
            'protocol_sha256': protocol_pin,
            'protocol_bytes_sha256': frozen.digest(protocol_raw),
            'bound_settings': {'practical_margin': value['margin'],
                               'omission_policy': value['omission_policy']},
            'roster_report': report,
            'limits': [
                'The outer protocol pin additionally binds margin and omission policy; the nested legacy-plan caveat applies only to its own pin.',
                'Retain this protocol pin independently before outcomes. Hashes do not establish timing, honest execution or scoring.',
                'IDs do not bind case payloads or executable bytes. Preserve those separately, for example with Benchmark Seal.',
                'Fixed sample size, iid latent case vectors, full family and accurate scoring remain assumptions. No optional stopping or selective publication.',
                'Restoration preserves unknown outcomes and the denominator; it does not measure missing cases.',
            ]}, normalized


def demo():
    plan = {'schema': frozen.SCHEMA, 'baseline': 'synthetic-base-v1',
            'candidates': ['synthetic-a-v1', 'synthetic-b-v1'],
            'pass_rule': 'Synthetic exact match only.', 'alpha': '0.05',
            'cases': ['empty', 'unicode', 'truncated']}
    manifest = frozen.freeze(frozen.canonical(plan))
    raw = b'case,baseline,synthetic-a-v1,synthetic-b-v1\nempty,1,1,1\ntruncated,0,1,?\n'
    pack = freeze(frozen.canonical(manifest), manifest['plan_sha256'], '0.10', 'restore-as-unknown')
    retained = pack['protocol_sha256']
    result, normalized = check(frozen.canonical(pack), raw, retained, frozen.digest(raw))
    rejected = {}
    for name, margin, policy in [('changed_margin', '0.2', 'restore-as-unknown'),
                                 ('changed_policy', '0.1', 'reject')]:
        replacement = freeze(frozen.canonical(manifest), manifest['plan_sha256'], margin, policy)
        try:
            check(frozen.canonical(replacement), raw, retained, frozen.digest(raw))
        except ValueError as exc:
            rejected[name] = str(exc)
        else:
            raise RuntimeError('demo accepted replacement protocol')
    return {'data_kind': 'synthetic_demonstration', 'protocol': pack,
            'report': result, 'normalized_csv': normalized.decode(), 'rejected': rejected}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo')
    create = sub.add_parser('freeze')
    create.add_argument('--manifest', required=True)
    create.add_argument('--expected-plan-sha256', required=True)
    create.add_argument('--margin', required=True)
    create.add_argument('--omission-policy', choices=POLICIES, required=True)
    run = sub.add_parser('check')
    run.add_argument('--protocol', required=True)
    run.add_argument('--results', required=True)
    run.add_argument('--expected-protocol-sha256', required=True)
    run.add_argument('--expected-results-sha256', required=True)
    run.add_argument('--emit-csv', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        elif args.command == 'freeze':
            result = freeze(frozen.read_workspace(args.manifest), args.expected_plan_sha256,
                            args.margin, args.omission_policy)
        else:
            result, normalized = check(frozen.read_workspace(args.protocol),
                frozen.read_workspace(args.results), args.expected_protocol_sha256,
                args.expected_results_sha256)
            if args.emit_csv:
                sys.stdout.buffer.write(normalized)
                return 0
    except (ValueError, OSError, RecursionError) as exc:
        parser.exit(2, 'error: ' + str(exc)[:240] + '\n')
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
