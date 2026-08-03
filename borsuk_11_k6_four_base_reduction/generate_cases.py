#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import math
from collections import defaultdict, deque
from io import StringIO
from pathlib import Path
from typing import Callable

N = 11
K = 6
A = (1 << 6) - 1
B_CASES = {
    "a1b1": 65,
    "a2b0": 3,
    "a2b2": 195,
    "a3b1": 71,
    "a3b3": 455,
}
EXPECTED_POINTWISE = {"a1b1": 24, "a2b0": 19, "a2b2": 36, "a3b1": 35, "a3b3": 35}
EXPECTED_SETWISE = {"a1b1": 19, "a2b0": 19, "a2b2": 26, "a3b1": 23, "a3b3": 14}
EXPECTED_CSV_SHA256 = "e60f5f81120e42c8c7eae2da299105e802266f6e92629cd6ac6ee24bcef9db19"


def distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def allowed(mask: int, bases: tuple[int, ...]) -> bool:
    return mask.bit_count() % 2 == 0 and all(distance(mask, base) <= K for base in bases)


def blocks_for(b: int) -> tuple[tuple[tuple[int, int], tuple[int, ...]], ...]:
    blocks: dict[tuple[int, int], list[int]] = defaultdict(list)
    for coordinate in range(N):
        blocks[((A >> coordinate) & 1, (b >> coordinate) & 1)].append(coordinate)
    return tuple((signature, tuple(positions)) for signature, positions in sorted(blocks.items()))


def key_for(mask: int, blocks: tuple[tuple[tuple[int, int], tuple[int, ...]], ...]) -> tuple[int, ...]:
    return tuple(sum((mask >> coordinate) & 1 for coordinate in positions) for _, positions in blocks)


def representative(key: tuple[int, ...], blocks: tuple[tuple[tuple[int, int], tuple[int, ...]], ...]) -> int:
    mask = 0
    for count, (_, positions) in zip(key, blocks):
        for coordinate in positions[:count]:
            mask |= 1 << coordinate
    return mask


def orbit_size(key: tuple[int, ...], blocks: tuple[tuple[tuple[int, int], tuple[int, ...]], ...]) -> int:
    size = 1
    for count, (_, positions) in zip(key, blocks):
        size *= math.comb(len(positions), count)
    return size


def make_isometry(b: int, sigma: tuple[int, int, int]) -> Callable[[int], int] | None:
    base = (0, A, b)
    translation = base[sigma[0]]
    source: dict[tuple[int, int], list[int]] = defaultdict(list)
    target: dict[tuple[int, int], list[int]] = defaultdict(list)

    for coordinate in range(N):
        source[((A >> coordinate) & 1, (b >> coordinate) & 1)].append(coordinate)
    for coordinate in range(N):
        signature = (
            ((base[sigma[1]] >> coordinate) & 1) ^ ((translation >> coordinate) & 1),
            ((base[sigma[2]] >> coordinate) & 1) ^ ((translation >> coordinate) & 1),
        )
        target[signature].append(coordinate)

    if {key: len(value) for key, value in source.items()} != {
        key: len(value) for key, value in target.items()
    }:
        return None

    coordinate_map: dict[int, int] = {}
    for signature, source_positions in source.items():
        for old, new in zip(source_positions, target[signature]):
            coordinate_map[old] = new

    def transform(mask: int) -> int:
        image = translation
        for old, new in coordinate_map.items():
            if (mask >> old) & 1:
                image ^= 1 << new
        return image

    assert tuple(transform(point) for point in base) == tuple(base[sigma[index]] for index in range(3))
    return transform


def vertex_hash(vertices: list[int]) -> str:
    serialized = "".join(f"{vertex:03x}\n" for vertex in vertices).encode("ascii")
    return hashlib.sha256(serialized).hexdigest()


