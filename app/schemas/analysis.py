"""Public API schemas for exam analysis."""

from pydantic import BaseModel, Field

from app.models.analysis import AnswerStatus, Topic


class QuestionAnalysisResponse(BaseModel):
    question_number: int
    raw_text: str
    normalized_expression: str | None
    student_answer: str | None
    expected_answer: str | None
    status: AnswerStatus
    topic: Topic
    confidence: float = Field(ge=0, le=1)
    solution_steps: list[str]
    warnings: list[str]


class TopicPerformanceResponse(BaseModel):
    topic: Topic
    total: int
    correct: int
    incorrect: int
    blank: int
    review_required: int
    accuracy: float | None


class ReportResponse(BaseModel):
    total: int
    correct: int
    incorrect: int
    blank: int
    review_required: int
    graded_total: int
    accuracy: float | None
    topic_performance: list[TopicPerformanceResponse]


class StudyTaskResponse(BaseModel):
    topic: Topic
    title: str
    reason: str
    duration_minutes: int
    question_count: int
    activities: list[str]


class StudyDayResponse(BaseModel):
    day: int
    tasks: list[StudyTaskResponse]
    total_minutes: int


class ExamAnalysisResponse(BaseModel):
    filename: str
    stored_filename: str
    extracted_text: str
    ocr_engine: str
    fallback_used: bool
    questions: list[QuestionAnalysisResponse]
    report: ReportResponse
    study_plan: list[StudyDayResponse]
    warnings: list[str]
