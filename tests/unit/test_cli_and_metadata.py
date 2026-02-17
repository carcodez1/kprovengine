# tests/unit/test_cli_and_metadata.py
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_cli_runs(tmp_path: Path) -> None:
    src = tmp_path / "in.txt"
    src.write_text("abc", encoding="utf-8")

    p = subprocess.run(
        [sys.executable, "-m", "kprovengine.cli", str(src), "--no-evidence"],
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, f"stdout={p.stdout!r}\nstderr={p.stderr!r}"
