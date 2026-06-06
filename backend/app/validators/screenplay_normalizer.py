from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


_APP_ROOT = Path(__file__).resolve().parents[3]
_OMIT = object()


# screenplay_normalizer.py — 导出前的 schema-aware 清洗层。
# 这层不放宽 schema，也不跳过校验；它只把模型或 fake provider 产生的
# None/null 按 schema 语义删除或补成最小合法值，确保后续校验能报告真正
# 的结构问题，而不是被无意义的 null 卡住。


def normalize_screenplay_for_export(data: dict[str, Any], schema_path: Path | None = None) -> dict[str, Any]:
    """按 screenplay JSON Schema 递归清洗导出数据。"""
    schema_file = schema_path or (_APP_ROOT / "schemas" / "screenplay.schema.json")
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    normalized = _normalize_value(copy.deepcopy(data), schema, schema, required=True, key=None, path=[])
    return normalized if isinstance(normalized, dict) else {}


def _resolve_schema(schema: dict[str, Any], root_schema: dict[str, Any]) -> dict[str, Any]:
    ref = schema.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
        return schema
    target: Any = root_schema
    for part in ref.lstrip("#/").split("/"):
        target = target.get(part, {}) if isinstance(target, dict) else {}
    if not isinstance(target, dict):
        return schema
    merged = dict(target)
    merged.update({key: value for key, value in schema.items() if key != "$ref"})
    return merged


def _schema_type(schema: dict[str, Any]) -> str | None:
    value = schema.get("type")
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        for item in value:
            if item != "null":
                return item
    return None


def _normalize_value(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    *,
    required: bool,
    key: str | None,
    path: list[str],
) -> Any:
    schema = _resolve_schema(schema, root_schema)
    schema_type = _schema_type(schema)

    if value is None:
        if not required:
            return _OMIT
        return _default_for_schema(schema, root_schema, key, path)

    if schema_type == "object" and isinstance(value, dict):
        return _normalize_object(value, schema, root_schema, path)
    if schema_type == "array":
        return _normalize_array(value, schema, root_schema, required=required, key=key, path=path)
    if schema_type == "string":
        return value if isinstance(value, str) else str(value)
    if schema_type == "integer" and not isinstance(value, int):
        return _default_for_schema(schema, root_schema, key, path)
    if schema_type == "number" and not isinstance(value, (int, float)):
        return _default_for_schema(schema, root_schema, key, path)
    if schema_type == "boolean" and not isinstance(value, bool):
        return bool(value)
    return value


def _normalize_object(
    value: dict[str, Any],
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: list[str],
) -> dict[str, Any]:
    properties = schema.get("properties", {})
    required_keys = set(schema.get("required", []))
    normalized: dict[str, Any] = {}

    for prop_key, prop_schema in properties.items():
        prop_required = prop_key in required_keys
        if prop_key in value:
            prop_value = _normalize_value(
                value[prop_key],
                prop_schema,
                root_schema,
                required=prop_required,
                key=prop_key,
                path=[*path, prop_key],
            )
            if prop_value is not _OMIT:
                normalized[prop_key] = prop_value
        elif prop_required:
            normalized[prop_key] = _default_for_schema(prop_schema, root_schema, prop_key, [*path, prop_key])

    additional = schema.get("additionalProperties", True)
    for prop_key, prop_value in value.items():
        if prop_key in properties:
            continue
        if prop_value is None:
            continue
        if isinstance(additional, dict):
            cleaned = _normalize_value(
                prop_value,
                additional,
                root_schema,
                required=False,
                key=prop_key,
                path=[*path, prop_key],
            )
            if cleaned is not _OMIT:
                normalized[prop_key] = cleaned
        elif additional is not False:
            normalized[prop_key] = _drop_none_unknown(prop_value)
    return normalized


