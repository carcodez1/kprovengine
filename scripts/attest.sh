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

# Bundle-first signing material (cosign v3 new bundle format).
artifacts=(
  "${DIST_DIR}"/*.whl
  "${DIST_DIR}"/*.tar.gz
  "${DIST_DIR}"/*.spdx.json
  "${DIST_DIR}"/*.cdx.json
)

for f in "${artifacts[@]}"; do
  b="${f}.bundle"
  [ -f "${b}" ] || fail "missing cosign bundle (${b}) for artifact (${f})"
done

# Optional cryptographic verification.
# CI should set COSIGN_OIDC_ISSUER=https://token.actions.githubusercontent.com
# Local runs may be https://github.com/login/oauth (browser login) depending on flow.
if command -v cosign >/dev/null 2>&1; then
  ISSUER="${COSIGN_OIDC_ISSUER:-}"
  ID_RE="${COSIGN_IDENTITY_REGEXP:-}"

  if [ -n "${ISSUER}" ] && [ -n "${ID_RE}" ]; then
    for f in "${artifacts[@]}"; do
      echo "Verifying bundle: ${f}"
      cosign verify-blob \
        --bundle "${f}.bundle" \
        --certificate-identity-regexp "${ID_RE}" \
        --certificate-oidc-issuer "${ISSUER}" \
        "${f}" >/dev/null
    done
    echo "OK: cosign verify-blob passed for all artifacts"
  else
    echo "NOTE: skipping cryptographic verification (set COSIGN_OIDC_ISSUER and COSIGN_IDENTITY_REGEXP to enable)"
  fi
else
  echo "NOTE: cosign not installed; bundle presence gate only"
fi

echo "OK: attest gate passed (dist present, SBOMs present, bundles present)"
