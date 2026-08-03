# Exact attack surface for \(n=11,\ k=6\)

## Reduction

Let \(S\subseteq\{0,1\}^{11}\) have diameter at most 6, and consider one
nontrivial connected component of its exact-distance-6 graph.

Translate one component vertex to \(0\). Every vertex of the translated
component has even weight and weight at most 6. Because the component is
nontrivial, \(0\) has a neighbor \(A\) of weight 6. A coordinate
permutation sends \(A\) to

\[
A=\{0,1,2,3,4,5\},
\]

encoded here as integer 63.

Every component vertex \(x\) also satisfies \(d_H(x,A)\leq6\). Therefore
the component lies inside the canonical trim set

\[
T=\{x:\operatorname{wt}(x)\text{ is even},\ 
       \operatorname{wt}(x)\leq6,\ d_H(x,A)\leq6\}.
\]

The set \(T\) has 692 vertices. Its exact-distance-6 graph has 104,606
edges.

A proper 12-coloring of this one trim graph would settle the diameter-6
case immediately.

## Critical limitation

The converse is false. The trim set \(T\) itself is not necessarily a
diameter-6 family: it contains pairs farther apart than 6. Therefore an
UNSAT result for the supplied 12-coloring instance would **not**
disprove the 11-dimensional 0/1-Borsuk statement. It would only prove
that the one-neighbor universal cover is too coarse and that additional
diameter-compatible branching is necessary.

## Hadamard clique and symmetry breaking

The graph contains the explicit 12-clique

```
0, 63, 455, 748, 858, 945,
1241, 1396, 1450, 1635, 1686, 1805
```

Every pair is at Hamming distance 6. These vectors are the shortened
binary form of an order-12 Hadamard matrix.

In any 12-coloring, these clique vertices must receive all 12 colors.
Relabeling colors lets us fix clique vertex \(i\) to color \(i\) without
loss of generality.

Once fixed-clique conflicts are removed, the exact SAT instance has:

- 4,440 Boolean vertex-color variables;
- 680 nonfixed vertices;
- 560 vertices with 6 available colors;
- 120 vertices with 9 available colors;
- 362,120 clauses.

The DIMACS instance is `k6_trim_12color.cnf`, with assignments decoded by
`variable_map.json`.

## Correlation-derived partial coloring

Augment each 11-bit vector by a leading \(+1\) sign and correlate it with
the 12 Hadamard rows. In Hamming language, apply this rule:

1. assign a clique center to itself;
2. otherwise assign the unique center at distance 2, when it exists;
3. otherwise assign the unique center at distance 10, when it exists;
4. leave the vector uncolored.

This produces a proper partial coloring of 572 of the 692 vertices.

The remaining 120 vertices have:

- weight distribution: 80 of weight 4 and 40 of weight 6;
- an induced graph with 3,015 edges;
- degree distribution: 90 vertices of degree 51 and 30 of degree 48;
- nine colors allowed by the fixed clique.

The partial coloring is maximal in a strong immediate sense: each of the
120 remaining vertices has a distance-6 neighbor in every one of the 12
existing color classes. Thus none can simply be inserted without
recoloring another vertex.

This 120-vertex set is an obstruction core for that natural Hadamard
partial coloring, not yet an equivalent reduction of the full SAT
instance.

## Interpretation

There are now two precise outcomes:

- **SAT:** the one-neighbor trim graph is 12-colorable, immediately
  proving the \(n=11,k=6\) case and—combined with the diameter-4 and
  diameter-8 candidates—the full 11-dimensional 0/1-Borsuk result.
- **UNSAT:** no theorem-level contradiction follows. The next step is
  to add a second diameter-compatible base vertex and enumerate the
  resulting symmetry orbits, mirroring but compressing the dimension-10
  calculation.

No SAT or UNSAT claim is made in this package.
