"""
Хранилище пользовательских шаблонов вопросов.
"""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4
from typing import Any, List, Optional

from flask import current_app


def _store_path():
    return current_app.config["TEMPLATE_STORE"]


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


def save_template(data: dict) -> dict:
    templates = _read_store()
    now = datetime.utcnow().isoformat()
    template = {
        "id": str(uuid4()),
        "name": data.get("name", "Без названия"),
        "type": data.get("type", ""),
        "description": data.get("description", ""),
        "config": data.get("config", "{}"),
        "schema_version": data.get("schema_version"),
        "created_at": now,
        "updated_at": now,
        "revisions": [],
    }
    templates.append(template)
    _write_store(templates)
    return template


def update_template(template_id: str, data: dict) -> bool:
    templates = _read_store()
    updated = False
    for template in templates:
        if template["id"] == template_id:
            # minimal revision history (keep last 10)
            revs = template.get("revisions", [])
            if isinstance(revs, list):
                revs.append(
                    {
                        "updated_at": datetime.utcnow().isoformat(),
                        "name": template.get("name"),
                        "type": template.get("type"),
                        "description": template.get("description"),
                        "config": template.get("config"),
                        "schema_version": template.get("schema_version"),
                    }
                )
                template["revisions"] = revs[-10:]
            template.update(
                {
                    "name": data.get("name", template["name"]),
                    "type": data.get("type", template["type"]),
                    "description": data.get("description", template.get("description", "")),
                    "config": data.get("config", template["config"]),
                    "schema_version": data.get("schema_version", template.get("schema_version")),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )
            updated = True
            break
    if updated:
        _write_store(templates)
    return updated


def delete_template(template_id: str) -> bool:
    templates = _read_store()
    new_templates = [tpl for tpl in templates if tpl["id"] != template_id]
    if len(new_templates) == len(templates):
        return False
    _write_store(new_templates)
    return True


def import_template(payload: dict) -> dict:
    template = {
        "id": str(uuid4()),
        "name": payload.get("name", "Импортированный шаблон"),
        "type": payload.get("type", ""),
        "description": payload.get("description", ""),
        "config": payload.get("config", "{}"),
    }
    templates = _read_store()
    templates.append(template)
    _write_store(templates)
    return template



