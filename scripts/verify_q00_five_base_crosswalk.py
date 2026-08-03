#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from collections import defaultdict
from pathlib import Path
from types import ModuleType
from typing import Callable

GOVERNED_CLAIM_ID = "n11-k6-q00-five-base-reduction"
HISTORICAL_DRAFT_COMMIT = "99de5d42d1caa3987734dfa7bd35c18ad5c19929"
GOVERNED_CASE_SHA256 = "d5b0825cd8645af2c595b3de3c851360e0b283d8ce61383482f76168e1ae9855"
GOVERNED_ASSIGNMENT_SHA256 = "6c94923a260290d59727bdcad68293b7f1962a7c5377885dd536fefa5962ffc7"
DIFFERENTIAL_CASE_SHA256 = "01b3ee2e629788037f1ccd6906140302abddd1ae1c077aa8cf7e8f619adb807a"
EXPECTED_ID_MAP = {
    "q00r00": "f11",
    "q00r01": "f09",
    "q00r02": "f05",
    "q00r03": "f07",
    "q00r04": "f02",
    "q00r05": "f10",
    "q00r06": "f08",
    "q00r07": "f03",
    "q00r08": "f06",
    "q00r09": "f01",
    "q00r10": "f04",
    "q00r11": "f00",
}


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vertex_sha256(vertices: list[int]) -> str:
    payload = "".join(f"{vertex:03x}\n" for vertex in sorted(vertices)).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def assignment_from_text(text: str) -> dict[int, str]:
    output: dict[int, str] = {}
    for line in text.splitlines():
        encoded, case_id = line.split(",", 1)
        vertex = int(encoded, 16)
        if vertex in output:
            raise SystemExit(f"duplicate governed assignment for {encoded}")
        output[vertex] = case_id
    return output


def differential_orbits(module: ModuleType) -> tuple[dict[str, list[int]], dict[int, str]]:
    transforms = module.stabilizer_transforms()
    parent = [mask for mask in range(1 << module.N) if module.allowed(mask, module.BASE)]
    candidates = set(parent) - set(module.BASE)
    unseen = set(candidates)
    orbits: list[list[int]] = []
    while unseen:
        seed = min(unseen)
        orbit = sorted({transform(seed) for transform in transforms})
        if not set(orbit) <= candidates:
            raise SystemExit("differential stabilizer orbit escaped the q00 candidate set")
        unseen -= set(orbit)
        orbits.append(orbit)
    orbits.sort(key=min)
    by_id = {f"f{index:02d}": orbit for index, orbit in enumerate(orbits)}
    assignment = {vertex: case_id for case_id, orbit in by_id.items() for vertex in orbit}
    if len(assignment) != 432:
        raise SystemExit(f"differential coverage has {len(assignment)} candidates, expected 432")
    return by_id, assignment


def coordinate_signatures(
    points: tuple[int, ...], origin_index: int, order: tuple[int, ...], n: int
) -> list[tuple[int, ...]]:
    origin = points[origin_index]
    return [
        tuple(((points[index] ^ origin) >> coordinate) & 1 for index in order)
        for coordinate in range(n)
    ]


