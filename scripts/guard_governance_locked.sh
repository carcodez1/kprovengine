#!/usr/bin/env bash
set -euo pipefail

LOCKED_FILES=(
  "docs/governance/PROMPT_V1_LOCKED.md"
  "docs/governance/STACK_V1_LOCKED.md"
  "docs/governance/CHANGE_CONTROL.md"
  "docs/governance/REVIEW_GATE_V1.md"
  "docs/governance/WORKFLOW_V1.md"
)

BASE_REF="${1:-origin/main}"

# If base ref doesn't exist (first push), do nothing.
git rev-parse --verify "$BASE_REF" >/dev/null 2>&1 || exit 0

changed="$(git diff --name-only "$BASE_REF"...HEAD || true)"

for f in "${LOCKED_FILES[@]}"; do
  if echo "$changed" | grep -qx "$f"; then
    echo "ERROR: governance file changed (V1 locked): $f"
    echo "Record changes in BACKLOG.md or open a V2 proposal per CHANGE_CONTROL."
    exit 1
  fi
done

echo "governance-guard: OK"
