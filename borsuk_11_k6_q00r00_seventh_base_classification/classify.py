#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

from classification_child import classify_child
from classification_core import (
    CLAIM_ID, SOURCE_ARCHIVE_SHA256, SOURCE_GOVERNANCE_COMMIT,
    SOURCE_MANIFEST_SHA256, SOURCE_STATUS_SYNC_COMMIT, canonical_json_bytes,
    pretty_json_bytes, sha256_file,
)

def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trim-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest_path = args.trim_root / "manifest.json"
    if sha256_file(manifest_path) != SOURCE_MANIFEST_SHA256:
        raise SystemExit("source child-trim manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    children = manifest.get("children")
    if not isinstance(children, list) or len(children) != 36:
        raise SystemExit("source manifest must contain exactly 36 children")
    expected_ids = [f"q00r00-s{index:03d}" for index in range(36)]
    if [child.get("child_id") for child in children] != expected_ids:
        raise SystemExit("source child order or coverage changed")

    shutil.rmtree(args.output, ignore_errors=True)
    child_output = args.output / "children"
    child_output.mkdir(parents=True)

    classifications: list[dict[str, object]] = []
    stream_digest = hashlib.sha256()
    grandchild_rows: list[dict[str, object]] = []
    for child in children:
        classification = classify_child(child, args.trim_root)
        classifications.append(classification)
        child_id = str(classification["child_id"])
        child_path = child_output / f"{child_id}.json"
        child_path.write_bytes(pretty_json_bytes(classification))
        stream_digest.update(canonical_json_bytes(classification))
        for orbit in classification["orbits"]:
            graph = orbit["graph"]
            proxy = orbit["raw_12color_cnf_proxy"]
            grandchild_rows.append(
                {
                    "grandchild_id": orbit["grandchild_id"],
                    "parent_child_id": child_id,
                    "representative": orbit["representative"],
                    "representative_hex": orbit["representative_hex"],
                    "orbit_size": orbit["orbit_size"],
                    "vertices": graph["vertices"],
                    "distance6_edges": graph["distance6_edges"],
                    "incompatible_pairs": graph["incompatible_pairs"],
                    "raw_variables": proxy["variables"],
                    "raw_clauses": proxy["clauses"],
                    "complexity_tier": proxy["tier"],
                    "status": "UNKNOWN",
                }
            )

    write_csv(
        args.output / "grandchildren.csv",
        grandchild_rows,
        [
            "grandchild_id",
            "parent_child_id",
            "representative",
            "representative_hex",
            "orbit_size",
            "vertices",
            "distance6_edges",
            "incompatible_pairs",
            "raw_variables",
            "raw_clauses",
            "complexity_tier",
            "status",
        ],
    )
    tier_counts = Counter(str(row["complexity_tier"]) for row in grandchild_rows)
    stabilizer_histogram = Counter(
        str(classification["setwise_stabilizer_order"]) for classification in classifications
    )
    pilot_cases = [
        str(row["grandchild_id"])
        for row in grandchild_rows
        if row["complexity_tier"] == "PILOT"
    ]
    summary = {
        "schema": "borsuk-q00r00-seventh-base-classification-summary-v1",
        "claim_id": CLAIM_ID,
        "status": "PASS",
        "source": {
            "child_trim_archive_sha256": SOURCE_ARCHIVE_SHA256,
            "child_trim_manifest_sha256": SOURCE_MANIFEST_SHA256,
            "sixth_base_screen_governance_commit": SOURCE_GOVERNANCE_COMMIT,
            "sixth_base_screen_status_sync_commit": SOURCE_STATUS_SYNC_COMMIT,
            "refinement_reason": "incomplete_screen_not_certified_obstruction",
        },
        "child_count": 36,
        "grandchild_count": len(grandchild_rows),
        "candidate_count_total": sum(int(item["candidate_count"]) for item in classifications),
        "setwise_orbit_count_total": sum(int(item["setwise_orbit_count"]) for item in classifications),
        "pointwise_orbit_count_negative_control_total": sum(
            int(item["pointwise_orbit_count_negative_control"]) for item in classifications
        ),
        "per_child_orbit_count_range": [
            min(int(item["setwise_orbit_count"]) for item in classifications),
            max(int(item["setwise_orbit_count"]) for item in classifications),
        ],
        "setwise_stabilizer_order_range": [
            min(int(item["setwise_stabilizer_order"]) for item in classifications),
            max(int(item["setwise_stabilizer_order"]) for item in classifications),
        ],
        "setwise_stabilizer_order_histogram": dict(sorted(stabilizer_histogram.items(), key=lambda item: int(item[0]))),
        "grandchild_trim_vertex_range": [
            min(int(row["vertices"]) for row in grandchild_rows),
            max(int(row["vertices"]) for row in grandchild_rows),
        ],
        "grandchild_distance6_edge_range": [
            min(int(row["distance6_edges"]) for row in grandchild_rows),
            max(int(row["distance6_edges"]) for row in grandchild_rows),
        ],
        "grandchild_incompatible_pair_range": [
            min(int(row["incompatible_pairs"]) for row in grandchild_rows),
            max(int(row["incompatible_pairs"]) for row in grandchild_rows),
        ],
        "raw_12color_cnf_proxy_clause_range": [
            min(int(row["raw_clauses"]) for row in grandchild_rows),
            max(int(row["raw_clauses"]) for row in grandchild_rows),
        ],
        "complexity_tier_counts": {
            tier: tier_counts.get(tier, 0) for tier in ("PILOT", "SMALL", "MEDIUM", "LARGE")
        },
        "pilot_cases": pilot_cases,
        "classification_stream_sha256": stream_digest.hexdigest(),
        "status_boundary": {
            "all_grandchildren": "UNKNOWN",
            "q00r00_s000_through_s035": "UNKNOWN",
            "q00r00": "UNKNOWN",
            "q00": "UNKNOWN",
            "n11-k6-full": "Gate 2 / OPEN",
        },
        "non_implications": [
            "No child is a certified obstruction.",
            "No SAT or UNSAT claim is made for any grandchild.",
            "Complexity tiers are scheduling proxies only.",
            "No cross-child merging or recanonicalization was performed.",
        ],
    }
    (args.output / "summary.json").write_bytes(pretty_json_bytes(summary))

    files = sorted(path for path in args.output.rglob("*") if path.is_file() and path.name != "SHA256SUMS")
    (args.output / "SHA256SUMS").write_text(
        "".join(
            f"{sha256_file(path)}  {path.relative_to(args.output).as_posix()}\n"
            for path in files
        ),
        encoding="ascii",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
