#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from collections import Counter, defaultdict
from io import StringIO
from pathlib import Path
from typing import Callable

N = 11
K = 6
BASE = (0, 63, 455, 1611)
EXPECTED_STABILIZER_ORDER = 384
EXPECTED_ORBITS = 12
EXPECTED_CSV_SHA256 = "01b3ee2e629788037f1ccd6906140302abddd1ae1c077aa8cf7e8f619adb807a"
FIELDS = [
    "id",
    "D",
    "orbit_size",
    "weight",
    "distances_to_q00_base",
    "vertices",
    "exact_distance_edges",
    "incompatible_pairs",
    "vertex_sha256",
    "base5_signature",
]


def distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def allowed(mask: int, bases: tuple[int, ...]) -> bool:
    return mask.bit_count() % 2 == 0 and all(distance(mask, base) <= K for base in bases)


def point_signatures(points: tuple[int, ...]) -> list[tuple[int, ...]]:
    origin = points[0]
    return [
        tuple(((points[index] ^ origin) >> coordinate) & 1 for index in range(1, len(points)))
        for coordinate in range(N)
    ]


def stabilizer_transforms() -> list[Callable[[int], int]]:
    source_signatures = point_signatures(BASE)
    source_blocks: dict[tuple[int, ...], list[int]] = defaultdict(list)
    for coordinate, signature in enumerate(source_signatures):
        source_blocks[signature].append(coordinate)

    transforms: list[Callable[[int], int]] = []
    for sigma in itertools.permutations(range(len(BASE))):
        target = tuple(BASE[sigma[index]] for index in range(len(BASE)))
        target_signatures = point_signatures(target)
        if Counter(source_signatures) != Counter(target_signatures):
            continue
        target_blocks: dict[tuple[int, ...], list[int]] = defaultdict(list)
        for coordinate, signature in enumerate(target_signatures):
            target_blocks[signature].append(coordinate)

        keys = sorted(source_blocks)
        choices = [list(itertools.permutations(target_blocks[key])) for key in keys]
        for selections in itertools.product(*choices):
            coordinate_map: dict[int, int] = {}
            for key, targets in zip(keys, selections):
                for old, new in zip(source_blocks[key], targets):
                    coordinate_map[old] = new
            translation = BASE[sigma[0]]

            def transform(
                mask: int,
                coordinate_map: dict[int, int] = coordinate_map,
                translation: int = translation,
            ) -> int:
                image = translation
                for old, new in coordinate_map.items():
                    if (mask >> old) & 1:
                        image ^= 1 << new
                return image

            if tuple(transform(BASE[index]) for index in range(len(BASE))) != target:
                raise SystemExit("constructed map does not realize requested base permutation")
            transforms.append(transform)

    unique: dict[tuple[int, ...], Callable[[int], int]] = {}
    for transform in transforms:
        key = (transform(0),) + tuple(transform(1 << coordinate) for coordinate in range(N))
        unique[key] = transform
    output = list(unique.values())
    if len(output) != EXPECTED_STABILIZER_ORDER:
        raise SystemExit(f"expected stabilizer order {EXPECTED_STABILIZER_ORDER}, got {len(output)}")
    return output


def canonical_point_signature(points: tuple[int, ...]) -> tuple[int, ...]:
    best: tuple[int, ...] | None = None
    for origin_index, origin in enumerate(points):
        translated = [points[index] ^ origin for index in range(len(points)) if index != origin_index]
        for permutation in itertools.permutations(translated):
            counts = [0] * (1 << (len(points) - 1))
            for coordinate in range(N):
                signature = sum(
                    (((permutation[index] >> coordinate) & 1) << index)
                    for index in range(len(permutation))
                )
                counts[signature] += 1
            candidate = tuple(counts)
            if best is None or candidate < best:
                best = candidate
    if best is None:
        raise SystemExit("failed to canonicalize points")
    return best


