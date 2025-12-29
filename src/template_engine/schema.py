from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypedDict


SchemaVersion = Literal[2]


class StylesV2(TypedDict, total=False):
    header_color: str
    title_size: int
    header_size: int
    body_size: int
    answer_size: int


class BlockLine(TypedDict, total=False):
    kind: Literal["line"]
    pattern: str  # e.g. "{{question.text}} — {{question.answer}}"


class BlockSpacer(TypedDict, total=False):
    kind: Literal["spacer"]
    mm: int


class BlockList(TypedDict, total=False):
    kind: Literal["list"]
    source: Literal[
        "answers_all",
        "answers_correct",
        "matching_pairs",
    ]
    pattern: str  # supports {{item}} or {{item.item}}/{{item.answer}}
    bullet: bool


class BlockTable(TypedDict, total=False):
    kind: Literal["table"]
    source: Literal[
        "answers_all",
        "answers_correct",
        "matching_pairs",
    ]
    headers: list[str]  # same length as cols
    cols: list[str]  # expressions per cell, supports item fields
    col_widths_pct: list[int]


TemplateBlock = BlockLine | BlockList | BlockTable | BlockSpacer


class TemplateConfigV2(TypedDict, total=False):
    version: SchemaVersion
    styles: StylesV2
    blocks: list[TemplateBlock]


@dataclass(frozen=True)
class RenderContext:
    question: dict[str, Any]
    metadata: dict[str, Any]


