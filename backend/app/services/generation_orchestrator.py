from __future__ import annotations

import logging
from typing import Any

from app.ai.providers.base import AiProviderConfigurationError
from app.ai.providers.factory import build_ai_provider
from app.ai.skills.novel_reader import NovelReaderSkill
from app.ai.skills.screenplay_writer import ScreenplayYamlWriterSkill
from app.ai.skills.story_ontology import StoryOntologySkill
from app.core.settings import AiSettings
from app.domain.adaptation import AdaptationConfig
from app.domain.jobs import GenerationJob
from app.services.artifact_service import ArtifactService
from app.services.job_service import JobService
from app.services.llm_trace_service import LlmTraceService
from app.services.project_service import ProjectService
from app.services.validation_service import ValidationService
from app.services.yaml_service import YamlService
from app.services.screenplay_render_service import ScreenplayRenderService
from app.repositories.file_store import default_data_root
from app.validators.screenplay_normalizer import normalize_screenplay_for_export


logger = logging.getLogger(__name__)


_TIME_OF_DAY_LABELS = {
    "day": "日",
    "night": "夜",
    "morning": "晨",
    "dusk": "昏",
}

_TIME_OF_DAY_ALIASES = {
    "day": "day",
    "日": "day",
    "night": "night",
    "夜": "night",
    "morning": "morning",
    "晨": "morning",
    "dawn": "morning",
    "dusk": "dusk",
    "昏": "dusk",
    "evening": "dusk",
}

_INTERIOR_EXTERIOR_LABELS = {
    "INT": "内景",
    "EXT": "外景",
    "INT/EXT": "内外景",
}

_INTERIOR_EXTERIOR_ALIASES = {
    "INT": "INT",
    "内景": "INT",
    "EXT": "EXT",
    "外景": "EXT",
    "INT/EXT": "INT/EXT",
    "内外景": "INT/EXT",
}


def _normalize_time_of_day(value: Any) -> str:
    """把模型可能输出的中文或英文时间段压到 schema enum。"""
    if isinstance(value, str):
        return _TIME_OF_DAY_ALIASES.get(value.strip(), _TIME_OF_DAY_ALIASES.get(value.strip().lower(), "day"))
    return "day"


def _normalize_interior_exterior(value: Any) -> str:
    """把内景/外景显示词压到联调用的 INT/EXT enum。"""
    if isinstance(value, str):
        return _INTERIOR_EXTERIOR_ALIASES.get(value.strip(), _INTERIOR_EXTERIOR_ALIASES.get(value.strip().upper(), "INT"))
    return "INT"


def _normalize_location_payload(location: Any) -> dict[str, Any]:
    """统一 location 对象，供 location 字段和 scene_heading 共享同一份地点信息。"""
    if isinstance(location, str):
        normalized: dict[str, Any] = {"name": location}
    elif isinstance(location, dict):
        normalized = dict(location)
    else:
        normalized = {}

    normalized.setdefault("name", "未命名地点")
    normalized["time"] = _normalize_time_of_day(normalized.get("time"))
    normalized["interior_exterior"] = _normalize_interior_exterior(normalized.get("interior_exterior"))
    return normalized


def _scene_heading_text(sequence: int, location: str, interior_exterior: str, time_of_day: str) -> str:
    """生成可单独成行展示的文学剧本场景标题文本。"""
    interior_label = _INTERIOR_EXTERIOR_LABELS.get(interior_exterior, interior_exterior)
    time_label = _TIME_OF_DAY_LABELS.get(time_of_day, time_of_day)
    return f"{sequence}. {location} {interior_label} {time_label}"


