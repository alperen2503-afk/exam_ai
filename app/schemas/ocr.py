"""OCR API schemas."""

from pydantic import BaseModel, Field


class OCRResponse(BaseModel):
    """Normalized response returned by the upload endpoint."""

    filename: str
    stored_filename: str
    extracted_text: str
    latex: str | None = None
    ocr_engine: str = Field(description="OCR engine that produced the result")
    fallback_used: bool
