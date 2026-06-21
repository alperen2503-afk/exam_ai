"""Normalized data returned by OCR engines."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OCRResult:
    """Engine-independent OCR output."""

    text: str
    engine: str
    latex: str | None = None
    fallback_used: bool = False
    lines: tuple[str, ...] = ()
    line_confidences: tuple[float, ...] = ()
