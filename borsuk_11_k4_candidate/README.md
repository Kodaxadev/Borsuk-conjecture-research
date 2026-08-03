# Borsuk \(n=11,\ k=4\) candidate proof package

This package advances the Batmanov--Voronov \(n=10,\ k=4\) covering argument
to dimension 11 and supplies independently checkable coloring witnesses.

Run:

```bash
python verify.py
```

Expected reconstructed cover data:

| Cover | Vertices | Edges | Colors |
|---|---:|---:|---:|
| triangle trim, even component | 109 | 3,123 | 12 |
| 3-star plus even radius-two ball | 64 | 1,222 | 10 |
| 5-top plus even radius-two ball | 61 | 1,135 | 9 |

The verifier also enumerates all maximal cliques of \(J(11,4)\), obtaining:

* 165 stars of size 8;
* 462 tops of size 5;
* no other maximal-clique type.

## Files

* `PROOF.md` — complete reduction and elementary structural proof.
* `HOSTILE_AUDIT.md` — explicit attack surface and responses.
* `witness.json` — explicit vertex-to-color witnesses.
* `verify.py` — standard-library-only Python verifier and Johnson-clique enumerator.
* `verify_independent.js` — separately implemented Node.js graph/witness verifier.
* `report.json` — generated verification report.
* `dependency_graph.json` — claim/dependency map for Cruthúnas-style auditing.

## Status

This is a compact candidate proof of the diameter-4 subcase in dimension 11,
not yet a literature-checked publication claim for the entire \(n=11\)
0/1-Borsuk problem. The unresolved even diameters remain \(k=6\) and \(k=8\).
