from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LLMResult:
    """
    A single LLM output, with optional raw metadata.

    `content`: the model’s primary output string.
    `raw`: any raw response data, opaque to V1 and for future introspection.
    """
    content: str
    raw: dict[str, Any] | None = None


class LLMAdapter(ABC):
    """
    Base adapter for language model completion.

    This defines the interface for adapters that invoke a model or
    LLM-like completion mechanism.

    For V1, concrete implementations are optional; no network calls are
    executed unless an adapter is explicitly instantiated.
    """

    @abstractmethod
    def name(self) -> str:
        """Return a unique identifier for this adapter."""
        pass

    @abstractmethod
    def complete(self, prompt: str) -> LLMResult:
        """
        Complete the given prompt.

        Args:
            prompt: text to complete.

        Returns:
            An LLMResult containing response content and optional metadata.
        """
        pass