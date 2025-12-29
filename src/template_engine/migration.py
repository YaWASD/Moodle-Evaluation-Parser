from __future__ import annotations

from typing import Any, Dict

from .presets import preset_table_default


def migrate_v1_to_v2(v1: dict[str, Any], question_type: str) -> dict[str, Any]:
    """
    Best-effort миграция старого конфига (v1 styles/layout) к v2 blocks.
    """
    v2 = preset_table_default(question_type)
    styles = v2.get("styles", {})

    v1_styles = v1.get("styles") if isinstance(v1.get("styles"), dict) else {}
    if isinstance(v1_styles.get("header_color"), str):
        styles["header_color"] = v1_styles["header_color"]
    for key_old, key_new in [
        ("title_size", "title_size"),
        ("header_size", "header_size"),
        ("body_size", "body_size"),
        ("answer_size", "answer_size"),
    ]:
        if isinstance(v1_styles.get(key_old), (int, float)):
            styles[key_new] = int(v1_styles[key_old])

    v2["styles"] = styles

    # v1 layout widths -> try map to table block width
    layout = v1.get("layout") if isinstance(v1.get("layout"), dict) else {}
    table_cols = None
    if isinstance(layout.get(question_type), dict):
        tc = layout[question_type].get("table_cols_pct")
        if isinstance(tc, list) and all(isinstance(x, (int, float)) for x in tc):
            table_cols = [int(x) for x in tc]
    if table_cols:
        for b in v2.get("blocks", []):
            if isinstance(b, dict) and b.get("kind") == "table":
                b["col_widths_pct"] = table_cols
                break

    return v2


