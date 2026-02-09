from __future__ import annotations

from .llm_base import LLMAdapter, LLMResult

try:
    from langchain.llms.base import LLM
except ImportError:
    LLM = None  # type: ignore

class LangChainLLMAdapter(LLMAdapter):
    """
    Adapter for LangChain LLMs.

    This is a *thin wrapper* that delegates to a LangChain LLM object.
    """

    def __init__(self, llm: object):
        if LLM is None:
            raise RuntimeError("langchain is not installed")
        self.llm = llm

    def name(self) -> str:
        return "langchain"

    def complete(self, prompt: str) -> LLMResult:
        result = self.llm(prompt)
        return LLMResult(content=result, raw=None)