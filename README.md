# Парсер оценочных материалов (Moodle XML → документы)

Веб-приложение на Flask для загрузки XML вопросов из Moodle, просмотра/редактирования и экспорта в DOCX/PDF/HTML/Markdown/Excel.

## Установка и запуск

1) Клонирование репозитория:

```bash
git clone https://github.com/YaWASD/Moodle-Evaluation-Parser.git
cd Moodle-Evaluation-Parser
```

2) Создание и активация виртуального окружения (venv):

Windows (PowerShell):

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

3) Установка зависимостей (внутри venv):

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4) Запуск:

```bash
python app.py
```

Открыть в браузере: `http://localhost:5000`

## Коротко о возможностях

- **Загрузка XML** (в том числе несколько файлов за раз)
- **Просмотр** курсов/категорий/вопросов
- **Редактирование** вопросов
- **Экспорт** + история экспортов и скачивание файлов
- **Шаблоны оформления** (набор шаблонов по типам вопросов)
- **Шаблоны метаданных**
- **Тёмная тема**

## Примечания

- Папки `uploads/`, `temp/`, `output/` содержат временные/сгенерированные данные и **не коммитятся** (см. `.gitignore`).
- Конфигурация: `config/__init__.py`.
