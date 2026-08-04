#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from collections import Counter, defaultdict
from itertools import permutations, product
from pathlib import Path
from typing import Iterable

N = 11
K = 6
COLORS = 12
CLAUSES_PER_VERTEX_RAW = 1 + math.comb(COLORS, 2)
CLAUSES_PER_EDGE_RAW = COLORS
CLAIM_ID = "n11-k6-q00r00-seventh-base-classification"
SOURCE_ARCHIVE_SHA256 = "a1862053e19a4341b941e62181c180805fb59a7969241d473705635dd04d0505"
SOURCE_MANIFEST_SHA256 = "559f83e4eb245902b9ec1808812248694c7931a535213c45b50d7a89a461e5fa"
SOURCE_GOVERNANCE_COMMIT = "2c7727666966fc1e0ad9657b3424e0616cab25e8"
SOURCE_STATUS_SYNC_COMMIT = "3b502090b0a0c246645b408c561c6a258ca46dbe"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def pretty_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def allowed(vertex: int, base: Iterable[int]) -> bool:
    return vertex.bit_count() % 2 == 0 and all(distance(vertex, point) <= K for point in base)


def permute_bits(vertex: int, output_to_input: tuple[int, ...]) -> int:
    result = 0
    for output_coordinate, input_coordinate in enumerate(output_to_input):
        if (vertex >> input_coordinate) & 1:
            result |= 1 << output_coordinate
    return result


def apply_transform(vertex: int, transform: tuple[int, tuple[int, ...]]) -> int:
    translation, output_to_input = transform
    return permute_bits(vertex, output_to_input) ^ translation


def compose(
    left: tuple[int, tuple[int, ...]],
    right: tuple[int, tuple[int, ...]],
) -> tuple[int, tuple[int, ...]]:
    """Return left(right(x))."""
    left_translation, left_permutation = left
    right_translation, right_permutation = right
    translation = permute_bits(right_translation, left_permutation) ^ left_translation
    permutation = tuple(right_permutation[left_permutation[index]] for index in range(N))
    return translation, permutation


def coordinate_groups(base: tuple[int, ...]) -> dict[int, tuple[int, ...]]:
    groups: dict[int, list[int]] = defaultdict(list)
    for coordinate in range(N):
        pattern = sum(((vertex >> coordinate) & 1) << index for index, vertex in enumerate(base))
        groups[pattern].append(coordinate)
    return {pattern: tuple(values) for pattern, values in groups.items()}


def setwise_stabilizer(base_values: list[int]) -> list[tuple[int, tuple[int, ...]]]:
    base = tuple(base_values)
    if len(base) != len(set(base)) or base[0] != 0:
        raise ValueError("base must contain distinct vertices and begin with zero")
    base_set = set(base)
    source_groups = coordinate_groups(base)
    source_profile = {pattern: len(values) for pattern, values in source_groups.items()}
    transformations: set[tuple[int, tuple[int, ...]]] = set()

    for base_permutation in permutations(range(len(base))):
        translation = base[base_permutation[0]]
        targets = tuple(base[base_permutation[index]] ^ translation for index in range(len(base)))
        target_groups = coordinate_groups(targets)
        if source_profile != {pattern: len(values) for pattern, values in target_groups.items()}:
            continue

        pattern_choices: list[list[tuple[tuple[int, ...], tuple[int, ...]]]] = []
        for pattern in sorted(source_groups):
            source_coordinates = source_groups[pattern]
            target_coordinates = target_groups[pattern]
            pattern_choices.append(
                [(target_coordinates, source_order) for source_order in permutations(source_coordinates)]
            )

        for choices in product(*pattern_choices):
            output_to_input: list[int | None] = [None] * N
            for target_coordinates, source_order in choices:
                for target_coordinate, source_coordinate in zip(target_coordinates, source_order):
                    output_to_input[target_coordinate] = source_coordinate
            if any(value is None for value in output_to_input):
                raise AssertionError("incomplete coordinate permutation")
            transform = translation, tuple(int(value) for value in output_to_input)
            images = {apply_transform(vertex, transform) for vertex in base}
            if images != base_set:
                raise AssertionError("invalid enumerated stabilizer transformation")
            transformations.add(transform)

    ordered = sorted(transformations)
    verify_group(base, ordered)
    return ordered


def verify_group(base: tuple[int, ...], transformations: list[tuple[int, tuple[int, ...]]]) -> None:
    keys = set(transformations)
    identity = (0, tuple(range(N)))
    if identity not in keys:
        raise AssertionError("stabilizer lacks identity")
    for transform in transformations:
        if {apply_transform(vertex, transform) for vertex in base} != set(base):
            raise AssertionError("transformation does not preserve base set")
    for left in transformations:
        for right in transformations:
            if compose(left, right) not in keys:
                raise AssertionError("stabilizer is not closed under composition")


def induced_base_permutation(
    base: tuple[int, ...], transform: tuple[int, tuple[int, ...]]
) -> list[int]:
    index = {vertex: position for position, vertex in enumerate(base)}
    return [index[apply_transform(vertex, transform)] for vertex in base]


def encode_transform(
    identifier: int,
    base: tuple[int, ...],
    transform: tuple[int, tuple[int, ...]],
) -> dict[str, object]:
    translation, output_to_input = transform
    return {
        "id": identifier,
        "translation": translation,
        "translation_hex": f"{translation:03x}",
        "output_to_input": list(output_to_input),
        "induced_base_permutation": induced_base_permutation(base, transform),
    }


def graph_stats(vertices: list[int]) -> dict[str, object]:
    vertex_digest = hashlib.sha256()
    for vertex in vertices:
        vertex_digest.update(f"{vertex:03x}\n".encode("ascii"))
    edge_count = 0
    incompatible_count = 0
    for left_index, left in enumerate(vertices):
        for right in vertices[left_index + 1 :]:
            separation = distance(left, right)
            if separation == K:
                edge_count += 1
            elif separation > K:
                incompatible_count += 1
    return {
        "vertices": len(vertices),
        "vertices_sha256": vertex_digest.hexdigest(),
        "distance6_edges": edge_count,
        "incompatible_pairs": incompatible_count,
    }


def complexity_tier(raw_clauses: int) -> str:
    if raw_clauses <= 100_000:
        return "PILOT"
    if raw_clauses <= 150_000:
        return "SMALL"
    if raw_clauses <= 200_000:
        return "MEDIUM"
    return "LARGE"


def read_vertices(path: Path) -> list[int]:
    text = path.read_text(encoding="ascii")
    if text and not text.endswith("\n"):
        raise ValueError(f"noncanonical vertex file without final newline: {path}")
    vertices = [int(line, 16) for line in text.splitlines()]
    if vertices != sorted(set(vertices)):
        raise ValueError(f"vertex file is not strictly sorted and unique: {path}")
    if any(f"{vertex:03x}" not in text.splitlines() for vertex in vertices):
        raise ValueError(f"vertex file has noncanonical hex: {path}")
    return vertices
