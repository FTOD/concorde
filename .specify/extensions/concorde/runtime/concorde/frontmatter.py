"""Parser for Concorde Architecture Source Profile 1 front matter."""

from __future__ import annotations

import json
import re
from typing import Any


class FrontMatterError(ValueError):
    def __init__(self, message: str, source: str = "", line: int | None = None):
        self.source = source
        self.line = line
        location = f"{source}:{line}: " if source and line else f"{source}: " if source else ""
        super().__init__(location + message)


_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
_INTEGER = re.compile(r"^-?[0-9]+$")


def _scalar(value: str, source: str, line: int) -> Any:
    value = value.strip()
    if not value:
        return None
    if any(token in value for token in ("&", "*", "!", "<<:")):
        raise FrontMatterError("unsupported YAML tag, anchor, alias, or merge key", source, line)
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if value in {"null", "~"}:
        return None
    if value in {"true", "false"}:
        return value == "true"
    if _INTEGER.fullmatch(value):
        return int(value)
    if value.startswith("[") or value.startswith("{"):
        try:
            return json.loads(value)
        except json.JSONDecodeError as error:
            raise FrontMatterError("inline collections must use JSON-compatible syntax", source, line) from error
    if value.startswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError as error:
            raise FrontMatterError("invalid quoted string", source, line) from error
    if value.startswith("'"):
        if not value.endswith("'"):
            raise FrontMatterError("unterminated quoted string", source, line)
        return value[1:-1].replace("''", "'")
    if value.startswith(("|", ">")):
        raise FrontMatterError("block scalars are not supported by Profile 1", source, line)
    return value


def _meaningful(lines: list[str], source: str) -> list[tuple[int, int, str]]:
    result: list[tuple[int, int, str]] = []
    for number, raw in enumerate(lines, start=2):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise FrontMatterError("indentation must use spaces", source, number)
        indent = len(raw) - len(raw.lstrip(" "))
        if indent % 2:
            raise FrontMatterError("indentation must be in multiples of two", source, number)
        result.append((number, indent, raw.strip()))
    return result


def _parse_block(
    tokens: list[tuple[int, int, str]], index: int, indent: int, source: str
) -> tuple[Any, int]:
    if index >= len(tokens) or tokens[index][1] < indent:
        return {}, index
    is_list = tokens[index][2].startswith("- ") or tokens[index][2] == "-"
    container: Any = [] if is_list else {}
    while index < len(tokens):
        line, current_indent, text = tokens[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise FrontMatterError("unexpected indentation", source, line)
        if is_list:
            if not text.startswith("-"):
                break
            item = text[1:].strip()
            if not item:
                value, index = _parse_block(tokens, index + 1, indent + 2, source)
                container.append(value)
                continue
            if ":" in item:
                key, raw_value = item.split(":", 1)
                if not _KEY.fullmatch(key.strip()):
                    raise FrontMatterError("invalid mapping key", source, line)
                record: dict[str, Any] = {}
                if raw_value.strip():
                    record[key.strip()] = _scalar(raw_value, source, line)
                    index += 1
                else:
                    value, index = _parse_block(tokens, index + 1, indent + 2, source)
                    record[key.strip()] = value
                if index < len(tokens) and tokens[index][1] == indent + 2 and not tokens[index][2].startswith("-"):
                    continuation, index = _parse_block(tokens, index, indent + 2, source)
                    record.update(continuation)
                container.append(record)
                continue
            container.append(_scalar(item, source, line))
            index += 1
        else:
            if text.startswith("-") or ":" not in text:
                raise FrontMatterError("expected key: value mapping", source, line)
            key, raw_value = text.split(":", 1)
            key = key.strip()
            if not _KEY.fullmatch(key):
                raise FrontMatterError("invalid mapping key", source, line)
            if key in container:
                raise FrontMatterError(f"duplicate key '{key}'", source, line)
            if raw_value.strip():
                container[key] = _scalar(raw_value, source, line)
                index += 1
            else:
                if index + 1 >= len(tokens) or tokens[index + 1][1] <= indent:
                    container[key] = {}
                    index += 1
                else:
                    value, index = _parse_block(tokens, index + 1, indent + 2, source)
                    container[key] = value
    return container, index


def parse_document(text: str, source: str = "") -> tuple[dict[str, Any], str]:
    normalized = text.replace("\r\n", "\n")
    lines = normalized.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontMatterError("document must begin with a front-matter fence", source, 1)
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as error:
        raise FrontMatterError("front matter has no closing fence", source, 1) from error
    tokens = _meaningful(lines[1:end], source)
    metadata, consumed = _parse_block(tokens, 0, 0, source) if tokens else ({}, 0)
    if consumed != len(tokens) or not isinstance(metadata, dict):
        line = tokens[consumed][0] if consumed < len(tokens) else 1
        raise FrontMatterError("invalid top-level mapping", source, line)
    return metadata, "\n".join(lines[end + 1 :]).lstrip("\n") + ("\n" if end + 1 < len(lines) else "")
