# Borsuk 11, diameter 6 — triangle-branch refinement

## Status

The normalized second-base branch with `|A cap B|=3` is the triangle branch:

- `0 = 0`;
- `A = 63 = {0,1,2,3,4,5}`;
- `B = 455 = {0,1,2,6,7,8}`.

Its 555-vertex universal branch graph is reported UNSAT by CaDiCaL for
12-coloring. That solver result is not promoted to a certificate until the
separate proof-trace workflow succeeds.

This package performs the next exact reduction independently of that solver
claim. It does **not yet settle** the diameter-6 case.

## Why a fourth base vertex suffices

Suppose a legal diameter-at-most-6 component contains the normalized triangle.
If the component consists only of those three vertices, it is trivially
12-colorable. Otherwise, connectedness provides a first vertex `C` outside the
triangle along a path from it. That vertex is at Hamming distance exactly 6
from one triangle vertex.

Renormalize the adjacent triangle vertex to `0`. The other two triangle
vertices become two weight-6 vectors at mutual distance 6, so a coordinate
permutation restores the canonical pair `A,B` above. Therefore `C` has weight
6 and satisfies

- `d(C,A) <= 6`;
- `d(C,B) <= 6`.

Split the 11 coordinates into four blocks:

1. `A cap B`, size 3;
2. `A minus B`, size 3;
3. `B minus A`, size 3;
4. outside `A union B`, size 2.

The pointwise stabilizer permutes coordinates within these blocks, and swapping
`A` with `B` exchanges the middle two counts. Thus `C` is classified by a
canonical tuple `(a,b,c,d)` with `b <= c`. Exhaustive enumeration gives exactly
11 orbits covering all 307 possible fourth vertices.

## Exact branch sizes

| Orbit | Representative `C` | Orbit size | Vertices | Distance-6 edges | CNF variables | CNF clauses |
|---|---:|---:|---:|---:|---:|---:|
| `a0_b3_c3_d0` | 504 | 1 | 436 | 39,642 | 3,339 | 219,595 |
| `a1_b2_c2_d1` | 729 | 54 | 436 | 39,640 | 3,145 | 190,813 |
| `a1_b2_c3_d0` | 473 | 18 | 460 | 44,391 | 3,322 | 213,295 |
| `a2_b1_c1_d2` | 1611 | 27 | 436 | 39,600 | 3,151 | 191,175 |
| `a2_b1_c2_d1` | 715 | 108 | 460 | 44,388 | 3,144 | 184,823 |
| `a2_b1_c3_d0` | 459 | 18 | 490 | 50,739 | 3,559 | 245,516 |
| `a2_b2_c2_d0` | 219 | 27 | 481 | 48,777 | 3,479 | 234,150 |
| `a3_b0_c1_d2` | 1607 | 6 | 461 | 44,553 | 3,337 | 214,654 |
| `a3_b0_c2_d1` | 711 | 12 | 491 | 50,904 | 3,566 | 246,143 |
| `a3_b1_c1_d1` | 591 | 18 | 482 | 48,973 | 3,711 | 271,527 |
| `a3_b1_c2_d0` | 207 | 18 | 512 | 55,617 | 3,719 | 268,564 |

## Reproduce

```bash
python borsuk_11_k6_triangle_refinement/enumerate_triangle_refinement.py \
  --out generated_triangle_refinement \
  --emit-cnf
```

The script uses only the Python standard library. It checks:

- the 555-vertex triangle trim;
- all 307 possible fourth vertices;
- the exact 11-orbit partition;
- every branch vertex and edge count;
- every edge-stream SHA-256;
- every generated CNF count and SHA-256.

## Interpretation

A verified 12-coloring of every orbit would settle every legal component that
contains an exact-distance-6 triangle. It would not settle the overlap-4 and
overlap-5 second-base branches.

An UNSAT orbit still would not refute Borsuk, because each universal branch
contains mutually incompatible pairs at distance greater than 6. Such an orbit
would require a fifth compatible base vertex or a direct encoding of the
remaining diameter constraints.
