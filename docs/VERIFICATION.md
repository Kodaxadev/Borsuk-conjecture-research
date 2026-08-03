# Verification guide

The repository is organized around independently checkable artifacts.

## Expected discipline

Each package should expose a minimal verification chain that can be re-run locally.

Typical evidence types include:

- Python verification scripts,
- Node.js independent checkers,
- SAT or DRAT/LRAT certificate verification,
- SHA256 manifests,
- witness and partial-coloring JSON artifacts.

## Verification policy

A claim should not be promoted to a final theorem statement without:

- a clearly documented theorem statement,
- an explicit reduction step,
- a reproducible verification recipe,
- and, where possible, an independent implementation of the verifier.
