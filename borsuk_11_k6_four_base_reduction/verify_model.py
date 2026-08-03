#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from build_instance import COLORS, build_graph, fixed_clique_for, get_case
from generate_cases import EXPECTED_CANONICAL_CSV_SHA256, K, distance


def parse_positive_literals(path: Path) -> set[int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if "UNSAT" in text.upper():
        raise ValueError("UNSAT text is not a certificate; provide a checked proof trace")

    positives: set[int] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("c", "p")):
            continue
        if line.startswith("s"):
            continue
        if line.startswith("v"):
            line = line[1:].strip()
            tokens = line.split()
        else:
            tokens = line.split()
            if not tokens:
                continue
            try:
                [int(token) for token in tokens]
            except ValueError:
                continue
        for token in tokens:
            literal = int(token)
            if literal > 0:
                positives.add(literal)
    if not positives:
        raise ValueError("model contains no positive literals")
    return positives


def independent_domains(
    vertices: list[int], fixed_clique: list[int]
) -> dict[int, tuple[int, ...]]:
    assigned = {vertex: color for color, vertex in enumerate(fixed_clique)}
    domains: dict[int, tuple[int, ...]] = {}
    for vertex in vertices:
        if vertex in assigned:
            domain = (assigned[vertex],)
        else:
            domain = tuple(
                color
                for color in range(COLORS)
                if color >= len(fixed_clique)
                or distance(vertex, fixed_clique[color]) != K
            )
        if not domain:
            raise ValueError(f"vertex {vertex} has an empty reconstructed color domain")
        domains[vertex] = domain
    return domains


def independent_variable_map(
    vertices: list[int], domains: dict[int, tuple[int, ...]]
) -> dict[tuple[int, int], int]:
    mapping: dict[tuple[int, int], int] = {}
    next_variable = 1
    for vertex in vertices:
        for color in domains[vertex]:
            mapping[(vertex, color)] = next_variable
            next_variable += 1
    return mapping


def decode_coloring(
    vertices: list[int], fixed_clique: list[int], positives: set[int]
) -> dict[int, int]:
    domains = independent_domains(vertices, fixed_clique)
    mapping = independent_variable_map(vertices, domains)
    max_variable = len(mapping)
    out_of_range = sorted(literal for literal in positives if literal > max_variable)
    if out_of_range:
        raise ValueError(f"model contains out-of-range variables: {out_of_range[:10]}")

    colors: dict[int, int] = {}
    for vertex in vertices:
        selected = [
            color
            for color in domains[vertex]
            if mapping[(vertex, color)] in positives
        ]
        if len(selected) != 1:
            raise ValueError(
                f"vertex {vertex} has {len(selected)} selected colors: {selected}"
            )
        colors[vertex] = selected[0]
    return colors


def verify_coloring(edges: list[tuple[int, int]], colors: dict[int, int]) -> None:
    bad = [
        (left, right, colors[left])
        for left, right in edges
        if colors[left] == colors[right]
    ]
    if bad:
        raise ValueError(f"monochromatic exact-distance-6 edges: {bad[:10]}")


def self_test() -> None:
    vertices = [0, 1]
    edges = [(0, 1)]
    fixed_clique = [0]
    domains = independent_domains(vertices, fixed_clique)
    mapping = independent_variable_map(vertices, domains)
    valid = {mapping[(0, 0)], mapping[(1, 1)]}
    colors = decode_coloring(vertices, fixed_clique, valid)
    verify_coloring(edges, colors)

    try:
        verify_coloring(edges, {0: 0, 1: 0})
    except ValueError:
        pass
    else:
        raise SystemExit("self-test failed: monochromatic edge was accepted")

    try:
        decode_coloring(vertices, fixed_clique, {max(mapping.values()) + 1})
    except ValueError:
        pass
    else:
        raise SystemExit("self-test failed: out-of-range variable was accepted")

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "solver.txt"
        path.write_text("s UNSATISFIABLE\n", encoding="utf-8")
        try:
            parse_positive_literals(path)
        except ValueError:
            pass
        else:
            raise SystemExit("self-test failed: UNSAT text was accepted as a model")

    print("PASS: compact model verifier self-test")


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
    fixed_clique = fixed_clique_for(vertices)
    try:
        positives = parse_positive_literals(args.model)
        colors = decode_coloring(vertices, fixed_clique, positives)
        verify_coloring(edges, colors)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    output = {
        "schema": "borsuk-verified-coloring-v1",
        "case_id": args.case_id,
        "canonical_case_list_sha256": EXPECTED_CANONICAL_CSV_SHA256,
        "model_sha256": hashlib.sha256(args.model.read_bytes()).hexdigest(),
        "vertices": len(vertices),
        "edges": len(edges),
        "colors_used": len(set(colors.values())),
        "coloring": {str(vertex): colors[vertex] for vertex in vertices},
    }
    if args.output:
        args.output.write_text(
            json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(
        f"PASS: verified {COLORS}-coloring for {args.case_id} "
        f"on {len(vertices)} vertices and {len(edges)} edges"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