def _normalize_array(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    *,
    required: bool,
    key: str | None,
    path: list[str],
) -> list[Any]:
    if value is None:
        items: list[Any] = []
    elif isinstance(value, list):
        items = value
    else:
        items = [value]

    item_schema = schema.get("items", {})
    normalized: list[Any] = []
    for index, item in enumerate(items):
        if item is None:
            continue
        cleaned = _normalize_value(
            item,
            item_schema if isinstance(item_schema, dict) else {},
            root_schema,
            required=False,
            key=key,
            path=[*path, str(index)],
        )
        if cleaned is not _OMIT:
            normalized.append(cleaned)

    min_items = schema.get("minItems", 0) if required else 0
    while len(normalized) < min_items:
        normalized.append(_default_for_schema(item_schema if isinstance(item_schema, dict) else {}, root_schema, key, path))
    return normalized


def _drop_none_unknown(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _drop_none_unknown(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_drop_none_unknown(item) for item in value if item is not None]
    return value


def _default_for_schema(
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    key: str | None,
    path: list[str],
) -> Any:
    schema = _resolve_schema(schema, root_schema)
    schema_type = _schema_type(schema)
    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        return _enum_default(key, enum)
    if "const" in schema:
        return schema["const"]
    if schema_type == "object":
        return _normalize_object({}, schema, root_schema, path)
    if schema_type == "array":
        return _normalize_array([], schema, root_schema, required=True, key=key, path=path)
    if schema_type == "integer":
        return int(schema.get("minimum", 0))
    if schema_type == "number":
        return float(schema.get("minimum", 0))
    if schema_type == "boolean":
        return False
    value = _string_default(key, path)
    if schema.get("minLength", 0) > 0 and value == "":
        return "待补文本"
    return value


def _enum_default(key: str | None, enum: list[Any]) -> Any:
    if key in {"time", "time_of_day"} and "day" in enum:
        return "day"
    if key == "interior_exterior" and "INT" in enum:
        return "INT"
    if key == "block_type" and "action" in enum:
        return "action"
    if key == "fidelity_level" and "medium" in enum:
        return "medium"
    return enum[0]


def _string_default(key: str | None, path: list[str]) -> str:
    dotted = ".".join(path)
    if key in {"time", "time_of_day"}:
        return "day"
    if key == "interior_exterior":
        return "INT"
    if key == "block_type":
        return "action"
    if key == "status":
        return "open"
    if key == "unit":
        return "scene"
    if key == "target_format":
        return "general"
    if key == "title":
        return "未命名"
    if key == "name":
        return "未命名"
    if key == "location":
        return "未指定"
    if key == "line":
        return "待补台词"
    if key == "text":
        return "待补文本"
    if key == "purpose":
        return "待补目的"
    if key == "description":
        return "待补描述"
    if key == "summary":
        return "待补摘要"
    if key == "chapter_id":
        return "chapter_001"
    if key in {"scene_id", "payoff_scene_id"}:
        return "scene_001"
    if key in {"event_id", "related_event_id", "setup_event_id", "payoff_event_id"}:
        return "event_001"
    if key == "character_id":
        return "char_001"
    if key in {"from", "to"}:
        return "event_001" if "causal" in dotted.lower() else "char_001"
    if key == "id":
        return _id_default_for_path(dotted)
    return ""


def _id_default_for_path(path: str) -> str:
    lowered = path.lower()
    if "chapters" in lowered or "sourcechapter" in lowered:
        return "chapter_001"
    if "characters" in lowered or "character" in lowered:
        return "char_001"
    if "relationship" in lowered:
        return "rel_001"
    if "events" in lowered or "event" in lowered:
        return "event_001"
    if "foreshadow" in lowered:
        return "foreshadow_001"
    if "outline" in lowered:
        return "outline_001"
    if "actions" in lowered:
        return "action_001"
    if "situations" in lowered:
        return "situation_001"
    if "content_blocks" in lowered or "block" in lowered:
        return "block_001"
    if "dialogue" in lowered or "line" in lowered:
        return "line_001"
    if "scenes" in lowered or "scene" in lowered:
        return "scene_001"
    return "id_001"
