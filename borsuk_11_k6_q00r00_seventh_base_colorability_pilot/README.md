# Seventh-base one-sided colorability pilot

Claim: `n11-k6-q00r00-seventh-base-colorability-pilot`

This package screens exactly the 15 `PILOT` grandchildren frozen by the repository-governed seventh-base classification. It does not generate or solve the other 4,461 grandchildren.

## Governed source

The sole mathematical input is the archived classification certificate:

```text
borsuk_11_k6_q00r00_seventh_base_classification/
  evidence/run-30875846299/artifacts/
  q00r00-seventh-base-classification-run-30875846299.zip

sha256:
dece0e924900b2bd751a62e82edca7e59f55e0c58a5bf92c5b9b196755646352
```

The workflow also verifies the classification governance binding committed at `f9e44bf830096d967546f8f5e9f7d634c2ea718b` and the governed branch head `865f6e99567ffe48d040e9de9693026a129a76ef`.

## Exact pilot set

```text
q00r00-s026-t066
q00r00-s028-t116
q00r00-s028-t144
q00r00-s028-t148
q00r00-s028-t154
q00r00-s030-t084
q00r00-s030-t086
q00r00-s031-t041
q00r00-s033-t084
q00r00-s034-t025
q00r00-s034-t028
q00r00-s034-t033
q00r00-s034-t034
q00r00-s034-t035
q00r00-s035-t008
```

No pilot case may be replaced, added, merged across parents, or recanonicalized.

## Instance construction

For each frozen seven-point base:

1. Reconstruct all even-parity vertices of the 11-cube at Hamming distance at most six from every base point.
2. Recompute all distance-six graph edges and all greater-than-six incompatible pairs.
3. Match the trim size, edge count, incompatible-pair count, and canonical vertex-stream hash recorded by the classification certificate.
4. Construct a deterministic clique by descending graph degree and ascending vertex.
5. Remove colors forbidden by that clique.
6. Emit a compact canonical 12-color CNF and a complete variable map.

The Python generator and independently written JavaScript verifier reconstruct every trim, graph, clique, color domain, variable assignment, clause, and CNF byte stream.

## Frozen instance totals

```text
cases:                         15
trim vertices across cases:    2,840
distance-six edges:          100,083
incompatible pairs:           27,343
compact variables:            18,397
compact clauses:             403,257

instances.json SHA-256:
1da3f53f072296806176580e31c58d5e04955271ff42e7c54cbec14273ed3d9f

SHA256SUMS SHA-256:
620efe06daf3d253b924e7e5764ca61df4831318a61a8d28765163607acfd83f
```

## One-sided result semantics

```text
SAT_CHECKED_COLORING
  -> directly checked against every distance-six edge
  -> closes only that grandchild
  -> does not close its sixth-base parent

PROOF_CHECKED_UNSAT
  -> full DRAT proof accepted by pinned drat-trim
  -> empty-proof negative control rejected
  -> proves only the universal trim non-12-colorable
  -> grandchild remains UNKNOWN
  -> enters the certified eighth-base refinement frontier

UNKNOWN
  -> timeout, solver failure, checker failure, or absent certificate
  -> remains an incomplete pilot case
```

A checked SAT coloring of one grandchild does not close its parent. Parent closure requires certified coverage of every canonical seventh-base grandchild under that parent plus the smaller-component boundary.

## Workflow structure

The read-only workflow has:

- one preparation job that validates the governed classification archive, reconstructs and independently verifies all 15 instances, and builds pinned Kissat and `drat-trim` binaries;
- 15 isolated matrix jobs, each with its own solver/checker artifact;
- direct SAT witness verification;
- full UNSAT proof verification and an empty-proof negative control;
- one aggregate summary requiring complete coverage of all 15 case artifacts.

Artifacts do not change repository status by themselves. Post-upload execution binding and governance promotion remain separate work.

## Mathematical boundary

Before execution, all 15 pilot grandchildren remain `UNKNOWN`. Every sixth-base parent, `q00r00`, `q00`, and `n11-k6-full` remain unchanged.
