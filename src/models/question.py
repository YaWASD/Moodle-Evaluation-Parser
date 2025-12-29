"""Модель вопроса"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Question:
    """Модель вопроса из XML"""
    type: str
    question_text: str
    reference_answer: str
    name: str
    answers: List[str] = field(default_factory=list)  # Все варианты ответов (для multichoice)
    correct_answers: List[str] = field(default_factory=list)  # Правильные ответы (для multichoice)
    matching_items: List[Dict[str, str]] = field(default_factory=list)  # Элементы сопоставления с ответами (для matching)
    matching_answers: List[str] = field(default_factory=list)  # Все уникальные варианты ответов (для matching)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Question':
        """Создание вопроса из словаря"""
        return cls(
            type=data.get('type', ''),
            question_text=data.get('question_text', ''),
            reference_answer=data.get('reference_answer', ''),
            name=data.get('name', ''),
            answers=data.get('answers', []),
            correct_answers=data.get('correct_answers', []),
            matching_items=data.get('matching_items', []),
            matching_answers=data.get('matching_answers', [])
        )
    
    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            'type': self.type,
            'question_text': self.question_text,
            'reference_answer': self.reference_answer,
            'name': self.name,
            'answers': self.answers,
            'correct_answers': self.correct_answers,
            'matching_items': self.matching_items,
            'matching_answers': self.matching_answers
        }

