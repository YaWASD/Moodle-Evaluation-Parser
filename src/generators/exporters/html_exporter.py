"""
Экспорт в HTML (самодостаточный файл с inline-CSS).

Экспортёр вызывается из web-роута для одного курса: на вход получает список вопросов и метаданные.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict, List


def _t(value: Any) -> str:
    return "" if value is None else str(value)


def _esc(value: Any) -> str:
    return html.escape(_t(value), quote=True)


def _header_text(metadata: Any, task_number: int) -> str:
    pk_prefix = _t(getattr(metadata, "pk_prefix", "ПК"))
    pk_id = _t(getattr(metadata, "pk_id", ""))
    ipk_prefix = _t(getattr(metadata, "ipk_prefix", "ИПК"))
    ipk_id = _t(getattr(metadata, "ipk_id", ""))
    description = _t(getattr(metadata, "description", ""))
    return f"- Задание {task_number} ({pk_prefix}-{pk_id} – {ipk_prefix}-{ipk_id} {description})"


CSS = """
:root{
  --red:#C00000;
  --border:#000;
}
body{
  font-family: "Times New Roman", Times, serif;
  font-size: 14px;
  color:#000;
  margin: 0;
  padding: 28mm 15mm 20mm 30mm;
  line-height: 1.35;
}
h1{
  text-align:center;
  font-size: 22px;
  margin: 0 0 12mm 0;
}
.task-header{
  color: var(--red);
  font-style: italic;
  font-size: 16px;
  margin: 6mm 0 0 0;
}
.qtext{
  margin: 2mm 0 3mm 0;
  text-align: justify;
}
table{
  border-collapse: collapse;
  width: 100%;
  table-layout: fixed;
}
td, th{
  border: 1px solid var(--border);
  padding: 6px 8px;
  vertical-align: top;
  word-wrap: break-word;
}
.muted{
  color:#666;
}
.bold{
  font-weight: 700;
}
@media print{
  body{ padding: 0; margin: 0; }
}
"""


class HTMLExporter:
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

        html_text, meta = self.render_html(questions, metadata, template_map=template_map)
        out.write_text(html_text, encoding="utf-8")
        return {
            "output_path": str(out),
            "rendered_questions": meta["rendered_questions"],
            "skipped_types": meta["skipped_types"],
        }

    def render_html(self, questions, metadata, template_map: Dict[str, Any] | None = None) -> tuple[str, Dict[str, Any]]:
        """
        Рендерит HTML в строку (для предпросмотра).
        template_map: {question_type: config_dict}
        """
        title = _t(getattr(metadata, "document_title", "")) or "Оценочные материалы"

        styles_cfg = {}
        # берём стили из первого доступного конфига
        if template_map:
            for cfg in template_map.values():
                if isinstance(cfg, dict) and isinstance(cfg.get("styles"), dict):
                    styles_cfg = cfg["styles"]
                    break

        css = CSS
        if styles_cfg:
            # простая замена ключевых значений
            header_color = _t(styles_cfg.get("header_color", "")).strip()
            if header_color:
                css = css.replace("--red:#C00000;", f"--red:{header_color};")
            title_size = styles_cfg.get("title_size")
            if isinstance(title_size, (int, float)):
                css = css.replace("font-size: 22px;", f"font-size: {int(title_size)}px;")
            body_size = styles_cfg.get("body_size")
            if isinstance(body_size, (int, float)):
                css = css.replace("font-size: 14px;", f"font-size: {int(body_size)}px;")

        parts: List[str] = []
        parts.append("<!doctype html>")
        parts.append("<html lang=\"ru\">")
        parts.append("<head>")
        parts.append("<meta charset=\"utf-8\"/>")
        parts.append("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>")
        parts.append(f"<title>{_esc(title)}</title>")
        parts.append(f"<style>{css}</style>")
        parts.append("</head>")
        parts.append("<body>")
        parts.append(f"<h1>{_esc(title)}</h1>")

        task_number = 1
        skipped_types: Dict[str, int] = {}

        for q in questions:
            q_type = _t(getattr(q, "type", ""))
            parts.append(f"<div class=\"task-header\">{_esc(_header_text(metadata, task_number))}</div>")
            parts.append(f"<div class=\"qtext\">{_esc(getattr(q, 'question_text', ''))}</div>")

            renderer = getattr(self, f"_render_{q_type}", None)
            if callable(renderer):
                cfg = (template_map or {}).get(q_type, {})
                parts.append(renderer(q, task_number, cfg))
            else:
                skipped_types[q_type] = skipped_types.get(q_type, 0) + 1
                parts.append(f"<div class=\"muted\">(Пропущено: нет HTML-шаблона для типа { _esc(q_type) })</div>")

            task_number += 1

        parts.append("</body></html>")
        return "\n".join(parts), {"rendered_questions": task_number - 1, "skipped_types": skipped_types}

    def _cols(self, q_type: str, cfg: Dict[str, Any], fallback: List[int]) -> List[int]:
        cols = (
            (cfg.get("layout") or {})
            .get(q_type, {})
            .get("table_cols_pct")
        )
        if isinstance(cols, list) and all(isinstance(x, (int, float)) for x in cols) and len(cols) == len(fallback):
            total = sum(cols) or 0
            if total > 0:
                # нормализуем на всякий случай
                return [int(round(100 * (x / total))) for x in cols]
        return fallback

    def _render_essay_gigachat(self, q: Any, task_number: int, cfg: Dict[str, Any]) -> str:
        ref = _esc(getattr(q, "reference_answer", ""))
        c = self._cols("essay_gigachat", cfg, [10, 10, 80])
        return (
            "<table>"
            f"<tr><td style=\"width:{c[0]}%\">№{task_number}</td><td style=\"width:{c[1]}%\"></td><td style=\"width:{c[2]}%\">{ref}</td></tr>"
            "</table>"
        )

    def _render_shortanswer(self, q: Any, task_number: int, cfg: Dict[str, Any]) -> str:
        answers = getattr(q, "correct_answers", None) or []
        if not answers:
            ref = _t(getattr(q, "reference_answer", ""))
            answers = [ref] if ref else []
        if not answers:
            answers = [""]
        c = self._cols("shortanswer", cfg, [10, 10, 80])
        rows = []
        for idx, ans in enumerate(answers):
            num = f"№{task_number}" if idx == 0 else ""
            rows.append(
                f"<tr><td style=\"width:{c[0]}%\">{_esc(num)}</td>"
                f"<td style=\"width:{c[1]}%\"></td>"
                f"<td style=\"width:{c[2]}%\">{_esc(ans)}</td></tr>"
            )
        return "<table>" + "".join(rows) + "</table>"

    def _render_multichoice(self, q: Any, task_number: int, cfg: Dict[str, Any]) -> str:
        answers = getattr(q, "answers", None) or []
        correct = set(getattr(q, "correct_answers", None) or [])
        c = self._cols("multichoice", cfg, [10, 45, 45])
        rows = [
            "<tr>"
            f"<td style=\"width:{c[0]}%\">№{task_number}</td>"
            f"<td class=\"bold\" style=\"width:{c[1]}%\">Варианты ответа:</td>"
            f"<td class=\"bold\" style=\"width:{c[2]}%\">Правильный ответ:</td>"
            "</tr>"
        ]
        for ans in answers:
            rows.append(
                "<tr>"
                "<td></td>"
                f"<td>{_esc(ans)}</td>"
                f"<td>{_esc(ans) if ans in correct else ''}</td>"
                "</tr>"
            )
        if not answers:
            rows.append("<tr><td></td><td></td><td></td></tr>")
        return "<table>" + "".join(rows) + "</table>"

    def _render_truefalse(self, q: Any, task_number: int, cfg: Dict[str, Any]) -> str:
        # Используем те же правила что и multichoice
        c = cfg.copy()
        # переиспользуем ключ в layout
        if isinstance(cfg.get("layout"), dict) and "truefalse" not in cfg["layout"] and "multichoice" in cfg["layout"]:
            c = {"layout": {"truefalse": cfg["layout"]["multichoice"]}, "styles": cfg.get("styles", {})}
        return self._render_multichoice(q, task_number, c)

    def _render_matching(self, q: Any, task_number: int, cfg: Dict[str, Any]) -> str:
        items = getattr(q, "matching_items", None) or []
        answers = getattr(q, "matching_answers", None) or []
        max_rows = max(len(items), len(answers), 1)
        c = self._cols("matching", cfg, [10, 25, 35, 30])
        rows = [
            "<tr>"
            f"<td style=\"width:{c[0]}%\">№{task_number}</td>"
            f"<td class=\"bold\" style=\"width:{c[1]}%\">Варианты ответа:</td>"
            f"<td class=\"bold\" style=\"width:{c[2]}%\">Элемент для сопоставления:</td>"
            f"<td class=\"bold\" style=\"width:{c[3]}%\">Правильный ответ:</td>"
            "</tr>"
        ]
        for i in range(max_rows):
            var = answers[i] if i < len(answers) else ""
            item = items[i].get("item", "") if i < len(items) and isinstance(items[i], dict) else ""
            ans = items[i].get("answer", "") if i < len(items) and isinstance(items[i], dict) else ""
            rows.append(
                "<tr>"
                "<td></td>"
                f"<td>{_esc(var)}</td>"
                f"<td>{_esc(item)}</td>"
                f"<td>{_esc(ans)}</td>"
                "</tr>"
            )
        return "<table>" + "".join(rows) + "</table>"



