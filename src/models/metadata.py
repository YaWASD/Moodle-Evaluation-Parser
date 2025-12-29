"""Модель метаданных документа"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DocumentMetadata:
    """Метаданные документа для генерации"""
    pk_prefix: str = 'ПК'
    pk_id: str = ''
    ipk_prefix: str = 'ИПК'
    ipk_id: str = ''
    description: str = ''
    document_title: str = ''
    
    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            'pk_prefix': self.pk_prefix,
            'pk_id': self.pk_id,
            'ipk_prefix': self.ipk_prefix,
            'ipk_id': self.ipk_id,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DocumentMetadata':
        """Создание из словаря"""
        return cls(
            pk_prefix=data.get('pk_prefix', 'ПК'),
            pk_id=data.get('pk_id', ''),
            ipk_prefix=data.get('ipk_prefix', 'ИПК'),
            ipk_id=data.get('ipk_id', ''),
            description=data.get('description', ''),
            document_title=data.get('document_title', '')
        )

