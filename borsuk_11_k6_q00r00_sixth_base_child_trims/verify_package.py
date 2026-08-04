#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "input"
WORK = ROOT / ".work"
PRIMARY = WORK / "python"
INDEPENDENT = WORK / "javascript"
GENERATED = ROOT / "generated"
EXPECTED = json.loads((ROOT / "EXPECTED_OUTPUT.json").read_text(encoding="utf-8"))
N = 11
K = 6
FIXED_BASE = (0, 63, 455, 1611, 732)


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


def allowed(vertex: int, base: tuple[int, ...]) -> bool:
    return vertex.bit_count() % 2 == 0 and all(distance(vertex, point) <= K for point in base)


def run(command: list[str]) -> None:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if completed.returncode != 0:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        raise SystemExit(f"command failed: {' '.join(command)}")
    if completed.stdout:
        print(completed.stdout.strip())


def all_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


def compare_trees(left: Path, right: Path) -> dict[str, object]:
    left_paths = {path.relative_to(left).as_posix(): path for path in all_files(left)}
    right_paths = {path.relative_to(right).as_posix(): path for path in all_files(right)}
    if set(left_paths) != set(right_paths):
        missing = sorted(set(left_paths) - set(right_paths))
        extra = sorted(set(right_paths) - set(left_paths))
        raise SystemExit(f"independent output path mismatch: missing={missing} extra={extra}")
    hashes: dict[str, str] = {}
    for relative in sorted(left_paths):
        left_hash = sha256_file(left_paths[relative])
        right_hash = sha256_file(right_paths[relative])
        if left_hash != right_hash:
            raise SystemExit(f"independent byte mismatch: {relative}")
        if left_paths[relative].stat().st_size != right_paths[relative].stat().st_size:
            raise SystemExit(f"independent size mismatch: {relative}")
        hashes[relative] = left_hash
    return {"all_bytes_identical": True, "file_count": len(hashes), "file_hashes": hashes}


def parse_vertices(path: Path) -> list[int]:
    text = path.read_bytes().decode("ascii")
    if text and not text.endswith("\n"):
        raise SystemExit(f"vertex file lacks final newline: {path}")
    values: list[int] = []
    for line in text.splitlines():
        if len(line) != 3 or line != line.lower():
            raise SystemExit(f"noncanonical vertex encoding {line!r} in {path}")
        value = int(line, 16)
        if f"{value:03x}" != line:
            raise SystemExit(f"noncanonical vertex hex {line!r} in {path}")
        values.append(value)
    if values != sorted(values) or len(values) != len(set(values)):
        raise SystemExit(f"vertex list is not strictly ascending and unique: {path}")
    return values


def parse_pairs(path: Path) -> list[tuple[int, int]]:
    with path.open("r", encoding="ascii", newline="") as handle:
        reader = csv.reader(handle)
        if next(reader, None) != ["left", "right"]:
            raise SystemExit(f"bad pair header in {path}")
        pairs: list[tuple[int, int]] = []
        previous: tuple[int, int] | None = None
        for row in reader:
            if len(row) != 2 or any(len(value) != 3 or value != value.lower() for value in row):
                raise SystemExit(f"noncanonical pair row in {path}: {row}")
            pair = int(row[0], 16), int(row[1], 16)
            if pair[0] >= pair[1] or (previous is not None and pair <= previous):
                raise SystemExit(f"pair file is not strictly canonical: {path}")
            previous = pair
            pairs.append(pair)
    return pairs


def expected_pairs(vertices: list[int]) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    edges: list[tuple[int, int]] = []
    incompatible: list[tuple[int, int]] = []
    for index, left in enumerate(vertices):
        for right in vertices[index + 1 :]:
            separation = distance(left, right)
            if separation == K:
                edges.append((left, right))
            elif separation > K:
                incompatible.append((left, right))
    return edges, incompatible


