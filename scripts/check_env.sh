#!/usr/bin/env bash
###############################################################################
# scripts/check_env.sh — Environment Readiness Validator for SnapToTask
#
# Verifies:
#   - Python (prefers project .venv if present) and minimum version
#   - Required Python packages importable
#   - Required environment variables present
#   - Obsidian vault directory exists (or optionally creates it)
#   - Ollama CLI present, endpoint reachable, model installed (exact match)
#   - Optional Docker / Docker Compose availability
#
# Usage:
#   source .env
#   bash scripts/check_env.sh
#
# Exit codes:
#   0 = ready (may include warnings)
#   1 = required failures present
#
# Optional env toggles:
#   CHECKENV_NO_COLOR=1        Disable ANSI color output
#   CHECKENV_CREATE_VAULT=1    Create OBISIDIAN_VAULT_PATH if missing
#   CHECKENV_STRICT=1          Treat warnings as failures
###############################################################################

set -o errexit
set -o pipefail
set -o nounset

# -----------------------------------------------------------------------------
# Output formatting
# -----------------------------------------------------------------------------
NO_COLOR="${CHECKENV_NO_COLOR:-0}"
if [[ "${NO_COLOR}" == "1" ]] || [[ ! -t 1 ]]; then
  RED='' GREEN='' YELLOW='' BLUE='' NC=''
else
  RED=$'\033[0;31m'
  GREEN=$'\033[0;32m'
  YELLOW=$'\033[1;33m'
  BLUE=$'\033[0;34m'
  NC=$'\033[0m'
fi

failures=0
warnings=0

info()    { printf "%s[INFO]%s %s\n" "${BLUE}" "${NC}" "$1"; }
ok()      { printf "%s[OK]%s   %s\n" "${GREEN}" "${NC}" "$1"; }
warn()    { printf "%s[WARN]%s %s\n" "${YELLOW}" "${NC}" "$1"; ((warnings++)) || true; }
fail()    { printf "%s[FAIL]%s %s\n" "${RED}" "${NC}" "$1"; ((failures++)) || true; }

# -----------------------------------------------------------------------------
# Resolve project root and preferred python
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
info "Project root resolved to: ${PROJECT_ROOT}"

# Prefer .venv python if present; fallback to python3 in PATH.
PYTHON="${PROJECT_ROOT}/.venv/bin/python3"
if [[ ! -x "${PYTHON}" ]]; then
  PYTHON="$(command -v python3 || true)"
fi

if [[ -z "${PYTHON}" ]] || [[ ! -x "${PYTHON}" ]]; then
  fail "python3 not found. Install Python 3.11+ and/or create .venv."
  PYTHON="python3" # keep going to report more failures where possible
else
  ok "Using Python: ${PYTHON}"
fi

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
python_version_tuple() {
  "${PYTHON}" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || echo "unknown"
}

python_version_ok() {
  "${PYTHON}" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
}

http_ok() {
  # args: url
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsS --max-time 2 "${url}" >/dev/null 2>&1
  elif command -v python3 >/dev/null 2>&1; then
    python3 - <<PY >/dev/null 2>&1
import urllib.request
urllib.request.urlopen("${url}", timeout=2).read()
PY
  else
    return 1
  fi
}

# -----------------------------------------------------------------------------
# Check Python version
# -----------------------------------------------------------------------------
info "Checking Python 3.11+ installation"
PY_VER="$(python_version_tuple)"
if [[ "${PY_VER}" == "unknown" ]]; then
  fail "Unable to determine Python version."
elif python_version_ok; then
  ok "Python 3.11+ available: ${PY_VER}"
else
  fail "Python 3.11+ required, found: ${PY_VER}"
fi

# -----------------------------------------------------------------------------
# Check Python packages (imports)
# -----------------------------------------------------------------------------
info "Verifying required Python packages"
REQUIRED_PKGS=(click easyocr rich requests)
MISSING_PKGS=()

for pkg in "${REQUIRED_PKGS[@]}"; do
  if ! "${PYTHON}" - <<PY >/dev/null 2>&1
try:
    import ${pkg}  # noqa: F401
except Exception:
    raise SystemExit(1)
PY
  then
    MISSING_PKGS+=("${pkg}")
  fi
done

