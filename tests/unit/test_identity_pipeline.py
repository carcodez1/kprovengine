# tests/unit/test_identity_pipeline.py
from __future__ import annotations

import json
from pathlib import Path

from kprovengine.pipeline.run import run_pipeline
from kprovengine.types import RunInputs


def test_identity_pipeline_end_to_end(tmp_path: Path) -> None:
    src = tmp_path / "input.txt"
    src.write_text("abc", encoding="utf-8")

    outdir = tmp_path / "runs"
    outdir.mkdir()

    res = run_pipeline(
        RunInputs(
            sources=[src],
            output_dir=outdir,
            evidence="ENABLED",
        )
    )

    assert res.run_id
    assert res.run_dir.exists()
    assert res.started_at is not None
    assert res.finished_at is not None

    # Render stage now emits deterministic structured JSON output.
    assert res.outputs, "pipeline must return at least one output path"
    rendered = res.outputs[0]
    assert rendered.exists()
    rendered_payload = json.loads(rendered.read_text(encoding="utf-8"))
    assert rendered_payload["schema"] == "kprovengine.render.v1"
    assert rendered_payload["rendered_text"] == "abc"

    # Evidence artifacts (full runtime contract)
    assert (res.run_dir / "manifest.json").exists()
    assert (res.run_dir / "provenance.json").exists()
    assert (res.run_dir / "human_review.json").exists()
    assert (res.run_dir / "run_summary.json").exists()
    assert (res.run_dir / "toolchain.json").exists()
    assert (res.run_dir / "hashes.txt").exists()
    assert (res.run_dir / "sbom.json").exists()
    assert (res.run_dir / "attestation.md").exists()

    # Evidence dir is a mode flag; contents are incremental in V1.
    assert res.evidence_dir is not None
    assert res.evidence_dir.exists()
