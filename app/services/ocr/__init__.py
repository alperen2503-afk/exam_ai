"""OCR engines and fallback orchestration."""

from app.services.ocr.models import OCRResult
from app.services.ocr.ocr_service import OCRService, get_ocr_service

__all__ = ["OCRResult", "OCRService", "get_ocr_service"]
