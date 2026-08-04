#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, TextIO

N = 11
K = 6
COLORS = 12
EXPECTED_CHILD_COUNT = 36
EXPECTED_ARCHIVE_SHA256 = "a1862053e19a4341b941e62181c180805fb59a7969241d473705635dd04d0505"
EXPECTED_PARENT_MANIFEST_SHA256 = "559f83e4eb245902b9ec1808812248694c7931a535213c45b50d7a89a461e5fa"
EXPECTED_PARENT_SHA256SUMS_SHA256 = "45e96e2b460d6f968ed664b06ec59adc6091040273acf9cfbc022d3a1586654c"
SOURCE_COMMIT = "aad27339d6e689afdb50dbb8c280a76230b915fc"
PARENT_RUN_ID = 30851783510
PARENT_ARTIFACT_ID = 8870872535


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


def parse_vertices(path: Path) -> list[int]:
    raw = path.read_bytes()
    text = raw.decode("ascii")
    if text and not text.endswith("\n"):
        raise SystemExit(f"missing final newline: {path}")
    vertices = [int(line, 16) for line in text.splitlines()]
    if any(f"{vertex:03x}" != line for vertex, line in zip(vertices, text.splitlines())):
        raise SystemExit(f"noncanonical vertex encoding: {path}")
    if vertices != sorted(set(vertices)):
        raise SystemExit(f"vertices are not strictly ascending and unique: {path}")
    return vertices


def parse_edges(path: Path) -> list[tuple[int, int]]:
    with path.open("r", encoding="ascii", newline="") as handle:
        reader = csv.reader(handle)
        if next(reader, None) != ["left", "right"]:
            raise SystemExit(f"bad edge header: {path}")
        edges: list[tuple[int, int]] = []
        for row in reader:
            if len(row) != 2:
                raise SystemExit(f"bad edge row: {path}: {row}")
            left, right = (int(value, 16) for value in row)
            if f"{left:03x}" != row[0] or f"{right:03x}" != row[1] or left >= right:
                raise SystemExit(f"noncanonical edge row: {path}: {row}")
            edges.append((left, right))
    if edges != sorted(set(edges)):
        raise SystemExit(f"edges are not strictly ascending and unique: {path}")
    return edges


def validate_parent_tree(root: Path) -> dict[str, object]:
    manifest_path = root / "manifest.json"
    sums_path = root / "SHA256SUMS"
    if sha256_file(manifest_path) != EXPECTED_PARENT_MANIFEST_SHA256:
        raise SystemExit("parent manifest hash changed")
    if sha256_file(sums_path) != EXPECTED_PARENT_SHA256SUMS_SHA256:
        raise SystemExit("parent SHA256SUMS hash changed")

    listed: set[str] = set()
    for line in sums_path.read_text(encoding="ascii").splitlines():
        digest, relative = line.split("  ", 1)
        if relative in listed:
            raise SystemExit(f"duplicate parent checksum entry: {relative}")
        path = root / relative
        if not path.is_file() or sha256_file(path) != digest:
            raise SystemExit(f"parent checksum mismatch: {relative}")
        listed.add(relative)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    children = manifest.get("children")
    if not isinstance(children, list) or len(children) != EXPECTED_CHILD_COUNT:
        raise SystemExit("parent manifest does not contain exactly 36 children")
    expected_ids = [f"q00r00-s{index:03d}" for index in range(EXPECTED_CHILD_COUNT)]
    if [child.get("child_id") for child in children] != expected_ids:
        raise SystemExit("parent child IDs are incomplete or reordered")
    if manifest.get("status_boundary") != {
        "children": "UNKNOWN",
        "n11-k6-full": "Gate 2 / OPEN",
        "q00": "UNKNOWN",
        "q00r00": "UNKNOWN",
    }:
        raise SystemExit("parent mathematical status boundary changed")
    return manifest


def deterministic_clique(vertices: list[int], edges: list[tuple[int, int]]) -> list[int]:
    degree = {vertex: 0 for vertex in vertices}
    for left, right in edges:
        degree[left] += 1
        degree[right] += 1
    clique: list[int] = []
    for vertex in sorted(vertices, key=lambda value: (-degree[value], value)):
        if all(distance(vertex, present) == K for present in clique):
            clique.append(vertex)
            if len(clique) == COLORS:
                break
    if not clique:
        raise SystemExit("deterministic clique construction returned an empty clique")
    return clique


