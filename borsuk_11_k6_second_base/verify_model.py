#!/usr/bin/env python3
"""Verify a SAT model for one generated second-base coloring instance."""
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

from enumerate_second_base import (
    A,
    COLORS,
    EXPECTED,
    K,
    REPRESENTATIVES,
    branch_edges,
    branch_vertices,
    color_domains,
    fixed_clique,
    trim_vertices,
)


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
            if value != 0:
                literals.append(value)
    if not literals:
        raise SystemExit("no DIMACS model literals found")
    return {value for value in literals if value > 0}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("overlap", type=int, choices=(3, 4, 5))
    parser.add_argument("model", type=Path)
    parser.add_argument("--witness", type=Path)
    args = parser.parse_args()

    positive = parse_model(args.model)
    trim = trim_vertices()
    b = REPRESENTATIVES[args.overlap]
    vertices = branch_vertices(trim, b)
    edges = branch_edges(vertices)
    expected_vertices, expected_edges, _ = EXPECTED[args.overlap]
    assert len(vertices) == expected_vertices
    assert len(edges) == expected_edges

    fixed = fixed_clique(vertices)
    domains = color_domains(vertices, fixed)
    reverse: list[tuple[int, int]] = []
    for vertex in vertices:
        for color in domains[vertex]:
            reverse.append((vertex, color))

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

    bad_domain = [
        (vertex, color)
        for vertex, color in coloring.items()
        if color not in domains[vertex]
    ]
    if bad_domain:
        raise SystemExit(f"model uses forbidden colors: {bad_domain[:5]}")

    bad_edges = [
        (u, v, coloring[u])
        for u, v in edges
        if coloring[u] == coloring[v]
    ]
    if bad_edges:
        raise SystemExit(f"monochromatic distance-6 edges: {bad_edges[:5]}")

    if len(set(coloring.values())) > COLORS:
        raise SystemExit("model uses too many colors")

    witness_path = args.witness or Path(
        f"witness_overlap_{args.overlap}.json"
    )
    witness = {
        "n": 11,
        "diameter": K,
        "base_A": A,
        "overlap": args.overlap,
        "representative_B": b,
        "vertices": len(vertices),
        "distance_6_edges": len(edges),
        "coloring": {str(v): coloring[v] for v in sorted(coloring)},
        "status": "verified proper 12-coloring",
    }
    witness_path.write_text(
        json.dumps(witness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"PASS overlap={args.overlap}: verified {len(vertices)} vertices, "
        f"{len(edges)} distance-6 edges; wrote {witness_path}"
    )


if __name__ == "__main__":
    main()
