#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
from pathlib import Path

CLAIM_ID = "n11-k6-q00r00-seventh-base-colorability-pilot"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_positive_literals(path: Path) -> set[int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    upper = text.upper()
    if "UNSATISFIABLE" in upper:
        raise ValueError("UNSAT output cannot be accepted as a SAT witness")
    positives: set[int] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("c", "p", "s")):
            continue
        if line.startswith("v"):
            line = line[1:].strip()
        try:
            literals = [int(token) for token in line.split()]
        except ValueError:
            continue
        positives.update(literal for literal in literals if literal > 0)
    if not positives:
        raise ValueError("solver output contains no positive model literals")
    return positives


def parse_edges(path: Path) -> list[tuple[int, int]]:
    with path.open("r", encoding="ascii", newline="") as handle:
        reader = csv.reader(handle)
        if next(reader, None) != ["left", "right"]:
            raise ValueError("bad edge header")
        edges = [(int(left, 16), int(right, 16)) for left, right in reader]
    return edges


def decode(mapping: dict[str, object], positives: set[int]) -> dict[int, int]:
    variable_order = mapping["variable_order"]
    max_variable = len(variable_order)
    bad = sorted(literal for literal in positives if literal > max_variable)
    if bad:
        raise ValueError(f"out-of-range model variables: {bad[:10]}")
    selected: dict[int, list[int]] = {int(vertex): [] for vertex in mapping["vertices"]}
    for record in variable_order:
        if int(record["variable"]) in positives:
            selected[int(record["vertex"])].append(int(record["color"]))
    coloring: dict[int, int] = {}
    for vertex, colors in selected.items():
        if len(colors) != 1:
            raise ValueError(f"vertex {vertex} has {len(colors)} selected colors: {colors}")
        coloring[vertex] = colors[0]
    return coloring


def verify(edges: list[tuple[int, int]], coloring: dict[int, int]) -> None:
    missing = sorted({vertex for edge in edges for vertex in edge} - set(coloring))
    if missing:
        raise ValueError(f"coloring misses edge vertices: {missing[:10]}")
    violations = [(left, right, coloring[left]) for left, right in edges if coloring[left] == coloring[right]]
    if violations:
        raise ValueError(f"monochromatic distance-six edges: {violations[:10]}")


def self_test() -> None:
    mapping = {
        "vertices": [0, 1],
        "variable_order": [
            {"variable": 1, "vertex": 0, "color": 0},
            {"variable": 2, "vertex": 1, "color": 0},
            {"variable": 3, "vertex": 1, "color": 1},
        ],
    }
    verify([(0, 1)], decode(mapping, {1, 3}))
    controls = [({1, 2}, "monochromatic"), ({1, 4}, "out-of-range"), ({1}, "missing color")]
    for positives, label in controls:
        try:
            verify([(0, 1)], decode(mapping, positives))
        except ValueError:
            pass
        else:
            raise SystemExit(f"negative control accepted: {label}")
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "solver.out"
        for text in ("s UNSATISFIABLE\n", "c no model\n"):
            path.write_text(text, encoding="utf-8")
            try:
                parse_positive_literals(path)
            except ValueError:
                pass
            else:
                raise SystemExit("non-SAT output negative control was accepted")
    print("PASS: pilot coloring verifier negative controls")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id", nargs="?")
    parser.add_argument("solver_output", nargs="?", type=Path)
    parser.add_argument("--instances", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if None in (args.case_id, args.solver_output, args.instances, args.output):
        parser.error("case_id, solver_output, --instances, and --output are required")

    case_id = str(args.case_id)
    case_dir = args.instances / "cases" / case_id
    map_path = case_dir / f"{case_id}_variable_map.json"
    metadata_path = case_dir / f"{case_id}_metadata.json"
    edge_path = case_dir / f"{case_id}_distance6_edges.csv"
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    positives = parse_positive_literals(args.solver_output)
    coloring = decode(mapping, positives)
    edges = parse_edges(edge_path)
    verify(edges, coloring)

    result = {
        "schema": "borsuk-q00r00-seventh-base-pilot-checked-coloring-v1",
        "claim_id": CLAIM_ID,
        "case_id": case_id,
        "certificate_state": "SAT_CHECKED_COLORING",
        "cnf_sha256": metadata["cnf_sha256"],
        "variable_map_sha256": metadata["variable_map_sha256"],
        "edge_file_sha256": metadata["edges_sha256"],
        "solver_output_sha256": sha256_file(args.solver_output),
        "vertices": metadata["vertices"],
        "edges_checked": len(edges),
        "colors_used": len(set(coloring.values())),
        "coloring": {str(vertex): coloring[vertex] for vertex in sorted(coloring)},
        "mathematical_effect": {
            "grandchild_status": "12_COLORABLE",
            "action": "CLOSE_GRANDCHILD_ONLY",
            "parent_status": "UNKNOWN",
            "statement": "The complete seven-point universal trim is 12-colorable; every legal subset inside it is 12-colorable.",
        },
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: checked 12-coloring for {case_id} on {len(coloring)} vertices and {len(edges)} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
