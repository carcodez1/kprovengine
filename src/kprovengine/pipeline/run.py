# src/kprovengine/pipeline/run.py
from __future__ import annotations

import json
import logging
import secrets
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from kprovengine.evidence.human_review import HumanReview
from kprovengine.evidence.provenance import ProvenanceRecord
from kprovengine.manifest.manifest import build_manifest
from kprovengine.storage.layout import RunLayout
from kprovengine.types import RunInputs, RunResult

logger = logging.getLogger(__name__)

RUN_SUMMARY_SCHEMA = "kprovengine.run_summary.v1"


def run_pipeline(inputs: RunInputs) -> RunResult:
    """
    V1 pipeline scaffold:
      1) normalize (identity copy)
      2) parse      (identity copy)
      3) extract    (identity copy)
      4) render     (identity copy)

    Writes a minimal, review-safe run_summary.json plus manifest/provenance/review stubs.
    No OCR/LLM guarantees are claimed in V1.
    """
    if not inputs.sources:
        raise ValueError("No source paths provided.")

    sources = [Path(p) for p in inputs.sources]
    for p in sources:
        if not p.exists():
            raise FileNotFoundError(f"Source path not found: {p}")

    started_at = datetime.now(UTC)
    run_id = inputs.run_id or _gen_run_id()

    layout = RunLayout(inputs.output_dir, run_id)
    layout.ensure_run_dir()

    # Stage directories prevent SameFileError when inputs are already inside out_dir.
    stages_dir = layout.run_dir / "stages"
    normalized_dir = stages_dir / "normalized"
    parsed_dir = stages_dir / "parsed"
    extracted_dir = stages_dir / "extracted"
    rendered_dir = layout.run_dir / "outputs"  # stable final location for V1

    for d in (normalized_dir, parsed_dir, extracted_dir, rendered_dir):
        d.mkdir(parents=True, exist_ok=True)

    normalized = normalize_files(sources, normalized_dir)
    parsed = parse_files(normalized, parsed_dir)
    extracted = extract_records(parsed, extracted_dir)
    rendered = render_output(extracted, rendered_dir)

    # Manifest over rendered outputs (V1).
    manifest = build_manifest(rendered)
    layout.manifest_path.write_text(manifest.to_json(), encoding="utf-8")

    # Provenance record (V1).
    prov = ProvenanceRecord.from_paths(run_id, sources, rendered)
    layout.provenance_path.write_text(prov.to_json(), encoding="utf-8")

    # Human review stub (V1).
    review = HumanReview.pending()
    layout.human_review_path.write_text(review.to_json(), encoding="utf-8")

    # Minimal run summary (this is what your smoke test is asserting on).
    finished_at = datetime.now(UTC)
    summary = {
        "schema": RUN_SUMMARY_SCHEMA,
        "run_id": run_id,
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "finished_at": finished_at.isoformat().replace("+00:00", "Z"),
        "evidence": inputs.evidence,
        "review_status": inputs.review_status,
        "sources": [str(p) for p in sources],
        "outputs": [str(p) for p in rendered],
    }
    (layout.run_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return RunResult(
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        run_dir=layout.run_dir,
        outputs=rendered,
        evidence_dir=layout.run_dir if inputs.evidence == "ENABLED" else None,
        summary=summary,
    )


def _gen_run_id() -> str:
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}-{secrets.token_hex(3)}"


def normalize_files(inputs: Sequence[Path], outdir: Path) -> list[Path]:
    from .normalize import normalize

    output_paths: list[Path] = []
    for p in inputs:
        out = outdir / p.name
        normalize(p, out)
        output_paths.append(out)
    return output_paths


def parse_files(inputs: Sequence[Path], outdir: Path) -> list[Path]:
    from .parse import parse

    output_paths: list[Path] = []
    for p in inputs:
        out = outdir / p.name
        parse(p, out)
        output_paths.append(out)
    return output_paths


def extract_records(inputs: Sequence[Path], outdir: Path) -> list[Path]:
    from .extract import extract

    output_paths: list[Path] = []
    for p in inputs:
        out = outdir / p.name
        extract(p, out)
        output_paths.append(out)
    return output_paths


def render_output(inputs: Sequence[Path], outdir: Path) -> list[Path]:
    from .render import render

    output_paths: list[Path] = []
    for p in inputs:
        out = outdir / p.name
        render(p, out)
        output_paths.append(out)
    return output_paths
