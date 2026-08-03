# Certificate-first solver workflow for q00 fifth-base children

This workflow applies to the 12 child trims `f00` through `f11`.

## Result classes

A bounded solver run has exactly one research interpretation:

- `SAT_MODEL_VERIFIED`: a complete solver model is independently decoded and every exact-distance-6 edge is checked;
- `UNSAT_PROOF_CHECKED`: the exact CNF has a proof trace accepted by a pinned independent checker, with a corrupted-proof rejection control;
- `UNKNOWN`: timeout, crash, incomplete output, absent proof, or checker failure.

Solver stdout alone is never an UNSAT certificate. Failure to find a coloring is never evidence of UNSAT.

## SAT boundary

`verify_child_model.py` regenerates the canonical fifth-base child from its case ID. It does not trust a stored edge list or variable map. It reconstructs:

- the child trim;
- all exact-distance-6 edges;
- the deterministic fixed clique;
- every allowed color domain;
- the compact variable numbering.

It requires exactly one allowed color per vertex and rejects out-of-range variables, UNSAT transcripts, incomplete models, and monochromatic edges.

A child may become `SAT_CLOSED` only after the verified coloring, hashes, checker output, and a typed Cruthúnas result record are stored.

## UNSAT boundary

The proof-producing solver writes binary DRAT for the exact frozen CNF. The pinned `drat-trim` checker must return an exact `s VERIFIED` verdict. The workflow then changes the first binary DRAT operation byte to invalid `0x62` and requires the checker to reject the corrupted trace.

A proof-checked UNSAT child is still a universal-trim obstruction. It requires a sixth compatible base or exact incompatibility branching. It does not become `UNSAT_REFINED` merely because its trim CNF is UNSAT.

## Initial f11 lane

The smallest child is `f11`:

- 334 vertices;
- 22,502 exact-distance-6 edges;
- 2,049 compact variables;
- 72,430 clauses;
- CNF SHA-256 `4341c1d9ba4b293f79e48b7a094e757d0c09aa46024d67e9a6f4556f3d3c2388`;
- variable-map SHA-256 `ff5b5f9df7c3364d79dcdf0942cc7ee58fb63a7d1911e7fa2ed4bb60da511f20`.

The `certify-f11` workflow is status-neutral. It uploads checked artifacts but does not modify `child_status.json`, the q00 parent status, the Cruthúnas ledger, or the full theorem target.
