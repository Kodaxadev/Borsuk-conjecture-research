# Agent operating contract

This repository is a certificate-first mathematical research workspace governed from the start by the repository-local **Cruthúnas CR-0** policy layer. Agents may extend the work, but they may not silently upgrade the status of a claim.

## Mandatory startup

Before changing proof text, claim status, solver outputs, case manifests, evidence, or public summaries:

1. Read `cruthunas/skills/cruthunas-govern/SKILL.md`.
2. Read `cruthunas/project.json`, `research/claims.json`, and `cruthunas/ledger.json`.
3. Identify every affected claim ID.
4. Read the registered sources, evidence, and transition history for those claims.
5. Run:

```bash
python scripts/cruthunas.py status
python scripts/cruthunas.py check --changed
```

## Authority model

Mathematical content and governance status are separate authority domains:

1. Package-local theorem statements, definitions, proof notes, and exact generated objects define mathematical content.
2. `research/claims.json` defines repository-level claim wording, dependencies, limitations, and public-scope status.
3. `cruthunas/ledger.json`, `cruthunas/evidence.json`, and `cruthunas/transitions.json` define whether that status is properly supported and how it may change.
4. Explicit certificates, witnesses, hashes, independent verifiers, and coverage manifests provide evidence.
5. Solver logs and exploratory notebooks are supporting records only.
6. Informal summaries have no authority.

A conflict must be resolved explicitly. Do not choose the stronger interpretation.

## Cruthúnas transition discipline

- Do not create an unregistered material claim.
- Do not edit a gate, verification state, or lifecycle state freehand.
- Prepare a serializable dry-run transaction before a status change.
- Register typed evidence before linking it to a transition.
- Preserve source-document boundaries.
- Keep transitions contiguous.
- Register every Gate 3 → Gate 4 move explicitly.
- Do not promote a candidate proof to external review, publication, or settlement without new evidence and a recorded transition.
- Cruthúnas passing establishes repository coherence only, not mathematical truth, novelty, external acceptance, publication readiness, CR-1, or framework maturity.

## Branch discipline

- Never make research changes directly on `main`.
- Use a dedicated branch and small, reviewable commits.
- Preserve existing artifacts; do not replace a witness or certificate without retaining provenance.
- Do not rewrite a claim merely to make it sound stronger.
- Keep Claude and Codex adapters generated from the canonical `cruthunas-govern` skill.

## Allowed repository claim states

- `reproduction-verified`: an existing published computation has been independently reconstructed within the stated scope.
- `candidate-proof`: a proof package and witnesses pass repository checks but have not completed external mathematical review or priority verification.
- `certified-obstruction`: a negative computational result has an independently checked proof certificate, but its logical scope may be narrower than the theorem target.
- `attack-surface`: a reduction, graph, core, or search instance that does not itself settle the theorem target.
- `open`: unresolved.

`research/claims.json` defines the claim state. Cruthúnas must contain a compatible gate tuple and complete transition chain for every claim.

## SAT and coloring rules

A solver outcome must be represented as exactly one of:

- `SAT`: accompanied by a complete model or coloring and checked by an independent verifier.
- `UNSAT`: accompanied by a proof trace accepted by an independent proof checker.
- `UNKNOWN`: timeout, resource exhaustion, crash, incomplete search, or any result lacking the required certificate.

Never treat a timeout or failure to find a coloring as UNSAT.

For the active `n=11, k=6` problem:

- the 692-vertex universal trim graph is certified not 12-colorable;
- that graph is not itself a legal diameter-6 set;
- therefore its UNSAT certificate rejects only the coarse one-base cover;
- it does not settle the full Boolean-cube Borsuk case;
- the 58 four-base trim types remain `UNKNOWN` at certificate level unless their case records say otherwise.

Any next-stage UNSAT result for a cover must add diameter-compatibility information, refine the base, or branch on an incompatible pair.

## Artifact requirements

Every new computational claim must include:

- a deterministic generator or an immutable canonical input;
- exact dimensions and graph statistics;
- SHA-256 hashes for central artifacts;
- a verification command;
- a machine-readable report;
- environment and tool details;
- source or revision pins;
- a statement of what the result does **not** prove;
- an independent verifier whenever practical;
- a typed Cruthúnas evidence record and transition record when status changes.

Generated files must not be trusted merely because they were produced by the same program that claims to verify them.

## Required checks

Run before proposing a change:

```bash
python scripts/cruthunas.py check --all
python scripts/cruthunas.py adapters check
make verify
make status
```

Long solver runs are not part of ordinary CI. Store their exact command, solver version, seed, limits, result state, model or proof trace, verification output, and hashes in the relevant package before registering them as evidence.

## Active research target

The current unresolved theorem target is `n11-k6-full`, held by Cruthúnas at:

```text
Gate 2; MATHEMATICAL; [UNCHECKED]; OPEN
```

The preferred order of attack is:

1. preserve and revalidate the existing trim graph and UNSAT chain;
2. work through the 58 canonical four-base trim types;
3. close a type with a verified SAT coloring or refine it after proof-checked UNSAT;
4. maintain complete case and branch coverage manifests;
5. eliminate every `UNKNOWN` dependency;
6. register theorem-level evidence only after an independent verifier checks complete coverage.

Do not start an unrelated Borsuk search while this dependency remains unresolved unless the new work directly reduces it.
