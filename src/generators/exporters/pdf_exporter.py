"""
Экспорт в PDF.

Реализация ориентирована на Windows: пытаемся зарегистрировать TTF-шрифт из C:\\Windows\\Fonts,
чтобы корректно отображалась кириллица. Если шрифт не найден — используем стандартный Helvetica
(в этом случае кириллица может отображаться некорректно).
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _try_register_windows_font() -> Optional[str]:
    """
    Возвращает имя зарегистрированного шрифта или None.
    """
    candidates = [
        r"C:\Windows\Fonts\times.ttf",      # Times New Roman (часто)
        r"C:\Windows\Fonts\timesbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\DejaVuSans.ttf",
    ]
    for font_path in candidates:
        path = Path(font_path)
        if path.exists():
            font_name = f"AppFont_{path.stem}"
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(path)))
                return font_name
            except Exception:
                # Если регистрация не удалась — пробуем следующий
                continue
    return None


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


class PDFExporter:
    def __init__(self) -> None:
        self._font_name = _try_register_windows_font() or "Helvetica"

    def export(self, questions, metadata, output_path: str, template_map: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Экспортирует список вопросов в PDF.
        """
        if not output_path or not str(output_path).strip():
            raise ValueError("output_path is empty")
        if questions is None:
            raise ValueError("questions is None")
        if not isinstance(questions, list):
            raise TypeError(f"questions must be a list, got {type(questions)!r}")
        if not questions:
            raise ValueError("Нет вопросов для экспорта.")

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        styles = getSampleStyleSheet()
        base = ParagraphStyle(
            "Base",
            parent=styles["Normal"],
            fontName=self._font_name,
            fontSize=11,
            leading=14,
            textColor=colors.black,
        )
        title_style = ParagraphStyle(
            "Title",
            parent=base,
            fontSize=16,
            leading=20,
            alignment=1,  # center
            spaceAfter=10,
        )
        header_style = ParagraphStyle(
            "Header",
            parent=base,
            fontSize=12,
            leading=14,
            textColor=colors.HexColor("#C00000"),
            italic=True,
            spaceBefore=8,
            spaceAfter=2,
        )

        doc = SimpleDocTemplate(
            str(out_path),
            pagesize=A4,
            leftMargin=30 * mm,
            rightMargin=15 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        story: List[Any] = []

        document_title = getattr(metadata, "document_title", "") or ""
        story.append(Paragraph(_as_text(document_title) or "Оценочные материалы", title_style))

        task_number = 1
        skipped_types: Dict[str, int] = {}

        for q in questions:
            q_type = getattr(q, "type", "") or ""
            q_name = getattr(q, "name", "") or ""
            q_text = getattr(q, "question_text", "") or ""

            header_text = self._build_header_text(metadata, task_number)
            story.append(Paragraph(header_text, header_style))
            story.append(Paragraph(_as_text(q_text), base))
            story.append(Spacer(1, 4 * mm))

            renderer = getattr(self, f"_render_{q_type}", None)
            if callable(renderer):
                story.extend(renderer(q, task_number, base))
            else:
                skipped_types[q_type] = skipped_types.get(q_type, 0) + 1
                story.append(
                    Paragraph(
                        f"(Пропущено: нет PDF-шаблона для типа '{_as_text(q_type)}' / '{_as_text(q_name)}')",
                        ParagraphStyle("Skip", parent=base, textColor=colors.red),
                    )
                )
            story.append(Spacer(1, 6 * mm))
            task_number += 1

        doc.build(story)
        return {
            "output_path": str(out_path),
            "rendered_questions": task_number - 1,
            "skipped_types": skipped_types,
            "font": self._font_name,
        }

    def _build_header_text(self, metadata: Any, task_number: int) -> str:
        pk_prefix = _as_text(getattr(metadata, "pk_prefix", "ПК"))
        pk_id = _as_text(getattr(metadata, "pk_id", ""))
        ipk_prefix = _as_text(getattr(metadata, "ipk_prefix", "ИПК"))
        ipk_id = _as_text(getattr(metadata, "ipk_id", ""))
        description = _as_text(getattr(metadata, "description", ""))
        return f"- Задание {task_number} ({pk_prefix}-{pk_id} – {ipk_prefix}-{ipk_id} {description})"

    def _mk_table(self, data: List[List[Any]], base_style: ParagraphStyle, col_widths: List[float]) -> Table:
        # Превращаем строки в Paragraph для переноса текста
        processed: List[List[Any]] = []
        for row in data:
            out_row: List[Any] = []
            for cell in row:
                out_row.append(Paragraph(_as_text(cell), base_style))
            processed.append(out_row)

        tbl = Table(processed, colWidths=col_widths, hAlign="LEFT")
        tbl.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        return tbl

    # ---- Renderers per question type ----

    def _render_essay_gigachat(self, q: Any, task_number: int, base: ParagraphStyle) -> List[Any]:
        ref = getattr(q, "reference_answer", "") or ""
        data = [[f"№{task_number}", "", ref]]
        col_widths = [18 * mm, 10 * mm, 120 * mm]
        return [self._mk_table(data, base, col_widths)]

    def _render_shortanswer(self, q: Any, task_number: int, base: ParagraphStyle) -> List[Any]:
        answers = getattr(q, "correct_answers", None) or []
        if not answers:
            ref = getattr(q, "reference_answer", "") or ""
            answers = [ref] if ref else []
        if not answers:
            data = [[f"№{task_number}", "", ""]]
        else:
            data = []
            for idx, ans in enumerate(answers):
                num = f"№{task_number}" if idx == 0 else ""
                data.append([num, "", ans])
        col_widths = [18 * mm, 10 * mm, 120 * mm]
        return [self._mk_table(data, base, col_widths)]

    def _render_multichoice(self, q: Any, task_number: int, base: ParagraphStyle) -> List[Any]:
        answers = getattr(q, "answers", None) or []
        correct = set(getattr(q, "correct_answers", None) or [])
        data = [[f"№{task_number}", "Варианты ответа:", "Правильный ответ:"]]
        if answers:
            for ans in answers:
                data.append(["", ans, ans if ans in correct else ""])
        col_widths = [18 * mm, 70 * mm, 60 * mm]
        return [self._mk_table(data, base, col_widths)]

    def _render_truefalse(self, q: Any, task_number: int, base: ParagraphStyle) -> List[Any]:
        return self._render_multichoice(q, task_number, base)

    def _render_matching(self, q: Any, task_number: int, base: ParagraphStyle) -> List[Any]:
        items = getattr(q, "matching_items", None) or []
        answers = getattr(q, "matching_answers", None) or []
        max_rows = max(len(items), len(answers), 1)
        data = [[f"№{task_number}", "Варианты ответа:", "Элемент для сопоставления:", "Правильный ответ:"]]
        for i in range(max_rows):
            var = answers[i] if i < len(answers) else ""
            item = items[i]["item"] if i < len(items) and isinstance(items[i], dict) else ""
            ans = items[i]["answer"] if i < len(items) and isinstance(items[i], dict) else ""
            data.append(["", var, item, ans])
        col_widths = [18 * mm, 45 * mm, 55 * mm, 45 * mm]
        return [self._mk_table(data, base, col_widths)]



