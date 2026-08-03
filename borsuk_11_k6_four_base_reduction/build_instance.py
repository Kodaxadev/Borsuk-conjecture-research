#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from generate_cases import (
    A,
    K,
    N,
    EXPECTED_CANONICAL_CSV_SHA256,
    allowed,
    canonical_classes,
    distance,
    generate_raw_cases,
)

COLORS = 12
ROOT_CLIQUE = [0, 63, 455, 748, 858, 945, 1241, 1396, 1450, 1635, 1686, 1805]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_case(case_id: str) -> dict[str, object]:
    raw, _ = generate_raw_cases()
    cases = canonical_classes(raw)
    for case in cases:
        if case["id"] == case_id:
            return case
    raise SystemExit(f"unknown canonical case id: {case_id}")


def build_graph(case: dict[str, object]) -> tuple[list[int], list[tuple[int, int]]]:
    base = (0, A, int(case["B"]), int(case["C"]))
    vertices = [mask for mask in range(1 << N) if allowed(mask, base)]
    edges: list[tuple[int, int]] = []
    for index, left in enumerate(vertices):
        for right in vertices[index + 1 :]:
            if distance(left, right) == K:
                edges.append((left, right))
    if len(vertices) != int(case["vertices"]) or len(edges) != int(case["exact_distance_edges"]):
        raise SystemExit("regenerated graph statistics disagree with canonical case record")
    return vertices, edges


def variable(vertex_index: int, color: int) -> int:
    return vertex_index * COLORS + color + 1


def build_cnf(vertices: list[int], edges: list[tuple[int, int]]) -> tuple[str, dict[str, object]]:
    index = {vertex: position for position, vertex in enumerate(vertices)}
    fixed_clique = [vertex for vertex in ROOT_CLIQUE if vertex in index]
    for left_index, left in enumerate(fixed_clique):
        for right in fixed_clique[left_index + 1 :]:
            if distance(left, right) != K:
                raise SystemExit("fixed symmetry-breaking vertices are not a clique")

    clauses: list[list[int]] = []
    for vertex_index in range(len(vertices)):
        ids = [variable(vertex_index, color) for color in range(COLORS)]
        clauses.append(ids)
        for left_color in range(COLORS):
            for right_color in range(left_color + 1, COLORS):
                clauses.append([-ids[left_color], -ids[right_color]])

    for left, right in edges:
        left_index = index[left]
        right_index = index[right]
        for color in range(COLORS):
            clauses.append([-variable(left_index, color), -variable(right_index, color)])

    for color, vertex in enumerate(fixed_clique):
        clauses.append([variable(index[vertex], color)])

    lines = [
        "c Borsuk n=11 k=6 canonical four-base trim 12-colorability",
        "c Variable x_(vertex_index,color) = vertex_index*12 + color + 1.",
        "c Unit clauses assign distinct colors to a deterministic contained clique.",
        f"p cnf {len(vertices) * COLORS} {len(clauses)}",
    ]
    lines.extend(" ".join(map(str, clause)) + " 0" for clause in clauses)
    cnf = "\n".join(lines) + "\n"
    mapping = {
        "schema": "borsuk-color-variable-map-v1",
        "colors": COLORS,
        "vertices": vertices,
        "fixed_clique": fixed_clique,
        "variable_formula": "vertex_index * 12 + color + 1",
        "clauses": len(clauses),
        "variables": len(vertices) * COLORS,
    }
    return cnf, mapping


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    case = get_case(args.case_id)
    vertices, edges = build_graph(case)
    cnf, mapping = build_cnf(vertices, edges)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    cnf_path = args.output_dir / f"{args.case_id}_12color.cnf"
    map_path = args.output_dir / f"{args.case_id}_variable_map.json"
    metadata_path = args.output_dir / f"{args.case_id}_metadata.json"
    cnf_path.write_text(cnf, encoding="ascii", newline="")
    map_path.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    metadata = {
        "schema": "borsuk-four-base-sat-instance-v1",
        "case_id": args.case_id,
        "canonical_case_list_sha256": EXPECTED_CANONICAL_CSV_SHA256,
        "representative_case": case["representative_case"],
        "covered_intermediate_cases": str(case["members"]).split(";"),
        "base": [0, A, int(case["B"]), int(case["C"])],
        "vertices": len(vertices),
        "edges": len(edges),
        "colors": COLORS,
        "fixed_clique": mapping["fixed_clique"],
        "variables": mapping["variables"],
        "clauses": mapping["clauses"],
        "cnf_sha256": sha256_bytes(cnf.encode("ascii")),
        "variable_map_sha256": sha256_bytes(map_path.read_bytes()),
        "result_state": "UNKNOWN",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
