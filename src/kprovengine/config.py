from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KProvConfig:
    """
    Runtime configuration. V1: minimal; keep deterministic and local-first.

    NOTE: Do not add network endpoints, remote APIs, or orchestration knobs in V1.
    """

    work_dir: Path
    default_runs_dirname: str = "runs"
    hash_algo: str = "sha256"