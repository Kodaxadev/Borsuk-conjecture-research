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

The base set is unordered. Every affine cube isometry that permutes the metric triple `{0,A,B}` acts on these pointwise classes. Quotienting by the full setwise stabilizer gives:

| Third-vertex family | Setwise four-base cases |
|---|---:|
| `(1,1)` | 19 |
| `(2,0)` | 19 |
| `(2,2)` | 26 |
| `(3,1)` | 23 |
| `(3,3)` | 14 |
| **Total** | **101** |

For every representative base `{0,A,B,C}`, define its trim as all even cube vertices within distance 6 of all four base vertices. Every actual component containing those base vertices is a subset of that trim.

Thus every component with at least four vertices is isometric to a subset of one of the 101 canonical trims recorded in `case_representatives.csv`.

## What remains

This is a covering reduction only. The trims have 436–612 vertices and may contain mutually incompatible pairs farther than 6 apart.

For each trim:

- a verified 12-coloring closes the branch by restriction;
- proof-checked UNSAT requires further diameter-compatible refinement;
- proof-checked UNSAT after all incompatibilities are removed yields a legal counterexample candidate;
- timeout or heuristic failure remains unresolved.
