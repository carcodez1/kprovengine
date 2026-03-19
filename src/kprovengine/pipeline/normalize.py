# src/kprovengine/pipeline/normalize.py
from __future__ import annotations

from pathlib import Path

__all__ = ["normalize"]


def normalize(src: Path, dst: Path) -> None:
    """
    Normalize source text into a deterministic UTF-8 representation.

    Behavior:
      - decode with replacement (never fails on invalid bytes)
      - normalize line endings to LF
      - strip trailing whitespace per line
      - strip UTF-8 BOM if present
      - ensure terminal newline for non-empty payloads
    """
    raw = src.read_bytes()
    text = raw.decode("utf-8", errors="replace")

    if text.startswith("\ufeff"):
        text = text[1:]

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]

    # split("\n") produces a trailing empty element when text ends with "\n".
    if lines and lines[-1] == "":
        lines = lines[:-1]

    normalized = "\n".join(lines)
    if normalized:
        normalized += "\n"

    dst.write_text(normalized, encoding="utf-8", newline="\n")
