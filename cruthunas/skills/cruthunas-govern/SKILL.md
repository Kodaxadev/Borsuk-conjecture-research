# cruthunas-govern

Cruthúnas is the deterministic evidence-governance layer for this repository. It is not a theorem prover, SAT solver, or substitute for mathematical review.

## Mandatory startup

Before changing mathematical status, proof text, solver outputs, manifests, or public summaries:

1. Read `cruthunas/project.json`.
2. Read `research/claims.json` and `cruthunas/ledger.json`.
3. Identify the exact claim IDs affected.
4. Read their registered source and evidence records.
5. Run `python scripts/cruthunas.py status`.

## Claim discipline

- Do not create an unregistered material claim.
- Do not change a gate or verification state by editing the ledger alone.
- Add a typed evidence record first.
- Add a contiguous transition record with source revision, actor, reason, and evidence references.
- Gate 3 to Gate 4 transitions must be explicitly registered.
- Candidate proofs may not be described as externally reviewed, published, or settled.
- The full `n11-k6-full` claim remains open while any required case is `UNKNOWN`.

## Solver discipline

Record solver results as exactly one of:

- `SAT`: complete witness and independent verification;
- `UNSAT`: proof trace and independent proof checking;
- `UNKNOWN`: timeout, resource limit, crash, incomplete run, missing proof, or checker failure.

Never infer UNSAT from failure to find a coloring.

## Source boundaries

Use only source documents registered for the affected claim. A source registered to one claim does not authorize promotion of a different claim. Preserve exact theorem scope and non-implications.

## Evidence requirements

Computational evidence must include:

- deterministic generator or canonical input;
- artifact paths;
- reproducibility commands;
- environment and tool information;
- source or revision pin;
- hashes for central generated artifacts where available;
- limitations;
- clean-room or independent verifier status.

## Required checks

Run before proposing a research change:

```bash
python scripts/cruthunas.py check --all
python scripts/cruthunas.py adapters check
make verify
```

`check --changed` is allowed during iteration, but CR-0 conservatively performs the full governance validation.

## Promotion boundary

Cruthúnas passing means the repository's governance records are internally coherent. It does not establish mathematical truth, originality, external acceptance, publication readiness, framework maturity, CR-1, or conformance beyond this repository-local CR-0 pilot.
