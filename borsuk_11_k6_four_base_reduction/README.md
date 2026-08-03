# Borsuk n=11, k=6 — exhaustive four-base reduction

This package reduces every nontrivial diameter-6 component with at least four vertices to one of **101 canonical trim cases**.

It is a complete symmetry reduction, not a coloring proof.

## Mathematical role

After normalizing an exact-distance-6 edge to

```text
0 and A = 0x03f,
```

any third vertex falls into five cases up to the setwise symmetry that exchanges `0` and `A`:

```text
(1,1), (2,0), (2,2), (3,1), (3,3).
```

For each third vertex `B`, the pointwise stabilizer of `{0,A,B}` classifies a fourth vertex `C` by coordinate-block counts. Setwise symmetries of the unordered base reduce 149 pointwise classes to 101 cases.

Every component with at most three vertices is trivially 12-colorable. Every larger component is contained in one of the 101 listed four-base trims.

## Reproduce

```bash
python generate_cases.py
node verify_independent.js
```

Both implementations verify:

- pointwise fourth-vertex orbits: 149;
- setwise four-base cases: 101;
- trim size range: 436–612 vertices;
- every stored representative's vertex count, exact-distance-6 edge count, incompatibility count, and canonical vertex hash.

`case_representatives.csv` is the canonical branch list for downstream coloring and certificate work.

## Status boundary

The 101 trims still contain pairs farther than 6 apart. A trim that is 12-colorable closes its entire branch. A trim that is not 12-colorable must be refined with another compatible base vertex or by exact incompatibility branching.

Heuristic coloring failures are `UNKNOWN`; they are not UNSAT evidence.
