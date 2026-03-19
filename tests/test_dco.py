from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK_DCO = ROOT / "scripts" / "check_dco.py"


def _run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=True,
    )


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd=cwd, check=check)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "remote", "add", "origin", "https://github.com/example/kprovengine.git")
    return repo


def _commit_file(repo: Path, name: str, content: str, message: str) -> str:
    path = repo / name
    path.write_text(content, encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def test_dco_check_fails_without_signed_off_by(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    base = _commit_file(repo, "a.txt", "one\n", "chore: base\n\nSigned-off-by: Test User <test@example.com>")
    head = _commit_file(repo, "a.txt", "two\n", "feat: missing signoff")

    proc = _run(
        [
            sys.executable,
            str(CHECK_DCO),
            "--base",
            base,
            "--head",
            head,
        ],
        cwd=repo,
        check=False,
    )

    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert "missing Signed-off-by" in proc.stderr


def test_dco_check_passes_with_matching_author_signoff(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    base = _commit_file(repo, "a.txt", "one\n", "chore: base\n\nSigned-off-by: Test User <test@example.com>")
    head = _commit_file(
        repo,
        "a.txt",
        "two\n",
        "feat: signed\n\nSigned-off-by: Test User <test@example.com>",
    )

    proc = _run(
        [
            sys.executable,
            str(CHECK_DCO),
            "--base",
            base,
            "--head",
            head,
        ],
        cwd=repo,
        check=False,
    )

    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "DCO check passed" in proc.stdout
