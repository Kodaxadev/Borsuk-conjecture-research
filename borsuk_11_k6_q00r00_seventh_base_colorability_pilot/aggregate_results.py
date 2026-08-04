#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CLAIM_ID = "n11-k6-q00r00-seventh-base-colorability-pilot"
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workflow-run-id", type=int, required=True)
    parser.add_argument("--workflow-run-attempt", type=int, required=True)
    parser.add_argument("--workflow-sha", required=True)
    parser.add_argument("--workflow-ref", required=True)
    args = parser.parse_args()

    records: dict[str, dict[str, object]] = {}
    for path in args.results_root.rglob("certificate-result.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        case_id = str(record.get("case_id"))
        if case_id in records:
            raise SystemExit(f"duplicate case result: {case_id}")
        if record.get("claim_id") != CLAIM_ID:
            raise SystemExit(f"wrong claim ID in {path}")
        if record.get("execution", {}).get("workflow_run_id") != args.workflow_run_id:
            raise SystemExit(f"mixed workflow run in {path}")
        if record.get("execution", {}).get("workflow_run_attempt") != args.workflow_run_attempt:
            raise SystemExit(f"mixed workflow attempt in {path}")
        if record.get("execution", {}).get("workflow_sha") != args.workflow_sha:
            raise SystemExit(f"mixed workflow SHA in {path}")
        if record.get("execution", {}).get("workflow_ref") != args.workflow_ref:
            raise SystemExit(f"mixed workflow ref in {path}")
        records[case_id] = record

    if set(records) != set(PILOT_CASES):
        missing = sorted(set(PILOT_CASES) - set(records))
        extra = sorted(set(records) - set(PILOT_CASES))
        raise SystemExit(f"pilot result coverage mismatch; missing={missing}, extra={extra}")

    ordered = [records[case_id] for case_id in PILOT_CASES]
    closed = [record["case_id"] for record in ordered if record["certificate_state"] == "SAT_CHECKED_COLORING"]
    frontier = [record["case_id"] for record in ordered if record["certificate_state"] == "PROOF_CHECKED_UNSAT"]
    incomplete = [record["case_id"] for record in ordered if record["certificate_state"] == "UNKNOWN"]
    if len(closed) + len(frontier) + len(incomplete) != len(PILOT_CASES):
        raise SystemExit("unknown certificate state in pilot results")

    parent_ids = sorted({str(record["parent_child_id"]) for record in ordered})
    summary = {
        "schema": "borsuk-q00r00-seventh-base-pilot-summary-v1",
        "claim_id": CLAIM_ID,
        "workflow": {
            "run_id": args.workflow_run_id,
            "run_attempt": args.workflow_run_attempt,
            "sha": args.workflow_sha,
            "ref": args.workflow_ref,
        },
        "case_count": len(PILOT_CASES),
        "case_ids": PILOT_CASES,
        "result_counts": {
            "SAT_CHECKED_COLORING": len(closed),
            "PROOF_CHECKED_UNSAT": len(frontier),
            "UNKNOWN": len(incomplete),
        },
        "closed_grandchildren": closed,
        "certified_eighth_base_refinement_frontier": frontier,
        "incomplete_pilot_cases": incomplete,
        "affected_sixth_base_parents": parent_ids,
        "parent_closure_count": 0,
        "parent_closure_not_implied": True,
        "mathematical_status": {
            "sixth_base_parents": "UNKNOWN",
            "proof_checked_unsat_grandchildren": "UNKNOWN with certified eighth-base refinement frontier status",
            "unknown_pilot_cases": "UNKNOWN",
            "q00r00": "UNKNOWN",
            "q00": "UNKNOWN",
            "n11-k6-full": "Gate 2 / OPEN",
        },
        "repository_effect": "ELIGIBLE_FOR_POST_UPLOAD_EXECUTION_BINDING_ONLY",
        "cases": ordered,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    summary_path = args.output / "pilot-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = []
    for path in sorted(args.results_root.rglob("*")):
        if path.is_file():
            manifest.append({
                "path": path.relative_to(args.results_root).as_posix(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            })
    (args.output / "result-file-manifest.json").write_text(
        json.dumps({"schema": "borsuk-q00r00-seventh-base-pilot-result-files-v1", "files": manifest}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    sums = [
        f"{sha256_file(path)}  {path.name}"
        for path in sorted(args.output.iterdir())
        if path.is_file() and path.name != "SHA256SUMS"
    ]
    (args.output / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="ascii")
    print(json.dumps({
        "status": "PASS",
        "case_count": len(PILOT_CASES),
        "result_counts": summary["result_counts"],
        "pilot_summary_sha256": sha256_file(summary_path),
        "parent_closure_count": 0,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