def trim_stats(base: tuple[int, int, int, int]) -> dict[str, int | str]:
    vertices = [mask for mask in range(1 << N) if allowed(mask, base)]
    exact_edges = 0
    incompatible_pairs = 0
    for index, left in enumerate(vertices):
        for right in vertices[index + 1 :]:
            d = distance(left, right)
            if d == K:
                exact_edges += 1
            elif d > K:
                incompatible_pairs += 1
    return {
        "vertices": len(vertices),
        "exact_distance_edges": exact_edges,
        "incompatible_pairs": incompatible_pairs,
        "vertex_sha256": vertex_hash(vertices),
    }


def generate() -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    cases: list[dict[str, object]] = []
    family_summary: dict[str, dict[str, object]] = {}

    for family, b in B_CASES.items():
        base3 = (0, A, b)
        blocks = blocks_for(b)
        grouped_keys: dict[tuple[int, ...], list[int]] = defaultdict(list)
        for c in range(1 << N):
            if c in base3:
                continue
            if allowed(c, base3):
                grouped_keys[key_for(c, blocks)].append(c)

        if len(grouped_keys) != EXPECTED_POINTWISE[family]:
            raise SystemExit(f"{family}: pointwise orbit count mismatch")
        for key, members in grouped_keys.items():
            if orbit_size(key, blocks) != len(members):
                raise SystemExit(f"{family}: orbit-size mismatch for {key}")

        isometries: list[Callable[[int], int]] = []
        for sigma in itertools.permutations(range(3)):
            if all(
                distance(base3[left], base3[right])
                == distance(base3[sigma[left]], base3[sigma[right]])
                for left in range(3)
                for right in range(3)
            ):
                transform = make_isometry(b, sigma)
                if transform is None:
                    raise SystemExit(f"{family}: missing base isometry for {sigma}")
                isometries.append(transform)

        unseen = set(grouped_keys)
        family_cases = 0
        while unseen:
            seed = min(unseen)
            orbit = {seed}
            queue = deque([seed])
            while queue:
                key = queue.popleft()
                c = representative(key, blocks)
                for transform in isometries:
                    image_key = key_for(transform(c), blocks)
                    if image_key not in grouped_keys:
                        raise SystemExit(f"{family}: setwise orbit escaped pointwise keys")
                    if image_key not in orbit:
                        orbit.add(image_key)
                        queue.append(image_key)
            unseen -= orbit

            c = representative(min(orbit), blocks)
            record: dict[str, object] = {
                "id": f"{family}_{family_cases:02d}",
                "family": family,
                "B": b,
                "C": c,
            }
            record.update(trim_stats((0, A, b, c)))
            cases.append(record)
            family_cases += 1

        if family_cases != EXPECTED_SETWISE[family]:
            raise SystemExit(f"{family}: setwise orbit count mismatch")
        family_summary[family] = {
            "pointwise_orbits": len(grouped_keys),
            "setwise_orbits": family_cases,
        }

    if len(cases) != 101:
        raise SystemExit(f"expected 101 cases, got {len(cases)}")
    return cases, family_summary


def render_csv(cases: list[dict[str, object]]) -> str:
    fields = [
        "id",
        "family",
        "B",
        "C",
        "vertices",
        "exact_distance_edges",
        "incompatible_pairs",
        "vertex_sha256",
    ]
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(cases)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    cases, summary = generate()
    text = render_csv(cases)
    digest = hashlib.sha256(text.encode("ascii")).hexdigest()
    if digest != EXPECTED_CSV_SHA256:
        raise SystemExit(f"case-list hash mismatch: {digest}")
    if args.output:
        args.output.write_text(text, encoding="ascii", newline="")

    sizes = [int(case["vertices"]) for case in cases]
    print(
        f"PASS pointwise={sum(v['pointwise_orbits'] for v in summary.values())} "
        f"setwise={len(cases)} trim_range={min(sizes)}-{max(sizes)} "
        f"csv_sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
