#!/usr/bin/env python3
"""Verify a SAT model for one triangle-refinement orbit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from enumerate_triangle_refinement import (
    COLORS,
    EXPECTED,
    K,
    branch_edges,
    branch_vertices,
    color_domains,
    fixed_clique,
    representative,
    triangle_trim,
    tuple_id,
)


def parse_counts(value: str) -> tuple[int, int, int, int]:
    for counts in EXPECTED:
        if tuple_id(counts) == value:
            return counts
    raise argparse.ArgumentTypeError(f"unknown orbit id: {value}")


def parse_model(path: Path) -> set[int]:
    literals: list[int] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("c") or line.startswith("s"):
            continue
        if line.startswith("v"):
            line = line[1:].strip()
        for token in line.split():
            try:
                value = int(token)
            except ValueError:
                continue
            if value:
                literals.append(value)
    if not literals:
        raise SystemExit("no DIMACS model literals found")
    return {literal for literal in literals if literal > 0}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("orbit", type=parse_counts)
    parser.add_argument("model", type=Path)
    parser.add_argument("--witness", type=Path)
    args = parser.parse_args()

    counts = args.orbit
    orbit = tuple_id(counts)
    c = representative(counts)
    trim = triangle_trim()
    vertices = branch_vertices(trim, c)
    edges = branch_edges(vertices)
    expected = EXPECTED[counts]
    assert len(vertices) == expected["vertices"]
    assert len(edges) == expected["edges"]

    fixed = fixed_clique(vertices)
    domains = color_domains(vertices, fixed)
    reverse: list[tuple[int, int]] = []
    for vertex in vertices:
        for color in domains[vertex]:
            reverse.append((vertex, color))

    positive = parse_model(args.model)
    coloring: dict[int, int] = {}
    for variable_id, (vertex, color) in enumerate(reverse, start=1):
        if variable_id not in positive:
            continue
        if vertex in coloring:
            raise SystemExit(f"vertex {vertex} has multiple true colors")
        coloring[vertex] = color

    missing = sorted(set(vertices) - set(coloring))
    if missing:
        raise SystemExit(f"{len(missing)} vertices have no true color")
    for vertex, color in coloring.items():
        if color not in domains[vertex]:
            raise SystemExit(f"vertex {vertex} uses forbidden color {color}")
    bad = [(u, v, coloring[u]) for u, v in edges if coloring[u] == coloring[v]]
    if bad:
        raise SystemExit(f"monochromatic distance-6 edges: {bad[:5]}")
    if len(set(coloring.values())) > COLORS:
        raise SystemExit("model uses more than 12 colors")

    witness_path = args.witness or Path(f"witness_{orbit}.json")
    witness = {
        "n": 11,
        "diameter": K,
        "triangle": [0, 63, 455],
        "orbit": orbit,
        "counts": list(counts),
        "representative_C": c,
        "vertices": len(vertices),
        "distance_6_edges": len(edges),
        "coloring": {str(v): coloring[v] for v in sorted(coloring)},
        "status": "verified proper 12-coloring",
    }
    witness_path.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"PASS {orbit}: verified {len(vertices)} vertices and "
        f"{len(edges)} distance-6 edges; wrote {witness_path}"
    )


if __name__ == "__main__":
    main()
