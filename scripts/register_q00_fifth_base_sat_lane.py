#!/usr/bin/env python3
"""Register the q00 fifth-base certificate-first solver lane as Cruthúnas evidence."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLAIM_ID = "n11-k6-q00-fifth-base-reduction"
EVIDENCE_ID = "E-K6-Q00-FIFTH-BASE-SAT-LANE"
SOURCE_ID = "SRC-K6-Q00-FIFTH-BASE-SAT-LANE"
PACKAGE = "borsuk_11_k6_q00_fifth_base_reduction"


def load(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def write(relative: str, value: dict[str, Any]) -> None:
    (ROOT / relative).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def by_id(values: list[dict[str, Any]], key: str, identifier: str) -> dict[str, Any] | None:
    return next((value for value in values if value.get(key) == identifier), None)


def main() -> int:
    revision = head()
    sources = load("cruthunas/sources.json")
    evidence = load("cruthunas/evidence.json")
    ledger = load("cruthunas/ledger.json")

    entry = by_id(ledger["entries"], "claim_id", CLAIM_ID)
    if entry is None:
        raise SystemExit(f"missing governed claim: {CLAIM_ID}")
    if entry.get("gate") != 4:
        raise SystemExit(f"solver lane requires existing Gate 4 reduction, found Gate {entry.get('gate')}")

    if by_id(sources["sources"], "id", SOURCE_ID) is None:
        sources["sources"].append({
            "id": SOURCE_ID,
            "kind": "repository-document",
            "path": f"{PACKAGE}/SAT-WORKFLOW.md",
            "revision_pin": revision,
            "allowed_claim_ids": [CLAIM_ID],
        })

    if by_id(evidence["evidence"], "id", EVIDENCE_ID) is None:
        evidence["evidence"].append({
            "id": EVIDENCE_ID,
            "claim_id": CLAIM_ID,
            "type": "SEARCH_INFRASTRUCTURE",
            "epistemic_class": "INFRASTRUCTURE",
            "verification_state": "INTERNALLY_VERIFIED",
            "paths": [
                f"{PACKAGE}/SAT-WORKFLOW.md",
                f"{PACKAGE}/build_child_instance.py",
                f"{PACKAGE}/verify_child_model.py",
                f"{PACKAGE}/child_status.json",
                ".github/workflows/certify-f11.yml",
            ],
            "commands": [
                f"cd {PACKAGE} && python verify_child_model.py --self-test",
                f"cd {PACKAGE} && python build_child_instance.py f11 --output-dir /tmp/f11",
                "echo '4341c1d9ba4b293f79e48b7a094e757d0c09aa46024d67e9a6f4556f3d3c2388  /tmp/f11/f11_12color.cnf' | sha256sum --check --strict",
                "echo 'ff5b5f9df7c3364d79dcdf0942cc7ee58fb63a7d1911e7fa2ed4bb60da511f20  /tmp/f11/f11_variable_map.json' | sha256sum --check --strict",
            ],
            "environment": {
                "python": ">=3.11",
                "solver": "Kissat 4.0.0",
                "proof_checker": "drat-trim revision 2e3b2dc0ecf938addbd779d42877b6ed69d9a985",
                "runner": "GitHub Actions ubuntu-24.04",
            },
            "source_revision": revision,
            "clean_room_verifier": True,
            "artifact_hashes": [
                {
                    "artifact": "f11 compact CNF smoke test",
                    "sha256": "4341c1d9ba4b293f79e48b7a094e757d0c09aa46024d67e9a6f4556f3d3c2388",
                },
                {
                    "artifact": "f11 variable map smoke test",
                    "sha256": "ff5b5f9df7c3364d79dcdf0942cc7ee58fb63a7d1911e7fa2ed4bb60da511f20",
                },
                {
                    "artifact": "canonical fifth-base case list",
                    "sha256": "01b3ee2e629788037f1ccd6906140302abddd1ae1c077aa8cf7e8f619adb807a",
                },
            ],
            "limitations": "This evidence verifies deterministic instance generation, independent SAT-model checking, proof-check plumbing, and status-neutral artifact handling. It does not resolve f11 or any fifth-base child. A timeout or unchecked solver report remains UNKNOWN.",
        })

    if SOURCE_ID not in entry["source_ids"]:
        entry["source_ids"].append(SOURCE_ID)
    if EVIDENCE_ID not in entry["evidence_ids"]:
        entry["evidence_ids"].append(EVIDENCE_ID)

    theorem = by_id(ledger["entries"], "claim_id", "n11-k6-full")
    if theorem is None or (theorem["gate"], theorem["verification_state"], theorem["lifecycle_state"]) != (2, "UNCHECKED", "OPEN"):
        raise SystemExit("full theorem boundary changed unexpectedly")

    write("cruthunas/sources.json", sources)
    write("cruthunas/evidence.json", evidence)
    write("cruthunas/ledger.json", ledger)
    print(f"Registered {EVIDENCE_ID} at revision {revision}; no gate or case status changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
