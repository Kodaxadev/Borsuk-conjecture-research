#!/usr/bin/env python3
"""Prospectively register the q00 trim UNSAT certificate through Cruthúnas.

This script performs exactly one requested stage. It is intentionally
idempotent only for the expected current gate and refuses noncontiguous moves.
It does not alter case_status.json or the n11-k6-full theorem target.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLAIM_ID = "n11-k6-q00-trim-unsat"
EVIDENCE_ID = "E-K6-Q00-UNSAT"
SOURCE_ID = "SRC-K6-Q00-UNSAT"
ACTOR = "openai-gpt-5.6-thinking"
TX_23_PATH = "cruthunas/transactions/n11-k6-q00-gate-2-to-3.ready.json"
TX_34_PATH = "cruthunas/transactions/n11-k6-q00-gate-3-to-4.ready.json"
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


def transition(
    identifier: str,
    from_gate: int,
    to_gate: int,
    reason: str,
    evidence_ids: list[str],
    source_revision: str,
) -> dict[str, Any]:
    return {
        "id": identifier,
        "from_gate": from_gate,
        "to_gate": to_gate,
        "date": date.today().isoformat(),
        "actor": ACTOR,
        "reason": reason,
        "evidence_ids": evidence_ids,
        "source_revision": source_revision,
        "bootstrap_import": False,
    }


def transaction_plan(
    identifier: str,
    expected_transition: str,
    from_gate: int,
    to_gate: int,
    reason: str,
    source_revision: str,
) -> dict[str, Any]:
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
        "source_revision": source_revision,
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
        raise SystemExit(f"{CLAIM_ID} already exists; expected an unregistered claim")

    claims["claims"].append(
        {
            "id": CLAIM_ID,
            "title": "Proof-checked UNSAT result for the q00 compact four-base trim",
            "type": "certificate",
            "status": "open",
            "package": "borsuk_11_k6_four_base_reduction",
            "claim": "The deterministic compact list-coloring CNF for canonical universal trim type q00 is UNSAT.",
            "depends_on": ["n11-k6-four-base-reduction"],
            "evidence_commands": [],
            "limitations": [
                "The q00 trim may contain pairs farther than Hamming distance 6 and is not itself a legal theorem instance.",
                "Proof-checked trim UNSAT requires exhaustive compatible refinement before q00 can be marked UNSAT_REFINED.",
                "The full n=11,k=6 theorem target remains open and unchanged.",
                "The proof bundle is currently retained as a time-limited GitHub Actions artifact; durable archival remains pending."
            ],
            "public_claim_allowed": False,
        }
    )

    sources["sources"].append(
        {
            "id": SOURCE_ID,
            "kind": "repository-document",
            "path": "borsuk_11_k6_four_base_reduction/certificates/q00/README.md",
            "revision_pin": revision,
            "allowed_claim_ids": [CLAIM_ID],
        }
    )

    evidence["evidence"].append(
        {
            "id": EVIDENCE_ID,
            "claim_id": CLAIM_ID,
            "type": "UNSAT_CERTIFICATE",
            "epistemic_class": "COMPUTATIONAL",
            "verification_state": "CERTIFICATE_CHECKED",
            "paths": [
                "borsuk_11_k6_four_base_reduction/certificates/q00/README.md",
                "borsuk_11_k6_four_base_reduction/certificates/q00/certificate-result.json",
                ".github/workflows/q00-proof-certificate-bundle.yml",
            ],
            "commands": [
                "gh run download 30827345819 -n q00-proof-certificate",
                "gunzip -c q00.drat.gz > q00.drat && drat-trim q00_12color.cnf q00.drat -v",
            ],
            "environment": {
                "solver": "Kissat 4.0.0",
                "checker": "drat-trim revision 2e3b2dc0ecf938addbd779d42877b6ed69d9a985",
                "proof_format": "binary DRAT",
                "runner": "GitHub Actions ubuntu-24.04",
            },
            "source_revision": revision,
            "clean_room_verifier": True,
            "artifact_hashes": [
                {"artifact": "q00 compact CNF", "sha256": "36da8f78ae376b370f119d1fa16a58f6504607d949ac8315648fdbda52450299"},
                {"artifact": "q00 variable map", "sha256": "5f94c619b6a5996c54f269a88de5bfaff042e4c855ea8543869b84009c7dae45"},
                {"artifact": "q00 binary DRAT proof", "sha256": "59bf62a00d0c63b5ced7967c33421d953af5b96e423cc93dc862e595d08561b5"},
                {"artifact": "drat-trim checker binary", "sha256": "92f0aa9575ed519d66a99b8b1b3dde6ece4618ae4c202a3a4b200265dda0aa7a"},
                {"artifact": "proof-producing workflow artifact", "sha256": "e75f4a6571a22bef7f686ec6f91037f17598fecf19872d1c085113f706be2351"},
                {"artifact": "final certificate bundle artifact", "sha256": "3131aacfd28b3959b1205067c6cff2dd34403fa4029bb70702ffc63b2a2e0a54"},
                {"artifact": "final certificate metadata artifact", "sha256": "16e5510f997d21380653b641e6e02a62e13e5bf0ec769b43e9446463bc87faa9"},
            ],
            "limitations": "This certificate proves UNSAT only for the q00 universal trim CNF. It does not settle a legal diameter-6 instance, q00 refinement, or the full theorem; the Actions proof artifact expires on 2026-11-01 unless archived durably.",
        }
    )

    ledger["entries"].append(
        {
            "claim_id": CLAIM_ID,
            "gate": 2,
            "epistemic_class": "COMPUTATIONAL",
            "verification_state": "UNCHECKED",
            "lifecycle_state": "OPEN",
            "source_ids": [SOURCE_ID],
            "evidence_ids": [],
            "current_transition_id": "T-K6-Q00-1-2",
        }
    )

    transitions["chains"].append(
        {
            "claim_id": CLAIM_ID,
            "records": [
                transition(
                    "T-K6-Q00-0-1",
                    0,
                    1,
                    "Register the scoped q00 universal-trim UNSAT claim prospectively.",
                    [],
                    revision,
                ),
                transition(
                    "T-K6-Q00-1-2",
                    1,
                    2,
                    "Record exact q00 trim scope, artifact boundary, refinement requirement, and theorem non-implication.",
                    [],
                    revision,
                ),
            ],
        }
    )

    write(
        TX_23_PATH,
        transaction_plan(
            "TX-K6-Q00-2-3",
            "T-K6-Q00-1-2",
            2,
            3,
            "Link the typed q00 UNSAT certificate evidence without promoting the trim to a legal theorem result.",
            revision,
        ),
    )
    plans = [path for path in project["transaction_plans"] if path not in {TX_23_PATH, TX_34_PATH}]
    plans.append(TX_23_PATH)
    project["transaction_plans"] = plans

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
        raise SystemExit("q00 claim must be registered before Gate 3")
    if entry.get("gate") != 2 or entry.get("current_transition_id") != "T-K6-Q00-1-2":
        raise SystemExit("q00 ledger is not at the expected Gate 2 state")
    if TX_23_PATH not in project.get("transaction_plans", []):
        raise SystemExit("validated Gate 2 to Gate 3 transaction is not registered")

    claim["status"] = "attack-surface"
    claim["evidence_commands"] = [
        "gh run download 30827345819 -n q00-proof-certificate",
        "gunzip -c q00.drat.gz > q00.drat && drat-trim q00_12color.cnf q00.drat -v",
    ]
    claim["public_claim_allowed"] = True

    entry.update(
        {
            "gate": 3,
            "verification_state": "CERTIFICATE_CHECKED",
            "lifecycle_state": "WORKING",
            "evidence_ids": [EVIDENCE_ID],
            "current_transition_id": "T-K6-Q00-2-3",
        }
    )
    chain["records"].append(
        transition(
            "T-K6-Q00-2-3",
            2,
            3,
            "Link the proof trace, exact CNF and map hashes, pinned independent checker, positive verdict, and rejected corrupted-proof control.",
            [EVIDENCE_ID],
            revision,
        )
    )

    write(
        TX_34_PATH,
        transaction_plan(
            "TX-K6-Q00-3-4",
            "T-K6-Q00-2-3",
            3,
            4,
            "Register the independently checked q00 UNSAT certificate as a scoped internal obstruction.",
            revision,
        ),
    )
    plans = [path for path in project["transaction_plans"] if path not in {TX_23_PATH, TX_34_PATH}]
    plans.append(TX_34_PATH)
    project["transaction_plans"] = plans

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
        raise SystemExit("q00 claim must exist before Gate 4")
    if entry.get("gate") != 3 or entry.get("current_transition_id") != "T-K6-Q00-2-3":
        raise SystemExit("q00 ledger is not at the expected Gate 3 state")
    if TX_34_PATH not in project.get("transaction_plans", []):
        raise SystemExit("validated Gate 3 to Gate 4 transaction is not registered")

    claim["status"] = "certified-obstruction"
    claim["public_claim_allowed"] = True
    entry.update(
        {
            "gate": 4,
            "verification_state": "CERTIFICATE_CHECKED",
            "lifecycle_state": "WORKING",
            "evidence_ids": [EVIDENCE_ID],
            "current_transition_id": "T-K6-Q00-3-4",
        }
    )
    chain["records"].append(
        transition(
            "T-K6-Q00-3-4",
            3,
            4,
            "Register the pinned drat-trim verification as a scoped Gate 4 obstruction while retaining all refinement and theorem boundaries.",
            [EVIDENCE_ID],
            revision,
        )
    )
    project["transaction_plans"] = [
        path for path in project["transaction_plans"] if path not in {TX_23_PATH, TX_34_PATH}
    ]
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
    print(f"Applied q00 Cruthúnas registration stage: {args.stage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
