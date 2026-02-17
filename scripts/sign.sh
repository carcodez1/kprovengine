#!/usr/bin/env bash
set -euo pipefail

DIST_DIR="${1:-dist}"

fail() { echo "FAIL: $*" >&2; exit 1; }

command -v cosign >/dev/null 2>&1 || fail "cosign not installed (macOS: brew install cosign)"
[ -d "${DIST_DIR}" ] || fail "missing ${DIST_DIR}/ (run: python -m build)"

shopt -s nullglob
artifacts=("${DIST_DIR}"/*.whl "${DIST_DIR}"/*.tar.gz "${DIST_DIR}"/*.spdx.json "${DIST_DIR}"/*.cdx.json)
[ "${#artifacts[@]}" -gt 0 ] || fail "no artifacts found in ${DIST_DIR}/"

for f in "${artifacts[@]}"; do
  echo "Signing: ${f}"
  cosign sign-blob \
    --yes \
    --output-signature "${f}.sig" \
    --output-certificate "${f}.crt" \
    "${f}"
done

echo "OK: cosign signatures written to ${DIST_DIR}/*.sig and certificates to ${DIST_DIR}/*.crt"
