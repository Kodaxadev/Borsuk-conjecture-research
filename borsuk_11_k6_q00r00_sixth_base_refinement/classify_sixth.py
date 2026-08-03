#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from collections import Counter, defaultdict, deque
from io import StringIO
from pathlib import Path
from typing import Iterable

N = 11
K = 6
BASE = (0, 63, 455, 1611, 732)
IDENTITY_PERM = tuple(range(N))
IDENTITY_BASE_PERM = tuple(range(len(BASE)))
SCHEMA = "borsuk-q00r00-sixth-base-classification-v1"
CLAIM_ID = "n11-k6-q00r00-sixth-base-classification"

Auto = tuple[int, tuple[int, ...]]  # translation, coordinate_map_old_to_new


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def compatible(vertex: int) -> bool:
    return (
        vertex not in BASE
        and vertex.bit_count() % 2 == 0
        and all(distance(vertex, base) <= K for base in BASE)
    )


def linear_apply(vertex: int, coordinate_map: tuple[int, ...]) -> int:
    image = 0
    for old_coordinate, new_coordinate in enumerate(coordinate_map):
        if (vertex >> old_coordinate) & 1:
            image |= 1 << new_coordinate
    return image


def apply_auto(vertex: int, auto: Auto) -> int:
    translation, coordinate_map = auto
    return linear_apply(vertex, coordinate_map) ^ translation


def compose(left: Auto, right: Auto) -> Auto:
    """Return left after right."""
    left_translation, left_map = left
    right_translation, right_map = right
    coordinate_map = tuple(left_map[right_map[old]] for old in range(N))
    translation = left_translation ^ linear_apply(right_translation, left_map)
    return translation, coordinate_map


def inverse(auto: Auto) -> Auto:
    translation, coordinate_map = auto
    inverse_map = [0] * N
    for old_coordinate, new_coordinate in enumerate(coordinate_map):
        inverse_map[new_coordinate] = old_coordinate
    inverse_map_tuple = tuple(inverse_map)
    return linear_apply(translation, inverse_map_tuple), inverse_map_tuple


def subgroup_closure(generators: Iterable[Auto]) -> set[Auto]:
    identity: Auto = (0, IDENTITY_PERM)
    moves = list(generators)
    moves.extend(inverse(generator) for generator in tuple(moves))
    closure = {identity}
    queue = deque([identity])
    while queue:
        current = queue.popleft()
        for move in moves:
            image = compose(move, current)
            if image not in closure:
                closure.add(image)
                queue.append(image)
    return closure


def coordinate_pattern(points: tuple[int, ...], coordinate: int) -> int:
    return sum(((point >> coordinate) & 1) << index for index, point in enumerate(points))


def enumerate_unordered_stabilizer() -> tuple[list[Auto], dict[Auto, tuple[int, ...]]]:
    """Enumerate all affine cube isometries preserving BASE as an unordered set.

    For each proposed permutation of the five base points, the image of zero fixes
    the translation. The four remaining point equations reduce coordinate
    permutations to bijections between equal four-bit coordinate-column patterns.
    """
    source_points = BASE[1:]
    source_groups: dict[int, list[int]] = defaultdict(list)
    for coordinate in range(N):
        source_groups[coordinate_pattern(source_points, coordinate)].append(coordinate)

    elements: dict[Auto, tuple[int, ...]] = {}
    for induced_permutation in itertools.permutations(range(len(BASE))):
        translation = BASE[induced_permutation[0]]
        target_points = tuple(
            BASE[induced_permutation[index]] ^ translation
            for index in range(1, len(BASE))
        )
        target_groups: dict[int, list[int]] = defaultdict(list)
        for coordinate in range(N):
            target_groups[coordinate_pattern(target_points, coordinate)].append(coordinate)

        if {key: len(value) for key, value in source_groups.items()} != {
            key: len(value) for key, value in target_groups.items()
        }:
            continue

        patterns = sorted(source_groups)
        assignment_choices = [
            list(itertools.permutations(target_groups[pattern])) for pattern in patterns
        ]
        for chosen_assignments in itertools.product(*assignment_choices):
            coordinate_map = [-1] * N
            for pattern, target_coordinates in zip(patterns, chosen_assignments):
                for old_coordinate, new_coordinate in zip(
                    source_groups[pattern], target_coordinates
                ):
                    coordinate_map[old_coordinate] = new_coordinate
            auto: Auto = (translation, tuple(coordinate_map))
            images = tuple(apply_auto(point, auto) for point in BASE)
            expected = tuple(BASE[index] for index in induced_permutation)
            if images != expected:
                raise AssertionError("constructed automorphism has wrong base action")
            previous = elements.get(auto)
            if previous is not None and previous != induced_permutation:
                raise AssertionError("one automorphism induced two base permutations")
            elements[auto] = induced_permutation

    ordered = sorted(elements, key=lambda auto: (auto[0], auto[1]))
    return ordered, elements


def minimal_generators(elements: list[Auto]) -> list[Auto]:
    target = set(elements)
    for size in range(1, len(elements) + 1):
        for generators in itertools.combinations(elements, size):
            if subgroup_closure(generators) == target:
                return list(generators)
    raise AssertionError("stabilizer is not generated by its elements")


