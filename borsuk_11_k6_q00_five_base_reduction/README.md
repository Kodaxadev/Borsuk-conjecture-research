# q00 five-base reduction

## Scoped reduction

Fix the canonical q00 four-point base

```text
0x000, 0x03f, 0x1c7, 0x64b
```

and its 436-vertex universal trim. Every legal diameter-6 component represented by q00 that contains at least five vertices has a fifth vertex compatible with all four base points. There are 432 possible fifth vertices.

Canonicalizing the resulting unordered five-point bases under all affine cube isometries reduces those 432 choices to **12 five-base trim types**.

Components with at most four vertices are trivially 12-colorable. Therefore the legal q00 case is covered by these 12 child trim types, subject to independent verification and Cruthúnas registration.

## Exact generated data

- parent q00 vertices: 436
- parent exact-distance-6 edges: 39,600
- parent distance-greater-than-6 pairs: 13,104
- fifth-vertex candidates: 432
- canonical unordered five-base types: 12
- child trim-size range: 334–428 vertices
- case-list SHA-256: `d5b0825cd8645af2c595b3de3c851360e0b283d8ce61383482f76168e1ae9855`
- fifth-vertex assignment SHA-256: `6c94923a260290d59727bdcad68293b7f1962a7c5377885dd536fefa5962ffc7`

## Reproduce independently

```bash
python generate_cases.py --output canonical_12.csv --assignment-output fifth_assignments.csv
node verify_independent.js
python verify_status.py
```

The Python generator and JavaScript verifier independently enumerate all 2,048 cube vertices, reconstruct q00, canonicalize every fifth-point extension, compute every child trim, and reproduce both hashes.

## Mathematical boundary

This is a finite symmetry reduction, not a coloring result.

- All 12 child trim types remain `UNKNOWN`.
- Each child is still a universal trim and may contain pairs farther than Hamming distance 6.
- A SAT child requires an independently checked coloring witness.
- A proof-checked UNSAT child requires another compatible-base or incompatibility refinement.
- This package does not change q00 in the parent `case_status.json`.
- This package does not promote the full `n=11,k=6` theorem target.

See `PROOF.md` for the coverage and canonicalization argument.
