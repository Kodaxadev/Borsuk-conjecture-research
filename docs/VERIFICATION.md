# Verification guide

The repository separates mathematical statements, generated objects, solver outcomes, independently checked certificates, and **Cruthúnas governance state**. Passing one layer does not silently establish the next.

Cruthúnas validates whether claim registration, sources, evidence, transitions, artifact paths, and gate tuples are internally coherent. It does not prove the mathematical claim.

## Required result states

Every solver-backed decision must be recorded as exactly one of:

- `SAT`: complete model or coloring present and independently verified;
- `UNSAT`: proof trace present and independently checked;
- `UNKNOWN`: timeout, crash, resource limit, missing certificate, checker failure, or incomplete search.

A timeout is never evidence of UNSAT. Failure to find a coloring is never evidence of non-colorability.

A bounded workflow result is initially a **probe artifact**, not registered evidence. It may enter Cruthúnas only after its files are preserved, hashed, independently checked, and linked to the exact claim or case it supports.

## Cruthúnas verification layers

Every material claim has four distinct governance dimensions:

1. **Gate** — registration and review progress.
2. **Epistemic class** — mathematical, computational, hybrid, or infrastructure.
3. **Verification state** — unchecked, internally verified, independently reproduced, certificate checked, formally verified, or externally reviewed.
4. **Lifecycle state** — open, working, superseded, or retracted.

Current gate meanings:

1. `REGISTERED`
2. `SCOPED`
3. `EVIDENCE_LINKED`
4. `INTERNALLY_CHECKED`
5. `EXTERNALLY_REVIEWED`
6. `PUBLICATION_FROZEN`

A Gate 4 attack surface is not a theorem. A Gate 4 candidate proof is not externally reviewed. The full `n11-k6-full` target remains:

```text
Gate 2; MATHEMATICAL; [UNCHECKED]; OPEN
```

## Package requirements

Every package-level computational claim should include:

- a precise claim and scope;
- a registered claim ID;
- a source-document boundary;
- a deterministic generator or canonical input;
- exact object statistics;
- a witness or proof certificate;
- a verifier that reconstructs the relevant object independently;
- SHA-256 hashes for important immutable artifacts;
- environment, tool, seed, and resource-limit records where applicable;
- a machine-readable report;
- explicit limitations and non-implications;
- a typed Cruthúnas evidence record when the artifact is material.

Candidate theorem packages should also include a dependency graph and hostile audit.

## Repository-level checks

Run:

```bash
python scripts/cruthunas.py check --all
python scripts/cruthunas.py adapters check
python scripts/validate_cruthunas_transactions.py
make validate
make verify
make status
```

`make validate` checks:

- Cruthúnas claim/ledger coverage;
- dependency acyclicity;
- source boundaries;
- evidence typing and artifact existence;
- ledger/evidence support matching;
- transition continuity and mandatory Gate 3 → Gate 4 registration;
- dry-run transaction consistency;
- Claude/Codex adapter synchronization;
- the mathematical claim registry and package links.

`make verify` then runs the lightweight package verifiers:

- the n=10, k=4 reproduction;
- Python and JavaScript verification for the n=11, k=4 candidate;
- Python and JavaScript verification for the n=11, k=8 candidate;
- structural, independent, and hash verification for the n=11, k=6 root attack surface;
- root branch-manifest verification;
- independent reproduction of the 101 intermediate and 58 canonical four-base cases;
- 58-case status validation;
- deterministic solver inventory and q00 CNF/model-verifier smoke tests.

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
- run negative controls by corrupting a witness, lemma, hash, case override, or tree edge and confirming rejection;
- ensure the Cruthúnas evidence record points to the independently checked artifact rather than only the producing program.

## The 58-case solver frontier

All 58 canonical four-base trims begin as `UNKNOWN`.

A case may leave `UNKNOWN` only as follows:

- `SAT_CLOSED`: complete coloring stored and independently verified from the canonical case ID;
- `UNSAT_REFINED`: proof trace checked independently and exact refinement children or incompatibility branches recorded;
- `LEGAL_UNSAT`: proof trace checked independently and no distance-greater-than-6 pair remains;
- otherwise it stays `UNKNOWN`.

A bounded q00–q57 workflow labels its output `PROBE_ONLY_NOT_REGISTERED_EVIDENCE`. That output cannot change `case_status.json`, the claim registry, or the Cruthúnas ledger automatically.

## Branch-coverage proofs

A complete computational proof by case splitting must export a coverage manifest. The verifier must establish:

- every branch condition is valid;
- each child is exactly the claimed restriction of its parent;
- all required children exist;
- canonical-node deduplication is sound;
- every terminal SAT node has a checked witness;
- every terminal UNSAT node has a checked proof;
- every material terminal result has registered typed evidence;
- no `UNKNOWN` node or canonical type remains.

Solver transcripts without a coverage manifest do not establish exhaustive search.

## Status changes

A status change requires a serializable dry-run transaction containing:

- the exact claim ID;
- the expected current transition ID;
- one contiguous gate move;
- actor and reason;
- source revision;
- evidence IDs;
- planned evidence, transition, and ledger operations;
- either satisfied requirements or explicit blocking conditions.

The blocked plan for `n11-k6-full` records why Gate 2 → Gate 3 is not currently allowed.

## Claim promotion

Repository CI establishes reproducibility and governance coherence of recorded artifacts, not novelty, publication priority, external mathematical acceptance, or framework maturity.

A `candidate-proof` remains a candidate after CI passes. Promotion requires new evidence, external review where appropriate, literature and attribution checks, and contiguous updates to both `research/claims.json` and the Cruthúnas records.
