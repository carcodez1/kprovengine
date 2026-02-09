#!/usr/bin/env bash
set -euo pipefail

# Fail if common sensitive / generated artifacts are tracked by git.
# This checks the *index* (tracked files), not the working tree.

fail=0

deny_patterns=(
  '^\.venv/'
  '^venv/'
  '^\.env$'
  '^\.env\..+'
  '^runs/'
  '^state/'
  '^vault/'
  '^output/'
  '^tmp/'
  '^dist/'
  '^build/'
  '.*\.egg-info/'
  '.*__pycache__/'
  '.*\.pyc$'
  '^\.pytest_cache/'
  '^\.ruff_cache/'
  '^\.mypy_cache/'
  '^\.DS_Store$'
)

allow_patterns=(
  '^\.env\.example$'
)

tracked="$(git ls-files)"

# Allowlist check helper
is_allowed() {
  local f="$1"
  for ap in "${allow_patterns[@]}"; do
    if [[ "$f" =~ $ap ]]; then
      return 0
    fi
  done
  return 1
}

echo "artifact-guard: scanning tracked files..."

while IFS= read -r f; do
  for dp in "${deny_patterns[@]}"; do
    if [[ "$f" =~ $dp ]]; then
      if is_allowed "$f"; then
        continue
      fi
      echo "ERROR: forbidden tracked file: $f (matched: $dp)"
      fail=1
      break
    fi
  done
done <<< "$tracked"

if [[ $fail -ne 0 ]]; then
  echo
  echo "Fix:"
  echo "  - remove from index: git rm -r --cached <path>"
  echo "  - ensure it is ignored in .gitignore"
  exit 1
fi

echo "artifact-guard: OK"
