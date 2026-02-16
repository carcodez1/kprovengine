# ======================================================================
# FILE: Makefile
# PROJECT: kprovengine (OSS core)
# PURPOSE: Deterministic local gates mirroring CI: lint/test/build + hygiene
# TRACEABILITY:
#   - Governance: OSS_GOVERNANCE.md
#   - CI: .github/workflows/ci.yml
# VERSION: V1-LOCKED
# LAST-UPDATED: 2026-02-16
# ======================================================================

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:

VENV ?= .venv

# Prefer python3.12; allow override (bootstrap ONLY).
PYTHON_BOOTSTRAP ?= python3.12

PY := $(VENV)/bin/python
PIP := $(PY) -m pip

# Policy (unambiguous): supported is >=MIN and <MAX_EXCL
SUPPORTED_PY_MIN ?= 3.11
SUPPORTED_PY_MAX_EXCL ?= 3.13

ARTIFACT_GUARD_SH := scripts/check_tracked_artifacts.sh
IDENTITY_GUARD_PY := scripts/check_project_identity.py
VENV_POLICY_PY    := scripts/check_venv_python.py
SBOM_SH           := scripts/sbom.sh
SIGN_SH           := scripts/sign.sh
ATTEST_SH         := scripts/attest.sh
DOCTOR_SH         := scripts/doctor.sh

DIST_DIR ?= dist

# Coverage policy: fail hard if below threshold
COV_FAIL_UNDER ?= 85

.PHONY: help env venv venv-policy install lint test cov build sbom sign attest \
        artifacts identity precommit tox preflight doctor docker-local \
        clean distclean all verify-tools

help:
	@printf "%s\n" \
	"Targets:" \
	"  env            Show resolved toolchain variables" \
	"  venv           Create venv using PYTHON_BOOTSTRAP" \
	"  venv-policy    Enforce python version policy inside venv" \
	"  install        Install editable package + dev deps into venv" \
	"  lint           Run ruff (no auto-fix)" \
	"  test           Run pytest (no coverage)" \
	"  cov            Run pytest with coverage XML+HTML (fails under COV_FAIL_UNDER)" \
	"  build          Build sdist + wheel (dist/)" \
	"  sbom           Generate SBOMs for dist artifacts" \
	"  sign           Cosign keyless sign dist artifacts (writes *.sig/*.crt)" \
	"  attest         Local policy gate for attest/sign/SBOM outputs" \
	"  artifacts      Fail if forbidden artifacts are tracked" \
	"  identity       Fail if project identity drift is detected" \
	"  precommit      Run pre-commit on all files (in venv)" \
	"  tox            Run tox via venv (py311/py312/lint matrix)" \
	"  doctor         Environment + build + sbom smoke checks" \
	"  preflight      lint + cov + build + sbom + sign + attest + artifacts + identity + precommit" \
	"  docker-local   Build local OCI image tag kprovengine:local" \
	"  clean          Remove build/test artifacts (keeps venv)" \
	"  distclean      clean + remove venv" \
	"  all            Alias for preflight" \
	"" \
	"Variables (override):" \
	"  VENV=.venv" \
	"  PYTHON_BOOTSTRAP=python3.12" \
	"  SUPPORTED_PY_MIN=3.11" \
	"  SUPPORTED_PY_MAX_EXCL=3.13" \
	"  DIST_DIR=dist" \
	"  COV_FAIL_UNDER=85"

env:
	@echo "PWD=$$(pwd)"
	@echo "VENV=$(VENV)"
	@echo "PYTHON_BOOTSTRAP=$(PYTHON_BOOTSTRAP)"
	@echo "PY=$(PY)"
	@echo "SUPPORTED_PY_MIN=$(SUPPORTED_PY_MIN)"
	@echo "SUPPORTED_PY_MAX_EXCL=$(SUPPORTED_PY_MAX_EXCL)"
	@echo "DIST_DIR=$(DIST_DIR)"
	@echo "COV_FAIL_UNDER=$(COV_FAIL_UNDER)"
	@echo "ARTIFACT_GUARD_SH=$(ARTIFACT_GUARD_SH)"
	@echo "IDENTITY_GUARD_PY=$(IDENTITY_GUARD_PY)"
	@echo "VENV_POLICY_PY=$(VENV_POLICY_PY)"
	@echo "SBOM_SH=$(SBOM_SH)"
	@echo "SIGN_SH=$(SIGN_SH)"
	@echo "ATTEST_SH=$(ATTEST_SH)"
	@echo "DOCTOR_SH=$(DOCTOR_SH)"

