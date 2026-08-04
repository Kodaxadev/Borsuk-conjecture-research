# Contributing to Borsuk Conjecture Research

This repository is a mathematical research archive governed by the repository-local **Cruthúnas CR-0** evidence layer. Contributions must preserve clarity, reproducibility, provenance, and independently auditable claim status.

## Before changing research state

Read:

- `cruthunas/skills/cruthunas-govern/SKILL.md`
- `cruthunas/project.json`
- `research/claims.json`
- `cruthunas/ledger.json`

Then run:

```bash
python scripts/cruthunas.py status
python scripts/cruthunas.py check --changed
```

Identify the exact registered claim IDs affected by the change. Do not create or promote a material claim only in prose, a README, solver log, or case-status file.

## Contribution expectations

Every contribution should:

- explain the mathematical context;
- preserve exact claim scope and non-implications;
- use a registered status such as candidate proof, reproduction, attack surface, certified obstruction, or open target;
- include verification instructions or a clear script entry point;
- preserve provenance for generated witnesses, solver output, proof traces, and coverage manifests;
- record environment, solver version, seed, limits, and source revision where computational work is involved;
- provide SHA-256 hashes for central immutable artifacts;
- distinguish `SAT`, `UNSAT`, and `UNKNOWN` exactly;
- include independent verification whenever practical.

## Cruthúnas evidence and transitions

A new material result requires:

1. a typed record in `cruthunas/evidence.json`;
2. artifact paths that exist in the repository;
3. reproducibility commands and environment information;
4. a source boundary registered in `cruthunas/sources.json`;
5. a serializable dry-run transaction for any status change;
6. a contiguous record in `cruthunas/transitions.json`;
7. a matching update to `cruthunas/ledger.json` only after the evidence and transition exist.

Every Gate 3 → Gate 4 transition must be explicitly registered. No freehand gate or verification-state edits are allowed.

Cruthúnas passing means the governance records are coherent. It does not establish mathematical truth, novelty, external review, publication readiness, CR-1, or framework maturity.

## Preferred workflow

1. Create or extend a package-specific subdirectory.
2. Add or update a package-local `README.md`.
3. Add deterministic generators, witnesses, certificates, verifiers, and hash records.
4. Update the mathematical claim registry only within the exact supported scope.
5. Add or amend Cruthúnas sources, evidence, transition history, and ledger state.
6. Synchronize generated adapters if the canonical governance skill changes:

```bash
python scripts/cruthunas.py adapters sync
```

7. Run the complete checks:

```bash
python scripts/cruthunas.py check --all
python scripts/cruthunas.py adapters check
make verify
make status
```

## The 58-case k=6 frontier

A change to `borsuk_11_k6_four_base_reduction/case_status.json` is not sufficient by itself to establish a material result.

For a case to leave `UNKNOWN`:

- `SAT_CLOSED` requires a complete coloring witness and an independent verifier;
- `UNSAT_REFINED` requires a checked proof trace plus the exact refinement or incompatibility branch that preserves coverage;
- `LEGAL_UNSAT` requires a checked proof trace and independent confirmation that no distance-greater-than-6 pair remains;
- timeout, crash, resource exhaustion, missing proof, or heuristic failure remains `UNKNOWN`.

A material case resolution must also be registered as typed Cruthúnas evidence under `n11-k6-four-base-reduction`, or as a new child claim if it introduces a reusable theorem-level statement. The full `n11-k6-full` claim must remain Gate 2 and open until all required cases and refinements are covered with independently checked evidence.

## Review norms

Research changes should be reviewed for:

- correctness of the mathematical statement;
- exact logical scope and limitations;
- reproducibility of the verification path;
- source-document boundaries;
- claim dependency integrity;
- certificate and coverage completeness;
- consistency between the claim registry and Cruthúnas gate tuple;
- clarity around what is proven, computationally checked, candidate, or unresolved.

## Pull requests

A pull request should explain:

- the research question being addressed;
- the affected claim IDs;
- the artifact or proof package changed;
- the Cruthúnas evidence and transition records added;
- the verification commands run;
- the interpretation and limitations of the evidence;
- whether any `UNKNOWN` dependency remains.
