set -euo pipefail

echo "=== 0) Location ==="
pwd
ls -la | sed -n '1,40p'

echo
echo "=== 1) Shell / OS ==="
echo "SHELL=${SHELL:-UNKNOWN}"
echo "ZSH_VERSION=${ZSH_VERSION:-UNKNOWN}"
sw_vers || true
uname -a || true

echo
echo "=== 2) CPU / Arch ==="
uname -m || true
sysctl -n machdep.cpu.brand_string 2>/dev/null || true

echo
echo "=== 3) Git ==="
git --version || true
git rev-parse --abbrev-ref HEAD || true
git status --porcelain=v1 || true

echo
echo "=== 4) Python resolution ==="
echo "--- which python/python3 ---"
command -v python || true
python --version 2>&1 || true
command -v python3 || true
python3 --version 2>&1 || true

echo
echo "=== 5) Python capabilities (tomllib/build) ==="
python3 - <<'PY'
import sys
print("executable:", sys.executable)
print("version:", sys.version.replace("\n"," "))
ok = True
try:
    import tomllib  # py3.11+
    print("tomllib: OK")
except Exception as e:
    ok = False
    print("tomllib: FAIL:", repr(e))
try:
    import build
    print("build: OK")
except Exception as e:
    print("build: MISSING:", repr(e))
print("RESULT:", "OK" if ok else "NEEDS_PY311_PLUS")
PY

echo
echo "=== 6) Pip / tooling ==="
python3 -m pip --version 2>&1 || true
python3 -m pip show ruff 2>&1 || true
python3 -m pip show pytest 2>&1 || true
python3 -m pip show pre-commit 2>&1 || true

echo
echo "=== 7) Ruff / Pytest binaries ==="
command -v ruff || true
ruff --version 2>&1 || true
command -v pytest || true
pytest --version 2>&1 || true
command -v pre-commit || true
pre-commit --version 2>&1 || true

echo
echo "=== 8) Perl (for README patch script option) ==="
command -v perl || true
perl -v | head -n 2 || true

echo
echo "=== 9) Docker ==="
command -v docker || true
docker --version 2>&1 || true
docker info 2>/dev/null | egrep -i 'Server Version|Operating System|Architecture|CPUs|Total Memory' || true

echo
echo "=== 10) Repo-specific: pyproject + README presence ==="
test -f pyproject.toml && echo "pyproject.toml: OK" || echo "pyproject.toml: MISSING"
test -f README.md && echo "README.md: OK" || echo "README.md: MISSING"
test -d .vscode && echo ".vscode/: OK" || echo ".vscode/: MISSING"

echo
echo "=== 11) Tracked artifact risk check ==="
git ls-files | egrep '^(runs/|demo_runs/|dist/|coverage\.xml|\.coverage)$' || echo "tracked artifacts: NONE (OK)"

echo
echo "=== DONE ==="
