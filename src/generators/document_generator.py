"""Генератор документов Word"""

from __future__ import annotations

import logging
from docx import Document
from docx.shared import Inches
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..models.question import Question
from ..models.metadata import DocumentMetadata
from .styles import DocumentStyles
from .templates import TemplateFactory


class DocumentGenerator:
    """Генератор документов с оценочными материалами"""
    
    def __init__(self, metadata: DocumentMetadata):
        """
        Инициализация генератора
        
        Args:
            metadata: Метаданные документа
        """
        self.metadata = metadata
        self._logger = logging.getLogger(__name__)
    
    def generate(
        self,
        questions: List[Question],
        output_path: str,
        template_map: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Генерация документа из списка вопросов
        
        Args:
            questions: Список вопросов
            output_path: Путь для сохранения документа
        """
        if not output_path or not str(output_path).strip():
            raise ValueError("output_path is empty")
        if questions is None:
            raise ValueError("questions is None")
        if not isinstance(questions, list):
            raise TypeError(f"questions must be a list, got {type(questions)!r}")
        if not questions:
            raise ValueError("Нет вопросов для экспорта.")

        title = (self.metadata.document_title or "").strip()
        if not title:
            # Не критично, но лучше иметь понятный заголовок
            self._logger.warning("Document title is empty; using fallback")
            title = "Оценочные материалы"

        # Создание документа
        doc = Document()
        
        # Настройка полей страницы
        self._setup_page_margins(doc)
        
        # Настройка стилей (можно переопределять через template config)
        style_cfg = None
        if template_map:
            for cfg in template_map.values():
                if isinstance(cfg, dict) and isinstance(cfg.get("styles"), dict):
                    style_cfg = cfg.get("styles")
                    break
        DocumentStyles.setup_styles(doc, style_cfg)
        
        # Добавление заголовка документа
        doc.add_paragraph(title, style="CustomTitle")
        
        # Обработка вопросов
        task_number = 1
        skipped_types: Dict[str, int] = {}
        render_errors: List[str] = []
        for question in questions:
            template = TemplateFactory.get_template(question.type)
            if template:
                try:
                    cfg = (template_map or {}).get(question.type) if template_map else None
                    # поддерживаем оба варианта сигнатуры render(...)
                    try:
                        template.render(doc, question, self.metadata, task_number, cfg)
                    except TypeError:
                        template.render(doc, question, self.metadata, task_number)
                    task_number += 1
                except Exception as e:
                    # Продолжаем генерацию, но фиксируем проблему.
                    msg = f"Ошибка рендеринга вопроса '{question.name}' (type={question.type}): {e}"
                    self._logger.exception(msg)
                    render_errors.append(msg)
            else:
                skipped_types[question.type] = skipped_types.get(question.type, 0) + 1
                self._logger.warning(
                    "Template for question type '%s' not found; skipping question '%s'",
                    question.type,
                    question.name,
                )
        
        # Сохранение документа
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)
        self._logger.info("DOCX saved: %s", output_path)

        return {
            "output_path": str(output_path_obj),
            "rendered_questions": task_number - 1,
            "skipped_types": skipped_types,
            "errors": render_errors,
        }
    
    def _setup_page_margins(self, doc: Document):
        """
        Настройка полей страницы
        
        Args:
            doc: Объект документа Word
        """
        section = doc.sections[0]
        section.top_margin = Inches(2/2.54)  # 2 см
        section.bottom_margin = Inches(2/2.54)  # 2 см
        section.left_margin = Inches(3/2.54)  # 3 см
        section.right_margin = Inches(1.5/2.54)  # 1.5 см

