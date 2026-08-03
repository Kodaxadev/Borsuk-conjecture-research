#!/usr/bin/env python3
"""Enumerate the exact three-branch reduction for Borsuk(11,6).

Only the Python standard library is used. The script reconstructs the one-base
trim, verifies the second-neighbor orbit classification by exhaustive
enumeration, and optionally emits symmetry-broken 12-coloring CNFs for the
three branches.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

N = 11
K = 6
COLORS = 12
A = (1 << 6) - 1  # {0,1,2,3,4,5}
HADAMARD_CLIQUE = [
    0, 63, 455, 748, 858, 945,
    1241, 1396, 1450, 1635, 1686, 1805,
]
REPRESENTATIVES = {
    3: 455,  # |A cap B|=3, d(A,B)=6
    4: 207,  # |A cap B|=4, d(A,B)=4
    5: 95,   # |A cap B|=5, d(A,B)=2
}
EXPECTED = {
    3: (
        555,
        65886,
        "19ec780b918ed24ecf8dce6d1466fcdde8e2d50315bf9d6a45b833472c365773",
    ),
    4: (
        582,
        72827,
        "95d56552d5578b04f2c0d7732d32c4942c3d7415ba6d4ea805b797733a411e37",
    ),
    5: (
        618,
        82598,
        "704681db24c6cd26e75df6aa29cc8603ad47bb6580489f6468a0be00441caeaf",
    ),
}


def wt(x: int) -> int:
    return x.bit_count()


def dist(x: int, y: int) -> int:
    return (x ^ y).bit_count()


def trim_vertices() -> list[int]:
    return [
        x
        for x in range(1 << N)
        if wt(x) % 2 == 0 and wt(x) <= K and dist(x, A) <= K
    ]


def branch_vertices(trim: list[int], b: int) -> list[int]:
    return [x for x in trim if dist(x, b) <= K]


def branch_edges(vertices: list[int]) -> list[tuple[int, int]]:
    return [
        (u, v)
        for u, v in combinations(vertices, 2)
        if dist(u, v) == K
    ]


def edge_hash(edges: list[tuple[int, int]]) -> str:
    payload = "".join(f"{u},{v}\n" for u, v in edges).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def classify_second_neighbors(trim: list[int]) -> dict[int, list[int]]:
    """Classify B with d(0,B)=6, B!=A, and d(A,B)<=6.

    The pointwise stabilizer of 0 and A is S_6 x S_5, so the orbit is
    determined by |A cap B|. Since |A|=|B|=6 and d(A,B)<=6, the only values
    are 3, 4, and 5; value 6 is B=A.
    """
    classes: dict[int, list[int]] = {3: [], 4: [], 5: []}
    for b in trim:
        if b == A or wt(b) != K:
            continue
        overlap = wt(b & A)
        assert overlap in classes
        classes[overlap].append(b)
    return classes


def fixed_clique(vertices: list[int]) -> dict[int, int]:
    present = set(vertices)
    return {
        h: color
        for color, h in enumerate(HADAMARD_CLIQUE)
        if h in present
    }


def color_domains(
    vertices: list[int], fixed: dict[int, int]
) -> dict[int, list[int]]:
    domains: dict[int, list[int]] = {}
    for v in vertices:
        if v in fixed:
            domains[v] = [fixed[v]]
            continue
        forbidden = {
            color for h, color in fixed.items() if dist(v, h) == K
        }
        domains[v] = [c for c in range(COLORS) if c not in forbidden]
        assert domains[v]
    return domains


def emit_cnf(
    out_dir: Path,
    overlap: int,
    vertices: list[int],
    edges: list[tuple[int, int]],
) -> dict[str, object]:
    fixed = fixed_clique(vertices)
    domains = color_domains(vertices, fixed)
    variable: dict[tuple[int, int], int] = {}
    reverse: list[tuple[int, int]] = []
    for v in vertices:
        for c in domains[v]:
            variable[(v, c)] = len(reverse) + 1
            reverse.append((v, c))

    clauses: list[list[int]] = []
    for v in vertices:
        ids = [variable[(v, c)] for c in domains[v]]
        clauses.append(ids)
        for a, b in combinations(ids, 2):
            clauses.append([-a, -b])

    for u, v in edges:
        shared = set(domains[u]).intersection(domains[v])
        for c in sorted(shared):
            clauses.append([-variable[(u, c)], -variable[(v, c)]])

    stem = f"k6_second_base_overlap_{overlap}"
    cnf_path = out_dir / f"{stem}.cnf"
    map_path = out_dir / f"{stem}_variables.json"
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
        "cnf": cnf_path.name,
        "variable_map": map_path.name,
        "domain_size_distribution": dict(
            sorted(Counter(map(len, domains.values())).items())
        ),
        "fixed_clique_vertices": len(fixed),
        "cnf_sha256": hashlib.sha256(cnf_path.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out", type=Path, default=Path("generated_second_base")
    )
    parser.add_argument("--emit-cnf", action="store_true")
    args = parser.parse_args()

    trim = trim_vertices()
    assert len(trim) == 692
    classes = classify_second_neighbors(trim)
    assert {o: len(vs) for o, vs in classes.items()} == {
        3: 200,
        4: 150,
        5: 30,
    }

    args.out.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "n": N,
        "diameter": K,
        "colors": COLORS,
        "base_A": A,
        "trim_vertices": len(trim),
        "reduction": (
            "Every connected component with at least three vertices has, "
            "after swapping 0 and A if needed, a third vertex B adjacent "
            "to 0. Up to S_6 x S_5, B is determined by |A cap B| in "
            "{3,4,5}."
        ),
        "branches": {},
    }

    for overlap in (3, 4, 5):
        b = REPRESENTATIVES[overlap]
        assert b in classes[overlap]
        vertices = branch_vertices(trim, b)
        edges = branch_edges(vertices)
        digest = edge_hash(edges)
        expected_v, expected_e, expected_h = EXPECTED[overlap]
        assert (len(vertices), len(edges), digest) == (
            expected_v,
            expected_e,
            expected_h,
        )
        incompatible = sum(
            1 for u, v in combinations(vertices, 2) if dist(u, v) > K
        )
        entry: dict[str, object] = {
            "overlap": overlap,
            "representative_B": b,
            "orbit_size": len(classes[overlap]),
            "distance_A_B": dist(A, b),
            "vertices": len(vertices),
            "distance_6_edges": len(edges),
            "remaining_pairs_above_diameter": incompatible,
            "edge_sha256": digest,
            "hadamard_clique_vertices_present": len(
                fixed_clique(vertices)
            ),
            "status": "colorability unresolved",
        }
        if args.emit_cnf:
            entry["cnf"] = emit_cnf(
                args.out, overlap, vertices, edges
            )
        report["branches"][str(overlap)] = entry

    report_path = args.out / "second_base_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
