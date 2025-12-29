"""
Базовая конфигурация веб-приложения.
"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class BaseConfig:
    """Настройки по умолчанию для Flask приложения."""

    SECRET_KEY = "change-me"
    DEBUG = True

    # Пути для работы с файлами
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    OUTPUT_FOLDER = BASE_DIR / "output"
    TEMP_FOLDER = BASE_DIR / "temp"
    DATA_FOLDER = BASE_DIR / "data"

    TEMPLATE_STORE = DATA_FOLDER / "question_templates.json"
    METADATA_STORE = DATA_FOLDER / "metadata_templates.json"

    # Ограничения на размер загружаемых файлов (50 МБ)
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024


def ensure_directories():
    """Гарантирует наличие требуемых директорий и файлов."""
    for folder in (
        BaseConfig.UPLOAD_FOLDER,
        BaseConfig.OUTPUT_FOLDER,
        BaseConfig.TEMP_FOLDER,
        BaseConfig.DATA_FOLDER,
    ):
        folder.mkdir(parents=True, exist_ok=True)

    for file_path in (
        BaseConfig.TEMPLATE_STORE,
        BaseConfig.METADATA_STORE,
    ):
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("[]", encoding="utf-8")


# Создаем директории при импорте конфигурации
ensure_directories()
