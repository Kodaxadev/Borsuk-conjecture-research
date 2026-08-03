# Proof of the q00 five-base reduction

## Statement

Let `P = {0x000, 0x03f, 0x1c7, 0x64b}` be the canonical q00 four-point base and let

```text
T(P) = {x in {0,1}^11 : wt(x) is even and d(x,p) <= 6 for every p in P}.
```

Every diameter-at-most-6 component containing `P` and at least one additional vertex is contained in one of 12 canonical five-base trims.

## 1. Exhaustive fifth vertices

Direct enumeration gives `|T(P)| = 436`. The four base points themselves account for four vertices, leaving 432 possible choices for a fifth component vertex `D`.

If a legal component represented by q00 has at least five vertices, one of its nonbase vertices is such a `D`. Because the component has diameter at most 6, every component vertex lies in

```text
T(P union {D}).
```

Thus the 432 five-base trims cover every q00 component with at least five vertices. Components with at most four vertices require at most four colors and are trivial for the 12-color target.

## 2. Complete affine-isometry invariant

For an unordered finite point set `S = {p0,...,pm-1}`, choose each point as a translation origin. For each origin, order the remaining `m-1` translated points in every way. At every coordinate record the resulting `(m-1)`-bit column pattern, and count the multiplicity of each of the `2^(m-1)` patterns.

Take the lexicographically least multiplicity vector over all origins and orderings.

This vector is invariant under coordinate permutations and translations. It is also complete: if two labeled translated sets have equal column-pattern multiplicities, matching coordinates pattern by pattern gives an explicit coordinate permutation between them. Minimizing over origins and labelings therefore classifies unordered point sets up to affine cube isometry.

For five-point bases the invariant has 16 entries. Applying it to every `P union {D}` partitions the 432 fifth vertices into 12 full affine-isometry types.

## 3. Child trims

For one representative of each type, the verifier regenerates the complete even-parity intersection of the five radius-6 Hamming balls. Isometric five-point bases produce isometric trims, so one child trim per type is sufficient.

The 12 child trims have 334–428 vertices. Their deterministic case-list and complete fifth-vertex assignment hashes are frozen in `generate_cases.py` and reproduced independently in JavaScript.

## Scope

The reduction establishes exhaustive coverage of q00 by 12 smaller universal trims. It does not establish that any child is 12-colorable or legally UNSAT. Every child remains unresolved until certificate-backed solver work and, where necessary, further diameter-compatible refinement are complete.
