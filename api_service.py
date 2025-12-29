"""
REST API сервис для интеграции с Moodle плагином
Предоставляет endpoints для экспорта вопросов в различные форматы
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Optional

from src.parsers.xml_parser import XMLParser
from src.generators.document_generator import DocumentGenerator
from src.models.metadata import DocumentMetadata
from src.models.question import Question
from src.utils.file_utils import sanitize_filename

app = Flask(__name__)
CORS(app)  # Разрешить запросы от Moodle

# Конфигурация
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
TEMP_DIR = Path(os.getenv('TEMP_DIR', tempfile.gettempdir())) / 'questionexport'
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# API ключи для безопасности (в продакшене использовать переменные окружения)
API_KEYS = os.getenv('API_KEYS', '').split(',') if os.getenv('API_KEYS') else []


@app.before_request
def check_api_key():
    """Проверка API ключа (если настроено)"""
    if API_KEYS:
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key not in API_KEYS:
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid API key'}), 401


@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Проверка работоспособности сервиса"""
    return jsonify({
        'status': 'ok',
        'service': 'questionexport-api',
        'version': '1.0.0'
    })


@app.route('/api/v1/formats', methods=['GET'])
def get_formats():
    """Получение списка поддерживаемых форматов экспорта"""
    formats = [
        {
            'id': 'docx',
            'name': 'Word Document',
            'description': 'Документ Microsoft Word (.docx)',
            'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        },
        {
            'id': 'pdf',
            'name': 'PDF Document',
            'description': 'Документ PDF для печати',
            'mime_type': 'application/pdf'
        },
        {
            'id': 'html',
            'name': 'HTML Document',
            'description': 'Веб-страница HTML',
            'mime_type': 'text/html'
        },
        {
            'id': 'markdown',
            'name': 'Markdown',
            'description': 'Документ Markdown',
            'mime_type': 'text/markdown'
        }
    ]
    return jsonify({'formats': formats})


@app.route('/api/v1/templates', methods=['GET'])
def get_templates():
    """Получение списка доступных шаблонов"""
    templates = [
        {
            'id': 'multichoice',
            'name': 'Множественный выбор',
            'type': 'multichoice',
            'description': 'Стандартный шаблон для вопросов с множественным выбором'
        },
        {
            'id': 'shortanswer',
            'name': 'Краткий ответ',
            'type': 'shortanswer',
            'description': 'Стандартный шаблон для вопросов с кратким ответом'
        },
        {
            'id': 'essay_gigachat',
            'name': 'Развернутый ответ',
            'type': 'essay_gigachat',
            'description': 'Стандартный шаблон для вопросов с развернутым ответом'
        },
        {
            'id': 'matching',
            'name': 'Сопоставление',
            'type': 'matching',
            'description': 'Стандартный шаблон для вопросов на сопоставление'
        },
        {
            'id': 'truefalse',
            'name': 'Верно/Неверно',
            'type': 'truefalse',
            'description': 'Стандартный шаблон для вопросов типа Верно/Неверно'
        }
    ]
    return jsonify({'templates': templates})


@app.route('/api/v1/export', methods=['POST'])
def export_questions():
    """
    Экспорт вопросов в документ
    
    Body:
    {
        "questions": [...],  # Список вопросов
        "format": "docx",    # Формат экспорта
        "template": "multichoice",  # Шаблон оформления
        "metadata": {...}    # Метаданные документа
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'Bad request', 'message': 'Request body is required'}), 400
        
        # Валидация входных данных
        questions_data = data.get('questions', [])
        format_type = data.get('format', 'docx')
        template_name = data.get('template', 'default')
        metadata_data = data.get('metadata', {})
        
        if not questions_data:
            return jsonify({'error': 'Bad request', 'message': 'Questions list is required'}), 400
        
        # Конвертация данных в модели
        questions = []
        for q_data in questions_data:
            try:
                question = Question.from_dict(q_data)
                questions.append(question)
            except Exception as e:
                app.logger.warning(f"Failed to parse question: {e}")
                continue
        
        if not questions:
            return jsonify({'error': 'Bad request', 'message': 'No valid questions found'}), 400
        
        # Создание метаданных
        metadata = DocumentMetadata.from_dict(metadata_data)
        
        # Генерация документа
        generator = DocumentGenerator(metadata)
        
        # Создание временного файла
        output_filename = f"export_{hash(str(questions))}.{format_type}"
        output_path = TEMP_DIR / output_filename
        
        # Генерация документа
        generator.generate(questions, str(output_path))
        
        # Проверка существования файла
        if not output_path.exists():
            return jsonify({'error': 'Internal error', 'message': 'Failed to generate document'}), 500
        
        file_size = output_path.stat().st_size
        
        return jsonify({
            'status': 'success',
            'task_id': f"task_{hash(str(questions))}",
            'file_url': f'/api/v1/download/{output_filename}',
            'file_size': file_size,
            'questions_count': len(questions),
            'format': format_type
        })
        
    except Exception as e:
        app.logger.error(f"Export error: {str(e)}")
        return jsonify({
            'error': 'Internal error',
            'message': str(e)
        }), 500


@app.route('/api/v1/download/<filename>', methods=['GET'])
def download_file(filename: str):
    """Скачивание сгенерированного файла"""
    try:
        # Безопасность: проверка имени файла
        safe_filename = sanitize_filename(filename)
        file_path = TEMP_DIR / safe_filename
        
        if not file_path.exists():
            return jsonify({'error': 'Not found', 'message': 'File not found'}), 404
        
        # Определение MIME типа
        mime_types = {
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'pdf': 'application/pdf',
            'html': 'text/html',
            'md': 'text/markdown'
        }
        
        ext = safe_filename.split('.')[-1].lower()
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=safe_filename,
            mimetype=mime_type
        )
        
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'Internal error', 'message': str(e)}), 500


@app.route('/api/v1/export/status/<task_id>', methods=['GET'])
def get_export_status(task_id: str):
    """Получение статуса задачи экспорта (для асинхронных задач)"""
    # В текущей реализации задачи выполняются синхронно
    # В будущем можно добавить поддержку Celery или другой очереди
    return jsonify({
        'task_id': task_id,
        'status': 'completed',
        'message': 'Task completed synchronously'
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal error', 'message': 'An internal error occurred'}), 500


if __name__ == '__main__':
    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=DEBUG
    )

