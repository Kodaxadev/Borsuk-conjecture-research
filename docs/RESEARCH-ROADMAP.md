# Research roadmap

## Program goal

Build an independently auditable finite-combinatorial proof program for the 0/1-Borsuk problem, with the immediate focus on dimension 11.

The repository currently has candidate packages for the diameter-4 and diameter-8 subcases. The diameter-6 subcase is the only active theorem target.

## Phase 0 — Workspace integrity

- Keep repository-level claim status in `research/claims.json`.
- Require package-local verification commands and explicit limitations.
- Run lightweight independent verifiers in CI.
- Keep expensive proof-certificate checks available as separate workflows.
- Prevent candidate or obstruction results from being described as settled theorems.

Exit condition: `make verify` passes and the claim registry is internally consistent.

## Phase 1 — Revalidate existing k=6 artifacts

- Regenerate the 692-vertex trim set from first principles.
- Regenerate the exact-distance-6 coloring graph and the distance-greater-than-6 incompatibility graph.
- Confirm graph statistics and hashes in two implementations.
- Recheck the stored UNSAT proof for the coarse trim coloring instance.
- Record the exact logical scope of the negative result.

Exit condition: the root attack node and its certificate chain are reproducible without relying on historical solver output alone.

## Phase 2 — Build the diameter-compatible branch engine

- Represent a node by its allowed vertex subset.
- Canonicalize node subsets under the stabilizer of the normalized base configuration.
- Query 12-colorability with proof-producing SAT infrastructure.
- Close SAT nodes with independently checked colorings.
- For certified UNSAT nodes, branch on a distance-greater-than-6 incompatibility edge.
- Treat timeout, crash, missing proof, and checker failure as `UNKNOWN`.

Exit condition: the root node expands into two correctly hashed child nodes and the coverage verifier rejects intentionally corrupted manifests.

## Phase 3 — Compress before scaling

- Measure stabilizer orbits on vertices and incompatibility edges.
- Memoize canonical node hashes.
- Prefer branch edges supported by UNSAT cores and large symmetry orbits.
- Search for smaller induced non-12-colorable cores inside the coarse trim graph.
- Test whether structural lemmas can replace repeated branches.

Exit condition: a reproducible benchmark shows meaningful reduction in unique nodes or certificate cost relative to naive branching.

## Phase 4 — Complete the k=6 coverage tree

- Resolve every reachable node to `SAT_CLOSED`, `UNSAT_BRANCHED`, or `LEGAL_UNSAT`.
- Leave no `UNKNOWN` node in a theorem-level run.
- Produce a complete manifest linking every parent, branch deletion, child, witness, proof, and hash.
- Independently verify the tree and all terminal artifacts.

Possible outcomes:

- all legal branches close by SAT, giving a candidate proof of the k=6 subcase;
- a `LEGAL_UNSAT` leaf yields a concrete finite counterexample candidate;
- unresolved resource-heavy nodes identify the exact remaining computational frontier.

## Phase 5 — External review and publication preparation

Only after the full k=6 result is internally complete:

- perform a fresh literature and priority search;
- contact relevant authors or specialists;
- obtain independent mathematical review of the normalization and branch-coverage argument;
- rerun certificates on a clean environment;
- freeze artifacts and hashes in a release;
- prepare a paper that distinguishes human mathematics, generated constructions, solver evidence, and independent verification.

## Deferred work

The Leech-lattice candidate, classical low-dimensional Borsuk bounds, and unrelated recurrence searches remain secondary until they directly support or supersede the active dimension-11 program.
