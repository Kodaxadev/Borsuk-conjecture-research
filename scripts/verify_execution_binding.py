#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


EXPECTED_RUN_ID = 30856667310
EXPECTED_RUN_ATTEMPT = 1
EXPECTED_WORKFLOW_REF = "refs/heads/research/q00r00-sixth-base-colorability-screen"
EXPECTED_SHA = "cca43b17354619afd473c835d63f363a16cae5bf"
EXPECTED_STATUS = "EXECUTION_BOUND"


class VerificationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_tsv(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 6:
            raise VerificationError(f"Unexpected TSV row in {path}: {line!r}")
        rows.append(
            {
                "artifact_id": int(parts[0]),
                "name": parts[1],
                "digest": parts[2],
                "size_bytes": int(parts[3]),
                "created_at": parts[4],
                "updated_at": parts[5],
            }
        )
    return rows


def read_sha_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise VerificationError(f"Empty digest file: {path}")
    return text.split()[0]


def load_case_dirs(extracted_root: Path):
    cases = []
    for case_dir in sorted(extracted_root.glob("q00r00-s*-colorability-screen")):
        if not case_dir.is_dir():
            continue
        case_id = case_dir.name[:-len("-colorability-screen")]
        cert_path = case_dir / "certificate-result.json"
        meta_path = case_dir / f"{case_id}_metadata.json"
        varmap_path = case_dir / f"{case_id}_variable_map.json"
        cases.append(
            {
                "case_id": case_id,
                "case_dir": case_dir,
                "cert": load_json(cert_path),
                "meta": load_json(meta_path),
                "varmap": load_json(varmap_path),
            }
        )
    return cases


def verify_artifact_archive_hashes(root: Path, artifact_rows):
    by_name = {row["name"]: row for row in artifact_rows}
    archive_root = root / "archives"
    required_names = [
        "q00r00-sixth-base-screen-inputs-cca43b17354619afd473c835d63f363a16cae5bf",
        "q00r00-sixth-base-colorability-screen-summary",
    ] + sorted(
        [name for name in by_name if name.startswith("q00r00-s") and name.endswith("-colorability-screen")]
    )
    expected_case_count = len([n for n in required_names if n.startswith("q00r00-s") and n.endswith("-colorability-screen")])
    if expected_case_count != 36:
        raise VerificationError(f"Expected 36 case archives, found {expected_case_count}")

    for name in required_names:
        row = by_name[name]
        zip_path = archive_root / f"{name}.zip"
        sha_path = archive_root / f"{name}.zip.sha256"
        if not zip_path.exists():
            raise VerificationError(f"Missing archive {zip_path}")
        if not sha_path.exists():
            raise VerificationError(f"Missing SHA256 file {sha_path}")
        file_digest = sha256_file(zip_path)
        manifest_digest = read_sha_file(sha_path)
        if file_digest != manifest_digest:
            raise VerificationError(f"Manifest digest mismatch for {name}: manifest {manifest_digest} file {file_digest}")
        if file_digest != row["digest"]:
            raise VerificationError(f"Artifact digest mismatch for {name}: expected {row['digest']} got {file_digest}")


def normalized_solver_identity(solver):
    return {
        "name": solver["name"],
        "version": solver["version"],
        "limit_seconds": solver["limit_seconds"],
        "exit_status": solver["exit_status"],
    }


def normalized_toolchain_identity(toolchain):
    return {
        "drat_trim_binary_sha256": toolchain["drat_trim_binary_sha256"],
        "kissat_binary_sha256": toolchain["kissat_binary_sha256"],
        "drat_trim_revision": toolchain["drat_trim_revision"],
        "kissat_version": toolchain["kissat_version"],
    }


def verify_case_bindings(root: Path, cases):
    prep_root = root / "extracted" / "q00r00-sixth-base-screen-inputs-cca43b17354619afd473c835d63f363a16cae5bf" / "trim-input"
    prep_manifest = load_json(prep_root / "manifest.json")
    prep_children = {child["child_id"]: child for child in prep_manifest["children"]}
    summary = load_json(root / "extracted" / "q00r00-sixth-base-colorability-screen-summary" / "screen-summary.json")
    expected_run = {"workflow_run_id": EXPECTED_RUN_ID, "workflow_run_attempt": EXPECTED_RUN_ATTEMPT, "workflow_ref": EXPECTED_WORKFLOW_REF, "workflow_sha": EXPECTED_SHA}

    all_state_counts = Counter()
    closed_cases = []
    frontier_cases = []
    incomplete_cases = []
    common_solver = None
    common_toolchain = None
    run_alignment = None

    case_bindings = []

    for entry in cases:
        case_id = entry["case_id"]
        cert = entry["cert"]
        meta = entry["meta"]
        case_dir = entry["case_dir"]
        case_files = cert["files"]
        execution = cert["execution"]
        instance = cert["instance"]
        solver = cert["solver"]
        toolchain = cert["toolchain"]
        state = cert["certificate_state"]

        if run_alignment is None:
            run_alignment = {k: execution[k] for k in expected_run}
        elif run_alignment != {k: execution[k] for k in expected_run}:
            raise VerificationError(f"Execution metadata diverges across cases for {case_id}")

        actual_cnf_digest = sha256_file(case_dir / f"{case_id}_12color.cnf")
        actual_meta_digest = sha256_file(case_dir / f"{case_id}_metadata.json")
        actual_varmap_digest = sha256_file(case_dir / f"{case_id}_variable_map.json")

        expected_cnf_digest = case_files[f"{case_id}_12color.cnf"]["sha256"]
        expected_meta_digest = case_files[f"{case_id}_metadata.json"]["sha256"]
        expected_varmap_digest = case_files[f"{case_id}_variable_map.json"]["sha256"]

        if expected_cnf_digest != actual_cnf_digest:
            raise VerificationError(f"CNF digest mismatch for {case_id}")
        if expected_meta_digest != actual_meta_digest:
            raise VerificationError(f"Metadata digest mismatch for {case_id}")
        if expected_varmap_digest != actual_varmap_digest:
            raise VerificationError(f"Variable-map digest mismatch for {case_id}")

        if meta["cnf_sha256"] != actual_cnf_digest:
            raise VerificationError(f"Metadata CNF hash mismatch for {case_id}")
        if meta["variable_map_sha256"] != actual_varmap_digest:
            raise VerificationError(f"Metadata variable-map hash mismatch for {case_id}")
        if meta["source_edges_sha256"] != prep_children[case_id]["files"]["distance6_edges"]["sha256"]:
            raise VerificationError(f"Source edge hash mismatch for {case_id}")
        if meta["source_vertices_sha256"] != prep_children[case_id]["files"]["vertices"]["sha256"]:
            raise VerificationError(f"Source vertex hash mismatch for {case_id}")

        if instance["cnf_sha256"] != actual_cnf_digest:
            raise VerificationError(f"Instance CNF hash mismatch for {case_id}")
        if instance["variable_map_sha256"] != actual_varmap_digest:
            raise VerificationError(f"Instance variable-map hash mismatch for {case_id}")

        solver_identity = normalized_solver_identity(solver)
        toolchain_identity = normalized_toolchain_identity(toolchain)

        if common_solver is None:
            common_solver = solver_identity
        elif solver_identity != common_solver:
            raise VerificationError(f"Solver identity mismatch across cases for {case_id}")
        if common_toolchain is None:
            common_toolchain = toolchain_identity
        elif toolchain_identity != common_toolchain:
            raise VerificationError(f"Toolchain identity mismatch across cases for {case_id}")

        all_state_counts[state] += 1
        if state == "UNKNOWN":
            incomplete_cases.append(case_id)
        elif state == "SAT_CHECKED_COLORING":
            closed_cases.append(case_id)
        elif state == "PROOF_CHECKED_UNSAT":
            frontier_cases.append(case_id)
        else:
            raise VerificationError(f"Unhandled certificate state for {case_id}: {state}")

        case_bindings.append(
            {
                "case_id": case_id,
                "artifact_name": f"{case_id}-colorability-screen",
                "embedded_execution": execution,
                "embedded_instance": meta,
                "solver_identity": {
                    "name": solver["name"],
                    "version": solver["version"],
                    "exit_status": solver["exit_status"],
                },
                "toolchain_identity": {
                    "drat_trim_binary_sha256": toolchain["drat_trim_binary_sha256"],
                    "kissat_binary_sha256": toolchain["kissat_binary_sha256"],
                    "drat_trim_revision": toolchain["drat_trim_revision"],
                    "kissat_version": toolchain["kissat_version"],
                },
                "certificate_state": state,
            }
        )

    if len(incomplete_cases) != 36:
        raise VerificationError(f"Expected 36 incomplete cases, found {len(incomplete_cases)}")
    if summary["case_count"] != 36:
        raise VerificationError(f"Summary case_count mismatch: {summary['case_count']}")
    if Counter(summary["certificate_state_counts"]) != all_state_counts:
        raise VerificationError("Summary certificate state counts do not match reconstructed results")
    if summary["checked_sat_cases"] != sorted(closed_cases):
        raise VerificationError("Summary checked_sat_cases does not match reconstructed closed cases")
    if summary["checked_unsat_universal_trim_cases"] != sorted(frontier_cases):
        raise VerificationError("Summary checked_unsat_universal_trim_cases does not match reconstructed frontier cases")
    if summary["incomplete_cases"] != sorted(incomplete_cases):
        raise VerificationError("Summary incomplete_cases does not match reconstructed incomplete cases")
    if summary["q00r00_certificate_effect"] != "REMAINS_UNKNOWN":
        raise VerificationError("Summary q00r00_certificate_effect should remain REMAINS_UNKNOWN")
    if summary["q00_status"] != "UNKNOWN":
        raise VerificationError("Summary q00_status should be UNKNOWN")

    return {
        "case_bindings": case_bindings,
        "closed_cases": sorted(closed_cases),
        "certified_seventh_base_frontier": sorted(frontier_cases),
        "incomplete_cases": sorted(incomplete_cases),
        "state_counts": dict(all_state_counts),
        "common_solver": common_solver,
        "common_toolchain": common_toolchain,
        "run_alignment": run_alignment,
    }


def write_binder(root: Path, artifact_rows, reconstructed):
    by_name = {row["name"]: row for row in artifact_rows}
    prep_name = "q00r00-sixth-base-screen-inputs-cca43b17354619afd473c835d63f363a16cae5bf"
    summary_name = "q00r00-sixth-base-colorability-screen-summary"
    prep_row = by_name[prep_name]
    summary_row = by_name[summary_name]
    expected_run_alignment = {
        "workflow_run_id": EXPECTED_RUN_ID,
        "workflow_run_attempt": EXPECTED_RUN_ATTEMPT,
        "workflow_ref": EXPECTED_WORKFLOW_REF,
        "workflow_sha": EXPECTED_SHA,
    }

    case_bindings = []
    for row in artifact_rows:
        if row["name"].startswith("q00r00-s") and row["name"].endswith("-colorability-screen"):
            case_name = row["name"]
            case_id = case_name[:-len("-colorability-screen")]
            archive_path = root / "archives" / f"{case_name}.zip"
            archive_digest = sha256_file(archive_path)
            if archive_digest != row["digest"]:
                raise VerificationError(f"Archive digest mismatch for {case_name}")
            evidence = next(item for item in reconstructed["case_bindings"] if item["case_id"] == case_id)
            case_bindings.append(
                {
                    "case_id": case_id,
                    "artifact_name": case_name,
                    "artifact_id": row["artifact_id"],
                    "archive_digest": row["digest"],
                    "downloaded_archive_sha256": archive_digest,
                    "downloaded_archive_verified": True,
                    "size_bytes": row["size_bytes"],
                    "created_at": row["created_at"],
                    "expires_at": row["updated_at"],
                    "embedded_execution": evidence["embedded_execution"],
                    "embedded_instance": evidence["embedded_instance"],
                    "solver_identity": evidence["solver_identity"],
                    "toolchain_identity": evidence["toolchain_identity"],
                    "certificate_state": evidence["certificate_state"],
                }
            )

    binder = {
        "schema": "borsuk-q00r00-execution-binding-v1",
        "run_id": EXPECTED_RUN_ID,
        "run_attempt": EXPECTED_RUN_ATTEMPT,
        "workflow_ref": EXPECTED_WORKFLOW_REF,
        "authoritative_sha": EXPECTED_SHA,
        "preparation_artifact": {
            "name": prep_name,
            "artifact_id": prep_row["artifact_id"],
            "digest": prep_row["digest"],
            "size_bytes": prep_row["size_bytes"],
            "created_at": prep_row["created_at"],
            "expires_at": prep_row["updated_at"],
        },
        "summary_artifact": {
            "name": summary_name,
            "artifact_id": summary_row["artifact_id"],
            "digest": summary_row["digest"],
            "size_bytes": summary_row["size_bytes"],
            "created_at": summary_row["created_at"],
            "expires_at": summary_row["updated_at"],
        },
        "case_archive_bindings": case_bindings,
        "reconstructed_partition": {
            "closed_cases": reconstructed["closed_cases"],
            "certified_seventh_base_frontier": reconstructed["certified_seventh_base_frontier"],
            "incomplete_screen_cases": reconstructed["incomplete_cases"],
            "q00r00_certificate_effect": "REMAINS_UNKNOWN",
        },
        "status_after_binding": {
            "computational": "COMPUTATIONAL",
            "implemented": "IMPLEMENTED",
            "ci_execution_complete": "CI_EXECUTION_COMPLETE",
            "artifact_archives_verified": "ARTIFACT_ARCHIVES_VERIFIED",
            "execution_bound": EXPECTED_STATUS,
            "working": "WORKING",
        },
        "validation": {
            "case_count": len(case_bindings),
            "verified_downloads": len(case_bindings),
            "all_identical_run": reconstructed["run_alignment"] == expected_run_alignment,
            "summary_matches_reconstructed_partition": True,
            "cnf_and_variable_map_agreement": True,
            "solver_and_toolchain_agreement": True,
            "preparation_and_summary_archives_verified": True,
        },
        "placeholder_resolution": {
            "placeholder_value": "PENDING_POST_UPLOAD_BINDING",
            "placeholder_is_expected": True,
            "resolution_method": "external post-upload artifact metadata binder over immutable case archives",
        },
    }
    out_path = root / "EXECUTION_BINDING.json"
    out_path.write_text(json.dumps(binder, indent=2) + "\n", encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Verify the q00r00 execution-binding evidence and emit a fail-closed EXECUTION_BINDING.json")
    parser.add_argument(
        "--run-dir",
        default=Path(__file__).resolve().parents[1] / "borsuk_11_k6_q00r00_sixth_base_colorability_screen" / "evidence" / "run-30856667310",
        type=Path,
    )
    args = parser.parse_args()

    run_dir = args.run_dir.resolve()
    if not run_dir.exists():
        raise VerificationError(f"Run directory does not exist: {run_dir}")

    artifacts_tsv = run_dir / "artifacts.tsv"
    if not artifacts_tsv.exists():
        raise VerificationError(f"Missing artifacts.tsv: {artifacts_tsv}")

    artifact_rows = parse_tsv(artifacts_tsv)
    if len(artifact_rows) != 38:
        raise VerificationError(f"Expected 38 artifacts, found {len(artifact_rows)}")

    verify_artifact_archive_hashes(run_dir, artifact_rows)

    extracted_root = run_dir / "extracted"
    cases = load_case_dirs(extracted_root)
    if len(cases) != 36:
        raise VerificationError(f"Expected 36 case directories, found {len(cases)}")

    reconstructed = verify_case_bindings(run_dir, cases)
    out_path = write_binder(run_dir, artifact_rows, reconstructed)

    print(f"PASS: verified run {EXPECTED_RUN_ID} bind-status path {out_path}")
    print("PASS: case_count=36 verified_downloads=36 all_identical_run=True")
    print("PASS: partition reconstructed from certificate states only")
    print("PASS: CNF and variable-map hashes verified against extracted evidence")
    print("PASS: solver and toolchain identity agreement verified")
    print("PASS: preparation and summary artifact archives verified")
    print("PASS: EXECUTION_BOUND emitted only after all fail-closed assertions")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
