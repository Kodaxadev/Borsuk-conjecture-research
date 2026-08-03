# Verification guide

The repository separates mathematical statements, generated objects, solver outcomes, and independently checked certificates. Passing one layer does not silently establish the next.

## Required result states

Every solver-backed decision must be recorded as exactly one of:

- `SAT`: complete model or coloring present and independently verified;
- `UNSAT`: proof trace present and independently checked;
- `UNKNOWN`: timeout, crash, resource limit, missing certificate, checker failure, or incomplete search.

A timeout is never evidence of UNSAT. Failure to find a coloring is never evidence of non-colorability.

## Package requirements

Every package-level computational claim should include:

- a precise claim and scope;
- a deterministic generator or canonical input;
- exact object statistics;
- a witness or proof certificate;
- a verifier that reconstructs the relevant object independently;
- SHA-256 hashes for important immutable artifacts;
- a machine-readable report where practical;
- explicit limitations and non-implications.

Candidate theorem packages should also include a dependency graph and hostile audit.

## Repository-level checks

Run:

```bash
make validate
make verify
make status
```

`make validate` checks the machine-readable claim registry and package links.

`make verify` runs the lightweight package verifiers:

- the n=10, k=4 reproduction;
- Python and JavaScript verification for the n=11, k=4 candidate;
- Python and JavaScript verification for the n=11, k=8 candidate;
- structural, independent, and hash verification for the n=11, k=6 attack surface.

The stored k=6 DRUP certificate is intentionally separate because it is larger:

```bash
make verify-k6-certificate
```

A manual GitHub Actions workflow exposes the same check.

## Independence rules

A verifier is not independent merely because it is in another file. Prefer implementations that differ in language, graph construction method, iteration order, and data path.

At minimum:

- regenerate edges from original bit masks rather than trusting a stored edge list;
- verify every color assignment against every relevant edge;
- verify graph counts and canonical hashes;
- ensure a certificate checker consumes the original CNF and proof trace;
- run negative controls by corrupting a witness, lemma, hash, or tree edge and confirming rejection.

## Branch-coverage proofs

A complete computational proof by case splitting must export a coverage manifest. The verifier must establish:

- every branch condition is valid;
- each child is exactly the claimed restriction of its parent;
- all required children exist;
- canonical-node deduplication is sound;
- every terminal SAT node has a checked witness;
- every terminal UNSAT node has a checked proof;
- no `UNKNOWN` node remains.

Solver transcripts without a coverage manifest do not establish exhaustive search.

## Claim promotion

Repository CI establishes reproducibility of recorded artifacts, not novelty, publication priority, or external mathematical acceptance.

A `candidate-proof` remains a candidate after CI passes. Promotion requires external review, literature and attribution checks, and an explicit update to `research/claims.json` with supporting evidence.
