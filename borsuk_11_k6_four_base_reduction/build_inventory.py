#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from io import StringIO
from pathlib import Path

from build_instance import fixed_clique_for, formula_counts
from generate_cases import A, allowed, canonical_classes, generate_raw_cases

EXPECTED_INVENTORY_SHA256 = "b2b4689bd1f344382c67a02a1a60b051a2ec532d0e018d05d1dee1412afff196"
FIELDS = [
    "rank",
    "id",
    "representative_case",
    "member_count",
    "vertices",
    "exact_distance_edges",
    "incompatible_pairs",
    "fixed_clique_size",
    "variables",
    "clauses",
    "edge_density_ppm",
    "incompatibility_density_ppm",
]


def build_rows() -> list[dict[str, int | str]]:
    raw, _ = generate_raw_cases()
    rows: list[dict[str, int | str]] = []
    for case in canonical_classes(raw):
        base = (0, A, int(case["B"]), int(case["C"]))
        vertices = [mask for mask in range(1 << 11) if allowed(mask, base)]
        fixed_count = len(fixed_clique_for(vertices))
        vertex_count = int(case["vertices"])
        edge_count = int(case["exact_distance_edges"])
        incompatible = int(case["incompatible_pairs"])
        variables, clauses = formula_counts(vertex_count, edge_count, fixed_count)
        pair_count = vertex_count * (vertex_count - 1) // 2
        rows.append({
            "rank": 0,
            "id": str(case["id"]),
            "representative_case": str(case["representative_case"]),
            "member_count": int(case["member_count"]),
            "vertices": vertex_count,
            "exact_distance_edges": edge_count,
            "incompatible_pairs": incompatible,
            "fixed_clique_size": fixed_count,
            "variables": variables,
            "clauses": clauses,
            "edge_density_ppm": round(edge_count * 1_000_000 / pair_count),
            "incompatibility_density_ppm": round(incompatible * 1_000_000 / pair_count),
        })
    rows.sort(key=lambda row: (
        int(row["clauses"]),
        int(row["vertices"]),
        int(row["incompatible_pairs"]),
        str(row["id"]),
    ))
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


def render(rows: list[dict[str, int | str]]) -> str:
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    text = render(build_rows())
    digest = hashlib.sha256(text.encode("ascii")).hexdigest()
    if digest != EXPECTED_INVENTORY_SHA256:
        raise SystemExit(f"inventory hash mismatch: {digest}")
    if args.output:
        args.output.write_text(text, encoding="ascii", newline="")
    print(f"PASS canonical_types=58 inventory_sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