def allowed_colors(vertices: list[int], clique: list[int]) -> dict[int, tuple[int, ...]]:
    fixed = {vertex: color for color, vertex in enumerate(clique)}
    domains: dict[int, tuple[int, ...]] = {}
    for vertex in vertices:
        if vertex in fixed:
            domain = (fixed[vertex],)
        else:
            domain = tuple(
                color
                for color in range(COLORS)
                if color >= len(clique) or distance(vertex, clique[color]) != K
            )
        if not domain:
            raise SystemExit(f"empty color domain for vertex {vertex}")
        domains[vertex] = domain
    return domains


def variable_maps(
    vertices: list[int], domains: dict[int, tuple[int, ...]]
) -> tuple[dict[tuple[int, int], int], dict[int, tuple[int, int]]]:
    forward: dict[tuple[int, int], int] = {}
    reverse: dict[int, tuple[int, int]] = {}
    next_variable = 1
    for vertex in vertices:
        for color in domains[vertex]:
            forward[(vertex, color)] = next_variable
            reverse[next_variable] = (vertex, color)
            next_variable += 1
    return forward, reverse


def domain_mask(domain: Iterable[int]) -> int:
    return sum(1 << color for color in domain)


def formula_counts(
    vertices: list[int], edges: list[tuple[int, int]], domains: dict[int, tuple[int, ...]]
) -> tuple[int, int]:
    variables = sum(len(domains[vertex]) for vertex in vertices)
    clauses = sum(1 + math.comb(len(domains[vertex]), 2) for vertex in vertices)
    masks = {vertex: domain_mask(domains[vertex]) for vertex in vertices}
    clauses += sum((masks[left] & masks[right]).bit_count() for left, right in edges)
    return variables, clauses


def emit_cnf(
    stream: TextIO,
    child_id: str,
    vertices: list[int],
    edges: list[tuple[int, int]],
    clique: list[int],
    domains: dict[int, tuple[int, ...]],
) -> None:
    forward, _ = variable_maps(vertices, domains)
    variables, clauses = formula_counts(vertices, edges, domains)
    stream.write(f"c {child_id} canonical compact 12-color CNF\n")
    stream.write("c Variables are ordered by ascending vertex then ascending allowed color.\n")
    stream.write("c Greedy clique order is descending degree then ascending vertex.\n")
    stream.write(f"p cnf {variables} {clauses}\n")

    for vertex in vertices:
        identifiers = [forward[(vertex, color)] for color in domains[vertex]]
        stream.write(" ".join(map(str, identifiers)) + " 0\n")
        for left_index in range(len(identifiers)):
            for right_index in range(left_index + 1, len(identifiers)):
                stream.write(f"-{identifiers[left_index]} -{identifiers[right_index]} 0\n")

    masks = {vertex: domain_mask(domains[vertex]) for vertex in vertices}
    for left, right in edges:
        common = masks[left] & masks[right]
        while common:
            bit = common & -common
            color = bit.bit_length() - 1
            common -= bit
            stream.write(f"-{forward[(left, color)]} -{forward[(right, color)]} 0\n")


def write_sha256sums(root: Path, paths: list[Path]) -> None:
    lines = [f"{sha256_file(path)}  {path.relative_to(root).as_posix()}" for path in sorted(paths)]
    (root / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="ascii")


