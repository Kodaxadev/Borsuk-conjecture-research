# Candidate proof that the 0/1-Borsuk statement holds for \(n=11,\ k=4\)

## Claim

For every \(S\subseteq\{0,1\}^{11}\) of Hamming diameter at most \(4\), the
graph joining pairs at Hamming distance exactly \(4\) is \(12\)-colorable.

Equivalently, every diameter-\(4\) subset of the 11-dimensional Boolean cube
can be partitioned into at most \(12\) subsets of strictly smaller diameter.

## 1. Reduce to one connected component

Let \(G(S;4)\) be the exact-distance-\(4\) graph. Color each connected component
independently, reusing the same palette.

Choose a vertex of a nontrivial connected component and translate it to the
origin by coordinate complementation. Every edge changes four coordinates, so
every vertex in that component has even Hamming weight. Since the original set
has diameter at most four, every vertex now has weight \(0\), \(2\), or \(4\).

Thus the only vertices outside the even radius-two ball are the weight-four
vertices adjacent to the origin.

## 2. Triangle case

Suppose the component contains a triangle. Translate one triangle vertex to
the origin. The two remaining vertices are weight-four vectors whose supports
intersect in two coordinates. A coordinate permutation maps the triangle to

\[
T=\bigl\{\varnothing,\{0,1,2,3\},\{0,1,4,5\}\bigr\}.
\]

Every other component vertex is within Hamming distance four of every member
of \(T\), so the whole component lies in the reconstructed graph
`triangle_trim_even`.

The supplied witness colors this 109-vertex, 3,123-edge graph with 12 colors.

## 3. Triangle-free case

Suppose the component contains an edge but no triangle. After translating one
endpoint to the origin, let \(\mathcal F\) be the supports of its weight-four
vertices.

For distinct \(A,B\in\mathcal F\), diameter at most four gives
\(|A\cap B|\ge2\). Equality would mean that \(0,A,B\) are pairwise at distance
four, a triangle. Hence

\[
|A\cap B|=3
\]

for every distinct pair. Therefore \(\mathcal F\) is a clique of the Johnson
graph \(J(11,4)\).

### Johnson-clique lemma

Every family of four-subsets with pairwise intersection three is contained in
one of the following:

1. a **star**: all members contain one fixed three-subset;
2. a **top**: all members are contained in one fixed five-subset.

### Elementary proof

A family with at most one member is trivially contained in a star. Otherwise, take distinct \(A=C\cup\{a\}\) and \(B=C\cup\{b\}\), where \(|C|=3\).

If every family member contains \(C\), the family is contained in the star
through \(C\).

Otherwise choose \(D\) not containing \(C\). If \(c\in C\setminus D\), the
conditions \(|D\cap A|\ge3\) and \(|D\cap B|\ge3\) force

\[
D=(C\setminus\{c\})\cup\{a,b\}.
\]

Now any member \(E=C\cup\{e\}\) containing \(C\) must have \(e\in\{a,b\}\) in
order to intersect \(D\) in three points. Every member not containing \(C\)
also has the displayed form. Consequently every member is a four-subset of
the five-set \(C\cup\{a,b\}\), proving the top case.

The verifier independently enumerates all maximal cliques of \(J(11,4)\):
165 stars of size 8 and 462 tops of size 5, with no third type.

## 4. Color the two triangle-free covers

All weight-zero and weight-two vertices lie in the even radius-two ball.

* In the star case, the component lies in `star_plus_even_ball`, whose supplied
  witness uses 10 colors.
* In the top case, the component lies in `top_plus_even_ball`, whose supplied
  witness uses 9 colors.

Both are therefore 12-colorable.

A component with no edge is trivially one-colorable. Combining the component
colorings proves the claim.

## Verification boundary

The mathematical reduction and Johnson-clique lemma are written above. The
only computer-assisted facts are three explicit coloring witnesses. `verify.py`
reconstructs each graph and validates every witness by both:

1. scanning every exact-distance-four edge; and
2. checking every pair inside every color class.

No SAT solver, timeout, floating-point arithmetic, or external Python package
is used.
