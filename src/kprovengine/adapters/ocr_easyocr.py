from __future__ import annotations

from pathlib import Path

from .ocr_base import OCRAdapter, OCRResult

try:
    import easyocr
except ImportError:
    easyocr = None  # type: ignore

class EasyOCRAdapter(OCRAdapter):
    """
    Adapter for the EasyOCR engine.

    EasyOCR must be installed manually by the user.
    """

    def __init__(self, languages: tuple[str, ...] = ("en",)):
        if easyocr is None:
            raise RuntimeError("easyocr package is not installed")
        self.reader = easyocr.Reader(list(languages))

    def name(self) -> str:
        return "easyocr"

    def extract(self, image_path: Path) -> OCRResult:
        results = self.reader.readtext(str(image_path))
        text = "\n".join(item[1] for item in results)
        # EasyOCR does not always include confidence as a float
        return OCRResult(text=text, confidence=None)