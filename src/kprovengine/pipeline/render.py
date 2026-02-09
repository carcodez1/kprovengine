# src/kprovengine/pipeline/render.py
from __future__ import annotations

from pathlib import Path

__all__ = ["render"]


def render(src: Path, dst: Path) -> None:
    """
    V1 identity render stage.

    Copies bytes from src->dst. This keeps the pipeline deterministic and simple.
    """
    dst.write_bytes(src.read_bytes())