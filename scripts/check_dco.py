#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Final

EX_OK: Final[int] = 0
EX_USAGE: Final[int] = 64
EX_SOFTWARE: Final[int] = 70
EX_FAIL: Final[int] = 1

_SIGNOFF_RE = re.compile(r"^Signed-off-by:\s*(?P<name>.+?)\s*<(?P<email>[^>]+)>\s*$", re.IGNORECASE)
_ZERO_SHA = "0" * 40


@dataclass(frozen=True)
class CommitInfo:
    sha: str
    author_name: str
    author_email: str
    body: str


@dataclass(frozen=True)
class Violation:
    sha: str
    reason: str


def _git(args: list[str]) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError as exc:
        raise RuntimeError(f"failed to execute git {' '.join(args)}: {exc}") from exc

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr}")
    return (proc.stdout or "").strip()


def _resolve_sha(ref: str) -> str:
    return _git(["rev-parse", ref]).strip()


def _commit_shas(base: str | None, head: str) -> list[str]:
    resolved_head = _resolve_sha(head)

    if base and base.strip() and base != _ZERO_SHA:
        resolved_base = _resolve_sha(base)
        if resolved_base != resolved_head:
            out = _git(["rev-list", "--reverse", f"{resolved_base}..{resolved_head}"])
            shas = [line.strip() for line in out.splitlines() if line.strip()]
            if shas:
                return shas

    out = _git(["rev-list", "--max-count", "1", resolved_head])
    single = [line.strip() for line in out.splitlines() if line.strip()]
    return single


def _commit_info(sha: str) -> CommitInfo:
    out = _git(["show", "--no-patch", "--format=%H%x1f%an%x1f%ae%x1f%B", sha])
    parts = out.split("\x1f", 3)
    if len(parts) != 4:
        raise RuntimeError(f"unexpected git show payload for {sha}")
    return CommitInfo(
        sha=parts[0].strip(),
        author_name=parts[1].strip(),
        author_email=parts[2].strip(),
        body=parts[3],
    )


def _signed_off_emails(message: str) -> list[str]:
    emails: list[str] = []
    for raw in message.splitlines():
        match = _SIGNOFF_RE.match(raw.strip())
        if not match:
            continue
        emails.append(match.group("email").strip().casefold())
    return emails


def _validate_commits(base: str | None, head: str) -> tuple[list[CommitInfo], list[Violation]]:
    commits = [_commit_info(sha) for sha in _commit_shas(base, head)]
    violations: list[Violation] = []

    for commit in commits:
        signoff_emails = _signed_off_emails(commit.body)
        if not signoff_emails:
            violations.append(Violation(sha=commit.sha, reason="missing Signed-off-by trailer"))
            continue

        if commit.author_email:
            author_email = commit.author_email.casefold()
            if author_email not in signoff_emails:
                violations.append(
                    Violation(
                        sha=commit.sha,
                        reason=(
                            "Signed-off-by email does not match commit author email "
                            f"({commit.author_email})"
                        ),
                    )
                )

    return commits, violations


def _default_base() -> str | None:
    return os.getenv("GITHUB_BASE_SHA")


def _default_head() -> str:
    return os.getenv("GITHUB_HEAD_SHA") or os.getenv("GITHUB_SHA") or "HEAD"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_dco",
        description="Validate Signed-off-by trailers for commits in a range.",
    )
    parser.add_argument("--base", default=_default_base(), help="Base commit SHA/ref (optional).")
    parser.add_argument("--head", default=_default_head(), help="Head commit SHA/ref. Default: HEAD")

    ns = parser.parse_args(argv)

    try:
        commits, violations = _validate_commits(ns.base, ns.head)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EX_SOFTWARE

    if not commits:
        print("ERROR: no commits found for DCO check", file=sys.stderr)
        return EX_FAIL

    if violations:
        for violation in violations:
            print(f"FAIL: {violation.sha}: {violation.reason}", file=sys.stderr)
        print(
            "FAIL: DCO check failed. Use 'git commit -s' and ensure sign-off email matches author.",
            file=sys.stderr,
        )
        return EX_FAIL

    print(f"OK: DCO check passed for {len(commits)} commit(s)")
    return EX_OK


if __name__ == "__main__":
    raise SystemExit(main())
