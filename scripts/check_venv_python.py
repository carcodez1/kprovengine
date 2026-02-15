#!/usr/bin/env python3
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Final

EX_OK: Final[int] = 0
EX_FAIL: Final[int] = 1


@dataclass(frozen=True)
class Policy:
    allowed: tuple[tuple[int, int], ...] = ((3, 11), (3, 12))


def main() -> int:
    v = sys.version_info
    cur = (v.major, v.minor)
    if cur not in Policy().allowed:
        print(
            f"ERROR: venv python must be 3.11 or 3.12; got {sys.version.split()[0]}",
            file=sys.stderr,
        )
        return EX_FAIL
    return EX_OK


if __name__ == "__main__":
    raise SystemExit(main())
