# q00r00 sixth-base one-sided 12-colorability screen

## Governed target

This package screens the 36 execution-bound universal child trims `q00r00-s000` through `q00r00-s035` for 12-colorability.

It consumes only the exact archived child-trim artifact:

```text
borsuk_11_k6_q00r00_sixth_base_child_trims/
  evidence/artifacts/q00r00-sixth-base-child-trims-run-30851783510.zip
```

with SHA-256:

```text
a1862053e19a4341b941e62181c180805fb59a7969241d473705635dd04d0505
```

## Asymmetric result rule

```text
SAT + directly checked coloring
→ proves the complete universal trim 12-colorable
→ every legal subset inside it is 12-colorable
→ child branch closes

UNSAT + drat-trim-checked proof
→ proves only the universal trim non-12-colorable
→ child remains UNKNOWN because legal subsets exclude incompatible pairs
→ child enters compatible seventh-base refinement
```

Timeouts, crashes, missing witnesses, missing proofs, failed checks, and unsupported solver outputs remain `UNKNOWN`.

## Canonical instances

`build_instances.py` reconstructs each graph from the archived trim vertices and exact-distance-six edge list. It uses a deterministic greedy clique, ordered by descending graph degree and then ascending vertex, to fix color labels and remove forbidden fixed-clique colors from each remaining vertex domain.

Variables are assigned by ascending vertex and then ascending allowed color. The CNF contains:

1. one at-least-one-color clause per vertex;
2. all pairwise at-most-one-color clauses inside each vertex domain;
3. one conflict clause for every exact-distance-six edge and color present in both endpoint domains.

`verify_instances.js` independently reconstructs every clique, domain, variable assignment, clause count, and exact CNF hash.

## Solver and certificate checks

The workflow builds pinned Kissat 4.0.0 and a pinned `drat-trim` revision once, then runs 36 independent matrix jobs.

- SAT output is decoded and checked directly against every exact-distance-six edge by `verify_coloring.py`.
- UNSAT output is accepted only when a nonempty proof is independently accepted by `drat-trim`.
- Every case produces its own artifact and bounded result record.
- A final summary records only checked results and preserves the one-sided interpretation.

## Mathematical boundary

No checked UNSAT universal-trim result closes a child. `q00r00` can close only when all 36 children receive checked SAT colorings. `q00`, and `n11-k6-full` remain unchanged by this package.
