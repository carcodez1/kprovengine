# src/kprovengine/pipeline/extract.py
from __future__ import annotations

from pathlib import Path

__all__ = ["extract"]


def extract(src: Path, dst: Path) -> None:
    """
    V1 identity extract stage.

    This is intentionally a no-op transformation beyond copying bytes from src->dst.
    No semantic guarantees are made.
    """
    dst.write_bytes(src.read_bytes())