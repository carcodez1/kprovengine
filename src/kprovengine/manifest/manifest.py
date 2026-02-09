# src/kprovengine/manifest/manifest.py
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .hashing import sha256_file

__all__ = ["Manifest", "ManifestEntry", "build_manifest"]


@dataclass(frozen=True)
class ManifestEntry:
    path: str
    sha256: str


@dataclass(frozen=True)
class Manifest:
    manifest: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return {"manifest": self.manifest}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def build_manifest(paths: Iterable[Path]) -> Manifest:
    entries: list[dict[str, str]] = []
    for p in paths:
        entries.append({"path": str(p), "sha256": sha256_file(p)})
    return Manifest(manifest=entries)