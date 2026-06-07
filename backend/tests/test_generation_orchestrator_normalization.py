from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.generation_orchestrator import (
    _resolve_char_id,
    _normalize_event_id,
    _normalize_char_id,
    _normalize_foreshadowing_id,
    _resolve_event_id,
    _auto_register_missing_characters,
    _normalize_source_refs_list,
)


# ── _resolve_char_id ────────────────────────────────────────────────────────

def test_resolve_char_id_maps_descriptive_id_through_lookup() -> None:
    """描述性角色 ID 只能映射到 story_bible 中已经存在的 canonical character。"""
    lookup = {"白浅": "char_001", "baiqian": "char_001", "夜华": "char_002"}

    assert _resolve_char_id("char_baiqian", lookup) == "char_001"


def test_resolve_char_id_keeps_unknown_descriptive_id_for_validation() -> None:
    """无法确认的角色引用应保留原值，让 validator 产出可追踪错误。"""
    lookup = {"白浅": "char_001"}

    assert _resolve_char_id("char_unknown", lookup) == "char_unknown"


def test_resolve_char_id_does_not_guess_from_partial_alias() -> None:
    """片段匹配可能误指向合法角色，因此不能绕过后续引用校验。"""
    lookup = {"baiqian": "char_001", "qianqian": "char_002"}

    assert _resolve_char_id("char_qian", lookup) == "char_qian"


# ── _normalize_event_id ─────────────────────────────────────────────────────

def test_normalize_event_id_pads_zero() -> None:
    """event_1 → event_001, event_12 → event_012"""
    assert _normalize_event_id("event_1") == "event_001"
    assert _normalize_event_id("event_12") == "event_012"


def test_normalize_event_id_passes_through_valid() -> None:
    """Already valid event_001 stays event_001"""
    assert _normalize_event_id("event_001") == "event_001"


def test_normalize_event_id_evt_prefix() -> None:
    """evt_001 → event_001"""
    assert _normalize_event_id("evt_001") == "event_001"


def test_normalize_event_id_descriptive_with_number() -> None:
    """event_merged_01 → event_001 via rsplit fallback"""
    assert _normalize_event_id("event_merged_01") == "event_001"
    assert _normalize_event_id("event_custom_99") == "event_099"


def test_normalize_event_id_pure_number() -> None:
    """'42' → event_042"""
    assert _normalize_event_id("42") == "event_042"


def test_normalize_event_id_unknown_format_kept() -> None:
    """Completely non-matching IDs stay as-is for validation"""
    assert _normalize_event_id("some_garbled_id") == "some_garbled_id"
    assert _normalize_event_id("") == ""


# ── _normalize_char_id ──────────────────────────────────────────────────────

def test_normalize_char_id_descriptive_with_number() -> None:
    """char_baiqian_01 → char_001 via rsplit fallback"""
    assert _normalize_char_id("char_baiqian_01") == "char_001"


def test_normalize_char_id_pads_zero() -> None:
    """char_1 → char_001"""
    assert _normalize_char_id("char_1") == "char_001"


# ── _resolve_event_id ───────────────────────────────────────────────────────

def test_resolve_event_id_normalizes_before_lookup() -> None:
    """event_merged_01 normalizes to event_001, which matches schema"""
    lookup = {"素锦陷害素素": "event_001", "素素生子": "event_002"}
    result = _resolve_event_id("event_merged_01", lookup)
    assert result == "event_001"


def test_resolve_event_id_uses_lookup_for_evt_ids() -> None:
    """evt_arrival resolves through lookup by name_part"""
    lookup = {"arrival": "event_003", "arrival at the palace": "event_003"}
    result = _resolve_event_id("evt_arrival", lookup)
    assert result == "event_003"


def test_resolve_event_id_keeps_valid_id() -> None:
    """Already valid event_001 passes through"""
    lookup = {"素锦陷害素素": "event_001"}
    assert _resolve_event_id("event_001", lookup) == "event_001"


# ── _resolve_char_id: Chinese name fuzzy matching ───────────────────────────

