#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from classification_core import (
    CLAIM_ID, CLAUSES_PER_EDGE_RAW, CLAUSES_PER_VERTEX_RAW, COLORS, K, N,
    allowed, apply_transform, complexity_tier, distance, encode_transform,
    graph_stats, read_vertices, setwise_stabilizer, sha256_bytes, sha256_file,
)

def classify_child(child: dict[str, object], trim_root: Path) -> dict[str, object]:
    child_id = str(child["child_id"])
    base = tuple(int(value) for value in child["base"])
    vertices_path = trim_root / str(child["files"]["vertices"]["path"])
    if sha256_file(vertices_path) != child["files"]["vertices"]["sha256"]:
        raise ValueError(f"source vertex hash mismatch for {child_id}")
    vertices = read_vertices(vertices_path)
    reconstructed = [vertex for vertex in range(1 << N) if allowed(vertex, base)]
    if vertices != reconstructed:
        raise ValueError(f"source trim is not exhaustive for {child_id}")
    if not set(base).issubset(vertices):
        raise ValueError(f"base missing from source trim for {child_id}")

    transformations = setwise_stabilizer(list(base))
    encoded_transforms = [
        encode_transform(identifier, base, transform)
        for identifier, transform in enumerate(transformations)
    ]
    pointwise_ids = [
        record["id"]
        for record in encoded_transforms
        if record["induced_base_permutation"] == list(range(len(base)))
    ]
    pointwise = [transformations[int(identifier)] for identifier in pointwise_ids]

    candidates = sorted(set(vertices) - set(base))
    if candidates != [vertex for vertex in vertices if vertex not in set(base)]:
        raise AssertionError("candidate ordering mismatch")
    candidate_set = set(candidates)

    def partition(group: list[tuple[int, tuple[int, ...]]]) -> list[list[int]]:
        unseen = set(candidates)
        partitioned: list[list[int]] = []
        while unseen:
            representative = min(unseen)
            members = sorted({apply_transform(representative, transform) for transform in group})
            if not set(members).issubset(candidate_set):
                raise AssertionError(f"orbit left candidate set for {child_id}")
            unseen.difference_update(members)
            partitioned.append(members)
        if sorted(value for orbit in partitioned for value in orbit) != candidates:
            raise AssertionError(f"orbit partition is not exhaustive for {child_id}")
        return partitioned

    setwise_orbits = partition(transformations)
    pointwise_orbits = partition(pointwise)
    orbits: list[dict[str, object]] = []
    for orbit_index, members in enumerate(setwise_orbits):
        representative = members[0]
        mapping_records: list[dict[str, int]] = []
        for member in members:
            matching = [
                identifier
                for identifier, transform in enumerate(transformations)
                if apply_transform(representative, transform) == member
            ]
            if not matching:
                raise AssertionError("orbit mapping is missing")
            mapping_records.append({"member": member, "transform_id": min(matching)})
        representative_stabilizer_order = sum(
            apply_transform(representative, transform) == representative
            for transform in transformations
        )
        if len(members) * representative_stabilizer_order != len(transformations):
            raise AssertionError("orbit-stabilizer identity failed")

        seven_base = list(base) + [representative]
        grandchild_vertices = [vertex for vertex in vertices if distance(vertex, representative) <= K]
        reconstructed_grandchild = [
            vertex for vertex in range(1 << N) if allowed(vertex, seven_base)
        ]
        if grandchild_vertices != reconstructed_grandchild:
            raise AssertionError("grandchild trim reconstruction mismatch")
        graph = graph_stats(grandchild_vertices)
        raw_variables = COLORS * int(graph["vertices"])
        raw_clauses = (
            CLAUSES_PER_VERTEX_RAW * int(graph["vertices"])
            + CLAUSES_PER_EDGE_RAW * int(graph["distance6_edges"])
        )
        grandchild_id = f"{child_id}-t{orbit_index:03d}"
        orbits.append(
            {
                "grandchild_id": grandchild_id,
                "status": "UNKNOWN",
                "representative": representative,
                "representative_hex": f"{representative:03x}",
                "members": members,
                "orbit_size": len(members),
                "representative_stabilizer_order": representative_stabilizer_order,
                "member_mappings": mapping_records,
                "base": seven_base,
                "graph": graph,
                "raw_12color_cnf_proxy": {
                    "variables": raw_variables,
                    "clauses": raw_clauses,
                    "tier": complexity_tier(raw_clauses),
                    "interpretation": "scheduling proxy only; no SAT or UNSAT inference",
                },
            }
        )

    return {
        "schema": "borsuk-q00r00-seventh-base-child-classification-v1",
        "claim_id": CLAIM_ID,
        "child_id": child_id,
        "child_status": "UNKNOWN",
        "refinement_reason": "incomplete_sixth_base_screen_not_certified_obstruction",
        "base": list(base),
        "source_trim": {
            "vertices": len(vertices),
            "vertices_sha256": child["files"]["vertices"]["sha256"],
            "distance6_edges": child["counts"]["distance6_edges"],
            "incompatible_pairs": child["counts"]["incompatible_pairs"],
        },
        "candidate_count": len(candidates),
        "candidates": candidates,
        "candidates_sha256": sha256_bytes(
            b"".join(f"{vertex:03x}\n".encode("ascii") for vertex in candidates)
        ),
        "setwise_stabilizer_order": len(transformations),
        "pointwise_stabilizer_order": len(pointwise),
        "setwise_stabilizer": encoded_transforms,
        "setwise_orbit_count": len(orbits),
        "pointwise_orbit_count_negative_control": len(pointwise_orbits),
        "orbits": orbits,
    }

