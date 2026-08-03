#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_instance import (
    COLORS,
    allowed_colors_for,
    build_graph,
    fixed_clique_for,
    get_case,
    variable_map_for,
)
from generate_cases import EXPECTED_CASE_CSV_SHA256


def parse_positive_literals(path: Path) -> set[int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if "UNSAT" in text.upper():
        raise ValueError("UNSAT text is not a SAT witness")
    positives: set[int] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("c", "p", "s")):
            continue
        if line.startswith("v"):
            line = line[1:].strip()
        tokens = line.split()
        try:
            literals = [int(token) for token in tokens]
        except ValueError:
            continue
        positives.update(literal for literal in literals if literal > 0)
    if not positives:
        raise ValueError("model contains no positive literals")
    return positives


def decode_coloring(
    vertices: list[int], fixed_clique: list[int], positives: set[int]
) -> dict[int, int]:
    domains = allowed_colors_for(vertices, fixed_clique)
    mapping, variable_to_pair = variable_map_for(vertices, domains)
    out_of_range = sorted(literal for literal in positives if literal not in variable_to_pair)
    if out_of_range:
        raise ValueError(f"model contains out-of-range variables: {out_of_range[:10]}")

    coloring: dict[int, int] = {}
    for vertex in vertices:
        selected = [
            color
            for color in domains[vertex]
            if mapping[(vertex, color)] in positives
        ]
        if len(selected) != 1:
            raise ValueError(f"vertex {vertex} has {len(selected)} selected colors: {selected}")
        coloring[vertex] = selected[0]
    return coloring


def verify_coloring(edges: list[tuple[int, int]], coloring: dict[int, int]) -> None:
    bad = [
        (left, right, coloring[left])
        for left, right in edges
        if coloring[left] == coloring[right]
    ]
    if bad:
        raise ValueError(f"monochromatic exact-distance-6 edges: {bad[:10]}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("model", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    case = get_case(args.case_id)
    vertices, edges = build_graph(case)
    fixed_clique = fixed_clique_for(vertices)
    try:
        positives = parse_positive_literals(args.model)
        coloring = decode_coloring(vertices, fixed_clique, positives)
        verify_coloring(edges, coloring)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    output = {
        "schema": "borsuk-q00-five-base-verified-coloring-v1",
        "case_id": args.case_id,
        "canonical_case_list_sha256": EXPECTED_CASE_CSV_SHA256,
        "model_sha256": hashlib.sha256(args.model.read_bytes()).hexdigest(),
        "vertices": len(vertices),
        "edges": len(edges),
        "colors_used": len(set(coloring.values())),
        "coloring": {str(vertex): coloring[vertex] for vertex in vertices},
    }
    if args.output:
        args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"PASS: verified {COLORS}-coloring for {args.case_id} "
        f"on {len(vertices)} vertices and {len(edges)} edges"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
