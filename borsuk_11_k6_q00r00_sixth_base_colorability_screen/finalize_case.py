#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("state", choices=["SAT_CHECKED_COLORING", "PROOF_CHECKED_UNSAT", "UNKNOWN"])
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--instance-dir", type=Path, required=True)
    parser.add_argument("--solver-exit-status", type=int, required=True)
    parser.add_argument("--started", required=True)
    parser.add_argument("--finished", required=True)
    parser.add_argument("--solver-limit-seconds", type=int, required=True)
    args = parser.parse_args()

    metadata_path = args.instance_dir / "cases" / args.case_id / f"{args.case_id}_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if args.state == "SAT_CHECKED_COLORING":
        effect = {
            "child_status": "12_COLORABLE",
            "branch_action": "CLOSE_BRANCH",
            "statement": "A directly checked coloring proves the entire universal trim 12-colorable.",
        }
    elif args.state == "PROOF_CHECKED_UNSAT":
        effect = {
            "child_status": "UNKNOWN",
            "branch_action": "SEVENTH_BASE_REFINEMENT_REQUIRED",
            "statement": "The checked proof rejects only the universal trim. Legal subsets exclude incompatible pairs, so the child remains unresolved.",
        }
    else:
        effect = {
            "child_status": "UNKNOWN",
            "branch_action": "SCREEN_INCOMPLETE",
            "statement": "No checked SAT coloring or checked UNSAT proof was obtained.",
        }

    files: dict[str, dict[str, object]] = {}
    for path in sorted(args.case_dir.iterdir()):
        if path.is_file() and path.name not in {"certificate-result.json", "artifact-sha256.txt", "finalize.out"}:
            files[path.name] = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}

    result = {
        "schema": "borsuk-q00r00-sixth-base-colorability-result-v1",
        "claim_id": "n11-k6-q00r00-sixth-base-colorability-screen",
        "case_id": args.case_id,
        "certificate_state": args.state,
        "source_child_trim_commit": "aad27339d6e689afdb50dbb8c280a76230b915fc",
        "source_child_trim_archive_sha256": "a1862053e19a4341b941e62181c180805fb59a7969241d473705635dd04d0505",
        "instance": {
            "cnf_sha256": metadata["cnf_sha256"],
            "variable_map_sha256": metadata["variable_map_sha256"],
            "vertices": metadata["vertices"],
            "edges": metadata["edges"],
            "incompatible_pairs": metadata["incompatible_pairs"],
            "variables": metadata["variables"],
            "clauses": metadata["clauses"],
        },
        "solver": {
            "name": "Kissat",
            "version": "4.0.0",
            "exit_status": args.solver_exit_status,
            "limit_seconds": args.solver_limit_seconds,
            "started_utc": args.started,
            "finished_utc": args.finished,
        },
        "mathematical_effect": effect,
        "files": files,
        "repository_status_changed": False,
        "parent_status_changed": False,
    }
    result_path = args.case_dir / "certificate-result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    all_files = sorted(path for path in args.case_dir.iterdir() if path.is_file() and path.name not in {"artifact-sha256.txt", "finalize.out"})
    (args.case_dir / "artifact-sha256.txt").write_text(
        "\n".join(f"{sha256_file(path)}  {path.name}" for path in all_files) + "\n",
        encoding="ascii",
    )
    print(json.dumps({"case_id": args.case_id, "certificate_state": args.state, **effect}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
