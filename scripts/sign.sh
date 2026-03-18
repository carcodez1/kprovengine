#!/usr/bin/env bash
set -euo pipefail

DIST_DIR="${1:-dist}"

fail() { echo "FAIL: $*" >&2; exit 1; }

command -v cosign >/dev/null 2>&1 || fail "cosign not installed (macOS: brew install cosign)"
[ -d "${DIST_DIR}" ] || fail "missing ${DIST_DIR}/ (run: python -m build)"

shopt -s nullglob

# Sign *everything we care about that exists in dist/, including SBOMs generated per-artifact.
artifacts=(
  "${DIST_DIR}"/*.whl
  "${DIST_DIR}"/*.tar.gz
  "${DIST_DIR}"/*.spdx.json
  "${DIST_DIR}"/*.cdx.json
)

[ "${#artifacts[@]}" -gt 0 ] || fail "no signable artifacts found in ${DIST_DIR}/"

for f in "${artifacts[@]}"; do
  b="${f}.bundle"

  # Skip if already bundled (idempotent), but sanity check it's non-empty.
  if [ -f "${b}" ]; then
    if [ ! -s "${b}" ]; then
      fail "existing bundle is empty: ${b}"
    fi
    echo "SKIP (bundle exists): ${f}"
    continue
  fi

  echo "Signing (bundle): ${f}"
  cosign sign-blob --yes --bundle "${b}" "${f}"

  [ -s "${b}" ] || fail "bundle not written or empty: ${b}"
done

echo "OK: cosign bundles present for all signable artifacts in ${DIST_DIR}/"
