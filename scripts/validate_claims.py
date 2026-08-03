#!/usr/bin/env python3
"""Validate the repository-level mathematical claim registry.

This script checks structure and repository consistency. It does not establish
mathematical truth; package-local verifiers and external review remain separate
trust layers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research" / "claims.json"

ALLOWED_STATUSES = {
    "reproduction-verified",
    "candidate-proof",
    "certified-obstruction",
    "attack-surface",
    "open",
}

REQUIRED_FIELDS = {
    "id",
    "title",
    "type",
    "status",
    "package",
    "claim",
    "evidence_commands",
    "limitations",
    "public_claim_allowed",
}


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def require_string(value: Any, field: str, claim_id: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        fail(f"{claim_id}: {field} must be a non-empty string", errors)


def load_registry() -> dict[str, Any]:
    try:
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"missing registry: {REGISTRY.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {REGISTRY.relative_to(ROOT)}: {exc}") from exc


def validate() -> list[str]:
    data = load_registry()
    errors: list[str] = []

    if data.get("schema_version") != 1:
        fail("schema_version must equal 1", errors)

    claims = data.get("claims")
    if not isinstance(claims, list) or not claims:
        fail("claims must be a non-empty array", errors)
        return errors

    claim_ids: set[str] = set()
    claim_by_id: dict[str, dict[str, Any]] = {}

    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            fail(f"claims[{index}] must be an object", errors)
            continue

        missing = sorted(REQUIRED_FIELDS - set(claim))
        provisional_id = str(claim.get("id", f"claims[{index}]"))
        if missing:
            fail(f"{provisional_id}: missing fields: {', '.join(missing)}", errors)

        claim_id = claim.get("id")
        if not isinstance(claim_id, str) or not claim_id.strip():
            fail(f"claims[{index}]: id must be a non-empty string", errors)
            continue
        if claim_id in claim_ids:
            fail(f"duplicate claim id: {claim_id}", errors)
            continue

        claim_ids.add(claim_id)
        claim_by_id[claim_id] = claim

        for field in ("title", "type", "package", "claim"):
            require_string(claim.get(field), field, claim_id, errors)

        status = claim.get("status")
        if status not in ALLOWED_STATUSES:
            fail(f"{claim_id}: unsupported status {status!r}", errors)

        package = claim.get("package")
        if isinstance(package, str) and package:
            package_dir = ROOT / package
            if not package_dir.is_dir():
                fail(f"{claim_id}: package directory does not exist: {package}", errors)
            elif not (package_dir / "README.md").is_file():
                fail(f"{claim_id}: package lacks README.md: {package}", errors)

        commands = claim.get("evidence_commands")
        if not isinstance(commands, list) or not all(
            isinstance(command, str) and command.strip() for command in commands
        ):
            fail(f"{claim_id}: evidence_commands must be an array of non-empty strings", errors)
        elif status != "open" and not commands:
            fail(f"{claim_id}: non-open claims require evidence commands", errors)

        limitations = claim.get("limitations")
        if not isinstance(limitations, list) or not limitations or not all(
            isinstance(item, str) and item.strip() for item in limitations
        ):
            fail(f"{claim_id}: limitations must be a non-empty string array", errors)

        public_allowed = claim.get("public_claim_allowed")
        if not isinstance(public_allowed, bool):
            fail(f"{claim_id}: public_claim_allowed must be boolean", errors)
        if status in {"candidate-proof", "open"} and public_allowed is not False:
            fail(f"{claim_id}: candidate/open claims cannot be marked public-claim allowed", errors)

    for claim_id, claim in claim_by_id.items():
        dependencies = claim.get("depends_on", [])
        if not isinstance(dependencies, list) or not all(
            isinstance(dep, str) and dep.strip() for dep in dependencies
        ):
            fail(f"{claim_id}: depends_on must be an array of non-empty claim ids", errors)
            continue
        for dependency in dependencies:
            if dependency not in claim_ids:
                fail(f"{claim_id}: unknown dependency {dependency}", errors)
            if dependency == claim_id:
                fail(f"{claim_id}: claim cannot depend on itself", errors)

    active_target = data.get("active_target")
    if active_target not in claim_ids:
        fail(f"active_target references unknown claim: {active_target!r}", errors)
    elif claim_by_id[active_target].get("status") != "open":
        fail("active_target must currently have status 'open'", errors)

    definitions = data.get("status_definitions")
    if not isinstance(definitions, dict):
        fail("status_definitions must be an object", errors)
    else:
        missing_definitions = sorted(ALLOWED_STATUSES - set(definitions))
        if missing_definitions:
            fail(
                "status_definitions missing: " + ", ".join(missing_definitions),
                errors,
            )

    return errors


def main() -> int:
    data = load_registry()
    errors = validate()
    if errors:
        print("Claim registry validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    claims = data["claims"]
    print(f"Claim registry OK: {len(claims)} claims")
    for claim in claims:
        print(f"- {claim['id']}: {claim['status']}")
    print(f"Active target: {data['active_target']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
