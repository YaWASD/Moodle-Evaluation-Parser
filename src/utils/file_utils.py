"""Утилиты для работы с файлами"""

import re
from pathlib import Path
from typing import Optional, Tuple
import xml.etree.ElementTree as ET


def sanitize_filename(filename: str) -> str:
    """
    Очистка имени файла от недопустимых символов
    
    Args:
        filename: Исходное имя файла
        
    Returns:
        Очищенное имя файла
    """
    # Заменяем недопустимые символы на подчеркивания
    # Windows недопустимые символы: < > : " / \ | ? *
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Убираем пробелы в начале и конце
    sanitized = sanitized.strip()
    
    # Заменяем множественные подчеркивания на одно
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Если имя файла пустое, возвращаем дефолтное
    if not sanitized:
        sanitized = "Без_названия"
    
    return sanitized


def escape_xml_text(text: str) -> str:
    """
    Экранирование XML-специальных символов в тексте
    
    Args:
        text: Исходный текст
        
    Returns:
        Текст с экранированными XML символами
    """
    if not text:
        return text
    
    # Важно: сначала экранируем &, чтобы не затронуть уже экранированные сущности
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    
    return text


def clean_xml_file(xml_content: str) -> str:
    """
    Очистка XML файла от CDATA и HTML тегов в текстовых элементах
    Обрабатывает весь файл за один раз перед парсингом
    
    Args:
        xml_content: Содержимое XML файла как строка
        
    Returns:
        Очищенное содержимое XML
    """
    if not xml_content:
        return xml_content
    
    # Паттерн для поиска CDATA блоков: <![CDATA[ ... ]]>
    cdata_pattern = r'<!\[CDATA\[(.*?)\]\]>'
    
    def replace_cdata(match):
        """Функция для замены CDATA на очищенный текст"""
        content = match.group(1)
        
        # Удаляем HTML теги (например, <p>, </p>, <br/> и т.д.)
        # Но сохраняем символы < и > которые не являются тегами (например, в формулах Excel)
        # Сначала удаляем известные HTML теги
        html_tags = [
            r'<p[^>]*>', r'</p>',
            r'<br[^>]*/?>',
            r'<div[^>]*>', r'</div>',
            r'<span[^>]*>', r'</span>',
            r'<strong[^>]*>', r'</strong>',
            r'<b[^>]*>', r'</b>',
            r'<em[^>]*>', r'</em>',
            r'<i[^>]*>', r'</i>',
            r'<u[^>]*>', r'</u>',
            r'<ul[^>]*>', r'</ul>',
            r'<ol[^>]*>', r'</ol>',
            r'<li[^>]*>', r'</li>',
            r'<table[^>]*>', r'</table>',
            r'<tr[^>]*>', r'</tr>',
            r'<td[^>]*>', r'</td>',
            r'<th[^>]*>', r'</th>',
        ]
        
        for tag_pattern in html_tags:
            content = re.sub(tag_pattern, '', content, flags=re.IGNORECASE)
        
        # Убираем лишние пробелы и переносы строк (но сохраняем один пробел)
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # Экранируем XML-специальные символы (включая < и > которые остались)
        content = escape_xml_text(content)
        
        return content
    
    # Заменяем все CDATA блоки на очищенный текст
    cleaned_xml = re.sub(cdata_pattern, replace_cdata, xml_content, flags=re.DOTALL)
    
    return cleaned_xml


def validate_xml_file(xml_file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Проверка корректности XML файла перед парсингом
    
    Args:
        xml_file_path: Путь к XML файлу
        
    Returns:
        Кортеж (is_valid, error_message)
        is_valid: True если файл корректен, False если есть ошибки
        error_message: Сообщение об ошибке с номером строки, или None если ошибок нет
    """
    if not xml_file_path.exists():
        return False, f"Файл не найден: {xml_file_path}"
    
    try:
        # Пытаемся распарсить XML
        tree = ET.parse(xml_file_path)
        return True, None
    except ET.ParseError as e:
        # Извлекаем информацию об ошибке
        error_msg = str(e)
        # Пытаемся найти номер строки в сообщении об ошибке
        line_match = re.search(r'line (\d+)', error_msg)
        col_match = re.search(r'column (\d+)', error_msg)
        
        if line_match:
            line_num = line_match.group(1)
            col_num = col_match.group(1) if col_match else "?"
            return False, f"Ошибка парсинга XML на строке {line_num}, столбец {col_num}: {error_msg}"
        else:
            return False, f"Ошибка парсинга XML: {error_msg}"
    except Exception as e:
        return False, f"Неожиданная ошибка при проверке XML: {str(e)}"

