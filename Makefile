PYTHON := $(shell command -v python3 || echo python3)

.PHONY: setup smoke test audit stage1 reproduce clean

setup:
	$(PYTHON) -m pip install -e .
	$(PYTHON) -m pip install pytest

test:
	$(PYTHON) -m pytest tests/ -q

smoke:
	$(PYTHON) scripts/smoke_test.py

audit:
	$(PYTHON) scripts/audit.py

stage1:
	$(PYTHON) scripts/train.py --stage 1

reproduce:
	$(PYTHON) scripts/reproduce.py

clean:
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null; true