if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
  fail "Missing Python packages (in ${PYTHON}): ${MISSING_PKGS[*]}"
  warn "Fix: activate venv and install deps: pip install -r requirements.txt"
else
  ok "All required Python packages installed"
fi

# -----------------------------------------------------------------------------
# Environment variables
# -----------------------------------------------------------------------------
info "Checking environment variables"
REQUIRED_VARS=(OBISIDIAN_VAULT_PATH LLM_ENDPOINT LLM_MODEL)

for var in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    fail "${var} is not set"
  else
    ok "${var} = ${!var}"
  fi
done

# -----------------------------------------------------------------------------
# Validate Obsidian vault directory
# -----------------------------------------------------------------------------
if [[ -n "${OBISIDIAN_VAULT_PATH:-}" ]]; then
  if [[ -d "${OBISIDIAN_VAULT_PATH}" ]]; then
    ok "Vault directory exists at: ${OBISIDIAN_VAULT_PATH}"
  else
    if [[ "${CHECKENV_CREATE_VAULT:-0}" == "1" ]]; then
      mkdir -p "${OBISIDIAN_VAULT_PATH}" && ok "Created vault directory at: ${OBISIDIAN_VAULT_PATH}" \
        || fail "Failed to create vault directory: ${OBISIDIAN_VAULT_PATH}"
    else
      fail "Vault directory not found: ${OBISIDIAN_VAULT_PATH}"
      warn "Fix: mkdir -p \"${OBISIDIAN_VAULT_PATH}\" (or set CHECKENV_CREATE_VAULT=1)"
    fi
  fi
fi

# -----------------------------------------------------------------------------
# Validate Ollama CLI, endpoint, and model
# -----------------------------------------------------------------------------
info "Checking Ollama CLI"
if ! command -v ollama >/dev/null 2>&1; then
  fail "ollama CLI not available in PATH"
  warn "Install: https://ollama.com (or use Docker Compose ollama service)"
else
  ok "ollama CLI detected"

  # Endpoint reachability (best-effort)
  if [[ -n "${LLM_ENDPOINT:-}" ]]; then
    # Derive a base host URL for a lightweight check
    # If endpoint is .../api/chat, base is scheme://host:port
    BASE_URL="${LLM_ENDPOINT%/api/chat}"
    if http_ok "${BASE_URL}"; then
      ok "LLM endpoint reachable: ${BASE_URL}"
    else
      warn "LLM endpoint not reachable: ${BASE_URL}"
      warn "If running locally: ensure 'ollama serve' is running."
    fi
  fi

  # Exact model match check
  if [[ -n "${LLM_MODEL:-}" ]]; then
    info "Checking local Vision LLM model: ${LLM_MODEL}"
    if ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -Fxq "${LLM_MODEL}"; then
      ok "Vision LLM model available: ${LLM_MODEL}"
    else
      warn "Vision LLM model not found: ${LLM_MODEL}"
      warn "Installed models:"
      ollama list 2>/dev/null || true
      warn "Fix: ollama pull ${LLM_MODEL}"
    fi
  fi
fi

# -----------------------------------------------------------------------------
# Optional: Docker + Docker Compose
# -----------------------------------------------------------------------------
info "Checking Docker installation"
if command -v docker >/dev/null 2>&1; then
  ok "Docker available ($(docker --version 2>/dev/null || echo "unknown version"))"
else
  warn "Docker not installed"
fi

info "Checking Docker Compose"
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  ok "Docker Compose available"
else
  warn "Docker Compose not available via 'docker compose'"
fi

# -----------------------------------------------------------------------------
# Final Summary
# -----------------------------------------------------------------------------
echo ""
info "===== Environment Readiness Summary ====="
printf "Failures:  %s\n" "${failures}"
printf "Warnings:  %s\n" "${warnings}"
echo ""

STRICT="${CHECKENV_STRICT:-0}"
if [[ "${failures}" -gt 0 ]]; then
  fail "Environment NOT ready — resolve failures before proceeding"
  exit 1
fi

if [[ "${STRICT}" == "1" && "${warnings}" -gt 0 ]]; then
  fail "Environment NOT ready (strict mode) — resolve warnings"
  exit 1
fi

if [[ "${warnings}" -gt 0 ]]; then
  warn "Environment ready with warnings"
  exit 0
fi

ok "Environment is ready"
exit 0