"""
Экспорт в Markdown.

Даём максимально переносимый Markdown: заголовки + простые таблицы.
Для сложных случаев (matching) используем таблицу на 4 колонки.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def _t(value: Any) -> str:
    return "" if value is None else str(value)


def _md_escape(text: Any) -> str:
    # Минимальная экранизация для таблиц: | и переносы строк
    s = _t(text)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("|", "\\|")
    s = s.replace("\n", "<br>")
    return s


def _header_text(metadata: Any, task_number: int) -> str:
    pk_prefix = _t(getattr(metadata, "pk_prefix", "ПК"))
    pk_id = _t(getattr(metadata, "pk_id", ""))
    ipk_prefix = _t(getattr(metadata, "ipk_prefix", "ИПК"))
    ipk_id = _t(getattr(metadata, "ipk_id", ""))
    description = _t(getattr(metadata, "description", ""))
    return f"- Задание {task_number} ({pk_prefix}-{pk_id} – {ipk_prefix}-{ipk_id} {description})"


def _table(headers: List[str], rows: List[List[Any]]) -> str:
    head = "| " + " | ".join(_md_escape(h) for h in headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(_md_escape(c) for c in row) + " |" for row in rows)
    return "\n".join([head, sep, body]) if body else "\n".join([head, sep])


class MarkdownExporter:
    def export(self, questions, metadata, output_path: str, template_map: Dict[str, Any] | None = None) -> Dict[str, Any]:
        if not output_path or not str(output_path).strip():
            raise ValueError("output_path is empty")
        if questions is None:
            raise ValueError("questions is None")
        if not isinstance(questions, list):
            raise TypeError(f"questions must be a list, got {type(questions)!r}")
        if not questions:
            raise ValueError("Нет вопросов для экспорта.")

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        title = _t(getattr(metadata, "document_title", "")) or "Оценочные материалы"

        lines: List[str] = []
        lines.append(f"# {_md_escape(title)}")
        lines.append("")
        lines.append("## Метаданные")
        lines.append("")
        lines.append(
            _table(
                ["Поле", "Значение"],
                [
                    ["ПК", f"{_t(getattr(metadata,'pk_prefix','ПК'))}-{_t(getattr(metadata,'pk_id',''))}"],
                    ["ИПК", f"{_t(getattr(metadata,'ipk_prefix','ИПК'))}-{_t(getattr(metadata,'ipk_id',''))}"],
                    ["Описание", _t(getattr(metadata, "description", ""))],
                ],
            )
        )
        lines.append("")

        task_number = 1
        skipped_types: Dict[str, int] = {}

        for q in questions:
            q_type = _t(getattr(q, "type", ""))
            lines.append(f"## {task_number}. {_md_escape(_header_text(metadata, task_number))}")
            lines.append("")
            lines.append(_md_escape(getattr(q, "question_text", "")))
            lines.append("")

            renderer = getattr(self, f"_render_{q_type}", None)
            if callable(renderer):
                lines.extend(renderer(q, task_number))
            else:
                skipped_types[q_type] = skipped_types.get(q_type, 0) + 1
                lines.append(f"_Пропущено: нет Markdown-шаблона для типа `{_md_escape(q_type)}`_")
                lines.append("")

            task_number += 1

        out.write_text("\n".join(lines), encoding="utf-8")
        return {
            "output_path": str(out),
            "rendered_questions": task_number - 1,
            "skipped_types": skipped_types,
        }

    def _render_essay_gigachat(self, q: Any, task_number: int) -> List[str]:
        ref = getattr(q, "reference_answer", "") or ""
        return [
            _table(["№", "", "Эталонный ответ"], [[f"№{task_number}", "", ref]]),
            "",
        ]

    def _render_shortanswer(self, q: Any, task_number: int) -> List[str]:
        answers = getattr(q, "correct_answers", None) or []
        if not answers:
            ref = getattr(q, "reference_answer", "") or ""
            answers = [ref] if ref else []
        if not answers:
            answers = [""]
        rows = []
        for idx, ans in enumerate(answers):
            num = f"№{task_number}" if idx == 0 else ""
            rows.append([num, "", ans])
        return [
            _table(["№", "", "Ответ"], rows),
            "",
        ]

    def _render_multichoice(self, q: Any, task_number: int) -> List[str]:
        answers = getattr(q, "answers", None) or []
        correct = set(getattr(q, "correct_answers", None) or [])
        rows = []
        if not answers:
            rows.append([f"№{task_number}", "", ""])
        else:
            for idx, ans in enumerate(answers):
                num = f"№{task_number}" if idx == 0 else ""
                rows.append([num, ans, ans if ans in correct else ""])
        return [
            _table(["№", "Варианты ответа", "Правильный ответ"], rows),
            "",
        ]

    def _render_truefalse(self, q: Any, task_number: int) -> List[str]:
        return self._render_multichoice(q, task_number)

    def _render_matching(self, q: Any, task_number: int) -> List[str]:
        items = getattr(q, "matching_items", None) or []
        answers = getattr(q, "matching_answers", None) or []
        max_rows = max(len(items), len(answers), 1)
        rows = []
        for i in range(max_rows):
            num = f"№{task_number}" if i == 0 else ""
            var = answers[i] if i < len(answers) else ""
            item = items[i].get("item", "") if i < len(items) and isinstance(items[i], dict) else ""
            ans = items[i].get("answer", "") if i < len(items) and isinstance(items[i], dict) else ""
            rows.append([num, var, item, ans])
        return [
            _table(["№", "Варианты ответа", "Элемент", "Правильный ответ"], rows),
            "",
        ]



