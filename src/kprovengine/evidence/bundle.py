# src/kprovengine/evidence/bundle.py
from __future__ import annotations

from dataclasses import dataclass

__all__ = ["EvidenceBundleSpec"]


@dataclass(frozen=True)
class EvidenceBundleSpec:
    """
    V1 evidence bundle file contract (spec only).

    Generation is incremental in V1; the contract is stable.
    """

    manifest_json: str = "manifest.json"
    provenance_json: str = "provenance.json"
    toolchain_json: str = "toolchain.json"
    human_review_json: str = "human_review.json"
    hashes_txt: str = "hashes.txt"
    attestation_md: str = "attestation.md"
    sbom_json: str = "sbom.json"

    def all_files(self) -> tuple[str, ...]:
        return (
            self.manifest_json,
            self.provenance_json,
            self.toolchain_json,
            self.human_review_json,
            self.hashes_txt,
            self.attestation_md,
            self.sbom_json,
        )