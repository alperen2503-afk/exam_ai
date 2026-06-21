"""Environment-driven application settings."""

from dataclasses import dataclass, field
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings with safe local defaults."""

    upload_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("EXAM_AI_UPLOAD_DIR", str(BASE_DIR / "app" / "uploads"))
        )
    )
    max_upload_bytes: int = field(
        default_factory=lambda: int(os.getenv("EXAM_AI_MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
    )
    tesseract_cmd: str = field(
        default_factory=lambda: os.getenv(
            "TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )
    )
    tesseract_language: str = field(
        default_factory=lambda: os.getenv("TESSERACT_LANGUAGE", "eng")
    )


settings = Settings()
