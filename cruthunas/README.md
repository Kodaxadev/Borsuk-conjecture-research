# Cruthúnas governance layer

Cruthúnas is the deterministic repository-policy and evidence-governance layer for this Borsuk research program. It is not a mathematical prover and does not upgrade a claim merely because repository checks pass.

This integration is deliberately marked **CR-0**. It is a working repository-local pilot, not a claim of framework maturity, external conformance, publication readiness, or CR-1.

## Canonical records

- `project.json` — framework state, gates, policies, adapter locations, observation registry, and transaction plans.
- `ledger.json` — current gate, epistemic class, verification state, and lifecycle state for every registered claim.
- `sources.json` — source-document boundaries and permitted claim IDs.
- `evidence.json` — typed evidence, paths, commands, environments, hashes, and limitations.
- `observations.json` — explicitly non-evidentiary probes, benchmarks, negative controls, and heuristic records.
- `transitions.json` — contiguous status histories; every Gate 3 → Gate 4 move is explicitly registered.
- `transactions/` — serializable dry-run status-change plans.
- `schemas/` — typed evidence, observation, transition, and transaction schemas.
- `skills/cruthunas-govern/SKILL.md` — canonical governance instructions.
- `.claude/skills/...` and `.codex/skills/...` — generated adapters checked for drift.

`research/claims.json` remains the mathematical claim registry. Cruthúnas governs how those claims are supported and promoted.

## Three record classes

Cruthúnas keeps three materially different things separate:

1. **Claims** — statements whose scope and status must be governed.
2. **Evidence** — independently checkable support that may justify a gate transition.
3. **Observations** — useful run history that carries no evidentiary weight and cannot change status.

A timeout, partial proof, heuristic failure, benchmark, or bounded unresolved probe belongs in observations. It must not be smuggled into the ledger as evidence.

## Commands

```bash
python scripts/cruthunas.py check --all
python scripts/cruthunas.py check --changed
python scripts/cruthunas.py status
python scripts/cruthunas.py adapters sync
python scripts/cruthunas.py adapters check
python scripts/validate_cruthunas_transactions.py
python scripts/validate_cruthunas_observations.py
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

The checked reductions, search scaffolds, root UNSAT certificate, and deterministic SAT lane are separate Gate 4 claims or evidence records. Their evidence does not automatically transfer to the full theorem claim.

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

## Bounded solver probes

The q00–q57 workflow performs bounded exact solver probes only after Cruthúnas preflight passes. Its output is marked:

```text
PROBE_ONLY_NOT_REGISTERED_EVIDENCE
```

The first q00 Kissat 4.0.0 probe exhausted its 180-second limit and remains `UNKNOWN`. Its partial proof is not a certificate. It is registered in `observations.json` so future work can avoid repeating the same unproductive run without giving that timeout any evidentiary weight.

The workflow cannot alter `case_status.json`, `research/claims.json`, or the Cruthúnas ledger. A material SAT or UNSAT result must be preserved, hashed, independently checked, and registered through the normal evidence and transition process.

## Known CR-0 limitations

- Bootstrap `source_revision` values currently identify the active research branch. They should be replaced or supplemented by immutable commit or release hashes when the branch is frozen.
- The JSON schemas document the intended record contracts, while the standard-library validators enforce the active repository rules. No external Cruthúnas conformance suite exists yet.
- `check --changed` intentionally performs a full check rather than a minimal dependency-aware incremental calculation.
- The adapter system currently targets Claude and Codex only.
- No cryptographic signing, transparency log, external timestamping, or remote artifact registry is implemented.
- No Gate 5 or Gate 6 claim exists in this repository.

These limitations are reasons to retain the CR-0 label, not silent promises of future functionality.

## Trust boundary

Cruthúnas checks repository coherence, including claim registration, dependency acyclicity, evidence typing, observation separation, transition continuity, artifact existence, transaction consistency, adapter synchronization, and support matching. It does not establish mathematical correctness, novelty, priority, external acceptance, publication readiness, CR-1, or framework maturity.
