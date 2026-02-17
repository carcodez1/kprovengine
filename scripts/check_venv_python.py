#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from typing import Final

EX_OK: Final[int] = 0
EX_USAGE: Final[int] = 64  # bad CLI usage / invalid flags (sysexits-ish)
EX_SOFTWARE: Final[int] = 70  # internal error
EX_FAIL: Final[int] = 1  # policy violation


@dataclass(frozen=True)
class Policy:
    min_inclusive: tuple[int, int]
    max_exclusive: tuple[int, int]


def _parse_mm(s: str) -> tuple[int, int]:
    raw = s.strip()
    parts = raw.split(".")
    if len(parts) != 2:
        raise ValueError(f"expected MAJOR.MINOR, got '{s}'")

    major_s, minor_s = parts
    if not major_s.isdigit() or not minor_s.isdigit():
        raise ValueError(f"expected numeric MAJOR.MINOR, got '{s}'")

    major = int(major_s)
    minor = int(minor_s)
    if major < 0 or minor < 0:
        raise ValueError(f"version cannot be negative: '{s}'")

    return (major, minor)


def _mm_from_running() -> tuple[int, int]:
    v = sys.version_info
    return (v.major, v.minor)


def _mm_from_python_exe(python_exe: str) -> tuple[int, int]:
    """
    Query MAJOR.MINOR from an arbitrary python executable without importing any deps.
    """
    try:
        out = subprocess.check_output(
            [python_exe, "-c", "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except FileNotFoundError as e:
        raise ValueError(f"python not found: {python_exe}") from e
    except subprocess.CalledProcessError as e:
        raise ValueError(f"failed to run python '{python_exe}': {e.output.strip()}") from e

    return _parse_mm(out)


def _validate_policy(pol: Policy) -> None:
    if pol.min_inclusive >= pol.max_exclusive:
        raise ValueError(
            f"invalid range: min {pol.min_inclusive} must be < max-excl {pol.max_exclusive}"
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="check_venv_python",
        description="Enforce Python version policy (>=min,<max-excl) for kprovengine (V1 LOCKED).",
    )
    ap.add_argument(
        "--min",
        required=True,
        help="Minimum supported Python version (inclusive), MAJOR.MINOR (e.g. 3.11).",
    )
    ap.add_argument(
        "--max-excl",
        required=True,
        help="Maximum supported Python version (exclusive), MAJOR.MINOR (e.g. 3.13).",
    )
    ap.add_argument(
        "--python",
        default=None,
        help="Optional path to python executable to validate (defaults to current interpreter).",
    )

    ns = ap.parse_args(argv)

    try:
        pol = Policy(min_inclusive=_parse_mm(ns.min), max_exclusive=_parse_mm(ns.max_excl))
        _validate_policy(pol)
    except ValueError as e:
        print(f"ERROR: invalid policy: {e}", file=sys.stderr)
        return EX_USAGE
    except Exception as e:
        print(f"ERROR: unexpected while parsing policy: {e}", file=sys.stderr)
        return EX_SOFTWARE

    try:
        cur = _mm_from_python_exe(ns.python) if ns.python else _mm_from_running()
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EX_USAGE
    except Exception as e:
        print(f"ERROR: unexpected while reading python version: {e}", file=sys.stderr)
        return EX_SOFTWARE

    if not (cur >= pol.min_inclusive and cur < pol.max_exclusive):
        cur_str = f"{cur[0]}.{cur[1]}"
        print(
            f"ERROR: python must be >={ns.min},<{ns.max_excl}; got {cur_str}",
            file=sys.stderr,
        )
        return EX_FAIL

    return EX_OK


if __name__ == "__main__":
    raise SystemExit(main())
