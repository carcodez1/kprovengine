from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN_MANIFEST = ROOT / "scripts" / "generate_changeset_manifest.py"
VERIFY_MANIFEST = ROOT / "scripts" / "verify_changeset_manifest.py"


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


def test_generate_manifest_is_deterministic(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    base = _commit_file(repo, "a.txt", "one\n", "chore: base")
    head = _commit_file(repo, "a.txt", "two\n", "feat: update")

    manifest_path = repo / "changeset-manifest.json"
    fixed_ts = "2026-03-19T00:00:00Z"

    for _ in range(2):
        proc = _run(
            [
                sys.executable,
                str(GEN_MANIFEST),
                "--base",
                base,
                "--head",
                head,
                "--generated-at",
                fixed_ts,
                "--output",
                str(manifest_path),
            ],
            cwd=repo,
            check=False,
        )
        assert proc.returncode == 0, (proc.stdout, proc.stderr)

    payload = manifest_path.read_text(encoding="utf-8")
    payload_2 = manifest_path.read_text(encoding="utf-8")
    assert payload == payload_2

    manifest = json.loads(payload)
    assert manifest["repoUrl"] == "https://github.com/example/kprovengine.git"
    assert manifest["baseSha"] == base
    assert manifest["headSha"] == head
    assert manifest["generatedAt"] == fixed_ts
    assert manifest["fileCount"] == 1

    file_row = manifest["files"][0]
    assert file_row["path"] == "a.txt"
    assert file_row["status"] == "M"
    assert file_row["sha256"] == hashlib.sha256(b"two\n").hexdigest()

    verify = _run(
        [
            sys.executable,
            str(VERIFY_MANIFEST),
            "--manifest",
            str(manifest_path),
        ],
        cwd=repo,
        check=False,
    )
    assert verify.returncode == 0, (verify.stdout, verify.stderr)


def test_verify_manifest_rejects_invalid_rfc3339_timestamp(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    base = _commit_file(repo, "a.txt", "one\n", "chore: base")
    head = _commit_file(repo, "a.txt", "two\n", "feat: update")

    manifest_path = repo / "changeset-manifest.json"
    generate = _run(
        [
            sys.executable,
            str(GEN_MANIFEST),
            "--base",
            base,
            "--head",
            head,
            "--generated-at",
            "2026-03-19T00:00:00Z",
            "--output",
            str(manifest_path),
        ],
        cwd=repo,
        check=False,
    )
    assert generate.returncode == 0, (generate.stdout, generate.stderr)

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["generatedAt"] = "2026-03-19 00:00:00"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verify = _run(
        [
            sys.executable,
            str(VERIFY_MANIFEST),
            "--manifest",
            str(manifest_path),
        ],
        cwd=repo,
        check=False,
    )
    assert verify.returncode == 1, (verify.stdout, verify.stderr)
    assert "generatedAt" in verify.stderr
