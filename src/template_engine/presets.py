from __future__ import annotations

from typing import Any


def preset_table_default(question_type: str) -> dict[str, Any]:
    # “как было”: текст вопроса + таблица ответов
    if question_type == "matching":
        return {
            "version": 2,
            "styles": {"header_color": "#C00000", "title_size": 22, "header_size": 16, "body_size": 14, "answer_size": 12},
            "blocks": [
                {"kind": "line", "pattern": "{{task.header}}"},
                {"kind": "line", "pattern": "{{question.question_text}}"},
                {"kind": "spacer", "mm": 2},
                {
                    "kind": "table",
                    "source": "matching_pairs",
                    # ближе к DOCX-шаблону (generators/templates.py): 4 колонки
                    "headers": ["№", "", "Элемент", "Правильный ответ"],
                    "cols": ["", "", "{{item.item}}", "{{item.answer}}"],
                    "col_widths_pct": [10, 25, 35, 30],
                },
            ],
        }

    if question_type in {"multichoice", "truefalse"}:
        return {
            "version": 2,
            "styles": {"header_color": "#C00000", "title_size": 22, "header_size": 16, "body_size": 14, "answer_size": 12},
            "blocks": [
                {"kind": "line", "pattern": "{{task.header}}"},
                {"kind": "line", "pattern": "{{question.question_text}}"},
                {"kind": "spacer", "mm": 2},
                {
                    "kind": "table",
                    "source": "answers_all",
                    # ближе к DOCX-шаблону: 3 колонки (№ / варианты / правильный ответ)
                    "headers": ["№", "Варианты ответа", "Правильный ответ"],
                    "cols": ["", "{{item}}", "{{item|if_correct}}"],
                    "col_widths_pct": [10, 45, 45],
                },
            ],
        }

    if question_type == "shortanswer":
        return {
            "version": 2,
            "styles": {"header_color": "#C00000", "title_size": 22, "header_size": 16, "body_size": 14, "answer_size": 12},
            "blocks": [
                {"kind": "line", "pattern": "{{task.header}}"},
                {"kind": "line", "pattern": "{{question.question_text}}"},
                {"kind": "spacer", "mm": 2},
                {
                    "kind": "table",
                    "source": "answers_correct",
                    "headers": ["№", "", "Ответ"],
                    "cols": ["", "", "{{item}}"],
                    "col_widths_pct": [10, 10, 80],
                },
            ],
        }

    # essay_gigachat default
    return {
        "version": 2,
        "styles": {"header_color": "#C00000", "title_size": 22, "header_size": 16, "body_size": 14, "answer_size": 12},
        "blocks": [
            {"kind": "line", "pattern": "{{task.header}}"},
            {"kind": "line", "pattern": "{{question.question_text}}"},
            {"kind": "spacer", "mm": 2},
            {"kind": "line", "pattern": "Эталон: {{question.reference_answer}}"},
        ],
    }


def preset_dash_answer(question_type: str) -> dict[str, Any]:
    """
    Пример “совсем другой” схемы: одна строка `Вопрос — Ответ`.
    Для типов с множеством ответов: `Вопрос — a; b; c`.
    """
    answer_expr = "{{question.reference_answer}}"
    if question_type in {"multichoice", "truefalse"}:
        answer_expr = "{{question.correct_join}}"
    if question_type == "shortanswer":
        answer_expr = "{{question.correct_join}}"
    if question_type == "matching":
        answer_expr = "{{question.matching_join}}"
    return {
        "version": 2,
        "styles": {"header_color": "#C00000", "title_size": 22, "header_size": 16, "body_size": 14, "answer_size": 12},
        "blocks": [
            {"kind": "line", "pattern": "{{task.header}}"},
            {"kind": "line", "pattern": "{{question.question_text}} — " + answer_expr},
        ],
    }


def presets_for_type(question_type: str) -> list[dict[str, Any]]:
    return [
        {"id": "table_default", "name": "Стандарт (таблица/список)", "config": preset_table_default(question_type)},
        {"id": "dash_answer", "name": "Вопрос — Ответ (без таблиц)", "config": preset_dash_answer(question_type)},
    ]


