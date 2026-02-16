#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

try:
    import tomllib  # py311+
except Exception as e:  # pragma: no cover
    print(f"error: tomllib unavailable: {e}", file=sys.stderr)
    raise SystemExit(70) from e

EX_OK: Final[int] = 0
EX_FAIL: Final[int] = 1
EX_SOFTWARE: Final[int] = 70

ROOT: Final[Path] = Path(__file__).resolve().parents[1]

# ---- Contract constants (V1 LOCKED) ----
TECH_NAME: Final[str] = "kprovengine"
CANONICAL_REPO: Final[str] = "https://github.com/carcodez1/kprovengine"

FORBIDDEN_TOKENS_FILE: Final[Path] = ROOT / "docs" / "governance" / "IDENTITY_FORBIDDEN_TOKENS.txt"
DISPLAY_NAME_FILE: Final[Path] = ROOT / "docs" / "governance" / "IDENTITY_DISPLAY_NAME.txt"

REQUIRED_CANONICAL_REPO_FILES: Final[tuple[Path, ...]] = (
    ROOT / "README.md",
    ROOT / "pyproject.toml",
    ROOT / "Dockerfile",
)

REQUIRED_TECH_IDENTITY_FILES: Final[tuple[Path, ...]] = (
    ROOT / "pyproject.toml",
    ROOT / "Dockerfile",
)

DISPLAY_ALLOWED_ROOTS: Final[tuple[Path, ...]] = (
    ROOT / "README.md",
    ROOT / "OSS_GOVERNANCE.md",
    ROOT / "SUPPORT.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "SECURITY.md",
    ROOT / "CODE_OF_CONDUCT.md",
    ROOT / "docs",
)

DISPLAY_FORBIDDEN_ROOTS: Final[tuple[Path, ...]] = (
    ROOT / "src",
    ROOT / "tests",
    ROOT / ".github",
    ROOT / "scripts",
)

DOCKERFILE: Final[Path] = ROOT / "Dockerfile"


@dataclass(frozen=True)
class Hit:
    path: Path
    line_no: int
    line: str


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)


def _ok(msg: str) -> None:
    print(f"OK: {msg}")


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _tracked_files() -> list[Path]:
    try:
        out = subprocess.check_output(["git", "ls-files"], text=True)
    except Exception as e:
        _fail(f"git ls-files failed: {e}")
        raise SystemExit(EX_SOFTWARE) from e

    files: list[Path] = []
    for line in out.splitlines():
        s = line.strip()
        if not s:
            continue
        files.append((ROOT / s).resolve())
    return files


def _find_hits(p: Path, needle: str) -> list[Hit]:
    hits: list[Hit] = []
    text = _read_text(p)
    for idx, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            hits.append(Hit(path=p, line_no=idx, line=line))
    return hits


def _load_display_name() -> str:
    if not DISPLAY_NAME_FILE.exists():
        _fail(f"missing display name SSOT file: {DISPLAY_NAME_FILE.relative_to(ROOT)}")
        raise SystemExit(EX_SOFTWARE)

    name = _read_text(DISPLAY_NAME_FILE).strip()
    if not name:
        _fail(f"display name SSOT file is empty: {DISPLAY_NAME_FILE.relative_to(ROOT)}")
        raise SystemExit(EX_SOFTWARE)

    return name


def _load_forbidden_tokens() -> list[str]:
    if not FORBIDDEN_TOKENS_FILE.exists():
        _fail(f"missing forbidden tokens file: {FORBIDDEN_TOKENS_FILE.relative_to(ROOT)}")
        raise SystemExit(EX_SOFTWARE)

    toks: list[str] = []
    for raw in _read_text(FORBIDDEN_TOKENS_FILE).splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        toks.append(s)

    if not toks:
        _fail(f"forbidden tokens file is empty: {FORBIDDEN_TOKENS_FILE.relative_to(ROOT)}")
        raise SystemExit(EX_SOFTWARE)

    return toks


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except Exception:
        return False


def _display_allowed(path: Path) -> bool:
    for r in DISPLAY_ALLOWED_ROOTS:
        if path == r:
            return True
        if r.is_dir() and _is_under(path, r):
            return True
    return False


def _display_forbidden(path: Path) -> bool:
    for r in DISPLAY_FORBIDDEN_ROOTS:
        if r.is_dir() and _is_under(path, r):
            return True
    return False


def _contains_verbatim(p: Path, needle: str) -> bool:
    return needle in _read_text(p)


def _check_required_surfaces() -> int:
    fail = 0

    for p in REQUIRED_CANONICAL_REPO_FILES:
        if not p.exists():
            _fail(f"required file missing: {p.relative_to(ROOT)}")
            fail = 1
            continue
        if not _contains_verbatim(p, CANONICAL_REPO):
            _fail(
                f"{p.relative_to(ROOT)}: expected canonical repo url '{CANONICAL_REPO}' to appear"
            )
            fail = 1

    for p in REQUIRED_TECH_IDENTITY_FILES:
        if not p.exists():
            _fail(f"required file missing: {p.relative_to(ROOT)}")
            fail = 1
            continue
        if not _contains_verbatim(p, TECH_NAME):
            _fail(f"{p.relative_to(ROOT)}: expected technical identity '{TECH_NAME}' to appear")
            fail = 1

    return fail


