#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Final

EX_OK: Final[int] = 0
EX_FAIL: Final[int] = 1


@dataclass(frozen=True)
class Policy:
    min_inclusive: tuple[int, int]
    max_exclusive: tuple[int, int]


def _parse_mm(s: str) -> tuple[int, int]:
    parts = s.strip().split(".")
    if len(parts) != 2:
        raise ValueError(f"expected MAJOR.MINOR, got '{s}'")
    major = int(parts[0])
    minor = int(parts[1])
    return (major, minor)


def _mm(v: sys.version_info) -> tuple[int, int]:
    return (v.major, v.minor)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="check_venv_python",
        description="Enforce venv Python version policy for kprovengine (V1 LOCKED).",
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

    ns = ap.parse_args(argv)

    try:
        pol = Policy(min_inclusive=_parse_mm(ns.min), max_exclusive=_parse_mm(ns.max_excl))
    except Exception as e:
        print(f"ERROR: invalid version flag: {e}", file=sys.stderr)
        return EX_FAIL

    cur = _mm(sys.version_info)
    if not (cur >= pol.min_inclusive and cur < pol.max_exclusive):
        cur_str = sys.version.split()[0]
        print(
            f"ERROR: venv python must be >={ns.min},<{ns.max_excl}; got {cur_str}",
            file=sys.stderr,
        )
        return EX_FAIL

    return EX_OK


if __name__ == "__main__":
    raise SystemExit(main())
