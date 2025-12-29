"""
Значения по умолчанию для конфигураций шаблонов (Template config v1).

Храним в JSON в поле `config` (строкой). UI может редактировать отдельные поля и синхронизировать JSON.

Schema v1 (упрощённо):
{
  "version": 1,
  "styles": {
    "header_color": "#C00000",
    "title_size": 22,
    "header_size": 16,
    "body_size": 14,
    "answer_size": 12
  },
  "layout": {
    "<question_type>": {
      "table_cols_pct": [10, 10, 80]
    }
  }
}
"""

from __future__ import annotations

from typing import Dict, List


def default_config(question_type: str) -> dict:
    base = {
        "version": 1,
        "styles": {
            "header_color": "#C00000",
            "title_size": 22,
            "header_size": 16,
            "body_size": 14,
            "answer_size": 12,
        },
        "layout": {},
    }

    # Table column widths in percent of available content width.
    type_layouts: Dict[str, List[int]] = {
        "essay_gigachat": [10, 10, 80],
        "shortanswer": [10, 10, 80],
        "multichoice": [10, 45, 45],
        "truefalse": [10, 45, 45],
        "matching": [10, 25, 35, 30],
    }

    cols = type_layouts.get(question_type)
    if cols:
        base["layout"][question_type] = {"table_cols_pct": cols}
    return base


