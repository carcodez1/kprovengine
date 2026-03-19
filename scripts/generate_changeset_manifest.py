#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

EX_OK: Final[int] = 0
EX_USAGE: Final[int] = 64
EX_SOFTWARE: Final[int] = 70


@dataclass(frozen=True)
class ChangedFile:
    path: str
    status: str
    sha256: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "status": self.status,
            "sha256": self.sha256,
        }


def _git(args: list[str], *, text: bool = True) -> str | bytes:
    try:
        proc = subprocess.run(
            ["git", *args],
            check=False,
            capture_output=True,
            text=text,
            encoding="utf-8" if text else None,
        )
    except OSError as exc:
        raise RuntimeError(f"failed to execute git {' '.join(args)}: {exc}") from exc

    if proc.returncode != 0:
        stderr = proc.stderr if text else proc.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr.strip()}")
    return proc.stdout if text else bytes(proc.stdout)


def _resolve_sha(ref: str) -> str:
    return str(_git(["rev-parse", ref], text=True)).strip()


def _repo_url() -> str:
    return str(_git(["config", "--get", "remote.origin.url"], text=True)).strip()


def _generated_at(value: str | None) -> str:
    if value is not None:
        return value
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _changed_files(base_sha: str, head_sha: str) -> list[ChangedFile]:
    out = str(
        _git(
            ["diff", "--name-status", "--find-renames", f"{base_sha}..{head_sha}"],
            text=True,
        )
    )

    rows: list[ChangedFile] = []
    for raw in out.splitlines():
        line = raw.strip()
        if not line:
            continue

        parts = line.split("\t")
        status_token = parts[0]
        status = status_token[0]

        if status == "R":
            if len(parts) < 3:
                raise RuntimeError(f"invalid rename row from git diff: {raw}")
            path = parts[2]
        else:
            if len(parts) < 2:
                raise RuntimeError(f"invalid diff row from git diff: {raw}")
            path = parts[1]

        file_sha = None if status == "D" else _blob_sha256(head_sha, path)
        rows.append(ChangedFile(path=path, status=status, sha256=file_sha))

    rows.sort(key=lambda row: (row.path, row.status))
    return rows


def _blob_sha256(head_sha: str, path: str) -> str:
    blob = _git(["show", f"{head_sha}:{path}"], text=False)
    return hashlib.sha256(blob).hexdigest()


def _manifest_payload(
    *,
    repo_url: str,
    base_sha: str,
    head_sha: str,
    generated_at: str,
    files: list[ChangedFile],
) -> dict[str, Any]:
    return {
        "schema": "kprovengine.changeset_manifest.v1",
        "repoUrl": repo_url,
        "baseSha": base_sha,
        "headSha": head_sha,
        "generatedAt": generated_at,
        "fileCount": len(files),
        "files": [row.to_dict() for row in files],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate_changeset_manifest",
        description="Generate deterministic changeset manifest for a git range.",
    )
    parser.add_argument("--base", required=True, help="Base SHA/ref")
    parser.add_argument("--head", required=True, help="Head SHA/ref")
    parser.add_argument(
        "--output",
        default="changeset-manifest.json",
        help="Output manifest path. Default: changeset-manifest.json",
    )
    parser.add_argument("--generated-at", default=None, help="Override generatedAt RFC3339 UTC value.")

    ns = parser.parse_args(argv)

    try:
        base_sha = _resolve_sha(ns.base)
        head_sha = _resolve_sha(ns.head)
        repo_url = _repo_url()
        files = _changed_files(base_sha, head_sha)

        payload = _manifest_payload(
            repo_url=repo_url,
            base_sha=base_sha,
            head_sha=head_sha,
            generated_at=_generated_at(ns.generated_at),
            files=files,
        )

        out_path = Path(ns.output)
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EX_SOFTWARE
    except OSError as exc:
        print(f"ERROR: failed writing output: {exc}", file=sys.stderr)
        return EX_SOFTWARE

    print(f"OK: wrote manifest to {ns.output}")
    return EX_OK


if __name__ == "__main__":
    raise SystemExit(main())
