# Backend API для веб-интерфейса

## Описание

Backend API для веб-интерфейса парсера оценочных материалов. Будет реализован на Flask или FastAPI.

## Планируемая структура

```
backend/
├── app.py                 # Основное приложение
├── config.py             # Конфигурация
├── routes/               # API маршруты
│   ├── __init__.py
│   ├── files.py          # Работа с файлами
│   ├── courses.py        # Работа с курсами
│   ├── questions.py      # Работа с вопросами
│   ├── documents.py      # Работа с документами
│   ├── metadata.py       # Метаданные
│   └── statistics.py     # Статистика
├── services/             # Бизнес-логика
│   ├── __init__.py
│   ├── file_service.py
│   ├── parser_service.py
│   └── generator_service.py
├── models/               # API модели (Pydantic)
│   ├── __init__.py
│   ├── file_models.py
│   ├── course_models.py
│   └── question_models.py
├── utils/                # Утилиты
│   ├── __init__.py
│   ├── validators.py
│   └── formatters.py
└── storage/              # Хранилище данных
    ├── __init__.py
    └── file_storage.py
```

## API Endpoints (планируемые)

### Файлы
- `POST /api/v1/upload` - загрузка XML файла
- `GET /api/v1/files` - список файлов
- `GET /api/v1/files/{id}` - информация о файле
- `DELETE /api/v1/files/{id}` - удаление файла
- `POST /api/v1/files/{id}/parse` - парсинг файла

### Курсы
- `GET /api/v1/courses` - список курсов
- `GET /api/v1/courses/{id}` - детали курса
- `GET /api/v1/courses/{id}/questions` - вопросы курса

### Вопросы
- `GET /api/v1/questions` - список вопросов (с фильтрами)
- `GET /api/v1/questions/{id}` - детали вопроса
- `PUT /api/v1/questions/{id}` - обновление вопроса
- `DELETE /api/v1/questions/{id}` - удаление вопроса
- `POST /api/v1/questions/bulk` - массовые операции

### Документы
- `POST /api/v1/documents/generate` - генерация документов
- `GET /api/v1/documents` - список документов
- `GET /api/v1/documents/{id}` - информация о документе
- `GET /api/v1/documents/{id}/download` - скачивание
- `GET /api/v1/documents/{id}/preview` - предпросмотр
- `DELETE /api/v1/documents/{id}` - удаление

### Метаданные
- `GET /api/v1/metadata/templates` - список шаблонов
- `POST /api/v1/metadata/templates` - создание шаблона
- `PUT /api/v1/metadata/templates/{id}` - обновление шаблона
- `DELETE /api/v1/metadata/templates/{id}` - удаление шаблона

### Статистика
- `GET /api/v1/statistics/overall` - общая статистика
- `GET /api/v1/statistics/files/{id}` - статистика по файлу
- `GET /api/v1/statistics/courses/{id}` - статистика по курсу

## Технологии

- Flask или FastAPI
- python-docx (существующее)
- Flask-CORS
- Pydantic для валидации
- SQLite/PostgreSQL для хранения метаданных

