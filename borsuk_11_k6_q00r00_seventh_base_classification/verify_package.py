#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def source_bundle_sha256(root: Path, names: list[str]) -> str:
    digest = hashlib.sha256()
    for name in names:
        data = (root / name).read_bytes()
        digest.update(name.encode('utf-8') + b'\0')
        digest.update(len(data).to_bytes(8, 'big'))
        digest.update(data)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--package-root', type=Path, required=True)
    parser.add_argument('--expected', type=Path, required=True)
    args = parser.parse_args()

    expected = json.loads(args.expected.read_text(encoding='utf-8'))
    summary_path = args.output / 'summary.json'
    grandchildren_path = args.output / 'grandchildren.csv'
    independent_path = args.output / 'independent-verification.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    independent = json.loads(independent_path.read_text(encoding='utf-8'))

    checks = {
        'summary_sha256': sha256_file(summary_path),
        'grandchildren_csv_sha256': sha256_file(grandchildren_path),
        'classification_stream_sha256': summary['classification_stream_sha256'],
        'independent_verification_sha256': sha256_file(independent_path),
        'primary_source_bundle_sha256': source_bundle_sha256(args.package_root, ['classification_core.py', 'classification_child.py', 'classify.py']),
        'independent_source_bundle_sha256': source_bundle_sha256(args.package_root, ['verification_core.js', 'verification_child.js', 'verify_independent.js']),
        'package_verifier_source_sha256': sha256_file(args.package_root / 'verify_package.py'),
    }
    for key, value in checks.items():
        if expected[key] != value:
            raise SystemExit(f'{key} mismatch: {value} != {expected[key]}')

    scalar_checks = {
        'child_count': summary['child_count'],
        'grandchild_count': summary['grandchild_count'],
        'candidate_count_total': summary['candidate_count_total'],
        'pointwise_orbit_count_negative_control_total': summary['pointwise_orbit_count_negative_control_total'],
        'pilot_case_count': len(summary['pilot_cases']),
    }
    for key, value in scalar_checks.items():
        if expected[key] != value:
            raise SystemExit(f'{key} mismatch: {value} != {expected[key]}')
    if independent.get('status') != 'PASS':
        raise SystemExit('independent verifier did not report PASS')
    if independent.get('classification_stream_sha256') != summary['classification_stream_sha256']:
        raise SystemExit('independent classification digest mismatch')
    if independent.get('grandchild_count') != summary['grandchild_count']:
        raise SystemExit('independent grandchild count mismatch')

    verification = {
        'schema': 'borsuk-q00r00-seventh-base-classification-verification-v1',
        'claim_id': 'n11-k6-q00r00-seventh-base-classification',
        'status': 'PASS',
        'primary_implementation': {
            'language': 'Python',
            'source_bundle_sha256': checks['primary_source_bundle_sha256'],
            'files': ['classification_core.py', 'classification_child.py', 'classify.py'],
        },
        'independent_implementation': {
            'language': 'JavaScript',
            'source_bundle_sha256': checks['independent_source_bundle_sha256'],
            'files': ['verification_core.js', 'verification_child.js', 'verify_independent.js'],
            'result_sha256': checks['independent_verification_sha256'],
        },
        'package_verifier': {
            'language': 'Python',
            'source_sha256': checks['package_verifier_source_sha256'],
        },
        'classification': {
            'child_count': summary['child_count'],
            'candidate_count_total': summary['candidate_count_total'],
            'grandchild_count': summary['grandchild_count'],
            'classification_stream_sha256': summary['classification_stream_sha256'],
            'summary_sha256': checks['summary_sha256'],
            'grandchildren_csv_sha256': checks['grandchildren_csv_sha256'],
            'pointwise_orbit_count_negative_control_total': summary['pointwise_orbit_count_negative_control_total'],
        },
        'complexity_inventory': {
            'tier_counts': summary['complexity_tier_counts'],
            'pilot_cases': summary['pilot_cases'],
            'interpretation': 'relative scheduling proxy only; not a solver result',
        },
        'source_boundary': summary['source'],
        'mathematical_status': summary['status_boundary'],
        'refinement_boundary': {
            'all_36_inputs_are_incomplete_screen_cases': True,
            'certified_obstruction_frontier_count': 0,
            'cross_child_merging_performed': False,
            'recanonicalization_across_children_performed': False,
        },
    }
    verification_path = args.output / 'verification.json'
    verification_path.write_text(json.dumps(verification, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    if 'verification_sha256' in expected and sha256_file(verification_path) != expected['verification_sha256']:
        raise SystemExit('verification_sha256 mismatch')

    files = sorted(path for path in args.output.rglob('*') if path.is_file() and path.name != 'SHA256SUMS')
    sums_path = args.output / 'SHA256SUMS'
    sums_path.write_text(
        ''.join(f'{sha256_file(path)}  {path.relative_to(args.output).as_posix()}\n' for path in files),
        encoding='ascii',
    )
    if 'sha256sums_sha256' in expected and sha256_file(sums_path) != expected['sha256sums_sha256']:
        raise SystemExit('sha256sums_sha256 mismatch')
    print(json.dumps(verification, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
