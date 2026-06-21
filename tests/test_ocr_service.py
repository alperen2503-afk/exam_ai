"""Tests for OCR fallback orchestration."""

from pathlib import Path
import unittest

from app.services.ocr.exceptions import OCRError, OCRProcessingError
from app.services.ocr.models import OCRResult
from app.services.ocr.ocr_service import OCRService


class FakeEngine:
    """Controllable OCR engine test double."""

    def __init__(self, name: str, result: str | Exception) -> None:
        self.name = name
        self._result = result

    def extract(self, image_path: Path) -> OCRResult:
        if isinstance(self._result, Exception):
            raise self._result
        return OCRResult(text=self._result, engine=self.name)


class OCRServiceTests(unittest.TestCase):
    def test_primary_engine_is_used_first(self) -> None:
        service = OCRService(
            [FakeEngine("primary", "x = 2"), FakeEngine("fallback", "x")]
        )

        result = service.extract(Path("question.png"))

        self.assertEqual(result.engine, "primary")
        self.assertFalse(result.fallback_used)

    def test_fallback_is_used_after_primary_failure(self) -> None:
        service = OCRService(
            [
                FakeEngine("pix2text", OCRError("failed")),
                FakeEngine("tesseract", "x = 2"),
            ]
        )

        result = service.extract(Path("question.png"))

        self.assertEqual(result.engine, "tesseract")
        self.assertTrue(result.fallback_used)

    def test_all_engine_failures_are_reported(self) -> None:
        service = OCRService(
            [
                FakeEngine("one", OCRError("failed")),
                FakeEngine("two", OCRError("failed")),
            ]
        )

        with self.assertRaisesRegex(OCRProcessingError, "Hiçbir OCR motoru"):
            service.extract(Path("question.png"))
