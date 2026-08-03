#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from build_instance import COLORS, build_graph, get_case, variable
from generate_cases import EXPECTED_CANONICAL_CSV_SHA256


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


def decode_coloring(vertices: list[int], positives: set[int]) -> dict[int, int]:
    max_variable = len(vertices) * COLORS
    out_of_range = sorted(literal for literal in positives if literal > max_variable)
    if out_of_range:
        raise ValueError(f"model contains out-of-range variables: {out_of_range[:10]}")

    colors: dict[int, int] = {}
    for vertex_index, vertex in enumerate(vertices):
        selected = [color for color in range(COLORS) if variable(vertex_index, color) in positives]
        if len(selected) != 1:
            raise ValueError(f"vertex {vertex} has {len(selected)} selected colors: {selected}")
        colors[vertex] = selected[0]
    return colors


def verify_coloring(edges: list[tuple[int, int]], colors: dict[int, int]) -> None:
    bad = [(left, right, colors[left]) for left, right in edges if colors[left] == colors[right]]
    if bad:
        raise ValueError(f"monochromatic exact-distance-6 edges: {bad[:10]}")


def self_test() -> None:
    vertices = [0, 1]
    edges = [(0, 1)]
    valid = {variable(0, 0), variable(1, 1)}
    colors = decode_coloring(vertices, valid)
    verify_coloring(edges, colors)

    try:
        verify_coloring(edges, {0: 0, 1: 0})
    except ValueError:
        pass
    else:
        raise SystemExit("self-test failed: monochromatic edge was accepted")

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "solver.txt"
        path.write_text("s UNSATISFIABLE\n", encoding="utf-8")
        try:
            parse_positive_literals(path)
        except ValueError:
            pass
        else:
            raise SystemExit("self-test failed: UNSAT text was accepted as a model")

    print("PASS: model verifier self-test")


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
    try:
        positives = parse_positive_literals(args.model)
        colors = decode_coloring(vertices, positives)
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
        args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"PASS: verified {COLORS}-coloring for {args.case_id} "
        f"on {len(vertices)} vertices and {len(edges)} edges"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
