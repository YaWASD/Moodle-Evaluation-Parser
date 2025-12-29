from __future__ import annotations

from typing import Any


def validate_template_config_v2(cfg: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(cfg, dict):
        return ["config is not an object"]
    if cfg.get("version") != 2:
        errors.append("config.version must be 2")

    styles = cfg.get("styles", {})
    if styles is not None and not isinstance(styles, dict):
        errors.append("config.styles must be an object")

    blocks = cfg.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        errors.append("config.blocks must be a non-empty list")
        return errors

    for i, b in enumerate(blocks):
        if not isinstance(b, dict):
            errors.append(f"blocks[{i}] must be an object")
            continue
        kind = b.get("kind")
        if kind not in {"line", "list", "table", "spacer"}:
            errors.append(f"blocks[{i}].kind invalid: {kind}")
            continue
        if kind == "line":
            if not isinstance(b.get("pattern"), str) or not b["pattern"].strip():
                errors.append(f"blocks[{i}].pattern is required")
        elif kind == "spacer":
            mm = b.get("mm", 4)
            if not isinstance(mm, int) or mm < 0 or mm > 50:
                errors.append(f"blocks[{i}].mm must be int 0..50")
        elif kind == "list":
            if b.get("source") not in {"answers_all", "answers_correct", "matching_pairs"}:
                errors.append(f"blocks[{i}].source invalid")
            if not isinstance(b.get("pattern"), str) or not b["pattern"].strip():
                errors.append(f"blocks[{i}].pattern is required")
        elif kind == "table":
            if b.get("source") not in {"answers_all", "answers_correct", "matching_pairs"}:
                errors.append(f"blocks[{i}].source invalid")
            cols = b.get("cols")
            if not isinstance(cols, list) or not cols:
                errors.append(f"blocks[{i}].cols must be a non-empty list")
            else:
                if not all(isinstance(c, str) and c.strip() for c in cols):
                    errors.append(f"blocks[{i}].cols must contain non-empty strings")
            headers = b.get("headers")
            if headers is not None:
                if not isinstance(headers, list) or (cols and len(headers) != len(cols)):
                    errors.append(f"blocks[{i}].headers must match cols length")
            widths = b.get("col_widths_pct")
            if widths is not None:
                if not isinstance(widths, list) or not all(isinstance(x, int) for x in widths):
                    errors.append(f"blocks[{i}].col_widths_pct must be list[int]")

    return errors


