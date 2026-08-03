# Project status ledger

Updated: 2026-08-02

This file summarizes the human-readable state. The machine-readable source of truth is [`research/claims.json`](../research/claims.json).

## Active theorem target

The unresolved target is the diameter-6 subcase of the 0/1-Borsuk problem in dimension 11:

> Every diameter-6 subset of the 11-dimensional Boolean cube is partitionable into at most 12 subsets of smaller diameter.

This claim remains **open** in the repository.

## Established package-level evidence

### n=10, k=4 reproduction

The published coloring computation for the three stated cover graphs has been independently reconstructed. This verifies the coloring step within the package's stated scope; it does not independently verify universal coverage.

### n=11, k=4 candidate

The package contains a structural proof, explicit coloring witnesses, and independent Python and JavaScript verification. It remains a candidate proof pending external mathematical and priority review.

### n=11, k=8 candidate

The package contains an explicit 12-coloring of the universal even-weight cover and independent Python and JavaScript verification. It remains a candidate proof pending external mathematical and priority review.

### n=11, k=6 attack surface

The one-base normalization produces a canonical trim graph with 692 vertices and 104,606 exact-distance-6 edges. This is a universal cover for possible normalized components, not a legal diameter-6 set.

### n=11, k=6 certified obstruction

The canonical trim graph has a checked UNSAT certificate for 12-colorability. This proves that the one-base cover is too coarse. It does **not** disprove or settle the diameter-6 theorem target because the trim graph contains pairs farther than 6 apart.

### n=11, k=6 branch-search scaffold

The root is independently regenerated with:

- 692 vertices;
- 104,606 exact-distance-6 coloring edges;
- 37,470 distance-greater-than-6 incompatibility edges;
- matching Python and JavaScript SHA-256 hashes.

The initial coverage manifest imports the root certified obstruction by claim reference and branches on the lexicographically first incompatibility edge `003--0fc`, whose Hamming distance is 8. The two 691-vertex children are recorded with verified vertex-set hashes and remain `UNKNOWN`.

## Current research frontier

The next exact layer must resolve those two first-level child nodes and then continue recursively:

- a verified SAT coloring closes a node and every descendant;
- a proof-checked UNSAT node must branch on a remaining distance-greater-than-6 pair;
- a legal proof-checked UNSAT node is a counterexample candidate;
- a timeout, crash, or missing certificate remains `UNKNOWN`.

Full details are in [`K6-EXECUTION-PLAN.md`](K6-EXECUTION-PLAN.md).

## Promotion boundary

No repository summary, paper draft, social post, or release should claim that the full dimension-11 Boolean-cube result is solved unless:

1. the diameter-compatible k=6 coverage tree is complete;
2. every SAT leaf has an independently checked coloring;
3. every UNSAT branch has an independently checked proof trace;
4. no branch remains `UNKNOWN`;
5. the mathematical normalization and coverage argument is independently reviewed;
6. novelty and attribution are checked against the literature and relevant authors.
