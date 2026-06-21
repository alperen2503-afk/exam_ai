"""Tests for grading, categorization, and study planning."""

import unittest

from app.models.analysis import AnswerStatus, Topic
from app.services.assessment_service import AssessmentService
from app.services.ocr.models import OCRResult


class AssessmentServiceTests(unittest.TestCase):
    def test_correct_wrong_and_blank_are_separated(self) -> None:
        ocr = OCRResult(
            text="2 + 2 = 4\n3 × 3 = 8\n15 ÷ 5 =",
            engine="fake",
            lines=("2 + 2 = 4", "3 × 3 = 8", "15 ÷ 5 ="),
            line_confidences=(0.99, 0.99, 0.99),
        )

        assessment = AssessmentService().analyze(ocr)

        self.assertEqual(
            [question.status for question in assessment.questions],
            [AnswerStatus.CORRECT, AnswerStatus.INCORRECT, AnswerStatus.BLANK],
        )
        self.assertEqual(assessment.questions[2].expected_answer, "3")
        self.assertEqual(assessment.questions[2].topic, Topic.DIVISION)
        self.assertTrue(assessment.study_plan)

    def test_low_confidence_is_not_auto_graded(self) -> None:
        ocr = OCRResult(
            text="2+2=5",
            engine="fake",
            lines=("2+2=5",),
            line_confidences=(0.30,),
        )

        assessment = AssessmentService().analyze(ocr)

        self.assertEqual(assessment.questions[0].status, AnswerStatus.REVIEW_REQUIRED)
        self.assertEqual(assessment.report.graded_total, 0)
