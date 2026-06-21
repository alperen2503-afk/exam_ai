"""Safe local storage for uploaded source files."""

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings, settings


ALLOWED_IMAGE_TYPES = {
    "image/bmp": ".bmp",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/tiff": ".tiff",
    "image/webp": ".webp",
}


class FileValidationError(ValueError):
    """Raised when an uploaded file is unsupported or too large."""


@dataclass(frozen=True, slots=True)
class StoredFile:
    """Metadata for a safely persisted upload."""

    original_name: str
    path: Path


class UploadStorage:
    """Validate and persist uploaded images using generated filenames."""

    def __init__(self, app_settings: Settings = settings) -> None:
        self._settings = app_settings

    async def save(self, upload: UploadFile) -> StoredFile:
        """Persist an upload after validating type and size."""
        content_type = (upload.content_type or "").lower()
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise FileValidationError(
                "Yalnızca PNG, JPEG, WebP, TIFF ve BMP görselleri destekleniyor."
            )

        data = await upload.read(self._settings.max_upload_bytes + 1)
        if not data:
            raise FileValidationError("Yüklenen dosya boş.")
        if len(data) > self._settings.max_upload_bytes:
            raise FileValidationError(
                f"Dosya boyutu {self._settings.max_upload_bytes} baytı aşamaz."
            )

        self._settings.upload_dir.mkdir(parents=True, exist_ok=True)
        suffix = ALLOWED_IMAGE_TYPES[content_type]
        destination = self._settings.upload_dir / f"{uuid4().hex}{suffix}"
        destination.write_bytes(data)

        return StoredFile(
            original_name=Path(upload.filename or "upload").name,
            path=destination,
        )


_storage: UploadStorage | None = None


def get_upload_storage() -> UploadStorage:
    """Return the process-wide upload storage instance."""
    global _storage
    if _storage is None:
        _storage = UploadStorage()
    return _storage
