from __future__ import annotations

import runpy
import sys
from collections.abc import Sequence
from pathlib import Path

from pytest import CaptureFixture


def _run_kprovengine_as_module(argv: Sequence[str]) -> int:
    """
    Execute `python -m kprovengine ...` in-process so pytest-cov captures coverage
    for __main__.py and cli.py.

    Returns:
        Exit code (0 for success).
    """
    old_argv = sys.argv[:]
    try:
        sys.argv = ["kprovengine", *argv]
        try:
            runpy.run_module("kprovengine", run_name="__main__")
        except SystemExit as e:
            code = e.code
            if code is None:
                return 0
            if isinstance(code, int):
                return code
            return 1
        return 0
    finally:
        sys.argv = old_argv


def _captured_text(capsys: CaptureFixture[str]) -> str:
    captured = capsys.readouterr()
    return f"{captured.out}\n{captured.err}"


def test_cli_happy_path_writes_output_file(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    """
    Exercise the main CLI flow (not just help/version) to cover the large missed blocks
    in src/kprovengine/cli.py.

    We provide:
      - a real source file path
      - an explicit --out path
      - --no-evidence to avoid any toolchain/evidence side effects
      - --format json to take the structured output path
    """
    source = tmp_path / "source.txt"
    source.write_text("hello\n", encoding="utf-8")

    out = tmp_path / "out.json"

    code = _run_kprovengine_as_module(
        ["--out", str(out), "--no-evidence", "--format", "json", str(source)]
    )
    assert code == 0, _captured_text(capsys)

    assert out.exists(), "expected CLI to create --out file"
    assert out.stat().st_size > 0, "expected --out file to be non-empty"
