# q00 certificate lane

## Purpose

This lane attempts one narrowly scoped result: produce a proof trace for the frozen compact `q00` CNF and independently check that trace.

It does not update `case_status.json`, `research/claims.json`, or `cruthunas/ledger.json`.

## Frozen instance

- case: `q00`
- encoding: `compact-list-color-v2`
- CNF SHA-256: `36da8f78ae376b370f119d1fa16a58f6504607d949ac8315648fdbda52450299`
- variable-map SHA-256: `5f94c619b6a5996c54f269a88de5bfaff042e4c855ea8543869b84009c7dae45`
- variables: 2,724
- clauses: 130,840

## Pinned tools

- Kissat 4.0.0, source archive MD5 `89801fadc6d7a2ee1519a9cccf0c9029`
- DRAT-trim commit `effa1dcce85c878236f8313133dff1a2b766cd7c`

Kissat writes its default binary DRAT trace. DRAT-trim is invoked with binary parsing forced by `-i`.

## Acceptance boundary

A successful workflow artifact must contain:

- the exact CNF and variable map;
- a nonempty binary DRAT proof;
- solver version, binary hash, output, and exit status 20;
- checker source revision, binary hash, output, and exit status 0;
- checker output reporting verification;
- a manifest with hashes for every central artifact.

Even then, the artifact is labeled `CERTIFICATE_CANDIDATE_NOT_REGISTERED_EVIDENCE`. It must be reviewed and registered as typed Cruthúnas evidence before any governed status change is considered.

A checked UNSAT result would still close no theorem branch by itself. The `q00` trim may contain incompatible vertex pairs, so the case must be refined by a fifth compatible base or an exhaustive incompatibility branch.

## Failure boundary

Timeout, missing proof, checker timeout, checker rejection, artifact loss, or hash mismatch leaves `q00` as `UNKNOWN` and changes no claim state.
