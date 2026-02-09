#!/usr/bin/env bash
set -euo pipefail

# Renders Mermaid diagrams from markdown into docs/assets as SVG.
# Requires: node + @mermaid-js/mermaid-cli (installed in CI)

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IN_MD="${ROOT}/docs/architecture.md"
OUT_DIR="${ROOT}/docs/assets"
OUT_SVG="${OUT_DIR}/architecture.svg"

mkdir -p "${OUT_DIR}"

# Extract the first mermaid block from architecture.md into a temp .mmd file
TMP_MMD="$(mktemp)"
awk '
  $0 ~ /^```mermaid/ {inblock=1; next}
  $0 ~ /^```/ && inblock==1 {exit}
  inblock==1 {print}
' "${IN_MD}" > "${TMP_MMD}"

if [[ ! -s "${TMP_MMD}" ]]; then
  echo "No mermaid block found in ${IN_MD}" >&2
  exit 1
fi

# Render (mmdc must be available)
npx --yes @mermaid-js/mermaid-cli@11.4.0 -i "${TMP_MMD}" -o "${OUT_SVG}" -t default

echo "Rendered: ${OUT_SVG}"