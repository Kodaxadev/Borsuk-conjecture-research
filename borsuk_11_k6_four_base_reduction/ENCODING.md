# Correctness of the compact clique-reduced list-color encoding

## Statement

Let `G = (V,E)` be one canonical exact-distance-6 trim graph, and let

```text
Q = (q_0, ..., q_{m-1})
```

be the verified clique selected by `build_instance.py`, where `m <= 12`.

The compact CNF emitted by the generator is satisfiable if and only if `G` is 12-colorable.

## Canonical clique colors

Every proper coloring assigns pairwise distinct colors to the vertices of `Q`. A global permutation of the 12 color labels therefore converts any proper coloring into one satisfying

```text
color(q_i) = i
```

for every `0 <= i < m`.

Thus fixing these clique colors loses no coloring.

## Reduced color domains

For a clique vertex, define

```text
D(q_i) = {i}.
```

For every other vertex `v`, define

```text
D(v) = {m, ..., 11}
       union
       {i < m : v is not adjacent to q_i}.
```

If `v` is adjacent to `q_i`, then `v` cannot have color `i` after the canonical clique assignment. Removing that color is therefore logically forced.

Colors `m` through `11` are not assigned to a fixed clique vertex and remain available to every non-clique vertex.

## Variables and clauses

The compact encoding creates a variable `x_(v,c)` only when `c` belongs to `D(v)`.

It contains:

1. one at-least-one-color clause for each vertex;
2. pairwise at-most-one-color clauses inside each vertex domain;
3. for every edge `{u,v}` and every color in `D(u) intersect D(v)`, the clause

```text
not x_(u,c) or not x_(v,c).
```

No clause is required for an edge/color pair removed from one endpoint's domain because that endpoint cannot select the color.

## Forward direction

Assume `G` has a proper 12-coloring.

Permute the color labels so that `q_i` has color `i` for every fixed clique vertex. Every non-clique vertex then has a color in its reduced domain: if its color is below `m`, it cannot be adjacent to the clique vertex carrying that color; colors at least `m` are always retained.

Set exactly the variable corresponding to each vertex's color to true. The exactly-one clauses hold. Because the coloring is proper, no edge has both endpoints assigned the same retained color, so every edge clause holds. The compact CNF is satisfiable.

## Reverse direction

Assume the compact CNF is satisfiable.

The per-vertex clauses select exactly one color from every reduced domain. Assign that color to the vertex. For every graph edge, the encoding forbids both endpoints from selecting any color common to their domains. A color absent from one endpoint's domain cannot be selected there. Therefore no edge is monochromatic, and the decoded assignment is a proper 12-coloring of `G`.

## Consequence for certificates

A verified SAT model decodes to an independently checkable graph coloring.

A checked UNSAT proof for the exact compact CNF proves that the corresponding trim graph has no 12-coloring. It does not, by itself, settle the diameter-6 theorem target because the trim may contain pairs at distance greater than 6 and must then be refined exhaustively.

## Implementation trust boundary

The repository independently checks that:

- the selected fixed vertices form a clique;
- every reduced domain matches the definition above;
- every variable number decodes to one allowed vertex-color pair;
- every returned SAT model selects exactly one allowed color per vertex;
- the decoded coloring has no monochromatic exact-distance-6 edge;
- deterministic CNF and variable-map hashes remain stable.
