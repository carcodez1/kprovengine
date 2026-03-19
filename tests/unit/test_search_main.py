from __future__ import annotations

import runpy
import sys

import pytest

import kprovengine.search.service as search_service


def test_search_main_delegates_to_service_main(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_main(argv: list[str] | None = None) -> int:
        captured["argv"] = argv
        return 17

    monkeypatch.setattr(search_service, "main", fake_main)

    old_argv = sys.argv[:]
    try:
        sys.argv = ["kprovengine.search", "--query", "audit"]
        with pytest.raises(SystemExit) as exc:
            runpy.run_module("kprovengine.search.__main__", run_name="__main__")
    finally:
        sys.argv = old_argv

    assert exc.value.code == 17
    assert captured["argv"] == ["--query", "audit"]
