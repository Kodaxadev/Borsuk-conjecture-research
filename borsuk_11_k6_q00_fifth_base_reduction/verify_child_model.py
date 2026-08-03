#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from build_child_instance import COLORS, build_graph, fixed_clique_for, get_case
from generate_fifth_base_cases import EXPECTED_CSV_SHA256, K, distance


def parse_positive_literals(path: Path) -> set[int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if "UNSAT" in text.upper():
        raise ValueError("UNSAT text is not a coloring certificate; provide a checked proof trace")
    positives: set[int] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("c", "p", "s")):
            continue
        if line.startswith("v"):
            line = line[1:].strip()
        tokens = line.split()
        if not tokens:
            continue
        try:
            literals = [int(token) for token in tokens]
        except ValueError:
            continue
        positives.update(literal for literal in literals if literal > 0)
    if not positives:
        raise ValueError("model contains no positive literals")
    return positives


def independent_domains(vertices: list[int], clique: list[int]) -> dict[int, tuple[int, ...]]:
    assigned = {vertex: color for color, vertex in enumerate(clique)}
    domains: dict[int, tuple[int, ...]] = {}
    for vertex in vertices:
        if vertex in assigned:
            domain = (assigned[vertex],)
        else:
            domain = tuple(
                color
                for color in range(COLORS)
                if color >= len(clique) or distance(vertex, clique[color]) != K
            )
        if not domain:
            raise ValueError(f"vertex {vertex} has an empty reconstructed domain")
        domains[vertex] = domain
    return domains


def independent_variable_map(vertices: list[int], domains: dict[int, tuple[int, ...]]) -> dict[tuple[int, int], int]:
    mapping: dict[tuple[int, int], int] = {}
    variable = 1
    for vertex in vertices:
        for color in domains[vertex]:
            mapping[(vertex, color)] = variable
            variable += 1
    return mapping


def decode_coloring(vertices: list[int], clique: list[int], positives: set[int]) -> dict[int, int]:
    domains = independent_domains(vertices, clique)
    mapping = independent_variable_map(vertices, domains)
    maximum = len(mapping)
    invalid = sorted(literal for literal in positives if literal > maximum)
    if invalid:
        raise ValueError(f"model contains out-of-range variables: {invalid[:10]}")
    coloring: dict[int, int] = {}
    for vertex in vertices:
        selected = [color for color in domains[vertex] if mapping[(vertex, color)] in positives]
        if len(selected) != 1:
            raise ValueError(f"vertex {vertex} has {len(selected)} selected colors: {selected}")
        coloring[vertex] = selected[0]
    return coloring


def verify_coloring(edges: list[tuple[int, int]], coloring: dict[int, int]) -> None:
    bad = [(left, right, coloring[left]) for left, right in edges if coloring[left] == coloring[right]]
    if bad:
        raise ValueError(f"monochromatic exact-distance-6 edges: {bad[:10]}")


def self_test() -> None:
    vertices = [0, 1]
    edges = [(0, 1)]
    clique = [0]
    domains = independent_domains(vertices, clique)
    mapping = independent_variable_map(vertices, domains)
    valid = {mapping[(0, 0)], mapping[(1, 1)]}
    verify_coloring(edges, decode_coloring(vertices, clique, valid))

    for bad_model in ({max(mapping.values()) + 1}, {mapping[(0, 0)], mapping[(1, 0)]}):
        try:
            colors = decode_coloring(vertices, clique, bad_model)
            verify_coloring(edges, colors)
        except ValueError:
            pass
        else:
            raise SystemExit("self-test failed: invalid model was accepted")

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "solver.out"
        path.write_text("s UNSATISFIABLE\n", encoding="utf-8")
        try:
            parse_positive_literals(path)
        except ValueError:
            pass
        else:
            raise SystemExit("self-test failed: UNSAT transcript was accepted as a model")
    print("PASS: fifth-base child model verifier self-test")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id", nargs="?")
    parser.add_argument("model", nargs="?", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.case_id is None or args.model is None:
        parser.error("case_id and model are required unless --self-test is used")

    case = get_case(args.case_id)
    vertices, edges = build_graph(case)
    clique = fixed_clique_for(vertices)
    try:
        positives = parse_positive_literals(args.model)
        coloring = decode_coloring(vertices, clique, positives)
        verify_coloring(edges, coloring)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    result = {
        "schema": "borsuk-q00-fifth-base-verified-coloring-v1",
        "case_id": args.case_id,
        "canonical_case_list_sha256": EXPECTED_CSV_SHA256,
        "model_sha256": hashlib.sha256(args.model.read_bytes()).hexdigest(),
        "vertices": len(vertices),
        "edges": len(edges),
        "colors_used": len(set(coloring.values())),
        "coloring": {str(vertex): coloring[vertex] for vertex in vertices},
    }
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: verified {COLORS}-coloring for {args.case_id} on {len(vertices)} vertices and {len(edges)} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
