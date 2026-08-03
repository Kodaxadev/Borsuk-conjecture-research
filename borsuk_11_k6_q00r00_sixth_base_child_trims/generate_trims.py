#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

N = 11
K = 6
FIXED_BASE = (0, 63, 455, 1611, 732)
PACKAGE_CLAIM = "n11-k6-q00r00-sixth-base-child-trims"
SCHEMA = "borsuk-q00r00-sixth-base-child-trims-v1"
PREDICATE = "wt(v) even and d_H(v,b) <= 6 for every b in the six-point base"
EXPECTED_CHILD_MANIFEST_SHA256 = "180e8398807c95478ac7cb62262758314a9c49270a487de0370f384dff39efb5"
EXPECTED_PARENT_ARCHIVE_SHA256 = "0f45e952cda60a47f01fb0a415de07438cc9bc32f3d4811c8d17ce1cb2982a7d"
EXPECTED_PARENT_SOURCE_COMMIT = "1cee54611bf414f7961cbdd43f5fc2b867b3230d"
EXPECTED_PARENT_RUN_ID = 30842512224
EXPECTED_PARENT_JOB_ID = 91782782478
EXPECTED_PARENT_ARTIFACT_ID = 8867349456


@dataclass(frozen=True)
class FrozenChild:
    child_id: str
    representative: int
    representative_hex: str
    orbit_size: int
    stabilizer_size: int
    status: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def trim_allowed(vertex: int, base: tuple[int, ...]) -> bool:
    return vertex.bit_count() % 2 == 0 and all(distance(vertex, point) <= K for point in base)


def read_frozen_children(path: Path) -> list[FrozenChild]:
    raw = path.read_bytes()
    actual_hash = sha256_bytes(raw)
    if actual_hash != EXPECTED_CHILD_MANIFEST_SHA256:
        raise SystemExit(f"classification child manifest hash mismatch: {actual_hash}")
    rows: list[FrozenChild] = []
    with path.open("r", encoding="ascii", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_fields = [
            "id",
            "representative",
            "representative_hex",
            "orbit_size",
            "stabilizer_size",
            "status",
        ]
        if reader.fieldnames != expected_fields:
            raise SystemExit(f"unexpected child manifest columns: {reader.fieldnames}")
        for index, row in enumerate(reader):
            expected_id = f"q00r00-s{index:03d}"
            child = FrozenChild(
                child_id=row["id"],
                representative=int(row["representative"]),
                representative_hex=row["representative_hex"],
                orbit_size=int(row["orbit_size"]),
                stabilizer_size=int(row["stabilizer_size"]),
                status=row["status"],
            )
            if child.child_id != expected_id:
                raise SystemExit(f"child ID sequence mismatch at {index}: {child.child_id}")
            if child.representative_hex != f"{child.representative:03x}":
                raise SystemExit(f"representative encoding mismatch for {child.child_id}")
            if child.status != "UNKNOWN":
                raise SystemExit(f"classification status changed for {child.child_id}")
            rows.append(child)
    if len(rows) != 36:
        raise SystemExit(f"expected 36 frozen children, got {len(rows)}")
    representatives = [row.representative for row in rows]
    if len(set(representatives)) != len(representatives):
        raise SystemExit("duplicate frozen representative")
    return rows


def validate_parent_binding(path: Path) -> dict[str, object]:
    binding = json.loads(path.read_text(encoding="utf-8"))
    expected_state = [
        "COMPUTATIONAL",
        "CI_INDEPENDENTLY_REPRODUCED",
        "EXECUTION_BOUND",
        "WORKING",
    ]
    checks = {
        "schema": binding.get("schema") == "borsuk-q00r00-sixth-base-execution-binding-v1",
        "status": binding.get("status") == "PASS",
        "claim": binding.get("claim_id") == "n11-k6-q00r00-sixth-base-classification",
        "evidence_state": binding.get("evidence_state") == expected_state,
        "run": (binding.get("workflow") or {}).get("run_id") == EXPECTED_PARENT_RUN_ID,
        "job": (binding.get("job") or {}).get("id") == EXPECTED_PARENT_JOB_ID,
        "job_success": (binding.get("job") or {}).get("conclusion") == "success",
        "artifact": (binding.get("artifact") or {}).get("id") == EXPECTED_PARENT_ARTIFACT_ID,
        "archive": (binding.get("artifact") or {}).get("archive_sha256") == EXPECTED_PARENT_ARCHIVE_SHA256,
        "source": (binding.get("source") or {}).get("commit") == EXPECTED_PARENT_SOURCE_COMMIT,
        "cases": (binding.get("classification") or {}).get("canonical_sixth_base_cases") == 36,
        "manifest_hash": (((binding.get("artifact") or {}).get("members") or {}).get("child_manifest.csv") or {}).get("sha256")
        == EXPECTED_CHILD_MANIFEST_SHA256,
        "q00r00_unknown": (binding.get("mathematical_status") or {}).get("q00r00") == "UNKNOWN",
        "q00_unknown": (binding.get("mathematical_status") or {}).get("q00") == "UNKNOWN",
        "full_open": (binding.get("mathematical_status") or {}).get("n11-k6-full") == "Gate 2 / OPEN",
    }
    failures = [name for name, passed in checks.items() if not passed]
    if failures:
        raise SystemExit(f"parent execution binding mismatch: {failures}")
    return binding


def render_vertices(vertices: Iterable[int]) -> bytes:
    return "".join(f"{vertex:03x}\n" for vertex in vertices).encode("ascii")


def render_pairs(pairs: Iterable[tuple[int, int]]) -> bytes:
    return ("left,right\n" + "".join(f"{left:03x},{right:03x}\n" for left, right in pairs)).encode("ascii")


def write_bytes(path: Path, data: bytes) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"path": path.as_posix(), "sha256": sha256_bytes(data), "size_bytes": len(data)}


