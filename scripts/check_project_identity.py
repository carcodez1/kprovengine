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
DISPLAY_NAME: Final[str] = "KProvEngine"
CANONICAL_REPO: Final[str] = "https://github.com/carcodez1/kprovengine"

# Forbidden tokens are externalized to avoid checker self-scan issues.
FORBIDDEN_TOKENS_FILE: Final[Path] = ROOT / "docs" / "governance" / "IDENTITY_FORBIDDEN_TOKENS.txt"

# Surfaces where CANONICAL_REPO must appear verbatim.
REQUIRED_CANONICAL_REPO_FILES: Final[tuple[Path, ...]] = (
    ROOT / "README.md",
    ROOT / "pyproject.toml",
    ROOT / "Dockerfile",
)

# Surfaces where TECH_NAME must appear (packaging + OCI title).
REQUIRED_TECH_IDENTITY_FILES: Final[tuple[Path, ...]] = (
    ROOT / "pyproject.toml",
    ROOT / "Dockerfile",
)

# Display name allowed only in documentation/marketing text and Dockerfile description label text.
# In practice: allow under docs/** and a limited set of top-level docs.
DISPLAY_ALLOWED_ROOTS: Final[tuple[Path, ...]] = (
    ROOT / "README.md",
    ROOT / "OSS_GOVERNANCE.md",
    ROOT / "SUPPORT.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "SECURITY.md",
    ROOT / "CODE_OF_CONDUCT.md",
    ROOT / "Dockerfile",  # allowed, but ONLY description-line usage is permitted (enforced elsewhere)
    ROOT / "docs",
)

# Code roots where DISPLAY_NAME MUST NOT appear.
DISPLAY_FORBIDDEN_ROOTS: Final[tuple[Path, ...]] = (
    ROOT / "src",
    ROOT / "tests",
    ROOT / ".github",
    ROOT / "scripts",
)

# We additionally restrict Dockerfile usage:
# - DISPLAY_NAME is allowed only in org.opencontainers.image.description value (free text).
# - TECH_NAME and CANONICAL_REPO must be used in title/source labels respectively.
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
        if not line.strip():
            continue
        files.append((ROOT / line.strip()).resolve())
    return files


def _contains_verbatim(p: Path, needle: str) -> bool:
    return needle in _read_text(p)


def _find_hits(p: Path, needle: str) -> list[Hit]:
    hits: list[Hit] = []
    text = _read_text(p)
    for idx, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            hits.append(Hit(path=p, line_no=idx, line=line))
    return hits


def _load_forbidden_tokens() -> list[str]:
    if not FORBIDDEN_TOKENS_FILE.exists():
        _fail(f"missing forbidden tokens file: {FORBIDDEN_TOKENS_FILE}")
        raise SystemExit(EX_SOFTWARE)

    toks: list[str] = []
    for raw in _read_text(FORBIDDEN_TOKENS_FILE).splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith("#"):
            continue
        toks.append(s)
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


def _check_required_surfaces() -> int:
    fail = 0

    # Canonical URL required.
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

    # Technical identity required.
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
        _fail(f"pyproject.toml: project.scripts['{TECH_NAME}'] must be '{expected_entry}', got '{entry}'")
        fail = 1

    urls = proj.get("urls", {})
    for k in ("Homepage", "Source", "Issues", "Documentation"):
        v = urls.get(k)
        if not isinstance(v, str) or "github.com" not in v:
            _fail(f"pyproject.toml: project.urls.{k} missing/invalid")
            fail = 1
    # Enforce canonical repo appears at least once in urls (strong but accurate).
    url_blob = "\n".join(str(v) for v in urls.values() if isinstance(v, str))
    if CANONICAL_REPO not in url_blob:
        _fail(f"pyproject.toml: project.urls must contain canonical repo '{CANONICAL_REPO}'")
        fail = 1

    return fail


