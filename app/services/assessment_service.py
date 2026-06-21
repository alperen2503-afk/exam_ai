"""Question assessment orchestration."""

from fractions import Fraction

from app.classifier.classifier_service import classify_expression
from app.models.analysis import AnswerStatus, Assessment, QuestionResult, Topic
from app.services.ocr.models import OCRResult
from app.services.report_service import build_report
from app.services.study_plan_service import build_study_plan
from app.solver.algebra_solver import (
    MathExpressionError,
    format_fraction,
    parse_and_solve,
    parse_answer,
)


MIN_AUTO_GRADE_CONFIDENCE = 0.60


class AssessmentService:
    """Convert OCR lines into graded, categorized question records."""

    def analyze(self, ocr_result: OCRResult) -> Assessment:
        lines = ocr_result.lines or tuple(
            line.strip() for line in ocr_result.text.splitlines() if line.strip()
        )
        confidences = ocr_result.line_confidences or tuple(0.70 for _ in lines)
        questions = tuple(
            self._assess_line(index, line, confidences[index - 1] if index - 1 < len(confidences) else 0.5)
            for index, line in enumerate(lines, start=1)
        )

        warnings: list[str] = []
        if not questions:
            warnings.append("Görselde değerlendirilebilir soru bulunamadı.")
        if any(question.status == AnswerStatus.REVIEW_REQUIRED for question in questions):
            warnings.append(
                "Düşük güvenli veya ayrıştırılamayan sorular otomatik puanlanmadı; insan incelemesi gerekir."
            )

        report = build_report(questions)
        return Assessment(
            questions=questions,
            report=report,
            study_plan=build_study_plan(report),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _assess_line(number: int, raw_text: str, confidence: float) -> QuestionResult:
        try:
            solved = parse_and_solve(raw_text)
        except MathExpressionError as exc:
            return QuestionResult(
                question_number=number,
                raw_text=raw_text,
                normalized_expression=None,
                student_answer=None,
                expected_answer=None,
                status=AnswerStatus.REVIEW_REQUIRED,
                topic=Topic.UNKNOWN,
                confidence=confidence,
                warnings=(str(exc),),
            )

        expected_text = format_fraction(solved.expected_value)
        topic = classify_expression(solved.expression)
        if confidence < MIN_AUTO_GRADE_CONFIDENCE:
            status = AnswerStatus.REVIEW_REQUIRED
            warnings = ("OCR güveni otomatik puanlama eşiğinin altında.",)
        elif solved.student_answer is None:
            status = AnswerStatus.BLANK
            warnings = ()
        else:
            try:
                actual: Fraction = parse_answer(solved.student_answer)
                status = (
                    AnswerStatus.CORRECT
                    if actual == solved.expected_value
                    else AnswerStatus.INCORRECT
                )
                warnings = ()
            except MathExpressionError as exc:
                status = AnswerStatus.REVIEW_REQUIRED
                warnings = (str(exc),)

        return QuestionResult(
            question_number=number,
            raw_text=raw_text,
            normalized_expression=solved.expression,
            student_answer=solved.student_answer,
            expected_answer=expected_text,
            status=status,
            topic=topic,
            confidence=confidence,
            solution_steps=solved.steps if status in {AnswerStatus.BLANK, AnswerStatus.INCORRECT} else (),
            warnings=warnings,
        )


_assessment_service: AssessmentService | None = None


def get_assessment_service() -> AssessmentService:
    global _assessment_service
    if _assessment_service is None:
        _assessment_service = AssessmentService()
    return _assessment_service
