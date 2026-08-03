# Borsuk n=11, k=6 — exhaustive four-base reduction

This package reduces every nontrivial diameter-6 component with at least four vertices to one of **58 canonical trim types**.

It is a complete symmetry reduction, not a coloring proof.

## Reduction layers

After normalizing an exact-distance-6 edge to `0` and `A = 0x03f`:

1. a third vertex has five symmetry families;
2. a fourth vertex gives 149 pointwise orbits;
3. stabilizers of the chosen metric triples reduce these to 101 intermediate cases;
4. canonicalization of the entire unordered four-point base under all affine cube isometries reduces the solver frontier to **58 trim types**.

Every component with at most three vertices is trivially 12-colorable. Every larger component is contained in one of the 58 canonical trims.

See `PROOF.md` for the completeness argument and the exact eight-column-count invariant.

## Reproduce

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

## Case status

`case_status.json` tracks the 58 full-isometry types with `UNKNOWN` as the enforced default. Only certified non-UNKNOWN results belong in `overrides`.

`verify_status.py` rejects unknown case IDs, unrecognized states, missing model/proof metadata, and any attempt to call an unresolved case complete. Initially it reports:

```text
UNKNOWN: 58
SAT_CLOSED: 0
UNSAT_REFINED: 0
LEGAL_UNSAT: 0
```

## Status boundary

The 58 trims still contain pairs farther than 6 apart. A trim that is 12-colorable closes its entire isometry class. A trim that is not 12-colorable must be refined with another compatible base vertex or by exact incompatibility branching.

Heuristic coloring failures are `UNKNOWN`; they are not UNSAT evidence.