def vertex_hash(vertices: list[int]) -> str:
    payload = "".join(f"{vertex:03x}\n" for vertex in vertices).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def trim_stats(d: int) -> dict[str, int | str]:
    vertices = [mask for mask in range(1 << N) if allowed(mask, BASE + (d,))]
    exact_edges = 0
    incompatible_pairs = 0
    for index, left in enumerate(vertices):
        for right in vertices[index + 1 :]:
            separation = distance(left, right)
            if separation == K:
                exact_edges += 1
            elif separation > K:
                incompatible_pairs += 1
    return {
        "vertices": len(vertices),
        "exact_distance_edges": exact_edges,
        "incompatible_pairs": incompatible_pairs,
        "vertex_sha256": vertex_hash(vertices),
    }


def generate_rows() -> tuple[list[dict[str, object]], dict[str, object]]:
    transforms = stabilizer_transforms()
    parent_vertices = [mask for mask in range(1 << N) if allowed(mask, BASE)]
    parent_set = set(parent_vertices)
    candidates = parent_set - set(BASE)
    if len(parent_vertices) != 436 or len(candidates) != 432:
        raise SystemExit("q00 parent size mismatch")
    if any({transform(vertex) for vertex in parent_vertices} != parent_set for transform in transforms):
        raise SystemExit("stabilizer does not preserve q00 trim")

    unseen = set(candidates)
    orbits: list[list[int]] = []
    while unseen:
        seed = min(unseen)
        orbit = sorted({transform(seed) for transform in transforms})
        if not set(orbit) <= candidates:
            raise SystemExit("candidate orbit escaped q00 trim")
        unseen -= set(orbit)
        orbits.append(orbit)
    orbits.sort(key=min)
    if len(orbits) != EXPECTED_ORBITS or sum(map(len, orbits)) != len(candidates):
        raise SystemExit("fifth-base orbit partition mismatch")

    rows: list[dict[str, object]] = []
    for index, orbit in enumerate(orbits):
        d = min(orbit)
        row: dict[str, object] = {
            "id": f"f{index:02d}",
            "D": d,
            "orbit_size": len(orbit),
            "weight": d.bit_count(),
            "distances_to_q00_base": "-".join(str(distance(d, base)) for base in BASE),
        }
        row.update(trim_stats(d))
        row["base5_signature"] = "-".join(map(str, canonical_point_signature(BASE + (d,))))
        rows.append(row)

    report: dict[str, object] = {
        "schema": "borsuk-q00-fifth-base-reduction-v1",
        "n": N,
        "diameter": K,
        "q00_base": list(BASE),
        "parent_vertices": len(parent_vertices),
        "nonbase_candidates": len(candidates),
        "stabilizer_order": len(transforms),
        "fifth_base_orbits": len(orbits),
        "orbit_size_distribution": dict(sorted(Counter(map(len, orbits)).items())),
        "child_trim_size_range": [min(int(row["vertices"]) for row in rows), max(int(row["vertices"]) for row in rows)],
        "status": "all fifth-base children UNKNOWN",
        "theorem_status_changed": False,
        "q00_case_status_changed": False,
    }
    return rows, report


def render_csv(rows: list[dict[str, object]]) -> str:
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    rows, report = generate_rows()
    csv_text = render_csv(rows)
    digest = hashlib.sha256(csv_text.encode("ascii")).hexdigest()
    if digest != EXPECTED_CSV_SHA256:
        raise SystemExit(f"fifth-base CSV hash mismatch: {digest}")
    report["canonical_csv_sha256"] = digest

    if args.output:
        args.output.write_text(csv_text, encoding="ascii", newline="")
    if args.report:
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"PASS stabilizer={report['stabilizer_order']} candidates={report['nonbase_candidates']} "
        f"orbits={report['fifth_base_orbits']} child_range={report['child_trim_size_range'][0]}-"
        f"{report['child_trim_size_range'][1]} csv_sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
