# Candidate theorem: the 11-dimensional 0/1-Borsuk case of diameter 8

## Statement

Let \(S\subseteq\{0,1\}^{11}\) have Hamming diameter at most \(8\).
Then \(S\) can be partitioned into at most \(12\) subsets of Hamming
diameter at most \(7\).

Equivalently, the graph on \(S\) joining pairs at Hamming distance
exactly \(8\) is 12-colorable.

## Reduction to one finite graph

Let \(G_8(S)\) be the exact-distance-8 graph on \(S\).

It is enough to color each connected component independently, because
different components have no distance-8 edge and may reuse the same
colors.

Fix a connected component \(C\) and choose \(x_0\in C\). Translate the
component by bitwise XOR with \(x_0\):

\[
C'= \{x\oplus x_0:x\in C\}.
\]

Translation is an isometry of the Boolean cube, so it preserves all
Hamming distances.

Every edge of \(G_8(S)\) changes eight coordinates. Therefore every
vertex reached from \(x_0\) by a path in \(G_8(S)\) differs from \(x_0\)
in an even number of coordinates. Consequently every vector in \(C'\)
has even Hamming weight.

Moreover, because \(S\) has diameter at most \(8\),

\[
\operatorname{wt}(x\oplus x_0)=d_H(x,x_0)\leq 8
\]

for every \(x\in C\).

Thus every translated component is contained in the fixed set

\[
B=\{x\in\{0,1\}^{11}:\operatorname{wt}(x)\in\{0,2,4,6,8\}\}.
\]

The set \(B\) contains

\[
\binom{11}{0}+\binom{11}{2}+\binom{11}{4}
+\binom{11}{6}+\binom{11}{8}
=1+55+330+462+165=1013
\]

vectors.

Let \(H\) be the graph with vertex set \(B\), joining two vertices when
their Hamming distance is exactly \(8\). The supplied witness assigns
one of 12 colors to every vertex of \(H\), and the independent
verifiers establish that no edge is monochromatic.

Therefore every translated component \(C'\), and hence every original
component \(C\), is 12-colorable. Reusing the same 12 colors across
components gives a 12-coloring of \(G_8(S)\). Each color class contains
no pair at distance 8. Since all distances in \(S\) are at most 8,
every color class has diameter at most 7.

This proves the stated diameter-8 case, conditional only on the finite
coloring witness being checked correctly.

## Finite certificate

The certificate covers all 1,013 vertices of \(B\). Its exact-distance
graph has 82,665 edges.

The canonical graph hash is SHA-256 of the sorted UTF-8 edge list, one
line per edge in the form

```
smaller_vertex,larger_vertex
```

The expected hash is recorded in `witness.json` and checked by both
verifiers.

## Scope

This is a proof candidate for the diameter-8 subcase only. Together
with a valid diameter-4 result it still does not settle the full
11-dimensional 0/1-Borsuk problem; diameter 6 remains.
