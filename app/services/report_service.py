"""Aggregate question-level outcomes into an auditable report."""

from collections import defaultdict

from app.models.analysis import (
    AnswerStatus,
    AssessmentReport,
    QuestionResult,
    Topic,
    TopicPerformance,
)


def build_report(questions: tuple[QuestionResult, ...]) -> AssessmentReport:
    """Build totals while excluding review-required items from accuracy."""
    counts = {status: 0 for status in AnswerStatus}
    topic_groups: dict[Topic, list[QuestionResult]] = defaultdict(list)
    for question in questions:
        counts[question.status] += 1
        topic_groups[question.topic].append(question)

    topic_performance = tuple(
        _topic_performance(topic, tuple(items))
        for topic, items in sorted(topic_groups.items(), key=lambda item: item[0].value)
    )
    graded = counts[AnswerStatus.CORRECT] + counts[AnswerStatus.INCORRECT]
    accuracy = round(counts[AnswerStatus.CORRECT] / graded, 4) if graded else None
    return AssessmentReport(
        total=len(questions),
        correct=counts[AnswerStatus.CORRECT],
        incorrect=counts[AnswerStatus.INCORRECT],
        blank=counts[AnswerStatus.BLANK],
        review_required=counts[AnswerStatus.REVIEW_REQUIRED],
        graded_total=graded,
        accuracy=accuracy,
        topic_performance=topic_performance,
    )


def _topic_performance(topic: Topic, questions: tuple[QuestionResult, ...]) -> TopicPerformance:
    counts = {status: sum(q.status == status for q in questions) for status in AnswerStatus}
    graded = counts[AnswerStatus.CORRECT] + counts[AnswerStatus.INCORRECT]
    return TopicPerformance(
        topic=topic,
        total=len(questions),
        correct=counts[AnswerStatus.CORRECT],
        incorrect=counts[AnswerStatus.INCORRECT],
        blank=counts[AnswerStatus.BLANK],
        review_required=counts[AnswerStatus.REVIEW_REQUIRED],
        accuracy=round(counts[AnswerStatus.CORRECT] / graded, 4) if graded else None,
    )
