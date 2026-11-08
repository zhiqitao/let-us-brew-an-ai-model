# The repository environment is .venv-311 (gitignored; `make setup` creates it —
# a clean clone ships no venv, so the bootstrap has to be documented + automated,
# round-2 R2-EX-N03). Every target prefers that interpreter when it exists, so
# `make setup && make test` works from a fresh clone.
VENV := .venv-311
PY311 := $(shell command -v python3.11 || echo python3.11)
PYTHON := $(shell if [ -x $(VENV)/bin/python ]; then echo $(VENV)/bin/python; else command -v python3 || echo python3; fi)

.PHONY: setup smoke test audit stage1 reproduce clean

setup:
	@if [ ! -x $(VENV)/bin/python ]; then echo "creating $(VENV) with $(PY311)"; $(PY311) -m venv $(VENV); fi
	$(VENV)/bin/pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-lock.txt
	$(VENV)/bin/pip install -e .
	$(VENV)/bin/pip install pytest

test:
	$(PYTHON) -m pytest tests/ -q

smoke:
	$(PYTHON) scripts/smoke_test.py

audit:
	$(PYTHON) scripts/audit.py

stage1:
	$(PYTHON) scripts/train.py --stage 1

reproduce:
	$(PYTHON) scripts/reproduce.py --dry-run

clean:
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null; true