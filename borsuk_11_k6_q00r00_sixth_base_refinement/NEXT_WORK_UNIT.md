# Next governed work unit: compatible sixth-base child trims

## Target

Generate and independently verify the 36 universal child trims associated with the canonical sixth-base representatives `q00r00-s000` through `q00r00-s035`.

The execution-bound classification in `EXECUTION_BINDING.json` is the only governed case source. This work unit must not recanonicalize, merge, split, solve, or refine the 36 cases.

## Primary implementation

For every child identifier, record:

- the six-point base and sixth-vertex representative;
- the exact trim predicate;
- the complete ascending trim-vertex list, count, and SHA-256;
- the complete exact-distance-six edge list, count, and SHA-256;
- the complete distance-greater-than-six incompatible-pair list, count, and SHA-256;
- the parent classification identifiers and hashes;
- status `UNKNOWN`.

Use a separate manifest mapping each child identifier to all generated artifact paths and hashes.

## Exhaustiveness checks

Mechanically verify that:

- all 36 classified representatives are consumed exactly once;
- no unclassified representative is consumed;
- every listed trim vertex satisfies the six-base compatibility predicate;
- every compatible cube vertex is listed;
- every exact-distance edge is present exactly once and has distance six;
- every incompatible pair is present exactly once and has distance greater than six;
- edge and incompatible-pair sets are disjoint;
- all child statuses remain `UNKNOWN`.

## Independent reproduction

A second implementation must regenerate every child trim and all counts and hashes without consuming the primary implementation's generated files. The comparison layer must require byte-identical canonical outputs or independently compare decoded mathematical sets.

## Scope boundary

This work unit ends after the 36 child trims are generated, independently reproduced, and execution-bound.

It does not run SAT solvers, claim colorings, infer UNSAT consequences, merge isomorphic children beyond the frozen classification, or change the status of `q00r00`, `q00`, or `n11-k6-full`.
