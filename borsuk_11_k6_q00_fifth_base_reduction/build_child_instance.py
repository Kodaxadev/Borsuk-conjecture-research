#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import TextIO

from generate_fifth_base_cases import (
    BASE,
    EXPECTED_CSV_SHA256,
    K,
    N,
    allowed,
    distance,
    generate_rows,
)

COLORS = 12
CLIQUE_SEARCH_NODE_LIMIT = 50_000
ROOT_CLIQUE = [0, 63, 455, 748, 858, 945, 1241, 1396, 1450, 1635, 1686, 1805]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_case(case_id: str) -> dict[str, object]:
    rows, _ = generate_rows()
    for row in rows:
        if row["id"] == case_id:
            return row
    raise SystemExit(f"unknown q00 fifth-base child: {case_id}")


def build_graph(case: dict[str, object]) -> tuple[list[int], list[tuple[int, int]]]:
    d = int(case["D"])
    vertices = [mask for mask in range(1 << N) if allowed(mask, BASE + (d,))]
    edges: list[tuple[int, int]] = []
    for index, left in enumerate(vertices):
        for right in vertices[index + 1 :]:
            if distance(left, right) == K:
                edges.append((left, right))
    if len(vertices) != int(case["vertices"]) or len(edges) != int(case["exact_distance_edges"]):
        raise SystemExit("regenerated child graph disagrees with canonical case record")
    return vertices, edges


def fixed_clique_for(vertices: list[int], node_limit: int = CLIQUE_SEARCH_NODE_LIMIT) -> list[int]:
    count = len(vertices)
    adjacency = [0] * count
    for left_index, left in enumerate(vertices):
        for right_index in range(left_index + 1, count):
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
        bits = candidates
        while bits:
            bit = bits & -bits
            index = bit.bit_length() - 1
            bits -= bit
            ordered.append((-(adjacency[index] & candidates).bit_count(), index))
        ordered.sort()
        remaining = candidates
        for _, index in ordered:
            if not ((remaining >> index) & 1):
                continue
            if len(clique) + remaining.bit_count() < COLORS:
                return None
            result = search(remaining & adjacency[index], clique + [index])
            if result is not None:
                return result
            if calls > node_limit:
                return None
            remaining &= ~(1 << index)
        return None

    found = search((1 << count) - 1, [])
    if found is not None:
        clique = [vertices[index] for index in found]
    else:
        present = set(vertices)
        clique = [vertex for vertex in ROOT_CLIQUE if vertex in present]
        candidates = sorted(
            (vertex for vertex in vertices if vertex not in clique),
            key=lambda vertex: (-sum(distance(vertex, other) == K for other in vertices), vertex),
        )
        for vertex in candidates:
            if len(clique) == COLORS:
                break
            if all(distance(vertex, existing) == K for existing in clique):
                clique.append(vertex)
    if any(distance(left, right) != K for index, left in enumerate(clique) for right in clique[index + 1 :]):
        raise SystemExit("fixed vertices are not a clique")
    return clique


def allowed_colors_for(vertices: list[int], clique: list[int]) -> dict[int, tuple[int, ...]]:
    assigned = {vertex: color for color, vertex in enumerate(clique)}
    domains: dict[int, tuple[int, ...]] = {}
    for vertex in vertices:
        if vertex in assigned:
            domains[vertex] = (assigned[vertex],)
        else:
            domains[vertex] = tuple(
                color
                for color in range(COLORS)
                if color >= len(clique) or distance(vertex, clique[color]) != K
            )
        if not domains[vertex]:
            raise SystemExit(f"empty color domain for vertex {vertex}")
    return domains


def variable_map_for(vertices: list[int], domains: dict[int, tuple[int, ...]]) -> dict[tuple[int, int], int]:
    output: dict[tuple[int, int], int] = {}
    next_variable = 1
    for vertex in vertices:
        for color in domains[vertex]:
            output[(vertex, color)] = next_variable
            next_variable += 1
    return output


