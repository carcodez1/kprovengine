#!/usr/bin/env bash
set -e

OUT="docs/governance/PROJECT_SNAPSHOT_V1_2026-02-08.md"

echo "# PROJECT SNAPSHOT — KProvEngine V1 (2026-02-08)" > $OUT
echo "" >> $OUT

echo "## Git Commit" >> $OUT
git rev-parse HEAD >> $OUT
echo "" >> $OUT

echo "## Repo Structure" >> $OUT
find . -maxdepth 4 -type f >> $OUT
echo "" >> $OUT

echo "## pyproject.toml" >> $OUT
sed -n '1,200p' pyproject.toml >> $OUT
echo "" >> $OUT

echo "## tests file list" >> $OUT
find tests -type f >> $OUT
echo "" >> $OUT

echo "## Snapshot created at $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> $OUT
