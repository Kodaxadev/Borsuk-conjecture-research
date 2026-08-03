# Agent operating contract

This repository is a certificate-first mathematical research workspace. Agents may extend the work, but they may not silently upgrade the status of a claim.

## Authority order

1. Package-local mathematical statement and proof notes.
2. `research/claims.json`, which records repository-level status and scope.
3. Explicit certificates, witnesses, hashes, and independent verifiers.
4. Solver logs and exploratory notebooks.
5. Informal summaries.

When two layers conflict, the higher layer wins until the conflict is resolved and documented.

## Branch discipline

- Never make research changes directly on `main`.
- Use a dedicated branch and small, reviewable commits.
- Preserve existing artifacts; do not replace a witness or certificate without retaining provenance.
- Do not rewrite a claim merely to make it sound stronger.

## Allowed claim states

- `reproduction-verified`: an existing published computation has been independently reconstructed within the stated scope.
- `candidate-proof`: a proof package and witnesses pass repository checks but have not completed external mathematical review or priority verification.
- `certified-obstruction`: a negative computational result has an independently checked proof certificate, but its logical scope may be narrower than the theorem target.
- `attack-surface`: a reduction, graph, core, or search instance that does not itself settle the theorem target.
- `open`: unresolved.

Only `research/claims.json` may define the current repository-level state.

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
- it does not settle the full Boolean-cube Borsuk case.

Any next-stage branch must add diameter-compatibility information or an equivalent structural restriction.

## Artifact requirements

Every new computational claim must include:

- a deterministic generator or an immutable canonical input;
- exact dimensions and graph statistics;
- a SHA-256 manifest for important artifacts;
- a verification command;
- a machine-readable report;
- a statement of what the result does **not** prove;
- an independent verifier whenever practical.

Generated files must not be trusted merely because they were produced by the same program that claims to verify them.

## Working commands

Run these before proposing a change:

```bash
make status
make verify
```

Long solver runs are not part of ordinary CI. Store their exact command, solver version, seed, limits, result state, model or proof trace, and verification output in the relevant package.

## Active research target

The current unresolved theorem target is the `n=11, k=6` diameter case. The preferred order of attack is:

1. validate the existing trim graph and UNSAT chain;
2. introduce diameter-compatible branching or quotient reductions;
3. search for the smallest unresolved canonical branch;
4. produce SAT witnesses or proof-producing UNSAT runs for every terminal branch;
5. export a complete coverage manifest linking all branches to the theorem claim.

Do not start an unrelated Borsuk search while this dependency remains unresolved unless the new work directly reduces it.
