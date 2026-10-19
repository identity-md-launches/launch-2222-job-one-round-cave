#!/usr/bin/env python3
"""Freeze rules, run the existing fixed policies, and display their actual results."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
POLICY = 'line-1/tools/policy-benchmark/policy_benchmark.py'
DISPLAY = 'shared/protocol-bounds-display/protocol_bounds_display.py'


def run(script, *args):
    result = subprocess.run([sys.executable, '-B', script, *args], cwd=ROOT,
                            capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError(result.stderr.decode('utf-8', errors='replace')[:400])
    return json.loads(result.stdout)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode()


def main():
    scratch = ROOT / 'test/scratch'
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as temporary:
        folder = Path(temporary)
        pack = run(POLICY, 'freeze', '--cases', 'line-1/tools/policy-benchmark/cases.json')
        manifest = pack['content']['manifest']
        (folder / 'manifest.json').write_bytes(canonical(manifest))
        # These choices and their local pin are retained before executing policies.
        protocol = run(DISPLAY, 'freeze', '--manifest', str(folder / 'manifest.json'),
            '--expected-plan-sha256', manifest['plan_sha256'], '--margin', '0.1',
            '--omission-policy', 'reject')
        protocol_pin = protocol['protocol_sha256']
        (folder / 'protocol.json').write_bytes(canonical(protocol))
        (folder / 'pack.json').write_bytes(canonical(pack))
        receipt = run(POLICY, 'run', '--pack', str(folder / 'pack.json'),
                      '--expected-seal-sha256', pack['seal_sha256'])
        (folder / 'receipt.json').write_bytes(canonical(receipt))
        replay = run(POLICY, 'recheck', '--receipt', str(folder / 'receipt.json'),
            '--expected-seal-sha256', pack['seal_sha256'],
            '--expected-receipt-sha256', receipt['receipt_sha256'])
        raw = base64.b64decode(receipt['body']['results_b64'], validate=True)
        (folder / 'results.csv').write_bytes(raw)
        result = run(DISPLAY, 'check', '--protocol', str(folder / 'protocol.json'),
            '--results', str(folder / 'results.csv'), '--expected-protocol-sha256', protocol_pin,
            '--expected-results-sha256', hashlib.sha256(raw).hexdigest())
        result['data_kind'] = 'measured_local_execution_on_curated_cases'
        result['execution'] = {'seal_sha256': pack['seal_sha256'],
            'receipt_sha256': receipt['receipt_sha256'], 'recheck': replay['status'],
            'case_source': 'line-1/tools/policy-benchmark/cases.json',
            'choices_frozen_before_local_execution': True,
            'choices': {'margin': '0.1', 'omission_policy': 'reject'},
            'limitations': 'Local ordering of steps is not independent preregistration or execution attestation. '
                'Hand-selected related cases are not iid population samples; confidence bounds here illustrate arithmetic only.'}
        print(json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2))


if __name__ == '__main__':
    main()
