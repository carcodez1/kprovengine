from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_smoke_imports() -> None:
    import kprovengine  # noqa: F401


def test_cli_help() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "kprovengine.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "Options:" in (proc.stdout + proc.stderr)


def test_cli_run_creates_summary(tmp_path: Path) -> None:
    src = tmp_path / "input.txt"
    src.write_text("hello\n", encoding="utf-8")

    out_dir = tmp_path / "runs"
    proc = subprocess.run(
        [sys.executable, "-m", "kprovengine.cli", str(src), "--out", str(out_dir)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0

    # Find created run dir by scanning for run_summary.json
    summaries = list(out_dir.rglob("run_summary.json"))
    assert len(summaries) == 1

    data = json.loads(summaries[0].read_text(encoding="utf-8"))
    assert data["schema"] == "kprovengine.run_summary.v1"
    assert data["sources"] == [str(src)]
