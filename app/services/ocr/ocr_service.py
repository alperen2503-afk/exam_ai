"""OCR engine orchestration and fallback policy."""

from dataclasses import replace
import logging
from pathlib import Path
from typing import Sequence

from app.services.ocr.base import OCREngine
from app.services.ocr.exceptions import OCRError, OCRProcessingError
from app.services.ocr.models import OCRResult
from app.services.ocr.pix2text_service import Pix2TextService
from app.services.ocr.tesseract_service import TesseractService


logger = logging.getLogger(__name__)


class OCRService:
    """Try OCR engines in priority order until one returns a valid result."""

    def __init__(self, engines: Sequence[OCREngine]) -> None:
        if not engines:
            raise ValueError("En az bir OCR motoru yapılandırılmalıdır.")
        self._engines = tuple(engines)

    def extract(self, image_path: Path) -> OCRResult:
        """Run the OCR chain and mark results produced by a fallback engine."""
        failures: list[str] = []
        for index, engine in enumerate(self._engines):
            try:
                result = engine.extract(image_path)
                if not result.text.strip():
                    raise OCRError("OCR motoru boş sonuç döndürdü.")
                return replace(result, fallback_used=index > 0)
            except OCRError as exc:
                failures.append(f"{engine.name}: {exc}")
                logger.warning("OCR engine %s failed: %s", engine.name, exc)
            except Exception as exc:
                failures.append(f"{engine.name}: beklenmeyen hata")
                logger.exception("Unexpected OCR engine failure: %s", engine.name)

        detail = "; ".join(failures)
        raise OCRProcessingError(f"Hiçbir OCR motoru sonuç üretemedi. {detail}")


_ocr_service: OCRService | None = None


def get_ocr_service() -> OCRService:
    """Return the default Pix2Text-first OCR pipeline."""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService([Pix2TextService(), TesseractService()])
    return _ocr_service
