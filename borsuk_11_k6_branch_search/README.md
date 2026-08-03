# Borsuk n=11, k=6 — diameter-compatible branch search

This package is the executable scaffold for the remaining diameter-6 theorem target.

It does **not** claim that the case is solved. It establishes the root object, both required graph relations, canonical hashes, and the first exact branch in a coverage manifest.

## Root definition

Fix the origin and the distance-6 neighbor `A = 0x03f`. The root trim set is

```text
T = {x in {0,1}^11 : weight(x) is even, weight(x) <= 6, d(x,A) <= 6}.
```

Two relations are regenerated independently:

- `G6`: Hamming distance exactly 6, used for 12-coloring;
- `D`: Hamming distance greater than 6, whose edges are forbidden in a legal diameter-6 set.

Expected root data:

- vertices: 692
- exact-distance-6 edges: 104,606
- incompatibility edges: 37,470
- vertex SHA-256: `ece78553536e8cbac3404fb77db0096352024b1dbf15ea4f129d782a1755590d`
- `G6` edge SHA-256: `28aeb05060799feae42e3af33d51a66f852f0e6308cb737f0326bcda0af17c3f`
- `D` edge SHA-256: `cc2059f512d2210f1c654c0ae7cbc1f00db22e29cc7fa6d1279e6b77a2f68828`

## Verify

```bash
python generate_root.py --write-report root_report.json
node verify_root_independent.js
python verify_manifest.py
```

The Python and JavaScript implementations independently regenerate the same vertex and edge hashes.

## Initial manifest

`manifest.json` records:

- the certified root UNSAT obstruction by claim reference;
- a deterministic incompatibility edge `003--0fc` at distance 8;
- the two required children obtained by deleting opposite endpoints;
- both children as `UNKNOWN`, because no solver result or certificate has yet been produced for them.

The manifest verifier reconstructs every node set from first principles, checks hashes and parent-child deletions, validates the incompatibility branch, and confirms the root certificate claim has repository status `certified-obstruction`.

## Result-state discipline

Every future node must be exactly one of:

- `SAT_CLOSED`: verified coloring witness;
- `UNSAT_BRANCHED`: checked UNSAT certificate and both incompatibility children;
- `LEGAL_UNSAT`: checked UNSAT certificate with no incompatibility edge;
- `UNKNOWN`: incomplete, timed out, crashed, or missing required evidence.

No theorem-level conclusion is permitted while an `UNKNOWN` leaf remains.

See `docs/K6-EXECUTION-PLAN.md` for the complete search and coverage requirements.
