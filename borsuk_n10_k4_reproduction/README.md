# Borsuk n=10, k=4 independent reconstruction

This package independently reconstructs the three exact-distance-4 graphs in
Proposition 7 of Batmanov and Voronov, *The Borsuk Problem for Subsets of the
Vertices of the 10-Dimensional Boolean Cube* (arXiv:2504.01233v1).

Run:

```bash
python reproduce_n10_k4.py
```

The script uses only the Python standard library. It rebuilds the vertex sets
from the bit strings in the paper, constructs every graph edge, computes a
deterministic DSATUR coloring, verifies every edge, and writes
`n10_k4_report.json`.

Observed results:

| Cover | Vertices | Edges | Colors found |
|---|---:|---:|---:|
| Trim_10_4(U1) | 109 | 2,259 | 10 |
| U2 union W | 63 | 805 | 9 |
| U3 union W | 61 | 755 | 8 |

These are upper bounds, not exact chromatic numbers.

## Scope

This verifies the computational coloring claim in Proposition 7 for the three
sets stated in Proposition 6. It does **not** yet verify that those three sets
form a universal covering system. That coverage claim is the next independent
audit target.
