"""Парсер XML файлов с вопросами"""

import xml.etree.ElementTree as ET
from typing import List, Optional
from pathlib import Path
import re

from ..models.question import Question
from ..models.course import Course
from ..utils.file_utils import clean_xml_file, validate_xml_file


class XMLParser:
    """Парсер XML файлов в формате Moodle"""
    
    # Префикс категорий, который нужно игнорировать
    CATEGORY_PREFIX = "$module$/top/По умолчанию для Банк вопросов курса Оценочные материалы"
    
    def __init__(self, xml_file_path: str):
        """
        Инициализация парсера
        
        Args:
            xml_file_path: Путь к XML файлу
        """
        self.xml_file_path = Path(xml_file_path)
        self.tree = None
        self.root = None
    
    def parse(self) -> List[Question]:
        """
        Парсинг XML файла и извлечение вопросов (старый метод для обратной совместимости)
        
        Returns:
            Список объектов Question
        """
        courses = self.parse_courses()
        # Объединяем все вопросы из всех курсов
        all_questions = []
        for course in courses:
            all_questions.extend(course.questions)
        return all_questions
    
    def parse_courses(self) -> List[Course]:
        """
        Парсинг XML файла и группировка вопросов по курсам
        
        Returns:
            Список объектов Course с вопросами
        """
        if not self.xml_file_path.exists():
            raise FileNotFoundError(f"XML файл не найден: {self.xml_file_path}")
        
        # Проверяем корректность XML файла перед обработкой
        is_valid, error_message = validate_xml_file(self.xml_file_path)
        if not is_valid:
            print(f"Предупреждение: XML файл содержит ошибки. {error_message}")
            print("Попытка очистки и повторного парсинга...")
        
        # Читаем XML файл как текст и очищаем от CDATA и HTML тегов
        with open(self.xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Очищаем XML от CDATA и HTML тегов
        cleaned_xml = clean_xml_file(xml_content)
        
        # Парсим очищенный XML из строки
        try:
            self.root = ET.fromstring(cleaned_xml)
            self.tree = ET.ElementTree(self.root)
        except ET.ParseError as e:
            # Если после очистки все еще есть ошибки, сообщаем об этом
            error_msg = str(e)
            line_match = re.search(r'line (\d+)', error_msg)
            col_match = re.search(r'column (\d+)', error_msg)
            
            if line_match:
                line_num = line_match.group(1)
                col_num = col_match.group(1) if col_match else "?"
                raise ValueError(
                    f"Ошибка парсинга XML после очистки на строке {line_num}, столбец {col_num}. "
                    f"{f'Исходная ошибка: {error_message}. ' if not is_valid else ''}"
                    f"Ошибка после очистки: {error_msg}"
                )
            else:
                raise ValueError(
                    f"Ошибка парсинга XML после очистки. "
                    f"{f'Исходная ошибка: {error_message}. ' if not is_valid else ''}"
                    f"Ошибка после очистки: {error_msg}"
                )
        
        courses = []
        current_course_name: Optional[str] = None
        current_course: Optional[Course] = None
        last_category_name: Optional[str] = None
        
        # Получаем все элементы question по порядку (важно сохранить порядок)
        all_elements = list(self.root.findall('.//question'))
        
        i = 0
        while i < len(all_elements):
            question_elem = all_elements[i]
            question_type = question_elem.get('type', '')
            
            if question_type == 'category':
                # Это категория - извлекаем название
                category_name = self._extract_course_name(question_elem)
                
                # Если это валидная категория (не None)
                if category_name:
                    # Если уже был курс с вопросами, сохраняем его
                    if current_course is not None and len(current_course) > 0:
                        courses.append(current_course)
                    
                    # Сохраняем название категории, но еще не создаем курс
                    # Курс будет создан только если после этой категории идут вопросы
                    last_category_name = category_name
                    current_course_name = None
                    current_course = None
            else:
                # Это вопрос
                # Если есть последняя категория, она становится курсом
                if last_category_name is not None and current_course is None:
                    current_course_name = last_category_name
                    current_course = Course(name=current_course_name)
                    last_category_name = None  # Сбрасываем, т.к. использовали
                
                # Если курс уже создан, добавляем вопрос
                if current_course is not None:
                    question_data = self._parse_question_element(question_elem)
                    question = Question.from_dict(question_data)
                    current_course.add_question(question)
                else:
                    # Вопросы без категории курса - создаем курс с дефолтным именем
                    current_course_name = "Без категории"
                    current_course = Course(name=current_course_name)
                    question_data = self._parse_question_element(question_elem)
                    question = Question.from_dict(question_data)
                    current_course.add_question(question)
            
            i += 1
        
        # Добавляем последний курс, если он есть
        if current_course is not None and len(current_course) > 0:
            courses.append(current_course)
        
        return courses
    
    def _extract_course_name(self, category_element) -> Optional[str]:
        """
        Извлечение названия курса из категории
        
        Args:
            category_element: XML элемент категории
            
        Returns:
            Название курса или None, если это не курс
        """
        category_text_elem = category_element.find('.//category/text')
        if category_text_elem is None or category_text_elem.text is None:
            return None
        
        category_path = category_text_elem.text.strip()
        
        # Убираем префикс
        if not category_path.startswith(self.CATEGORY_PREFIX):
            return None
        
        # Убираем префикс и лишние пробелы
        relative_path = category_path[len(self.CATEGORY_PREFIX):].strip()
        
        # Если путь пустой или начинается не с '/', это не курс
        if not relative_path or not relative_path.startswith('/'):
            return None
        
        # Убираем начальный '/'
        relative_path = relative_path[1:]
        
        # Если после префикса ничего нет, это корневая категория
        if not relative_path:
            return None
        
        # Разделяем по '/'
        parts = [part.strip() for part in relative_path.split('/') if part.strip()]
        
        # Название курса - это последний элемент пути
        # Но только если это не просто подкатегория (если есть хотя бы 2 уровня)
        # На самом деле, по требованию пользователя, название курса - это последний уровень
        
        if parts:
            # Возвращаем последний элемент как название курса
            return parts[-1]
        
        return None
    
    def _parse_question_element(self, question_element) -> dict:
        """
        Парсинг XML элемента вопроса
        
        Args:
            question_element: XML элемент вопроса
            
        Returns:
            Словарь с данными вопроса
        """
        question_data = {}
        
        # Тип вопроса
        question_data['type'] = question_element.get('type', '')
        
        # Текст вопроса
        question_text_elem = question_element.find('.//questiontext/text')
        question_data['question_text'] = question_text_elem.text if question_text_elem is not None else ""
        
        # Эталонный ответ (для essay_gigachat)
        reference_answer_elem = question_element.find('.//referenceanswer/text')
        question_data['reference_answer'] = reference_answer_elem.text if reference_answer_elem is not None else ""
        
        # Название задания
        name_elem = question_element.find('.//name/text')
        question_data['name'] = name_elem.text if name_elem is not None else ""
        
        # Парсинг вариантов ответов для multichoice
        if question_data['type'] == 'multichoice':
            question_data['answers'] = []
            question_data['correct_answers'] = []
            
            # Парсинг всех вариантов ответов
            for answer_elem in question_element.findall('.//answer'):
                answer_text_elem = answer_elem.find('.//text')
                if answer_text_elem is not None and answer_text_elem.text:
                    answer_text = answer_text_elem.text
                    # Получаемправильный ответ
                    fraction = float(answer_elem.get('fraction', '0'))
                    
                    question_data['answers'].append(answer_text)
                    if fraction != 0:
                        question_data['correct_answers'].append(answer_text)
        
        # Парсинг данных для matching
        elif question_data['type'] == 'matching':
            question_data['matching_items'] = []
            question_data['matching_answers'] = []
            answer_set = set()
            
            # Парсинг subquestion элементов
            for subquestion_elem in question_element.findall('.//subquestion'):
                # Текст элемента для сопоставления
                subquestion_text_elem = subquestion_elem.find('.//text')
                matching_item_text = subquestion_text_elem.text if subquestion_text_elem is not None and subquestion_text_elem.text else ""
                
                # Правильный ответ для этого элемента
                answer_elem = subquestion_elem.find('.//answer')
                if answer_elem is not None:
                    answer_text_elem = answer_elem.find('.//text')
                    correct_answer = answer_text_elem.text if answer_text_elem is not None and answer_text_elem.text else ""
                    
                    if matching_item_text and correct_answer:
                        question_data['matching_items'].append({
                            'item': matching_item_text,
                            'answer': correct_answer
                        })
                        answer_set.add(correct_answer)
            
            # Собираем все уникальные варианты ответов
            question_data['matching_answers'] = sorted(list(answer_set))
        
        # Парсинг данных для shortanswer
        elif question_data['type'] == 'shortanswer':
            # Парсинг правильных ответов из answer элементов с fraction != 0
            correct_answers = []
            for answer_elem in question_element.findall('.//answer'):
                fraction = float(answer_elem.get('fraction', '0'))
                if fraction != 0:
                    answer_text_elem = answer_elem.find('.//text')
                    if answer_text_elem is not None and answer_text_elem.text:
                        correct_answers.append(answer_text_elem.text)
            
            # Сохраняем список ответов для отображения каждого на отдельной строке
            question_data['correct_answers'] = correct_answers
            # Для совместимости также сохраняем первый ответ как reference_answer
            if correct_answers:
                question_data['reference_answer'] = correct_answers[0]
            else:
                question_data['reference_answer'] = ""
        
        # Парсинг данных для truefalse
        elif question_data['type'] == 'truefalse':
            # Парсинг ответов true/false
            answer_dict = {}  # Словарь для хранения ответов и их правильности
            correct_answers = []
            
            for answer_elem in question_element.findall('.//answer'):
                answer_text_elem = answer_elem.find('.//text')
                if answer_text_elem is not None and answer_text_elem.text:
                    answer_text = answer_text_elem.text.strip().lower()
                    fraction = float(answer_elem.get('fraction', '0'))
                    
                    # Конвертируем true/false в Верно/Неверно
                    if answer_text == 'true':
                        russian_answer = 'Верно'
                    elif answer_text == 'false':
                        russian_answer = 'Неверно'
                    else:
                        russian_answer = answer_text  # На случай неожиданных значений
                    
                    answer_dict[russian_answer] = (fraction == 100.0)
                    if fraction == 100.0:
                        correct_answers.append(russian_answer)
            
            # Упорядочиваем ответы: сначала Верно, потом Неверно
            answers = []
            if 'Верно' in answer_dict:
                answers.append('Верно')
            if 'Неверно' in answer_dict:
                answers.append('Неверно')
            # Добавляем любые другие неожиданные ответы
            for answer in answer_dict:
                if answer not in ['Верно', 'Неверно']:
                    answers.append(answer)
            
            question_data['answers'] = answers
            question_data['correct_answers'] = correct_answers
        
        return question_data

