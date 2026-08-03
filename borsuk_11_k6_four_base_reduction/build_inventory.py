#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from io import StringIO
from pathlib import Path

from build_instance import (
    allowed_colors_for,
    build_graph,
    fixed_clique_for,
    formula_counts,
)
from generate_cases import canonical_classes, generate_raw_cases

EXPECTED_INVENTORY_SHA256 = "3212beac7ab2b301a7ca97801c91610344f27a29c03233041bd7392209c91ccf"
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
        vertices, edges = build_graph(case)
        fixed_clique = fixed_clique_for(vertices)
        domains = allowed_colors_for(vertices, fixed_clique)
        vertex_count = int(case["vertices"])
        edge_count = int(case["exact_distance_edges"])
        incompatible = int(case["incompatible_pairs"])
        variables, clauses = formula_counts(vertices, edges, domains)
        pair_count = vertex_count * (vertex_count - 1) // 2
        rows.append({
            "rank": 0,
            "id": str(case["id"]),
            "representative_case": str(case["representative_case"]),
            "member_count": int(case["member_count"]),
            "vertices": vertex_count,
            "exact_distance_edges": edge_count,
            "incompatible_pairs": incompatible,
            "fixed_clique_size": len(fixed_clique),
            "variables": variables,
            "clauses": clauses,
            "edge_density_ppm": round(edge_count * 1_000_000 / pair_count),
            "incompatibility_density_ppm": round(incompatible * 1_000_000 / pair_count),
        })
    rows.sort(key=lambda row: (
        int(row["clauses"]),
        int(row["variables"]),
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
