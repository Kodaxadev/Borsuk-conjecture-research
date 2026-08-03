# Borsuk Conjecture Research

This repository is a certificate-first research workspace for finite-combinatorial work on the 0/1-Borsuk problem.

The immediate program targets dimension 11. Candidate proof packages exist for diameters 4 and 8. The diameter-6 subcase remains open and is the active theorem target.

## Exact current status

- `borsuk_n10_k4_reproduction/` — independently reconstructs the published coloring computation within its stated scope.
- `borsuk_11_k4_candidate/` — candidate proof with explicit witnesses and independent verifiers.
- `borsuk_11_k8_candidate/` — candidate proof with an explicit 12-coloring and independent verifiers.
- `borsuk_11_k6_attack_surface/` — canonical 692-vertex one-base reduction for the remaining diameter-6 work.
- `borsuk_11_k6_trim_unsat_certificate/` — independently checked UNSAT certificate showing the coarse trim graph is not 12-colorable.
- `borsuk_11_k6_branch_search/` — verifies the exact incompatibility-branch proof architecture on the root instance.
- `borsuk_11_k6_four_base_reduction/` — exhaustively reduces every component with at least four vertices through 101 intermediate cases to 58 full-isometry trim types of 436–612 vertices.

The k=6 UNSAT result does **not** settle the theorem target. The trim graph contains pairs farther than 6 apart, so it is a universal cover rather than a legal diameter-6 set.

The preferred execution frontier is now the 58-type four-base reduction. Each type can be SAT-closed with an explicit coloring or refined only after proof-checked UNSAT. The root branch package remains the generic coverage-proof infrastructure.

The machine-readable source of truth is [`research/claims.json`](research/claims.json). Candidate packages must not be promoted beyond the status recorded there.

## Verification

Run the standard lightweight verification suite:

```bash
make validate
make verify
make status
```

Recheck the larger stored k=6 proof certificate separately:

```bash
make verify-k6-certificate
```

CI runs the lightweight suite on pushes and pull requests. The certificate check is available as a manual workflow.

## Active k=6 method

The exact-distance-6 coloring graph and the distance-greater-than-6 incompatibility graph are maintained on the same vertex set.

At each trim or descendant search node:

1. a verified 12-coloring closes the node and every descendant;
2. a proof-checked UNSAT result must add another compatible base vertex or branch on an incompatible pair;
3. timeout, crash, or missing certificate remains `UNKNOWN` and cannot close a branch;
4. certified UNSAT with no incompatible pair is a legal counterexample candidate.

The one-base root has 692 vertices, 104,606 coloring edges, and 37,470 incompatibility edges. Symmetry and two additional compatible base vertices produce 101 intermediate cases; canonicalizing the full unordered base under all affine cube isometries leaves 58 solver types.

Independent Python and JavaScript implementations agree on both LF-normalized hashes:

```text
intermediate 101: e60f5f81120e42c8c7eae2da299105e802266f6e92629cd6ac6ee24bcef9db19
canonical 58:    08913feaddbc0f930b6ef90a1677fbc4577cb23dcb6f4dac8987e37056d34742
```

The full certificate-producing plan is documented in [`docs/K6-EXECUTION-PLAN.md`](docs/K6-EXECUTION-PLAN.md).

## Repository rules

- Work on branches, not directly on `main`.
- Keep claims, witnesses, certificates, generators, and verifiers logically separate.
- Preserve provenance and SHA-256 hashes for important artifacts.
- Require complete SAT witnesses or checked UNSAT proofs.
- Export complete branch-coverage manifests for exhaustive computations.
- Treat literature novelty and external mathematical review as separate from CI success.

Agent-specific operating constraints are in [`AGENTS.md`](AGENTS.md).

## Documentation

- [`docs/PROJECT-STATUS.md`](docs/PROJECT-STATUS.md) — human-readable claim ledger.
- [`docs/RESEARCH-ROADMAP.md`](docs/RESEARCH-ROADMAP.md) — phased research plan.
- [`docs/VERIFICATION.md`](docs/VERIFICATION.md) — verification and certificate policy.
- [`docs/K6-EXECUTION-PLAN.md`](docs/K6-EXECUTION-PLAN.md) — exact remaining search architecture.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution workflow.

## Citation and license

Citation metadata is in [`CITATION.cff`](CITATION.cff). The repository is licensed under the MIT license; see [`LICENSE`](LICENSE).
