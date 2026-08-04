#!/usr/bin/env python3
"""Prospectively register the q00 five-base symmetry reduction.

The three stages are intentionally separate and noncontiguous use is rejected.
No stage alters the parent 58-type case_status.json, the q00 obstruction claim,
or the full n11-k6 theorem target.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLAIM_ID = "n11-k6-q00-five-base-reduction"
SOURCE_ID = "SRC-K6-Q00-FIVE-BASE"
EVIDENCE_ID = "E-K6-Q00-FIVE-BASE"
ACTOR = "openai-gpt-5.6-thinking"
PACKAGE = "borsuk_11_k6_q00_five_base_reduction"
TX_23_PATH = "cruthunas/transactions/n11-k6-q00-five-base-gate-2-to-3.ready.json"
TX_34_PATH = "cruthunas/transactions/n11-k6-q00-five-base-gate-3-to-4.ready.json"
BLOCKED_FULL_PATH = "cruthunas/transactions/n11-k6-gate-2-to-3.blocked.json"


def load(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def write(relative: str, value: dict[str, Any]) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def by_id(values: list[dict[str, Any]], key: str, identifier: str) -> dict[str, Any] | None:
    for value in values:
        if value.get(key) == identifier:
            return value
    return None


def transition(identifier: str, from_gate: int, to_gate: int, reason: str, evidence_ids: list[str], revision: str) -> dict[str, Any]:
    return {
        "id": identifier,
        "from_gate": from_gate,
        "to_gate": to_gate,
        "date": date.today().isoformat(),
        "actor": ACTOR,
        "reason": reason,
        "evidence_ids": evidence_ids,
        "source_revision": revision,
        "bootstrap_import": False,
    }


def plan(identifier: str, expected_transition: str, from_gate: int, to_gate: int, reason: str, revision: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "transaction_id": identifier,
        "dry_run": True,
        "claim_id": CLAIM_ID,
        "expected_current_transition_id": expected_transition,
        "from_gate": from_gate,
        "to_gate": to_gate,
        "actor": ACTOR,
        "reason": reason,
        "source_revision": revision,
        "evidence_ids": [EVIDENCE_ID],
        "operations": [
            {"operation": "update", "path": "cruthunas/evidence.json"},
            {"operation": "update", "path": "cruthunas/transitions.json"},
            {"operation": "update", "path": "cruthunas/ledger.json"},
        ],
        "status": "READY",
        "blocking_conditions": [],
    }


def ensure_makefile_verifiers() -> None:
    path = ROOT / "Makefile"
    text = path.read_text(encoding="utf-8")
    commands = (
        f"\tcd {PACKAGE} && $(PYTHON) generate_cases.py\n"
        f"\tcd {PACKAGE} && $(NODE) verify_independent.js\n"
        f"\tcd {PACKAGE} && $(PYTHON) verify_status.py\n"
    )
    if commands in text:
        return
    marker = "\tcd borsuk_11_k6_four_base_reduction && $(PYTHON) verify_sat_lane.py\n"
    if marker not in text:
        raise SystemExit("Makefile insertion marker not found")
    path.write_text(text.replace(marker, marker + commands), encoding="utf-8", newline="\n")


def scoped() -> None:
    revision = git_head()
    claims = load("research/claims.json")
    sources = load("cruthunas/sources.json")
    evidence = load("cruthunas/evidence.json")
    ledger = load("cruthunas/ledger.json")
    transitions = load("cruthunas/transitions.json")
    project = load("cruthunas/project.json")

    if by_id(claims["claims"], "id", CLAIM_ID):
        raise SystemExit(f"{CLAIM_ID} already exists")

    claims["claims"].append(
        {
            "id": CLAIM_ID,
            "title": "Exhaustive 12-type five-base reduction beneath q00",
            "type": "symmetry-reduction",
            "status": "open",
            "package": PACKAGE,
            "claim": "Every legal q00 component with at least five vertices is contained in one of 12 canonical unordered five-base trims; smaller components are trivially 12-colorable.",
            "depends_on": ["n11-k6-four-base-reduction", "n11-k6-q00-trim-unsat"],
            "evidence_commands": [],
            "limitations": [
                "All 12 five-base child trims remain UNKNOWN.",
                "The child trims remain universal covers and may contain pairs farther than Hamming distance 6.",
                "This reduction does not close q00 or change the parent 58-type case status.",
                "This reduction does not promote the full n=11,k=6 theorem target."
            ],
            "public_claim_allowed": False,
        }
    )

    sources["sources"].append(
        {
            "id": SOURCE_ID,
            "kind": "repository-document",
            "path": f"{PACKAGE}/README.md",
            "revision_pin": revision,
            "allowed_claim_ids": [CLAIM_ID],
        }
    )

    evidence["evidence"].append(
        {
            "id": EVIDENCE_ID,
            "claim_id": CLAIM_ID,
            "type": "SYMMETRY_REDUCTION",
            "epistemic_class": "HYBRID",
            "verification_state": "INDEPENDENTLY_REPRODUCED",
            "paths": [
                f"{PACKAGE}/README.md",
                f"{PACKAGE}/PROOF.md",
                f"{PACKAGE}/generate_cases.py",
                f"{PACKAGE}/verify_independent.js",
                f"{PACKAGE}/case_status.json",
                f"{PACKAGE}/verify_status.py",
            ],
            "commands": [
                f"cd {PACKAGE} && python generate_cases.py",
                f"cd {PACKAGE} && node verify_independent.js",
                f"cd {PACKAGE} && python verify_status.py",
            ],
            "environment": {
                "python": "3.11 standard library",
                "node": "22 standard library",
                "arithmetic": "exact integer enumeration",
            },
            "source_revision": revision,
            "clean_room_verifier": True,
            "artifact_hashes": [
                {"artifact": "canonical 12-type case CSV", "sha256": "d5b0825cd8645af2c595b3de3c851360e0b283d8ce61383482f76168e1ae9855"},
                {"artifact": "complete fifth-vertex assignment", "sha256": "6c94923a260290d59727bdcad68293b7f1962a7c5377885dd536fefa5962ffc7"},
                {"artifact": "parent q00 compact CNF certificate dependency", "sha256": "36da8f78ae376b370f119d1fa16a58f6504607d949ac8315648fdbda52450299"},
            ],
            "limitations": "The reduction is exhaustive for five-point extensions of q00 but provides no SAT or UNSAT conclusion for any of the 12 child trims and no theorem-level promotion.",
        }
    )

    ledger["entries"].append(
        {
            "claim_id": CLAIM_ID,
            "gate": 2,
            "epistemic_class": "HYBRID",
            "verification_state": "UNCHECKED",
            "lifecycle_state": "OPEN",
            "source_ids": [SOURCE_ID],
            "evidence_ids": [],
            "current_transition_id": "T-K6-Q00-FIVE-BASE-1-2",
        }
    )

    transitions["chains"].append(
        {
            "claim_id": CLAIM_ID,
            "records": [
                transition("T-K6-Q00-FIVE-BASE-0-1", 0, 1, "Register the q00 five-base reduction prospectively.", [], revision),
                transition("T-K6-Q00-FIVE-BASE-1-2", 1, 2, "Scope the reduction to exhaustive five-point extensions of q00 with 12 unresolved universal child trims.", [], revision),
            ],
        }
    )

    write(TX_23_PATH, plan("TX-K6-Q00-FIVE-BASE-2-3", "T-K6-Q00-FIVE-BASE-1-2", 2, 3, "Link independently reproduced Python and JavaScript five-base reduction evidence.", revision))
    project["transaction_plans"] = [path for path in project["transaction_plans"] if path not in {TX_23_PATH, TX_34_PATH}] + [TX_23_PATH]

    ensure_makefile_verifiers()
    write("research/claims.json", claims)
    write("cruthunas/sources.json", sources)
    write("cruthunas/evidence.json", evidence)
    write("cruthunas/ledger.json", ledger)
    write("cruthunas/transitions.json", transitions)
    write("cruthunas/project.json", project)


def gate3() -> None:
    revision = git_head()
    claims = load("research/claims.json")
    ledger = load("cruthunas/ledger.json")
    transitions = load("cruthunas/transitions.json")
    project = load("cruthunas/project.json")
    claim = by_id(claims["claims"], "id", CLAIM_ID)
    entry = by_id(ledger["entries"], "claim_id", CLAIM_ID)
    chain = by_id(transitions["chains"], "claim_id", CLAIM_ID)
    if claim is None or entry is None or chain is None:
        raise SystemExit("five-base claim is not registered")
    if entry.get("gate") != 2 or entry.get("current_transition_id") != "T-K6-Q00-FIVE-BASE-1-2":
        raise SystemExit("five-base claim is not at expected Gate 2 state")
    if TX_23_PATH not in project.get("transaction_plans", []):
        raise SystemExit("Gate 2 to Gate 3 transaction is not registered")

    claim["status"] = "attack-surface"
    claim["public_claim_allowed"] = True
    claim["evidence_commands"] = [
        f"cd {PACKAGE} && python generate_cases.py",
        f"cd {PACKAGE} && node verify_independent.js",
        f"cd {PACKAGE} && python verify_status.py",
    ]
    entry.update(
        {
            "gate": 3,
            "verification_state": "INDEPENDENTLY_REPRODUCED",
            "lifecycle_state": "WORKING",
            "evidence_ids": [EVIDENCE_ID],
            "current_transition_id": "T-K6-Q00-FIVE-BASE-2-3",
        }
    )
    chain["records"].append(
        transition("T-K6-Q00-FIVE-BASE-2-3", 2, 3, "Link exact enumeration, complete affine-isometry canonicalization, child statistics, coverage assignment, and independent JavaScript reproduction.", [EVIDENCE_ID], revision)
    )
    write(TX_34_PATH, plan("TX-K6-Q00-FIVE-BASE-3-4", "T-K6-Q00-FIVE-BASE-2-3", 3, 4, "Register the independently reproduced q00 five-base reduction as internally checked infrastructure.", revision))
    project["transaction_plans"] = [path for path in project["transaction_plans"] if path not in {TX_23_PATH, TX_34_PATH}] + [TX_34_PATH]

    write("research/claims.json", claims)
    write("cruthunas/ledger.json", ledger)
    write("cruthunas/transitions.json", transitions)
    write("cruthunas/project.json", project)


def gate4() -> None:
    revision = git_head()
    claims = load("research/claims.json")
    ledger = load("cruthunas/ledger.json")
    transitions = load("cruthunas/transitions.json")
    project = load("cruthunas/project.json")
    claim = by_id(claims["claims"], "id", CLAIM_ID)
    entry = by_id(ledger["entries"], "claim_id", CLAIM_ID)
    chain = by_id(transitions["chains"], "claim_id", CLAIM_ID)
    if claim is None or entry is None or chain is None:
        raise SystemExit("five-base claim is not registered")
    if entry.get("gate") != 3 or entry.get("current_transition_id") != "T-K6-Q00-FIVE-BASE-2-3":
        raise SystemExit("five-base claim is not at expected Gate 3 state")
    if TX_34_PATH not in project.get("transaction_plans", []):
        raise SystemExit("Gate 3 to Gate 4 transaction is not registered")

    entry.update(
        {
            "gate": 4,
            "verification_state": "INDEPENDENTLY_REPRODUCED",
            "lifecycle_state": "WORKING",
            "evidence_ids": [EVIDENCE_ID],
            "current_transition_id": "T-K6-Q00-FIVE-BASE-3-4",
        }
    )
    chain["records"].append(
        transition("T-K6-Q00-FIVE-BASE-3-4", 3, 4, "Register the independently reproduced 12-type reduction as Gate 4 attack-surface infrastructure without changing any child, parent-case, or theorem status.", [EVIDENCE_ID], revision)
    )
    project["transaction_plans"] = [path for path in project["transaction_plans"] if path not in {TX_23_PATH, TX_34_PATH}]
    if not project["transaction_plans"]:
        project["transaction_plans"] = [BLOCKED_FULL_PATH]

    write("research/claims.json", claims)
    write("cruthunas/ledger.json", ledger)
    write("cruthunas/transitions.json", transitions)
    write("cruthunas/project.json", project)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("scoped", "gate3", "gate4"))
    args = parser.parse_args()
    {"scoped": scoped, "gate3": gate3, "gate4": gate4}[args.stage]()
    print(f"Applied q00 five-base Cruthúnas stage: {args.stage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
