#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
from pathlib import Path


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
        tokens = line.split()
        try:
            literals = [int(token) for token in tokens]
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
        return [(int(left, 16), int(right, 16)) for left, right in reader]


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
    coloring = decode(mapping, {1, 3})
    verify([(0, 1)], coloring)
    for positives in ({1, 2}, {1, 4}, set()):
        try:
            if positives:
                candidate = decode(mapping, positives)
                verify([(0, 1)], candidate)
            else:
                raise ValueError("empty")
        except ValueError:
            pass
        else:
            raise SystemExit("negative control was accepted")
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "solver.out"
        path.write_text("s UNSATISFIABLE\n", encoding="utf-8")
        try:
            parse_positive_literals(path)
        except ValueError:
            pass
        else:
            raise SystemExit("UNSAT negative control was accepted")
    print("PASS: coloring verifier negative controls")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id", nargs="?")
    parser.add_argument("solver_output", nargs="?", type=Path)
    parser.add_argument("--trim-root", type=Path)
    parser.add_argument("--instances", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if None in (args.case_id, args.solver_output, args.trim_root, args.instances, args.output):
        parser.error("case_id, solver_output, --trim-root, --instances, and --output are required")

    case_id = str(args.case_id)
    map_path = args.instances / "cases" / case_id / f"{case_id}_variable_map.json"
    metadata_path = args.instances / "cases" / case_id / f"{case_id}_metadata.json"
    edge_path = args.trim_root / "children" / case_id / "distance6_edges.csv"
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    positives = parse_positive_literals(args.solver_output)
    coloring = decode(mapping, positives)
    edges = parse_edges(edge_path)
    verify(edges, coloring)

    result = {
        "schema": "borsuk-q00r00-sixth-base-checked-coloring-v1",
        "claim_id": "n11-k6-q00r00-sixth-base-colorability-screen",
        "case_id": case_id,
        "certificate_state": "SAT_CHECKED_COLORING",
        "cnf_sha256": metadata["cnf_sha256"],
        "variable_map_sha256": metadata["variable_map_sha256"],
        "solver_output_sha256": sha256_file(args.solver_output),
        "vertices": metadata["vertices"],
        "edges_checked": len(edges),
        "colors_used": len(set(coloring.values())),
        "coloring": {str(vertex): coloring[vertex] for vertex in sorted(coloring)},
        "mathematical_effect": "The complete universal trim is 12-colorable; every legal subset inside it is 12-colorable, so this child branch closes.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: checked 12-coloring for {case_id} on {len(coloring)} vertices and {len(edges)} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
