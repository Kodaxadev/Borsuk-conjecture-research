#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Iterable, TextIO

N = 11
K = 6
COLORS = 12
CLAIM_ID = "n11-k6-q00r00-seventh-base-colorability-pilot"
SOURCE_CLAIM_ID = "n11-k6-q00r00-seventh-base-classification"
SOURCE_ARCHIVE_SHA256 = "dece0e924900b2bd751a62e82edca7e59f55e0c58a5bf92c5b9b196755646352"
SOURCE_CLASSIFICATION_STREAM_SHA256 = "932c4ed2ffc689ce5b5fe5cea07eec9876734159186df70b598b6f3ec316f6de"
SOURCE_RUN_ID = 30875846299
SOURCE_ARTIFACT_ID = 8879504727
SOURCE_CLASSIFIED_SHA = "bdcd88d18a01e383aa30aac401c083d8775e2ca2"
SOURCE_WORKFLOW_REVISION = "eb3f921983946b2ab8fa930fbec4f08c0133d3ac"
SOURCE_GOVERNANCE_COMMIT = "f9e44bf830096d967546f8f5e9f7d634c2ea718b"
SOURCE_STATUS_HEAD = "865f6e99567ffe48d040e9de9693026a129a76ef"
PILOT_CASES = [
    "q00r00-s026-t066",
    "q00r00-s028-t116",
    "q00r00-s028-t144",
    "q00r00-s028-t148",
    "q00r00-s028-t154",
    "q00r00-s030-t084",
    "q00r00-s030-t086",
    "q00r00-s031-t041",
    "q00r00-s033-t084",
    "q00r00-s034-t025",
    "q00r00-s034-t028",
    "q00r00-s034-t033",
    "q00r00-s034-t034",
    "q00r00-s034-t035",
    "q00r00-s035-t008",
]


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


def allowed(vertex: int, base: Iterable[int]) -> bool:
    return vertex.bit_count() % 2 == 0 and all(distance(vertex, point) <= K for point in base)


def reconstruct_trim(base: list[int]) -> tuple[list[int], list[tuple[int, int]], int]:
    vertices = [vertex for vertex in range(1 << N) if allowed(vertex, base)]
    edges: list[tuple[int, int]] = []
    incompatible = 0
    for index, left in enumerate(vertices):
        for right in vertices[index + 1 :]:
            separation = distance(left, right)
            if separation == K:
                edges.append((left, right))
            elif separation > K:
                incompatible += 1
    return vertices, edges, incompatible


def vertices_digest(vertices: list[int]) -> str:
    return sha256_bytes("".join(f"{vertex:03x}\n" for vertex in vertices).encode("ascii"))


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
    case_id: str,
    vertices: list[int],
    edges: list[tuple[int, int]],
    domains: dict[int, tuple[int, ...]],
) -> None:
    forward, _ = variable_maps(vertices, domains)
    variables, clauses = formula_counts(vertices, edges, domains)
    stream.write(f"c {case_id} canonical compact 12-color CNF\n")
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


def validate_source(root: Path) -> dict[str, object]:
    sums = root / "SHA256SUMS"
    if not sums.is_file():
        raise SystemExit("classification SHA256SUMS missing")
    listed: set[str] = set()
    for line in sums.read_text(encoding="ascii").splitlines():
        digest, relative = line.split("  ", 1)
        if relative in listed:
            raise SystemExit(f"duplicate classification checksum entry: {relative}")
        path = root / relative
        if not path.is_file() or sha256_file(path) != digest:
            raise SystemExit(f"classification checksum mismatch: {relative}")
        listed.add(relative)
    if len([path for path in root.rglob("*") if path.is_file()]) != 41:
        raise SystemExit("classification artifact does not contain exactly 41 files")
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    if summary.get("status") != "PASS":
        raise SystemExit("classification summary is not PASS")
    if summary.get("classification_stream_sha256") != SOURCE_CLASSIFICATION_STREAM_SHA256:
        raise SystemExit("classification stream hash changed")
    if summary.get("pilot_cases") != PILOT_CASES:
        raise SystemExit("classification pilot list changed")
    if summary.get("status_boundary") != {
        "all_grandchildren": "UNKNOWN",
        "n11-k6-full": "Gate 2 / OPEN",
        "q00": "UNKNOWN",
        "q00r00": "UNKNOWN",
        "q00r00_s000_through_s035": "UNKNOWN",
    }:
        raise SystemExit("classification status boundary changed")
    return summary


def find_orbit(root: Path, case_id: str) -> dict[str, object]:
    parent_id = case_id.rsplit("-t", 1)[0]
    child = json.loads((root / "children" / f"{parent_id}.json").read_text(encoding="utf-8"))
    if child.get("child_status") != "UNKNOWN" or child.get("refinement_reason") != "incomplete_sixth_base_screen_not_certified_obstruction":
        raise SystemExit(f"bad parent status boundary: {parent_id}")
    matches = [orbit for orbit in child["orbits"] if orbit.get("grandchild_id") == case_id]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one classification orbit for {case_id}")
    orbit = matches[0]
    if orbit.get("status") != "UNKNOWN" or orbit.get("raw_12color_cnf_proxy", {}).get("tier") != "PILOT":
        raise SystemExit(f"case is not an UNKNOWN PILOT: {case_id}")
    return orbit


