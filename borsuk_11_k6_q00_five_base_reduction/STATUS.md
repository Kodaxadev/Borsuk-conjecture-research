# Status

## Verified target shape

- q00 parent vertices: 436.
- Possible nonbase fifth vertices: 432.
- Canonical unordered five-base types: 12.
- Child trim-size range: 334–428 vertices.
- Python and JavaScript expected hashes agree.

## Current child classification

- `UNKNOWN`: 12.
- `SAT_CLOSED`: 0.
- `UNSAT_REFINED`: 0.
- `LEGAL_UNSAT`: 0.

## Boundary

This package is a reduction and solver frontier only. It does not close q00, alter the parent 58-type `case_status.json`, or promote the full `n=11,k=6` theorem. Every material child result requires its own certificate-backed evidence and Cruthúnas transition.

## Next action

Build deterministic compact list-coloring instances for `q00r00` through `q00r11`, order them by encoding size, and close SAT children with explicit verified colorings. Refine proof-checked UNSAT children again by a sixth compatible base or exact incompatibility branching.
