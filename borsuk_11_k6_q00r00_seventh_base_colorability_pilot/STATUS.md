# Status

- package claim: `n11-k6-q00r00-seventh-base-colorability-pilot`
- evidence state: `COMPUTATIONAL / DUAL_IMPLEMENTATION_REPRODUCED / CI_EXECUTION_COMPLETE / ARTIFACT_ARCHIVES_VERIFIED / EXECUTION_BOUND / REPOSITORY_GOVERNED / WORKING`
- governed source classification: `n11-k6-q00r00-seventh-base-classification`
- classification repository head: `865f6e99567ffe48d040e9de9693026a129a76ef`
- classification artifact SHA-256: `dece0e924900b2bd751a62e82edca7e59f55e0c58a5bf92c5b9b196755646352`

## Authoritative execution

- authoritative pilot implementation SHA: `8ef3163bb508d37f1adba5d246b1b0dd636b0778`
- workflow: `screen-q00r00-seventh-base-pilot` (workflow ID `326703705`)
- run ID: `30880666065`, attempt `1`, event `workflow_dispatch`
- branch: `research/q00r00-seventh-base-colorability-pilot`
- jobs: `17 / 17` successful (1 preparation, 15 case, 1 summarize)
- artifacts archived and verified: `17 / 17`
- inputs artifact ID: `8881165725`
- summary artifact ID: `8881190923`
- evidence: `evidence/run-30880666065/`

## Result partition

- `SAT_CHECKED_COLORING`: `15`
- `PROOF_CHECKED_UNSAT`: `0`
- `UNKNOWN`: `0`

## Closed grandchildren

All 15 transitioned `UNKNOWN` -> `12_COLORABLE` / `CLOSED_GRANDCHILD` on
evidence class `SAT_CHECKED_COLORING`:

- `q00r00-s026-t066`
- `q00r00-s028-t116`
- `q00r00-s028-t144`
- `q00r00-s028-t148`
- `q00r00-s028-t154`
- `q00r00-s030-t084`
- `q00r00-s030-t086`
- `q00r00-s031-t041`
- `q00r00-s033-t084`
- `q00r00-s034-t025`
- `q00r00-s034-t028`
- `q00r00-s034-t033`
- `q00r00-s034-t034`
- `q00r00-s034-t035`
- `q00r00-s035-t008`

## Frozen instance totals

- pilot cases: `15`
- generated trim vertices across cases: `2,840`
- distance-six edges across cases: `100,083`
- incompatible pairs across cases: `27,343`
- compact CNF variables across cases: `18,397`
- compact CNF clauses across cases: `403,257`

## Mathematical status

- certified eighth-base refinement cases: `0`
- incomplete pilot cases: `0`
- remaining nonpilot grandchildren: `4,461` `UNKNOWN`
- sixth-base parent closure count: `0`
- all sixth-base parents: `UNKNOWN`
- `q00r00`: `UNKNOWN`
- `q00`: `UNKNOWN`
- `n11-k6-full`: Gate 2 / `OPEN`

Affected but unresolved sixth-base parents: `q00r00-s026`, `q00r00-s028`,
`q00r00-s030`, `q00r00-s031`, `q00r00-s033`, `q00r00-s034`, `q00r00-s035`.

## Governance commits

- execution evidence commit: `7af760c34adf19c412e31258462c7b89cebee7bf`
- `EXECUTION_BINDING.json` SHA-256: `5c7c5538a59ff8a3a4b9cae25c06460589a56149cdb062c45393574972f635a0`
- governance binding commit: `d2fd7649c905e9d2f85e4b2090de1e0b94e36611`
- `GOVERNANCE_BINDING.json` SHA-256: `4ccb08542e1b1d40f1d96505f5db699695e09126006194083c8001f093bf72f9`
- aggregate archive manifest SHA-256: `dccd84c7a32e848004546c313ef11c54ae698ab7fd52cc3112efc53b74cbb33a`

## Deferred defect

Low severity, deferred: the binding host is Windows with git
`core.autocrlf=true`, which applies platform-default CRLF conversion to text
files on checkout. All checksum text files (`SHA256SUMS` and every
`<archive>.zip.sha256`) were written with explicit LF bytes and are committed as
LF blobs, and the 17 artifact ZIPs are binary and byte-identical to the
GitHub-produced archives. A Windows working-tree checkout may render the
checksum text files with CRLF, so a naive local `sha256sum -c` of those text
files can disagree while the committed blobs remain correct. No archive byte,
recorded digest, or mathematical conclusion is affected. No `.gitattributes`
normalization is added here because the governed commit scope is restricted to
execution archives, checksum files and the binding documents.

## Interpretation

Each of the 15 closed grandchildren is a complete seven-point universal trim
shown 12-colorable by a directly checked coloring, recomputed at binding time
from the raw solver assignment and rechecked across all 100,083 distance-six
edges with zero monochromatic edges and exactly 12 colors per case. Closing a
grandchild closes only that grandchild: every legal subset inside a 12-colorable
trim is 12-colorable, so no sixth-base parent, and therefore neither `q00r00`,
`q00`, nor `n11-k6-full`, changes status.

The pilot produced no `PROOF_CHECKED_UNSAT` case and therefore created no
certified eighth-base refinement frontier; eighth-base work is not authorized.
The next governed decision is to select a bounded seventh-base colorability
expansion from the remaining 4,461 `UNKNOWN` grandchildren.
