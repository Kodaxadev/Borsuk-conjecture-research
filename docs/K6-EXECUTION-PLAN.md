# Exact execution plan for the open n=11, k=6 case

## Current state

Let `T` be the 692-vertex canonical one-base trim set recorded in `borsuk_11_k6_attack_surface/`. Its exact-distance-6 graph is not 12-colorable, and the separate certificate package verifies that negative result.

This does not settle the theorem target because `T` contains incompatible pairs at Hamming distance greater than 6. A legal normalized component must be a subset of `T` containing no such pair.

The remaining task is to prove that every diameter-compatible subset of `T` is 12-colorable, or to find a legal subset that is not.

## Exhaustive compressed front

Do not begin by branching the full 692-vertex root arbitrarily.

The four-base reduction proves:

1. components with at most three vertices are trivially 12-colorable;
2. every larger normalized component lies in one of 101 intermediate four-base cases;
3. full canonicalization of the unordered four-point base under affine cube isometries reduces these to **58 trim types**.

The 101-case hash is the exhaustive audit layer. The 58-type hash is the solver frontier. `case_status.json` must account for all 58 types and defaults every unverified type to `UNKNOWN`.

## Two graphs on every trim

For each canonical trim `U`, maintain two independently generated graphs:

- `G6[U]`: vertices are adjacent when their Hamming distance is exactly 6. This is the graph that must be 12-colored.
- `D[U]`: vertices are adjacent when their Hamming distance is greater than 6. A legal diameter-6 set is an independent set in `D[U]`.

The local theorem target is:

> Every independent set `S` of `D[U]` induces a 12-colorable graph `G6[S]`.

## Certificate-producing decision algorithm

At a trim or descendant node `U`:

1. Ask whether `G6[U]` is 12-colorable.
2. If SAT, store and independently verify the complete coloring. The whole node closes because every descendant is an induced subgraph of a colorable graph.
3. If UNSAT, require a checked proof trace before refining the node.
4. Prefer adding a fifth compatible base vertex and quotienting its orbits when that gives fewer exhaustive children.
5. Otherwise choose an incompatibility edge `{u,v}` of `D[U]` and branch into `U-{u}` and `U-{v}`. Every legal subset lies in at least one child.
6. If `D[U]` has no edge, `U` is itself a legal diameter-6 set. Certified UNSAT is then a genuine counterexample candidate and must trigger immediate independent reconstruction.

No timeout, heuristic failure, crash, or missing certificate closes a node.

## Required result states

Top-level four-base types use:

- `SAT_CLOSED`: complete coloring witness independently verified.
- `UNSAT_REFINED`: checked UNSAT proof plus exhaustive child coverage.
- `LEGAL_UNSAT`: checked UNSAT proof and no incompatibility edge.
- `UNKNOWN`: timeout, crash, heuristic failure, missing proof, checker failure, or incomplete work.

Descendant branch nodes may use `UNSAT_BRANCHED` when the refinement is a binary incompatibility deletion. Every non-SAT UNSAT state requires a checked proof trace.

`UNKNOWN` nodes block any theorem-level conclusion.

## Search compression

Apply compression only when it preserves the certificate chain:

1. Canonicalize full unordered base configurations, not only a chosen ordered prefix.
2. Memoize canonical vertex-set or base-signature hashes.
3. Prefer fifth-base or incompatibility orbits with high symmetry and strong UNSAT-core incidence.
4. Extract smaller UNSAT induced cores only with a verified embedding into the parent node.
5. Reuse a SAT coloring only after checking it on the exact canonical representative.
6. Map every closed canonical representative back to all intermediate cases in its isometry class.

A quotient computation is an optimization and coverage lemma, not a coloring proof by itself.

## Coverage manifest

The final artifact must include, for every canonical type and descendant node:

- canonical id and SHA-256 vertex-set or base-signature hash;
- all covered intermediate case ids;
- parent id and refinement condition;
- vertex and edge counts for both graph relations;
- result state;
- solver name, version, seed, command, and resource limits;
- model or proof-trace hash;
- independent checker output hash;
- complete child ids for refined nodes.

A separate verifier must check:

- regeneration of the 101 intermediate cases and 58 canonical types;
- complete mapping of all 101 cases to the 58 types;
- graph regeneration from bit masks;
- every SAT coloring;
- every UNSAT proof;
- every fifth-base or incompatibility refinement is exhaustive;
- all parent-child restrictions and hashes;
- no `UNKNOWN` remains;
- all artifact hashes match.

## Immediate implementation milestone

1. Keep the 101 intermediate and 58 canonical hashes stable in two implementations.
2. Generate a static difficulty inventory for `q00` through `q57`.
3. Run witness-only heuristics only for scheduling; record no failure as evidence.
4. Produce deterministic CNFs with a documented variable map.
5. Resolve the easiest canonical type to `SAT_CLOSED` with an independently verified model.
6. Resolve one hard type through proof-producing SAT or certified refinement.
7. Add negative tests that corrupt a coloring, proof reference, canonical mapping, and child hash.

Only after this loop is green should long-running parallel classification begin.

## Logical boundary

The full `n=11, k=6` claim remains open until all 58 canonical types have complete certificate-backed coverage and all 101 intermediate cases are verified to map into those types. External mathematical review of the normalization and canonicalization remains a separate dependency before public theorem promotion.
