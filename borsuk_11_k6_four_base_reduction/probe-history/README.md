# Solver probe history

This directory records bounded exploratory runs that produced no certificate-backed status change.

Probe records are operational history, not mathematical evidence. They may be used to avoid duplicate runs and to schedule different solvers, encodings, or limits.

Rules:

- `UNKNOWN` remains `UNKNOWN` regardless of conflict count or elapsed time.
- Partial proof traces from interrupted runs are not proof certificates.
- Probe records must state `repository_status_changed: false`.
- A later SAT model or checked UNSAT proof must be stored through the result workflow and independently verified before changing `case_status.json`.
- Cruthúnas evidence and ledger state are not changed by files in this directory.
