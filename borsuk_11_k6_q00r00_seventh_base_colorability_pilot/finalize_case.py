#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CLAIM_ID = "n11-k6-q00r00-seventh-base-colorability-pilot"
SOURCE_CLASSIFICATION_ARCHIVE_SHA256 = "dece0e924900b2bd751a62e82edca7e59f55e0c58a5bf92c5b9b196755646352"
SOURCE_CLASSIFICATION_STREAM_SHA256 = "932c4ed2ffc689ce5b5fe5cea07eec9876734159186df70b598b6f3ec316f6de"
SOURCE_GOVERNANCE_COMMIT = "f9e44bf830096d967546f8f5e9f7d634c2ea718b"
SOURCE_REPOSITORY_HEAD = "865f6e99567ffe48d040e9de9693026a129a76ef"


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
    parser.add_argument("--checker-limit-seconds", type=int, required=True)
    parser.add_argument("--workflow-run-id", type=int, required=True)
    parser.add_argument("--workflow-run-attempt", type=int, required=True)
    parser.add_argument("--workflow-sha", required=True)
    parser.add_argument("--workflow-ref", required=True)
    args = parser.parse_args()

    metadata_path = args.instance_dir / "cases" / args.case_id / f"{args.case_id}_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    parent_id = metadata["parent_child_id"]
    if args.state == "SAT_CHECKED_COLORING":
        effect = {
            "grandchild_status": "12_COLORABLE",
            "certificate_class": "CLOSED_GRANDCHILD",
            "branch_action": "CLOSE_GRANDCHILD_ONLY",
            "parent_child_status": "UNKNOWN",
            "statement": "A directly checked coloring proves this complete seven-point universal trim 12-colorable.",
        }
    elif args.state == "PROOF_CHECKED_UNSAT":
        effect = {
            "grandchild_status": "UNKNOWN",
            "certificate_class": "CERTIFIED_EIGHTH_BASE_REFINEMENT_FRONTIER",
            "branch_action": "CLASSIFY_COMPATIBLE_EIGHTH_VERTICES",
            "parent_child_status": "UNKNOWN",
            "statement": "The checked proof rejects only this universal trim. Legal subsets exclude incompatible pairs, so the grandchild remains unresolved but eighth-base refinement is certified.",
        }
    else:
        effect = {
            "grandchild_status": "UNKNOWN",
            "certificate_class": "INCOMPLETE_PILOT_CASE",
            "branch_action": "PILOT_INCOMPLETE",
            "parent_child_status": "UNKNOWN",
            "statement": "No checked SAT coloring or checked UNSAT proof was obtained.",
        }

    files: dict[str, dict[str, object]] = {}
    for path in sorted(args.case_dir.iterdir()):
        if path.is_file() and path.name not in {"certificate-result.json", "artifact-sha256.txt", "finalize.out"}:
            files[path.name] = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}

    def read_text(name: str) -> str:
        path = args.case_dir / name
        return path.read_text(encoding="utf-8").strip() if path.is_file() else "MISSING"

    def read_recorded_sha256(name: str) -> str:
        text = read_text(name)
        return text.split()[0] if text != "MISSING" and text.split() else "MISSING"

    result = {
        "schema": "borsuk-q00r00-seventh-base-pilot-result-v1",
        "claim_id": CLAIM_ID,
        "case_id": args.case_id,
        "parent_child_id": parent_id,
        "certificate_state": args.state,
        "source_classification": {
            "archive_sha256": SOURCE_CLASSIFICATION_ARCHIVE_SHA256,
            "classification_stream_sha256": SOURCE_CLASSIFICATION_STREAM_SHA256,
            "governance_commit": SOURCE_GOVERNANCE_COMMIT,
            "repository_head": SOURCE_REPOSITORY_HEAD,
        },
        "instance": {
            "base": metadata["base"],
            "representative": metadata["representative"],
            "orbit_size": metadata["orbit_size"],
            "cnf_sha256": metadata["cnf_sha256"],
            "variable_map_sha256": metadata["variable_map_sha256"],
            "vertices_sha256": metadata["vertices_sha256"],
            "edges_sha256": metadata["edges_sha256"],
            "vertices": metadata["vertices"],
            "edges": metadata["edges"],
            "incompatible_pairs": metadata["incompatible_pairs"],
            "variables": metadata["variables"],
            "clauses": metadata["clauses"],
        },
        "execution": {
            "workflow_run_id": args.workflow_run_id,
            "workflow_run_attempt": args.workflow_run_attempt,
            "workflow_sha": args.workflow_sha,
            "workflow_ref": args.workflow_ref,
            "artifact_id": "PENDING_POST_UPLOAD_BINDING",
        },
        "toolchain": {
            "kissat_version": read_text("kissat-version.txt"),
            "kissat_binary_sha256": read_recorded_sha256("kissat-binary.sha256"),
            "drat_trim_revision": read_text("drat-trim-revision.txt"),
            "drat_trim_binary_sha256": read_recorded_sha256("drat-trim-binary.sha256"),
        },
        "solver": {
            "name": "Kissat",
            "version": "4.0.0",
            "exit_status": args.solver_exit_status,
            "limit_seconds": args.solver_limit_seconds,
            "started_utc": args.started,
            "finished_utc": args.finished,
        },
        "checker": {
            "name": "drat-trim",
            "limit_seconds": args.checker_limit_seconds,
            "empty_proof_negative_control_required": True,
        },
        "mathematical_effect": effect,
        "files": files,
        "parent_status_changed": False,
        "q00r00_status_changed": False,
        "repository_status_changed": False,
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
