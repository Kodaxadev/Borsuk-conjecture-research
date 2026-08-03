# Completeness of the n=11, k=6 four-base reduction

Let `S` be a connected component of the exact-distance-6 graph of a subset of the 11-cube whose Hamming diameter is at most 6.

Translate one component vertex to `0`. Exact-distance-6 edges preserve parity, so the component lies in the even-parity half-cube. Choose a neighbor and permute coordinates so that

```text
A = 0x03f
```

has weight 6.

Every component vertex `x` then satisfies

```text
weight(x) even,
weight(x) <= 6,
d(x,A) <= 6.
```

## Third normalized vertex

If the component contains only `0` and `A`, it is trivially colorable. Otherwise choose a third vertex `B`.

Write

```text
a = |supp(B) intersect supp(A)|,
b = |supp(B) outside supp(A)|.
```

The trim conditions imply

```text
a+b is even,
a+b <= 6,
b <= a.
```

Excluding `B=0,A`, the possibilities are

```text
(1,1), (2,0), (2,2), (3,1), (3,3), (4,0), (4,2), (5,1).
```

The affine cube isometry `x -> x xor A` exchanges `0` and `A` and maps `(a,b)` to `(6-a,b)`. Therefore only five setwise cases remain:

```text
(1,1), (2,0), (2,2), (3,1), (3,3).
```

The coordinate stabilizer `S_6 x S_5` is transitive on each fixed `(a,b)` class, so one representative `B` per listed class is complete.

## Fourth normalized vertex

If the component has only three vertices, it is trivially colorable. Otherwise choose a fourth distinct vertex `C`.

For fixed `B`, partition the coordinates by their two-bit membership signature `(A_i,B_i)`. The pointwise stabilizer of `0,A,B` permutes coordinates independently inside these blocks. Therefore `C` is classified by how many selected coordinates it has in each block.

Exhaustive enumeration gives:

| Third-vertex family | Pointwise `C` orbits |
|---|---:|
| `(1,1)` | 24 |
| `(2,0)` | 19 |
| `(2,2)` | 36 |
| `(3,1)` | 35 |
| `(3,3)` | 35 |
| **Total** | **149** |

Quotienting by the setwise stabilizer of each chosen metric triple `{0,A,B}` gives 101 intermediate four-base cases:

| Third-vertex family | Intermediate cases |
|---|---:|
| `(1,1)` | 19 |
| `(2,0)` | 19 |
| `(2,2)` | 26 |
| `(3,1)` | 23 |
| `(3,3)` | 14 |
| **Total** | **101** |

## Full four-base isometry canonicalization

The choice of which nonzero point is called `B` is artificial. To quotient the complete unordered base `{P_0,P_1,P_2,P_3}`, use the following exact invariant.

Choose each base point in turn as the translation origin. Permute the remaining three points in all six ways. After translation, every coordinate contributes one of eight three-bit column signatures. Coordinate permutations preserve only the multiplicities of these eight signatures. For each origin and labeling, form the eight-entry multiplicity tuple and take the lexicographically least tuple.

This tuple is a complete affine-cube-isometry invariant for an unordered four-point set:

- translation is exhausted by the four origin choices;
- relabeling is exhausted by the six permutations;
- coordinate permutations act only by reordering columns;
- equal column multiplicities give an explicit coordinate permutation between the translated labeled bases.

Applying this invariant to all 101 intermediate cases produces exactly **58 full-isometry classes**. The member counts sum to 101, so no intermediate case is lost.

For every representative base `{0,A,B,C}`, define its trim as all even cube vertices within distance 6 of all four base vertices. Affine cube isometries preserve parity differences, Hamming distances, exact-distance graphs, and diameter incompatibilities. Therefore isometric bases produce isometric trims, and one representative per full base class is sufficient.

Thus every component with at least four vertices is isometric to a subset of one of **58 canonical trims**. The 101-case list remains an independently hashed intermediate coverage layer; the 58-case list is the solver frontier.

## What remains

This is a covering reduction only. The canonical trims have 436–612 vertices and may contain mutually incompatible pairs farther than 6 apart.

For each trim:

- a verified 12-coloring closes the branch by restriction;
- proof-checked UNSAT requires further diameter-compatible refinement;
- proof-checked UNSAT after all incompatibilities are removed yields a legal counterexample candidate;
- timeout or heuristic failure remains unresolved.
