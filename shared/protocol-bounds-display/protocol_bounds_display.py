#!/usr/bin/env python3
"""Display benchmark bounds using settings from a verified pre-outcome protocol."""
import argparse
from contextlib import contextmanager
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import sys

import missing_bounds_display as display

HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / 'engines' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextmanager
def imports(**modules):
    """Resolve upstream ordinary imports locally, restoring caller modules."""
    saved = {name: sys.modules.get(name) for name in modules}
    sys.modules.update(modules)
    try:
        yield
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


frozen = load('protocol_display_frozen', 'frozen_engine.py')
with imports(frozen_engine=frozen, missing_bounds=display.missing):
    roster = load('protocol_display_roster', 'roster_bounds.py')
with imports(roster_bounds=roster):
    protocol = load('protocol_display_protocol', 'bound_protocol.py')


def summarize(protocol_raw, observations, protocol_pin, results_pin, places=2):
    display.display_interval(F(0), F(0), places)
    settings = protocol.verify(protocol_raw, protocol_pin)
    evidence, normalized = protocol.check(protocol_raw, observations, protocol_pin, results_pin)
    original = evidence['roster_report']
    # Neither inference settings nor restoration policy can be overridden here.
    view = display.summarize(normalized, original['normalized_csv_sha256'],
                             F(settings['manifest']['plan']['alpha']),
                             F(settings['margin']), places)
    if original['analysis'] != view['analysis']:
        raise ValueError('protocol and display analysis disagree')
    return {
        'schema': 'protocol-bounds-display/1', 'protocol_evidence': evidence,
        'normalized_csv': normalized.decode('utf-8'), 'reading_view': view,
        'limits': [
            'Retain the protocol pin independently before observations; a hash does not prove when choices were made.',
            'Alpha, family, roster, margin and omission policy come from the verified protocol. Display precision is not pinned.',
            'Lower endpoints round down and upper endpoints round up; precision cannot create an exact criterion.',
            'The nested legacy-plan margin caveat concerns its inner pin; the outer protocol additionally binds margin and omission policy.',
            'Original observation, protocol-byte and normalized-CSV identities are separate. Unknowns are never invented observations.',
            'Fixed sample size, iid latent case vectors, full prospective family and accurate scoring remain assumptions.',
            'No optional stopping, selective reporting, measurement validation, execution attestation or deployment recommendation.',
            'Case IDs do not bind payloads or executable bytes; retain those separately, for example with Benchmark Seal.',
        ],
    }


def demo():
    source = protocol.demo()
    pack = source['protocol']
    raw = b'case,baseline,synthetic-a-v1,synthetic-b-v1\nempty,1,1,1\ntruncated,0,1,?\n'
    result = summarize(frozen.canonical(pack), raw, pack['protocol_sha256'], roster.digest(raw))
    result['data_kind'] = 'synthetic_demonstration'
    result['replacement_protocols_rejected'] = source['rejected']
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo')
    create = sub.add_parser('freeze')
    create.add_argument('--manifest', required=True)
    create.add_argument('--expected-plan-sha256', required=True)
    create.add_argument('--margin', required=True)
    create.add_argument('--omission-policy', choices=protocol.POLICIES, required=True)
    check = sub.add_parser('check')
    check.add_argument('--protocol', required=True)
    check.add_argument('--results', required=True)
    check.add_argument('--expected-protocol-sha256', required=True)
    check.add_argument('--expected-results-sha256', required=True)
    check.add_argument('--places', type=int, default=2)
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        elif args.command == 'freeze':
            result = protocol.freeze(frozen.read_workspace(args.manifest), args.expected_plan_sha256,
                                     args.margin, args.omission_policy)
        else:
            result = summarize(frozen.read_workspace(args.protocol), frozen.read_workspace(args.results),
                               args.expected_protocol_sha256, args.expected_results_sha256, args.places)
            result['data_kind'] = 'user_supplied_benchmark'
        rendered = json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2) + '\n'
    except (ValueError, TypeError, OSError, OverflowError, RecursionError) as exc:
        parser.exit(2, 'protocol-bounds-display: ' + ascii(str(exc))[:240] + '\n')
    sys.stdout.write(rendered)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
