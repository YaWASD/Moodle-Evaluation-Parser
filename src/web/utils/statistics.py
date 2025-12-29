"""
Утилиты для подсчета статистики.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Dict, List


def overall_stats(snapshot: dict, uploads: List[dict]) -> dict:
    questions = snapshot.get("questions", [])
    courses = snapshot.get("courses", [])

    type_distribution = Counter(q["type"] for q in questions)
    course_distribution = [
        {
            "id": course["id"],
            "name": course["name"],
            "question_count": course.get("question_count", 0),
        }
        for course in courses
    ]

    recent_upload = max(uploads, key=lambda item: item["uploaded_at"], default=None)

    return {
        "total_questions": len(questions),
        "total_courses": len(courses),
        "type_distribution": type_distribution,
        "course_distribution": course_distribution,
        "recent_upload": recent_upload,
        "generated_reports": 0,
    }


def course_stats(course: dict) -> dict:
    questions = course.get("questions", [])
    type_distribution = Counter(q["type"] for q in questions)
    return {
        "name": course["name"],
        "question_count": len(questions),
        "type_distribution": type_distribution,
    }


def build_csv_report(snapshot: dict) -> str:
    lines = ["Course,Question Count"]
    for course in snapshot.get("courses", []):
        lines.append(f"{course['name']},{course.get('question_count', 0)}")
    return "\n".join(lines)

