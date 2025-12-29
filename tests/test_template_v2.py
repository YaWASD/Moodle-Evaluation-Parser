from __future__ import annotations

import json
import unittest

from src.template_engine.migration import migrate_v1_to_v2
from src.template_engine.presets import preset_dash_answer, preset_table_default
from src.template_engine.render_html import render_question_html
from src.template_engine.validator import validate_template_config_v2


class TemplateV2Tests(unittest.TestCase):
    def test_presets_validate(self) -> None:
        for q_type in ["essay_gigachat", "shortanswer", "multichoice", "matching", "truefalse"]:
            cfg = preset_table_default(q_type)
            self.assertEqual(validate_template_config_v2(cfg), [])
            cfg2 = preset_dash_answer(q_type)
            self.assertEqual(validate_template_config_v2(cfg2), [])

    def test_dash_preset_renders_question_answer(self) -> None:
        cfg = preset_dash_answer("essay_gigachat")
        q = {"type": "essay_gigachat", "question_text": "Q?", "reference_answer": "A", "correct_answers": [], "answers": []}
        meta = {"pk_prefix": "ПК", "pk_id": "1.3", "ipk_prefix": "ИПК", "ipk_id": "1.3.3", "description": "desc"}
        html = render_question_html(cfg, q, meta, 1)
        self.assertIn("Q?", html)
        self.assertIn("—", html)
        self.assertIn("A", html)

    def test_migrate_v1_to_v2(self) -> None:
        v1 = {"styles": {"header_color": "#00FF00", "title_size": 20}, "layout": {"essay_gigachat": {"table_cols_pct": [15, 15, 70]}}}
        v2 = migrate_v1_to_v2(v1, "essay_gigachat")
        self.assertEqual(v2.get("version"), 2)
        self.assertEqual(v2.get("styles", {}).get("header_color"), "#00FF00")


if __name__ == "__main__":
    unittest.main()


