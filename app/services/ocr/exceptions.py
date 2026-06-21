"""OCR-specific exception hierarchy."""


class OCRError(RuntimeError):
    """Base error raised by an OCR engine."""


class OCRUnavailableError(OCRError):
    """Raised when an OCR engine or its model is unavailable."""


class OCRProcessingError(OCRError):
    """Raised when every configured OCR engine fails."""