def relative_record(root: Path, path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def generate_child(root: Path, frozen: FrozenChild, parent_binding: dict[str, object]) -> dict[str, object]:
    base = FIXED_BASE + (frozen.representative,)
    if len(set(base)) != 6:
        raise AssertionError(f"repeated six-point base entry for {frozen.child_id}")
    if not trim_allowed(frozen.representative, FIXED_BASE):
        raise AssertionError(f"frozen representative is not compatible for {frozen.child_id}")

    vertices = [vertex for vertex in range(1 << N) if trim_allowed(vertex, base)]
    if any(point not in vertices for point in base):
        raise AssertionError(f"six-point base is not contained in child trim {frozen.child_id}")

    exact_edges: list[tuple[int, int]] = []
    incompatible_pairs: list[tuple[int, int]] = []
    for index, left in enumerate(vertices):
        for right in vertices[index + 1 :]:
            separation = distance(left, right)
            if separation == K:
                exact_edges.append((left, right))
            elif separation > K:
                incompatible_pairs.append((left, right))

    child_dir = root / "children" / frozen.child_id
    parent_members = (parent_binding["artifact"] or {}).get("members")  # type: ignore[union-attr]
    base_record = {
        "base": list(base),
        "base_hex": [f"{point:03x}" for point in base],
        "child_id": frozen.child_id,
        "claim_id": f"n11-k6-{frozen.child_id}-universal-trim",
        "dimension": N,
        "diameter": K,
        "parent_classification": {
            "artifact_archive_sha256": EXPECTED_PARENT_ARCHIVE_SHA256,
            "artifact_id": EXPECTED_PARENT_ARTIFACT_ID,
            "child_manifest_sha256": EXPECTED_CHILD_MANIFEST_SHA256,
            "classification_json_sha256": parent_members["classification.json"]["sha256"],
            "orbits_json_sha256": parent_members["orbits.json"]["sha256"],
            "source_commit": EXPECTED_PARENT_SOURCE_COMMIT,
            "workflow_run_id": EXPECTED_PARENT_RUN_ID,
        },
        "predicate": PREDICATE,
        "representative": frozen.representative,
        "representative_hex": frozen.representative_hex,
        "status": "UNKNOWN",
    }
    base_path = child_dir / "base.json"
    vertices_path = child_dir / "vertices.txt"
    edges_path = child_dir / "distance6_edges.csv"
    incompatible_path = child_dir / "incompatible_pairs.csv"
    base_path.parent.mkdir(parents=True, exist_ok=True)
    base_path.write_bytes(canonical_json_bytes(base_record))
    vertices_path.write_bytes(render_vertices(vertices))
    edges_path.write_bytes(render_pairs(exact_edges))
    incompatible_path.write_bytes(render_pairs(incompatible_pairs))

    summary_record = {
        "base": relative_record(root, base_path),
        "child_id": frozen.child_id,
        "counts": {
            "distance6_edges": len(exact_edges),
            "incompatible_pairs": len(incompatible_pairs),
            "vertices": len(vertices),
        },
        "distance6_edges": relative_record(root, edges_path),
        "incompatible_pairs": relative_record(root, incompatible_path),
        "representative": frozen.representative,
        "representative_hex": frozen.representative_hex,
        "status": "UNKNOWN",
        "vertices": relative_record(root, vertices_path),
    }
    summary_path = child_dir / "summary.json"
    summary_path.write_bytes(canonical_json_bytes(summary_record))

    return {
        "base": list(base),
        "base_hex": [f"{point:03x}" for point in base],
        "child_id": frozen.child_id,
        "counts": summary_record["counts"],
        "files": {
            "base": relative_record(root, base_path),
            "distance6_edges": relative_record(root, edges_path),
            "incompatible_pairs": relative_record(root, incompatible_path),
            "summary": relative_record(root, summary_path),
            "vertices": relative_record(root, vertices_path),
        },
        "orbit_size": frozen.orbit_size,
        "representative": frozen.representative,
        "representative_hex": frozen.representative_hex,
        "stabilizer_size": frozen.stabilizer_size,
        "status": "UNKNOWN",
    }


def render_sha256sums(root: Path) -> bytes:
    paths = sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.name not in {"SHA256SUMS", "generation.json"}
    )
    return "".join(f"{sha256_file(path)}  {path.relative_to(root).as_posix()}\n" for path in paths).encode("ascii")


