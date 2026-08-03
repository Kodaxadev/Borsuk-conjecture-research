#!/usr/bin/env python3
"""Verifier 1: generate distance-8 neighbors by XOR masks."""
from __future__ import annotations
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
N = 11
K = 8

def popcount(x: int) -> int:
    return x.bit_count()

def vertices() -> list[int]:
    return [x for x in range(1 << N) if popcount(x) % 2 == 0 and popcount(x) <= K]

def masks_of_weight(k: int) -> list[int]:
    return [sum(1 << i for i in c) for c in itertools.combinations(range(N), k)]

def main() -> None:
    witness = json.loads((ROOT / "witness.json").read_text())
    expected = witness["expected"]
    colors = {int(v): c for v, c in witness["colors"].items()}

    verts = vertices()
    vset = set(verts)
    assert len(verts) == 1013, len(verts)
    assert set(colors) == vset, "Witness does not cover exactly the canonical vertex set"
    assert all(isinstance(c, int) and 0 <= c < 12 for c in colors.values())
    assert len(set(colors.values())) <= 12

    edges: list[tuple[int, int]] = []
    bad: list[tuple[int, int, int]] = []
    for a in verts:
        for mask in masks_of_weight(K):
            b = a ^ mask
            if b in vset and a < b:
                edges.append((a, b))
                if colors[a] == colors[b]:
                    bad.append((a, b, colors[a]))

    edges.sort()
    assert len(edges) == len(set(edges)), "Duplicate edge generation"
    assert len(edges) == 82665, len(edges)
    digest = hashlib.sha256(
        "".join(f"{a},{b}\n" for a, b in edges).encode("utf-8")
    ).hexdigest()
    assert digest == expected["graph_sha256"], (digest, expected["graph_sha256"])
    assert not bad, f"Monochromatic edges: {bad[:10]}"

    # Independent-within-this-script certificate check: scan every pair in
    # every color class, not the generated edge list.
    classes: dict[int, list[int]] = {}
    for v, c in colors.items():
        classes.setdefault(c, []).append(v)
    for c, cls in classes.items():
        for i, a in enumerate(cls):
            for b in cls[i + 1:]:
                assert popcount(a ^ b) != K, (c, a, b)

    print(json.dumps({
        "status": "PASS",
        "dimension": N,
        "diameter": K,
        "vertices": len(verts),
        "edges": len(edges),
        "colors_used": len(set(colors.values())),
        "monochromatic_edges": 0,
        "graph_sha256": digest,
        "method": "XOR masks plus color-class pair scan"
    }, indent=2))

if __name__ == "__main__":
    main()