def test_resolve_char_id_maps_chinese_name_directly() -> None:
    """LLM outputs '素素' instead of char_001 → resolved via name lookup"""
    lookup = {"素素": "char_001", "白浅": "char_001", "夜华": "char_002"}
    assert _resolve_char_id("素素", lookup) == "char_001"


def test_resolve_char_id_maps_substring_chinese_name() -> None:
    """LLM outputs '白浅' but lookup has '素素/白浅' → fuzzy match"""
    lookup = {"素素/白浅": "char_001", "夜华": "char_002"}
    assert _resolve_char_id("白浅", lookup) == "char_001"


def test_resolve_char_id_maps_via_alias_substring() -> None:
    """LLM outputs '青丘白浅' but alias is '青丘白浅上神' → fuzzy match"""
    lookup = {"青丘白浅上神": "char_001"}
    assert _resolve_char_id("青丘白浅", lookup) == "char_001"


# ── _auto_register_missing_characters ──────────────────────────────────────


def test_auto_register_adds_missing_chinese_names_in_events() -> None:
    """events 中出现 story_bible 未收录的中文名时，自动注册为 char_NNN。

    复现 bug: '多宝元君' does not match '^char_[0-9]{3}$' at events.7.participants.1
    """
    screenplay = {
        "story_bible": {
            "characters": [
                {"id": "char_001", "name": "白浅", "aliases": ["司音"]},
                {"id": "char_002", "name": "夜华", "aliases": []},
            ]
        },
        "events": [
            {
                "id": "event_001",
                "title": "仙宴登场",
                "participants": ["char_001", "多宝元君", "南斗真君"],
            }
        ],
        "scenes": [],
    }
    initial_lookup = {"白浅": "char_001", "司音": "char_001", "夜华": "char_002"}

    updated = _auto_register_missing_characters(screenplay, initial_lookup)

    # 新角色应已注册
    assert "多宝元君" in updated
    assert "南斗真君" in updated
    assert updated["多宝元君"] == "char_003"
    assert updated["南斗真君"] == "char_004"

    # story_bible.characters 应已追加
    chars = screenplay["story_bible"]["characters"]
    assert len(chars) == 4
    assert chars[2]["name"] == "多宝元君"
    assert chars[2]["id"] == "char_003"
    assert chars[2]["_auto_registered"] is True
    assert chars[3]["name"] == "南斗真君"
    assert chars[3]["id"] == "char_004"


def test_auto_register_skips_already_resolvable_names() -> None:
    """已在 lookup 中的中文名不应被重复注册。"""
    screenplay = {
        "story_bible": {
            "characters": [
                {"id": "char_001", "name": "白浅", "aliases": []},
            ]
        },
        "events": [
            {"id": "event_001", "title": "test", "participants": ["白浅"]}
        ],
        "scenes": [],
    }
    initial_lookup = {"白浅": "char_001"}

    updated = _auto_register_missing_characters(screenplay, initial_lookup)

    # 不应重复注册
    assert len(screenplay["story_bible"]["characters"]) == 1
    assert updated == initial_lookup


def test_auto_register_skips_valid_char_ids() -> None:
    """已经是合法 char_NNN 格式的 ID 不应被处理。"""
    screenplay = {
        "story_bible": {
            "characters": [
                {"id": "char_001", "name": "白浅", "aliases": []},
            ]
        },
        "events": [
            {"id": "event_001", "title": "test", "participants": ["char_001", "char_005"]}
        ],
        "scenes": [],
    }
    initial_lookup = {"白浅": "char_001"}

    updated = _auto_register_missing_characters(screenplay, initial_lookup)

    # char_001 和 char_005 都是合法格式，不应触发注册
    assert len(screenplay["story_bible"]["characters"]) == 1


def test_auto_register_handles_scenes_characters() -> None:
    """scenes.characters 中的未注册中文名也应被自动注册。"""
    screenplay = {
        "story_bible": {"characters": []},
        "events": [],
        "scenes": [
            {"id": "scene_001", "characters": ["南极仙翁"]}
        ],
    }

    updated = _auto_register_missing_characters(screenplay, {})

    assert "南极仙翁" in updated
    assert updated["南极仙翁"] == "char_001"


