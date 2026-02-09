# tests/unit/test_adapters.py
from __future__ import annotations

from pathlib import Path

from kprovengine.adapters.llm_base import LLMAdapter, LLMResult
from kprovengine.adapters.ocr_base import OCRAdapter, OCRResult


class DummyOCR(OCRAdapter):
    def name(self) -> str:
        return "dummy"

    def extract(self, image_path: Path) -> OCRResult:
        return OCRResult(text="dummy-text")


class DummyLLM(LLMAdapter):
    def name(self) -> str:
        return "dummy"

    def complete(self, prompt: str) -> LLMResult:
        return LLMResult(content="ok")


def test_dummy_ocr_adapter() -> None:
    d = DummyOCR()
    assert d.name() == "dummy"
    result = d.extract(Path("/tmp"))
    assert isinstance(result.text, str)


def test_dummy_llm_adapter() -> None:
    d = DummyLLM()
    assert d.name() == "dummy"
    out = d.complete("x")
    assert isinstance(out.content, str)
