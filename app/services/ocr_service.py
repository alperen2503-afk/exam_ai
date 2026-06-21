"""Backward-compatible access to the modular OCR pipeline."""

from pathlib import Path

from app.services.ocr.ocr_service import get_ocr_service


def extract_text(image_path: str | Path) -> str:
    """Extract text using the configured OCR pipeline.

    New code should use :func:`app.services.ocr.ocr_service.get_ocr_service`
    to retain engine and LaTeX metadata.
    """
    return get_ocr_service().extract(Path(image_path)).text