define ASSERT_BOOTSTRAP
	command -v "$(PYTHON_BOOTSTRAP)" >/dev/null 2>&1 || ( \
		echo "ERROR: PYTHON_BOOTSTRAP not found on PATH: $(PYTHON_BOOTSTRAP)" >&2; \
		echo "Tip (macOS/Homebrew): brew install python@3.12 && export PYTHON_BOOTSTRAP=/opt/homebrew/opt/python@3.12/bin/python3.12" >&2; \
		exit 1; \
	)
endef

define ASSERT_VENV
	test -x "$(PY)" || (echo "ERROR: venv missing. Run: make venv" >&2; exit 1)
endef

define ASSERT_FILE
	test -f "$(1)" || (echo "ERROR: missing $(1)" >&2; exit 1)
endef

verify-tools: venv
	@# Never rely on global python; enforce venv python only.
	@$(call ASSERT_VENV)
	@$(PY) -V
	@$(PIP) --version
	@# Optional external tools (scripts should also gate internally)
	@command -v bash >/dev/null 2>&1 || (echo "ERROR: bash missing" >&2; exit 1)
	@echo "OK: tool resolution looks sane"

venv:
	@$(call ASSERT_BOOTSTRAP)
	@if [ ! -x "$(PY)" ]; then \
		"$(PYTHON_BOOTSTRAP)" -m venv "$(VENV)"; \
	fi
	@$(call ASSERT_VENV)
	@$(PY) -V
	@$(PIP) --version
	@$(MAKE) venv-policy

venv-policy:
	@$(call ASSERT_VENV)
	@$(call ASSERT_FILE,$(VENV_POLICY_PY))
	@$(PY) "$(VENV_POLICY_PY)" --min "$(SUPPORTED_PY_MIN)" --max-excl "$(SUPPORTED_PY_MAX_EXCL)"

install: venv
	@$(PIP) install -U pip
	@$(PIP) install -e ".[dev]"

lint: install
	@$(PY) -m ruff check .

test: install
	@$(PY) -m pytest -q

cov: install
	@# Fail hard if coverage < COV_FAIL_UNDER; emit XML+HTML deterministically.
	@$(PY) -m pytest -q \
		--cov=kprovengine \
		--cov-report=term-missing \
		--cov-report=xml:coverage.xml \
		--cov-report=html:htmlcov \
		--cov-fail-under="$(COV_FAIL_UNDER)"

build: install
	@rm -rf "$(DIST_DIR)"
	@$(PY) -m build -q

sbom: build
	@$(call ASSERT_FILE,$(SBOM_SH))
	@bash "$(SBOM_SH)"

sign: sbom
	@$(call ASSERT_FILE,$(SIGN_SH))
	@bash "$(SIGN_SH)" "$(DIST_DIR)"

attest: sign
	@$(call ASSERT_FILE,$(ATTEST_SH))
	@bash "$(ATTEST_SH)" "$(DIST_DIR)"

artifacts:
	@$(call ASSERT_FILE,$(ARTIFACT_GUARD_SH))
	@bash "$(ARTIFACT_GUARD_SH)"

identity: venv
	@$(call ASSERT_FILE,$(IDENTITY_GUARD_PY))
	@$(PY) "$(IDENTITY_GUARD_PY)"

precommit: install
	@$(PY) -m pre_commit run --all-files

tox: install
	@$(PY) -m tox

doctor: verify-tools
	@$(call ASSERT_FILE,$(DOCTOR_SH))
	@bash "$(DOCTOR_SH)"

preflight: lint cov build sbom sign attest artifacts identity precommit
	@echo "OK: preflight passed"

docker-local:
	@docker build -t kprovengine:local .

clean:
	@rm -rf .pytest_cache .ruff_cache htmlcov coverage.xml .coverage .coverage.* build dist *.egg-info

distclean: clean
	@rm -rf "$(VENV)"

all: preflight

# ======================================================================
# END OF FILE
# ======================================================================
