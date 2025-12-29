"""
Веб-пакет приложения.
"""

from pathlib import Path

from flask import Flask, session

from config import BaseConfig
from src.web.routes.main import main_bp


def create_app(config_object: type[BaseConfig] = BaseConfig) -> Flask:
    """
    Фабрика Flask приложения (будет расширена на следующих этапах).

    Args:
        config_object: класс конфигурации Flask.
    """

    package_dir = Path(__file__).resolve().parent

    app = Flask(
        __name__,
        template_folder=str(package_dir / "templates"),
        static_folder=str(package_dir / "static"),
    )
    app.config.from_object(config_object)

    # Регистрация blueprints
    app.register_blueprint(main_bp)

    @app.context_processor
    def inject_theme():
        return {"theme": session.get("theme", "light")}

    return app

