# src/kprovengine/pipeline/extract.py
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["extract"]


def extract(src: Path, dst: Path) -> None:
    """
    Extract deterministic records from parsed line JSON.
    """
    parsed = json.loads(src.read_text(encoding="utf-8"))
    lines = parsed.get("lines", [])

    records: list[dict[str, object]] = []
    total_chars = 0

    for index, line in enumerate(lines, start=1):
        text = str(line.get("text", ""))
        total_chars += len(text)
        records.append(
            {
                "record_id": f"line-{index:06d}",
                "line_no": int(line.get("line_no", index)),
                "text": text,
                "char_count": len(text),
            }
        )

    payload = {
        "schema": "kprovengine.extract.v1",
        "source_name": parsed.get("source_name", src.name),
        "record_count": len(records),
        "total_chars": total_chars,
        "records": records,
    }

    dst.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
