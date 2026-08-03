# Proof of the exhaustive 12-type fifth-base refinement for q00

## Statement

Let

\[
Q=(0,63,455,1611)
\]

and let

\[
T_Q=\{x\in\{0,1\}^{11}: \operatorname{wt}(x)\text{ is even and }
 d_H(x,q)\le 6\text{ for every }q\in Q\}.
\]

Then `T_Q` has 436 vertices. Under the affine cube-isometry group stabilizing
the unordered set `Q`, the 432 vertices of `T_Q \ Q` form exactly 12 orbits.
For one representative `D` from each orbit, define

\[
T_{Q,D}=\{x\in T_Q:d_H(x,D)\le6\}.
\]

Every diameter-at-most-6 family containing `Q` is either `Q` itself or, up to
an isometry stabilizing `Q`, is contained in one of the 12 sets `T_{Q,D}`.

## 1. Exact q00 trim

The four q00 base points are pairwise at Hamming distance 6. Direct standard-
library enumeration of the even-weight vectors lying within distance 6 of all
four base points gives 436 vertices. The package verifies this independently
in Python and JavaScript.

## 2. Full unordered-base stabilizer

An affine cube isometry has the form

\[
x\mapsto t\oplus\pi(x),
\]

where `t` is a translation vector and `pi` is a coordinate permutation.

For each of the 24 permutations of the four base points, the verifier compares
the 3-bit coordinate-column signatures obtained after translating the first
point to zero. Whenever the signature multiplicities agree, it enumerates all
coordinate bijections within equal-signature blocks and checks the requested
base permutation directly.

For q00, all 24 base permutations occur. Four signature blocks have size 2 and
the remaining nonempty blocks have size 1, giving

\[
24\,(2!)^4=384
\]

distinct affine stabilizer maps. Both implementations deduplicate the maps by
their images on zero and the 11 coordinate unit vectors and obtain order 384.

## 3. Fifth-point orbit enumeration

Remove the four base points from `T_Q`. For the least unseen vertex `D`, apply
all 384 stabilizer maps and remove the resulting orbit. Repeating this exact
procedure partitions all 432 candidates into 12 orbits, whose sizes sum to
432.

For an additional independent invariant, each five-point base is canonicalized
under every choice of translated origin and every permutation of the remaining
four points. The resulting 16 coordinate-column counts are recorded in
`canonical_12.csv`.

## 4. Coverage argument

Let `S` be a diameter-at-most-6 family represented by the q00 four-base type,
so `Q` is contained in `S` and `S` is contained in `T_Q`.

If `S=Q`, then `S` has four points and is trivially partitionable into at most
12 smaller-diameter subsets.

Otherwise choose `D` in `S \ Q`. Because `S` is contained in `T_Q`, `D` is one
of the 432 enumerated candidates. Some stabilizer map sends `D` to the chosen
representative `D_i` of its orbit. That map preserves `Q`, Hamming distance,
and parity. Every point of the transformed family remains within distance 6
of `Q` and, because the original family has diameter at most 6, within distance
6 of `D_i`. Hence the transformed family is contained in `T_{Q,D_i}`.

Thus the 12 child trims are exhaustive.

## 5. What this does not prove

The child trims are covers, not necessarily legal diameter-6 families. Their
incompatible-pair counts range from 7,129 to 12,288. No child is classified as
SAT or proof-checked UNSAT in this package. The q00 case and the full theorem
therefore remain unresolved.
