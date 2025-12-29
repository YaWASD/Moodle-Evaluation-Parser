"""
Помощники для работы с данными текущей сессии.
"""

from __future__ import annotations

from typing import Any

from flask import session

from .storage import load_snapshot, save_snapshot


def _file_id_from_question_id(question_id: str) -> str | None:
    """
    Пытаемся извлечь file_id из question_id вида:
    <file_id>:<course_index>:<question_index> (и похожих вариантов).
    """
    if not question_id or ":" not in question_id:
        return None
    file_id = question_id.split(":", 1)[0].strip()
    return file_id or None


def set_current_file(file_id: str) -> None:
    session["current_file_id"] = file_id
    session.modified = True


def get_current_file_id() -> str | None:
    return session.get("current_file_id")


def get_snapshot(file_id: str | None = None) -> dict[str, Any] | None:
    target = file_id or get_current_file_id()
    if not target:
        return None
    return load_snapshot(target)


def get_question(question_id: str, file_id: str | None = None) -> dict[str, Any] | None:
    inferred = file_id or _file_id_from_question_id(question_id)
    snapshot = get_snapshot(inferred)
    if not snapshot:
        return None
    return next((q for q in snapshot.get("questions", []) if q["id"] == question_id), None)


def update_question(question_id: str, updated_fields: dict[str, Any]) -> bool:
    target_file_id = _file_id_from_question_id(question_id) or get_current_file_id()
    snapshot = get_snapshot(target_file_id)
    if not snapshot:
        return False

    changed = False
    for question in snapshot.get("questions", []):
        if question["id"] == question_id:
            question.update(updated_fields)
            changed = True
            break

    if not changed:
        return False

    for course in snapshot.get("courses", []):
        for question in course.get("questions", []):
            if question["id"] == question_id:
                question.update(updated_fields)
                break

    save_snapshot(snapshot["id"], snapshot)
    _refresh_upload_meta(snapshot)
    return True


def add_question(course_id: str, question_payload: dict[str, Any]) -> bool:
    snapshot = get_snapshot()
    if not snapshot:
        return False

    target_course = next((c for c in snapshot.get("courses", []) if c["id"] == course_id), None)
    if not target_course:
        return False

    target_course.setdefault("questions", []).append(question_payload)
    target_course["question_count"] = len(target_course["questions"])

    snapshot.setdefault("questions", []).append(question_payload)
    snapshot["question_count"] = len(snapshot["questions"])

    save_snapshot(snapshot["id"], snapshot)
    _refresh_upload_meta(snapshot)
    return True


def _refresh_upload_meta(snapshot: dict[str, Any]) -> None:
    uploads = session.get("uploads", [])
    for item in uploads:
        if item["id"] == snapshot["id"]:
            item["course_count"] = len(snapshot.get("courses", []))
            item["question_count"] = len(snapshot.get("questions", []))
            break
    session["uploads"] = uploads
    session.modified = True



