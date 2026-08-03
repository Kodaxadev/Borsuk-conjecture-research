# Borsuk Conjecture Research

This repository is the top-level research archive for the 0/1-Borsuk program centered on finite-combinatorial reductions, verifier artifacts, and independently checkable proof packages.

The project is intentionally organized as a collection of reproducible investigation units rather than a single monolithic build. Each subdirectory packages a specific mathematical claim, witness, obstruction, or independent reconstruction around a finite Borsuk instance.

## Research scope

The active work in this archive targets the combinatorial and SAT-based side of the 0/1-Borsuk problem, especially the finite reductions relevant to the $n=11$ and related diameter cases.

The repository currently contains the following major investigation packages:

- `borsuk_11_k4_candidate/` — candidate proof package for the diameter-4, dimension-11 case.
- `borsuk_11_k6_attack_surface/` — attack-surface reduction package that records a symmetry-broken finite attack instance.
- `borsuk_11_k6_trim_unsat_certificate/` — UNSAT-certificate-oriented artifact for the coarser trim instance.
- `borsuk_11_k8_candidate/` — independent candidate package for the diameter-8 case.
- `borsuk_n10_k4_reproduction/` — independent reconstruction of the $n=10, k=4$ result.
- `archive/` — historical or packaged artifacts retained for provenance.

## Project status

This repository should be treated as a research workspace and artifact registry rather than a finished theorem publication. The mathematical status of each package is documented in the package-local README files and proof notes.

## Repository conventions

- Every package should keep its own local `README.md`, verification instructions, and hash manifest.
- New mathematical claims should be recorded in a dedicated subdirectory with a minimal provenance trail.
- Reproducibility and independent checking are priority concerns.

## Documentation

- [docs/RESEARCH-ROADMAP.md](docs/RESEARCH-ROADMAP.md) — strategic plan for the project.
- [docs/VERIFICATION.md](docs/VERIFICATION.md) — cross-package verification expectations.
- [docs/PROJECT-STATUS.md](docs/PROJECT-STATUS.md) — living status ledger for the project.

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for the recommended workflow for adding new mathematical note packages, verification scripts, witnesses, or reproducibility data.

## Citation

If you use this repository as a research artifact, please cite the repository metadata in [CITATION.cff](CITATION.cff).

## License

This project is licensed under the MIT license. See [LICENSE](LICENSE).
