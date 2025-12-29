"""Модель курса"""

from dataclasses import dataclass, field
from typing import List

from .question import Question


@dataclass
class Course:
    """Модель курса с вопросами"""
    name: str
    questions: List[Question] = field(default_factory=list)
    
    def add_question(self, question: Question):
        """Добавление вопроса в курс"""
        self.questions.append(question)
    
    def __len__(self) -> int:
        """Количество вопросов в курсе"""
        return len(self.questions)

