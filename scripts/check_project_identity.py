#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

try:
    import tomllib  # py311+
except Exception as e:  # pragma: no cover
    print(f"error: tomllib unavailable: {e}", file=sys.stderr)
    raise SystemExit(70) from e

EX_OK = 0
EX_FAIL = 1
EX_SOFTWARE = 70

CANON = {
    "brand": "KProvEngine",
    "repo_url": "https://github.com/carcodez1/kprovengine",
    "repo_slug": "carcodez1/kprovengine",
    "project_name": "kprovengine",
    "pkg_import": "kprovengine",
    "cli_name": "kprovengine",
    "cli_entry": "kprovengine.cli:main",
}

FORBIDDEN_FILE = Path("docs/governance/IDENTITY_FORBIDDEN_TOKENS.txt")

CHECK_FILES_REQUIRE_REPO_URL = [
    Path("README.md"),
    Path("pyproject.toml"),
    Path("Dockerfile"),
]


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="strict")


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)


def _ok(msg: str) -> None:
    print(f"OK: {msg}")


def _scan_forbidden(tracked_files: list[Path]) -> int:
    if not FORBIDDEN_FILE.exists():
        _fail(f"{FORBIDDEN_FILE}: missing forbidden token policy")
        return 1

    forbidden = [ln.strip() for ln in _read_text(FORBIDDEN_FILE).splitlines() if ln.strip() and not ln.strip().startswith("#")]

    skip = {Path(__file__).resolve(), FORBIDDEN_FILE.resolve()}

    rc = 0
    for tok in forbidden:
        hits: list[str] = []
        for f in tracked_files:
            if f.resolve() in skip:
                continue
            # Skip obvious binaries by extension; keep minimal.
            if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf"}:
                continue
            try:
                txt = _read_text(f)
            except Exception:
                continue
            if tok in txt:
                # best-effort line number
                for i, line in enumerate(txt.splitlines(), start=1):
                    if tok in line:
                        hits.append(f"{f}:{i}:{line.strip()}")
                        break
        if hits:
            _fail(f"forbidden token '{tok}' found (example hit shown):")
            for h in hits[:5]:
                print(f"  {h}", file=sys.stderr)
            rc = 1
    return rc


def _load_pyproject() -> dict:
    p = Path("pyproject.toml")
    if not p.exists():
        _fail("pyproject.toml not found")
        raise SystemExit(EX_FAIL)
    data = tomllib.loads(_read_text(p))
    return data


def _check_pyproject(data: dict) -> int:
    rc = 0
    proj = data.get("project") or {}
    name = proj.get("name")
    if name != CANON["project_name"]:
        _fail(f"pyproject.toml: project.name must be '{CANON['project_name']}', got '{name}'")
        rc = 1

    scripts = proj.get("scripts") or {}
    entry = scripts.get(CANON["cli_name"])
    if entry != CANON["cli_entry"]:
        _fail(
            f"pyproject.toml: project.scripts.{CANON['cli_name']} must be "
            f"'{CANON['cli_entry']}', got '{entry}'"
        )
        rc = 1

    urls = proj.get("urls") or {}
    for k in ("Homepage", "Source", "Issues", "Documentation"):
        v = urls.get(k)
        if not isinstance(v, str) or not v.startswith(CANON["repo_url"]):
            _fail(f"pyproject.toml: project.urls.{k} must start with '{CANON['repo_url']}', got '{v}'")
            rc = 1

    return rc


def _check_required_repo_url() -> int:
    rc = 0
    for f in CHECK_FILES_REQUIRE_REPO_URL:
        if not f.exists():
            continue
        try:
            txt = _read_text(f)
        except Exception as e:
            _fail(f"{f}: cannot read: {e}")
            rc = 1
            continue
        if CANON["repo_url"] not in txt:
            _fail(f"{f}: expected canonical repo url '{CANON['repo_url']}' to appear")
            rc = 1
    return rc


def _tracked_files() -> list[Path]:
    # Deterministic: tracked files only. Uses git if available; otherwise minimal set.
    import subprocess

    try:
        out = subprocess.check_output(["git", "ls-files"], text=True)
    except Exception as e:
        _fail(f"git ls-files failed: {e}")
        raise SystemExit(EX_SOFTWARE) from e

    files: list[Path] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        files.append(Path(line.strip()))
    return files


def main() -> int:
    print("== Project Identity Guard ==")
    print(f"Canonical brand: {CANON['brand']}")
    print(f"Canonical repo:  {CANON['repo_url']}")
    print()

    tracked = _tracked_files()

    rc = 0
    rc |= _scan_forbidden(tracked)
    data = _load_pyproject()
    rc |= _check_pyproject(data)
    rc |= _check_required_repo_url()

    if rc == 0:
        _ok("project identity checks passed")
        return EX_OK

    return EX_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
