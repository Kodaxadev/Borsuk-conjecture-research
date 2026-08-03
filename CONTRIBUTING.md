# Contributing to Borsuk Conjecture Research

This repository is a mathematical research archive. Contributions should preserve clarity, reproducibility, and independent auditability.

## Contribution expectations

Please make sure each contribution:

- is accompanied by an explanation of the mathematical context,
- has a clear status label (candidate, reproduction, attack surface, or certificate),
- includes verification instructions or a clear script entry point,
- preserves provenance information for any generated witness files or solver output.

## Preferred workflow

1. Create or extend a package-specific subdirectory.
2. Add or update a local `README.md` in the package.
3. Include reproducibility details and any expected command-line checks.
4. If the package represents a new theorem claim, document the assumptions and the scope of the claim explicitly.
5. Provide a hash manifest or a verification recipe where possible.

## Review norms

Research changes should be reviewed for:

- correctness of the underlying statement,
- mathematical scope and limitations,
- reproducibility of the verification path,
- clarity around what is proven versus what remains conjectural.

## Documentation style

Prefer precise mathematical language over informal summaries. Keep explicit notes on unresolved edges, limitations, and known attack surfaces.

## Pull requests

A pull request should explain:

- the research question being addressed,
- the artifact or proof package being added or updated,
- the verification commands that were run,
- the interpretation of the evidence.
