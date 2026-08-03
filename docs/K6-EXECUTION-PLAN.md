# Exact execution plan for the open n=11, k=6 case

## Current state

Let `T` be the 692-vertex canonical one-base trim set recorded in
`borsuk_11_k6_attack_surface/`. Its exact-distance-6 graph is not 12-colorable,
and the separate certificate package verifies that negative result.

This does not settle the theorem target because `T` contains incompatible pairs
at Hamming distance greater than 6. A legal normalized component must be a
subset of `T` containing no such pair.

The remaining task is therefore not to color `T`. It is to prove that every
**diameter-compatible subset** of `T` is 12-colorable, or to find a legal subset
that is not.

## Two graphs on the same vertex set

Maintain two independently generated graphs on `T`:

- `G6`: vertices are adjacent when their Hamming distance is exactly 6. This is
  the graph that must be 12-colored.
- `D`: vertices are adjacent when their Hamming distance is greater than 6.
  A legal diameter-6 set is an independent set in `D`.

The theorem target for this normalized branch is:

> Every independent set `S` of `D` induces a 12-colorable graph `G6[S]`.

## Certificate-producing branch algorithm

At a search node, let `U` be the currently allowed subset of `T`.

1. Ask whether `G6[U]` is 12-colorable.
2. If SAT, store and independently verify the coloring. The entire branch is
   closed because every descendant is an induced subgraph of a colorable graph.
3. If UNSAT, require a checked proof trace. Then search `D[U]` for an
   incompatibility edge `{u,v}`.
4. If such an edge exists, branch into `U - {u}` and `U - {v}`. Every legal
   subset of `U` lies in at least one child because it cannot contain both ends.
5. If no incompatibility edge exists, `U` is itself a legal diameter-6 set.
   Certified UNSAT at this node is a genuine counterexample candidate and must
   trigger immediate independent reconstruction.

This creates an exact coverage tree. No timeout or heuristic failure closes a
branch.

## Required node states

Every node must end in exactly one machine-readable state:

- `SAT_CLOSED`: complete coloring witness verified independently.
- `UNSAT_BRANCHED`: checked UNSAT proof plus a recorded incompatibility edge and
  two child identifiers.
- `LEGAL_UNSAT`: checked UNSAT proof and no incompatibility edge; potential
  counterexample.
- `UNKNOWN`: timeout, crash, missing proof, checker failure, or incomplete work.

`UNKNOWN` nodes remain open and block any theorem-level conclusion.

## Search compression

Apply compression only when it preserves the certificate chain:

1. Canonicalize `U` under the stabilizer of the fixed normalized base
   configuration `{0,A}`.
2. Memoize canonical node hashes.
3. Prefer incompatibility edges with high symmetry orbit size or high incidence
   in the current UNSAT core.
4. Extract smaller UNSAT induced cores when possible, but retain a verified
   mapping from the core to `U`.
5. Reuse a SAT coloring only after independently checking it on the exact node.

A quotient or orbit computation is an optimization, not a proof by itself.

## Coverage manifest

The final proof artifact must include a manifest containing, for every node:

- canonical node id and SHA-256 vertex-set hash;
- parent id and branch deletion;
- vertex and edge counts for both `G6[U]` and `D[U]`;
- terminal state;
- solver name, version, seed, command, and resource limits;
- model or proof-trace hash;
- independent checker output hash;
- child ids for branched nodes.

A separate verifier must check:

- graph regeneration from bit masks;
- every SAT coloring;
- every UNSAT proof;
- every branch edge is genuinely incompatible;
- child sets equal the parent with the stated endpoint removed;
- every nonterminal node has both children;
- no `UNKNOWN` node remains;
- all referenced artifact hashes match.

## First implementation milestone

Do not begin with a full uncontrolled solver run. Implement and verify:

1. deterministic generation of `T`, `G6`, and `D`;
2. canonical vertex-set serialization and hashing;
3. one root-node record matching the existing 692-vertex artifacts;
4. proof-checked root UNSAT import;
5. deterministic selection of one incompatibility edge;
6. creation of the first two child-node records;
7. a manifest verifier that rejects missing children, altered hashes, and an
   intentionally corrupted witness or proof reference.

Only after this seven-step loop is green should long-running branching begin.

## Logical boundary

A complete tree with only `SAT_CLOSED` and correctly expanded
`UNSAT_BRANCHED` leaves proves the normalized one-base case. The surrounding
mathematical reduction must still establish that every nontrivial diameter-6
component is isometric to a subset represented by the root trim instance.
That reduction is recorded separately and must remain an explicit dependency
in any theorem claim.
