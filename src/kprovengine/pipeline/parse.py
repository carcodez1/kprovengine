# src/kprovengine/pipeline/parse.py
from __future__ import annotations

from pathlib import Path

__all__ = ["parse"]


def parse(src: Path, dst: Path) -> None:
    """
    V1 identity parse stage.

    No parsing is performed in V1; bytes are copied only.
    """
    dst.write_bytes(src.read_bytes())
