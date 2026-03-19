from __future__ import annotations

import json
import shutil
from pathlib import Path

from kprovengine.manifest.hashing import sha256_file
from kprovengine.pipeline.run import run_pipeline
from kprovengine.types import RunInputs


def _run_with_contract(tmp_path: Path, *, run_id: str) -> Path:
    src = tmp_path / "input.txt"
    src.write_text("alpha\nbeta\n", encoding="utf-8")

    outdir = tmp_path / "runs"
    outdir.mkdir(exist_ok=True)

    result = run_pipeline(
        RunInputs(
            sources=[src],
            output_dir=outdir,
            run_id=run_id,
            evidence="ENABLED",
        )
    )
    return result.run_dir


def _parse_hashes(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        row = raw.strip()
        if not row:
            continue
        sha256, rel_path = row.split("  ", 1)
        entries[rel_path] = sha256
    return entries


def test_artifact_bundle_completeness(tmp_path: Path) -> None:
    run_dir = _run_with_contract(tmp_path, run_id="20260101T000000Z-contract")

    expected = {
        "manifest.json",
        "provenance.json",
        "human_review.json",
        "run_summary.json",
        "toolchain.json",
        "hashes.txt",
        "sbom.json",
        "attestation.md",
    }
    emitted = {path.name for path in run_dir.iterdir() if path.is_file()}
    assert expected.issubset(emitted), {"missing": sorted(expected - emitted), "emitted": sorted(emitted)}


def test_manifest_and_hashes_are_consistent(tmp_path: Path) -> None:
    run_dir = _run_with_contract(tmp_path, run_id="20260101T000001Z-contract")

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    manifest_entries = manifest["manifest"]
    hashes = _parse_hashes(run_dir / "hashes.txt")

    assert manifest_entries, "manifest must not be empty"

    for entry in manifest_entries:
        rel_path = entry["path"]
        digest = entry["sha256"]
        assert rel_path in hashes, f"hashes.txt missing {rel_path}"
        assert hashes[rel_path] == digest, f"hash mismatch for {rel_path}"

        artifact_path = run_dir / rel_path
        assert artifact_path.is_file(), f"manifest path missing on disk: {rel_path}"
        assert sha256_file(artifact_path) == digest, f"digest mismatch on disk: {rel_path}"

    assert hashes["manifest.json"] == sha256_file(run_dir / "manifest.json")


def test_toolchain_contract_emitted(tmp_path: Path) -> None:
    run_dir = _run_with_contract(tmp_path, run_id="20260101T000002Z-contract")
    payload = json.loads((run_dir / "toolchain.json").read_text(encoding="utf-8"))

    assert payload["schema_version"] == "1"
    assert payload["kprovengine"]["entrypoint"] == "cli"
    assert isinstance(payload["kprovengine"]["version"], str) and payload["kprovengine"]["version"]

    python = payload["python"]
    platform = payload["platform"]
    runtime = payload["runtime"]
    git = payload["git"]

    assert set(python.keys()) == {"implementation", "version"}
    assert set(platform.keys()) == {"machine", "release", "system"}
    assert set(runtime.keys()) == {"in_container"}
    assert set(git.keys()) == {"ref", "repo", "sha"}


def test_provenance_contains_stage_lineage(tmp_path: Path) -> None:
    run_dir = _run_with_contract(tmp_path, run_id="20260101T000003Z-contract")
    provenance = json.loads((run_dir / "provenance.json").read_text(encoding="utf-8"))

    stages = provenance["stage_lineage"]
    assert [stage["stage"] for stage in stages] == ["normalize", "parse", "extract", "render"]
    for stage in stages:
        assert stage["outputs"] == sorted(stage["outputs"])


def test_deterministic_contract_for_fixed_run_id(tmp_path: Path) -> None:
    run_id = "20260101T000004Z-deterministic"
    first_run = _run_with_contract(tmp_path, run_id=run_id)

    first_manifest = (first_run / "manifest.json").read_text(encoding="utf-8")
    first_hashes = (first_run / "hashes.txt").read_text(encoding="utf-8")
    first_summary = (first_run / "run_summary.json").read_text(encoding="utf-8")
    first_rendered = (first_run / "outputs" / "input.txt").read_text(encoding="utf-8")

    shutil.rmtree(first_run)

    second_run = _run_with_contract(tmp_path, run_id=run_id)
    assert (second_run / "manifest.json").read_text(encoding="utf-8") == first_manifest
    assert (second_run / "hashes.txt").read_text(encoding="utf-8") == first_hashes
    assert (second_run / "run_summary.json").read_text(encoding="utf-8") == first_summary
    assert (second_run / "outputs" / "input.txt").read_text(encoding="utf-8") == first_rendered
