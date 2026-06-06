from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.generation_orchestrator import _resolve_char_id, _normalize_event_id, _normalize_char_id, _resolve_event_id


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
