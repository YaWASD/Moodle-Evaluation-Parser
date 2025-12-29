"""
Локальный журнал действий пользователя.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from flask import session


def log(action: str, details: str) -> None:
    history = session.get("history", [])
    history.append(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
        }
    )
    session["history"] = history[-200:]
    session.modified = True


def list_history() -> List[dict]:
    return session.get("history", [])










