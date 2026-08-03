#!/usr/bin/env python3
"""Prospectively register the q00 fifth-base reduction through Cruthúnas."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLAIM_ID = "n11-k6-q00-fifth-base-reduction"
EVIDENCE_ID = "E-K6-Q00-FIFTH-BASE"
SOURCE_ID = "SRC-K6-Q00-FIFTH-BASE"
ACTOR = "openai-gpt-5.6-thinking"
TX_23_PATH = "cruthunas/transactions/n11-k6-q00-fifth-base-gate-2-to-3.ready.json"
TX_34_PATH = "cruthunas/transactions/n11-k6-q00-fifth-base-gate-3-to-4.ready.json"
BLOCKED_FULL_PATH = "cruthunas/transactions/n11-k6-gate-2-to-3.blocked.json"
PACKAGE = "borsuk_11_k6_q00_fifth_base_reduction"


def load(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def write(relative: str, value: dict[str, Any]) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def by_id(values: list[dict[str, Any]], key: str, identifier: str) -> dict[str, Any] | None:
    return next((value for value in values if value.get(key) == identifier), None)


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


def transaction(identifier: str, expected: str, from_gate: int, to_gate: int, reason: str, revision: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "transaction_id": identifier,
        "dry_run": True,
        "claim_id": CLAIM_ID,
        "expected_current_transition_id": expected,
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


def stage_scoped() -> None:
    revision = git_head()
    claims = load("research/claims.json")
    sources = load("cruthunas/sources.json")
    evidence = load("cruthunas/evidence.json")
    ledger = load("cruthunas/ledger.json")
    transitions = load("cruthunas/transitions.json")
    project = load("cruthunas/project.json")
    if by_id(claims["claims"], "id", CLAIM_ID):
        raise SystemExit(f"{CLAIM_ID} already exists")

    claims["claims"].append({
        "id": CLAIM_ID,
        "title": "Exhaustive 12-type fifth-base refinement of q00",
        "type": "symmetry-reduction",
        "status": "open",
        "package": PACKAGE,
        "claim": "Every q00-compatible diameter-6 family containing more than the four q00 base points is contained, up to an affine cube isometry stabilizing the unordered q00 base, in one of 12 canonical fifth-base child trims; the four-point base alone is trivially 12-colorable.",
        "depends_on": ["n11-k6-four-base-reduction", "n11-k6-q00-trim-unsat"],
        "evidence_commands": [],
        "limitations": [
            "All 12 fifth-base child trims remain UNKNOWN.",
            "The child trims may contain pairs farther than Hamming distance 6 and are covers rather than legal theorem instances.",
            "This reduction does not change q00 in case_status.json.",
            "The full n=11,k=6 theorem target remains Gate 2, UNCHECKED, and OPEN."
        ],
        "public_claim_allowed": False
    })
    sources["sources"].append({
        "id": SOURCE_ID,
        "kind": "repository-document",
        "path": f"{PACKAGE}/PROOF.md",
        "revision_pin": revision,
        "allowed_claim_ids": [CLAIM_ID]
    })
    evidence["evidence"].append({
        "id": EVIDENCE_ID,
        "claim_id": CLAIM_ID,
        "type": "SYMMETRY_REDUCTION",
        "epistemic_class": "HYBRID",
        "verification_state": "INDEPENDENTLY_REPRODUCED",
        "paths": [
            f"{PACKAGE}/README.md",
            f"{PACKAGE}/PROOF.md",
            f"{PACKAGE}/generate_fifth_base_cases.py",
            f"{PACKAGE}/verify_independent.js",
            f"{PACKAGE}/build_child_instance.py",
            f"{PACKAGE}/canonical_12.csv",
            f"{PACKAGE}/report.json",
            f"{PACKAGE}/child_status.json",
            f"{PACKAGE}/verify_status.py",
            f"{PACKAGE}/SHA256SUMS"
        ],
        "commands": [
            f"cd {PACKAGE} && python generate_fifth_base_cases.py --output canonical_12.csv --report report.json",
            f"cd {PACKAGE} && node verify_independent.js",
            f"cd {PACKAGE} && python verify_status.py",
            f"cd {PACKAGE} && sha256sum -c SHA256SUMS",
            f"cd {PACKAGE} && python build_child_instance.py f11 --metadata-only"
        ],
        "environment": {"python": ">=3.11", "node": ">=20", "external_dependencies": []},
        "source_revision": revision,
        "clean_room_verifier": True,
        "artifact_hashes": [
            {"artifact": "canonical fifth-base case list", "sha256": "01b3ee2e629788037f1ccd6906140302abddd1ae1c077aa8cf7e8f619adb807a"},
            {"artifact": "Python fifth-base generator", "sha256": "a9bd046824a9be2727184a1a27ed9785e755d4ae9f7067c561fe835e71ec43f9"},
            {"artifact": "independent JavaScript verifier", "sha256": "8121c3cfd5e970b0b41a50bb61807dad1388755412b221278968c34b87536ac4"},
            {"artifact": "fifth-base completeness proof", "sha256": "65be383913cfaaace50650334360f76e845489e1fdb56a649d7ca1edeff525a7"},
            {"artifact": "f11 compact CNF smoke test", "sha256": "4341c1d9ba4b293f79e48b7a094e757d0c09aa46024d67e9a6f4556f3d3c2388"},
            {"artifact": "f11 variable map smoke test", "sha256": "ff5b5f9df7c3364d79dcdf0942cc7ee58fb63a7d1911e7fa2ed4bb60da511f20"}
        ],
        "limitations": "This evidence establishes only the exhaustive 12-child fifth-base cover. It resolves no child, does not change q00 case status, and does not promote the full theorem."
    })
    ledger["entries"].append({
        "claim_id": CLAIM_ID,
        "gate": 2,
        "epistemic_class": "HYBRID",
        "verification_state": "UNCHECKED",
        "lifecycle_state": "OPEN",
        "source_ids": [SOURCE_ID],
        "evidence_ids": [],
        "current_transition_id": "T-K6-Q00-FIFTH-1-2"
    })
    transitions["chains"].append({
        "claim_id": CLAIM_ID,
        "records": [
            transition("T-K6-Q00-FIFTH-0-1", 0, 1, "Register the q00 fifth-base refinement prospectively.", [], revision),
            transition("T-K6-Q00-FIFTH-1-2", 1, 2, "Record the exact 12-child scope, UNKNOWN boundary, and theorem non-implication.", [], revision)
        ]
    })
    write(TX_23_PATH, transaction("TX-K6-Q00-FIFTH-2-3", "T-K6-Q00-FIFTH-1-2", 2, 3, "Link the independently reproduced fifth-base reduction evidence.", revision))
    project["transaction_plans"] = [p for p in project["transaction_plans"] if p not in {TX_23_PATH, TX_34_PATH}] + [TX_23_PATH]
    write("research/claims.json", claims)
    write("cruthunas/sources.json", sources)
    write("cruthunas/evidence.json", evidence)
    write("cruthunas/ledger.json", ledger)
    write("cruthunas/transitions.json", transitions)
    write("cruthunas/project.json", project)


def stage_gate3() -> None:
    revision = git_head()
    claims = load("research/claims.json")
    ledger = load("cruthunas/ledger.json")
    transitions = load("cruthunas/transitions.json")
    project = load("cruthunas/project.json")
    claim = by_id(claims["claims"], "id", CLAIM_ID)
    entry = by_id(ledger["entries"], "claim_id", CLAIM_ID)
    chain = by_id(transitions["chains"], "claim_id", CLAIM_ID)
    if claim is None or entry is None or chain is None:
        raise SystemExit("claim must be registered before Gate 3")
    if entry.get("gate") != 2 or entry.get("current_transition_id") != "T-K6-Q00-FIFTH-1-2":
        raise SystemExit("unexpected Gate 2 state")
    if TX_23_PATH not in project.get("transaction_plans", []):
        raise SystemExit("Gate 2 to Gate 3 transaction is not registered")
    claim["status"] = "attack-surface"
    claim["evidence_commands"] = [
        f"cd {PACKAGE} && python generate_fifth_base_cases.py --output canonical_12.csv --report report.json",
        f"cd {PACKAGE} && node verify_independent.js",
        f"cd {PACKAGE} && python verify_status.py"
    ]
    claim["public_claim_allowed"] = True
    entry.update({
        "gate": 3,
        "verification_state": "INDEPENDENTLY_REPRODUCED",
        "lifecycle_state": "WORKING",
        "evidence_ids": [EVIDENCE_ID],
        "current_transition_id": "T-K6-Q00-FIFTH-2-3"
    })
    chain["records"].append(transition("T-K6-Q00-FIFTH-2-3", 2, 3, "Link the exact orbit list, completeness proof, independent verifier, hashes, and UNKNOWN child ledger.", [EVIDENCE_ID], revision))
    write(TX_34_PATH, transaction("TX-K6-Q00-FIFTH-3-4", "T-K6-Q00-FIFTH-2-3", 3, 4, "Register the independently reproduced fifth-base reduction as a checked attack surface.", revision))
    project["transaction_plans"] = [p for p in project["transaction_plans"] if p not in {TX_23_PATH, TX_34_PATH}] + [TX_34_PATH]
    write("research/claims.json", claims)
    write("cruthunas/ledger.json", ledger)
    write("cruthunas/transitions.json", transitions)
    write("cruthunas/project.json", project)


def stage_gate4() -> None:
    revision = git_head()
    claims = load("research/claims.json")
    ledger = load("cruthunas/ledger.json")
    transitions = load("cruthunas/transitions.json")
    project = load("cruthunas/project.json")
    claim = by_id(claims["claims"], "id", CLAIM_ID)
    entry = by_id(ledger["entries"], "claim_id", CLAIM_ID)
    chain = by_id(transitions["chains"], "claim_id", CLAIM_ID)
    if claim is None or entry is None or chain is None:
        raise SystemExit("claim must exist before Gate 4")
    if entry.get("gate") != 3 or entry.get("current_transition_id") != "T-K6-Q00-FIFTH-2-3":
        raise SystemExit("unexpected Gate 3 state")
    if TX_34_PATH not in project.get("transaction_plans", []):
        raise SystemExit("Gate 3 to Gate 4 transaction is not registered")
    claim["status"] = "attack-surface"
    claim["public_claim_allowed"] = True
    entry.update({
        "gate": 4,
        "verification_state": "INDEPENDENTLY_REPRODUCED",
        "lifecycle_state": "WORKING",
        "evidence_ids": [EVIDENCE_ID],
        "current_transition_id": "T-K6-Q00-FIFTH-3-4"
    })
    chain["records"].append(transition("T-K6-Q00-FIFTH-3-4", 3, 4, "Register successful internal checks without claiming any fifth-base child resolved.", [EVIDENCE_ID], revision))
    project["transaction_plans"] = [p for p in project["transaction_plans"] if p not in {TX_23_PATH, TX_34_PATH}]
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
    {"scoped": stage_scoped, "gate3": stage_gate3, "gate4": stage_gate4}[args.stage]()
    print(f"Applied q00 fifth-base Cruthúnas stage: {args.stage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
