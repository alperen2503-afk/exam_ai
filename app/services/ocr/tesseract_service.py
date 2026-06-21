"""Tesseract fallback OCR optimized for worksheet-style mathematics."""

from pathlib import Path
import math
import re

import cv2
import numpy as np
import pytesseract
from pytesseract import Output

from app.core.config import Settings, settings
from app.services.ocr.exceptions import OCRError, OCRUnavailableError
from app.services.ocr.models import OCRResult


class TesseractService:
    """Fallback OCR with line segmentation and math-symbol recovery."""

    name = "tesseract"

    def __init__(self, app_settings: Settings = settings) -> None:
        self._settings = app_settings
        pytesseract.pytesseract.tesseract_cmd = app_settings.tesseract_cmd

    def extract(self, image_path: Path) -> OCRResult:
        """Recognize each visual line independently and retain confidence data."""
        image = self._read_image(image_path)
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            line_images = self._segment_lines(gray)
            lines_with_confidence = [self._recognize_line(line) for line in line_images]
        except pytesseract.TesseractNotFoundError as exc:
            raise OCRUnavailableError(
                "Tesseract bulunamadı; TESSERACT_CMD ayarını kontrol edin."
            ) from exc
        except pytesseract.TesseractError as exc:
            raise OCRError("Tesseract OCR işlemi başarısız oldu.") from exc
        except cv2.error as exc:
            raise OCRError("Görsel ön işleme sırasında OpenCV hatası oluştu.") from exc

        valid = [(text, confidence) for text, confidence in lines_with_confidence if text]
        if not valid:
            raise OCRError("Tesseract boş sonuç döndürdü.")
        lines, confidences = zip(*valid)
        return OCRResult(
            text="\n".join(lines),
            engine=self.name,
            lines=tuple(lines),
            line_confidences=tuple(confidences),
        )

    @staticmethod
    def _read_image(image_path: Path) -> np.ndarray:
        """Read Unicode Windows paths reliably through OpenCV."""
        try:
            encoded = np.fromfile(str(image_path), dtype=np.uint8)
            image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        except OSError as exc:
            raise OCRError("Görsel dosyası okunamadı.") from exc
        if image is None:
            raise OCRError("Tesseract görsel dosyasını okuyamadı.")
        return image

    @staticmethod
    def _segment_lines(gray: np.ndarray) -> list[np.ndarray]:
        """Split a worksheet image by horizontal ink projection."""
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        binary = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )[1]
        edge_width = max(2, gray.shape[1] // 50)
        edge_columns = list(range(edge_width)) + list(
            range(max(0, gray.shape[1] - edge_width), gray.shape[1])
        )
        for column in edge_columns:
            if np.count_nonzero(binary[:, column]) >= gray.shape[0] * 0.8:
                binary[:, column] = 0
        ink_per_row = np.count_nonzero(binary, axis=1)
        # Requiring at least two ink pixels ignores scanner borders and isolated
        # dust that would otherwise connect every row into one giant block.
        active_rows = np.flatnonzero(ink_per_row >= max(2, gray.shape[1] // 150))
        if active_rows.size == 0:
            return [gray]

        groups: list[tuple[int, int]] = []
        start = previous = int(active_rows[0])
        for row in active_rows[1:]:
            current = int(row)
            if current - previous > 2:
                groups.append((start, previous))
                start = current
            previous = current
        groups.append((start, previous))

        minimum_height = max(3, gray.shape[0] // 100)
        padding = max(3, gray.shape[0] // 100)
        crops: list[np.ndarray] = []
        for top, bottom in groups:
            if bottom - top + 1 < minimum_height:
                continue
            region = binary[top : bottom + 1, :]
            active_columns = np.flatnonzero(np.count_nonzero(region, axis=0) >= 2)
            if active_columns.size:
                left = max(0, int(active_columns[0]) - padding)
                right = min(gray.shape[1], int(active_columns[-1]) + padding + 1)
            else:
                left, right = 0, gray.shape[1]
            crops.append(
                gray[
                    max(0, top - padding) : min(gray.shape[0], bottom + padding + 1),
                    left:right,
                ]
            )
        return crops or [gray]

    def _recognize_line(self, gray_line: np.ndarray) -> tuple[str, float]:
        """Upscale and OCR one line, then repair visually verified division signs."""
        scale = min(6, max(3, math.ceil(48 / max(1, gray_line.shape[0]))))
        enlarged = cv2.resize(
            gray_line,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC,
        )
        binary = cv2.threshold(
            enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]
        padded = cv2.copyMakeBorder(
            binary, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255
        )
        config = "--oem 3 --psm 7 -c preserve_interword_spaces=1"
        data = pytesseract.image_to_data(
            padded,
            lang=self._settings.tesseract_language,
            config=config,
            output_type=Output.DICT,
        )
        tokens = [token.strip() for token in data["text"] if token.strip()]
        confidences = [
            float(value)
            for value, token in zip(data["conf"], data["text"])
            if token.strip() and float(value) >= 0
        ]
        text = re.sub(r"\s+", "", " ".join(tokens)).strip("|")
        division_verified = self._has_division_glyph(gray_line)
        if division_verified:
            text = self._restore_division(text)
        confidence = (sum(confidences) / len(confidences) / 100) if confidences else 0.0
        if self._is_complete_arithmetic_row(text):
            # A complete equation-shaped row is independently constrained by
            # layout and grammar; visually verified ÷ supplies extra evidence.
            confidence = max(confidence, 0.78 if division_verified else 0.70)
        return text, round(max(0.0, min(confidence, 1.0)), 4)

    @staticmethod
    def _is_complete_arithmetic_row(text: str) -> bool:
        return bool(
            re.fullmatch(
                r"[+\-]?\d+(?:[+\-xX×÷/*][+\-]?\d+)+=(?:[+\-]?\d+(?:[.,]\d+)?|\d+/\d+)?",
                text,
            )
        )

    @staticmethod
    def _restore_division(text: str) -> str:
        """Replace the first OCR-confused operator only after visual ÷ detection."""
        compact = re.sub(r"\s+", "", text)
        return re.sub(r"(?<=\d)[^\d=]+(?=\d)", "÷", compact, count=1)

    @staticmethod
    def _has_division_glyph(gray_line: np.ndarray) -> bool:
        """Detect the dot-bar-dot geometry of a division sign."""
        binary = cv2.threshold(
            gray_line, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )[1]
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = [cv2.boundingRect(contour) for contour in contours]
        line_height, line_width = gray_line.shape
        for x, y, width, height in boxes:
            if height == 0 or width / height < 2.2:
                continue
            if width > line_width * 0.25 or height > line_height * 0.30:
                continue
            center_x = x + width / 2
            above = False
            below = False
            for dot_x, dot_y, dot_width, dot_height in boxes:
                if (dot_x, dot_y, dot_width, dot_height) == (x, y, width, height):
                    continue
                dot_center_x = dot_x + dot_width / 2
                is_small = dot_width <= max(width * 0.8, 4) and dot_height <= max(line_height * 0.3, 4)
                aligned = abs(dot_center_x - center_x) <= max(width * 0.65, 4)
                if not (is_small and aligned):
                    continue
                above = above or dot_y + dot_height <= y
                below = below or dot_y >= y + height
            if above and below:
                return True
        return False
