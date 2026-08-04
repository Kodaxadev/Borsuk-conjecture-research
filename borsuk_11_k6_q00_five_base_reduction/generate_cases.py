#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
from collections import defaultdict
from io import StringIO
from pathlib import Path

N = 11
K = 6
A = (1 << 6) - 1
Q00_BASE = (0, A, 455, 1611)
EXPECTED_PARENT_VERTICES = 436
EXPECTED_PARENT_EDGES = 39_600
EXPECTED_PARENT_INCOMPATIBLE = 13_104
EXPECTED_FIFTH_CANDIDATES = 432
EXPECTED_TYPES = 12
EXPECTED_CASE_CSV_SHA256 = "d5b0825cd8645af2c595b3de3c851360e0b283d8ce61383482f76168e1ae9855"
EXPECTED_ASSIGNMENT_SHA256 = "6c94923a260290d59727bdcad68293b7f1962a7c5377885dd536fefa5962ffc7"


def distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def allowed(mask: int, bases: tuple[int, ...]) -> bool:
    return mask.bit_count() % 2 == 0 and all(distance(mask, base) <= K for base in bases)


def trim_vertices(base: tuple[int, ...]) -> list[int]:
    return [mask for mask in range(1 << N) if allowed(mask, base)]


def trim_stats(base: tuple[int, ...]) -> tuple[int, int, int]:
    vertices = trim_vertices(base)
    exact_edges = 0
    incompatible_pairs = 0
    for index, left in enumerate(vertices):
        for right in vertices[index + 1 :]:
            d = distance(left, right)
            if d == K:
                exact_edges += 1
            elif d > K:
                incompatible_pairs += 1
    return len(vertices), exact_edges, incompatible_pairs


def canonical_base_signature(points: tuple[int, ...]) -> tuple[int, ...]:
    """Complete affine-cube-isometry invariant for an unordered finite base.

    Choose each point as translation origin, order the remaining points in every
    way, and record the multiplicity of every coordinate column pattern. Equal
    canonical vectors provide an explicit coordinate permutation and translation.
    """

    best: tuple[int, ...] | None = None
    for origin_index, origin in enumerate(points):
        translated = [points[index] ^ origin for index in range(len(points)) if index != origin_index]
        for permutation in itertools.permutations(translated):
            counts = [0] * (1 << (len(points) - 1))
            for coordinate in range(N):
                signature = sum(
                    ((permutation[index] >> coordinate) & 1) << index
                    for index in range(len(permutation))
                )
                counts[signature] += 1
            candidate = tuple(counts)
            if best is None or candidate < best:
                best = candidate
    assert best is not None
    return best


def render_csv(rows: list[dict[str, object]]) -> str:
    fields = [
        "id",
        "D",
        "D_hex",
        "member_count",
        "vertices",
        "exact_distance_edges",
        "incompatible_pairs",
        "base_signature",
    ]
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def generate_cases() -> tuple[list[dict[str, object]], str]:
    parent_vertices = trim_vertices(Q00_BASE)
    parent_stats = trim_stats(Q00_BASE)
    expected_parent = (
        EXPECTED_PARENT_VERTICES,
        EXPECTED_PARENT_EDGES,
        EXPECTED_PARENT_INCOMPATIBLE,
    )
    if parent_stats != expected_parent:
        raise SystemExit(f"q00 parent statistics mismatch: {parent_stats}")

    candidates = [vertex for vertex in parent_vertices if vertex not in Q00_BASE]
    if len(candidates) != EXPECTED_FIFTH_CANDIDATES:
        raise SystemExit(f"expected {EXPECTED_FIFTH_CANDIDATES} fifth vertices, got {len(candidates)}")

    grouped: dict[tuple[int, ...], list[int]] = defaultdict(list)
    for fifth in candidates:
        grouped[canonical_base_signature(Q00_BASE + (fifth,))].append(fifth)

    if len(grouped) != EXPECTED_TYPES:
        raise SystemExit(f"expected {EXPECTED_TYPES} five-base types, got {len(grouped)}")

    rows: list[dict[str, object]] = []
    assignments: list[str] = []
    for index, (signature, members) in enumerate(sorted(grouped.items())):
        members.sort()
        case_id = f"q00r{index:02d}"
        representative = members[0]
        vertices, exact_edges, incompatible_pairs = trim_stats(Q00_BASE + (representative,))
        rows.append(
            {
                "id": case_id,
                "D": representative,
                "D_hex": f"{representative:03x}",
                "member_count": len(members),
                "vertices": vertices,
                "exact_distance_edges": exact_edges,
                "incompatible_pairs": incompatible_pairs,
                "base_signature": "-".join(map(str, signature)),
            }
        )
        assignments.extend(f"{member:03x},{case_id}\n" for member in members)

    if sum(int(row["member_count"]) for row in rows) != EXPECTED_FIFTH_CANDIDATES:
        raise SystemExit("five-base type memberships do not cover all fifth vertices")

    assignment_text = "".join(assignments)
    assignment_hash = hashlib.sha256(assignment_text.encode("ascii")).hexdigest()
    if assignment_hash != EXPECTED_ASSIGNMENT_SHA256:
        raise SystemExit(f"fifth-vertex assignment hash mismatch: {assignment_hash}")
    return rows, assignment_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="write the 12 canonical five-base cases")
    parser.add_argument("--assignment-output", type=Path, help="write fifth-vertex to type assignments")
    args = parser.parse_args()

    rows, assignment_text = generate_cases()
    case_csv = render_csv(rows)
    case_hash = hashlib.sha256(case_csv.encode("ascii")).hexdigest()
    if case_hash != EXPECTED_CASE_CSV_SHA256:
        raise SystemExit(f"five-base case-list hash mismatch: {case_hash}")

    if args.output:
        args.output.write_text(case_csv, encoding="ascii", newline="")
    if args.assignment_output:
        args.assignment_output.write_text(assignment_text, encoding="ascii", newline="")

    sizes = [int(row["vertices"]) for row in rows]
    print(
        f"PASS q00_parent={EXPECTED_PARENT_VERTICES} fifth_candidates={EXPECTED_FIFTH_CANDIDATES} "
        f"canonical={len(rows)} trim_range={min(sizes)}-{max(sizes)} "
        f"csv_sha256={case_hash} assignment_sha256={EXPECTED_ASSIGNMENT_SHA256}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
