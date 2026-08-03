#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from generate_cases import (
    EXPECTED_CANONICAL_CSV_SHA256,
    canonical_classes,
    generate_raw_cases,
    render_csv,
)

PACKAGE = Path(__file__).resolve().parent
STATUS_PATH = PACKAGE / "case_status.json"
ALLOWED_STATES = {"UNKNOWN", "SAT_CLOSED", "UNSAT_REFINED", "LEGAL_UNSAT"}
CANONICAL_FIELDS = [
    "id",
    "representative_case",
    "members",
    "member_count",
    "B",
    "C",
    "vertices",
    "exact_distance_edges",
    "incompatible_pairs",
    "vertex_sha256",
    "base_signature",
]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def require_nonempty_string(record: dict[str, Any], field: str, case_id: str, errors: list[str]) -> None:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        fail(errors, f"{case_id}: {field} must be a non-empty string")


def main() -> int:
    data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []

    raw_cases, _ = generate_raw_cases()
    cases = canonical_classes(raw_cases)
    case_ids = {str(case["id"]) for case in cases}
    case_csv = render_csv(cases, CANONICAL_FIELDS)
    actual_hash = hashlib.sha256(case_csv.encode("ascii")).hexdigest()

    if data.get("schema_version") != 1:
        fail(errors, "schema_version must equal 1")
    if actual_hash != EXPECTED_CANONICAL_CSV_SHA256:
        fail(errors, f"generator case-list hash changed: {actual_hash}")
    if data.get("case_list_sha256") != actual_hash:
        fail(errors, "case_status.json does not target the generated case list")
    if data.get("default_state") != "UNKNOWN":
        fail(errors, "default_state must remain UNKNOWN")

    overrides = data.get("overrides")
    if not isinstance(overrides, dict):
        fail(errors, "overrides must be an object")
        overrides = {}

    for case_id, record in overrides.items():
        if case_id not in case_ids:
            fail(errors, f"unknown case id in overrides: {case_id}")
            continue
        if not isinstance(record, dict):
            fail(errors, f"{case_id}: override must be an object")
            continue
        state = record.get("state")
        if state not in ALLOWED_STATES - {"UNKNOWN"}:
            fail(errors, f"{case_id}: override state must be a certified non-UNKNOWN state")
            continue

        require_nonempty_string(record, "result_sha256", case_id, errors)
        require_nonempty_string(record, "verification_command", case_id, errors)
        require_nonempty_string(record, "checker_output_sha256", case_id, errors)

        if state == "SAT_CLOSED":
            require_nonempty_string(record, "coloring_artifact", case_id, errors)
        elif state == "UNSAT_REFINED":
            require_nonempty_string(record, "proof_artifact", case_id, errors)
            children = record.get("children")
            if not isinstance(children, list) or not children or not all(
                isinstance(child, str) and child.strip() for child in children
            ):
                fail(errors, f"{case_id}: UNSAT_REFINED requires non-empty child identifiers")
        elif state == "LEGAL_UNSAT":
            require_nonempty_string(record, "proof_artifact", case_id, errors)
            if record.get("incompatibility_pairs") != 0:
                fail(errors, f"{case_id}: LEGAL_UNSAT must record incompatibility_pairs = 0")

    states = Counter("UNKNOWN" for _ in case_ids)
    for record in overrides.values():
        if isinstance(record, dict) and record.get("state") in ALLOWED_STATES - {"UNKNOWN"}:
            states["UNKNOWN"] -= 1
            states[str(record["state"])] += 1

    if errors:
        print("Four-base status verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Case status OK: {len(case_ids)} canonical trim types")
    for state in sorted(ALLOWED_STATES):
        print(f"- {state}: {states[state]}")
    if states["UNKNOWN"] > 0:
        print("The n=11, k=6 theorem target remains open.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
