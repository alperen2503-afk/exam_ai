"""Common OCR engine contract."""

from pathlib import Path
from typing import Protocol

from app.services.ocr.models import OCRResult


class OCREngine(Protocol):
    """Interface implemented by all OCR providers."""

    name: str

    def extract(self, image_path: Path) -> OCRResult:
        """Extract text and optional LaTeX from an image."""
        ...
