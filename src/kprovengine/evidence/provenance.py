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
    stage_lineage: list[dict[str, Any]] | None = None
    toolchain_path: str | None = None

    @classmethod
    def from_paths(
        cls,
        run_id: str,
        inputs: Sequence[Path],
        outputs: Sequence[Path],
        *,
        timestamp: str | None = None,
        stage_lineage: list[dict[str, Any]] | None = None,
        toolchain_path: str | None = None,
    ) -> ProvenanceRecord:
        return cls(
            run_id=run_id,
            inputs=[str(p) for p in inputs],
            outputs=[str(p) for p in outputs],
            timestamp=timestamp or _now_utc_iso(),
            stage_lineage=stage_lineage,
            toolchain_path=toolchain_path,
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "run_id": self.run_id,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "timestamp": self.timestamp,
        }
        if self.stage_lineage is not None:
            payload["stage_lineage"] = self.stage_lineage
        if self.toolchain_path is not None:
            payload["toolchain_path"] = self.toolchain_path
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _now_utc_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
