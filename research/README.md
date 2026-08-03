# Research registry

`claims.json` is the machine-readable repository-level status ledger.

It records:

- the exact scope of each package claim;
- the allowed status of the claim;
- verification commands;
- known limitations and non-implications;
- dependencies between the active theorem target and supporting artifacts;
- whether repository summaries may describe the package result publicly within its limited scope.

This registry does not replace package-local proof notes or certificates. It prevents those artifacts from being summarized more strongly than their verified logical scope.

Validate it with:

```bash
python scripts/validate_claims.py
```

Any status change must be supported by new evidence and made in a reviewable branch. CI passing does not by itself justify changing `candidate-proof` to a settled theorem claim.
