# src/kprovengine/adapters/llm_ollama.py
from __future__ import annotations

from .llm_base import LLMAdapter, LLMResult

__all__ = ["OllamaAdapter"]


class OllamaAdapter(LLMAdapter):
    """
    V1 placeholder adapter.

    Local-first contract only. No network calls are performed in V1.
    """

    def name(self) -> str:
        return "ollama"

    def complete(self, prompt: str) -> LLMResult:
        raise NotImplementedError("Ollama adapter is V1 placeholder; implement in adapters layer in V1+ increment.")
