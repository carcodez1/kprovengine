#!/usr/bin/env bash
set -euo pipefail

echo "== DOCTOR =="
echo "PWD=$(pwd)"
echo "USER=${USER:-unknown}"
echo "SHELL=${SHELL:-unknown}"
echo "0=${0:-unknown}"
echo "TERM=${TERM:-unknown}"

echo "== PATH (first 40 entries) =="
i=1
OLDIFS=${IFS}
IFS=:
for p in ${PATH}; do
  printf "%2d  %s\n" "${i}" "${p}"
  i=$((i+1))
  [ "${i}" -le 40 ] || break
done
IFS=${OLDIFS}

echo "== COMMAND RESOLUTION =="
command -v python  >/dev/null 2>&1 && echo "python=$(command -v python)"  || echo "NO python on PATH"
command -v python3 >/dev/null 2>&1 && echo "python3=$(command -v python3)" || echo "NO python3 on PATH"

echo "== VENV CHECK =="
if [ -x .venv/bin/python ]; then
  echo "venv_python=$(pwd)/.venv/bin/python"
  ./.venv/bin/python -V
  ./.venv/bin/python -c "import sys; print(sys.executable)"
else
  echo "FAIL: missing .venv/bin/python (run: make venv)" >&2
  exit 1
fi

echo "== BUILD/SBOM SMOKE =="
rm -rf dist || true
./.venv/bin/python -m build -q
bash scripts/sbom.sh
ls -la dist | rg -n '\.(spdx|cdx)\.json$' || (echo "FAIL: missing SBOM outputs" >&2; exit 1)

echo "OK: doctor passed"
