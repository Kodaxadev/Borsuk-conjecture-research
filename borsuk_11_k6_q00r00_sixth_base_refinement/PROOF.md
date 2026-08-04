# Exhaustiveness argument

## Candidate enumeration

Both implementations scan all 2,048 vertices and independently evaluate `v not in B`, even Hamming weight, and distance at most six from every point of `B`. The scan yields 329 candidates.

## Complete unordered stabilizer

Every cube automorphism has form `g(x)=P(x) xor t`. For a proposed permutation of the five base points, `t=g(0)` is forced. The remaining four equations are solved completely by matching equal four-bit coordinate-column patterns and enumerating every bijection within each pattern class.

This yields 24 distinct affine automorphisms and 12 induced base permutations. The pointwise kernel has order two. Identity, inverses, composition closure, base preservation, candidate invariance, and generator closure are checked mechanically.

## Orbit partition

For the least uncovered candidate `r`, each implementation computes `{g(r):g in Stab_set(B)}`. Every orbit stores an explicit automorphism from its representative to each member. A multiplicity counter requires every one of the 329 candidates to appear exactly once and no incompatible vertex to appear. Orbit-stabilizer is checked against group order 24.

The resulting partition has 36 orbits.

## Pointwise falsification control

Using the pointwise subgroup instead produces 222 orbits. This exhaustive but noncanonical over-splitting is frozen as the strongest immediate negative control.

## Independent reproduction

The Python and JavaScript programs consume only the governed constants and serialization rules. They run in separate output directories and must produce byte-identical candidate, stabilizer, orbit, manifest, and summary files.
