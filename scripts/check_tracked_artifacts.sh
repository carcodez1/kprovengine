#!/usr/bin/env bash
set -euo pipefail

PATTERN='^(runs/|demo_runs/|dist/|coverage\.xml|\.coverage)$'

if git ls-files | grep -Eq "$PATTERN"; then
  echo "tracked artifacts: FOUND (FAIL)" >&2
  git ls-files | grep -E "$PATTERN" >&2
  exit 1
fi

echo "tracked artifacts: NONE (OK)"