def generate(output: Path, input_dir: Path) -> dict[str, object]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    frozen_manifest_path = input_dir / "classification_child_manifest.csv"
    parent_binding_path = input_dir / "classification_execution_binding.json"
    frozen_children = read_frozen_children(frozen_manifest_path)
    parent_binding = validate_parent_binding(parent_binding_path)

    children = [generate_child(output, frozen, parent_binding) for frozen in frozen_children]
    if [child["child_id"] for child in children] != [f"q00r00-s{i:03d}" for i in range(36)]:
        raise AssertionError("frozen representatives were not consumed exactly once")
    if any(child["status"] != "UNKNOWN" for child in children):
        raise AssertionError("child status changed")

    total_vertices = sum(int(child["counts"]["vertices"]) for child in children)  # type: ignore[index]
    total_edges = sum(int(child["counts"]["distance6_edges"]) for child in children)  # type: ignore[index]
    total_incompatible = sum(int(child["counts"]["incompatible_pairs"]) for child in children)  # type: ignore[index]
    vertex_counts = [int(child["counts"]["vertices"]) for child in children]  # type: ignore[index]
    edge_counts = [int(child["counts"]["distance6_edges"]) for child in children]  # type: ignore[index]
    incompatible_counts = [int(child["counts"]["incompatible_pairs"]) for child in children]  # type: ignore[index]

    manifest = {
        "children": children,
        "claim_id": PACKAGE_CLAIM,
        "dimension": N,
        "diameter": K,
        "fixed_five_point_base": list(FIXED_BASE),
        "fixed_five_point_base_hex": [f"{point:03x}" for point in FIXED_BASE],
        "parent_classification": {
            "artifact_archive_sha256": EXPECTED_PARENT_ARCHIVE_SHA256,
            "artifact_id": EXPECTED_PARENT_ARTIFACT_ID,
            "child_manifest_sha256": EXPECTED_CHILD_MANIFEST_SHA256,
            "execution_binding_input_sha256": sha256_file(parent_binding_path),
            "source_commit": EXPECTED_PARENT_SOURCE_COMMIT,
            "workflow_job_id": EXPECTED_PARENT_JOB_ID,
            "workflow_run_id": EXPECTED_PARENT_RUN_ID,
        },
        "predicate": PREDICATE,
        "schema": SCHEMA,
        "status": "PASS",
        "status_boundary": {
            "children": "UNKNOWN",
            "n11-k6-full": "Gate 2 / OPEN",
            "q00": "UNKNOWN",
            "q00r00": "UNKNOWN",
        },
        "summary": {
            "child_count": len(children),
            "distance6_edge_count_range": [min(edge_counts), max(edge_counts)],
            "incompatible_pair_count_range": [min(incompatible_counts), max(incompatible_counts)],
            "total_distance6_edges_across_children": total_edges,
            "total_incompatible_pairs_across_children": total_incompatible,
            "total_vertices_across_children": total_vertices,
            "vertex_count_range": [min(vertex_counts), max(vertex_counts)],
        },
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_bytes(canonical_json_bytes(manifest))

    sha_path = output / "SHA256SUMS"
    sha_path.write_bytes(render_sha256sums(output))

    generation = {
        "claim_id": PACKAGE_CLAIM,
        "generated_file_count": sum(1 for path in output.rglob("*") if path.is_file()),
        "manifest_sha256": sha256_file(manifest_path),
        "schema": "borsuk-q00r00-sixth-base-child-trims-generation-v1",
        "sha256sums_sha256": sha256_file(sha_path),
        "status": "PASS",
        "summary": manifest["summary"],
    }
    generation_path = output / "generation.json"
    generation_path.write_bytes(canonical_json_bytes(generation))

    return {
        "manifest_sha256": sha256_file(manifest_path),
        "sha256sums_sha256": sha256_file(sha_path),
        "summary": manifest["summary"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path(__file__).with_name("input"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = generate(args.output, args.input_dir)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
