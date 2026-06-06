from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.validators.schema_validator import SchemaValidator
from app.validators.screenplay_normalizer import normalize_screenplay_for_export


def test_normalize_screenplay_removes_none_string_fields() -> None:
    """导出前清洗应处理 optional/required string 中的 None，并保持 schema 合法。"""
    root = Path(__file__).resolve().parents[2]
    screenplay = json.loads((root / "fixtures" / "demo_screenplay.json").read_text(encoding="utf-8"))
    dirty = copy.deepcopy(screenplay)

    dirty["project"]["logline"] = None
    dirty["scenes"][0]["dialogue"][0]["subtext"] = None
    dirty["scenes"][0]["content_blocks"][0]["text"] = None
    dirty["story_bible"]["characters"][0]["name"] = None
    dirty["adaptation_plan"]["scene_plan"][0]["purpose"] = None

    normalized = normalize_screenplay_for_export(dirty)
    errors = [finding for finding in SchemaValidator().validate(normalized) if finding.severity == "error"]

    assert errors == []
    assert "logline" not in normalized["project"]
    assert "subtext" not in normalized["scenes"][0]["dialogue"][0]
    assert normalized["scenes"][0]["content_blocks"][0]["text"] == "待补文本"
    assert normalized["story_bible"]["characters"][0]["name"] == "未命名"
    assert normalized["adaptation_plan"]["scene_plan"][0]["purpose"] == "待补目的"
