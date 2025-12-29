"""
Сохранение и загрузка данных обработки XML.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flask import current_app


def _snapshot_dir() -> Path:
    return Path(current_app.config["TEMP_FOLDER"])


def _snapshot_path(file_id: str) -> Path:
    return _snapshot_dir() / f"{file_id}.json"


def save_snapshot(file_id: str, data: dict[str, Any]) -> None:
    """Сохраняет результаты парсинга во временный файл."""
    path = _snapshot_path(file_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_snapshot(file_id: str) -> dict[str, Any] | None:
    """Загружает результаты парсинга, если они существуют."""
    path = _snapshot_path(file_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))



