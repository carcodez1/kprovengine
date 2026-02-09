# tests/unit/test_storage_layout.py
from __future__ import annotations

from pathlib import Path

from kprovengine.storage.layout import RunLayout


def test_run_dir_properties(tmp_path: Path) -> None:
    rl = RunLayout(tmp_path, "run0")
    assert rl.run_dir == tmp_path / "run0"

    expected_files = {
        "manifest": rl.manifest_path,
        "provenance": rl.provenance_path,
        "toolchain": rl.toolchain_path,
        "human_review": rl.human_review_path,
        "hashes": rl.hashes_txt_path,
        "attestation": rl.attestation_path,
        "sbom": rl.sbom_path,
    }
    for _label, p in expected_files.items():
        assert isinstance(p, Path)


def test_ensure_and_cleanup(tmp_path: Path) -> None:
    rl = RunLayout(tmp_path, "run1")
    run_dir = rl.ensure_run_dir()
    assert run_dir.exists()

    f = run_dir / "dummy.txt"
    f.write_text("x", encoding="utf-8")
    assert f.exists()

    rl.cleanup()
    assert not f.exists()
