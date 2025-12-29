"""
Хранилище шаблонов метаданных.
"""

from __future__ import annotations

import json
from typing import List, Optional
from uuid import uuid4

from flask import current_app


def _store_path():
    return current_app.config["METADATA_STORE"]


def _read_store() -> List[dict]:
    path = _store_path()
    if not path.exists():
        path.write_text("[]", encoding="utf-8")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _write_store(data: List[dict]) -> None:
    path = _store_path()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_templates() -> List[dict]:
    return _read_store()


def get_template(template_id: str) -> Optional[dict]:
    return next((tpl for tpl in _read_store() if tpl["id"] == template_id), None)


def create_template(data: dict) -> dict:
    template = {
        "id": str(uuid4()),
        "name": data.get("name", "Шаблон метаданных"),
        "pk_prefix": data.get("pk_prefix", ""),
        "pk_id": data.get("pk_id", ""),
        "ipk_prefix": data.get("ipk_prefix", ""),
        "ipk_id": data.get("ipk_id", ""),
        "description": data.get("description", ""),
    }
    templates = _read_store()
    templates.append(template)
    _write_store(templates)
    return template


def update_template(template_id: str, data: dict) -> bool:
    templates = _read_store()
    changed = False
    for template in templates:
        if template["id"] == template_id:
            template.update(
                {
                    "name": data.get("name", template["name"]),
                    "pk_prefix": data.get("pk_prefix", template["pk_prefix"]),
                    "pk_id": data.get("pk_id", template["pk_id"]),
                    "ipk_prefix": data.get("ipk_prefix", template["ipk_prefix"]),
                    "ipk_id": data.get("ipk_id", template["ipk_id"]),
                    "description": data.get("description", template["description"]),
                }
            )
            changed = True
            break
    if changed:
        _write_store(templates)
    return changed


def delete_template(template_id: str) -> bool:
    templates = _read_store()
    new_templates = [tpl for tpl in templates if tpl["id"] != template_id]
    if len(new_templates) == len(templates):
        return False
    _write_store(new_templates)
    return True