def recover_affine_map(
    source: tuple[int, ...], target: tuple[int, ...], n: int
) -> tuple[int, tuple[int, ...], tuple[int, ...], Callable[[int], int]]:
    """Recover x -> translation XOR coordinate_permutation(x) mapping source set to target set."""
    for source_origin in range(len(source)):
        source_rest = tuple(index for index in range(len(source)) if index != source_origin)
        source_signatures = coordinate_signatures(source, source_origin, source_rest, n)
        source_blocks: dict[tuple[int, ...], list[int]] = defaultdict(list)
        for coordinate, signature in enumerate(source_signatures):
            source_blocks[signature].append(coordinate)

        for target_origin in range(len(target)):
            for target_rest in itertools.permutations(
                index for index in range(len(target)) if index != target_origin
            ):
                target_signatures = coordinate_signatures(target, target_origin, target_rest, n)
                target_blocks: dict[tuple[int, ...], list[int]] = defaultdict(list)
                for coordinate, signature in enumerate(target_signatures):
                    target_blocks[signature].append(coordinate)
                if {key: len(value) for key, value in source_blocks.items()} != {
                    key: len(value) for key, value in target_blocks.items()
                }:
                    continue

                coordinate_map = [-1] * n
                for signature in sorted(source_blocks):
                    for old, new in zip(
                        sorted(source_blocks[signature]), sorted(target_blocks[signature])
                    ):
                        coordinate_map[old] = new
                if any(value < 0 for value in coordinate_map):
                    raise SystemExit("incomplete recovered coordinate map")

                translation = target[target_origin]

                def transform(
                    mask: int,
                    translation: int = translation,
                    coordinate_map: tuple[int, ...] = tuple(coordinate_map),
                    source_origin_value: int = source[source_origin],
                ) -> int:
                    image = translation
                    translated_mask = mask ^ source_origin_value
                    for old, new in enumerate(coordinate_map):
                        if (translated_mask >> old) & 1:
                            image ^= 1 << new
                    return image

                point_permutation = [-1] * len(source)
                point_permutation[source_origin] = target_origin
                for old, new in zip(source_rest, target_rest):
                    point_permutation[old] = new
                if tuple(transform(source[index]) for index in range(len(source))) != tuple(
                    target[point_permutation[index]] for index in range(len(source))
                ):
                    continue
                if {transform(point) for point in source} != set(target):
                    continue
                return translation, tuple(coordinate_map), tuple(point_permutation), transform
    raise SystemExit(f"no affine cube isometry maps {source} to {target}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()

    governed_path = repo_root / "borsuk_11_k6_q00_five_base_reduction" / "generate_cases.py"
    differential_path = (
        repo_root
        / "borsuk_11_k6_q00_five_base_reduction"
        / "differential"
        / "generate_stabilizer_orbits.py"
    )
    governed = load_module("governed_q00_five_base", governed_path)
    differential = load_module("differential_q00_five_base", differential_path)

    governed_rows, governed_assignment_text = governed.generate_cases()
    governed_csv = governed.render_csv(governed_rows)
    governed_case_hash = hashlib.sha256(governed_csv.encode("ascii")).hexdigest()
    governed_assignment_hash = hashlib.sha256(
        governed_assignment_text.encode("ascii")
    ).hexdigest()
    if governed_case_hash != GOVERNED_CASE_SHA256:
        raise SystemExit(f"governed case hash mismatch: {governed_case_hash}")
    if governed_assignment_hash != GOVERNED_ASSIGNMENT_SHA256:
        raise SystemExit(f"governed assignment hash mismatch: {governed_assignment_hash}")

    differential_rows, _ = differential.generate_rows()
    differential_csv = differential.render_csv(differential_rows)
    differential_case_hash = hashlib.sha256(differential_csv.encode("ascii")).hexdigest()
    if differential_case_hash != DIFFERENTIAL_CASE_SHA256:
        raise SystemExit(f"differential case hash mismatch: {differential_case_hash}")

    governed_assignment = assignment_from_text(governed_assignment_text)
    differential_members, differential_assignment = differential_orbits(differential)
    if set(governed_assignment) != set(differential_assignment):
        raise SystemExit("the implementations do not cover the same 432 fifth vertices")

    governed_by_signature = {row["base_signature"]: row for row in governed_rows}
    differential_by_signature = {row["base5_signature"]: row for row in differential_rows}
    if len(governed_by_signature) != 12 or len(differential_by_signature) != 12:
        raise SystemExit("a classification contains duplicate canonical signatures")
    if set(governed_by_signature) != set(differential_by_signature):
        raise SystemExit("canonical signature sets differ")

    crosswalk: list[dict[str, object]] = []
    id_map: dict[str, str] = {}
    for signature in sorted(governed_by_signature):
        left = governed_by_signature[signature]
        right = differential_by_signature[signature]
        left_id = str(left["id"])
        right_id = str(right["id"])
        left_members = sorted(
            vertex for vertex, case_id in governed_assignment.items() if case_id == left_id
        )
        right_members = differential_members[right_id]
        if left_members != right_members:
            raise SystemExit(f"coverage block mismatch: {left_id} versus {right_id}")
        if (
            int(left["member_count"]) != int(right["orbit_size"])
            or int(left["member_count"]) != len(left_members)
        ):
            raise SystemExit(f"orbit-size mismatch: {left_id} versus {right_id}")
        for field in ("vertices", "exact_distance_edges", "incompatible_pairs"):
            if int(left[field]) != int(right[field]):
                raise SystemExit(f"{field} mismatch: {left_id} versus {right_id}")

        left_d = int(left["D"])
        right_d = int(right["D"])
        source_base = tuple(governed.Q00_BASE) + (left_d,)
        target_base = tuple(differential.BASE) + (right_d,)
        translation, coordinate_map, point_permutation, transform = recover_affine_map(
            source_base, target_base, governed.N
        )
        source_vertices = governed.trim_vertices(source_base)
        target_vertices = [
            mask for mask in range(1 << differential.N) if differential.allowed(mask, target_base)
        ]
        transformed_vertices = {transform(vertex) for vertex in source_vertices}
        if transformed_vertices != set(target_vertices):
            raise SystemExit(f"transformed child-set mismatch: {left_id} versus {right_id}")
        computed_vertex_hash = vertex_sha256(target_vertices)
        if computed_vertex_hash != str(right["vertex_sha256"]):
            raise SystemExit(f"vertex hash mismatch: {left_id} versus {right_id}")

        id_map[left_id] = right_id
        crosswalk.append(
            {
                "governed_id": left_id,
                "historical_differential_id": right_id,
                "governed_D": left_d,
                "differential_D": right_d,
                "canonical_signature": signature,
                "orbit_size": len(left_members),
                "vertices": len(source_vertices),
                "exact_distance_edges": int(left["exact_distance_edges"]),
                "incompatible_pairs": int(left["incompatible_pairs"]),
                "vertex_sha256": computed_vertex_hash,
                "affine_map": {
                    "translation": translation,
                    "coordinate_map_old_to_new": list(coordinate_map),
                    "source_point_to_target_index": list(point_permutation),
                },
                "transformed_child_vertex_sets_equal": True,
            }
        )

    if id_map != EXPECTED_ID_MAP:
        raise SystemExit(f"unexpected 12-class bijection: {id_map}")
    for vertex in sorted(governed_assignment):
        mapped = id_map.get(governed_assignment[vertex])
        if mapped != differential_assignment[vertex]:
            raise SystemExit(f"candidate assignment mismatch at {vertex:03x}")

    crosswalk.sort(key=lambda row: str(row["governed_id"]))
    result = {
        "schema": "borsuk-q00-five-base-crosswalk-v2",
        "status": "PASS",
        "governed_claim_id": GOVERNED_CLAIM_ID,
        "historical_draft_commit": HISTORICAL_DRAFT_COMMIT,
        "historical_differential_labels_only": True,
        "governed_generator_sha256": file_sha256(governed_path),
        "differential_generator_sha256": file_sha256(differential_path),
        "governed_case_csv_sha256": governed_case_hash,
        "governed_assignment_sha256": governed_assignment_hash,
        "differential_case_csv_sha256": differential_case_hash,
        "candidate_count": len(governed_assignment),
        "class_count": len(crosswalk),
        "complete_bijection": True,
        "coverage_assignments_equal_under_crosswalk": True,
        "all_transformed_child_vertex_sets_equal": True,
        "claim_status_changed": False,
        "child_status_changed": False,
        "parent_q00_status_changed": False,
        "theorem_status_changed": False,
        "crosswalk": crosswalk,
    }
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
