# q00 compact-trim UNSAT certificate

## Exact scoped claim

The deterministic compact list-coloring CNF for canonical four-base trim type `q00` is UNSAT.

This is a certificate for the **universal trim cover only**. The trim can contain pairs at Hamming distance greater than 6, so this result does not settle the legal `n=11, k=6` Boolean-cube Borsuk subcase and does not by itself change `case_status.json`.

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
- proof SHA-256: `59bf62a00d0c63b5ced7967c33421d953af5b96e423cc93dc862e595d08561b5`
- checker: `drat-trim`
- checker revision: `2e3b2dc0ecf938addbd779d42877b6ed69d9a985`
- checker binary SHA-256: `92f0aa9575ed519d66a99b8b1b3dde6ece4618ae4c202a3a4b200265dda0aa7a`
- positive verdict: `s VERIFIED`

The negative control changed the first binary DRAT operation byte from valid addition byte `0x61` to invalid byte `0x62`. The same pinned checker rejected the corrupted proof with exit status 1.

## Artifact chain

Proof-producing run:

- workflow run ID: `30822622138`
- artifact ID: `8859778824`
- artifact digest: `sha256:e75f4a6571a22bef7f686ec6f91037f17598fecf19872d1c085113f706be2351`

Final compact bundle:

- workflow run ID: `30827345819`
- certificate artifact ID: `8861415369`
- certificate artifact digest: `sha256:3131aacfd28b3959b1205067c6cff2dd34403fa4029bb70702ffc63b2a2e0a54`
- metadata artifact ID: `8861414746`
- metadata artifact digest: `sha256:16e5510f997d21380653b641e6e02a62e13e5bf0ec769b43e9446463bc87faa9`
- artifact expiry: `2026-11-01`

The proof bundle is currently retained as a GitHub Actions artifact rather than a permanent repository object or release asset. Its hashes and verification metadata are frozen here; durable long-term archival remains required.

## Required next mathematical step

Because `q00` is a universal trim rather than a legal diameter-6 set, proof-checked UNSAT must be refined exhaustively by compatible fifth bases or exact incompatibility branching. Only after those descendants are certificate-resolved may the q00 case ledger move to `UNSAT_REFINED`.
