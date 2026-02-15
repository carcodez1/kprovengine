# =============================================================================
# kprovengine Makefile (OSS Core — Release Hardened)
#
# Contract:
# - Never installs into system Python.
# - Local venv only.
# - Supports Python 3.11 and 3.12 ONLY.
# - Deterministic failure modes and messaging.
# - CI parity via `make preflight`.
# =============================================================================

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:

# --- User Overrides (explicit only) ---
VENV ?= .venv
PYTHON_BOOTSTRAP ?= python3.12

# --- Derived Paths ---
PY := $(VENV)/bin/python
PIP := $(PY) -m pip

ARTIFACT_GUARD_SH := scripts/check_tracked_artifacts.sh
IDENTITY_GUARD_PY := scripts/check_project_identity.py

.PHONY: help env venv install lint test cov build artifacts identity precommit preflight clean distclean

help:
	@printf "%s\n" \
	"Targets:" \
	"  env         Show resolved configuration" \
	"  venv        Create local virtual environment + enforce python policy" \
	"  install     Install editable package + dev deps" \
	"  lint        Run ruff" \
	"  test        Run pytest" \
	"  cov         Run pytest with coverage reports" \
	"  build       Build sdist + wheel" \
	"  artifacts   Enforce artifact hygiene" \
	"  identity    Enforce project identity policy" \
	"  precommit   Run pre-commit on all files" \
	"  preflight   lint + test + build + artifacts + identity + precommit" \
	"  clean       Remove build/test artifacts" \
	"  distclean   Remove artifacts + venv"

env:
	@echo "PWD=$$(pwd)"
	@echo "VENV=$(VENV)"
	@echo "PYTHON_BOOTSTRAP=$(PYTHON_BOOTSTRAP)"
	@echo "PY=$(PY)"
	@echo "ARTIFACT_GUARD_SH=$(ARTIFACT_GUARD_SH)"
	@echo "IDENTITY_GUARD_PY=$(IDENTITY_GUARD_PY)"

# Internal: ensure bootstrap exists on PATH
define ASSERT_BOOTSTRAP
	command -v "$(PYTHON_BOOTSTRAP)" >/dev/null || ( \
		echo "ERROR: PYTHON_BOOTSTRAP not found: $(PYTHON_BOOTSTRAP)" >&2; \
		echo "Tip (macOS/Homebrew): brew install python@3.12" >&2; \
		exit 1; \
	)
endef

# Internal: ensure venv python exists
define ASSERT_VENV
	test -x "$(PY)" || ( \
		echo "ERROR: venv missing. Run: make venv" >&2; \
		exit 1; \
	)
endef

# Internal: enforce venv python version policy (NO HEREDOC)
# Note: this is a policy choice to avoid silent compatibility with unsupported Python versions.
# If we wanted to support more versions, we could relax this check and rely on classifiers and CI to enforce compatibility, but for now we want hard enforcement.
# Also note that this check is separate from ASSERT_VENV to ensure that we get a clear error message about missing venv vs unsupported python version.
define ASSERT_VENV_PY_POLICY
	$(call ASSERT_VENV)
	"$(PY)" -c 'import sys; maj, min = sys.version_info[:2]; \
allowed = ((3, 11), (3, 12)); \
if (maj, min) not in allowed: \
    raise SystemExit(f"ERROR: venv python must be 3.11 or 3.12; got {sys.version.split()[0]}")'
endef

venv:
	@$(call ASSERT_BOOTSTRAP)
	@if [ ! -x "$(PY)" ]; then \
		"$(PYTHON_BOOTSTRAP)" -m venv "$(VENV)"; \
	fi
	@$(call ASSERT_VENV_PY_POLICY)
	@$(PY) -V
	@$(PIP) --version

install: venv
	@$(PIP) install --upgrade pip
	@$(PIP) install -e ".[dev]"

lint: install
	@$(PY) -m ruff check .

test: install
	@$(PY) -m pytest -q

cov: install
	@$(PY) -m pytest -q \
		--cov=kprovengine \
		--cov-report=term-missing \
		--cov-report=xml \
		--cov-report=html

build: install
	@$(PY) -m build -q

artifacts:
	@test -f "$(ARTIFACT_GUARD_SH)" || (echo "ERROR: missing $(ARTIFACT_GUARD_SH)" >&2; exit 1)
	@bash "$(ARTIFACT_GUARD_SH)"

identity: venv
	@test -f "$(IDENTITY_GUARD_PY)" || (echo "ERROR: missing $(IDENTITY_GUARD_PY)" >&2; exit 1)
	@$(PY) "$(IDENTITY_GUARD_PY)"

precommit: install
	@$(PY) -m pre_commit run --all-files

preflight: lint test build artifacts identity precommit
	@echo "OK: preflight passed"

clean:
	@rm -rf .pytest_cache .ruff_cache htmlcov coverage.xml .coverage .coverage.* build dist *.egg-info

distclean: clean
	@rm -rf "$(VENV)"
