#!/usr/bin/env python3
"""Validate Cruthúnas CR-0 dry-run status-change transactions.

This validates governance consistency only. It does not execute transitions or
establish mathematical truth.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECT_PATH = ROOT / "cruthunas" / "project.json"
ALLOWED_STATUS = {"BLOCKED", "READY"}
ALLOWED_OPERATIONS = {"create", "update"}
REQUIRED_OPERATION_PATHS = {
    "cruthunas/evidence.json",
    "cruthunas/transitions.json",
    "cruthunas/ledger.json",
}


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


def require_string(value: Any, context: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        add(errors, f"{context} must be a non-empty string")
        return False
    return True


def validate() -> list[str]:
    errors: list[str] = []
    try:
        project = load(PROJECT_PATH)
        claims_data = load(ROOT / project["claim_registry"])
        ledger_data = load(ROOT / project["ledger"])
        evidence_data = load(ROOT / project["evidence_registry"])
        transitions_data = load(ROOT / project["transition_registry"])
    except (ValueError, KeyError) as exc:
        return [str(exc)]

    schema_path = ROOT / str(project.get("transaction_schema", ""))
    if not schema_path.is_file():
        add(errors, f"missing transaction schema: {schema_path.relative_to(ROOT)}")

    claim_ids = {
        claim.get("id")
        for claim in claims_data.get("claims", [])
        if isinstance(claim, dict) and isinstance(claim.get("id"), str)
    }
    ledger = {
        entry.get("claim_id"): entry
        for entry in ledger_data.get("entries", [])
        if isinstance(entry, dict) and isinstance(entry.get("claim_id"), str)
    }
    evidence_ids = {
        item.get("id")
        for item in evidence_data.get("evidence", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    chain_tail: dict[str, str] = {}
    for chain in transitions_data.get("chains", []):
        if not isinstance(chain, dict) or not isinstance(chain.get("claim_id"), str):
            continue
        records = chain.get("records")
        if isinstance(records, list) and records and isinstance(records[-1], dict):
            tail = records[-1].get("id")
            if isinstance(tail, str):
                chain_tail[chain["claim_id"]] = tail

    plan_paths = project.get("transaction_plans")
    if not isinstance(plan_paths, list) or not plan_paths:
        add(errors, "project.transaction_plans must be a non-empty array")
        return errors

    transaction_ids: set[str] = set()
    for plan_path_value in plan_paths:
        if not isinstance(plan_path_value, str) or not plan_path_value.strip():
            add(errors, "transaction plan path must be a non-empty string")
            continue
        plan_path = ROOT / plan_path_value
        try:
            plan = load(plan_path)
        except ValueError as exc:
            add(errors, str(exc))
            continue

        context = plan_path_value
        if plan.get("schema_version") != 1:
            add(errors, f"{context}: schema_version must equal 1")
        transaction_id = plan.get("transaction_id")
        if require_string(transaction_id, f"{context}.transaction_id", errors):
            assert isinstance(transaction_id, str)
            if transaction_id in transaction_ids:
                add(errors, f"duplicate transaction id: {transaction_id}")
            transaction_ids.add(transaction_id)
        if plan.get("dry_run") is not True:
            add(errors, f"{context}: dry_run must be true")

        claim_id = plan.get("claim_id")
        if claim_id not in claim_ids:
            add(errors, f"{context}: unknown claim_id {claim_id!r}")
            continue
        entry = ledger.get(claim_id)
        if entry is None:
            add(errors, f"{context}: claim has no ledger entry")
            continue

        expected_transition = plan.get("expected_current_transition_id")
        if expected_transition != entry.get("current_transition_id"):
            add(errors, f"{context}: expected transition does not match ledger")
        if expected_transition != chain_tail.get(claim_id):
            add(errors, f"{context}: expected transition does not match chain tail")

        from_gate = plan.get("from_gate")
        to_gate = plan.get("to_gate")
        if from_gate != entry.get("gate"):
            add(errors, f"{context}: from_gate does not match current ledger gate")
        if not isinstance(from_gate, int) or not isinstance(to_gate, int) or to_gate != from_gate + 1:
            add(errors, f"{context}: transaction must describe one contiguous gate move")

        require_string(plan.get("actor"), f"{context}.actor", errors)
        require_string(plan.get("reason"), f"{context}.reason", errors)
        require_string(plan.get("source_revision"), f"{context}.source_revision", errors)

        plan_evidence = plan.get("evidence_ids")
        if not isinstance(plan_evidence, list):
            add(errors, f"{context}: evidence_ids must be an array")
            plan_evidence = []
        for evidence_id in plan_evidence:
            if evidence_id not in evidence_ids:
                add(errors, f"{context}: unknown evidence id {evidence_id!r}")

        operations = plan.get("operations")
        operation_paths: set[str] = set()
        if not isinstance(operations, list) or not operations:
            add(errors, f"{context}: operations must be non-empty")
        else:
            for index, operation in enumerate(operations):
                if not isinstance(operation, dict):
                    add(errors, f"{context}.operations[{index}] must be an object")
                    continue
                if operation.get("operation") not in ALLOWED_OPERATIONS:
                    add(errors, f"{context}.operations[{index}]: unsupported operation")
                path_value = operation.get("path")
                if require_string(path_value, f"{context}.operations[{index}].path", errors):
                    assert isinstance(path_value, str)
                    operation_paths.add(path_value)
        missing_operations = REQUIRED_OPERATION_PATHS - operation_paths
        if missing_operations:
            add(errors, f"{context}: missing governance operations: {', '.join(sorted(missing_operations))}")

        status = plan.get("status")
        if status not in ALLOWED_STATUS:
            add(errors, f"{context}: status must be BLOCKED or READY")
        blockers = plan.get("blocking_conditions", [])
        if not isinstance(blockers, list) or not all(isinstance(item, str) and item.strip() for item in blockers):
            add(errors, f"{context}: blocking_conditions must be a string array")
            blockers = []
        if status == "BLOCKED":
            if not blockers:
                add(errors, f"{context}: BLOCKED transaction requires blocking conditions")
            if plan_evidence:
                add(errors, f"{context}: BLOCKED transaction must not pretend supporting evidence is ready")
        if status == "READY":
            if blockers:
                add(errors, f"{context}: READY transaction cannot retain blocking conditions")
            if to_gate >= 3 and not plan_evidence:
                add(errors, f"{context}: READY transition to Gate 3+ requires evidence")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Cruthúnas transaction validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Cruthúnas dry-run transactions are internally consistent.")
    print("No transaction was applied; mathematical and governance states are unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
