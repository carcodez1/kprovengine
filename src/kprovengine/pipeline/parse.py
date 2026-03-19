# src/kprovengine/pipeline/parse.py
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["parse"]


def parse(src: Path, dst: Path) -> None:
    """
    Parse normalized text into a deterministic line-structured JSON document.
    """
    text = src.read_text(encoding="utf-8")
    lines = text.splitlines()

    payload = {
        "schema": "kprovengine.parse.v1",
        "source_name": src.name,
        "line_count": len(lines),
        "lines": [
            {
                "line_no": index,
                "text": value,
            }
            for index, value in enumerate(lines, start=1)
        ],
    }

    dst.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