def _check_pyproject_toml() -> int:
    p = ROOT / "pyproject.toml"
    if not p.exists():
        _fail("pyproject.toml missing")
        return 1

    data = tomllib.loads(_read_text(p))
    fail = 0

    proj = data.get("project", {})
    name = proj.get("name")
    if name != TECH_NAME:
        _fail(f"pyproject.toml: project.name must be '{TECH_NAME}', got '{name}'")
        fail = 1

    scripts = proj.get("scripts", {})
    entry = scripts.get(TECH_NAME)
    expected_entry = f"{TECH_NAME}.cli:main"
    if entry != expected_entry:
        _fail(
            f"pyproject.toml: project.scripts['{TECH_NAME}'] must be '{expected_entry}', got '{entry}'"
        )
        fail = 1

    urls = proj.get("urls", {})
    url_blob = "\n".join(str(v) for v in urls.values() if isinstance(v, str))
    if CANONICAL_REPO not in url_blob:
        _fail(f"pyproject.toml: project.urls must contain canonical repo '{CANONICAL_REPO}'")
        fail = 1

    return fail


def _check_dockerfile_labels(display_name: str) -> int:
    if not DOCKERFILE.exists():
        _fail("Dockerfile missing")
        return 1

    text = _read_text(DOCKERFILE)
    fail = 0

    if CANONICAL_REPO not in text:
        _fail(f"Dockerfile: expected canonical repo url '{CANONICAL_REPO}' to appear")
        fail = 1

    if TECH_NAME not in text:
        _fail(f"Dockerfile: expected technical identity '{TECH_NAME}' to appear")
        fail = 1

    # DISPLAY is allowed only in the description label line.
    for idx, line in enumerate(text.splitlines(), start=1):
        if display_name in line and "org.opencontainers.image.description" not in line:
            _fail(
                f"Dockerfile: display name '{display_name}' is allowed only in "
                f"org.opencontainers.image.description (line {idx})"
            )
            fail = 1
            break

    return fail


def _check_forbidden_tokens(tracked: list[Path], forbidden_tokens: list[str]) -> int:
    excluded = {FORBIDDEN_TOKENS_FILE.resolve(), DISPLAY_NAME_FILE.resolve()}
    for tok in forbidden_tokens:
        for p in tracked:
            if p in excluded or not p.is_file():
                continue
            hits = _find_hits(p, tok)
            if hits:
                h = hits[0]
                _fail(
                    f"forbidden token '{tok}' found (example hit shown): "
                    f"{h.path.relative_to(ROOT)}:{h.line_no}:{h.line.strip()}"
                )
                return 1
    return 0


def _check_display_name_scope(tracked: list[Path], display_name: str) -> int:
    """
    Contract:
      - Display name allowed only in docs/** and selected top-level docs files.
      - Display name forbidden under src/tests/.github/scripts.
      - Dockerfile is handled by _check_dockerfile_labels and is exempt from this scan.
    """
    for p in tracked:
        if not p.is_file():
            continue
        if p.resolve() == DOCKERFILE.resolve():
            continue  # Dockerfile display handling is validated elsewhere.
        if display_name not in _read_text(p):
            continue

        if _display_forbidden(p):
            hits = _find_hits(p, display_name)
            h = hits[0]
            _fail(
                f"display name '{display_name}' is forbidden in {h.path.relative_to(ROOT)} "
                f"(example hit): {h.path.relative_to(ROOT)}:{h.line_no}:{h.line.strip()}"
            )
            return 1

        if not _display_allowed(p):
            hits = _find_hits(p, display_name)
            h = hits[0]
            _fail(
                f"display name '{display_name}' appears in non-allowed file {h.path.relative_to(ROOT)} "
                f"(example hit): {h.path.relative_to(ROOT)}:{h.line_no}:{h.line.strip()}"
            )
            return 1

    return 0


def main() -> int:
    print("== Project Identity Guard ==")
    display_name = _load_display_name()
    print(f"Technical identity: {TECH_NAME}")
    print(f"Display identity:   {display_name}")
    print(f"Canonical repo:     {CANONICAL_REPO}")

    tracked = _tracked_files()
    forbidden = _load_forbidden_tokens()

    fail = 0
    fail |= _check_forbidden_tokens(tracked, forbidden)
    fail |= _check_required_surfaces()
    fail |= _check_pyproject_toml()
    fail |= _check_dockerfile_labels(display_name)
    fail |= _check_display_name_scope(tracked, display_name)

    if fail:
        return EX_FAIL

    _ok("project identity checks passed")
    return EX_OK


if __name__ == "__main__":
    raise SystemExit(main())