def auto_record(auto: Auto, induced_permutation: tuple[int, ...]) -> dict[str, object]:
    translation, coordinate_map = auto
    return {
        "coordinate_map_old_to_new": list(coordinate_map),
        "induced_base_permutation": list(induced_permutation),
        "translation": translation,
        "translation_hex": f"{translation:03x}",
    }


def render_candidates(candidates: list[int]) -> bytes:
    return "".join(f"{vertex:03x}\n" for vertex in candidates).encode("ascii")


def render_manifest(orbits: list[dict[str, object]]) -> bytes:
    fields = [
        "id",
        "representative",
        "representative_hex",
        "orbit_size",
        "stabilizer_size",
        "status",
    ]
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for orbit in orbits:
        writer.writerow(
            {
                "id": orbit["id"],
                "representative": orbit["representative"],
                "representative_hex": orbit["representative_hex"],
                "orbit_size": orbit["orbit_size"],
                "stabilizer_size": orbit["stabilizer_size"],
                "status": "UNKNOWN",
            }
        )
    return buffer.getvalue().encode("ascii")


def classify() -> dict[str, bytes]:
    candidates = [vertex for vertex in range(1 << N) if compatible(vertex)]
    candidate_set = set(candidates)
    candidate_bytes = render_candidates(candidates)

    elements, induced_by_element = enumerate_unordered_stabilizer()
    element_set = set(elements)
    identity: Auto = (0, IDENTITY_PERM)

    # Mechanical group and action checks.
    if identity not in element_set:
        raise AssertionError("stabilizer lacks identity")
    for element in elements:
        if inverse(element) not in element_set:
            raise AssertionError("stabilizer is not inverse closed")
        if set(apply_auto(point, element) for point in BASE) != set(BASE):
            raise AssertionError("element does not preserve the base set")
        if any(apply_auto(vertex, element) not in candidate_set for vertex in candidates):
            raise AssertionError("candidate set is not invariant")
    for left in elements:
        for right in elements:
            if compose(left, right) not in element_set:
                raise AssertionError("stabilizer is not composition closed")

    generators = minimal_generators(elements)
    if subgroup_closure(generators) != element_set:
        raise AssertionError("generator closure mismatch")

    induced_permutations = sorted(set(induced_by_element.values()))
    pointwise_elements = [
        element
        for element in elements
        if induced_by_element[element] == IDENTITY_BASE_PERM
    ]

    stabilizer_element_records = [
        auto_record(element, induced_by_element[element]) for element in elements
    ]
    stabilizer_elements_bytes = canonical_json_bytes(stabilizer_element_records)
    induced_permutations_bytes = canonical_json_bytes(
        [list(permutation) for permutation in induced_permutations]
    )

    generator_records = [
        auto_record(generator, induced_by_element[generator]) for generator in generators
    ]
    pointwise_records = [
        auto_record(element, induced_by_element[element]) for element in pointwise_elements
    ]

    stabilizer_document = {
        "action": "g(x)=P(x) xor t; coordinate_map_old_to_new[i] is the image coordinate of input coordinate i",
        "base": list(BASE),
        "element_count": len(elements),
        "elements": stabilizer_element_records,
        "elements_sha256": sha256(stabilizer_elements_bytes),
        "generator_count": len(generators),
        "generators": generator_records,
        "induced_base_permutation_count": len(induced_permutations),
        "induced_base_permutations": [list(permutation) for permutation in induced_permutations],
        "induced_base_permutations_sha256": sha256(induced_permutations_bytes),
        "order": len(elements),
        "pointwise_element_count": len(pointwise_elements),
        "pointwise_elements": pointwise_records,
        "pointwise_order": len(pointwise_elements),
        "schema": "borsuk-affine-cube-set-stabilizer-v1",
    }
    stabilizer_bytes = canonical_json_bytes(stabilizer_document)

    unseen = set(candidates)
    orbit_records: list[dict[str, object]] = []
    coverage_counter: Counter[int] = Counter()
    for orbit_index in range(len(candidates)):
        if not unseen:
            break
        representative = min(unseen)
        members = sorted({apply_auto(representative, element) for element in elements})
        member_set = set(members)
        if not member_set <= candidate_set:
            raise AssertionError("orbit contains a noncandidate")
        stabilizer_size = sum(
            apply_auto(representative, element) == representative for element in elements
        )
        if len(members) * stabilizer_size != len(elements):
            raise AssertionError("orbit-stabilizer mismatch")

        mappings = []
        for member in members:
            mapping_candidates = [
                element
                for element in elements
                if apply_auto(representative, element) == member
            ]
            if not mapping_candidates:
                raise AssertionError("missing representative-to-member map")
            chosen = min(mapping_candidates, key=lambda auto: (auto[0], auto[1]))
            if apply_auto(representative, chosen) != member:
                raise AssertionError("invalid representative-to-member map")
            mappings.append(
                {
                    "automorphism": auto_record(chosen, induced_by_element[chosen]),
                    "member": member,
                    "member_hex": f"{member:03x}",
                }
            )

        orbit_id = f"q00r00-s{orbit_index:03d}"
        orbit_records.append(
            {
                "id": orbit_id,
                "mappings_from_representative": mappings,
                "members": members,
                "members_hex": [f"{member:03x}" for member in members],
                "orbit_size": len(members),
                "representative": representative,
                "representative_hex": f"{representative:03x}",
                "stabilizer_size": stabilizer_size,
                "status": "UNKNOWN",
            }
        )
        coverage_counter.update(members)
        unseen -= member_set

    if unseen:
        raise AssertionError("orbit enumeration left candidates uncovered")
    if set(coverage_counter) != candidate_set:
        raise AssertionError("orbit union differs from candidate set")
    if any(count != 1 for count in coverage_counter.values()):
        raise AssertionError("orbit partition is not disjoint")

    orbits_document = {
        "base": list(BASE),
        "candidate_count": len(candidates),
        "orbit_count": len(orbit_records),
        "orbits": orbit_records,
        "schema": "borsuk-q00r00-sixth-base-orbits-v1",
        "stabilizer_order": len(elements),
    }
    orbits_bytes = canonical_json_bytes(orbits_document)
    manifest_bytes = render_manifest(orbit_records)

    # Hostile negative control: pointwise stabilizer must over-split the action.
    pointwise_unseen = set(candidates)
    pointwise_orbit_count = 0
    while pointwise_unseen:
        representative = min(pointwise_unseen)
        members = {apply_auto(representative, element) for element in pointwise_elements}
        pointwise_unseen -= members
        pointwise_orbit_count += 1

    all_listed_compatible = all(compatible(vertex) for vertex in candidates)
    exhaustive_scan_equal = candidate_set == {
        vertex
        for vertex in range(1 << N)
        if vertex not in BASE
        and vertex.bit_count() % 2 == 0
        and all(distance(vertex, base) <= K for base in BASE)
    }

    output_hashes = {
        "child_manifest_csv_sha256": sha256(manifest_bytes),
        "compatible_candidates_sha256": sha256(candidate_bytes),
        "orbits_json_sha256": sha256(orbits_bytes),
        "stabilizer_json_sha256": sha256(stabilizer_bytes),
    }
    histogram = Counter(int(orbit["orbit_size"]) for orbit in orbit_records)
    report = {
        "base": list(BASE),
        "candidate_count": len(candidates),
        "candidate_encoding": "ascending lowercase three-hex-digit vertices, one per LF-terminated line",
        "checks": {
            "all_listed_candidates_compatible": all_listed_compatible,
            "all_orbit_mappings_valid": True,
            "candidate_scan_exhaustive": exhaustive_scan_equal,
            "generator_closure_equals_stabilizer": subgroup_closure(generators) == element_set,
            "no_incompatible_vertex_listed": all_listed_compatible,
            "orbit_stabilizer_identity": all(
                int(orbit["orbit_size"]) * int(orbit["stabilizer_size"]) == len(elements)
                for orbit in orbit_records
            ),
            "orbits_disjoint": all(count == 1 for count in coverage_counter.values()),
            "orbits_union_candidate_set": set(coverage_counter) == candidate_set,
            "unordered_and_pointwise_actions_distinct": len(elements) != len(pointwise_elements),
        },
        "claim_id": CLAIM_ID,
        "compatibility_predicate": "v not in B; wt(v) is even; and d_H(v,b) <= 6 for every b in B",
        "induced_base_permutation_count": len(induced_permutations),
        "n": N,
        "k": K,
        "orbit_count": len(orbit_records),
        "orbit_size_histogram": [
            {"orbit_size": size, "count": count}
            for size, count in sorted(histogram.items())
        ],
        "output_hashes": output_hashes,
        "pointwise_orbit_count_negative_control": pointwise_orbit_count,
        "pointwise_stabilizer_order": len(pointwise_elements),
        "schema": SCHEMA,
        "stabilizer_generator_count": len(generators),
        "stabilizer_order": len(elements),
        "status": "PASS",
    }
    report_bytes = canonical_json_bytes(report)

    return {
        "child_manifest.csv": manifest_bytes,
        "classification.json": report_bytes,
        "compatible_candidates.txt": candidate_bytes,
        "orbits.json": orbits_bytes,
        "stabilizer.json": stabilizer_bytes,
    }


def write_outputs(output_dir: Path) -> None:
    outputs = classify()
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        (output_dir / name).write_bytes(content)
    sums = "".join(f"{sha256(content)}  {name}\n" for name, content in sorted(outputs.items()))
    (output_dir / "SHA256SUMS").write_text(sums, encoding="ascii", newline="")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    write_outputs(args.output_dir)
    report = json.loads((args.output_dir / "classification.json").read_text(encoding="utf-8"))
    print(
        "PASS "
        f"candidates={report['candidate_count']} "
        f"stabilizer={report['stabilizer_order']} "
        f"pointwise={report['pointwise_stabilizer_order']} "
        f"orbits={report['orbit_count']} "
        f"pointwise_orbits={report['pointwise_orbit_count_negative_control']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
