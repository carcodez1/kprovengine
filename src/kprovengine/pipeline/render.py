# src/kprovengine/pipeline/render.py
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["render"]


def render(src: Path, dst: Path) -> None:
    """
    Render extracted records into a stable JSON output payload.
    """
    extracted = json.loads(src.read_text(encoding="utf-8"))
    records = extracted.get("records", [])

    rendered_text = "\n".join(str(record.get("text", "")) for record in records)
    payload = {
        "schema": "kprovengine.render.v1",
        "source_name": extracted.get("source_name", src.name),
        "record_count": len(records),
        "rendered_text": rendered_text,
        "records": [
            {
                "record_id": record.get("record_id"),
                "line_no": record.get("line_no"),
                "text": record.get("text"),
            }
            for record in records
        ],
    }

    dst.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
