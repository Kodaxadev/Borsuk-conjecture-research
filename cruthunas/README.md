# Cruthúnas governance layer

Cruthúnas is the deterministic repository-policy and evidence-governance layer for this Borsuk research program. It is not a mathematical prover and does not upgrade a claim merely because repository checks pass.

This integration is deliberately marked **CR-0**. It is a working repository-local pilot, not a claim of framework maturity, external conformance, publication readiness, or CR-1.

## Canonical records

- `project.json` — framework state, gates, policies, and adapter locations.
- `ledger.json` — current gate, epistemic class, verification state, and lifecycle state for every registered claim.
- `sources.json` — source-document boundaries and permitted claim IDs.
- `evidence.json` — typed evidence, paths, commands, environments, hashes, and limitations.
- `transitions.json` — contiguous status histories; every Gate 3 → Gate 4 move is explicitly registered.
- `schemas/` — typed evidence and transition schemas.
- `skills/cruthunas-govern/SKILL.md` — canonical governance instructions.
- `.claude/skills/...` and `.codex/skills/...` — generated adapters checked for drift.

`research/claims.json` remains the mathematical claim registry. Cruthúnas governs how those claims are supported and promoted.

## Commands

```bash
python scripts/cruthunas.py check --all
python scripts/cruthunas.py check --changed
python scripts/cruthunas.py status
python scripts/cruthunas.py adapters sync
python scripts/cruthunas.py adapters check
```

At CR-0, `check --changed` intentionally falls back to the complete governance check. This is slower but prevents an incomplete changed-file calculation from bypassing a cross-claim dependency or source-boundary violation.

## Gate meanings

1. `REGISTERED`
2. `SCOPED`
3. `EVIDENCE_LINKED`
4. `INTERNALLY_CHECKED`
5. `EXTERNALLY_REVIEWED`
6. `PUBLICATION_FROZEN`

A Gate 4 entry may still be a candidate proof, attack surface, or scoped obstruction. Gate numbers describe governance completion, not theorem importance or truth.

## Current active target

The full `n11-k6-full` theorem target is intentionally held at:

```text
Gate 2; MATHEMATICAL; [UNCHECKED]; OPEN
```

The checked reductions, search scaffolds, and root UNSAT certificate are separate Gate 4 claims. Their evidence does not automatically transfer to the full theorem claim.

## Status-change procedure

A status change must be prepared as a serializable dry-run transaction before editing the live ledger:

1. identify the exact claim ID;
2. state the expected current transition ID;
3. name the contiguous gate move;
4. register typed evidence and artifact paths;
5. pin the source revision and environment;
6. record actor, reason, limitations, and non-implications;
7. run Cruthúnas checks in dry-run form;
8. apply the evidence, transition, and ledger changes together in one reviewable change.

No freehand gate edits are permitted.

## Trust boundary

Cruthúnas checks repository coherence, including claim registration, dependency acyclicity, evidence typing, transition continuity, artifact existence, adapter synchronization, and support matching. It does not establish mathematical correctness, novelty, priority, or external acceptance.
