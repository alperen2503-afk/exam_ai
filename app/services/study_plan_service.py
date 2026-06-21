"""Generate a conservative study plan from observed performance."""

from app.models.analysis import AssessmentReport, StudyDay, StudyTask, Topic


_TOPIC_NAMES = {
    Topic.ADDITION: "Toplama",
    Topic.SUBTRACTION: "Çıkarma",
    Topic.MULTIPLICATION: "Çarpma",
    Topic.DIVISION: "Bölme",
    Topic.MIXED_ARITHMETIC: "Karışık İşlemler",
    Topic.ALGEBRA: "Cebir",
    Topic.UNKNOWN: "İncelenecek Sorular",
}


def build_study_plan(report: AssessmentReport, max_days: int = 7) -> tuple[StudyDay, ...]:
    """Prioritize wrong/blank topics; never infer mastery from ungraded OCR."""
    priorities = sorted(
        report.topic_performance,
        key=lambda item: (
            -(item.incorrect * 3 + item.blank * 2 + item.review_required),
            item.topic.value,
        ),
    )
    priorities = [
        item
        for item in priorities
        if item.incorrect or item.blank or item.review_required
    ]
    if not priorities:
        return ()

    days: list[StudyDay] = []
    for index, performance in enumerate(priorities[:max_days], start=1):
        weakness = performance.incorrect + performance.blank
        minutes = min(60, 20 + weakness * 5 + performance.review_required * 5)
        count = min(30, max(10, weakness * 5))
        topic_name = _TOPIC_NAMES[performance.topic]
        reasons: list[str] = []
        if performance.incorrect:
            reasons.append(f"{performance.incorrect} yanlış")
        if performance.blank:
            reasons.append(f"{performance.blank} boş")
        if performance.review_required:
            reasons.append(f"{performance.review_required} öğretmen incelemesi")
        task = StudyTask(
            topic=performance.topic,
            title=f"{topic_name} güçlendirme",
            reason=", ".join(reasons),
            duration_minutes=minutes,
            question_count=count,
            activities=(
                "5 dakika konu özeti ve örnek inceleme",
                f"Kolaydan zora {count} soru çözümü",
                "Yanlışların nedenini yazıp benzer 3 soru çözme",
                "Ertesi gün kısa tekrar testi",
            ),
        )
        days.append(StudyDay(day=index, tasks=(task,), total_minutes=minutes))
    return tuple(days)
