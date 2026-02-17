from __future__ import annotations

import subprocess
import sys


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True)


def test_policy_passes_for_current_interpreter() -> None:
    # Current test runner python is whatever tox/venv provided.
    cp = run(
        [sys.executable, "scripts/check_venv_python.py", "--min", "3.11", "--max-excl", "3.13"]
    )
    assert cp.returncode == 0, (cp.stdout, cp.stderr)


def test_invalid_range_is_usage_error() -> None:
    cp = run(
        [sys.executable, "scripts/check_venv_python.py", "--min", "3.12", "--max-excl", "3.12"]
    )
    assert cp.returncode == 64, (cp.stdout, cp.stderr)
    assert "invalid range" in cp.stderr.lower()


def test_invalid_version_format_is_usage_error() -> None:
    cp = run(
        [sys.executable, "scripts/check_venv_python.py", "--min", "3.12.1", "--max-excl", "3.13"]
    )
    assert cp.returncode == 64, (cp.stdout, cp.stderr)
