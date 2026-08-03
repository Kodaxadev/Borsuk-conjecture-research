#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import TextIO

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
CLIQUE_SEARCH_NODE_LIMIT = 50_000
ROOT_CLIQUE = [0, 63, 455, 748, 858, 945, 1241, 1396, 1450, 1635, 1686, 1805]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_case(case_id: str) -> dict[str, object]:
    raw, _ = generate_raw_cases()
    for case in canonical_classes(raw):
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


def fixed_clique_for(
    vertices: list[int], node_limit: int = CLIQUE_SEARCH_NODE_LIMIT
) -> list[int]:
    """Find a deterministic symmetry-breaking clique of size at most COLORS.

    A bounded exact search first tries to find a full 12-clique. If that search
    exhausts its deterministic node budget, the routine falls back to the
    historical root clique intersected with the trim and extends it greedily.
    Either result is independently checked before it is used in the encoding.
    """

    vertex_count = len(vertices)
    adjacency = [0] * vertex_count
    for left_index, left in enumerate(vertices):
        for right_index in range(left_index + 1, vertex_count):
            if distance(left, vertices[right_index]) == K:
                adjacency[left_index] |= 1 << right_index
                adjacency[right_index] |= 1 << left_index

    calls = 0

    def search(candidates: int, clique: list[int]) -> list[int] | None:
        nonlocal calls
        calls += 1
        if calls > node_limit:
            return None
        if len(clique) == COLORS:
            return clique
        if len(clique) + candidates.bit_count() < COLORS:
            return None

        ordered: list[tuple[int, int]] = []
        remaining_bits = candidates
        while remaining_bits:
            bit = remaining_bits & -remaining_bits
            vertex_index = bit.bit_length() - 1
            remaining_bits -= bit
            ordered.append((-(adjacency[vertex_index] & candidates).bit_count(), vertex_index))
        ordered.sort()

        remaining = candidates
        for _, vertex_index in ordered:
            if not ((remaining >> vertex_index) & 1):
                continue
            if len(clique) + remaining.bit_count() < COLORS:
                return None
            result = search(remaining & adjacency[vertex_index], clique + [vertex_index])
            if result is not None:
                return result
            if calls > node_limit:
                return None
            remaining &= ~(1 << vertex_index)
        return None

    found = search((1 << vertex_count) - 1, [])
    if found is not None:
        clique = [vertices[index] for index in found]
    else:
        present = set(vertices)
        clique = [vertex for vertex in ROOT_CLIQUE if vertex in present]
        candidates = sorted(
            (vertex for vertex in vertices if vertex not in clique),
            key=lambda vertex: (
                -sum(distance(vertex, other) == K for other in vertices),
                vertex,
            ),
        )
        for vertex in candidates:
            if len(clique) == COLORS:
                break
            if all(distance(vertex, existing) == K for existing in clique):
                clique.append(vertex)

    for left_index, left in enumerate(clique):
        for right in clique[left_index + 1 :]:
            if distance(left, right) != K:
                raise SystemExit("fixed symmetry-breaking vertices are not a clique")
    if len(clique) > COLORS:
        raise SystemExit("symmetry-breaking clique exceeds the color count")
    return clique


def formula_counts(vertex_count: int, edge_count: int, fixed_count: int) -> tuple[int, int]:
    variables = vertex_count * COLORS
    clauses_per_vertex = 1 + math.comb(COLORS, 2)
    clauses = vertex_count * clauses_per_vertex + edge_count * COLORS + fixed_count
    return variables, clauses


def mapping_document(vertices: list[int], fixed_clique: list[int], clauses: int) -> dict[str, object]:
    return {
        "schema": "borsuk-color-variable-map-v1",
        "colors": COLORS,
        "vertices": vertices,
        "fixed_clique": fixed_clique,
        "variable_formula": "vertex_index * 12 + color + 1",
        "clauses": clauses,
        "variables": len(vertices) * COLORS,
    }


def instance_metadata(
    case: dict[str, object],
    vertices: list[int],
    edges: list[tuple[int, int]],
    fixed_clique: list[int],
) -> dict[str, object]:
    variables, clauses = formula_counts(len(vertices), len(edges), len(fixed_clique))
    return {
        "schema": "borsuk-four-base-sat-instance-v1",
        "case_id": case["id"],
        "canonical_case_list_sha256": EXPECTED_CANONICAL_CSV_SHA256,
        "representative_case": case["representative_case"],
        "covered_intermediate_cases": str(case["members"]).split(";"),
        "base": [0, A, int(case["B"]), int(case["C"])],
        "vertices": len(vertices),
        "edges": len(edges),
        "colors": COLORS,
        "fixed_clique": fixed_clique,
        "variables": variables,
        "clauses": clauses,
        "result_state": "UNKNOWN",
    }


def emit_cnf(stream: TextIO, vertices: list[int], edges: list[tuple[int, int]], fixed_clique: list[int]) -> None:
    variables, clauses = formula_counts(len(vertices), len(edges), len(fixed_clique))
    index = {vertex: position for position, vertex in enumerate(vertices)}

    stream.write("c Borsuk n=11 k=6 canonical four-base trim 12-colorability\n")
    stream.write("c Variable x_(vertex_index,color) = vertex_index*12 + color + 1.\n")
    stream.write("c Exactly one color is selected per vertex.\n")
    stream.write("c Unit clauses assign distinct colors to a deterministic contained clique.\n")
    stream.write(f"p cnf {variables} {clauses}\n")

    for vertex_index in range(len(vertices)):
        ids = [variable(vertex_index, color) for color in range(COLORS)]
        stream.write(" ".join(map(str, ids)) + " 0\n")
        for left_color in range(COLORS):
            for right_color in range(left_color + 1, COLORS):
                stream.write(f"-{ids[left_color]} -{ids[right_color]} 0\n")

    for left, right in edges:
        left_index = index[left]
        right_index = index[right]
        for color in range(COLORS):
            stream.write(f"-{variable(left_index, color)} -{variable(right_index, color)} 0\n")

    for color, vertex in enumerate(fixed_clique):
        stream.write(f"{variable(index[vertex], color)} 0\n")


def write_cnf(path: Path, vertices: list[int], edges: list[tuple[int, int]], fixed_clique: list[int]) -> str:
    with path.open("w", encoding="ascii", newline="") as stream:
        emit_cnf(stream, vertices, edges, fixed_clique)
    return sha256_bytes(path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="regenerate the case and print deterministic instance counts without writing CNF artifacts",
    )
    args = parser.parse_args()

    if not args.metadata_only and args.output_dir is None:
        parser.error("--output-dir is required unless --metadata-only is used")

    case = get_case(args.case_id)
    vertices, edges = build_graph(case)
    fixed_clique = fixed_clique_for(vertices)
    metadata = instance_metadata(case, vertices, edges, fixed_clique)

    if args.metadata_only:
        print(json.dumps(metadata, indent=2, sort_keys=True))
        return 0

    assert args.output_dir is not None
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cnf_path = args.output_dir / f"{args.case_id}_12color.cnf"
    map_path = args.output_dir / f"{args.case_id}_variable_map.json"
    metadata_path = args.output_dir / f"{args.case_id}_metadata.json"

    mapping = mapping_document(vertices, fixed_clique, int(metadata["clauses"]))
    map_path.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    metadata["cnf_sha256"] = write_cnf(cnf_path, vertices, edges, fixed_clique)
    metadata["variable_map_sha256"] = sha256_bytes(map_path.read_bytes())
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
