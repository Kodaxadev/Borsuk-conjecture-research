# Conservative seventh-base classification

Claim: `n11-k6-q00r00-seventh-base-classification`

This package classifies compatible seventh vertices for every incomplete sixth-base case `q00r00-s000` through `q00r00-s035`.

The refinement is conservative. The sixth-base colorability screen produced no checked SAT coloring and no proof-checked UNSAT certificate. All 36 inputs remain `UNKNOWN`; none is a certified obstruction.

## Frozen source boundary

The package consumes the execution-bound child-trim archive:

```text
q00r00-sixth-base-child-trims-run-30851783510.zip
sha256:a1862053e19a4341b941e62181c180805fb59a7969241d473705635dd04d0505
```

It also requires the repository-governed sixth-base screen binding at commit `2c7727666966fc1e0ad9657b3424e0616cab25e8` and the synchronized status commit `3b502090b0a0c246645b408c561c6a258ca46dbe`.

## Classification algorithm

For each six-point base:

1. Reconstruct the complete compatible trim from all 2,048 cube vertices.
2. Enumerate the full unordered setwise stabilizer among parity-preserving affine cube isometries `x -> P(x) xor t`.
3. Verify identity, closure, exact base-set preservation, and every induced base permutation.
4. Remove the six base vertices to obtain the seventh-vertex candidate set.
5. Partition the candidates into stabilizer orbits.
6. Record a canonical representative and an explicit stabilizer transformation from that representative to every orbit member.
7. Construct the corresponding seven-point base and independently reconstruct its universal trim.
8. Record exact vertex, distance-six edge, and incompatible-pair counts.
9. Assign a raw 12-color CNF size proxy for scheduling only.

Grandchildren are named within their parent only:

```text
q00r00-s012-t000
q00r00-s012-t001
...
```

There is no cross-child merging, isomorphism collapse, or recanonicalization.

## Independent reproduction

`classify.py` is the primary Python implementation.

`verify_independent.js` independently reconstructs every six-base stabilizer, candidate set, orbit partition, representative mapping, grandchild trim, and graph count. It does not trust the Python child JSON files. Both implementations must produce the same canonical classification stream hash.

A pointwise-stabilizer partition is also generated as a negative control. It must over-split the classification relative to the unordered setwise action.

## Frozen local result

```text
sixth-base inputs:                         36
compatible seventh candidates:             10,297
canonical grandchildren:                   4,476
pointwise negative-control cases:           8,483
setwise stabilizer orders:                  1–144
per-child canonical orbit counts:           9–291
grandchild trim sizes:                      177–324
distance-six edge counts:                   5,744–21,078
incompatible-pair counts:                   1,632–6,347
canonical classification stream SHA-256:    932c4ed2ffc689ce5b5fe5cea07eec9876734159186df70b598b6f3ec316f6de
```

## Scheduling inventory

The raw CNF proxy uses 12 variables per vertex, one at-least-one and 66 at-most-one clauses per vertex, and 12 edge clauses per distance-six edge. It is a deterministic size proxy, not a prediction of solver behavior and not a SAT result.

```text
PILOT   <= 100,000 raw clauses:              15
SMALL   <= 150,000 raw clauses:             816
MEDIUM  <= 200,000 raw clauses:           2,573
LARGE   >  200,000 raw clauses:           1,072
```

The 15 `PILOT` grandchildren are the first reasonable targets for trim generation and a fresh one-sided colorability screen. The full list is stored in `summary.json`.

## Output certificate

The workflow artifact contains:

- one complete classification JSON file per sixth-base child;
- `grandchildren.csv` with all 4,476 canonical cases and scheduling statistics;
- `summary.json`;
- `independent-verification.json`;
- `verification.json`;
- `SHA256SUMS`.

## Mathematical boundary

This package performs classification only.

- Every sixth-base child remains `UNKNOWN`.
- Every seventh-base grandchild begins `UNKNOWN`.
- No child is promoted to a certified obstruction.
- No SAT or UNSAT claim is made.
- `q00r00`, `q00`, and `n11-k6-full` remain unchanged.
