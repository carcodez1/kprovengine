# ======================================================================
# FILE: Makefile
# PROJECT: kprovengine (OSS core)
# PURPOSE: Deterministic local gates mirroring CI: lint/test/build + hygiene
# TRACEABILITY:
#   - Governance: OSS_GOVERNANCE.md (CI and merge requirements, determinism)
#   - CI: .github/workflows/ci.yml
# VERSION: V1-LOCKED
# LAST-UPDATED: 2026-02-15
# ======================================================================

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:

# ---- User-configurable knobs (override: make VENV=.venv PYTHON_BOOTSTRAP=python3.12) ----
VENV ?= .venv
PYTHON_BOOTSTRAP ?= python3.12

# ---- Derived ----
PY := $(VENV)/bin/python
PIP := $(PY) -m pip

# ---- Policy ----
SUPPORTED_PY_MIN ?= 3.11
SUPPORTED_PY_MAX ?= 3.12

# ---- Gates (SSOT names) ----
ARTIFACT_GUARD_SH := scripts/check_tracked_artifacts.sh
IDENTITY_GUARD_PY := scripts/check_project_identity.py
VENV_POLICY_PY    := scripts/check_venv_python.py

.PHONY: help env venv install lint test cov build artifacts identity venv-policy precommit preflight clean distclean

help:
	@printf "%s\n" \
	"Targets:" \
	"  env            Show resolved toolchain variables" \
	"  venv           Create venv using PYTHON_BOOTSTRAP (no system install)" \
	"  install        Install editable package + dev deps into venv" \
	"  lint           Run ruff (no auto-fix)" \
	"  test           Run pytest" \
	"  cov            Run pytest with coverage outputs" \
	"  build          Build sdist + wheel" \
	"  artifacts      Fail if forbidden artifacts are tracked" \
	"  identity       Fail if project identity drift is detected" \
	"  precommit      Run pre-commit on all files (in venv)" \
	"  preflight      lint + test + build + artifacts + identity + precommit" \
	"  clean          Remove build/test artifacts (keeps venv)" \
	"  distclean      clean + remove venv" \
	"" \
	"Variables (override):" \
	"  VENV=.venv" \
	"  PYTHON_BOOTSTRAP=python3.12"

env:
	@echo "PWD=$$(pwd)"
	@echo "VENV=$(VENV)"
	@echo "PYTHON_BOOTSTRAP=$(PYTHON_BOOTSTRAP)"
	@echo "PY=$(PY)"
	@echo "SUPPORTED_PY=$(SUPPORTED_PY_MIN)..$(SUPPORTED_PY_MAX)"
	@echo "ARTIFACT_GUARD_SH=$(ARTIFACT_GUARD_SH)"
	@echo "IDENTITY_GUARD_PY=$(IDENTITY_GUARD_PY)"
	@echo "VENV_POLICY_PY=$(VENV_POLICY_PY)"

# Internal: ensure bootstrap exists on PATH
define ASSERT_BOOTSTRAP
	command -v "$(PYTHON_BOOTSTRAP)" >/dev/null 2>&1 || ( \
		echo "ERROR: PYTHON_BOOTSTRAP not found on PATH: $(PYTHON_BOOTSTRAP)" >&2; \
		echo "Tip (macOS/Homebrew): brew install python@3.12 && export PYTHON_BOOTSTRAP=/opt/homebrew/opt/python@3.12/bin/python3.12" >&2; \
		exit 1; \
	)
endef

# Internal: ensure venv python exists
define ASSERT_VENV
	test -x "$(PY)" || (echo "ERROR: venv missing. Run: make venv" >&2; exit 1)
endef

venv:
	@$(call ASSERT_BOOTSTRAP)
	@if [ ! -x "$(PY)" ]; then \
		"$(PYTHON_BOOTSTRAP)" -m venv "$(VENV)"; \
	fi
	@$(call ASSERT_VENV)
	@$(PY) -V
	@$(PIP) --version
	@$(MAKE) venv-policy

# Enforce venv python policy using a dedicated script (avoids Make heredoc hazards)
venv-policy:
	@$(call ASSERT_VENV)
	@test -f "$(VENV_POLICY_PY)" || (echo "ERROR: missing $(VENV_POLICY_PY)" >&2; exit 1)
	@$(PY) "$(VENV_POLICY_PY)" --min "$(SUPPORTED_PY_MIN)" --max "$(SUPPORTED_PY_MAX)"

install: venv
	@$(PIP) install -U pip
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

# ======================================================================
# END OF FILE
# ======================================================================
