"""
Проверки качества вопросов.
"""

from __future__ import annotations

from typing import Dict, List


def validate_question(question: dict) -> List[dict]:
    issues = []
    if not question.get("question_text", "").strip():
        issues.append({"severity": "error", "message": "Нет текста вопроса."})

    q_type = question.get("type", "")
    if q_type in {"multichoice", "shortanswer", "matching"}:
        answers = question.get("answers", [])
        if not answers:
            issues.append({"severity": "warning", "message": "Нет вариантов ответов."})
    if q_type in {"multichoice", "shortanswer", "truefalse"}:
        correct = question.get("correct_answers", [])
        if not correct:
            issues.append({"severity": "error", "message": "Нет правильного ответа."})

    if len(question.get("question_text", "")) > 2000:
        issues.append({"severity": "warning", "message": "Очень длинный текст вопроса."})

    return issues


def validate_snapshot(snapshot: dict) -> List[dict]:
    results = []
    for question in snapshot.get("questions", []):
        issues = validate_question(question)
        for issue in issues:
            results.append(
                {
                    "question_id": question["id"],
                    "question_name": question["name"],
                    "course_name": question.get("course_name", ""),
                    "severity": issue["severity"],
                    "message": issue["message"],
                }
            )
    return results










