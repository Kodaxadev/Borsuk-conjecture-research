#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from generate_fifth_base_cases import EXPECTED_CSV_SHA256, EXPECTED_ORBITS, generate_rows

ROOT = Path(__file__).resolve().parent
ALLOWED = {"UNKNOWN", "SAT_CLOSED", "UNSAT_REFINED", "LEGAL_UNSAT"}


def main() -> int:
    status = json.loads((ROOT / "child_status.json").read_text(encoding="utf-8"))
    if status.get("case_list_sha256") != EXPECTED_CSV_SHA256:
        raise SystemExit("child status case-list hash mismatch")
    rows, _ = generate_rows()
    case_ids = {str(row["id"]) for row in rows}
    if len(case_ids) != EXPECTED_ORBITS:
        raise SystemExit("child case count mismatch")
    default = status.get("default_state")
    if default not in ALLOWED:
        raise SystemExit("invalid default child state")
    overrides = status.get("overrides")
    if not isinstance(overrides, dict):
        raise SystemExit("overrides must be an object")
    for case_id, record in overrides.items():
        if case_id not in case_ids:
            raise SystemExit(f"unknown child override: {case_id}")
        if not isinstance(record, dict) or record.get("state") not in ALLOWED - {"UNKNOWN"}:
            raise SystemExit(f"invalid child override: {case_id}")
        raise SystemExit("no non-UNKNOWN child override schema is registered yet")
    print(f"PASS q00 fifth-base status: UNKNOWN={len(case_ids)} resolved=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
