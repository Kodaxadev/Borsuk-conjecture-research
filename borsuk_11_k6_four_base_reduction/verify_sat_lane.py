#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from build_instance import (
    build_graph,
    fixed_clique_for,
    get_case,
    instance_metadata,
    mapping_document,
    write_cnf,
)
from verify_model import self_test

EXPECTED = {
    "case_id": "q00",
    "representative_case": "a3b3_13",
    "vertices": 436,
    "edges": 39600,
    "variables": 5232,
    "clauses": 504422,
    "fixed_clique": [0, 63, 455, 748, 858, 1241, 1450, 1635, 1686, 1805],
    "cnf_sha256": "b07c254b71ae0964851afb8dd9f7fa8a728433e27ae76a327e5c10a6e6e7df55",
    "variable_map_sha256": "742bf72f1ae30dc207e22a0c7efe1033ee6e4a5361987ed9e2f8ed3e2b85ed7d",
}


def main() -> int:
    case = get_case("q00")
    vertices, edges = build_graph(case)
    fixed_clique = fixed_clique_for(vertices)
    metadata = instance_metadata(case, vertices, edges, fixed_clique)

    for field in ("case_id", "representative_case", "vertices", "edges", "variables", "clauses", "fixed_clique"):
        if metadata[field] != EXPECTED[field]:
            raise SystemExit(f"q00 {field}: expected {EXPECTED[field]!r}, got {metadata[field]!r}")

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        cnf_path = root / "q00_12color.cnf"
        map_path = root / "q00_variable_map.json"
        mapping = mapping_document(vertices, fixed_clique, int(metadata["clauses"]))
        map_path.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        cnf_hash = write_cnf(cnf_path, vertices, edges, fixed_clique)
        map_hash = hashlib.sha256(map_path.read_bytes()).hexdigest()
        if cnf_hash != EXPECTED["cnf_sha256"]:
            raise SystemExit(f"q00 CNF hash mismatch: {cnf_hash}")
        if map_hash != EXPECTED["variable_map_sha256"]:
            raise SystemExit(f"q00 variable-map hash mismatch: {map_hash}")

    self_test()
    print("PASS: deterministic q00 SAT lane")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