def test_auto_register_returns_unchanged_lookup_when_nothing_to_add() -> None:
    """没有需要注册的角色时，返回原 lookup（非同一对象但内容相等）。"""
    screenplay = {
        "story_bible": {"characters": []},
        "events": [],
        "scenes": [],
    }

    result = _auto_register_missing_characters(screenplay, {})

    assert result == {}


# ── _normalize_source_refs_list: phantom chapter remapping ─────────────────


def test_source_refs_remaps_hallucinated_chapter_id() -> None:
    """LLM 引用了不存在的 chapter_000（楔子），自动重映射到 chapter_001。

    复现 bug: "Scene scene_001 references missing chapter chapter_000"
    """
    refs = [{"chapter_id": "chapter_000", "event_ids": ["event_001"]}]
    valid = {"chapter_001", "chapter_002", "chapter_003"}

    result = _normalize_source_refs_list(refs, "chapter_001", valid)

    assert result[0]["chapter_id"] == "chapter_001"
    # event_ids 旧格式字段应被移除
    assert "event_ids" not in result[0]


def test_source_refs_keeps_valid_chapter_id() -> None:
    """合法的 chapter_002 不应被重映射。"""
    refs = [{"chapter_id": "chapter_002"}]
    valid = {"chapter_001", "chapter_002", "chapter_003"}

    result = _normalize_source_refs_list(refs, "chapter_001", valid)

    assert result[0]["chapter_id"] == "chapter_002"


def test_source_refs_handles_string_ref_with_colon() -> None:
    """"chapter_000:p_005" 格式的字符串引用应被解析并重映射。"""
    refs = ["chapter_000:p_005"]
    valid = {"chapter_001", "chapter_002"}

    result = _normalize_source_refs_list(refs, "chapter_001", valid)

    assert result[0]["chapter_id"] == "chapter_001"
    assert result[0]["paragraph_range"] == "p_005"


def test_source_refs_no_valid_set_means_no_remapping() -> None:
    """未提供 valid_chapter_ids 时，不重映射（向后兼容）。"""
    refs = [{"chapter_id": "chapter_000"}]

    result = _normalize_source_refs_list(refs, "chapter_001")

    # 不改动，留给 validator 处理
    assert result[0]["chapter_id"] == "chapter_000"


# ── _normalize_foreshadowing_id ─────────────────────────────────────────────


def test_normalize_foreshadowing_id_fsh_prefix() -> None:
    """fsh_001 → foreshadow_001, fsh_1 → foreshadow_001"""
    assert _normalize_foreshadowing_id("fsh_001") == "foreshadow_001"
    assert _normalize_foreshadowing_id("fsh_1") == "foreshadow_001"
    assert _normalize_foreshadowing_id("fsh_005") == "foreshadow_005"


def test_normalize_foreshadowing_id_pads_zero() -> None:
    """foreshadow_1 → foreshadow_001"""
    assert _normalize_foreshadowing_id("foreshadow_1") == "foreshadow_001"
    assert _normalize_foreshadowing_id("foreshadow_12") == "foreshadow_012"


def test_normalize_foreshadowing_id_passes_through_valid() -> None:
    """已合法的不变"""
    assert _normalize_foreshadowing_id("foreshadow_001") == "foreshadow_001"


def test_normalize_foreshadowing_id_foreshadowing_prefix() -> None:
    """foreshadowing_01 → foreshadow_001"""
    assert _normalize_foreshadowing_id("foreshadowing_01") == "foreshadow_001"


def test_normalize_foreshadowing_id_fs_prefix() -> None:
    """fs_001 → foreshadow_001"""
    assert _normalize_foreshadowing_id("fs_001") == "foreshadow_001"


def test_normalize_foreshadowing_id_pure_number() -> None:
    """"5" → foreshadow_005"""
    assert _normalize_foreshadowing_id("5") == "foreshadow_005"


def test_normalize_foreshadowing_id_unknown_kept() -> None:
    """无法识别的 ID 保持原样"""
    assert _normalize_foreshadowing_id("some_garbled") == "some_garbled"
    assert _normalize_foreshadowing_id("") == ""
