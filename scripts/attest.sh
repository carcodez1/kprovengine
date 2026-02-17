#!/usr/bin/env bash
set -euo pipefail

DIST_DIR="${1:-dist}"

fail() { echo "FAIL: $*" >&2; exit 1; }

[ -d "${DIST_DIR}" ] || fail "missing ${DIST_DIR}/ (run: python -m build)"

shopt -s nullglob
sdists=("${DIST_DIR}"/*.tar.gz)
wheels=("${DIST_DIR}"/*.whl)
spdx=("${DIST_DIR}"/*.spdx.json)
cdx=("${DIST_DIR}"/*.cdx.json)

[ "${#sdists[@]}" -gt 0 ] || fail "no sdist found in ${DIST_DIR}/"
[ "${#wheels[@]}" -gt 0 ] || fail "no wheel found in ${DIST_DIR}/"
[ "${#spdx[@]}" -gt 0 ] || fail "missing SPDX SBOM outputs (${DIST_DIR}/*.spdx.json)"
[ "${#cdx[@]}" -gt 0 ] || fail "missing CycloneDX SBOM outputs (${DIST_DIR}/*.cdx.json)"

# If signatures are required for release, enforce presence.
# If you only sign on tag builds, keep this gate only in release.yml.
sigs=("${DIST_DIR}"/*.sig)
crts=("${DIST_DIR}"/*.crt)
[ "${#sigs[@]}" -gt 0 ] || fail "missing cosign signatures (*.sig) in ${DIST_DIR}/"
[ "${#crts[@]}" -gt 0 ] || fail "missing cosign certificates (*.crt) in ${DIST_DIR}/"

echo "OK: attest gate passed (dist present, SBOMs present, signatures present)"
