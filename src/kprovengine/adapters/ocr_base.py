from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

__all__ = ["OCRAdapter", "OCRResult"]


@dataclass(frozen=True)
class OCRResult:
    """
    A minimal result from an OCR extraction.

    text: the raw text extracted (no semantic structure claimed),
    confidence: optional confidence if provided by an adapter.
    """
    text: str
    confidence: float | None = None


class OCRAdapter(ABC):
    """
    Base class for OCR adapters.

    This defines the interface only. V1 adapters must subclass this
    and implement the required methods.

    Implementations should not be imported automatically at module import
    time: users decide which adapters to install.
    """

    @abstractmethod
    def name(self) -> str:
        """
        Return a unique name for this adapter.

        Example: "easyocr", "tesseract".
        """
        pass

    @abstractmethod
    def extract(self, image_path: Path) -> OCRResult:
        """
        Extract text from the given file.

        Args:
            image_path: local file path

        Returns:
            OCRResult with extracted text
        """
        pass