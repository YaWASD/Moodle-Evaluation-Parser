"""
Точка входа в веб-приложение «Парсер оценочных материалов».
"""

from config import BaseConfig
from src.web import create_app


def main():
    """Запускает Flask сервер."""
    app = create_app(BaseConfig)
    app.run(debug=app.config.get("DEBUG", False))


if __name__ == "__main__":
    main()

