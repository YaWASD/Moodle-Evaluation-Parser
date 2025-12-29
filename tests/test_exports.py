from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path


# Ensure project root is first on sys.path (avoid conflicts with any external `src` package).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.generators.document_generator import DocumentGenerator  # noqa: E402
from src.generators.exporters.excel_exporter import ExcelExporter  # noqa: E402
from src.generators.exporters.html_exporter import HTMLExporter  # noqa: E402
from src.generators.exporters.markdown_exporter import MarkdownExporter  # noqa: E402
from src.generators.exporters.pdf_exporter import PDFExporter  # noqa: E402
from src.models.metadata import DocumentMetadata  # noqa: E402
from src.models.question import Question  # noqa: E402


def _sample_questions() -> list[Question]:
    return [
        Question(
            type="essay_gigachat",
            question_text="Опишите принцип работы TCP.",
            reference_answer="TCP — протокол транспортного уровня с установлением соединения.",
            name="essay_1",
        ),
        Question(
            type="shortanswer",
            question_text="Столица Франции?",
            reference_answer="Париж",
            name="short_1",
            correct_answers=["Париж"],
        ),
        Question(
            type="multichoice",
            question_text="Выберите простые числа.",
            reference_answer="",
            name="multi_1",
            answers=["2", "3", "4"],
            correct_answers=["2", "3"],
        ),
        Question(
            type="matching",
            question_text="Сопоставьте термин и определение.",
            reference_answer="",
            name="match_1",
            matching_items=[
                {"item": "CPU", "answer": "Центральный процессор"},
                {"item": "RAM", "answer": "Оперативная память"},
            ],
            matching_answers=["Оперативная память", "Центральный процессор"],
        ),
        Question(
            type="truefalse",
            question_text="HTTP — протокол прикладного уровня.",
            reference_answer="",
            name="tf_1",
            answers=["Верно", "Неверно"],
            correct_answers=["Верно"],
        ),
    ]


class ExportSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.metadata = DocumentMetadata(
            pk_prefix="ПК",
            pk_id="1.3",
            ipk_prefix="ИПК",
            ipk_id="1.3.3",
            description="Тестовое описание компетенции",
            document_title="Тестовый курс",
        )
        self.questions = _sample_questions()

    def test_docx_export_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.docx"
            gen = DocumentGenerator(self.metadata)
            result = gen.generate(self.questions, str(out))
            self.assertTrue(out.exists(), "DOCX file was not created")
            self.assertGreater(out.stat().st_size, 0, "DOCX file is empty")
            self.assertEqual(result["rendered_questions"], len(self.questions))

    def test_pdf_export_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.pdf"
            exporter = PDFExporter()
            result = exporter.export(self.questions, self.metadata, str(out))
            self.assertTrue(out.exists(), "PDF file was not created")
            self.assertGreater(out.stat().st_size, 0, "PDF file is empty")
            self.assertEqual(result["rendered_questions"], len(self.questions))

    def test_html_export_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.html"
            exporter = HTMLExporter()
            result = exporter.export(self.questions, self.metadata, str(out))
            self.assertTrue(out.exists(), "HTML file was not created")
            self.assertGreater(out.stat().st_size, 0, "HTML file is empty")
            self.assertEqual(result["rendered_questions"], len(self.questions))

    def test_markdown_export_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.md"
            exporter = MarkdownExporter()
            result = exporter.export(self.questions, self.metadata, str(out))
            self.assertTrue(out.exists(), "Markdown file was not created")
            self.assertGreater(out.stat().st_size, 0, "Markdown file is empty")
            self.assertEqual(result["rendered_questions"], len(self.questions))

    def test_excel_export_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.xlsx"
            exporter = ExcelExporter()
            result = exporter.export(self.questions, self.metadata, str(out))
            self.assertTrue(out.exists(), "XLSX file was not created")
            self.assertGreater(out.stat().st_size, 0, "XLSX file is empty")
            self.assertGreaterEqual(result["rendered_questions"], 1)


if __name__ == "__main__":
    unittest.main()


