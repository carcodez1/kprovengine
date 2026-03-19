#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Final

EX_OK: Final[int] = 0
EX_USAGE: Final[int] = 64
EX_FAIL: Final[int] = 1
EX_SOFTWARE: Final[int] = 70

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


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


def _repo_url() -> str:
    return str(_git(["config", "--get", "remote.origin.url"], text=True)).strip()


def _blob_sha256(head_sha: str, path: str) -> str:
    blob = _git(["show", f"{head_sha}:{path}"], text=False)
    return hashlib.sha256(blob).hexdigest()


def _changed_files(base_sha: str, head_sha: str) -> list[dict[str, str | None]]:
    out = str(
        _git(
            ["diff", "--name-status", "--find-renames", f"{base_sha}..{head_sha}"],
            text=True,
        )
    )

    rows: list[dict[str, str | None]] = []
    for raw in out.splitlines():
        line = raw.strip()
        if not line:
            continue

        parts = line.split("\t")
        status = parts[0][0]

        if status == "R":
            if len(parts) < 3:
                raise RuntimeError(f"invalid rename row from git diff: {raw}")
            path = parts[2]
        else:
            if len(parts) < 2:
                raise RuntimeError(f"invalid diff row from git diff: {raw}")
            path = parts[1]

        digest = None if status == "D" else _blob_sha256(head_sha, path)
        rows.append({"path": path, "status": status, "sha256": digest})

    rows.sort(key=lambda row: (str(row["path"]), str(row["status"])))
    return rows


def _validate_generated_at(value: str) -> None:
    if not _RFC3339_UTC_RE.fullmatch(value):
        raise ValueError(f"generatedAt must be RFC3339 UTC second precision, got '{value}'")
    datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def _validate_manifest_structure(payload: dict[str, Any]) -> None:
    required = {"repoUrl", "baseSha", "headSha", "generatedAt", "files"}
    missing = sorted(required - set(payload.keys()))
    if missing:
        raise ValueError(f"manifest missing required keys: {missing}")

    base_sha = str(payload["baseSha"])
    head_sha = str(payload["headSha"])
    if not _SHA_RE.fullmatch(base_sha) or not _SHA_RE.fullmatch(head_sha):
        raise ValueError("baseSha/headSha must be 40-char lowercase hex commit IDs")

    _validate_generated_at(str(payload["generatedAt"]))

    files = payload["files"]
    if not isinstance(files, list):
        raise ValueError("files must be a list")

    for row in files:
        if not isinstance(row, dict):
            raise ValueError("each files entry must be an object")
        if not isinstance(row.get("path"), str) or not row.get("path"):
            raise ValueError("files entry path must be a non-empty string")
        if not isinstance(row.get("status"), str) or len(str(row.get("status"))) != 1:
            raise ValueError("files entry status must be a single-character string")

        digest = row.get("sha256")
        if digest is None:
            if row.get("status") != "D":
                raise ValueError("non-deleted files must include sha256")
        elif not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("sha256 must be 64-char lowercase hex or null for deleted files")


def _verify_cosign_bundle(
    manifest_path: Path,
    bundle_path: Path,
    identity: str,
    issuer: str,
) -> None:
    try:
        proc = subprocess.run(
            [
                "cosign",
                "verify-blob",
                "--bundle",
                str(bundle_path),
                "--certificate-identity",
                identity,
                "--certificate-oidc-issuer",
                issuer,
                str(manifest_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError as exc:
        raise RuntimeError(f"failed to execute cosign: {exc}") from exc

    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "cosign verify-blob failed").strip()
        raise RuntimeError(msg)


def _canonical_files(rows: list[dict[str, Any]]) -> list[dict[str, str | None]]:
    normalized: list[dict[str, str | None]] = []
    for row in rows:
        normalized.append(
            {
                "path": str(row["path"]),
                "status": str(row["status"]),
                "sha256": None if row.get("sha256") is None else str(row.get("sha256")),
            }
        )
    normalized.sort(key=lambda item: (str(item["path"]), str(item["status"])))
    return normalized


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="verify_changeset_manifest",
        description="Verify changeset manifest content and optional cosign bundle.",
    )
    parser.add_argument("--manifest", required=True, help="Path to manifest JSON")
    parser.add_argument("--bundle", default=None, help="Optional cosign bundle path")
    parser.add_argument(
        "--certificate-identity",
        default=None,
        help="Required when --bundle is set: expected certificate identity",
    )
    parser.add_argument(
        "--certificate-oidc-issuer",
        default=None,
        help="Required when --bundle is set: expected OIDC issuer",
    )

    ns = parser.parse_args(argv)

    manifest_path = Path(ns.manifest)
    if not manifest_path.is_file():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        return EX_USAGE

    if ns.bundle and (not ns.certificate_identity or not ns.certificate_oidc_issuer):
        print(
            "ERROR: --bundle requires --certificate-identity and --certificate-oidc-issuer",
            file=sys.stderr,
        )
        return EX_USAGE

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("manifest root must be a JSON object")

        _validate_manifest_structure(payload)

        current_repo_url = _repo_url()
        manifest_repo_url = str(payload["repoUrl"])
        if manifest_repo_url != current_repo_url:
            raise ValueError(
                "repoUrl mismatch between manifest and repository "
                f"({manifest_repo_url} != {current_repo_url})"
            )

        base_sha = str(payload["baseSha"])
        head_sha = str(payload["headSha"])

        expected_files = _changed_files(base_sha, head_sha)
        actual_files = _canonical_files(list(payload["files"]))
        if actual_files != expected_files:
            raise ValueError("manifest files list or sha256 values do not match git range")

        if ns.bundle:
            _verify_cosign_bundle(
                manifest_path,
                Path(ns.bundle),
                str(ns.certificate_identity),
                str(ns.certificate_oidc_issuer),
            )
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return EX_FAIL
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return EX_FAIL
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EX_SOFTWARE

    print("OK: changeset manifest verification passed")
    return EX_OK


if __name__ == "__main__":
    raise SystemExit(main())
