"""Exam AI FastAPI application entry point."""

from dataclasses import asdict

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.schemas.analysis import ExamAnalysisResponse
from app.schemas.ocr import OCRResponse
from app.services.assessment_service import get_assessment_service
from app.services.ocr.exceptions import OCRProcessingError
from app.services.ocr.ocr_service import get_ocr_service
from app.services.storage_service import FileValidationError, get_upload_storage

app = FastAPI(title="Exam AI", version="1.2.0")


@app.get("/")
def root() -> dict[str, str]:
    """Return a lightweight health response."""
    return {"message": "Exam AI çalışıyor"}


@app.post("/upload", response_model=OCRResponse)
async def upload_file(file: UploadFile = File(...)) -> OCRResponse:
    """Store an uploaded image and extract its text with the OCR pipeline."""
    storage = get_upload_storage()

    try:
        stored_file = await storage.save(file)
        result = await run_in_threadpool(get_ocr_service().extract, stored_file.path)
    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc
    except OCRProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return OCRResponse(
        filename=stored_file.original_name,
        stored_filename=stored_file.path.name,
        extracted_text=result.text,
        latex=result.latex,
        ocr_engine=result.engine,
        fallback_used=result.fallback_used,
    )


@app.post("/analyze", response_model=ExamAnalysisResponse)
async def analyze_exam(file: UploadFile = File(...)) -> ExamAnalysisResponse:
    """OCR, grade, classify, report, and plan study for an uploaded worksheet."""
    storage = get_upload_storage()
    try:
        stored_file = await storage.save(file)
        ocr_result = await run_in_threadpool(get_ocr_service().extract, stored_file.path)
        assessment = await run_in_threadpool(
            get_assessment_service().analyze,
            ocr_result,
        )
    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc
    except OCRProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return ExamAnalysisResponse(
        filename=stored_file.original_name,
        stored_filename=stored_file.path.name,
        extracted_text=ocr_result.text,
        ocr_engine=ocr_result.engine,
        fallback_used=ocr_result.fallback_used,
        **asdict(assessment),
    )
