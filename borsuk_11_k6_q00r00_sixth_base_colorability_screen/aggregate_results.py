#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    records: list[dict[str, object]] = []
    expected_ids = [f"q00r00-s{index:03d}" for index in range(36)]
    for case_id in expected_ids:
        matches = list(args.results.rglob(f"{case_id}/certificate-result.json")) + list(args.results.rglob(f"{case_id}-result/certificate-result.json"))
        if not matches:
            matches = [path for path in args.results.rglob("certificate-result.json") if json.loads(path.read_text()).get("case_id") == case_id]
        if len(matches) != 1:
            raise SystemExit(f"expected one result for {case_id}, found {len(matches)}")
        record = json.loads(matches[0].read_text(encoding="utf-8"))
        if record.get("case_id") != case_id:
            raise SystemExit(f"case mismatch for {case_id}")
        records.append(record)

    counts = Counter(str(record["certificate_state"]) for record in records)
    sat_cases = [str(record["case_id"]) for record in records if record["certificate_state"] == "SAT_CHECKED_COLORING"]
    unsat_cases = [str(record["case_id"]) for record in records if record["certificate_state"] == "PROOF_CHECKED_UNSAT"]
    unknown_cases = [str(record["case_id"]) for record in records if record["certificate_state"] == "UNKNOWN"]
    non_sat_cases = [case_id for case_id in expected_ids if case_id not in sat_cases]
    summary = {
        "schema": "borsuk-q00r00-sixth-base-colorability-screen-summary-v1",
        "claim_id": "n11-k6-q00r00-sixth-base-colorability-screen",
        "case_count": 36,
        "certificate_state_counts": dict(sorted(counts.items())),
        "checked_sat_cases": sat_cases,
        "checked_unsat_universal_trim_cases": unsat_cases,
        "incomplete_cases": unknown_cases,
        "seventh_base_refinement_frontier": non_sat_cases,
        "proof_checked_unsat_frontier": unsat_cases,
        "closed_child_branches": sat_cases,
        "q00r00_certificate_effect": "ELIGIBLE_FOR_GOVERNED_CLOSURE" if len(sat_cases) == 36 else "REMAINS_UNKNOWN",
        "repository_q00r00_status_changed": False,
        "q00_status": "UNKNOWN",
        "n11-k6-full": "Gate 2 / OPEN",
        "interpretation": {
            "SAT_CHECKED_COLORING": "closes that child branch",
            "PROOF_CHECKED_UNSAT": "does not close that child; sends it to compatible seventh-base refinement",
            "UNKNOWN": "screen must be retried or otherwise resolved before refinement classification",
        },
        "results": records,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    summary_path = args.output / "screen-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "screen-summary.sha256").write_text(f"{sha256_file(summary_path)}  screen-summary.json\n", encoding="ascii")
    print(json.dumps({key: summary[key] for key in ("certificate_state_counts", "closed_child_branches", "seventh_base_refinement_frontier", "proof_checked_unsat_frontier", "incomplete_cases", "q00r00_certificate_effect")}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
