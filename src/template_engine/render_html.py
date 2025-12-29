from __future__ import annotations

import html
import re
from typing import Any, Dict, List

from .validator import validate_template_config_v2


_EXPR_RE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


def _esc(v: Any) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def _get_question_view(question: dict[str, Any]) -> dict[str, Any]:
    correct = question.get("correct_answers") or []
    matching_pairs = question.get("matching_items") or []
    return {
        **question,
        "correct_join": "; ".join(str(x) for x in correct),
        "matching_join": "; ".join(
            f"{p.get('item','')}→{p.get('answer','')}" for p in matching_pairs if isinstance(p, dict)
        ),
    }


def _eval_pipe(expr: str, ctx: dict[str, Any], item: Any | None = None) -> str:
    """
    Minimal placeholder engine:
    - {{question.field}}
    - {{metadata.field}}
    - {{task.header}}
    - {{item}} / {{item.item}} / {{item.answer}}
    - pipe: {{item|is_correct}} (for answers_all)
    """
    expr = expr.strip()
    if "|" in expr:
        base, op = [p.strip() for p in expr.split("|", 1)]
        if op == "is_correct":
            # returns "+" if item in correct_answers else ""
            val = _eval_pipe(base, ctx, item=item)
            correct = set(ctx["question"].get("correct_answers") or [])
            return "+" if val in correct else ""
        if op == "if_correct":
            # returns value if item in correct_answers else ""
            val = _eval_pipe(base, ctx, item=item)
            correct = set(ctx["question"].get("correct_answers") or [])
            return val if val in correct else ""
        return _eval_pipe(base, ctx, item=item)

    if expr.startswith("question."):
        key = expr[len("question.") :]
        return "" if key not in ctx["question"] else str(ctx["question"].get(key) or "")
    if expr.startswith("metadata."):
        key = expr[len("metadata.") :]
        return "" if key not in ctx["metadata"] else str(ctx["metadata"].get(key) or "")
    if expr == "task.header":
        return str(ctx.get("task_header") or "")
    if expr == "item":
        return "" if item is None else str(item)
    if expr.startswith("item.") and isinstance(item, dict):
        return str(item.get(expr[len("item.") :], "") or "")
    return ""


def _render_pattern(pattern: str, ctx: dict[str, Any], item: Any | None = None) -> str:
    def repl(m: re.Match) -> str:
        return _esc(_eval_pipe(m.group(1), ctx, item=item))

    return _EXPR_RE.sub(repl, pattern)


def render_question_html(cfg: dict[str, Any], question: dict[str, Any], metadata: dict[str, Any], task_number: int) -> str:
    errors = validate_template_config_v2(cfg)
    if errors:
        return f"<div class='muted'>Template error: {_esc('; '.join(errors))}</div>"

    qv = _get_question_view(question)
    task_header = (
        f"- Задание {task_number} "
        f"({metadata.get('pk_prefix','ПК')}-{metadata.get('pk_id','')} – "
        f"{metadata.get('ipk_prefix','ИПК')}-{metadata.get('ipk_id','')} "
        f"{metadata.get('description','')})"
    )
    ctx = {"question": qv, "metadata": metadata, "task_header": task_header}

    blocks: List[dict[str, Any]] = cfg.get("blocks") or []
    out: List[str] = []
    for b in blocks:
        kind = b.get("kind")
        if kind == "line":
            out.append(f"<div class='line'>{_render_pattern(b.get('pattern',''), ctx)}</div>")
        elif kind == "spacer":
            mm = int(b.get("mm", 4))
            out.append(f"<div style='height:{mm}mm'></div>")
        elif kind == "list":
            source = b.get("source")
            pattern = b.get("pattern", "{{item}}")
            bullet = bool(b.get("bullet", True))
            items: list[Any] = []
            if source == "answers_all":
                items = question.get("answers") or []
            elif source == "answers_correct":
                items = question.get("correct_answers") or []
            elif source == "matching_pairs":
                items = question.get("matching_items") or []
            tag = "ul" if bullet else "ol"
            lis = "".join(f"<li>{_render_pattern(pattern, ctx, item=x)}</li>" for x in items) or "<li></li>"
            out.append(f"<{tag}>{lis}</{tag}>")
        elif kind == "table":
            source = b.get("source")
            headers = b.get("headers") or []
            cols = b.get("cols") or []
            widths = b.get("col_widths_pct") or []

            items: list[Any] = []
            if source == "answers_all":
                items = question.get("answers") or []
            elif source == "answers_correct":
                items = question.get("correct_answers") or []
            elif source == "matching_pairs":
                items = question.get("matching_items") or []

            col_count = len(cols)
            if widths and len(widths) == col_count:
                width_style = [f"width:{int(w)}%" for w in widths]
            else:
                width_style = ["" for _ in range(col_count)]

            head_html = ""
            if headers and len(headers) == col_count:
                ths = "".join(
                    f"<th style='{_esc(width_style[i])}'>{_esc(headers[i])}</th>" for i in range(col_count)
                )
                head_html = f"<thead><tr>{ths}</tr></thead>"

            rows_html = []
            for it in items or [None]:
                tds = "".join(
                    f"<td style='{_esc(width_style[i])}'>{_render_pattern(cols[i], ctx, item=it)}</td>"
                    for i in range(col_count)
                )
                rows_html.append(f"<tr>{tds}</tr>")
            out.append(f"<table>{head_html}<tbody>{''.join(rows_html)}</tbody></table>")

    return "\n".join(out)


def render_document_html(
    questions: list[dict[str, Any]],
    metadata: dict[str, Any],
    templates_by_type: dict[str, dict[str, Any]],
    title: str,
) -> str:
    styles_cfg = next((t.get("styles") for t in templates_by_type.values() if isinstance(t, dict)), {}) or {}
    header_color = styles_cfg.get("header_color", "#C00000")
    body_size = styles_cfg.get("body_size", 14)
    title_size = styles_cfg.get("title_size", 22)
    header_size = styles_cfg.get("header_size", 16)

    css = f"""
    body{{font-family: "Times New Roman", Times, serif; font-size:{int(body_size)}px; padding:28mm 15mm 20mm 30mm;}}
    h1{{text-align:center; font-size:{int(title_size)}px; margin:0 0 12mm 0;}}
    .task{{color:{_esc(header_color)}; font-style:italic; font-size:{int(header_size)}px; margin:6mm 0 0 0;}}
    .line{{margin:2mm 0;}}
    table{{border-collapse:collapse; width:100%; table-layout:fixed;}}
    td,th{{border:1px solid #000; padding:6px 8px; vertical-align:top; word-wrap:break-word;}}
    .muted{{color:#666;}}
    """

    parts = [
        "<!doctype html>",
        "<html lang='ru'>",
        "<head><meta charset='utf-8'/><meta name='viewport' content='width=device-width, initial-scale=1'/>",
        f"<title>{_esc(title)}</title><style>{css}</style></head>",
        "<body>",
        f"<h1>{_esc(title)}</h1>",
    ]

    for i, q in enumerate(questions, start=1):
        q_type = q.get("type", "")
        cfg = templates_by_type.get(q_type)
        if not cfg:
            parts.append(f"<div class='muted'>Нет шаблона для типа {_esc(q_type)} (пропущено)</div>")
            continue
        parts.append(f"<div class='task'></div>")
        parts.append(render_question_html(cfg, q, metadata, i))

    parts.append("</body></html>")
    return "\n".join(parts)


