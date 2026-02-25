from __future__ import annotations

import runpy
import sys
from collections.abc import Sequence

from pytest import CaptureFixture


def _run_as_module(argv: Sequence[str]) -> int:
    """
    Execute `python -m kprovengine ...` in-process so pytest-cov captures coverage
    for __main__.py and cli.py.

    Returns:
        The SystemExit code (0 for success, nonzero for failures).
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
    """
    Return combined stdout/stderr as a single string.

    We type capsys explicitly so Pylance/pyright knows captured.out/err are str.
    """
    captured = capsys.readouterr()
    return f"{captured.out}\n{captured.err}"


def test_module_help_exits_zero_and_prints_usage(capsys: CaptureFixture[str]) -> None:
    code = _run_as_module(["--help"])
    assert code == 0

    out = _captured_text(capsys).lower()
    # Keep flexible across CLI frameworks.
    assert "usage:" in out or "help" in out or "options" in out


def test_module_version_with_required_source_exits_zero(capsys: CaptureFixture[str]) -> None:
    """
    Your CLI defines --version but still requires positional 'source'.
    Provide a dummy source value to avoid EX_USAGE-style failures.
    """
    code = _run_as_module(["--version", "dummy-source"])
    assert code == 0

    out = _captured_text(capsys).strip()
    assert out, "expected non-empty version output"


def test_module_missing_required_source_exits_nonzero(capsys: CaptureFixture[str]) -> None:
    """
    Validate the error path deterministically: missing positional 'source' should fail.
    Accept common exit codes (argparse uses 2; sysexits EX_USAGE is 64).
    """
    code = _run_as_module([])
    assert code in (2, 64, 1)

    out = _captured_text(capsys).lower()
    assert "required" in out or "usage:" in out or "error" in out
