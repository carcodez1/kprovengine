# src/kprovengine/storage/layout.py
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunLayout:
    """
    Filesystem layout for a single pipeline run.

    V1 guarantees:
      - deterministic paths
      - local-only storage
      - no implicit creation except via ensure_run_dir()
    """

    base_dir: Path
    run_id: str

    @property
    def run_dir(self) -> Path:
        return self.base_dir / self.run_id

    @property
    def manifest_path(self) -> Path:
        return self.run_dir / "manifest.json"

    @property
    def provenance_path(self) -> Path:
        return self.run_dir / "provenance.json"

    @property
    def toolchain_path(self) -> Path:
        return self.run_dir / "toolchain.json"

    @property
    def human_review_path(self) -> Path:
        return self.run_dir / "human_review.json"

    @property
    def hashes_txt_path(self) -> Path:
        return self.run_dir / "hashes.txt"

    @property
    def attestation_path(self) -> Path:
        return self.run_dir / "attestation.md"

    @property
    def sbom_path(self) -> Path:
        return self.run_dir / "sbom.json"

    def ensure_run_dir(self) -> Path:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        return self.run_dir

    def cleanup(self) -> None:
        if self.run_dir.exists():
            shutil.rmtree(self.run_dir)
