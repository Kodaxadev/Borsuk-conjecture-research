#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from generate_cases import EXPECTED_CASE_CSV_SHA256, generate_cases

ALLOWED_STATES = {"UNKNOWN", "SAT_CLOSED", "UNSAT_REFINED", "LEGAL_UNSAT"}
ROOT = Path(__file__).resolve().parent


def main() -> int:
    rows, _ = generate_cases()
    case_ids = {str(row["id"]) for row in rows}
    document = json.loads((ROOT / "case_status.json").read_text(encoding="utf-8"))

    if document.get("schema_version") != 1:
        raise SystemExit("unsupported q00 refinement status schema")
    if document.get("case_list_sha256") != EXPECTED_CASE_CSV_SHA256:
        raise SystemExit("q00 refinement status is pinned to the wrong case-list hash")
    if document.get("default_state") != "UNKNOWN":
        raise SystemExit("q00 refinement default state must remain UNKNOWN")

    overrides = document.get("overrides")
    if not isinstance(overrides, dict):
        raise SystemExit("q00 refinement overrides must be an object")
    unknown_ids = sorted(set(overrides) - case_ids)
    if unknown_ids:
        raise SystemExit(f"unknown q00 refinement case IDs: {unknown_ids}")
    invalid_states = {case_id: state for case_id, state in overrides.items() if state not in ALLOWED_STATES}
    if invalid_states:
        raise SystemExit(f"invalid q00 refinement states: {invalid_states}")

    counts = {state: 0 for state in sorted(ALLOWED_STATES)}
    for case_id in sorted(case_ids):
        counts[overrides.get(case_id, "UNKNOWN")] += 1
    if sum(counts.values()) != 12:
        raise SystemExit("q00 refinement status does not cover all 12 cases")

    print(json.dumps({"status": "PASS", "counts": counts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