def validate_sha256sums(root: Path) -> None:
    lines = (root / "SHA256SUMS").read_text(encoding="ascii").splitlines()
    seen: set[str] = set()
    for line in lines:
        if len(line) < 67 or line[64:66] != "  ":
            raise SystemExit(f"malformed SHA256SUMS row: {line!r}")
        digest, relative = line[:64], line[66:]
        if relative in seen:
            raise SystemExit(f"duplicate SHA256SUMS path: {relative}")
        seen.add(relative)
        file_path = root / relative
        if not file_path.is_file() or sha256_file(file_path) != digest:
            raise SystemExit(f"SHA256SUMS mismatch: {relative}")
    expected_paths = {
        path.relative_to(root).as_posix()
        for path in all_files(root)
        if path.name not in {"SHA256SUMS", "generation.json"}
    }
    if seen != expected_paths:
        raise SystemExit("SHA256SUMS coverage mismatch")


def validate_mathematics(root: Path) -> dict[str, object]:
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256_file(manifest_path) != EXPECTED["manifest_sha256"]:
        raise SystemExit("frozen manifest hash mismatch")
    if sha256_file(root / "SHA256SUMS") != EXPECTED["sha256sums_sha256"]:
        raise SystemExit("frozen SHA256SUMS hash mismatch")
    if manifest.get("schema") != "borsuk-q00r00-sixth-base-child-trims-v1" or manifest.get("status") != "PASS":
        raise SystemExit("manifest schema or status mismatch")
    if manifest.get("fixed_five_point_base") != list(FIXED_BASE):
        raise SystemExit("fixed five-point base changed")
    if manifest.get("status_boundary") != {
        "children": "UNKNOWN",
        "n11-k6-full": "Gate 2 / OPEN",
        "q00": "UNKNOWN",
        "q00r00": "UNKNOWN",
    }:
        raise SystemExit("mathematical status boundary changed")
    if manifest.get("summary") != EXPECTED["summary"]:
        raise SystemExit("aggregate summary mismatch")

    children = manifest.get("children")
    if not isinstance(children, list) or len(children) != 36:
        raise SystemExit("manifest does not contain exactly 36 children")
    expected_ids = [f"q00r00-s{index:03d}" for index in range(36)]
    if [child.get("child_id") for child in children] != expected_ids:
        raise SystemExit("child IDs are incomplete, reordered, or duplicated")
    representatives = [child.get("representative") for child in children]
    if len(set(representatives)) != 36:
        raise SystemExit("frozen representatives were not consumed exactly once")

    total_vertices = total_edges = total_incompatible = 0
    for child in children:
        child_id = child["child_id"]
        if child.get("status") != "UNKNOWN":
            raise SystemExit(f"child status changed: {child_id}")
        file_paths = {
            key: root / child["files"][key]["path"]
            for key in ("base", "vertices", "distance6_edges", "incompatible_pairs", "summary")
        }
        for key, file_path in file_paths.items():
            record = child["files"][key]
            if sha256_file(file_path) != record["sha256"] or file_path.stat().st_size != record["size_bytes"]:
                raise SystemExit(f"manifest file binding mismatch: {child_id}/{key}")

        base_record = json.loads(file_paths["base"].read_text(encoding="utf-8"))
        base = tuple(base_record["base"])
        if len(base) != 6 or base[:5] != FIXED_BASE or base[5] != child["representative"] or len(set(base)) != 6:
            raise SystemExit(f"six-point base mismatch: {child_id}")
        if base_record.get("status") != "UNKNOWN" or base_record.get("predicate") != manifest.get("predicate"):
            raise SystemExit(f"base status or predicate mismatch: {child_id}")

        vertices = parse_vertices(file_paths["vertices"])
        if vertices != [vertex for vertex in range(1 << N) if allowed(vertex, base)]:
            raise SystemExit(f"trim vertex set is not exhaustive: {child_id}")
        if any(point not in vertices for point in base):
            raise SystemExit(f"six-point base absent from trim: {child_id}")

        edges = parse_pairs(file_paths["distance6_edges"])
        incompatible = parse_pairs(file_paths["incompatible_pairs"])
        recomputed_edges, recomputed_incompatible = expected_pairs(vertices)
        if edges != recomputed_edges or incompatible != recomputed_incompatible:
            raise SystemExit(f"pair classification mismatch: {child_id}")
        if set(edges).intersection(incompatible):
            raise SystemExit(f"edge and incompatible-pair sets overlap: {child_id}")

        counts = {
            "distance6_edges": len(edges),
            "incompatible_pairs": len(incompatible),
            "vertices": len(vertices),
        }
        if child["counts"] != counts:
            raise SystemExit(f"child count mismatch: {child_id}")
        summary = json.loads(file_paths["summary"].read_text(encoding="utf-8"))
        if summary.get("counts") != counts or summary.get("status") != "UNKNOWN":
            raise SystemExit(f"child summary mismatch: {child_id}")
        total_vertices += len(vertices)
        total_edges += len(edges)
        total_incompatible += len(incompatible)

    aggregate = {
        "child_count": 36,
        "total_distance6_edges_across_children": total_edges,
        "total_incompatible_pairs_across_children": total_incompatible,
        "total_vertices_across_children": total_vertices,
    }
    for key, value in aggregate.items():
        if EXPECTED["summary"][key] != value:
            raise SystemExit(f"aggregate total mismatch for {key}")
    validate_sha256sums(root)
    return aggregate


