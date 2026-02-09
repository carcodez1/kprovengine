#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-core}"

# Resolve repo root
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "[INFO] Project root resolved to: ${ROOT}"

# Choose Python:
# - If VIRTUAL_ENV is active, use its python.
# - Else if .venv exists, use it (local developer convenience).
# - Else fall back to python on PATH (CI).
PY=""
if [[ -n "${VIRTUAL_ENV:-}" ]] && [[ -x "${VIRTUAL_ENV}/bin/python" ]]; then
  PY="${VIRTUAL_ENV}/bin/python"
elif [[ -x "${ROOT}/.venv/bin/python3" ]]; then
  PY="${ROOT}/.venv/bin/python3"
elif command -v python >/dev/null 2>&1; then
  PY="$(command -v python)"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
else
  echo "[FAIL] No python interpreter found."
  exit 1
fi

echo "[OK]   Using Python: ${PY}"

# Basic version check for V1: >=3.11,<3.13
echo "[INFO] Checking Python version (V1 supports >=3.11,<3.13)"
PY_VER="$("${PY}" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
echo "[OK]   Python detected: ${PY_VER}"

# Compare versions in Python (robust)
"${PY}" - <<'PY'
import sys
v = sys.version_info
if not (v >= (3, 11) and v < (3, 13)):
    raise SystemExit(1)
PY
echo "[OK]   Python version satisfies V1 range"

if [[ "${MODE}" == "core" ]]; then
  echo "[INFO] Mode=core (V1): do not require OCR/LLM deps or env vars."
  echo "[INFO] Verifying dev gate tools exist (ruff, pytest, build)"

  missing=()
  "${PY}" -c "import ruff" 2>/dev/null || missing+=("ruff")
  "${PY}" -c "import pytest" 2>/dev/null || missing+=("pytest")
  "${PY}" -c "import build" 2>/dev/null || missing+=("build")

  if (( ${#missing[@]} > 0 )); then
    echo "[FAIL] Missing dev tools in ${PY} (${missing[*]})."
    echo "[WARN] Fix (local): make install"
    echo "[WARN] Fix (CI): python -m pip install -e '.[dev]'"
    echo "[INFO] ===== Environment Readiness Summary ====="
    echo "Mode:      core"
    echo "Failures:  1"
    echo "Warnings:  0"
    echo
    echo "[FAIL] Environment NOT ready — resolve failures before proceeding"
    exit 1
  fi

  echo "[OK]   Dev gate tools present"
  echo "[INFO] ===== Environment Readiness Summary ====="
  echo "Mode:      core"
  echo "Failures:  0"
  echo "Warnings:  0"
  echo
  echo "[OK] Environment ready (core)"
  exit 0
fi

# Non-core mode (full) can be stricter; keep it V2+/local only.
echo "[INFO] Mode=${MODE}: full checks (local/dev only)"
failures=0

check_env_var() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "[FAIL] ${name} is not set"
    failures=$((failures+1))
  else
    echo "[OK]   ${name} is set"
  fi
}

check_env_var "OBISIDIAN_VAULT_PATH"
check_env_var "LLM_ENDPOINT"
check_env_var "LLM_MODEL"

if (( failures > 0 )); then
  echo "[INFO] ===== Environment Readiness Summary ====="
  echo "Mode:      ${MODE}"
  echo "Failures:  ${failures}"
  echo "Warnings:  0"
  echo
  echo "[FAIL] Environment NOT ready — resolve failures before proceeding"
  exit 1
fi

echo "[INFO] ===== Environment Readiness Summary ====="
echo "Mode:      ${MODE}"
echo "Failures:  0"
echo "Warnings:  0"
echo
echo "[OK] Environment ready (${MODE})"