def _normalize_scenes(
    scenes: list[dict[str, Any]],
    chapters: list[dict[str, Any]],
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    """将 LLM 输出的 scenes 归一化为 schema 要求的精确格式。

    LLM（尤其是小模型）可能会用简写格式输出 scenes 字段，例如：
    - source_refs 写成 ["evt_001"] 而非 [{"chapter_id": "...", "event_ids": [...]}]
    - dramatic_purpose / action 写成字符串而非数组
    - location 写成字符串而非对象
    - dialogue 用 speaker 而非 character_id，缺 id
    此函数做无损转换，补齐缺失的字段。
    """
    chapter_ids = [ch.get("id") for ch in chapters if ch.get("id")]
    default_chapter_id = chapter_ids[0] if chapter_ids else "chapter_001"

    normalized: list[dict[str, Any]] = []
    for scene_index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            continue

        # --- source_refs: 字符串 → 对象 (schema sourceRef 仅要求 chapter_id) ---
        raw_refs = scene.get("source_refs", [])
        if not raw_refs or not isinstance(raw_refs, list):
            scene["source_refs"] = [{"chapter_id": default_chapter_id}]
        elif isinstance(raw_refs[0], str):
            # DeepSeek 经常把 event ID 写进 source_refs；新 schema 中 source_refs 指向章节
            scene["source_refs"] = [{"chapter_id": default_chapter_id}]
        else:
            # 已经是对象列表，确保每条都有 chapter_id
            for ref in raw_refs:
                if isinstance(ref, dict):
                    ref.setdefault("chapter_id", default_chapter_id)
                    # 移除旧格式的 event_ids（新 schema 的 sourceRef 没有此字段）
                    ref.pop("event_ids", None)
            scene["source_refs"] = raw_refs

        # --- related_events: 规范化事件 ID ---
        related = scene.get("related_events")
        if isinstance(related, list):
            scene["related_events"] = [_normalize_event_id(e) for e in related if isinstance(e, str)]

        # --- characters: 规范化角色 ID ---
        chars = scene.get("characters")
        if isinstance(chars, list):
            scene["characters"] = [_normalize_char_id(c) for c in chars if isinstance(c, str)]

        # --- dramatic_purpose: 字符串 → 数组 ---
        dp = scene.get("dramatic_purpose")
        if isinstance(dp, str):
            scene["dramatic_purpose"] = [dp]

        # --- location: 字符串 → 对象 ---
        scene["location"] = _normalize_location_payload(scene.get("location"))

        # --- scene_heading: 从 location 推导文学剧本标题 ---
        heading = scene.get("scene_heading")
        if not isinstance(heading, dict):
            heading = {}
        heading.setdefault("sequence", scene_index)
        heading.setdefault("location", scene["location"]["name"])
        heading["interior_exterior"] = _normalize_interior_exterior(
            heading.get("interior_exterior", scene["location"]["interior_exterior"])
        )
        heading["time_of_day"] = _normalize_time_of_day(heading.get("time_of_day", scene["location"]["time"]))
        heading.setdefault(
            "text",
            _scene_heading_text(
                heading["sequence"],
                heading["location"],
                heading["interior_exterior"],
                heading["time_of_day"],
            ),
        )
        scene["scene_heading"] = heading

        # --- action: 字符串 → 数组 ---
        act = scene.get("action")
        if isinstance(act, str):
            scene["action"] = [act]

        # --- dialogue 归一化 ---
        dialogue = scene.get("dialogue", [])
        norm_dialogue: list[dict[str, Any]] = []
        for idx, line in enumerate(dialogue):
            if not isinstance(line, dict):
                continue
            # id 缺失时自动生成
            if "id" not in line:
                line["id"] = f"line_{idx + 1:03d}"
            # speaker → character_id
            if "speaker" in line and "character_id" not in line:
                line["character_id"] = line.pop("speaker")
            norm_dialogue.append(line)
        scene["dialogue"] = norm_dialogue

        # --- content_blocks: 将动作和对白排列成 scene heading 下方的自然段正文 ---
        content_blocks = scene.get("content_blocks")
        if not isinstance(content_blocks, list) or not content_blocks:
            generated_blocks: list[dict[str, Any]] = []
            for action_text in scene.get("action", []):
                if isinstance(action_text, str) and action_text:
                    generated_blocks.append(
                        {
                            "id": f"block_{len(generated_blocks) + 1:03d}",
                            "block_type": "action",
                            "text": action_text,
                        }
                    )
            for line in norm_dialogue:
                line_text = line.get("line")
                if isinstance(line_text, str) and line_text:
                    generated_blocks.append(
                        {
                            "id": f"block_{len(generated_blocks) + 1:03d}",
                            "block_type": "dialogue",
                            "character_id": line.get("character_id"),
                            "dialogue_line_id": line.get("id"),
                            "text": line_text,
                        }
                    )
            scene["content_blocks"] = generated_blocks

        normalized.append(scene)

    return normalized


def _normalize_story_bible(story_bible: dict[str, Any]) -> dict[str, Any]:
    """确保 story_bible 含 schema 要求的必填字段，并统一 ID 格式。"""
    import re
    story_bible.setdefault("relationship_edges", [])
    story_bible.setdefault("knowledge_states", [])
    story_bible.setdefault("continuity_anchors", [])
    dramatic_assets = story_bible.get("dramatic_assets")
    if not isinstance(dramatic_assets, dict):
        dramatic_assets = {}
    dramatic_assets.setdefault("conflict_pool", [])
    dramatic_assets.setdefault("filmic_constraints", [])
    story_bible["dramatic_assets"] = dramatic_assets
    # 补全角色必填字段 + 规范化角色 ID
    characters = story_bible.get("characters", [])
    for idx, char in enumerate(characters):
        if isinstance(char, dict):
            raw_id = char.get("id", "")
            normalized = _normalize_char_id(raw_id)
            # 如果规范化后仍不是合法 char_NNN 格式，则基于索引生成
            if not re.match(r"^char_[0-9]{3}$", normalized):
                normalized = f"char_{(idx + 1):03d}"
            char["id"] = normalized
            # 确保 name 存在
            char.setdefault("name", char.get("name") or raw_id or normalized)
    # 规范化关系边
    edges = story_bible.get("relationship_edges", [])
    for idx, edge in enumerate(edges):
        if isinstance(edge, dict):
            if "id" not in edge or not edge["id"]:
                edge["id"] = f"rel_{idx + 1:03d}"
            # 规范化 from/to 角色 ID
            for key in ("from", "to"):
                if key in edge:
                    edge[key] = _normalize_char_id(edge[key])
            edge.setdefault("type", "unspecified")
    # 规范化 knowledge_states
    for ks in story_bible.get("knowledge_states", []):
        if isinstance(ks, dict) and "character_id" in ks:
            ks["character_id"] = _normalize_char_id(ks["character_id"])
    # Evidence fields are source-grounded facts; normalize IDs but do not invent content.
    for anchor in story_bible.get("continuity_anchors", []):
        if isinstance(anchor, dict):
            applies_to = anchor.get("applies_to")
            if isinstance(applies_to, list):
                anchor["applies_to"] = [_normalize_char_id(item) for item in applies_to if isinstance(item, str)]
    for conflict in dramatic_assets.get("conflict_pool", []):
        if isinstance(conflict, dict):
            participants = conflict.get("participants")
            if isinstance(participants, list):
                conflict["participants"] = [_normalize_char_id(item) for item in participants if isinstance(item, str)]
            related_events = conflict.get("related_events")
            if isinstance(related_events, list):
                conflict["related_events"] = [_normalize_event_id(item) for item in related_events if isinstance(item, str)]
    for constraint in dramatic_assets.get("filmic_constraints", []):
        if isinstance(constraint, dict):
            related_characters = constraint.get("related_characters")
            if isinstance(related_characters, list):
                constraint["related_characters"] = [
                    _normalize_char_id(item) for item in related_characters if isinstance(item, str)
                ]
            related_events = constraint.get("related_events")
            if isinstance(related_events, list):
                constraint["related_events"] = [_normalize_event_id(item) for item in related_events if isinstance(item, str)]
    return story_bible


def _normalize_event_id(raw: str) -> str:
    """将模型可能输出的各种事件 ID 统一为零填充的 event_NNN 格式。"""
    if not raw:
        return raw
    # event_N 或 event_NN → 补零到 event_NNN
    if raw.startswith("event_"):
        suffix = raw[6:]
        if suffix.isdigit():
            return f"event_{int(suffix):03d}"
        # 非纯数字后缀（如 event_merged_01）→ 继续尝试 rsplit
    # evt_001 → event_001
    if raw.startswith("evt_"):
        suffix = raw[4:]
        if suffix.isdigit():
            return f"event_{int(suffix):03d}"
        # 非纯数字后缀（如 evt_arrival_02）→ 继续尝试
    # 纯数字 → event_NNN
    if raw.isdigit():
        return f"event_{int(raw):03d}"
    # 其他带下划线的情况：取最后一节数字
    # 例：event_merged_01 → event_001, evt_ambush_03 → event_003
    parts = raw.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return f"event_{int(parts[1]):03d}"
    return raw


def _normalize_foreshadowing_id(raw: str) -> str:
    """将模型可能输出的伏笔 ID 统一为零填充的 foreshadow_NNN 格式。

    例: fsh_001 → foreshadow_001, fsh_1 → foreshadow_001,
         foreshadow_1 → foreshadow_001, foreshadowing_01 → foreshadow_001
    """
    if not raw:
        return raw
    # 已合法：foreshadow_NNN
    if raw.startswith("foreshadow_"):
        suffix = raw[11:]
        if suffix.isdigit():
            return f"foreshadow_{int(suffix):03d}"
    # fsh_001 / fsh_1 → foreshadow_001
    if raw.startswith("fsh_"):
        suffix = raw[4:]
        if suffix.isdigit():
            return f"foreshadow_{int(suffix):03d}"
    # foreshadowing_01 → foreshadow_001
    if raw.startswith("foreshadowing_"):
        suffix = raw[14:]
        if suffix.isdigit():
            return f"foreshadow_{int(suffix):03d}"
    # fs_001 → foreshadow_001
    if raw.startswith("fs_"):
        suffix = raw[3:]
        if suffix.isdigit():
            return f"foreshadow_{int(suffix):03d}"
    # 纯数字 → foreshadow_NNN
    if raw.isdigit():
        return f"foreshadow_{int(raw):03d}"
    # 其他带下划线的情况：取最后一节数字
    parts = raw.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return f"foreshadow_{int(parts[1]):03d}"
    return raw


def _normalize_char_id(raw: str) -> str:
    """将模型可能输出的各种角色 ID 统一为零填充的 char_NNN 格式。"""
    if not raw:
        return raw
    if raw.startswith("char_"):
        suffix = raw[5:]
        if suffix.isdigit():
            return f"char_{int(suffix):03d}"
        # 非纯数字后缀（如 char_baiqian_01）→ 继续尝试 rsplit
    if raw.isdigit():
        return f"char_{int(raw):03d}"
    # 其他带下划线的情况：取最后一节数字
    # 例：char_baiqian_01 → char_001
    parts = raw.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return f"char_{int(parts[1]):03d}"
    return raw


def _build_character_lookup(story_bible: dict[str, Any]) -> dict[str, str]:
    """从 story_bible 构建 name/alias → char_id 的查找表。"""
    lookup: dict[str, str] = {}
    for char in story_bible.get("characters", []):
        if not isinstance(char, dict):
            continue
        char_id = char.get("id", "")
        if not char_id:
            continue
        # 直接 name → id
        name = char.get("name", "")
        if name:
            lookup[name] = char_id
            lookup[name.lower()] = char_id
        # aliases → id
        for alias in char.get("aliases", []):
            if isinstance(alias, str) and alias:
                lookup[alias] = char_id
                lookup[alias.lower()] = char_id
    return lookup


def _build_event_lookup(events: list[dict[str, Any]]) -> dict[str, str]:
    """从事件列表构建 title/description → event_id 的查找表。"""
    lookup: dict[str, str] = {}
    for evt in events:
        if not isinstance(evt, dict):
            continue
        eid = evt.get("id", "")
        if not eid:
            continue
        # title → id
        title = evt.get("title", "")
        if title:
            lookup[title.lower()] = eid
        # 从 id 本身推导 (如 evt_arrival → 匹配 arrival)
        # 在 _resolve_event_id 中处理
    return lookup


def _resolve_event_id(raw: str, event_lookup: dict[str, str]) -> str:
    """规范化事件 ID：先尝试零填充，再尝试事件查找表。"""
    import re
    if not raw:
        return raw
    # 已经是合法 event_NNN 格式
    if re.match(r"^event_[0-9]{3}$", raw):
        return raw
    # 尝试模式规范化
    normalized = _normalize_event_id(raw)
    if re.match(r"^event_[0-9]{3}$", normalized):
        return normalized
    # 尝试从事件查找表中匹配
    if raw.lower() in event_lookup:
        return event_lookup[raw.lower()]
    # 如果 raw 是 evt_something 格式，尝试将 something 部分与事件 title 匹配
    if raw.startswith("evt_"):
        name_part = raw[4:].lower().replace("_", " ")
        if name_part in event_lookup:
            return event_lookup[name_part]
        # 模糊匹配：查找包含 name_part 的事件
        for title, eid in event_lookup.items():
            if name_part in title or title in name_part:
                return eid
    return raw


def _resolve_char_id(raw: str, lookup: dict[str, str]) -> str:
    """先尝试模式匹配规范化，失败则从角色查找表中解析。

    当 LLM 输出描述性 ID（如 char_baiqian）或直接用中文名（"白浅"）
    而不是规范 char_NNN 时，此函数尝试通过名称查表、子串匹配等方式
    将其映射回合法格式。
    """
    import re
    # 已经是合法 char_NNN 格式则直接返回
    if re.match(r"^char_[0-9]{3}$", raw):
        return raw
    # 尝试通过规范化修正（如 char_1 → char_001）
    normalized = _normalize_char_id(raw)
    if re.match(r"^char_[0-9]{3}$", normalized):
        return normalized
    # 尝试 lookup（大小写不敏感）
    if raw and raw.lower() in lookup:
        return lookup[raw.lower()]
    # raw 是 "char_something" 格式（描述性 ID），尝试从 lookup 中找 name 匹配
    if raw.startswith("char_") and len(raw) > 5:
        name_part = raw[5:]
        if name_part.lower() in lookup:
            return lookup[name_part.lower()]
    # LLM 可能直接输出中文名（如 "白浅" 而非 char_001）；尝试子串匹配
    # 对纯中文输入做模糊查找：raw 是某个 lookup key 的子串，或 vice versa
    if raw and any('一' <= c <= '鿿' for c in raw):
        for key, cid in lookup.items():
            if raw in key or key in raw:
                return cid
    return raw


def _auto_register_missing_characters(
    screenplay_json: dict[str, Any],
    char_lookup: dict[str, str],
) -> dict[str, str]:
    """扫描角色引用字段，为无法通过 lookup 解析的中文名自动注册角色。

    当 LLM（通常是 StoryOntology）在 events/scenes/story_bible 中引用了
    story_bible.characters 里不存在的角色名时（如背景角色仅作为 event participant 出现），
    此函数自动创建 char_NNN 条目，避免后续 schema 校验因非规范 ID 格式而失败。
    """
    import re
    char_pattern = re.compile(r"^char_[0-9]{3}$")

    def _has_chinese(s: str) -> bool:
        return any("一" <= c <= "鿿" for c in s)

    def _is_unresolved(raw: str) -> bool:
        """raw 包含中文且无法通过 _resolve_char_id 解析为合法 char_NNN。"""
        if not raw or char_pattern.match(raw):
            return False
        if not _has_chinese(raw):
            return False
        resolved = _resolve_char_id(raw, char_lookup)
        return not char_pattern.match(resolved)

    # 收集所有未解析的中文角色名（去重，保持首次出现的写法）
    unresolved_names: dict[str, str] = {}

    # events.participants
    for evt in screenplay_json.get("events", []):
        if isinstance(evt, dict):
            for p in evt.get("participants") or []:
                if isinstance(p, str) and _is_unresolved(p):
                    unresolved_names[p] = p

    # scenes.characters
    for scene in screenplay_json.get("scenes", []):
        if isinstance(scene, dict):
            for c in scene.get("characters") or []:
                if isinstance(c, str) and _is_unresolved(c):
                    unresolved_names[c] = c

    # core_elements.protagonists
    core = screenplay_json.get("core_elements")
    if isinstance(core, dict):
        for p in core.get("protagonists") or []:
            if isinstance(p, str) and _is_unresolved(p):
                unresolved_names[p] = p

    # story_bible → knowledge_states.character_id
    bible = screenplay_json.get("story_bible")
    if isinstance(bible, dict):
        for ks in bible.get("knowledge_states", []):
            if isinstance(ks, dict) and isinstance(ks.get("character_id"), str):
                cid = ks["character_id"]
                if _is_unresolved(cid):
                    unresolved_names[cid] = cid

        # story_bible → relationship_edges.from / .to
        for edge in bible.get("relationship_edges", []):
            if isinstance(edge, dict):
                for key in ("from", "to"):
                    val = edge.get(key)
                    if isinstance(val, str) and _is_unresolved(val):
                        unresolved_names[val] = val

        # story_bible → continuity_anchors.applies_to
        for anchor in bible.get("continuity_anchors", []):
            if isinstance(anchor, dict):
                for item in anchor.get("applies_to") or []:
                    if isinstance(item, str) and _is_unresolved(item):
                        unresolved_names[item] = item

        # dramatic_assets → conflict_pool.participants
        da = bible.get("dramatic_assets")
        if isinstance(da, dict):
            for conflict in da.get("conflict_pool", []):
                if isinstance(conflict, dict):
                    for p in conflict.get("participants") or []:
                        if isinstance(p, str) and _is_unresolved(p):
                            unresolved_names[p] = p
            # dramatic_assets → filmic_constraints.related_characters
            for fc in da.get("filmic_constraints", []):
                if isinstance(fc, dict):
                    for c in fc.get("related_characters") or []:
                        if isinstance(c, str) and _is_unresolved(c):
                            unresolved_names[c] = c

    if not unresolved_names:
        return char_lookup

    # 在 story_bible.characters 中自动注册
    bible = screenplay_json.setdefault("story_bible", {})
    characters: list[dict[str, Any]] = bible.setdefault("characters", [])

    # 找到下一个可用的 char ID
    max_id = 0
    for c in characters:
        if isinstance(c, dict):
            m = re.match(r"^char_(\d+)$", c.get("id", ""))
            if m:
                max_id = max(max_id, int(m.group(1)))

    new_lookup = dict(char_lookup)
    for name in unresolved_names.values():
        max_id += 1
        new_id = f"char_{max_id:03d}"
        characters.append({
            "id": new_id,
            "name": name,
            "aliases": [],
            "narrative_role": "minor",
            "goals": {"explicit": "", "hidden": ""},
            "voice_profile": {"rhythm": "", "diction": "", "defense_mechanism": ""},
            "source_refs": [],
            "_auto_registered": True,
        })
        new_lookup[name] = new_id
        new_lookup[name.lower()] = new_id
        logger.info("Auto-registered missing character: %s → %s", name, new_id)

    return new_lookup


def _normalize_events(events: list[dict[str, Any]], char_lookup: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """确保事件列表含 schema 要求的必填字段，并统一 ID 格式。

    如果提供了 char_lookup，会尝试将中文角色名解析为 char_NNN 格式；
    否则仅做基本的零填充规范化。
    """
    for evt in events:
        if isinstance(evt, dict):
            evt["id"] = _normalize_event_id(evt.get("id", ""))
            evt.setdefault("title", evt.get("id", "未命名事件"))
            evt.setdefault("event_type", "narrative")
            evt.setdefault("participants", [])
            evt.setdefault("summary", evt.get("description", evt.get("title", "")))
            # 确保 participants 中的角色 ID 也规范化
            participants = evt.get("participants")
            if isinstance(participants, list):
                if char_lookup:
                    evt["participants"] = [_resolve_char_id(p, char_lookup) for p in participants if isinstance(p, str)]
                else:
                    evt["participants"] = [_normalize_char_id(p) for p in participants if isinstance(p, str)]
            # 确保 event_flow 非空（schema 要求 minItems=1）
            flow = evt.get("event_flow")
            if isinstance(flow, list) and len(flow) == 0:
                evt["event_flow"] = [evt.get("title", evt.get("id", "未命名事件"))]
    return events


def _normalize_causal_graph(causal_graph: dict[str, Any]) -> dict[str, Any]:
    """确保因果图的边含 schema 要求的 relation 和 explanation。"""
    causal_graph.setdefault("edges", [])
    for edge in causal_graph.get("edges", []):
        if isinstance(edge, dict):
            edge.setdefault("relation", "leads_to")
            edge.setdefault("explanation", f"Event {edge.get('from', '?')} leads to {edge.get('to', '?')}")
    return causal_graph


def _normalize_foreshadowing(foreshadowing: list[dict[str, Any]], events: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """确保伏笔列表含 schema 要求的必填字段，并规范化 ID。"""
    event_ids = [e.get("id") for e in (events or []) if e.get("id")]
    for idx, item in enumerate(foreshadowing):
        if isinstance(item, dict):
            # 规范化已有 ID（修复 fsh_001 → foreshadow_001 等）或补默认值
            raw_id = item.get("id", "")
            if raw_id:
                item["id"] = _normalize_foreshadowing_id(raw_id)
            else:
                item.setdefault("id", f"foreshadow_{(idx + 1):03d}")
            # 规范化 setup_event_id
            setup = item.get("setup_event_id", "")
            if setup:
                item["setup_event_id"] = _normalize_event_id(setup)
            elif event_ids:
                item["setup_event_id"] = event_ids[0] if idx == 0 else event_ids[min(idx, len(event_ids) - 1)]
            else:
                item["setup_event_id"] = f"event_{(idx + 1):03d}"
            item.setdefault("status", "open")
            item.setdefault("description", item.get("description") or "待定伏笔")
            # 规范化 payoff IDs
            for key in ("payoff_event_id", "payoff_scene_id"):
                val = item.get(key, "")
                if val and key == "payoff_event_id":
                    item[key] = _normalize_event_id(val)
                elif not val:
                    item.pop(key, None)
    return foreshadowing


def _normalize_adaptation_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """规范化 adaptation_plan 中的事件 ID 引用，并补全 scene_plan 的必填字段。"""
    # retained_events
    retained = plan.get("retained_events", [])
    if isinstance(retained, list):
        plan["retained_events"] = [_normalize_event_id(e) for e in retained if isinstance(e, str)]
    # scene_plan: 补全 schema 要求的 scene_id / purpose / source_events
    scene_plan = plan.get("scene_plan", [])
    if isinstance(scene_plan, list):
        for idx, item in enumerate(scene_plan):
            if isinstance(item, dict):
                # scene_id 缺失时自动生成
                item.setdefault("scene_id", f"scene_{(idx + 1):03d}")
                # purpose 缺失时从其他字段推导
                if "purpose" not in item:
                    item["purpose"] = item.get("description") or item.get("summary") or f"Scene {idx + 1}"
                # 规范化 source_events 中的事件 ID
                src = item.get("source_events", [])
                if isinstance(src, list):
                    item["source_events"] = [_normalize_event_id(e) for e in src if isinstance(e, str)]
                elif not src:
                    item["source_events"] = []
    # merged_events 规范化
    merged = plan.get("merged_events", [])
    if isinstance(merged, list):
        for item in merged:
            if isinstance(item, dict) and isinstance(item.get("from"), list):
                item["from"] = [_normalize_event_id(e) for e in item["from"] if isinstance(e, str)]
    # deleted_or_deferred_events: 确保是对象列表
    deferred = plan.get("deleted_or_deferred_events", [])
    if not isinstance(deferred, list):
        plan["deleted_or_deferred_events"] = []
    # protected_elements: 确保是字符串列表
    protected = plan.get("protected_elements", [])
    if not isinstance(protected, list):
        plan["protected_elements"] = []
    return plan


def _normalize_source_refs_list(
    refs: list[Any],
    default_chapter_id: str = "chapter_001",
    valid_chapter_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """将 source_refs 中的字符串条目转为合法的 sourceRef 对象。

    当提供了 valid_chapter_ids 时，会将不在集合内的章节 ID（如 LLM 幻影引用的
    chapter_000）自动重映射到 default_chapter_id，避免后续校验因"引用不存在的章节"而阻断。
    """
    def _ensure_valid(cid: str) -> str:
        if valid_chapter_ids is not None and cid and cid not in valid_chapter_ids:
            logger.debug(
                "Remapping hallucinated chapter ref %s → %s", cid, default_chapter_id,
            )
            return default_chapter_id
        return cid

    result: list[dict[str, Any]] = []
    for ref in refs:
        if isinstance(ref, dict):
            cid = ref.get("chapter_id") or default_chapter_id
            ref["chapter_id"] = _ensure_valid(cid)
            ref.pop("event_ids", None)  # 移除旧格式字段
            result.append(ref)
        elif isinstance(ref, str):
            # "chapter_001:p_001" → {"chapter_id": "chapter_001", "paragraph_range": "p_001"}
            if ":" in ref:
                parts = ref.split(":", 1)
                cid = parts[0].strip() or default_chapter_id
                obj: dict[str, Any] = {"chapter_id": _ensure_valid(cid)}
                if len(parts) > 1 and parts[1].strip():
                    obj["paragraph_range"] = parts[1].strip()
                result.append(obj)
            else:
                # 纯字符串，可能为 chapter ID 或 event ID
                result.append({"chapter_id": default_chapter_id})
    return result or [{"chapter_id": default_chapter_id}]


def _normalize_all_references(
    screenplay: dict[str, Any],
    char_lookup: dict[str, str],
    event_lookup: dict[str, str],
    default_chapter_id: str = "chapter_001",
    valid_chapter_ids: set[str] | None = None,
) -> dict[str, Any]:
    """扫描 screenplay 中所有角色/事件引用/source_refs 字段，替换为规范格式。

    当提供 valid_chapter_ids 时，source_refs 中引用的幻影章节 ID（如 chapter_000）
    会被自动重映射到 default_chapter_id。"""
    # 自动推导 valid_chapter_ids（如果调用方未提供）
    if valid_chapter_ids is None:
        chapters = screenplay.get("source", {}).get("chapters", [])
        if chapters:
            valid_chapter_ids = {c["id"] for c in chapters if isinstance(c, dict) and c.get("id")}
    # events → participants, source_refs
    for evt in screenplay.get("events", []):
        if isinstance(evt, dict):
            participants = evt.get("participants")
            if isinstance(participants, list):
                evt["participants"] = [_resolve_char_id(p, char_lookup) for p in participants if isinstance(p, str)]
            srefs = evt.get("source_refs")
            if isinstance(srefs, list):
                evt["source_refs"] = _normalize_source_refs_list(srefs, default_chapter_id, valid_chapter_ids)

    # scenes → characters, dialogue, content_blocks, related_events, source_refs
    for scene in screenplay.get("scenes", []):
        if not isinstance(scene, dict):
            continue
        chars = scene.get("characters")
        if isinstance(chars, list):
            scene["characters"] = [_resolve_char_id(c, char_lookup) for c in chars if isinstance(c, str)]
        for line in scene.get("dialogue", []):
            if isinstance(line, dict) and "character_id" in line:
                line["character_id"] = _resolve_char_id(line["character_id"], char_lookup)
        for block in scene.get("content_blocks", []):
            if isinstance(block, dict) and "character_id" in block and block["character_id"]:
                block["character_id"] = _resolve_char_id(block["character_id"], char_lookup)
        related = scene.get("related_events")
        if isinstance(related, list):
            scene["related_events"] = [_resolve_event_id(e, event_lookup) for e in related if isinstance(e, str)]
        srefs = scene.get("source_refs")
        if isinstance(srefs, list):
            scene["source_refs"] = _normalize_source_refs_list(srefs, default_chapter_id, valid_chapter_ids)

        # 自动将 dialogue / content_blocks 中引用但 scene.characters 未声明的角色补全。
        # 否则 ReferenceValidator 会以 error 阻断导出。
        scene_chars = scene.setdefault("characters", [])
        scene_char_set: set[str] = set(scene_chars)
        for line in scene.get("dialogue", []):
            if isinstance(line, dict):
                cid = line.get("character_id", "")
                if cid and cid not in scene_char_set:
                    scene_chars.append(cid)
                    scene_char_set.add(cid)
        for block in scene.get("content_blocks", []):
            if isinstance(block, dict):
                cid = block.get("character_id", "")
                if cid and cid not in scene_char_set:
                    scene_chars.append(cid)
                    scene_char_set.add(cid)

    # core_elements → protagonists, plot, actions
    core = screenplay.get("core_elements")
    if isinstance(core, dict):
        protagonists = core.get("protagonists")
        if isinstance(protagonists, list):
            core["protagonists"] = [_resolve_char_id(p, char_lookup) for p in protagonists if isinstance(p, str)]
        plot = core.get("plot")
        if isinstance(plot, list):
            for beat in plot:
                if isinstance(beat, dict) and "event_id" in beat:
                    beat["event_id"] = _resolve_event_id(beat["event_id"], event_lookup)
        actions = core.get("actions")
        if isinstance(actions, list):
            for action in actions:
                if isinstance(action, dict) and "related_event_id" in action and action["related_event_id"]:
                    action["related_event_id"] = _resolve_event_id(action["related_event_id"], event_lookup)

    # story_bible → characters.source_refs, knowledge_states, relationship_edges
    bible = screenplay.get("story_bible")
    if isinstance(bible, dict):
        for char in bible.get("characters", []):
            if isinstance(char, dict):
                srefs = char.get("source_refs")
                if isinstance(srefs, list):
                    char["source_refs"] = _normalize_source_refs_list(srefs, default_chapter_id, valid_chapter_ids)
        for ks in bible.get("knowledge_states", []):
            if isinstance(ks, dict) and "character_id" in ks:
                ks["character_id"] = _resolve_char_id(ks["character_id"], char_lookup)
        for edge in bible.get("relationship_edges", []):
            if isinstance(edge, dict):
                for key in ("from", "to"):
                    if edge.get(key):
                        edge[key] = _resolve_char_id(edge[key], char_lookup)
                srefs = edge.get("source_refs")
                if isinstance(srefs, list):
                    edge["source_refs"] = _normalize_source_refs_list(srefs, default_chapter_id, valid_chapter_ids)
        for anchor in bible.get("continuity_anchors", []):
            if isinstance(anchor, dict):
                applies_to = anchor.get("applies_to")
                if isinstance(applies_to, list):
                    anchor["applies_to"] = [_resolve_char_id(c, char_lookup) for c in applies_to if isinstance(c, str)]
                srefs = anchor.get("source_refs")
                if isinstance(srefs, list):
                    anchor["source_refs"] = _normalize_source_refs_list(srefs, default_chapter_id, valid_chapter_ids)
        dramatic_assets = bible.get("dramatic_assets")
        if isinstance(dramatic_assets, dict):
            for conflict in dramatic_assets.get("conflict_pool", []):
                if isinstance(conflict, dict):
                    participants = conflict.get("participants")
                    if isinstance(participants, list):
                        conflict["participants"] = [
                            _resolve_char_id(c, char_lookup) for c in participants if isinstance(c, str)
                        ]
                    related_events = conflict.get("related_events")
                    if isinstance(related_events, list):
                        conflict["related_events"] = [
                            _resolve_event_id(e, event_lookup) for e in related_events if isinstance(e, str)
                        ]
                    srefs = conflict.get("source_refs")
                    if isinstance(srefs, list):
                        conflict["source_refs"] = _normalize_source_refs_list(srefs, default_chapter_id, valid_chapter_ids)
            for constraint in dramatic_assets.get("filmic_constraints", []):
                if isinstance(constraint, dict):
                    related_characters = constraint.get("related_characters")
                    if isinstance(related_characters, list):
                        constraint["related_characters"] = [
                            _resolve_char_id(c, char_lookup) for c in related_characters if isinstance(c, str)
                        ]
                    related_events = constraint.get("related_events")
                    if isinstance(related_events, list):
                        constraint["related_events"] = [
                            _resolve_event_id(e, event_lookup) for e in related_events if isinstance(e, str)
                        ]
                    srefs = constraint.get("source_refs")
                    if isinstance(srefs, list):
                        constraint["source_refs"] = _normalize_source_refs_list(srefs, default_chapter_id, valid_chapter_ids)

    # foreshadowing → setup_event_id, payoff_event_id
    foreshadows = screenplay.get("foreshadowing", [])
    for item in foreshadows:
        if isinstance(item, dict):
            for key in ("setup_event_id", "payoff_event_id"):
                if item.get(key):
                    item[key] = _resolve_event_id(item[key], event_lookup)

    # causal_graph edges
    cg = screenplay.get("causal_graph")
    if isinstance(cg, dict):
        for edge in cg.get("edges", []):
            if isinstance(edge, dict):
                for key in ("from", "to"):
                    if edge.get(key):
                        edge[key] = _resolve_event_id(edge[key], event_lookup)

    # adaptation_plan event references
    ap = screenplay.get("adaptation_plan")
    if isinstance(ap, dict):
        retained = ap.get("retained_events")
        if isinstance(retained, list):
            ap["retained_events"] = [_resolve_event_id(e, event_lookup) for e in retained if isinstance(e, str)]
        for item in ap.get("scene_plan", []):
            if isinstance(item, dict):
                src = item.get("source_events")
                if isinstance(src, list):
                    item["source_events"] = [_resolve_event_id(e, event_lookup) for e in src if isinstance(e, str)]

    # script_structure → story_outline[].related_events
    script = screenplay.get("script_structure")
    if isinstance(script, dict):
        for item in script.get("story_outline", []):
            if isinstance(item, dict):
                re_events = item.get("related_events")
                if isinstance(re_events, list):
                    item["related_events"] = [_resolve_event_id(e, event_lookup) for e in re_events if isinstance(e, str)]

    return screenplay

def _strip_chapter_text(data: dict[str, Any]) -> dict[str, Any]:
    """移除 chapter 对象的 text 和 paragraphs 字段，替换为 paragraph_count 引用。

    D10: 中间 artifact 不应完整复制章节原文。此函数保留章节元数据
    （id、title、order）和段落计数，但删除冗余的原文副本。
    """
    import copy
    result = copy.deepcopy(data)

    for key in ("chapters", "chapters_used"):
        chapters = result.get(key)
        if not isinstance(chapters, list):
            continue
        for chapter in chapters:
            if not isinstance(chapter, dict):
                continue
            paragraphs = chapter.pop("paragraphs", None)
            chapter.pop("text", None)
            chapter.pop("source_anchor", None)
            chapter.pop("source_file", None)
            if isinstance(paragraphs, list):
                chapter["paragraph_count"] = len(paragraphs)
            elif "paragraph_count" not in chapter:
                chapter["paragraph_count"] = 0

    return result


def _normalize_script_structure(
    script_structure: Any,
    events: list[dict[str, Any]],
    scenes: list[dict[str, Any]],
    adaptation_plan: dict[str, Any],
    project: dict[str, Any],
) -> dict[str, Any]:
    """补齐结构训练三段式，保证导出资产总能解释梗概、大纲和 scene-based 剧本。"""
    normalized = dict(script_structure) if isinstance(script_structure, dict) else {}
    scene_ids = [scene.get("id") for scene in scenes if scene.get("id")]
    event_by_id = {event.get("id"): event for event in events if event.get("id")}

    normalized.setdefault("story_synopsis", project.get("logline") or "待补故事梗概")
    outline = normalized.get("story_outline")
    if not isinstance(outline, list) or not outline:
        outline = []
        for idx, item in enumerate(adaptation_plan.get("scene_plan", []), start=1):
            if not isinstance(item, dict):
                continue
            outline.append(
                {
                    "id": f"outline_{idx:03d}",
                    "summary": item.get("purpose", "待补大纲条目"),
                    "related_events": item.get("source_events", []),
                    "target_scenes": [item.get("scene_id")] if item.get("scene_id") else [],
                }
            )
    for idx, item in enumerate(outline, start=1):
        if not isinstance(item, dict):
            continue
        related_events = item.get("related_events")
        first_event_id = related_events[0] if isinstance(related_events, list) and related_events else None
        item.setdefault("id", f"outline_{idx:03d}")
        item.setdefault("summary", event_by_id.get(first_event_id, {}).get("summary", "待补大纲条目"))
        item.setdefault("related_events", [])
        item.setdefault("target_scenes", [])
    normalized["story_outline"] = outline

    literary_screenplay = normalized.get("literary_screenplay")
    if not isinstance(literary_screenplay, dict):
        literary_screenplay = {}
    literary_screenplay["unit"] = "scene"
    literary_screenplay.setdefault(
        "format_note",
        "每场以 scene_heading 单独成行，标题下方用 content_blocks 自然段展开动作与对白。",
    )
    literary_screenplay["scene_ids"] = literary_screenplay.get("scene_ids") or scene_ids
    normalized["literary_screenplay"] = literary_screenplay
    return normalized


def _normalize_core_elements(
    core_elements: Any,
    story_bible: dict[str, Any],
    events: list[dict[str, Any]],
    scenes: list[dict[str, Any]],
    project: dict[str, Any],
) -> dict[str, Any]:
    """生成文学剧本核心元素索引；索引只引用已有实体，方便 validator 做断链检查。"""
    normalized = dict(core_elements) if isinstance(core_elements, dict) else {}
    characters = story_bible.get("characters", [])
    relationships = story_bible.get("relationship_edges", [])

    if not isinstance(normalized.get("actions"), list) or not normalized["actions"]:
        actions: list[dict[str, Any]] = []
        for idx, scene in enumerate(scenes, start=1):
            action_texts = scene.get("action", [])
            if not action_texts:
                continue
            related_events = scene.get("related_events", [])
            actions.append(
                {
                    "id": f"action_{idx:03d}",
                    "description": action_texts[0],
                    "scene_id": scene.get("id"),
                    "related_event_id": related_events[0] if related_events else None,
                }
            )
        normalized["actions"] = actions

    if not isinstance(normalized.get("plot"), list) or not normalized["plot"]:
        normalized["plot"] = [
            {"event_id": event.get("id"), "function": event.get("event_type", "narrative")}
            for event in events
            if event.get("id")
        ]

    if not isinstance(normalized.get("situations"), list) or not normalized["situations"]:
        normalized["situations"] = [
            {
                "id": f"situation_{idx:03d}",
                "scene_id": scene.get("id"),
                "description": "；".join(scene.get("dramatic_purpose", [])) or scene.get("title", "待补情境"),
            }
            for idx, scene in enumerate(scenes, start=1)
            if scene.get("id")
        ]

    normalized.setdefault("theme", project.get("logline") or "待补主题")
    protagonists = normalized.get("protagonists")
    if not isinstance(protagonists, list) or not protagonists:
        normalized["protagonists"] = [
            character.get("id")
            for character in characters
            if character.get("id") and character.get("narrative_role") in {"protagonist", "point_of_view", "detective"}
        ][:2] or [character.get("id") for character in characters[:1] if character.get("id")]

    character_relationships = normalized.get("character_relationships")
    if not isinstance(character_relationships, list):
        normalized["character_relationships"] = [
            relationship.get("id") for relationship in relationships if relationship.get("id")
        ]
    return normalized


class GenerationOrchestrator:
    def __init__(
        self,
        novel_reader: NovelReaderSkill,
        story_ontology: StoryOntologySkill,
        screenplay_writer: ScreenplayYamlWriterSkill,
        *,
        adaptation_planner: Any | None = None,  # V2.1: 已废弃，adaptation_plan 由 StoryOntology 一并产出
        artifact_service: ArtifactService | None = None,
        job_service: JobService | None = None,
        llm_trace_service: LlmTraceService | None = None,
        validation_service: ValidationService | None = None,
        yaml_service: YamlService | None = None,
    ) -> None:
        self.novel_reader = novel_reader
        self.story_ontology = story_ontology
        self.screenplay_writer = screenplay_writer
        self.artifact_service = artifact_service or ArtifactService()
        self.job_service = job_service or JobService()
        self.llm_trace_service = llm_trace_service or LlmTraceService()
        self.validation_service = validation_service or ValidationService()
        self.yaml_service = yaml_service or YamlService(validation_service=self.validation_service)

    @classmethod
    def from_provider_settings(
        cls,
        settings: AiSettings | None = None,
        *,
        fixtures: dict[str, dict[str, Any]] | None = None,
        client: Any | None = None,
    ) -> "GenerationOrchestrator":
        provider = build_ai_provider(settings, fixtures=fixtures, client=client)
        if getattr(provider, "name", None) != "deepseek":
            raise AiProviderConfigurationError(
                f"GenerationOrchestrator requires a real AI provider (got '{getattr(provider, 'name', 'unknown')}'). "
                "Set XENGINEER_AI_PROVIDER=deepseek and provide a valid DEEPSEEK_API_KEY."
            )
        return cls(
            novel_reader=NovelReaderSkill(provider),
            story_ontology=StoryOntologySkill(provider),
            screenplay_writer=ScreenplayYamlWriterSkill(provider),
        )

    def run_story_bible(
        self,
        project_id: str,
        chapters: list[dict[str, Any]],
        adaptation_config: AdaptationConfig,
        job: GenerationJob | None = None,
    ) -> GenerationJob:
        """仅运行 novel_reader → story_ontology，生成并保存 story_bible artifact。

        用于分步调试、单步重跑、前端展示 pipeline progress。
        """
        active_job = job or self.job_service.create_job(project_id)
        chapters = chapters[:4]
        try:
            project = ProjectService().get_project(project_id)
            project_payload = project.model_dump(mode="json") if project is not None else {"id": project_id}
            artifact_dir = default_data_root() / "projects" / project_id / "artifacts"
            logger.info(
                "run_story_bible project_id=%s project_title=%s chapters_count=%s provider=%s artifact_dir=%s",
                project_id,
                project_payload.get("title", ""),
                len(chapters),
                getattr(self.novel_reader.provider, "name", "unknown"),
                artifact_dir,
            )
            import time as _time

            # Phase 1: novel_reader
            active_job = self.job_service.mark_step(active_job, "running", "novel_reader")
            _t0 = _time.monotonic()
            novel_analysis = self.novel_reader.run({"project": project_payload, "chapters": chapters})
            self.llm_trace_service.record_run(
                active_job.id, "novel_reader",
                provider_name=getattr(self.novel_reader.provider, "name", "unknown"),
                model_name=getattr(self.novel_reader.provider, "model", "unknown"),
                duration_ms=(_time.monotonic() - _t0) * 1000,
            )
            # 分步模式下始终保存中间产物以便调试
            self.artifact_service.save_artifact(
                project_id, "novel_analysis",
                _strip_chapter_text(novel_analysis), active_job.id,
            )

            # Phase 2: story_ontology
            active_job = self.job_service.mark_step(active_job, "running", "story_ontology")
            _t0 = _time.monotonic()
            story_assets = self.story_ontology.run(
                {
                    "project": project_payload,
                    "adaptation_config": adaptation_config.model_dump(),
                    **novel_analysis,
                    "upstream_characters": novel_analysis.get("character_candidates", []),
                    "upstream_events": novel_analysis.get("events", []),
                }
            )
            self.llm_trace_service.record_run(
                active_job.id, "story_ontology",
                provider_name=getattr(self.story_ontology.provider, "name", "unknown"),
                model_name=getattr(self.story_ontology.provider, "model", "unknown"),
                duration_ms=(_time.monotonic() - _t0) * 1000,
            )
            self.artifact_service.save_artifact(
                project_id, "story_bible",
                _strip_chapter_text(story_assets), active_job.id,
            )

            return self.job_service.mark_step(active_job, "succeeded", "complete")
        except Exception as exc:
            return self.job_service.mark_step(active_job, "failed", active_job.current_step, str(exc))

    def run_adaptation_plan(
        self,
        project_id: str,
        chapters: list[dict[str, Any]],
        adaptation_config: AdaptationConfig,
        job: GenerationJob | None = None,
    ) -> GenerationJob:
        """运行 novel_reader → story_ontology，生成并保存 adaptation_plan artifact。
        adaptation_plan 由 StoryOntology 一并产出，不再有独立的 adaptation_planner 步骤。

        用于分步调试、单步重跑、前端展示 pipeline progress。
        """
        active_job = job or self.job_service.create_job(project_id)
        chapters = chapters[:4]
        try:
            project = ProjectService().get_project(project_id)
            project_payload = project.model_dump(mode="json") if project is not None else {"id": project_id}
            artifact_dir = default_data_root() / "projects" / project_id / "artifacts"
            logger.info(
                "run_adaptation_plan project_id=%s project_title=%s chapters_count=%s provider=%s artifact_dir=%s",
                project_id,
                project_payload.get("title", ""),
                len(chapters),
                getattr(self.novel_reader.provider, "name", "unknown"),
                artifact_dir,
            )
            import time as _time

            # Phase 1: novel_reader
            active_job = self.job_service.mark_step(active_job, "running", "novel_reader")
            _t0 = _time.monotonic()
            novel_analysis = self.novel_reader.run({"project": project_payload, "chapters": chapters})
            self.llm_trace_service.record_run(
                active_job.id, "novel_reader",
                provider_name=getattr(self.novel_reader.provider, "name", "unknown"),
                model_name=getattr(self.novel_reader.provider, "model", "unknown"),
                duration_ms=(_time.monotonic() - _t0) * 1000,
            )
            self.artifact_service.save_artifact(
                project_id, "novel_analysis",
                _strip_chapter_text(novel_analysis), active_job.id,
            )

            # Phase 2: story_ontology
            active_job = self.job_service.mark_step(active_job, "running", "story_ontology")
            _t0 = _time.monotonic()
            story_assets = self.story_ontology.run(
                {
                    "project": project_payload,
                    "adaptation_config": adaptation_config.model_dump(),
                    **novel_analysis,
                    "upstream_characters": novel_analysis.get("character_candidates", []),
                    "upstream_events": novel_analysis.get("events", []),
                }
            )
            self.llm_trace_service.record_run(
                active_job.id, "story_ontology",
                provider_name=getattr(self.story_ontology.provider, "name", "unknown"),
                model_name=getattr(self.story_ontology.provider, "model", "unknown"),
                duration_ms=(_time.monotonic() - _t0) * 1000,
            )
            self.artifact_service.save_artifact(
                project_id, "story_bible",
                _strip_chapter_text(story_assets), active_job.id,
            )

            # adaptation_plan 由 StoryOntology 在 adaptation_plan 字段中一并产出
            adaptation_plan = story_assets.get("adaptation_plan") or {}
            self.artifact_service.save_artifact(
                project_id, "adaptation_plan", adaptation_plan, active_job.id,
            )

            return self.job_service.mark_step(active_job, "succeeded", "complete")
        except Exception as exc:
            return self.job_service.mark_step(active_job, "failed", active_job.current_step, str(exc))

    def run_v1(
        self,
        project_id: str,
        chapters: list[dict[str, Any]],
        adaptation_config: AdaptationConfig,
        job: GenerationJob | None = None,
        *,
        save_intermediates: bool = False,
    ) -> GenerationJob:
        active_job = job or self.job_service.create_job(project_id)
        # 硬截章节窗口：只处理前 4 章（楔子 + 第一章~第三章）
        chapters = chapters[:4]
        try:
            project = ProjectService().get_project(project_id)
            project_payload = project.model_dump(mode="json") if project is not None else {"id": project_id}
            artifact_dir = default_data_root() / "projects" / project_id / "artifacts"
            logger.info(
                "generate project_id=%s project_title=%s chapters_count=%s provider=%s artifact_dir=%s",
                project_id,
                project_payload.get("title", ""),
                len(chapters),
                getattr(self.novel_reader.provider, "name", "unknown"),
                artifact_dir,
            )
            import time as _time

            active_job = self.job_service.mark_step(active_job, "running", "novel_reader")
            _t0 = _time.monotonic()
            novel_analysis = self.novel_reader.run({"project": project_payload, "chapters": chapters})
            self.llm_trace_service.record_run(
                active_job.id, "novel_reader",
                provider_name=getattr(self.novel_reader.provider, "name", "unknown"),
                model_name=getattr(self.novel_reader.provider, "model", "unknown"),
                duration_ms=(_time.monotonic() - _t0) * 1000,
            )
            if save_intermediates:
                self.artifact_service.save_artifact(
                    project_id, "novel_analysis",
                    _strip_chapter_text(novel_analysis), active_job.id,
                )

            active_job = self.job_service.mark_step(active_job, "running", "story_ontology")
            _t0 = _time.monotonic()
            story_assets = self.story_ontology.run(
                {
                    "project": project_payload,
                    "adaptation_config": adaptation_config.model_dump(),
                    **novel_analysis,
                    "upstream_characters": novel_analysis.get("character_candidates", []),
                    "upstream_events": novel_analysis.get("events", []),
                }
            )
            self.llm_trace_service.record_run(
                active_job.id, "story_ontology",
                provider_name=getattr(self.story_ontology.provider, "name", "unknown"),
                model_name=getattr(self.story_ontology.provider, "model", "unknown"),
                duration_ms=(_time.monotonic() - _t0) * 1000,
            )
            self.artifact_service.save_artifact(
                project_id, "story_bible",
                _strip_chapter_text(story_assets), active_job.id,
            )

            # adaptation_plan 由 StoryOntology 在 adaptation_plan 字段中一并产出，
            # 不再作为独立的 LLM 调用步骤。归一化层负责补全缺失字段。
            adaptation_plan = story_assets.get("adaptation_plan") or {}
            if save_intermediates:
                self.artifact_service.save_artifact(project_id, "adaptation_plan", adaptation_plan, active_job.id)

            active_job = self.job_service.mark_step(active_job, "running", "screenplay_writer")
            _t0 = _time.monotonic()
            screenplay_json = self.screenplay_writer.run(
                {
                    "project": project_payload,
                    **story_assets,
                    "adaptation_config": adaptation_config.model_dump(),
                    "adaptation_plan": adaptation_plan,
                    "canonical_characters": [
                        {"id": c.get("id"), "name": c.get("name")}
                        for c in story_assets.get("story_bible", {}).get("characters", [])
                        if isinstance(c, dict)
                    ],
                    "canonical_events": story_assets.get("events", []),
                }
            )
            self.llm_trace_service.record_run(
                active_job.id, "screenplay_writer",
                provider_name=getattr(self.screenplay_writer.provider, "name", "unknown"),
                model_name=getattr(self.screenplay_writer.provider, "model", "unknown"),
                duration_ms=(_time.monotonic() - _t0) * 1000,
            )
            # 注入 schema 要求的固定字段：LLM 只负责生成 scenes，
            # 其余字段由编排器保证，避免 LLM 回显残缺数据导致校验失败
            screenplay_json["schema_version"] = "1.1"
            screenplay_json["project"] = {
                "id": project_id,
                "title": project_payload.get("title") or adaptation_config.target_format.replace("_", " ").title(),
                "logline": project_payload.get("logline"),
                "target_format": adaptation_config.target_format,
            }
            screenplay_json["source"] = {
                "chapters": [
                    {"id": chapter["id"], "title": chapter["title"], "order": idx + 1}
                    for idx, chapter in enumerate(chapters)
                ]
            }
            screenplay_json["adaptation_config"] = adaptation_config.model_dump()
            # None-safety: LLM 可能输出 null 值，.get() 对存在但值为 None 的 key 不返回默认值
            _events_raw = story_assets.get("events") or []
            _foreshadowing_raw = story_assets.get("foreshadowing") or []
            _scenes_raw = screenplay_json.get("scenes") or []
            _story_bible_raw = story_assets.get("story_bible") or {}
            _causal_graph_raw = story_assets.get("causal_graph") or {}

            screenplay_json["story_bible"] = _normalize_story_bible(_story_bible_raw)
            screenplay_json["events"] = _normalize_events(_events_raw)
            screenplay_json["causal_graph"] = _normalize_causal_graph(_causal_graph_raw)
            screenplay_json["foreshadowing"] = _normalize_foreshadowing(_foreshadowing_raw, screenplay_json["events"])
            screenplay_json["adaptation_plan"] = _normalize_adaptation_plan(adaptation_plan)
            # 归一化 scenes：LLM 可能输出不完全匹配 schema 的格式
            screenplay_json["scenes"] = _normalize_scenes(_scenes_raw, chapters, screenplay_json["source"])
            screenplay_json["script_structure"] = _normalize_script_structure(
                screenplay_json.get("script_structure"),
                screenplay_json["events"],
                screenplay_json["scenes"],
                screenplay_json["adaptation_plan"],
                screenplay_json["project"],
            )
            screenplay_json["core_elements"] = _normalize_core_elements(
                screenplay_json.get("core_elements"),
                screenplay_json["story_bible"],
                screenplay_json["events"],
                screenplay_json["scenes"],
                screenplay_json["project"],
            )
            # 构建查找表，扫描全文中所有角色+事件引用字段并替换为规范 ID
            char_lookup = _build_character_lookup(screenplay_json["story_bible"])
            event_lookup = _build_event_lookup(screenplay_json["events"])
            # 自动注册 LLM 引用但 story_bible 中缺失的角色（如背景角色仅出现在 event participants）
            char_lookup = _auto_register_missing_characters(screenplay_json, char_lookup)
            if char_lookup or event_lookup:
                screenplay_json = _normalize_all_references(screenplay_json, char_lookup, event_lookup)
            screenplay_json = normalize_screenplay_for_export(screenplay_json)
            findings = self.validation_service.validate_screenplay(screenplay_json)
            audit_report = self.validation_service.audit_report_for(findings).model_dump()
            screenplay_json["audit_report"] = audit_report
            # 无条件保存 screenplay_json，即使后续校验/导出失败也能用于调试
            screenplay_artifact = self.artifact_service.save_artifact(project_id, "screenplay_json", screenplay_json, active_job.id)
            logger.info(
                "generate screenplay_json_path=%s",
                artifact_dir / f"screenplay_json_v{screenplay_artifact.version:03d}.json",
            )
            # YAML 导出：校验器已重新启用，校验不通过则阻断 pipeline
            # （如需恢复降级逻辑，取消下方注释）
            yaml_text = self.yaml_service.export_validated(screenplay_json)
            # yaml_export_errors: list[str] = []
            # try:
            #     yaml_text = self.yaml_service.export_validated(screenplay_json)
            # except ValueError as ve:
            #     yaml_export_errors.append(str(ve))
            #     logger.warning("YAML export blocked by validation, falling back to best-effort export: %s", ve)
            #     try:
            #         yaml_text = self.yaml_service.exporter.export(screenplay_json)
            #     except Exception as fe:
            #         yaml_text = f"# YAML export failed: {fe}\n# Validation: {ve}\n"
            #         logger.error("Best-effort YAML export also failed: %s", fe)
            self.artifact_service.save_artifact(project_id, "screenplay_yaml", yaml_text, active_job.id)
            self.artifact_service.save_artifact(project_id, "audit_report", audit_report, active_job.id)
            if save_intermediates:
                render_service = ScreenplayRenderService(
                    validation_service=self.validation_service,
                    artifact_service=self.artifact_service,
                )
                render_service.render_and_save(project_id, screenplay_json, active_job.id)
            return self.job_service.mark_step(active_job, "succeeded", "complete")
        except Exception as exc:
            return self.job_service.mark_step(active_job, "failed", active_job.current_step, str(exc))
