#!/usr/bin/env bash

# -----------------------------------------------------------------------------
# Bootstrap Script for SnapToTask
# -----------------------------------------------------------------------------
# This script sets up the local development environment:
#   - Python virtualenv
#   - Python dependencies
#   - Environment variables
#   - Vault directory
#   - Optional Docker/CICD checks
#
# Usage:
#   ./bootstrap.sh
#
# Requirements: bash, Python 3.11+, curl, docker (optional), docker compose (optional)
# -----------------------------------------------------------------------------

set -e
set -o pipefail

# -----------------------------------------------------------------------------
# Configurable Paths
# -----------------------------------------------------------------------------

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
VAULT_PATH="${HOME}/ObsidianVault"

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

function header() {
  printf "\n\n==========  %s  ==========\n\n" "$1"
}

function fail() {
  echo "ERROR: $1"
  exit 1
}

# -----------------------------------------------------------------------------
# 1) Validate Python
# -----------------------------------------------------------------------------

header "Checking Python 3.11+"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 not found in PATH. Please install Python 3.11+."
fi

PYTHON_VERSION="$(python3 -c 'import sys;print(sys.version_info[:2])' 2>&1)"

echo "Detected Python version: ${PYTHON_VERSION}"

if [[ ! "$(echo "$PYTHON_VERSION" | grep -E '3,[1-9]')" ]]; then
  fail "Python 3.11+ is required."
fi

# -----------------------------------------------------------------------------
# 2) Create Virtual Environment
# -----------------------------------------------------------------------------

header "Setting up Python virtual environment"

if [[ -d "$VENV_DIR" ]]; then
  echo "Virtual environment already exists at: $VENV_DIR"
else
  python3 -m venv "$VENV_DIR"
  echo "Created virtual environment at: $VENV_DIR"
fi

header "Activating virtual environment"

# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

# -----------------------------------------------------------------------------
# 3) Install Python Dependencies
# -----------------------------------------------------------------------------

header "Installing Python dependencies"

if [[ ! -f "${PROJECT_ROOT}/pyproject.toml" ]]; then
  fail "pyproject.toml not found at project root."
fi

pip install --upgrade pip
pip install -e ".[dev,vision]" || pip install -e ".[dev]"

echo "Python dependencies installed."

# -----------------------------------------------------------------------------
# 4) Setup Obsidian Vault
# -----------------------------------------------------------------------------

header "Ensuring Obsidian Vault exists at: $VAULT_PATH"

if [[ ! -d "$VAULT_PATH" ]]; then
  mkdir -p "$VAULT_PATH"
  echo "Created Obsidian Vault directory: $VAULT_PATH"
else
  echo "Obsidian vault directory already exists."
fi

# Write a vault environment file
ENV_FILE="${PROJECT_ROOT}/.env"
header "Writing environment file ($ENV_FILE)"

cat > "$ENV_FILE" <<EOF
# Obsidian vault
OBISIDIAN_VAULT_PATH="${VAULT_PATH}"

# Vision LLM
LLM_ENDPOINT="http://localhost:11434/api/chat"
LLM_MODEL="qwen2.5vl:3b"
EOF

echo "Environment variables written to .env"
echo "Load them with: source .env"

# -----------------------------------------------------------------------------
# 5) Validate Ollama
# -----------------------------------------------------------------------------

header "Checking Ollama local Vision LLM"

if ! command -v ollama >/dev/null 2>&1; then
  echo "WARNING: ollama not installed. Install via Homebrew or official sources."
  echo "Visit: https://ollama.com"
else
  echo "ollama found: $(ollama version)"
fi

# -----------------------------------------------------------------------------
# 6) Docker & Docker Compose Check
# -----------------------------------------------------------------------------

header "Checking Docker and Docker Compose"

if command -v docker >/dev/null 2>&1; then
  echo "Docker found: $(docker --version)"
else
  echo "Docker not found. Install Docker Desktop or equivalent."
fi

if docker compose version >/dev/null 2>&1; then
  echo "Docker Compose available."
else
  echo "Docker Compose is not available via 'docker compose'."
fi

# -----------------------------------------------------------------------------
# 7) Final Instructions
# -----------------------------------------------------------------------------

header "Bootstrap Complete"

echo "Next steps:"
echo "  1) Activate the virtual environment:"
echo "       source .venv/bin/activate"
echo "  2) Source your .env file:"
echo "       source .env"
echo "  3) Serve Ollama with:"
echo "       ollama pull qwen2.5vl"
echo "       ollama serve"
echo "  4) Run your MVP script:"
echo "       python3 mvp.py path/to/image.png"
echo ""
echo "If you prefer Docker:"
echo "       docker compose up --build"
echo ""
echo "Obsidian vault is mounted at: $VAULT_PATH"
echo "Modify your .env file as needed."

exit 0