def _check_dockerfile_labels() -> int:
    if not DOCKERFILE.exists():
        _fail("Dockerfile missing")
        return 1

    text = _read_text(DOCKERFILE)
    fail = 0

    # Must include canonical source label (exact URL).
    # We do NOT over-parse Dockerfile; we verify presence of canonical URL.
    if CANONICAL_REPO not in text:
        _fail(f"Dockerfile: expected canonical repo url '{CANONICAL_REPO}' to appear")
        fail = 1

    # Must include TECH_NAME in title label (or at least somewhere; we enforce label key presence).
    # Strongly recommended exact label line; but keep robust by checking both tokens.
    if TECH_NAME not in text:
        _fail(f"Dockerfile: expected technical identity '{TECH_NAME}' to appear")
        fail = 1

    # DISPLAY_NAME is allowed ONLY in description label text.
    # If DISPLAY_NAME appears and it is not on a line containing 'org.opencontainers.image.description',
    # we fail with an example hit.
    for idx, line in enumerate(text.splitlines(), start=1):
        if DISPLAY_NAME in line and "org.opencontainers.image.description" not in line:
            _fail(
                f"Dockerfile: display name '{DISPLAY_NAME}' is allowed only in org.opencontainers.image.description "
                f"(line {idx})"
            )
            fail = 1
            break

    return fail


def _check_forbidden_tokens(tracked: list[Path], forbidden_tokens: list[str]) -> int:
    fail = 0

    # Avoid scanning the forbidden tokens file itself (it must contain forbidden strings by design).
    excluded = {FORBIDDEN_TOKENS_FILE.resolve()}

    for tok in forbidden_tokens:
        for p in tracked:
            if p in excluded:
                continue
            if not p.is_file():
                continue
            # Skip .gitignored non-tracked not possible; tracked list already.
            hits = _find_hits(p, tok)
            if hits:
                h = hits[0]
                _fail(
                    f"forbidden token '{tok}' found (example hit shown): {h.path.relative_to(ROOT)}:{h.line_no}:{h.line.strip()}"
                )
                fail = 1
                break
        if fail:
            break

    return fail


def _check_display_name_scope(tracked: list[Path]) -> int:
    """
    Enforce contract:
      - DISPLAY_NAME allowed only in docs/** + selected top-level markdown.
      - DISPLAY_NAME MUST NOT appear under src/** (and other forbidden roots).
      - Dockerfile exception: DISPLAY_NAME allowed ONLY on OCI description label line(s).
    """
    for p in tracked:
        if not p.is_file():
            continue

        text = _read_text(p)
        if DISPLAY_NAME not in text:
            continue

        # Hard-forbidden roots (src/tests/.github/scripts) are never allowed.
        if _display_forbidden(p):
            hits = _find_hits(p, DISPLAY_NAME)
            h = hits[0]
            _fail(
                f"display name '{DISPLAY_NAME}' is forbidden in {h.path.relative_to(ROOT)} "
                f"(example hit): {h.path.relative_to(ROOT)}:{h.line_no}:{h.line.strip()}"
            )
            return 1

        # Dockerfile is allowed ONLY for org.opencontainers.image.description lines.
        if p.resolve() == DOCKERFILE.resolve():
            for idx, line in enumerate(text.splitlines(), start=1):
                if DISPLAY_NAME in line and "org.opencontainers.image.description" not in line:
                    _fail(
                        f"Dockerfile: display name '{DISPLAY_NAME}' is allowed only in "
                        f"org.opencontainers.image.description (line {idx})"
                    )
                    return 1
            # If we got here, Dockerfile hits are compliant.
            continue

        # Non-Dockerfile: must be in explicitly allowed roots.
        if not _display_allowed(p):
            hits = _find_hits(p, DISPLAY_NAME)
            h = hits[0]
            _fail(
                f"display name '{DISPLAY_NAME}' appears in non-allowed file {h.path.relative_to(ROOT)} "
                f"(example hit): {h.path.relative_to(ROOT)}:{h.line_no}:{h.line.strip()}"
            )
            return 1

    return 0

def main() -> int:
    print("== Project Identity Guard ==")
    print(f"Technical identity: {TECH_NAME}")
    print(f"Display identity:   {DISPLAY_NAME}")
    print(f"Canonical repo:     {CANONICAL_REPO}")

    tracked = _tracked_files()
    forbidden = _load_forbidden_tokens()

    fail = 0
    fail |= _check_forbidden_tokens(tracked, forbidden)
    fail |= _check_required_surfaces()
    fail |= _check_pyproject_toml()
    fail |= _check_dockerfile_labels()
    fail |= _check_display_name_scope(tracked)

    if fail:
        return EX_FAIL

    _ok("project identity checks passed")
    return EX_OK


if __name__ == "__main__":
    raise SystemExit(main())
