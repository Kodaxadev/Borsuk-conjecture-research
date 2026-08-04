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
B_CASES = {"a1b1": 65, "a2b0": 3, "a2b2": 195, "a3b1": 71, "a3b3": 455}
EXPECTED_POINTWISE = {"a1b1": 24, "a2b0": 19, "a2b2": 36, "a3b1": 35, "a3b3": 35}
EXPECTED_SETWISE = {"a1b1": 19, "a2b0": 19, "a2b2": 26, "a3b1": 23, "a3b3": 14}
EXPECTED_RAW_CSV_SHA256 = "e60f5f81120e42c8c7eae2da299105e802266f6e92629cd6ac6ee24bcef9db19"
EXPECTED_CANONICAL_CSV_SHA256 = "08913feaddbc0f930b6ef90a1677fbc4577cb23dcb6f4dac8987e37056d34742"


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
    if {key: len(value) for key, value in source.items()} != {key: len(value) for key, value in target.items()}:
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

    return transform


def vertex_hash(vertices: list[int]) -> str:
    return hashlib.sha256("".join(f"{vertex:03x}\n" for vertex in vertices).encode("ascii")).hexdigest()


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


def generate_raw_cases() -> tuple[list[dict[str, object]], dict[str, dict[str, int]]]:
    cases: list[dict[str, object]] = []
    family_summary: dict[str, dict[str, int]] = {}
    for family, b in B_CASES.items():
        base3 = (0, A, b)
        blocks = blocks_for(b)
        grouped_keys: dict[tuple[int, ...], list[int]] = defaultdict(list)
        for c in range(1 << N):
            if c not in base3 and allowed(c, base3):
                grouped_keys[key_for(c, blocks)].append(c)
        if len(grouped_keys) != EXPECTED_POINTWISE[family]:
            raise SystemExit(f"{family}: pointwise orbit count mismatch")
        for key, members in grouped_keys.items():
            if orbit_size(key, blocks) != len(members):
                raise SystemExit(f"{family}: orbit-size mismatch for {key}")

        isometries: list[Callable[[int], int]] = []
        for sigma in itertools.permutations(range(3)):
            if all(distance(base3[i], base3[j]) == distance(base3[sigma[i]], base3[sigma[j]]) for i in range(3) for j in range(3)):
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
                        raise SystemExit(f"{family}: setwise orbit escaped")
                    if image_key not in orbit:
                        orbit.add(image_key)
                        queue.append(image_key)
            unseen -= orbit
            c = representative(min(orbit), blocks)
            record: dict[str, object] = {"id": f"{family}_{family_cases:02d}", "family": family, "B": b, "C": c}
            record.update(trim_stats((0, A, b, c)))
            cases.append(record)
            family_cases += 1
        if family_cases != EXPECTED_SETWISE[family]:
            raise SystemExit(f"{family}: setwise orbit count mismatch")
        family_summary[family] = {"pointwise_orbits": len(grouped_keys), "setwise_orbits": family_cases}
    if len(cases) != 101:
        raise SystemExit(f"expected 101 intermediate cases, got {len(cases)}")
    return cases, family_summary


def canonical_base_signature(points: tuple[int, int, int, int]) -> tuple[int, ...]:
    best: tuple[int, ...] | None = None
    for origin_index, origin in enumerate(points):
        translated = [points[index] ^ origin for index in range(4) if index != origin_index]
        for permutation in itertools.permutations(translated):
            counts = [0] * 8
            for coordinate in range(N):
                signature = sum(((permutation[index] >> coordinate) & 1) << index for index in range(3))
                counts[signature] += 1
            candidate = tuple(counts)
            if best is None or candidate < best:
                best = candidate
    assert best is not None
    return best


def canonical_classes(cases: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[int, ...], list[dict[str, object]]] = defaultdict(list)
    for case in cases:
        signature = canonical_base_signature((0, A, int(case["B"]), int(case["C"])))
        grouped[signature].append(case)

    output: list[dict[str, object]] = []
    for index, (signature, members) in enumerate(sorted(grouped.items())):
        members.sort(key=lambda case: str(case["id"]))
        stats = {(m["vertices"], m["exact_distance_edges"], m["incompatible_pairs"]) for m in members}
        if len(stats) != 1:
            raise SystemExit("isometric base classes produced inconsistent trim statistics")
        representative_case = members[0]
        output.append({
            "id": f"q{index:02d}",
            "representative_case": representative_case["id"],
            "members": ";".join(str(member["id"]) for member in members),
            "member_count": len(members),
            "B": representative_case["B"],
            "C": representative_case["C"],
            "vertices": representative_case["vertices"],
            "exact_distance_edges": representative_case["exact_distance_edges"],
            "incompatible_pairs": representative_case["incompatible_pairs"],
            "vertex_sha256": representative_case["vertex_sha256"],
            "base_signature": "-".join(map(str, signature)),
        })
    if len(output) != 58 or sum(int(row["member_count"]) for row in output) != 101:
        raise SystemExit("full four-base canonicalization count mismatch")
    return output


def render_csv(rows: list[dict[str, object]], fields: list[str]) -> str:
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="write the 58 canonical trim classes")
    parser.add_argument("--raw-output", type=Path, help="write the 101 intermediate triple-stabilizer cases")
    args = parser.parse_args()

    raw_cases, summary = generate_raw_cases()
    raw_fields = ["id", "family", "B", "C", "vertices", "exact_distance_edges", "incompatible_pairs", "vertex_sha256"]
    raw_csv = render_csv(raw_cases, raw_fields)
    raw_hash = hashlib.sha256(raw_csv.encode("ascii")).hexdigest()
    if raw_hash != EXPECTED_RAW_CSV_SHA256:
        raise SystemExit(f"intermediate case-list hash mismatch: {raw_hash}")

    classes = canonical_classes(raw_cases)
    canonical_fields = ["id", "representative_case", "members", "member_count", "B", "C", "vertices", "exact_distance_edges", "incompatible_pairs", "vertex_sha256", "base_signature"]
    canonical_csv = render_csv(classes, canonical_fields)
    canonical_hash = hashlib.sha256(canonical_csv.encode("ascii")).hexdigest()
    if canonical_hash != EXPECTED_CANONICAL_CSV_SHA256:
        raise SystemExit(f"canonical case-list hash mismatch: {canonical_hash}")

    if args.raw_output:
        args.raw_output.write_text(raw_csv, encoding="ascii", newline="")
    if args.output:
        args.output.write_text(canonical_csv, encoding="ascii", newline="")

    sizes = [int(row["vertices"]) for row in classes]
    print(
        f"PASS pointwise={sum(v['pointwise_orbits'] for v in summary.values())} "
        f"intermediate={len(raw_cases)} canonical={len(classes)} "
        f"trim_range={min(sizes)}-{max(sizes)} csv_sha256={canonical_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
