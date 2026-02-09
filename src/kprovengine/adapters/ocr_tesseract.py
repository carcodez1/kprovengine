from __future__ import annotations

from pathlib import Path

from .ocr_base import OCRAdapter, OCRResult

try:
    import pytesseract
except ImportError:
    pytesseract = None  # type: ignore

class TesseractOCRAdapter(OCRAdapter):
    """
    Adapter for Tesseract via pytesseract.

    Tesseract binary must be present on the system and pytesseract installed.
    """

    def name(self) -> str:
        return "tesseract"

    def extract(self, image_path: Path) -> OCRResult:
        if pytesseract is None:
            raise RuntimeError("pytesseract is not installed")
        text = pytesseract.image_to_string(str(image_path))
        return OCRResult(text=text, confidence=None)
