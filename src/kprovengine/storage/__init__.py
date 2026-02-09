from __future__ import annotations

from pathlib import Path

from .layout import RunLayout

__all__ = ["RunLayout"]

# Useful alias for backwards compatibility
PathLike = Path | str
