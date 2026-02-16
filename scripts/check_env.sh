#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-core}"

# Resolve repo root
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "[INFO] Project root resolved to: ${ROOT}"

# Choose Python:
# - If VIRTUAL_ENV is active, use it.
# - Else if .venv exists, use it.
# - Else fall back to python3/python on PATH (CI).
PY=""
if [[ -n "${VIRTUAL_ENV:-}" ]] && [[ -x "${VIRTUAL_ENV}/bin/python" ]]; then
  PY="${VIRTUAL_ENV}/bin/python"
elif [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PY="$(command -v python)"
else
  echo "[FAIL] No python interpreter found on PATH and no active venv."
  exit 1
fi

echo "[OK]   Using Python: ${PY}"

# Basic version check for V1: >=3.11,<3.13
echo "[INFO] Checking Python version (V1 supports >=3.11,<3.13)"
PY_VER="$("${PY}" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
echo "[OK]   Python detected: ${PY_VER}"

"${PY}" - <<'PY'
import sys
v = sys.version_info
if not (v >= (3, 11) and v < (3, 13)):
    raise SystemExit(
        f"ERROR: V1 requires Python >=3.11,<3.13; got {sys.version.split()[0]}"
    )
PY
echo "[OK]   Python version satisfies V1 range"

failures=0
warnings=0

_fail() { echo "[FAIL] $*" >&2; failures=$((failures+1)); }
_warn() { echo "[WARN] $*" >&2; warnings=$((warnings+1)); }
_ok()   { echo "[OK]   $*"; }

if [[ "${MODE}" == "core" ]]; then
  echo "[INFO] Mode=core (V1): do not require OCR/LLM deps or env vars."
  echo "[INFO] Verifying dev gate tools exist (ruff, pytest, build)"

  # ruff is a CLI tool (not importable). Prefer CLI existence.
  if command -v ruff >/dev/null 2>&1; then
    _ok "ruff found: $(command -v ruff)"
  else
    _fail "ruff not found on PATH"
  fi

  if "${PY}" -m pytest --version >/dev/null 2>&1; then
    _ok "pytest importable via: ${PY} -m pytest"
  else
    _fail "pytest not available in selected interpreter (${PY})"
  fi

  if "${PY}" -m build --version >/dev/null 2>&1; then
    _ok "build importable via: ${PY} -m build"
  else
    _fail "build not available in selected interpreter (${PY})"
  fi

  echo "[INFO] ===== Environment Readiness Summary ====="
  echo "Mode:      core"
  echo "Failures:  ${failures}"
  echo "Warnings:  ${warnings}"
  echo

  if (( failures > 0 )); then
    echo "[FAIL] Environment NOT ready — resolve failures before proceeding"
    echo "[INFO] Fix (local): make install"
    echo "[INFO] Fix (CI):    python -m pip install -e '.[dev]'"
    exit 1
  fi

  echo "[OK] Environment ready (core)"
  exit 0
fi

# Non-core mode: local integration checks (optional / not required for OSS core).
echo "[INFO] Mode=${MODE}: local integration checks (NOT required for OSS core)"

check_env_var() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    _fail "${name} is not set"
  else
    _ok "${name} is set"
  fi
}

# These are placeholders for local/private integrations.
check_env_var "OBSIDIAN_VAULT_PATH"
check_env_var "LLM_ENDPOINT"
check_env_var "LLM_MODEL"

echo "[INFO] ===== Environment Readiness Summary ====="
echo "Mode:      ${MODE}"
echo "Failures:  ${failures}"
echo "Warnings:  ${warnings}"
echo

if (( failures > 0 )); then
  echo "[FAIL] Environment NOT ready — resolve failures before proceeding"
  exit 1
fi

echo "[OK] Environment ready (${MODE})"
