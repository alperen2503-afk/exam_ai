"""Domain models for mathematics assessment."""

from dataclasses import dataclass, field
from enum import StrEnum


class AnswerStatus(StrEnum):
    """Outcome assigned to a detected question."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    BLANK = "blank"
    REVIEW_REQUIRED = "review_required"


class Topic(StrEnum):
    """Stable topic identifiers used by reports and study plans."""

    ADDITION = "arithmetic.addition"
    SUBTRACTION = "arithmetic.subtraction"
    MULTIPLICATION = "arithmetic.multiplication"
    DIVISION = "arithmetic.division"
    MIXED_ARITHMETIC = "arithmetic.mixed"
    ALGEBRA = "algebra"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class QuestionResult:
    """Complete assessment record for one detected question."""

    question_number: int
    raw_text: str
    normalized_expression: str | None
    student_answer: str | None
    expected_answer: str | None
    status: AnswerStatus
    topic: Topic
    confidence: float
    solution_steps: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TopicPerformance:
    """Aggregated performance for one topic."""

    topic: Topic
    total: int
    correct: int
    incorrect: int
    blank: int
    review_required: int
    accuracy: float | None


@dataclass(frozen=True, slots=True)
class AssessmentReport:
    """Assessment summary and per-topic breakdown."""

    total: int
    correct: int
    incorrect: int
    blank: int
    review_required: int
    graded_total: int
    accuracy: float | None
    topic_performance: tuple[TopicPerformance, ...]


@dataclass(frozen=True, slots=True)
class StudyTask:
    """One actionable study activity."""

    topic: Topic
    title: str
    reason: str
    duration_minutes: int
    question_count: int
    activities: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StudyDay:
    """Daily group of study tasks."""

    day: int
    tasks: tuple[StudyTask, ...]
    total_minutes: int


@dataclass(frozen=True, slots=True)
class Assessment:
    """Full output of an assessment pipeline run."""

    questions: tuple[QuestionResult, ...]
    report: AssessmentReport
    study_plan: tuple[StudyDay, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
