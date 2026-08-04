#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

N = 11
A = (1 << 6) - 1
EXPECTED = {
    "vertex_count": 692,
    "g6_edge_count": 104606,
    "incompatibility_edge_count": 37470,
    "vertex_sha256": "ece78553536e8cbac3404fb77db0096352024b1dbf15ea4f129d782a1755590d",
    "g6_edge_sha256": "28aeb05060799feae42e3af33d51a66f852f0e6308cb737f0326bcda0af17c3f",
    "incompatibility_edge_sha256": "cc2059f512d2210f1c654c0ae7cbc1f00db22e29cc7fa6d1279e6b77a2f68828",
}


def weight(mask: int) -> int:
    return mask.bit_count()


def distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def root_vertices() -> list[int]:
    return [
        mask
        for mask in range(1 << N)
        if weight(mask) % 2 == 0
        and weight(mask) <= 6
        and distance(mask, A) <= 6
    ]


def relations(vertices: list[int]) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    exact: list[tuple[int, int]] = []
    incompatible: list[tuple[int, int]] = []
    for index, left in enumerate(vertices):
        for right in vertices[index + 1 :]:
            d = distance(left, right)
            if d == 6:
                exact.append((left, right))
            elif d > 6:
                incompatible.append((left, right))
    return exact, incompatible


def serialize_vertices(vertices: list[int]) -> bytes:
    return "".join(f"{mask:03x}\n" for mask in vertices).encode("ascii")


def serialize_edges(edges: list[tuple[int, int]]) -> bytes:
    return "".join(f"{left:03x},{right:03x}\n" for left, right in edges).encode("ascii")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def orbit_key(mask: int) -> tuple[int, int]:
    inside = weight(mask & A)
    outside = weight(mask >> 6)
    return min(inside, 6 - inside), outside


def build_report() -> dict[str, object]:
    vertices = root_vertices()
    exact, incompatible = relations(vertices)
    orbit_sizes = Counter(orbit_key(mask) for mask in vertices)
    first_incompatibility = incompatible[0]
    report: dict[str, object] = {
        "dimension": N,
        "fixed_neighbor_hex": f"{A:03x}",
        "vertex_count": len(vertices),
        "g6_edge_count": len(exact),
        "incompatibility_edge_count": len(incompatible),
        "vertex_sha256": sha256(serialize_vertices(vertices)),
        "g6_edge_sha256": sha256(serialize_edges(exact)),
        "incompatibility_edge_sha256": sha256(serialize_edges(incompatible)),
        "base_stabilizer_vertex_orbits": [
            {"key": [inside, outside], "size": size}
            for (inside, outside), size in sorted(orbit_sizes.items())
        ],
        "first_incompatibility_edge": {
            "left": f"{first_incompatibility[0]:03x}",
            "right": f"{first_incompatibility[1]:03x}",
            "distance": distance(*first_incompatibility),
        },
    }
    return report


def verify_expected(report: dict[str, object]) -> None:
    for field, expected in EXPECTED.items():
        actual = report[field]
        if actual != expected:
            raise SystemExit(f"{field}: expected {expected!r}, got {actual!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", type=Path)
    args = parser.parse_args()

    report = build_report()
    verify_expected(report)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.write_report:
        args.write_report.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
