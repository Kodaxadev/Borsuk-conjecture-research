# q00 fifth-base refinement

This package refines the proof-checked UNSAT result for the canonical `q00`
universal trim into an exhaustive finite frontier of **12 fifth-base child
trims**.

It is a symmetry reduction and solver workspace. It does not resolve any child
trim, does not change `q00` in `case_status.json`, and does not promote the full
`n=11, k=6` theorem target.

## Exact result

Fix the q00 four-point base

```text
0, 63, 455, 1611
```

and its 436-vertex universal trim. The full affine cube-isometry stabilizer of
the unordered base has order 384. It partitions the 432 nonbase trim vertices
into exactly 12 orbits.

Any legal q00-compatible diameter-6 family containing more than the four base
points contains a fifth point. After a stabilizer isometry, that point is one
of the 12 representatives in `canonical_12.csv`, and the whole family lies in
the corresponding fifth-base child trim. A family containing only the four
base points is trivially 12-colorable.

The 12 child trims contain 334–428 vertices. They remain universal covers and
may still contain incompatible pairs at distance greater than 6.

## Reproduce

```bash
python generate_fifth_base_cases.py \
  --output canonical_12.csv \
  --report report.json
node verify_independent.js
python verify_status.py
```

Both implementations independently verify:

- q00 parent vertices: 436;
- nonbase fifth-point candidates: 432;
- unordered-base stabilizer order: 384;
- fifth-base orbits: 12;
- orbit sizes sum to 432;
- child trim size range: 334–428;
- canonical CSV SHA-256:

```text
01b3ee2e629788037f1ccd6906140302abddd1ae1c077aa8cf7e8f619adb807a
```

## Deterministic child instance

Generate a compact list-coloring CNF for one child:

```bash
python build_child_instance.py f11 --metadata-only
python build_child_instance.py f11 --output-dir work/f11
```

`f11` is the smallest current child and contains a deterministic 12-clique. Its
compact smoke-test instance has:

- 334 vertices;
- 22,502 exact-distance-6 edges;
- 2,049 variables;
- 72,430 clauses;
- CNF SHA-256 `4341c1d9ba4b293f79e48b7a094e757d0c09aa46024d67e9a6f4556f3d3c2388`;
- variable-map SHA-256 `ff5b5f9df7c3364d79dcdf0942cc7ee58fb63a7d1911e7fa2ed4bb60da511f20`.

These hashes freeze the execution lane, not a SAT or UNSAT result.

## Status boundary

`child_status.json` keeps all 12 children `UNKNOWN`. A verified SAT coloring
closes that fifth-base orbit. A proof-checked UNSAT child requires another
compatible base or exact incompatibility branching because the child is still
a universal trim.
