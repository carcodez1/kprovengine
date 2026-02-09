# tests/integration/test_cli_smoke.py
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_cli_help() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "kprovengine.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0


def test_cli_runs(tmp_path: Path) -> None:
    src = tmp_path / "in.txt"
    src.write_text("abc", encoding="utf-8")

    outdir = tmp_path / "runs"
    proc = subprocess.run(
        [sys.executable, "-m", "kprovengine.cli", str(src), "--out", str(outdir), "--no-evidence"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    out = proc.stdout + proc.stderr
    assert "run_id=" in out
    assert "run_dir=" in out
    assert "outputs:" in out