def build_child(trim_root: Path, output: Path, child: dict[str, object]) -> dict[str, object]:
    child_id = str(child["child_id"])
    source = trim_root / "children" / child_id
    vertices_path = source / "vertices.txt"
    edges_path = source / "distance6_edges.csv"
    base_path = source / "base.json"
    summary_path = source / "summary.json"

    vertices = parse_vertices(vertices_path)
    edges = parse_edges(edges_path)
    base = json.loads(base_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("status") != "UNKNOWN" or base.get("status") != "UNKNOWN":
        raise SystemExit(f"status leakage in parent trim: {child_id}")
    if summary.get("counts") != {
        "distance6_edges": len(edges),
        "incompatible_pairs": child["counts"]["incompatible_pairs"],
        "vertices": len(vertices),
    }:
        raise SystemExit(f"parent summary count mismatch: {child_id}")
    vertex_set = set(vertices)
    if any(left not in vertex_set or right not in vertex_set or distance(left, right) != K for left, right in edges):
        raise SystemExit(f"invalid source edge: {child_id}")

    clique = deterministic_clique(vertices, edges)
    domains = allowed_colors(vertices, clique)
    variables, clauses = formula_counts(vertices, edges, domains)
    _, reverse = variable_maps(vertices, domains)

    child_out = output / "cases" / child_id
    child_out.mkdir(parents=True, exist_ok=True)
    cnf_path = child_out / f"{child_id}_12color.cnf"
    map_path = child_out / f"{child_id}_variable_map.json"
    metadata_path = child_out / f"{child_id}_metadata.json"

    with cnf_path.open("w", encoding="ascii", newline="") as stream:
        emit_cnf(stream, child_id, vertices, edges, clique, domains)

    mapping = {
        "schema": "borsuk-q00r00-sixth-base-color-map-v1",
        "case_id": child_id,
        "colors": COLORS,
        "vertices": vertices,
        "fixed_clique": clique,
        "allowed_colors": {str(vertex): list(domains[vertex]) for vertex in vertices},
        "variables": variables,
        "clauses": clauses,
        "variable_order": [
            {"variable": variable, "vertex": pair[0], "color": pair[1]}
            for variable, pair in reverse.items()
        ],
    }
    map_path.write_bytes(canonical_json_bytes(mapping))

    metadata = {
        "schema": "borsuk-q00r00-sixth-base-color-instance-v1",
        "claim_id": "n11-k6-q00r00-sixth-base-colorability-screen",
        "case_id": child_id,
        "base": base["base"],
        "representative": child["representative"],
        "vertices": len(vertices),
        "edges": len(edges),
        "incompatible_pairs": child["counts"]["incompatible_pairs"],
        "colors": COLORS,
        "fixed_clique": clique,
        "fixed_clique_size": len(clique),
        "variables": variables,
        "clauses": clauses,
        "source_vertices_sha256": sha256_file(vertices_path),
        "source_edges_sha256": sha256_file(edges_path),
        "cnf_sha256": sha256_file(cnf_path),
        "variable_map_sha256": sha256_file(map_path),
        "result_state": "UNKNOWN",
        "interpretation": {
            "checked_sat": "proves the complete universal trim 12-colorable and closes this child branch",
            "checked_unsat": "proves only the universal trim non-12-colorable; child remains UNKNOWN and requires compatible seventh-base refinement",
        },
    }
    metadata_path.write_bytes(canonical_json_bytes(metadata))
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trim-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = validate_parent_tree(args.trim_root)
    if args.output.exists():
        import shutil
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)

    records = [build_child(args.trim_root, args.output, child) for child in manifest["children"]]
    aggregate = {
        "schema": "borsuk-q00r00-sixth-base-colorability-instances-v1",
        "claim_id": "n11-k6-q00r00-sixth-base-colorability-screen",
        "source": {
            "child_trim_source_commit": SOURCE_COMMIT,
            "child_trim_workflow_run_id": PARENT_RUN_ID,
            "child_trim_artifact_id": PARENT_ARTIFACT_ID,
            "child_trim_archive_sha256": EXPECTED_ARCHIVE_SHA256,
            "child_trim_manifest_sha256": EXPECTED_PARENT_MANIFEST_SHA256,
            "child_trim_sha256sums_sha256": EXPECTED_PARENT_SHA256SUMS_SHA256,
        },
        "case_count": len(records),
        "cases": records,
        "totals": {
            "vertices_across_cases": sum(int(record["vertices"]) for record in records),
            "edges_across_cases": sum(int(record["edges"]) for record in records),
            "variables_across_cases": sum(int(record["variables"]) for record in records),
            "clauses_across_cases": sum(int(record["clauses"]) for record in records),
        },
        "status_boundary": {
            "children": "UNKNOWN until an individual checked SAT coloring exists",
            "checked_unsat_children": "UNKNOWN",
            "q00r00": "UNKNOWN",
            "q00": "UNKNOWN",
            "n11-k6-full": "Gate 2 / OPEN",
        },
    }
    instances_path = args.output / "instances.json"
    instances_path.write_bytes(canonical_json_bytes(aggregate))
    paths = [path for path in args.output.rglob("*") if path.is_file() and path.name != "SHA256SUMS"]
    write_sha256sums(args.output, paths)
    print(json.dumps({
        "case_count": len(records),
        "instances_sha256": sha256_file(instances_path),
        "sha256sums_sha256": sha256_file(args.output / "SHA256SUMS"),
        **aggregate["totals"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