def write_edges(path: Path, edges: list[tuple[int, int]]) -> None:
    with path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["left", "right"])
        writer.writerows((f"{left:03x}", f"{right:03x}") for left, right in edges)


def build_case(source_root: Path, output: Path, case_id: str) -> dict[str, object]:
    orbit = find_orbit(source_root, case_id)
    base = [int(value) for value in orbit["base"]]
    if len(base) != 7 or len(base) != len(set(base)):
        raise SystemExit(f"invalid seven-point base: {case_id}")
    vertices, edges, incompatible = reconstruct_trim(base)
    graph = orbit["graph"]
    if graph != {
        "vertices": len(vertices),
        "vertices_sha256": vertices_digest(vertices),
        "distance6_edges": len(edges),
        "incompatible_pairs": incompatible,
    }:
        raise SystemExit(f"classification graph mismatch: {case_id}")

    clique = deterministic_clique(vertices, edges)
    domains = allowed_colors(vertices, clique)
    variables, clauses = formula_counts(vertices, edges, domains)
    forward, reverse = variable_maps(vertices, domains)
    del forward

    case_dir = output / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    vertices_path = case_dir / f"{case_id}_vertices.txt"
    edges_path = case_dir / f"{case_id}_distance6_edges.csv"
    cnf_path = case_dir / f"{case_id}_12color.cnf"
    map_path = case_dir / f"{case_id}_variable_map.json"
    metadata_path = case_dir / f"{case_id}_metadata.json"
    vertices_path.write_text("".join(f"{vertex:03x}\n" for vertex in vertices), encoding="ascii", newline="")
    write_edges(edges_path, edges)
    with cnf_path.open("w", encoding="ascii", newline="") as stream:
        emit_cnf(stream, case_id, vertices, edges, domains)

    mapping = {
        "schema": "borsuk-q00r00-seventh-base-pilot-color-map-v1",
        "case_id": case_id,
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
        "schema": "borsuk-q00r00-seventh-base-pilot-instance-v1",
        "claim_id": CLAIM_ID,
        "case_id": case_id,
        "parent_child_id": case_id.rsplit("-t", 1)[0],
        "base": base,
        "representative": orbit["representative"],
        "orbit_size": orbit["orbit_size"],
        "classification_status": orbit["status"],
        "vertices": len(vertices),
        "edges": len(edges),
        "incompatible_pairs": incompatible,
        "colors": COLORS,
        "fixed_clique": clique,
        "fixed_clique_size": len(clique),
        "variables": variables,
        "clauses": clauses,
        "classification_vertices_sha256": graph["vertices_sha256"],
        "vertices_sha256": sha256_file(vertices_path),
        "edges_sha256": sha256_file(edges_path),
        "cnf_sha256": sha256_file(cnf_path),
        "variable_map_sha256": sha256_file(map_path),
        "result_state": "UNKNOWN",
        "interpretation": {
            "checked_sat": "proves this grandchild universal trim 12-colorable and closes only this grandchild",
            "checked_unsat": "proves only this grandchild universal trim non-12-colorable; the grandchild remains UNKNOWN and enters the certified eighth-base refinement frontier",
            "unknown": "no checked result; this pilot case remains incomplete",
            "parent_closure": "never implied by one pilot result",
        },
    }
    metadata_path.write_bytes(canonical_json_bytes(metadata))
    return metadata


def write_sha256sums(root: Path, paths: list[Path]) -> None:
    lines = [f"{sha256_file(path)}  {path.relative_to(root).as_posix()}" for path in sorted(paths)]
    (root / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="ascii")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--classification-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_source(args.classification_root)
    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)
    records = [build_case(args.classification_root, args.output, case_id) for case_id in PILOT_CASES]
    aggregate = {
        "schema": "borsuk-q00r00-seventh-base-pilot-instances-v1",
        "claim_id": CLAIM_ID,
        "source": {
            "classification_claim_id": SOURCE_CLAIM_ID,
            "classification_run_id": SOURCE_RUN_ID,
            "classification_artifact_id": SOURCE_ARTIFACT_ID,
            "classification_archive_sha256": SOURCE_ARCHIVE_SHA256,
            "classification_stream_sha256": SOURCE_CLASSIFICATION_STREAM_SHA256,
            "classified_source_sha": SOURCE_CLASSIFIED_SHA,
            "classification_workflow_revision": SOURCE_WORKFLOW_REVISION,
            "classification_governance_commit": SOURCE_GOVERNANCE_COMMIT,
            "classification_repository_head": SOURCE_STATUS_HEAD,
        },
        "case_count": len(records),
        "case_ids": PILOT_CASES,
        "cases": records,
        "totals": {
            "vertices_across_cases": sum(int(record["vertices"]) for record in records),
            "edges_across_cases": sum(int(record["edges"]) for record in records),
            "variables_across_cases": sum(int(record["variables"]) for record in records),
            "clauses_across_cases": sum(int(record["clauses"]) for record in records),
            "incompatible_pairs_across_cases": sum(int(record["incompatible_pairs"]) for record in records),
        },
        "status_boundary": {
            "pilot_grandchildren": "UNKNOWN until an individual checked SAT coloring exists",
            "proof_checked_unsat_grandchildren": "UNKNOWN and certified for eighth-base refinement",
            "sixth_base_parents": "UNKNOWN",
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
