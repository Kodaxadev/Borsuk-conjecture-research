# Borsuk n=11, k=6 — exhaustive four-base reduction

This package reduces every nontrivial diameter-6 component with at least four vertices to one of **58 canonical trim types**.

It is a complete symmetry reduction and solver workspace, not a coloring proof.

## Reduction layers

After normalizing an exact-distance-6 edge to `0` and `A = 0x03f`:

1. a third vertex has five symmetry families;
2. a fourth vertex gives 149 pointwise orbits;
3. stabilizers of the chosen metric triples reduce these to 101 intermediate cases;
4. canonicalization of the entire unordered four-point base under all affine cube isometries reduces the solver frontier to **58 trim types**.

Every component with at most three vertices is trivially 12-colorable. Every larger component is contained in one of the 58 canonical trims.

See `PROOF.md` for the completeness argument and the exact eight-column-count invariant.

## Reproduce the reduction

```bash
python generate_cases.py \
  --raw-output intermediate_101.csv \
  --output canonical_58.csv
node verify_independent.js
python verify_status.py
sha256sum intermediate_101.csv canonical_58.csv
```

Both implementations independently verify:

- pointwise fourth-vertex orbits: 149;
- intermediate triple-stabilizer cases: 101;
- full-isometry trim types: 58;
- trim size range: 436–612 vertices;
- canonical LF-normalized hashes:

```text
intermediate 101: e60f5f81120e42c8c7eae2da299105e802266f6e92629cd6ac6ee24bcef9db19
canonical 58:    08913feaddbc0f930b6ef90a1677fbc4577cb23dcb6f4dac8987e37056d34742
```

The CSV files are generated rather than checked in so both languages define and verify the lists independently.

## Deterministic solver inventory

```bash
python build_inventory.py --output inventory.csv
```

This orders all 58 types by deterministic CNF size and records graph density, incompatibility density, fixed-clique size, variable count, and clause count. It is a scheduling inventory, not an empirical hardness claim.

Before encoding, a bounded deterministic clique search tries to find a full 12-clique for color-symmetry breaking. If that search exceeds its fixed node budget, the generator falls back to a verified deterministic clique. Across the current 58-type inventory, two types receive full 12-clique fixing; all other fixed cliques remain valid but smaller.

Inventory SHA-256:

```text
860fc2d3762a6956afda8739e651aa0f03fe7b4fce6686267d038f113f43a9a5
```

## SAT lane

Inspect or generate a canonical instance:

```bash
python build_instance.py q00 --metadata-only
python build_instance.py q00 --output-dir work/q00
```

Verify a returned SAT model independently:

```bash
python verify_model.py q00 work/q00/solver.out \
  --output work/q00/q00_verified_coloring.json
```

`q00` contains a verified 12-clique, so all 12 color labels are fixed before search. `verify_sat_lane.py` freezes the resulting deterministic CNF and variable-map hashes in a temporary directory and runs negative controls against the model verifier.

See [`SAT-WORKFLOW.md`](SAT-WORKFLOW.md) for the exact SAT, UNSAT, and artifact-recording contract.

## Case status

`case_status.json` tracks the 58 full-isometry types with `UNKNOWN` as the enforced default. Only certificate-backed non-UNKNOWN results belong in `overrides`.

Initially:

```text
UNKNOWN: 58
SAT_CLOSED: 0
UNSAT_REFINED: 0
LEGAL_UNSAT: 0
```

## Probe history

`probe-history/` records bounded exploratory runs that did not produce certificate-backed results. These records cannot alter `case_status.json` or Cruthúnas evidence state.

The first `q00` Kissat probe used the earlier 10-clique encoding and ended `UNKNOWN` after 180 seconds. The current 12-clique encoding has a different CNF hash, so the old run is retained only as operational history and is not directly comparable evidence.

## Status boundary

The 58 trims still contain pairs farther than 6 apart. A trim that is 12-colorable closes its entire isometry class. A trim that is not 12-colorable must be refined with another compatible base vertex or by exact incompatibility branching.

Heuristic coloring failures are `UNKNOWN`; they are not UNSAT evidence.
