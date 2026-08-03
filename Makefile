PYTHON ?= python

.PHONY: help status docs

help:
	@echo "Available targets:"
	@echo "  make status   Show the current top-level research package layout"
	@echo "  make docs     Show the documentation entry points"

status:
	$(PYTHON) scripts/repo_status.py

docs:
	@echo "Repository documentation:"
	@echo "  - docs/RESEARCH-ROADMAP.md"
	@echo "  - docs/VERIFICATION.md"
	@echo "  - docs/PROJECT-STATUS.md"
