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


def fixed_clique_for(
    vertices: list[int], node_limit: int = CLIQUE_SEARCH_NODE_LIMIT
) -> list[int]:
    """Find a deterministic symmetry-breaking clique of size at most COLORS."""

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


def allowed_colors_for(
    vertices: list[int], fixed_clique: list[int]
) -> dict[int, tuple[int, ...]]:
    """Return the sound list-color domain after fixing the clique labels.

    Every proper coloring gives distinct colors to clique vertices. A global
    color permutation therefore lets us assign clique vertex i color i. A
    non-clique vertex cannot use the color of any fixed clique neighbor, so
    those variables can be deleted before CNF generation.
    """

    assigned = {vertex: color for color, vertex in enumerate(fixed_clique)}
    domains: dict[int, tuple[int, ...]] = {}
    for vertex in vertices:
        if vertex in assigned:
            domains[vertex] = (assigned[vertex],)
        else:
            domains[vertex] = tuple(
                color
                for color in range(COLORS)
                if color >= len(fixed_clique)
                or distance(vertex, fixed_clique[color]) != K
            )
        if not domains[vertex]:
            raise SystemExit(f"fixed clique leaves vertex {vertex} with an empty color domain")
    return domains


def variable_map_for(
    vertices: list[int], domains: dict[int, tuple[int, ...]]
) -> tuple[dict[tuple[int, int], int], dict[int, tuple[int, int]]]:
    pair_to_variable: dict[tuple[int, int], int] = {}
    variable_to_pair: dict[int, tuple[int, int]] = {}
    next_variable = 1
    for vertex in vertices:
        for color in domains[vertex]:
            pair_to_variable[(vertex, color)] = next_variable
            variable_to_pair[next_variable] = (vertex, color)
            next_variable += 1
    return pair_to_variable, variable_to_pair


def domain_mask(domain: tuple[int, ...]) -> int:
    return sum(1 << color for color in domain)


def formula_counts(
    vertices: list[int],
    edges: list[tuple[int, int]],
    domains: dict[int, tuple[int, ...]],
) -> tuple[int, int]:
    variables = sum(len(domains[vertex]) for vertex in vertices)
    clauses = sum(1 + math.comb(len(domains[vertex]), 2) for vertex in vertices)
    masks = {vertex: domain_mask(domains[vertex]) for vertex in vertices}
    clauses += sum((masks[left] & masks[right]).bit_count() for left, right in edges)
    return variables, clauses


def mapping_document(
    vertices: list[int],
    fixed_clique: list[int],
    domains: dict[int, tuple[int, ...]],
    clauses: int,
) -> dict[str, object]:
    _, variable_to_pair = variable_map_for(vertices, domains)
    return {
        "schema": "borsuk-list-color-variable-map-v2",
        "colors": COLORS,
        "vertices": vertices,
        "fixed_clique": fixed_clique,
        "allowed_colors": {str(vertex): list(domains[vertex]) for vertex in vertices},
        "variables": len(variable_to_pair),
        "clauses": clauses,
    }


def instance_metadata(
    case: dict[str, object],
    vertices: list[int],
    edges: list[tuple[int, int]],
    fixed_clique: list[int],
    domains: dict[int, tuple[int, ...]],
) -> dict[str, object]:
    variables, clauses = formula_counts(vertices, edges, domains)
    domain_sizes = sorted({len(domain) for domain in domains.values()})
    return {
        "schema": "borsuk-four-base-list-color-instance-v2",
        "case_id": case["id"],
        "canonical_case_list_sha256": EXPECTED_CANONICAL_CSV_SHA256,
        "representative_case": case["representative_case"],
        "covered_intermediate_cases": str(case["members"]).split(";"),
        "base": [0, A, int(case["B"]), int(case["C"])],
        "vertices": len(vertices),
        "edges": len(edges),
        "colors": COLORS,
        "fixed_clique": fixed_clique,
        "domain_size_histogram": {
            str(size): sum(len(domain) == size for domain in domains.values())
            for size in domain_sizes
        },
        "variables": variables,
        "clauses": clauses,
        "result_state": "UNKNOWN",
    }


def emit_cnf(
    stream: TextIO,
    vertices: list[int],
    edges: list[tuple[int, int]],
    fixed_clique: list[int],
    domains: dict[int, tuple[int, ...]],
) -> None:
    pair_to_variable, _ = variable_map_for(vertices, domains)
    variables, clauses = formula_counts(vertices, edges, domains)

    stream.write("c Borsuk n=11 k=6 compact 12-list-coloring encoding\n")
    stream.write("c Fixed clique colors are removed from incompatible vertex domains.\n")
    stream.write("c Variables are assigned by vertex order, then allowed color order.\n")
    stream.write(f"p cnf {variables} {clauses}\n")

    for vertex in vertices:
        identifiers = [pair_to_variable[(vertex, color)] for color in domains[vertex]]
        stream.write(" ".join(map(str, identifiers)) + " 0\n")
        for left_index in range(len(identifiers)):
            for right_index in range(left_index + 1, len(identifiers)):
                stream.write(
                    f"-{identifiers[left_index]} -{identifiers[right_index]} 0\n"
                )

    masks = {vertex: domain_mask(domains[vertex]) for vertex in vertices}
    for left, right in edges:
        common = masks[left] & masks[right]
        while common:
            bit = common & -common
            color = bit.bit_length() - 1
            common -= bit
            stream.write(
                f"-{pair_to_variable[(left, color)]} "
                f"-{pair_to_variable[(right, color)]} 0\n"
            )


def write_cnf(
    path: Path,
    vertices: list[int],
    edges: list[tuple[int, int]],
    fixed_clique: list[int],
    domains: dict[int, tuple[int, ...]],
) -> str:
    with path.open("w", encoding="ascii", newline="") as stream:
        emit_cnf(stream, vertices, edges, fixed_clique, domains)
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
    domains = allowed_colors_for(vertices, fixed_clique)
    metadata = instance_metadata(case, vertices, edges, fixed_clique, domains)

    if args.metadata_only:
        print(json.dumps(metadata, indent=2, sort_keys=True))
        return 0

    assert args.output_dir is not None
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cnf_path = args.output_dir / f"{args.case_id}_12color.cnf"
    map_path = args.output_dir / f"{args.case_id}_variable_map.json"
    metadata_path = args.output_dir / f"{args.case_id}_metadata.json"

    mapping = mapping_document(
        vertices, fixed_clique, domains, int(metadata["clauses"])
    )
    map_path.write_text(
        json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    metadata["cnf_sha256"] = write_cnf(
        cnf_path, vertices, edges, fixed_clique, domains
    )
    metadata["variable_map_sha256"] = sha256_bytes(map_path.read_bytes())
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