def domain_mask(domain: tuple[int, ...]) -> int:
    return sum(1 << color for color in domain)


def formula_counts(vertices: list[int], edges: list[tuple[int, int]], domains: dict[int, tuple[int, ...]]) -> tuple[int, int]:
    variables = sum(len(domains[vertex]) for vertex in vertices)
    clauses = sum(1 + math.comb(len(domains[vertex]), 2) for vertex in vertices)
    masks = {vertex: domain_mask(domains[vertex]) for vertex in vertices}
    clauses += sum((masks[left] & masks[right]).bit_count() for left, right in edges)
    return variables, clauses


def emit_cnf(stream: TextIO, vertices: list[int], edges: list[tuple[int, int]], domains: dict[int, tuple[int, ...]]) -> None:
    variables = variable_map_for(vertices, domains)
    variable_count, clause_count = formula_counts(vertices, edges, domains)
    stream.write("c Borsuk q00 fifth-base child compact 12-list-coloring encoding\n")
    stream.write("c Variables are assigned by vertex order, then allowed color order.\n")
    stream.write(f"p cnf {variable_count} {clause_count}\n")
    for vertex in vertices:
        identifiers = [variables[(vertex, color)] for color in domains[vertex]]
        stream.write(" ".join(map(str, identifiers)) + " 0\n")
        for left_index in range(len(identifiers)):
            for right_index in range(left_index + 1, len(identifiers)):
                stream.write(f"-{identifiers[left_index]} -{identifiers[right_index]} 0\n")
    masks = {vertex: domain_mask(domains[vertex]) for vertex in vertices}
    for left, right in edges:
        common = masks[left] & masks[right]
        while common:
            bit = common & -common
            color = bit.bit_length() - 1
            common -= bit
            stream.write(f"-{variables[(left, color)]} -{variables[(right, color)]} 0\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    if not args.metadata_only and args.output_dir is None:
        parser.error("--output-dir is required unless --metadata-only is used")

    case = get_case(args.case_id)
    vertices, edges = build_graph(case)
    clique = fixed_clique_for(vertices)
    domains = allowed_colors_for(vertices, clique)
    variables, clauses = formula_counts(vertices, edges, domains)
    metadata: dict[str, object] = {
        "schema": "borsuk-q00-fifth-base-list-color-instance-v1",
        "case_id": case["id"],
        "canonical_case_list_sha256": EXPECTED_CSV_SHA256,
        "q00_base": list(BASE),
        "fifth_base": int(case["D"]),
        "vertices": len(vertices),
        "edges": len(edges),
        "colors": COLORS,
        "fixed_clique": clique,
        "domain_size_histogram": dict(sorted(Counter(map(len, domains.values())).items())),
        "variables": variables,
        "clauses": clauses,
        "result_state": "UNKNOWN",
    }
    if args.metadata_only:
        print(json.dumps(metadata, indent=2, sort_keys=True))
        return 0

    assert args.output_dir is not None
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cnf_path = args.output_dir / f"{args.case_id}_12color.cnf"
    map_path = args.output_dir / f"{args.case_id}_variable_map.json"
    metadata_path = args.output_dir / f"{args.case_id}_metadata.json"
    pair_map = variable_map_for(vertices, domains)
    reverse = {str(variable): [vertex, color] for (vertex, color), variable in pair_map.items()}
    map_path.write_text(json.dumps({
        "schema": "borsuk-q00-fifth-base-variable-map-v1",
        "case_id": case["id"],
        "vertices": vertices,
        "fixed_clique": clique,
        "allowed_colors": {str(vertex): list(domains[vertex]) for vertex in vertices},
        "variables": variables,
        "clauses": clauses,
        "variable_to_vertex_color": reverse,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with cnf_path.open("w", encoding="ascii", newline="") as stream:
        emit_cnf(stream, vertices, edges, domains)
    metadata["cnf_sha256"] = sha256_bytes(cnf_path.read_bytes())
    metadata["variable_map_sha256"] = sha256_bytes(map_path.read_bytes())
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
