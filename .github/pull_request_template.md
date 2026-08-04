## Summary

Describe the mathematical package, inference, artifact, or governance record changed.

## Affected claims

List every affected claim ID from `research/claims.json`.

- Claim IDs:
- Existing Cruthúnas gate tuple(s):
- Proposed gate tuple(s), if any:

## Cruthúnas evidence and transitions

- [ ] Registered or updated typed evidence in `cruthunas/evidence.json`.
- [ ] Preserved source-document boundaries in `cruthunas/sources.json`.
- [ ] Added a serializable dry-run transaction before any status change.
- [ ] Added a contiguous transition record.
- [ ] Updated `cruthunas/ledger.json` only after evidence and transition records existed.
- [ ] Did not promote a candidate, obstruction, cover, timeout, or heuristic result beyond its exact scope.
- [ ] Claude and Codex adapters remain synchronized.

Explain the evidence, transition, limitations, and non-implications. Write `No status change` where appropriate.

## Solver result state

For computational changes, record exactly one:

- `SAT` — complete witness and independent verification attached.
- `UNSAT` — proof trace and independent proof checking attached.
- `UNKNOWN` — timeout, crash, resource limit, incomplete search, or missing certificate.
- `Not applicable`.

Never use solver failure or timeout as UNSAT evidence.

## Verification

List the commands used, including:

```bash
python scripts/cruthunas.py check --all
python scripts/cruthunas.py adapters check
make verify
make status
```

Add any package-specific verifier, SAT model checker, proof checker, or negative-control command.

## Scope and unresolved dependencies

State:

- the exact claim supported;
- what the evidence does not prove;
- whether any `UNKNOWN` case, branch, or dependency remains;
- whether novelty, external review, or publication readiness has been established.

Cruthúnas passing establishes repository coherence only. It does not establish mathematical truth, novelty, external acceptance, publication readiness, CR-1, or framework maturity.
