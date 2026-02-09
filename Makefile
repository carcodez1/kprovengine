# KProvEngine Makefile (V1 LOCKED)
# macOS (Apple Silicon) + Homebrew Python. Local venv only. No system installs.

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

VENV := .venv
PYTHON_BOOTSTRAP ?= /opt/homebrew/opt/python@3.12/bin/python3.12

PY := $(VENV)/bin/python
PIP := $(PY) -m pip

.PHONY: help env venv install lint test cov build preflight clean distclean

help:
	@echo "Targets:"
	@echo "  make venv        Create venv (uses PYTHON_BOOTSTRAP if missing)"
	@echo "  make install     Install editable + dev deps into venv"
	@echo "  make lint        Run ruff"
	@echo "  make test        Run pytest"
	@echo "  make cov         Run pytest with coverage (term + xml + html)"
	@echo "  make build       Build sdist + wheel"
	@echo "  make preflight   lint + test + build"
	@echo "  make clean       Remove build/test artifacts"
	@echo "  make distclean   clean + remove venv"

env:
	@echo "PYTHON_BOOTSTRAP=$(PYTHON_BOOTSTRAP)"
	@test -x "$(PYTHON_BOOTSTRAP)" || (echo "ERROR: PYTHON_BOOTSTRAP not found: $(PYTHON_BOOTSTRAP)"; exit 1)
	@echo "VENV=$(VENV)"
	@echo "PY=$(PY)"

venv:
	@if [ ! -x "$(PY)" ]; then \
		test -x "$(PYTHON_BOOTSTRAP)" || (echo "ERROR: PYTHON_BOOTSTRAP not found: $(PYTHON_BOOTSTRAP)"; exit 1); \
		"$(PYTHON_BOOTSTRAP)" -m venv "$(VENV)"; \
	fi
	@$(PY) -V
	@$(PIP) --version

install: venv
	@$(PIP) install -U pip
	@$(PIP) install -e ".[dev]"

lint: install
	@$(PY) -m ruff check .

test: install
	@$(PY) -m pytest -q

cov: install
	@$(PY) -m pytest -q --cov=kprovengine --cov-report=term-missing --cov-report=xml --cov-report=html

build: install
	@$(PY) -m build -q

preflight: lint test build
	@echo "OK: preflight passed"

clean:
	@rm -rf .pytest_cache .ruff_cache htmlcov coverage.xml .coverage .coverage.* build dist *.egg-info

distclean: clean
	@rm -rf "$(VENV)"