def main() -> int:
    if sha256_file(INPUT / "classification_child_manifest.csv") != EXPECTED["classification_child_manifest_sha256"]:
        raise SystemExit("governed classification child manifest input changed")
    if sha256_file(INPUT / "classification_execution_binding.json") != EXPECTED["classification_execution_binding_sha256"]:
        raise SystemExit("governed classification execution binding input changed")

    shutil.rmtree(WORK, ignore_errors=True)
    shutil.rmtree(GENERATED, ignore_errors=True)
    WORK.mkdir(parents=True)
    run([sys.executable, str(ROOT / "generate_trims.py"), "--input-dir", str(INPUT), "--output", str(PRIMARY)])
    run(["node", str(ROOT / "verify_independent.js"), "--input-dir", str(INPUT), "--output", str(INDEPENDENT)])

    comparison = compare_trees(PRIMARY, INDEPENDENT)
    if comparison["file_count"] != EXPECTED["generated_file_count_before_comparison"]:
        raise SystemExit(f"unexpected generated file count: {comparison['file_count']}")
    aggregate = validate_mathematics(PRIMARY)

    shutil.copytree(PRIMARY, GENERATED)
    report = {
        "aggregate": aggregate,
        "all_bytes_identical": True,
        "child_count": 36,
        "claim_id": "n11-k6-q00r00-sixth-base-child-trims",
        "independent_implementation": {
            "language": "JavaScript",
            "source_sha256": sha256_file(ROOT / "verify_independent.js"),
        },
        "manifest_sha256": EXPECTED["manifest_sha256"],
        "parent_classification": {
            "artifact_archive_sha256": "0f45e952cda60a47f01fb0a415de07438cc9bc32f3d4811c8d17ce1cb2982a7d",
            "artifact_id": 8867349456,
            "child_manifest_sha256": EXPECTED["classification_child_manifest_sha256"],
            "source_commit": "1cee54611bf414f7961cbdd43f5fc2b867b3230d",
            "workflow_job_id": 91782782478,
            "workflow_run_id": 30842512224,
        },
        "primary_implementation": {
            "language": "Python",
            "source_sha256": sha256_file(ROOT / "generate_trims.py"),
        },
        "schema": "borsuk-q00r00-sixth-base-child-trims-comparison-v1",
        "sha256sums_sha256": EXPECTED["sha256sums_sha256"],
        "status": "PASS",
        "status_boundary": {
            "children": "UNKNOWN",
            "n11-k6-full": "Gate 2 / OPEN",
            "q00": "UNKNOWN",
            "q00r00": "UNKNOWN",
        },
    }
    (GENERATED / "comparison.json").write_bytes(canonical_json_bytes(report))
    shutil.rmtree(WORK)
    print(
        "PASS children=36 vertices_total={total_vertices_across_children} "
        "edges_total={total_distance6_edges_across_children} "
        "incompatible_total={total_incompatible_pairs_across_children} "
        "manifest_sha256={manifest}".format(manifest=EXPECTED["manifest_sha256"], **aggregate)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
