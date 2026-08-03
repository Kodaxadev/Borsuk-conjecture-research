#!/usr/bin/env python3
"""Validate Cruthúnas observations that are explicitly not evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "cruthunas" / "project.json"
ALLOWED_TYPES = {"BOUNDED_SOLVER_PROBE", "HEURISTIC_SEARCH", "NEGATIVE_CONTROL", "BENCHMARK"}
ALLOWED_STATES = {"UNKNOWN", "OBSERVED_SAT_UNREGISTERED", "OBSERVED_UNSAT_UNVERIFIED"}


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON must be an object: {path.relative_to(ROOT)}")
    return value


def add(errors: list[str], message: str) -> None:
    errors.append(message)


def validate() -> list[str]:
    errors: list[str] = []
    try:
        project = load(PROJECT)
        claims = load(ROOT / project["claim_registry"])
        ledger = load(ROOT / project["ledger"])
        evidence = load(ROOT / project["evidence_registry"])
        observations = load(ROOT / project["observation_registry"])
    except (ValueError, KeyError) as exc:
        return [str(exc)]

    schema_path = ROOT / str(project.get("observation_schema", ""))
    if not schema_path.is_file():
        add(errors, f"missing observation schema: {schema_path.relative_to(ROOT)}")

    claim_ids = {
        item.get("id")
        for item in claims.get("claims", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    evidence_ids = {
        item.get("id")
        for item in evidence.get("evidence", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    linked_evidence_ids: set[str] = set()
    for entry in ledger.get("entries", []):
        if isinstance(entry, dict) and isinstance(entry.get("evidence_ids"), list):
            linked_evidence_ids.update(
                item for item in entry["evidence_ids"] if isinstance(item, str)
            )

    records = observations.get("observations")
    if not isinstance(records, list):
        return ["observations must be an array"]

    observation_ids: set[str] = set()
    for index, record in enumerate(records):
        context = f"observations[{index}]"
        if not isinstance(record, dict):
            add(errors, f"{context} must be an object")
            continue
        observation_id = record.get("id")
        if not isinstance(observation_id, str) or not observation_id:
            add(errors, f"{context}.id must be a non-empty string")
        elif observation_id in observation_ids:
            add(errors, f"duplicate observation id: {observation_id}")
        else:
            observation_ids.add(observation_id)
            context = observation_id

        claim_id = record.get("claim_id")
        if claim_id not in claim_ids:
            add(errors, f"{context}: unknown claim {claim_id!r}")
        if record.get("type") not in ALLOWED_TYPES:
            add(errors, f"{context}: unsupported observation type")
        if record.get("result_state") not in ALLOWED_STATES:
            add(errors, f"{context}: unsupported result state")
        if record.get("epistemic_effect") != "NONE":
            add(errors, f"{context}: observations must have epistemic_effect NONE")
        if record.get("repository_status_changed") is not False:
            add(errors, f"{context}: observation cannot change repository status")
        if record.get("evidence_registered") is not False:
            add(errors, f"{context}: observation cannot claim evidence registration")
        if record.get("certificate_present") is not False:
            add(errors, f"{context}: non-evidentiary observation cannot claim a certificate")

        artifact_path = record.get("artifact_path")
        if not isinstance(artifact_path, str) or not artifact_path:
            add(errors, f"{context}: artifact_path must be a non-empty string")
            continue
        artifact = ROOT / artifact_path
        if not artifact.is_file():
            add(errors, f"{context}: artifact does not exist: {artifact_path}")
            continue
        try:
            payload = load(artifact)
        except ValueError as exc:
            add(errors, str(exc))
            continue

        if payload.get("claim_id") != claim_id:
            add(errors, f"{context}: artifact claim_id mismatch")
        if payload.get("case_id") != record.get("case_id"):
            add(errors, f"{context}: artifact case_id mismatch")
        run = payload.get("run")
        if not isinstance(run, dict):
            add(errors, f"{context}: artifact run section missing")
            run = {}
        if run.get("state") != record.get("result_state"):
            add(errors, f"{context}: artifact result state mismatch")
        if run.get("workflow_run_id") != record.get("workflow_run_id"):
            add(errors, f"{context}: workflow run id mismatch")
        if run.get("limit_seconds") != record.get("limit_seconds"):
            add(errors, f"{context}: solver limit mismatch")

        interpretation = payload.get("interpretation")
        if not isinstance(interpretation, dict):
            add(errors, f"{context}: artifact interpretation missing")
            interpretation = {}
        if interpretation.get("repository_status_changed") is not False:
            add(errors, f"{context}: artifact must record no status change")
        if interpretation.get("cruthunas_evidence_registered") is not False:
            add(errors, f"{context}: artifact must record no Cruthúnas evidence")
        if interpretation.get("partial_proof_is_certificate") is not False:
            add(errors, f"{context}: partial proof must not be a certificate")

        source_revision = record.get("source_revision")
        if not isinstance(source_revision, str) or len(source_revision) != 40:
            add(errors, f"{context}: source_revision should be a 40-character commit SHA")
        if run.get("workflow_head_sha") != source_revision:
            add(errors, f"{context}: source revision does not match workflow head")

        if observation_id in evidence_ids or observation_id in linked_evidence_ids:
            add(errors, f"{context}: observation id must never appear as evidence")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Cruthúnas observation validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Cruthúnas non-evidentiary observations are internally consistent.")
    print("No observation contributes evidence or changes claim status.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
