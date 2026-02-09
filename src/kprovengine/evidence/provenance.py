# src/kprovengine/evidence/provenance.py
from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__all__ = ["ProvenanceRecord"]


@dataclass(frozen=True)
class ProvenanceRecord:
    run_id: str
    inputs: list[str]
    outputs: list[str]
    timestamp: str

    @classmethod
    def from_paths(cls, run_id: str, inputs: Sequence[Path], outputs: Sequence[Path]) -> ProvenanceRecord:
        return cls(
            run_id=run_id,
            inputs=[str(p) for p in inputs],
            outputs=[str(p) for p in outputs],
            timestamp=_now_utc_iso(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _now_utc_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
