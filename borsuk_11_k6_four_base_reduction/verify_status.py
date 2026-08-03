#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from build_instance import COLORS, build_graph
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


def require_nonempty_string(
    record: dict[str, Any], field: str, case_id: str, errors: list[str]
) -> str | None:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        fail(errors, f"{case_id}: {field} must be a non-empty string")
        return None
    return value


def artifact_path(relative: str, case_id: str, field: str, errors: list[str]) -> Path | None:
    path = Path(relative)
    if path.is_absolute():
        fail(errors, f"{case_id}: {field} must be package-relative")
        return None
    resolved = (PACKAGE / path).resolve()
    try:
        resolved.relative_to(PACKAGE.resolve())
    except ValueError:
        fail(errors, f"{case_id}: {field} escapes the package directory")
        return None
    if not resolved.is_file():
        fail(errors, f"{case_id}: missing artifact {relative}")
        return None
    return resolved


def verify_hash(path: Path, expected: str, case_id: str, label: str, errors: list[str]) -> None:
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        fail(errors, f"{case_id}: {label} SHA-256 mismatch; expected {expected}, got {actual}")


def verify_sat_coloring(
    case_id: str,
    case: dict[str, object],
    record: dict[str, Any],
    errors: list[str],
) -> None:
    relative = require_nonempty_string(record, "coloring_artifact", case_id, errors)
    result_sha = require_nonempty_string(record, "result_sha256", case_id, errors)
    if relative is None or result_sha is None:
        return
    path = artifact_path(relative, case_id, "coloring_artifact", errors)
    if path is None:
        return
    verify_hash(path, result_sha, case_id, "coloring artifact", errors)

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(errors, f"{case_id}: invalid coloring JSON: {exc}")
        return
    if payload.get("schema") != "borsuk-verified-coloring-v1":
        fail(errors, f"{case_id}: unexpected coloring schema")
    if payload.get("case_id") != case_id:
        fail(errors, f"{case_id}: coloring artifact names another case")
    if payload.get("canonical_case_list_sha256") != EXPECTED_CANONICAL_CSV_SHA256:
        fail(errors, f"{case_id}: coloring artifact targets another canonical case list")

    vertices, edges = build_graph(case)
    raw_coloring = payload.get("coloring")
    if not isinstance(raw_coloring, dict):
        fail(errors, f"{case_id}: coloring must be an object")
        return
    expected_keys = {str(vertex) for vertex in vertices}
    if set(raw_coloring) != expected_keys:
        fail(errors, f"{case_id}: coloring vertex set does not match the regenerated trim")
        return
    colors: dict[int, int] = {}
    for vertex in vertices:
        color = raw_coloring[str(vertex)]
        if not isinstance(color, int) or not 0 <= color < COLORS:
            fail(errors, f"{case_id}: invalid color {color!r} for vertex {vertex}")
            return
        colors[vertex] = color
    for left, right in edges:
        if colors[left] == colors[right]:
            fail(errors, f"{case_id}: coloring has monochromatic edge {left}--{right}")
            return
    if payload.get("vertices") != len(vertices) or payload.get("edges") != len(edges):
        fail(errors, f"{case_id}: coloring graph statistics do not match regeneration")


def main() -> int:
    data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []

    raw_cases, _ = generate_raw_cases()
    cases = canonical_classes(raw_cases)
    case_by_id = {str(case["id"]): case for case in cases}
    case_ids = set(case_by_id)
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

        require_nonempty_string(record, "verification_command", case_id, errors)
        checker_relative = require_nonempty_string(
            record, "checker_output_artifact", case_id, errors
        )
        checker_sha = require_nonempty_string(record, "checker_output_sha256", case_id, errors)
        if checker_relative is not None and checker_sha is not None:
            checker_path = artifact_path(
                checker_relative, case_id, "checker_output_artifact", errors
            )
            if checker_path is not None:
                verify_hash(checker_path, checker_sha, case_id, "checker output", errors)
                if not checker_path.read_text(
                    encoding="utf-8", errors="replace"
                ).strip():
                    fail(errors, f"{case_id}: checker output is empty")

        if state == "SAT_CLOSED":
            verify_sat_coloring(case_id, case_by_id[case_id], record, errors)
        elif state == "UNSAT_REFINED":
            proof_relative = require_nonempty_string(record, "proof_artifact", case_id, errors)
            proof_sha = require_nonempty_string(record, "result_sha256", case_id, errors)
            if proof_relative is not None and proof_sha is not None:
                proof_path = artifact_path(proof_relative, case_id, "proof_artifact", errors)
                if proof_path is not None:
                    verify_hash(proof_path, proof_sha, case_id, "proof artifact", errors)
            children = record.get("children")
            if not isinstance(children, list) or not children or not all(
                isinstance(child, str) and child.strip() for child in children
            ):
                fail(errors, f"{case_id}: UNSAT_REFINED requires non-empty child identifiers")
            if record.get("proof_check_tier") not in {"ci", "manual-heavy"}:
                fail(
                    errors,
                    f"{case_id}: UNSAT_REFINED requires proof_check_tier ci or manual-heavy",
                )
        elif state == "LEGAL_UNSAT":
            proof_relative = require_nonempty_string(record, "proof_artifact", case_id, errors)
            proof_sha = require_nonempty_string(record, "result_sha256", case_id, errors)
            if proof_relative is not None and proof_sha is not None:
                proof_path = artifact_path(proof_relative, case_id, "proof_artifact", errors)
                if proof_path is not None:
                    verify_hash(proof_path, proof_sha, case_id, "proof artifact", errors)
            if record.get("incompatibility_pairs") != 0:
                fail(errors, f"{case_id}: LEGAL_UNSAT must record incompatibility_pairs = 0")
            if record.get("proof_check_tier") not in {"ci", "manual-heavy"}:
                fail(
                    errors,
                    f"{case_id}: LEGAL_UNSAT requires proof_check_tier ci or manual-heavy",
                )

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
