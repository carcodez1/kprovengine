# src/kprovengine/pipeline/normalize.py
from __future__ import annotations

from pathlib import Path

__all__ = ["normalize"]


def normalize(src: Path, dst: Path) -> None:
    """
    V1 identity normalize stage.

    In later versions, this may canonicalize formats; V1 copies bytes only.
    """
    dst.write_bytes(src.read_bytes())
