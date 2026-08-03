PYTHON ?= python
NODE ?= node

.PHONY: help status validate verify verify-fast verify-k6-certificate docs

help:
	@echo "Available targets:"
	@echo "  make status                Show the machine-readable research status"
	@echo "  make validate              Validate the claim registry and package links"
	@echo "  make verify                Run all lightweight independent verifiers"
	@echo "  make verify-k6-certificate Recheck the stored k=6 DRUP certificate"
	@echo "  make docs                  Show the documentation entry points"

status:
	$(PYTHON) scripts/repo_status.py

validate:
	$(PYTHON) scripts/validate_claims.py

verify: verify-fast

verify-fast: validate
	cd borsuk_n10_k4_reproduction && $(PYTHON) reproduce_n10_k4.py
	cd borsuk_11_k4_candidate && $(PYTHON) verify.py
	cd borsuk_11_k4_candidate && $(NODE) verify_independent.js
	cd borsuk_11_k8_candidate && $(PYTHON) verify.py
	cd borsuk_11_k8_candidate && $(NODE) verify_independent.js
	cd borsuk_11_k6_attack_surface && $(PYTHON) verify_structure.py
	cd borsuk_11_k6_attack_surface && $(NODE) verify_independent.js
	cd borsuk_11_k6_attack_surface && sha256sum -c SHA256SUMS
	cd borsuk_11_k6_branch_search && $(PYTHON) generate_root.py
	cd borsuk_11_k6_branch_search && $(NODE) verify_root_independent.js
	cd borsuk_11_k6_branch_search && $(PYTHON) verify_manifest.py
	cd borsuk_11_k6_four_base_reduction && $(PYTHON) generate_cases.py
	cd borsuk_11_k6_four_base_reduction && $(NODE) verify_independent.js

verify-k6-certificate:
	@set -eu; \
	tmpdir="$$(mktemp -d)"; \
	trap 'rm -rf "$$tmpdir"' EXIT; \
	g++ -O3 -std=c++17 borsuk_11_k6_trim_unsat_certificate/drup_check.cpp -o "$$tmpdir/drup_check"; \
	gzip -dc borsuk_11_k6_trim_unsat_certificate/k6_trim_12color.drat.gz > "$$tmpdir/proof.drat"; \
	"$$tmpdir/drup_check" \
	  borsuk_11_k6_trim_unsat_certificate/k6_trim_12color.cnf \
	  "$$tmpdir/proof.drat"

docs:
	@echo "Repository documentation:"
	@echo "  - AGENTS.md"
	@echo "  - research/claims.json"
	@echo "  - docs/RESEARCH-ROADMAP.md"
	@echo "  - docs/VERIFICATION.md"
	@echo "  - docs/PROJECT-STATUS.md"
	@echo "  - docs/K6-EXECUTION-PLAN.md"
