# Status

## Verified reduction

- Third normalized vertex families: 5.
- Pointwise fourth-vertex orbits: 149.
- Intermediate triple-stabilizer cases: 101.
- Full unordered four-base isometry types: 58.
- Trim sizes: 436–612 vertices.
- Python and JavaScript independently produce the same intermediate and canonical case-list hashes.

## Current classification state

- `UNKNOWN`: 58.
- `SAT_CLOSED`: 0.
- `UNSAT_REFINED`: 0.
- `LEGAL_UNSAT`: 0.

`case_status.json` is intentionally unchanged. No full isometry type has yet completed the certificate-backed refinement required for a case override.

## Scoped q00 obstruction

The deterministic compact list-coloring CNF for the `q00` universal trim is proof-checked UNSAT:

- CNF SHA-256: `36da8f78ae376b370f119d1fa16a58f6504607d949ac8315648fdbda52450299`;
- binary DRAT proof SHA-256: `59bf62a00d0c63b5ced7967c33421d953af5b96e423cc93dc862e595d08561b5`;
- pinned `drat-trim` verdict: `s VERIFIED`;
- corrupted-first-record control: rejected.

Cruthúnas registers this separately as `n11-k6-q00-trim-unsat`:

```text
Gate 4; COMPUTATIONAL; [CERTIFICATE_CHECKED]; WORKING
```

This does not close `q00`. The trim may contain pairs farther than Hamming distance 6, so the obstruction must be refined exhaustively by compatible fifth bases or exact incompatibility branching before `q00` can become `UNSAT_REFINED`.

## Not established

- No canonical isometry type is recorded as `SAT_CLOSED`, `UNSAT_REFINED`, or `LEGAL_UNSAT`.
- No heuristic failure is evidence of non-colorability.
- The trims are universal covers and may contain pairs farther than 6 apart.
- The scoped q00 certificate does not settle the n=11, k=6 theorem target.
- The full theorem remains Gate 2, `UNCHECKED`, and `OPEN`.

## Next action

Construct the exhaustive q00 fifth-base or incompatibility-branch refinement. Each child must be closed by an independently verified coloring or a checked UNSAT certificate. Solver work on the remaining q01–q57 trims can proceed in parallel, but no bounded or uncertified run may alter case status.
