#!/usr/bin/env python3
"""Exact fourth-vertex refinement of the Borsuk(11,6) triangle branch.

The standard library is sufficient. The script classifies the fourth base
vertex into 11 stabilizer orbits, reconstructs every branch graph, checks fixed
hashes, and optionally emits symmetry-broken 12-coloring CNFs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from itertools import combinations
from pathlib import Path

N = 11
K = 6
COLORS = 12
ZERO = 0
A = 63
B = 455
HADAMARD_CLIQUE = [
    0, 63, 455, 748, 858, 945,
    1241, 1396, 1450, 1635, 1686, 1805,
]
BLOCKS = (
    (0, 1, 2),       # A intersect B
    (3, 4, 5),       # A minus B
    (6, 7, 8),       # B minus A
    (9, 10),          # outside A union B
)

EXPECTED = {
    (0, 3, 3, 0): {
        "representative": 504, "orbit_size": 1, "vertices": 436,
        "edges": 39642, "incompatible_pairs": 13284,
        "fixed_clique": 9, "variables": 3339, "clauses": 219595,
        "edge_sha256": "e82086a490ef406484c52167b14c590824e8c7ad66c13edfa83f294c1168b383",
        "cnf_sha256": "9417bf106dfb6a75a570d4eb8d74c6e2a0bf46752aa31948b000cff2e26fa86e",
    },
    (1, 2, 2, 1): {
        "representative": 729, "orbit_size": 54, "vertices": 436,
        "edges": 39640, "incompatible_pairs": 13188,
        "fixed_clique": 10, "variables": 3145, "clauses": 190813,
        "edge_sha256": "5e05c4dc8a3ed5cd23ad40c56fd2b8d48aef1feec985a9044905c6c1467eb517",
        "cnf_sha256": "573da4a49831684323978f1f86a617a3bf21359d51ee982a3099d7f3d5ee719b",
    },
    (1, 2, 3, 0): {
        "representative": 473, "orbit_size": 18, "vertices": 460,
        "edges": 44391, "incompatible_pairs": 14676,
        "fixed_clique": 10, "variables": 3322, "clauses": 213295,
        "edge_sha256": "4da92b4ac01818ee028bd7f693d39f405aceb3f05f0cd64d7762c329712a08b0",
        "cnf_sha256": "7daf0cf8fd87437df519f47aaebe2f9695c37b6a2800582df6a1e7dc69d66c9c",
    },
    (2, 1, 1, 2): {
        "representative": 1611, "orbit_size": 27, "vertices": 436,
        "edges": 39600, "incompatible_pairs": 13104,
        "fixed_clique": 10, "variables": 3151, "clauses": 191175,
        "edge_sha256": "f009ecf6dba467260f003ef860494dfb0985614e8a47c1066fcf9511f77c08aa",
        "cnf_sha256": "1c02051b15358d6584fd7401eb909785cc04dbd503e9eb884165e2c567490171",
    },
    (2, 1, 2, 1): {
        "representative": 715, "orbit_size": 108, "vertices": 460,
        "edges": 44388, "incompatible_pairs": 14484,
        "fixed_clique": 11, "variables": 3144, "clauses": 184823,
        "edge_sha256": "9035ad6b4f6da62e13fdae30acc9ba147d968128fe0809c6a30b8401480c9156",
        "cnf_sha256": "7e48668d95bea36097448ccd28b2cd8cac74a5b03361f64a5028a8cb5da9b161",
    },
    (2, 1, 3, 0): {
        "representative": 459, "orbit_size": 18, "vertices": 490,
        "edges": 50739, "incompatible_pairs": 16740,
        "fixed_clique": 10, "variables": 3559, "clauses": 245516,
        "edge_sha256": "980f61465b191b91a0a886414f0d335c90f726e953ac74da8de3fcb87b95ef77",
        "cnf_sha256": "3cabdb5317eacf11656811d1025ec90ca41d05aa32d31325cf12e07ec98fa2d2",
    },
    (2, 2, 2, 0): {
        "representative": 219, "orbit_size": 27, "vertices": 481,
        "edges": 48777, "incompatible_pairs": 15870,
        "fixed_clique": 10, "variables": 3479, "clauses": 234150,
        "edge_sha256": "f5b9030cb67800347d0dc91ccc2500be2c6c4a02dab803d8dedf07509a2bed86",
        "cnf_sha256": "e5e2baba3c38b5b93b5ee61962ae8d8ffba8c1e7e07c4b2c468042775a82ee84",
    },
    (3, 0, 1, 2): {
        "representative": 1607, "orbit_size": 6, "vertices": 461,
        "edges": 44553, "incompatible_pairs": 14502,
        "fixed_clique": 10, "variables": 3337, "clauses": 214654,
        "edge_sha256": "f8d22900624d3e3a6746e9564ce0ea36a90e93c4fecb87ce7cba54f43dd7b021",
        "cnf_sha256": "b7d6c6602ff0e3ebdda639c54a1821dcc21c948785ffc164c18950cdfa0d2dc4",
    },
    (3, 0, 2, 1): {
        "representative": 711, "orbit_size": 12, "vertices": 491,
        "edges": 50904, "incompatible_pairs": 16605,
        "fixed_clique": 10, "variables": 3566, "clauses": 246143,
        "edge_sha256": "080915128a5ff2d09fb01a8943a2312ce891dc37ce0783e7276b9d1ccdcfe3dc",
        "cnf_sha256": "1603332aba070f0bc0e5d8662d1019470793d19f057a0e7eba4ead8ba94ad646",
    },
    (3, 1, 1, 1): {
        "representative": 591, "orbit_size": 18, "vertices": 482,
        "edges": 48973, "incompatible_pairs": 15816,
        "fixed_clique": 9, "variables": 3711, "clauses": 271527,
        "edge_sha256": "52c8e57aa49375ff068ecb8979eb14d74161b5d093f2f0519c8802dd9e070f18",
        "cnf_sha256": "75e2b14bfa151a99e7c4e5e5c2eaadbb173a0d1b66822b21b38153799ee4cf80",
    },
    (3, 1, 2, 0): {
        "representative": 207, "orbit_size": 18, "vertices": 512,
        "edges": 55617, "incompatible_pairs": 18378,
        "fixed_clique": 10, "variables": 3719, "clauses": 268564,
        "edge_sha256": "76f268db2462491a6e302b0e5391184454080ebacd1748ccbc7b05d58b1031b9",
        "cnf_sha256": "b8720b7d8c8981e6d23998fe14919bb05a84822e52c9a17478a37c3582ea1c7a",
    },
}


def wt(x: int) -> int:
    return x.bit_count()


def dist(x: int, y: int) -> int:
    return (x ^ y).bit_count()


def tuple_id(counts: tuple[int, int, int, int]) -> str:
    a, b, c, d = counts
    return f"a{a}_b{b}_c{c}_d{d}"


def counts_for(x: int) -> tuple[int, int, int, int]:
    return tuple(sum((x >> coordinate) & 1 for coordinate in block) for block in BLOCKS)  # type: ignore[return-value]


def canonical_counts(x: int) -> tuple[int, int, int, int]:
    a, b, c, d = counts_for(x)
    return (a, min(b, c), max(b, c), d)


def representative(counts: tuple[int, int, int, int]) -> int:
    value = 0
    for count, block in zip(counts, BLOCKS):
        for coordinate in block[:count]:
            value |= 1 << coordinate
    return value


def triangle_trim() -> list[int]:
    return [
        x for x in range(1 << N)
        if wt(x) % 2 == 0
        and dist(x, ZERO) <= K
        and dist(x, A) <= K
        and dist(x, B) <= K
    ]


def candidate_fourth_vertices(trim: list[int]) -> list[int]:
    return [x for x in trim if wt(x) == K and x not in (A, B)]


def orbit_sizes(candidates: list[int]) -> Counter[tuple[int, int, int, int]]:
    return Counter(canonical_counts(x) for x in candidates)


def branch_vertices(trim: list[int], c: int) -> list[int]:
    return [x for x in trim if dist(x, c) <= K]


def branch_edges(vertices: list[int]) -> list[tuple[int, int]]:
    return [
        (u, v) for u, v in combinations(vertices, 2)
        if dist(u, v) == K
    ]


def edge_hash(edges: list[tuple[int, int]]) -> str:
    data = "".join(f"{u},{v}\n" for u, v in edges).encode("ascii")
    return hashlib.sha256(data).hexdigest()


def fixed_clique(vertices: list[int]) -> dict[int, int]:
    present = set(vertices)
    return {h: color for color, h in enumerate(HADAMARD_CLIQUE) if h in present}


def color_domains(vertices: list[int], fixed: dict[int, int]) -> dict[int, list[int]]:
    result: dict[int, list[int]] = {}
    for vertex in vertices:
        if vertex in fixed:
            result[vertex] = [fixed[vertex]]
            continue
        forbidden = {
            color for h, color in fixed.items()
            if dist(vertex, h) == K
        }
        result[vertex] = [
            color for color in range(COLORS)
            if color not in forbidden
        ]
        assert result[vertex]
    return result


def emit_cnf(
    out_dir: Path,
    orbit: str,
    vertices: list[int],
    edges: list[tuple[int, int]],
) -> dict[str, object]:
    fixed = fixed_clique(vertices)
    domains = color_domains(vertices, fixed)
    variable: dict[tuple[int, int], int] = {}
    reverse: list[tuple[int, int]] = []
    for vertex in vertices:
        for color in domains[vertex]:
            variable[(vertex, color)] = len(reverse) + 1
            reverse.append((vertex, color))

    clauses: list[list[int]] = []
    for vertex in vertices:
        ids = [variable[(vertex, color)] for color in domains[vertex]]
        clauses.append(ids)
        for first, second in combinations(ids, 2):
            clauses.append([-first, -second])
    for u, v in edges:
        shared = set(domains[u]).intersection(domains[v])
        for color in sorted(shared):
            clauses.append([-variable[(u, color)], -variable[(v, color)]])

    cnf_path = out_dir / f"triangle_refinement_{orbit}.cnf"
    map_path = out_dir / f"triangle_refinement_{orbit}_variables.json"
    with cnf_path.open("w", encoding="ascii", newline="\n") as handle:
        handle.write(f"p cnf {len(reverse)} {len(clauses)}\n")
        for clause in clauses:
            handle.write(" ".join(map(str, clause)) + " 0\n")
    mapping = {
        str(index + 1): {"vertex": vertex, "color": color}
        for index, (vertex, color) in enumerate(reverse)
    }
    map_path.write_text(
        json.dumps(mapping, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "variables": len(reverse),
        "clauses": len(clauses),
        "fixed_clique_vertices": len(fixed),
        "domain_size_distribution": dict(sorted(Counter(map(len, domains.values())).items())),
        "cnf": cnf_path.name,
        "variable_map": map_path.name,
        "cnf_sha256": hashlib.sha256(cnf_path.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("generated_triangle_refinement"))
    parser.add_argument("--emit-cnf", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    trim = triangle_trim()
    assert len(trim) == 555
    candidates = candidate_fourth_vertices(trim)
    assert len(candidates) == 307
    observed_orbits = orbit_sizes(candidates)
    assert observed_orbits == Counter({counts: data["orbit_size"] for counts, data in EXPECTED.items()})
    assert sum(observed_orbits.values()) == 307

    report: dict[str, object] = {
        "n": N,
        "diameter": K,
        "triangle": [ZERO, A, B],
        "triangle_branch_vertices": len(trim),
        "candidate_fourth_vertices": len(candidates),
        "orbit_count": len(EXPECTED),
        "reduction": (
            "If a connected component containing the normalized triangle has more than three vertices, "
            "the first outside vertex on a path from the triangle is distance 6 from one triangle vertex. "
            "Renormalizing that vertex to be adjacent to 0 and quotienting by the triangle stabilizer gives "
            "the 11 count tuples listed here."
        ),
        "orbits": {},
    }

    for counts in sorted(EXPECTED):
        expected = EXPECTED[counts]
        c = representative(counts)
        assert c == expected["representative"]
        vertices = branch_vertices(trim, c)
        edges = branch_edges(vertices)
        incompatible = sum(1 for u, v in combinations(vertices, 2) if dist(u, v) > K)
        digest = edge_hash(edges)
        assert len(vertices) == expected["vertices"]
        assert len(edges) == expected["edges"]
        assert incompatible == expected["incompatible_pairs"]
        assert digest == expected["edge_sha256"]
        assert observed_orbits[counts] == expected["orbit_size"]

        orbit = tuple_id(counts)
        entry: dict[str, object] = {
            "counts": list(counts),
            "representative_C": c,
            "orbit_size": observed_orbits[counts],
            "vertices": len(vertices),
            "distance_6_edges": len(edges),
            "remaining_pairs_above_diameter": incompatible,
            "edge_sha256": digest,
            "status": "colorability unresolved",
        }
        if args.emit_cnf:
            cnf = emit_cnf(args.out, orbit, vertices, edges)
            assert cnf["variables"] == expected["variables"]
            assert cnf["clauses"] == expected["clauses"]
            assert cnf["fixed_clique_vertices"] == expected["fixed_clique"]
            assert cnf["cnf_sha256"] == expected["cnf_sha256"]
            entry["cnf"] = cnf
        report["orbits"][orbit] = entry

    report_path = args.out / "triangle_refinement_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
