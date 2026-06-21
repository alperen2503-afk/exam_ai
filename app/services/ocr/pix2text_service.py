"""Pix2Text-backed mathematical OCR engine."""

from __future__ import annotations

import re
from pathlib import Path
from threading import Lock
from typing import Any

from PIL import Image

from app.services.ocr.exceptions import OCRError, OCRUnavailableError
from app.services.ocr.models import OCRResult


class Pix2TextService:
    """Primary OCR engine for mixed text and mathematical formulas.

    Model loading is lazy because Pix2Text initialization is expensive and may
    download model weights on the first request.
    """

    name = "pix2text"

    def __init__(self, model: Any | None = None) -> None:
        self._model = model
        self._load_lock = Lock()

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        with self._load_lock:
            if self._model is not None:
                return self._model
            try:
                from pix2text import Pix2Text
            except Exception as exc:
                raise OCRUnavailableError(
                    "Pix2Text kullanılamıyor; paket ve model bağımlılıklarını kontrol edin."
                ) from exc

            try:
                self._model = Pix2Text.from_config()
            except Exception as exc:
                raise OCRUnavailableError(
                    "Pix2Text modeli yüklenemedi."
                ) from exc
        return self._model

    def extract(self, image_path: Path) -> OCRResult:
        """Recognize mixed natural language and formulas from an image."""
        try:
            with Image.open(image_path) as source:
                image = source.convert("RGB")
            output = self._recognize(self._get_model(), image)
            text = self._normalize_output(output)
        except OCRUnavailableError:
            raise
        except Exception as exc:
            raise OCRError("Pix2Text görseli işleyemedi.") from exc

        if not text:
            raise OCRError("Pix2Text boş sonuç döndürdü.")

        return OCRResult(
            text=text,
            latex=self._extract_latex(text),
            engine=self.name,
        )

    @staticmethod
    def _recognize(model: Any, image: Image.Image) -> Any:
        """Call the current Pix2Text API with compatibility for older releases."""
        try:
            return model.recognize(
                image,
                file_type="text_formula",
                return_text=True,
            )
        except TypeError:
            return model.recognize(image)

    @classmethod
    def _normalize_output(cls, output: Any) -> str:
        """Convert supported Pix2Text response shapes into Markdown text."""
        if isinstance(output, str):
            return output.strip()
        if isinstance(output, dict):
            return cls._render_fragment(output)
        if isinstance(output, (list, tuple)):
            return "\n".join(
                fragment
                for item in output
                if (fragment := cls._normalize_output(item))
            ).strip()
        if hasattr(output, "to_text"):
            return str(output.to_text()).strip()
        return str(output).strip() if output is not None else ""

    @staticmethod
    def _render_fragment(fragment: dict[str, Any]) -> str:
        value = str(fragment.get("text") or fragment.get("latex") or "").strip()
        fragment_type = str(fragment.get("type", "")).lower()
        if value and fragment_type in {"formula", "isolated", "embedding"}:
            return f"$${value}$$" if fragment_type == "isolated" else f"${value}$"
        return value

    @staticmethod
    def _extract_latex(text: str) -> str | None:
        formulas = re.findall(r"\$\$(.+?)\$\$|\$(.+?)\$", text, flags=re.DOTALL)
        values = [block or inline for block, inline in formulas]
        return "\n".join(values) if values else None
