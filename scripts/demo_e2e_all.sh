#!/usr/bin/env bash
set -euo pipefail

say(){ printf "\n\033[1m==> %s\033[0m\n" "$*"; }
fail(){ echo "FAIL: $*" >&2; exit 1; }
have(){ command -v "$1" >/dev/null 2>&1; }
need(){ have "$1" || fail "missing tool on PATH: $1"; }

say "0) Preconditions"
need git
need python3.12

say "0.1) Confirm repo root and required files"
ROOT="$(git rev-parse --show-toplevel)"
echo "REPO_ROOT=${ROOT}"
cd "${ROOT}"

[ -f pyproject.toml ] || fail "pyproject.toml missing at repo root (${ROOT})"
[ -d scripts ] || fail "scripts/ directory missing at repo root (${ROOT})"

[ -x scripts/guard_governance_locked.sh ] || fail "missing scripts/guard_governance_locked.sh (expected in vendor repo)"
[ -x scripts/forbid_tracked_artifacts.sh ] || fail "missing scripts/forbid_tracked_artifacts.sh (expected in vendor repo)"

say "0.2) Ensure clean working tree for demo"
rm -f in.txt || true
rm -rf runs || true
rm -rf dist || true

if ! git diff --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
  say "WARNING: working tree is not clean (continuing, but you should explain this)"
  git status -sb
else
  echo "OK: working tree clean"
fi

say "1) Local venv"
rm -rf .venv
python3.12 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

python -V
python -c "import sys; print(sys.executable)"
pip -V
python -m pip install -U pip >/dev/null

say "2) Install project + test toolchain"
# Prefer dev extras; fall back to base if extras not defined in this vendor copy.
python -m pip install -e ".[dev]" >/dev/null 2>&1 || python -m pip install -e . >/dev/null

# Ensure required demo tooling exists even if extras were minimal.
python -m pip install -U pytest pytest-cov build >/dev/null

say "3) Lint (optional)"
if python -m pip show ruff >/dev/null 2>&1; then
  python -m ruff --version
  python -m ruff check .
else
  echo "NOTE: ruff not installed in this repo env; skipping lint"
fi

say "4) Tests + coverage gate"
# pytest-cov is guaranteed installed above, so coverage flags should work.
python -m pytest -q --cov=kprovengine --cov-branch --cov-fail-under=85

say "5) Deterministic build artifacts (sdist + wheel)"
python -m build -q
[ -d dist ] || fail "dist/ not created"
ls -la dist
ls -1 dist/*.whl >/dev/null
ls -1 dist/*.tar.gz >/dev/null
echo "OK: wheel + sdist present"

say "6) Governance + artifact hygiene guards"
bash scripts/guard_governance_locked.sh
bash scripts/forbid_tracked_artifacts.sh

say "7) Runtime demo (best-effort)"
echo "demo input $(date -u +%Y-%m-%dT%H:%M:%SZ)" > in.txt

if python -c "import kprovengine.cli" >/dev/null 2>&1; then
  python -m kprovengine.cli in.txt --out runs/
  LATEST="$(ls -1dt runs/* | head -n 1)"
  [ -n "${LATEST}" ] || fail "no run output written under runs/"
  echo "LATEST_RUN=${LATEST}"
  ls -la "${LATEST}"
else
  echo "NOTE: kprovengine.cli not present in this vendor copy."
  echo "Demo alternative: open src/kprovengine/ + tests/ and explain evidence model + deterministic layout."
fi

say "8) What to show for CI/CD supply-chain"
cat <<'EOF'
Open in GitHub UI (read-only proof):
- .github/workflows/ci.yml        (lint/test/build/governance)
- .github/workflows/release.yml   (SBOM + provenance attestation + cosign signing bundles)
Note: tag-triggered release needs push permission; local demo proves determinism + governance.
EOF

say "DONE"
