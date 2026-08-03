# Project status ledger

Updated: 2026-08-02

This file summarizes the human-readable state. [`research/claims.json`](../research/claims.json) is the mathematical claim registry. The [`cruthunas/`](../cruthunas/) records govern source boundaries, typed evidence, transitions, and status promotion.

## Active theorem target

The unresolved target is the diameter-6 subcase of the 0/1-Borsuk problem in dimension 11:

> Every diameter-6 subset of the 11-dimensional Boolean cube is partitionable into at most 12 subsets of smaller diameter.

This claim remains **open** in the repository and is intentionally held by Cruthúnas at:

```text
Gate 2; MATHEMATICAL; [UNCHECKED]; OPEN
```

The blocked Gate 2 → Gate 3 dry-run transaction records the missing theorem-level evidence. Checked reductions, solver infrastructure, and scoped certificates remain separate Gate 4 claims and do not automatically support promotion of the full theorem target.

## Cruthúnas governance posture

The repository currently operates as a **CR-0 repository-local pilot**:

- every material claim has a unique registered ID;
- claim dependencies are checked for cycles;
- source documents are restricted to explicit claim boundaries;
- evidence records include artifact paths, commands, environments, hashes, verification state, and limitations;
- gate transitions are contiguous;
- every Gate 3 → Gate 4 move is registered;
- Claude and Codex adapters are generated from one canonical `cruthunas-govern` skill;
- solver probes cannot alter claim or case status automatically;
- status changes require a serializable dry-run transaction.

Cruthúnas checks governance coherence only. It does not establish mathematical truth, novelty, external acceptance, publication readiness, CR-1, or framework maturity.

## Established package-level evidence

### n=10, k=4 reproduction

The published coloring computation for the three stated cover graphs has been independently reconstructed. This verifies the coloring step within the package's stated scope; it does not independently verify universal coverage.

Cruthúnas state:

```text
Gate 4; COMPUTATIONAL; [INDEPENDENTLY_REPRODUCED]; WORKING
```

### n=11, k=4 candidate

The package contains a structural proof, explicit coloring witnesses, and independent Python and JavaScript verification. It remains a candidate proof pending external mathematical and priority review.

Cruthúnas state:

```text
Gate 4; HYBRID; [INTERNALLY_VERIFIED]; WORKING
```

### n=11, k=8 candidate

The package contains an explicit 12-coloring of the universal even-weight cover and independent Python and JavaScript verification. It remains a candidate proof pending external mathematical and priority review.

Cruthúnas state:

```text
Gate 4; HYBRID; [INTERNALLY_VERIFIED]; WORKING
```

### n=11, k=6 one-base attack surface

The one-base normalization produces a canonical trim graph with:

- 692 vertices;
- 104,606 exact-distance-6 coloring edges;
- 37,470 distance-greater-than-6 incompatibility pairs.

This is a universal cover for possible normalized components, not a legal diameter-6 set.

### n=11, k=6 certified obstruction

The canonical trim graph has a checked UNSAT certificate for 12-colorability. This proves that the one-base cover is too coarse. It does **not** disprove or settle the diameter-6 theorem target because the trim graph contains pairs farther than 6 apart.

Cruthúnas records this as a scoped obstruction:

```text
Gate 4; COMPUTATIONAL; [CERTIFICATE_CHECKED]; WORKING
```

### n=11, k=6 generic branch scaffold

The branch-search package independently regenerates both graph relations and verifies the exact rule that proof-checked UNSAT must branch on an incompatibility pair. Its first two root children remain `UNKNOWN` and are retained as a test of generic coverage-manifest infrastructure.

### n=11, k=6 four-base reduction

The preferred execution frontier is now smaller:

- 5 third-vertex symmetry families;
- 149 pointwise fourth-vertex orbits;
- 101 intermediate cases after stabilizers of the selected metric triples;
- 58 full unordered four-base isometry types;
- trim sizes 436–612 vertices.

The complete unordered-base invariant is the lexicographically least eight-entry coordinate-pattern multiplicity tuple over all four translation origins and all six labelings of the remaining three points. Equal tuples give an explicit affine cube isometry.

Independent Python and JavaScript implementations agree on:

```text
intermediate 101: e60f5f81120e42c8c7eae2da299105e802266f6e92629cd6ac6ee24bcef9db19
canonical 58:    08913feaddbc0f930b6ef90a1677fbc4577cb23dcb6f4dac8987e37056d34742
```

Cruthúnas links both the symmetry reduction and deterministic SAT-lane smoke tests to this Gate 4 infrastructure claim. `case_status.json` still records all 58 types as `UNKNOWN`.

## Current research frontier

Resolve the 58 canonical trim types:

- a verified SAT coloring closes an entire isometry type and every descendant;
- a proof-checked UNSAT trim must be refined by a fifth compatible base or an exact incompatibility branch;
- a legal proof-checked UNSAT node is a counterexample candidate;
- timeout, crash, heuristic failure, or missing certificate remains `UNKNOWN`.

The bounded q00–q57 workflow produces probe artifacts marked `PROBE_ONLY_NOT_REGISTERED_EVIDENCE`. A material result must be preserved, hashed, independently checked, and registered as typed Cruthúnas evidence before any case override or claim transition.

The 101 intermediate cases remain the exhaustive coverage audit beneath the 58-type solver frontier.

Full details are in [`K6-EXECUTION-PLAN.md`](K6-EXECUTION-PLAN.md).

## Promotion boundary

No repository summary, paper draft, social post, or release should claim that the full dimension-11 Boolean-cube result is solved unless:

1. all 58 canonical k=6 types have complete diameter-compatible coverage;
2. every SAT leaf has an independently checked coloring;
3. every UNSAT branch has an independently checked proof trace;
4. every material result has typed evidence and a valid transition history;
5. no branch remains `UNKNOWN`;
6. the mathematical normalization and coverage argument is independently reviewed;
7. novelty and attribution are checked against the literature and relevant authors.
