# Hostile audit

## Claim under attack

Every diameter-at-most-8 subset of the 11-dimensional Boolean cube is
partitionable into 12 subsets of smaller diameter.

## Failure attempts

### 1. Does a connected component really become even-weight?

Yes. Translation sends the chosen base vertex to zero. Every graph edge
has Hamming weight 8, hence even parity. Parity is invariant along every
path in the exact-distance graph.

### 2. Could a translated component contain weight 10?

No. Every original point is at distance at most 8 from the selected base
point because the entire set has diameter at most 8.

### 3. Are components sufficient?

Yes. The graph's connected components have no edges between them by
definition. A proper coloring may reuse the same palette in each one.

### 4. Does avoiding distance 8 imply smaller diameter?

Only because the original set is assumed to have diameter at most 8.
Within that set, a color class with no distance-8 pair has all distances
at most 7.

### 5. Is the witness missing vertices?

Both verifiers reconstruct the canonical 1,013-element vertex set and
require exact equality with the witness keys.

### 6. Is the graph generator circular?

Two implementations use different generation routes:

- Python generates neighbors by XOR with all 165 weight-eight masks.
- JavaScript scans all unordered pairs and measures Hamming distance.

They agree on 82,665 edges and the same canonical SHA-256 graph hash.

### 7. Could the witness use more than 12 colors?

No. Both verifiers require every color to be an integer from 0 through
11 and report exactly 12 used colors.

### 8. Could a monochromatic edge evade the edge list?

Each verifier also performs a separate all-pairs scan inside every color
class. This check does not depend on trusting a supplied edge list.

## Remaining risks

- This package has not yet been reviewed by an external mathematician.
- Novelty has not been established conclusively.
- A corrupted or malicious runtime could falsify both executions,
  although the small standard-library verifiers are inspectable.
- The result covers diameter 8 only; diameter 6 remains necessary for
  the full 11-dimensional 0/1-Borsuk theorem.
