#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT/dist"
OUT_DIR="$ROOT/dist"

if [ ! -d "$DIST_DIR" ]; then
  echo "dist/ missing. Run: python -m build"
  exit 1
fi

if ! command -v syft >/dev/null 2>&1; then
  echo "syft not installed."
  echo "macOS: brew install syft"
  echo "Linux: curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh"
  exit 1
fi

for artifact in "$DIST_DIR"/*.whl "$DIST_DIR"/*.tar.gz; do
  syft "$artifact" -o spdx-json="$OUT_DIR/$(basename "$artifact").spdx.json"
  syft "$artifact" -o cyclonedx-json="$OUT_DIR/$(basename "$artifact").cdx.json"
done

echo "SBOM generation complete."
