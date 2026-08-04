# q00 compact-trim UNSAT certificate

## Exact scoped claim

The deterministic compact list-coloring CNF for canonical four-base trim type `q00` is UNSAT.

This is a certificate for the **universal trim cover only**. The trim can contain pairs at Hamming distance greater than 6, so this result does not settle the legal `n=11, k=6` Boolean-cube Borsuk subcase and does not change `case_status.json`.

## Frozen instance

- case: `q00`
- encoding: compact list-coloring
- vertices: 436
- variables: 2,724
- clauses: 130,840
- CNF SHA-256: `36da8f78ae376b370f119d1fa16a58f6504607d949ac8315648fdbda52450299`
- variable-map SHA-256: `5f94c619b6a5996c54f269a88de5bfaff042e4c855ea8543869b84009c7dae45`

## Proof and checker

- proof format: binary DRAT
- proof bytes: 118,009,628
- proof records: 3,374,480
- proof SHA-256: `59bf62a00d0c63b5ced7967c33421d953af5b96e423cc93dc862e595d08561b5`
- checker: `drat-trim`
- checker revision: `2e3b2dc0ecf938addbd779d42877b6ed69d9a985`
- checker binary SHA-256: `92f0aa9575ed519d66a99b8b1b3dde6ece4618ae4c202a3a4b200265dda0aa7a`
- positive verdict: `s VERIFIED`

## Negative controls

Two independent checker-sensitivity controls are preserved.

### Structural corruption

The first binary DRAT operation byte was changed from valid addition byte `0x61` to invalid byte `0x62`. The pinned checker rejected the corrupted proof with exit status 1.

### Semantic record-aligned prefix

A format-aware parser found one explicit empty-clause addition at byte offset `118009626`, the final record of the proof. Removing only that record still returned `s VERIFIED`: `drat-trim` had already detected a root contradiction from the preceding learned clauses. Therefore explicit empty-clause-record removal alone is not a valid negative control for this proof/checker pair.

The successful semantic control truncates at a complete binary-DRAT record boundary before the empty clause and 256 immediately preceding records:

- records removed at boundary: 257
- negative proof bytes: 118,008,578
- negative proof SHA-256: `f38c1b6439eb20f6d2c1a80e63e1de7c8d421ea5d65e7fb61961a0f5d609c064`
- checker exit status: 1
- exact verdict: `s NOT VERIFIED`
- elapsed wall time: 5.43 seconds
- metadata: `semantic-negative-control.json`

This gives the required controlled pair: the untouched proof is accepted and a deterministic, format-aware record prefix before the checker acceptance boundary is rejected.

## Artifact chain

Proof-producing run:

- workflow run ID: `30822622138`
- artifact ID: `8859778824`
- artifact digest: `sha256:e75f4a6571a22bef7f686ec6f91037f17598fecf19872d1c085113f706be2351`

Final proof bundle:

- workflow run ID: `30827345819`
- certificate artifact ID: `8861415369`
- certificate artifact digest: `sha256:3131aacfd28b3959b1205067c6cff2dd34403fa4029bb70702ffc63b2a2e0a54`
- metadata artifact ID: `8861414746`
- metadata artifact digest: `sha256:16e5510f997d21380653b641e6e02a62e13e5bf0ec769b43e9446463bc87faa9`
- artifact expiry: `2026-11-01`

Semantic-control artifact:

- workflow run ID: `30828438527`
- artifact ID: `8861877893`
- artifact digest: `sha256:31f10ecdc9db90cd29328b09c68a90e8d97f983173905555bb80b9d96c2902fd`
- artifact expiry: `2026-09-02`

The large proof remains in GitHub Actions artifacts rather than a permanent repository object or release asset. Its hashes and compact verification metadata are frozen here; durable long-term archival remains required.

## Status boundary

- frozen q00 CNF claim: proof-checked UNSAT
- legal q00 Borsuk case: `UNKNOWN`
- `n11-k6-full`: Gate 2; `MATHEMATICAL`; `[UNCHECKED]`; `OPEN`

## Required next mathematical step

Because `q00` is a universal trim rather than a legal diameter-6 set, proof-checked UNSAT must be refined exhaustively by compatible fifth bases or exact incompatibility branching. Only after those descendants are certificate-resolved may the q00 case ledger move to `UNSAT_REFINED`.
