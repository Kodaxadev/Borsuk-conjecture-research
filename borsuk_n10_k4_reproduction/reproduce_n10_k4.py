#!/usr/bin/env python3
"""
Independent reconstruction of Proposition 7's three n=10, k=4 cover graphs
from Batmanov--Voronov (arXiv:2504.01233v1).

This script uses only Python's standard library. It:
  1. reconstructs the three cover vertex sets from the paper,
  2. constructs their exact-Hamming-distance-4 graphs,
  3. finds a deterministic DSATUR coloring,
  4. independently verifies every edge is properly colored,
  5. writes a machine-readable report with canonical graph hashes.

It proves only the coloring upper bounds for the three stated cover graphs.
It does not by itself verify Proposition 6 (that the three sets cover every
diameter-4 subset up to cube isometry).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

N = 10
K = 4


def bits(s: str) -> int:
    if len(s) != N or any(c not in "01" for c in s):
        raise ValueError(f"Expected a {N}-bit string, got {s!r}")
    return int(s, 2)


def bitstring(x: int) -> str:
    return format(x, f"0{N}b")


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def trim(centers: Iterable[int], radius: int) -> List[int]:
    cs = tuple(centers)
    return [
        x for x in range(1 << N)
        if all(hamming(x, c) <= radius for c in cs)
    ]


def build_graph(vertices: Iterable[int], distance: int) -> Dict[int, Set[int]]:
    verts = sorted(set(vertices))
    adj: Dict[int, Set[int]] = {v: set() for v in verts}
    for i, u in enumerate(verts):
        for v in verts[i + 1:]:
            if hamming(u, v) == distance:
                adj[u].add(v)
                adj[v].add(u)
    return adj


def deterministic_dsatur(adj: Dict[int, Set[int]]) -> Dict[int, int]:
    """Greedy DSATUR with explicit deterministic tie-breaking."""
    colors: Dict[int, int] = {}
    uncolored = set(adj)

    while uncolored:
        def key(v: int) -> Tuple[int, int, int]:
            neighbor_colors = {colors[u] for u in adj[v] if u in colors}
            # Highest saturation, then degree, then smallest integer vertex.
            return (len(neighbor_colors), len(adj[v]), -v)

        v = max(uncolored, key=key)
        forbidden = {colors[u] for u in adj[v] if u in colors}
        color = 0
        while color in forbidden:
            color += 1
        colors[v] = color
        uncolored.remove(v)

    return colors


def canonical_edges(adj: Dict[int, Set[int]]) -> List[Tuple[int, int]]:
    return [
        (u, v)
        for u in sorted(adj)
        for v in sorted(adj[u])
        if u < v
    ]


def graph_sha256(adj: Dict[int, Set[int]]) -> str:
    payload = "".join(
        f"{bitstring(u)} {bitstring(v)}\n"
        for u, v in canonical_edges(adj)
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def verify(adj: Dict[int, Set[int]], colors: Dict[int, int]) -> None:
    if set(colors) != set(adj):
        raise AssertionError("Coloring does not assign exactly one color to every vertex")
    for u, v in canonical_edges(adj):
        if colors[u] == colors[v]:
            raise AssertionError(
                f"Invalid coloring: {bitstring(u)} and {bitstring(v)} "
                f"share color {colors[u]}"
            )


def make_covers() -> Dict[str, List[int]]:
    zero = bits("0000000000")
    u1 = bits("0000001111")
    u2 = bits("0000110011")
    v = [
        bits("0000010111"),
        bits("0000100111"),
        bits("0001000111"),
        bits("0010000111"),
        bits("0100000111"),
        bits("1000000111"),
    ]
    w1 = bits("0000011011")
    w2 = bits("0000011101")
    w3 = bits("0000011110")

    U1 = {zero, u1, u2}
    U2 = {zero, u1, *v}
    U3 = {zero, u1, v[0], w1, w2, w3}
    W = set(trim({zero}, 2))

    return {
        "Trim_10_4(U1)": sorted(trim(U1, 4)),
        "U2_union_W": sorted(U2 | W),
        "U3_union_W": sorted(U3 | W),
    }


def main() -> None:
    report = {
        "claim": "Each stated n=10,k=4 cover graph is colorable with at most 11 colors.",
        "scope_warning": (
            "This independently verifies the graph-coloring part of Proposition 7, "
            "not the covering-system proof in Proposition 6."
        ),
        "n": N,
        "distance": K,
        "covers": {},
    }

    for name, vertices in make_covers().items():
        adj = build_graph(vertices, K)
        colors = deterministic_dsatur(adj)
        verify(adj, colors)
        edges = canonical_edges(adj)
        color_count = 1 + max(colors.values(), default=-1)
        if color_count > 11:
            raise AssertionError(f"{name} used {color_count} colors, exceeding 11")

        report["covers"][name] = {
            "vertex_count": len(vertices),
            "edge_count": len(edges),
            "color_count_found": color_count,
            "graph_edge_list_sha256": graph_sha256(adj),
            "vertices": [bitstring(v) for v in vertices],
            "coloring": {
                bitstring(v): colors[v]
                for v in sorted(colors)
            },
        }

    output = Path(__file__).with_name("n10_k4_report.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for name, data in report["covers"].items():
        print(
            f"{name}: {data['vertex_count']} vertices, "
            f"{data['edge_count']} edges, "
            f"{data['color_count_found']} colors, VERIFIED"
        )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
