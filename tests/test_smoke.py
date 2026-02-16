from __future__ import annotations

import subprocess
import sys


def test_cli_help() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "kprovengine.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0

    out = proc.stdout + proc.stderr

    # argparse help contract: assert semantics, not Click-specific headings
    assert "usage:" in out
    assert "--out" in out
    assert "--evidence" in out
    assert "--no-evidence" in out
    assert "--format" in out
    assert "--version" in out
