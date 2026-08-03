# SAT workflow for the 58 canonical trim types

This workflow separates instance generation, solver execution, witness or proof checking, and repository status updates.

A solver transcript is never a certificate by itself.

## 1. Inspect a type without writing large artifacts

```bash
python build_instance.py q00 --metadata-only
```

This regenerates the canonical representative and reports its base, graph size, contained symmetry-breaking clique, variable count, and clause count.

## 2. Generate a deterministic instance

```bash
python build_instance.py q00 --output-dir work/q00
```

The generated directory contains:

- `q00_12color.cnf`
- `q00_variable_map.json`
- `q00_metadata.json`

The metadata records the canonical case-list hash, all covered intermediate cases, graph statistics, CNF hash, variable-map hash, and `UNKNOWN` as the initial result state.

Generated work files are ignored by Git. Only checked result artifacts and compact manifests should be promoted into the repository.

## 3. Run a solver

Use a solver invocation that preserves exact version, command, seed, limits, exit code, stdout, stderr, and—when claiming UNSAT—a proof trace.

Conceptually:

```bash
<proof-producing-solver> work/q00/q00_12color.cnf \
  > work/q00/solver.out \
  2> work/q00/solver.err
```

Do not infer the result from elapsed time or the absence of a model.

Possible research states are:

- a complete SAT model is present;
- a proof-producing UNSAT result and proof trace are present;
- anything else is `UNKNOWN`.

## 4. Verify SAT independently

```bash
python verify_model.py \
  q00 \
  work/q00/solver.out \
  --output work/q00/q00_verified_coloring.json
```

The verifier does not trust the stored edge list or variable map. It regenerates the canonical trim and every exact-distance-6 edge from the case id, decodes exactly one color per vertex, rejects out-of-range variables, and checks every edge.

It explicitly rejects UNSAT text presented as a model.

A SAT type may become `SAT_CLOSED` only after:

- the model verifies;
- the verified coloring artifact is stored;
- all artifact hashes are recorded;
- checker output is preserved;
- the corresponding `case_status.json` override passes `verify_status.py`.

## 5. Verify UNSAT independently

An UNSAT type may not be recorded from solver stdout alone.

Required evidence:

- the exact CNF and SHA-256 hash;
- a proof trace produced for that CNF;
- an independent proof checker accepting the trace;
- checker command, version, output, and output hash;
- a subsequent exhaustive refinement because the trim may still contain pairs farther than 6.

After proof checking, the state is normally `UNSAT_REFINED`, not a theorem conclusion. Refine by either:

- an exhaustive symmetry-reduced fifth compatible base; or
- an exact incompatibility branch covering both endpoint deletions.

Only proof-checked UNSAT with zero incompatibility pairs may be labeled `LEGAL_UNSAT`.

## 6. Record status

`case_status.json` has `UNKNOWN` as the default for all 58 types. Add an override only for a certificate-backed result.

SAT example shape:

```json
{
  "q00": {
    "state": "SAT_CLOSED",
    "coloring_artifact": "results/q00/verified_coloring.json",
    "result_sha256": "<sha256>",
    "verification_command": "python verify_model.py q00 results/q00/solver.out --output results/q00/verified_coloring.json",
    "checker_output_sha256": "<sha256>"
  }
}
```

UNSAT-refined example shape:

```json
{
  "q00": {
    "state": "UNSAT_REFINED",
    "proof_artifact": "results/q00/proof.drat",
    "result_sha256": "<sha256>",
    "verification_command": "<independent proof-check command>",
    "checker_output_sha256": "<sha256>",
    "children": ["q00-child-...", "q00-child-..."]
  }
}
```

These are schema illustrations, not existing results.

## 7. Re-run repository verification

```bash
make validate
make verify
make status
```

The theorem target remains open until every canonical type and every required descendant has certificate-backed coverage and no `UNKNOWN` remains.

## Deterministic smoke test

`verify_sat_lane.py` generates `q00` in a temporary directory and freezes:

- vertices: 436
- edges: 39,600
- variables: 5,232
- clauses: 504,422
- CNF SHA-256: `b07c254b71ae0964851afb8dd9f7fa8a728433e27ae76a327e5c10a6e6e7df55`
- variable-map SHA-256: `742bf72f1ae30dc207e22a0c7efe1033ee6e4a5361987ed9e2f8ed3e2b85ed7d`

The same test runs negative controls against the model verifier.
