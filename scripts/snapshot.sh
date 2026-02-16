#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DISPLAY_FILE="$ROOT/docs/governance/IDENTITY_DISPLAY_NAME.txt"
OUT="$ROOT/docs/governance/PROJECT_SNAPSHOT_V1_$(date -u +"%Y-%m-%d").md"

if [[ ! -f "$DISPLAY_FILE" ]]; then
  echo "ERROR: missing $DISPLAY_FILE" >&2
  exit 70
fi

DISPLAY_NAME="$(tr -d '\r\n' < "$DISPLAY_FILE")"
if [[ -z "$DISPLAY_NAME" ]]; then
  echo "ERROR: empty display name in $DISPLAY_FILE" >&2
  exit 70
fi

{
  echo "# PROJECT SNAPSHOT — ${DISPLAY_NAME} V1 ($(date -u +"%Y-%m-%d"))"
  echo
  echo "## Git Commit"
  git -C "$ROOT" rev-parse HEAD
  echo
  echo "## Repo Structure (tracked files)"
  git -C "$ROOT" ls-files
  echo
  echo "## pyproject.toml (first 200 lines)"
  sed -n '1,200p' "$ROOT/pyproject.toml"
  echo
  echo "## tests file list"
  find "$ROOT/tests" -type f 2>/dev/null || true
  echo
  echo "## Snapshot created at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
} > "$OUT"

echo "OK: wrote $OUT"
