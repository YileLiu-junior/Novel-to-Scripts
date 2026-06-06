from __future__ import annotations

from typing import Any

from app.ai.providers.factory import build_ai_provider
from app.ai.skills.adaptation_planner import AdaptationPlannerSkill
from app.ai.skills.novel_reader import NovelReaderSkill
from app.ai.skills.screenplay_writer import ScreenplayYamlWriterSkill
from app.ai.skills.story_ontology import StoryOntologySkill
from app.core.settings import AiSettings
from app.domain.adaptation import AdaptationConfig
from app.domain.jobs import GenerationJob
from app.services.artifact_service import ArtifactService
from app.services.job_service import JobService
from app.services.llm_trace_service import LlmTraceService
from app.services.validation_service import ValidationService
from app.services.yaml_service import YamlService


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
        return raw
    # evt_001 → event_001
    if raw.startswith("evt_"):
        suffix = raw[4:]
        if suffix.isdigit():
            return f"event_{int(suffix):03d}"
        return raw
    # 纯数字 → event_NNN
    if raw.isdigit():
        return f"event_{int(raw):03d}"
    # 其他带下划线的情况：取最后一节数字
    parts = raw.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return f"event_{int(parts[1]):03d}"
    return raw


def _normalize_char_id(raw: str) -> str:
    """将模型可能输出的各种角色 ID 统一为零填充的 char_NNN 格式。"""
    if not raw:
        return raw
    if raw.startswith("char_"):
        suffix = raw[5:]
        if suffix.isdigit():
            return f"char_{int(suffix):03d}"
        return raw
    if raw.isdigit():
        return f"char_{int(raw):03d}"
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
    """先尝试模式匹配规范化，失败则从角色查找表中解析。"""
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
    # 最后尝试：如果 raw 是 "char_something" 格式，从 lookup 中找 name 匹配
    if raw.startswith("char_") and len(raw) > 5:
        name_part = raw[5:]
        if name_part.lower() in lookup:
            return lookup[name_part.lower()]
    return raw


def _normalize_events(events: list[dict[str, Any]], char_lookup: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """确保事件列表含 schema 要求的必填字段，并统一 ID 格式。"""
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
                evt["participants"] = [_normalize_char_id(p) for p in participants if isinstance(p, str)]
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


def _normalize_source_refs_list(refs: list[Any], default_chapter_id: str = "chapter_001") -> list[dict[str, Any]]:
    """将 source_refs 中的字符串条目转为合法的 sourceRef 对象。"""
    result: list[dict[str, Any]] = []
    for ref in refs:
        if isinstance(ref, dict):
            ref.setdefault("chapter_id", ref.get("chapter_id") or default_chapter_id)
            ref.pop("event_ids", None)  # 移除旧格式字段
            result.append(ref)
        elif isinstance(ref, str):
            # "chapter_001:p_001" → {"chapter_id": "chapter_001", "paragraph_range": "p_001"}
            if ":" in ref:
                parts = ref.split(":", 1)
                obj: dict[str, Any] = {"chapter_id": parts[0].strip() or default_chapter_id}
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
) -> dict[str, Any]:
    """扫描 screenplay 中所有角色/事件引用/source_refs 字段，替换为规范格式。"""
    # events → participants, source_refs
    for evt in screenplay.get("events", []):
        if isinstance(evt, dict):
            participants = evt.get("participants")
            if isinstance(participants, list):
                evt["participants"] = [_resolve_char_id(p, char_lookup) for p in participants if isinstance(p, str)]
            srefs = evt.get("source_refs")
            if isinstance(srefs, list):
                evt["source_refs"] = _normalize_source_refs_list(srefs, default_chapter_id)

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
            scene["source_refs"] = _normalize_source_refs_list(srefs, default_chapter_id)

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
                    char["source_refs"] = _normalize_source_refs_list(srefs, default_chapter_id)
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
                    edge["source_refs"] = _normalize_source_refs_list(srefs, default_chapter_id)

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


def _ensure_non_empty_arrays(screenplay: dict[str, Any]) -> dict[str, Any]:
    """最终安全网：确保所有 schema 中要求 minItems >= 1 的数组至少有一个元素。"""
    # story_outline
    script = screenplay.get("script_structure")
    if isinstance(script, dict):
        outline = script.get("story_outline")
        if not isinstance(outline, list) or not outline:
            script["story_outline"] = [
                {"id": "outline_001", "summary": "待补大纲", "related_events": [], "target_scenes": []}
            ]
        # scene_ids
        ls_play = script.get("literary_screenplay")
        if isinstance(ls_play, dict):
            sids = ls_play.get("scene_ids")
            if not isinstance(sids, list) or not sids:
                scene_list = screenplay.get("scenes", [])
                ls_play["scene_ids"] = [s.get("id") for s in scene_list if s.get("id")] or ["scene_001"]

    # core_elements
    core = screenplay.get("core_elements")
    if isinstance(core, dict):
        if not isinstance(core.get("actions"), list) or not core["actions"]:
            core["actions"] = [{"id": "action_001", "description": "待补动作", "scene_id": "scene_001"}]
        if not isinstance(core.get("plot"), list) or not core["plot"]:
            core["plot"] = [{"event_id": "event_001", "function": "exposition"}]
        if not isinstance(core.get("situations"), list) or not core["situations"]:
            core["situations"] = [{"id": "situation_001", "scene_id": "scene_001", "description": "待补情境"}]
        if not isinstance(core.get("protagonists"), list) or not core["protagonists"]:
            bible = screenplay.get("story_bible", {})
            chars = bible.get("characters", [])
            core["protagonists"] = [c.get("id") for c in chars[:1] if c.get("id")] or ["char_001"]

    return screenplay


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
        adaptation_planner: AdaptationPlannerSkill,
        screenplay_writer: ScreenplayYamlWriterSkill,
        artifact_service: ArtifactService | None = None,
        job_service: JobService | None = None,
        llm_trace_service: LlmTraceService | None = None,
        validation_service: ValidationService | None = None,
        yaml_service: YamlService | None = None,
    ) -> None:
        self.novel_reader = novel_reader
        self.story_ontology = story_ontology
        self.adaptation_planner = adaptation_planner
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
        return cls(
            novel_reader=NovelReaderSkill(provider),
            story_ontology=StoryOntologySkill(provider),
            adaptation_planner=AdaptationPlannerSkill(provider),
            screenplay_writer=ScreenplayYamlWriterSkill(provider),
        )

    def run_v1(
        self,
        project_id: str,
        chapters: list[dict[str, Any]],
        adaptation_config: AdaptationConfig,
        job: GenerationJob | None = None,
    ) -> GenerationJob:
        active_job = job or self.job_service.create_job(project_id)
        try:
            active_job = self.job_service.mark_step(active_job, "running", "novel_reader")
            novel_analysis = self.novel_reader.run({"chapters": chapters})
            self.artifact_service.save_artifact(project_id, "novel_analysis", novel_analysis, active_job.id)
            self.llm_trace_service.record_fake_run(active_job.id, "novel_reader", novel_analysis)

            active_job = self.job_service.mark_step(active_job, "running", "story_ontology")
            story_assets = self.story_ontology.run(novel_analysis)
            self.artifact_service.save_artifact(project_id, "story_bible", story_assets, active_job.id)

            active_job = self.job_service.mark_step(active_job, "running", "adaptation_planner")
            adaptation_plan = self.adaptation_planner.run(
                {
                    **story_assets,
                    "adaptation_config": adaptation_config.model_dump(),
                }
            )
            self.artifact_service.save_artifact(project_id, "adaptation_plan", adaptation_plan, active_job.id)

            active_job = self.job_service.mark_step(active_job, "running", "screenplay_writer")
            screenplay_json = self.screenplay_writer.run(
                {
                    **story_assets,
                    "adaptation_config": adaptation_config.model_dump(),
                    "adaptation_plan": adaptation_plan,
                }
            )
            # 注入 schema 要求的固定字段：LLM 只负责生成 scenes，
            # 其余字段由编排器保证，避免 LLM 回显残缺数据导致校验失败
            screenplay_json["schema_version"] = "1.1"
            screenplay_json["project"] = {
                "id": project_id,
                "title": adaptation_config.target_format.replace("_", " ").title(),
                "target_format": adaptation_config.target_format,
            }
            screenplay_json["source"] = {
                "chapters": [
                    {"id": chapter["id"], "title": chapter["title"], "order": idx + 1}
                    for idx, chapter in enumerate(chapters)
                ]
            }
            screenplay_json["adaptation_config"] = adaptation_config.model_dump()
            screenplay_json["story_bible"] = _normalize_story_bible(story_assets.get("story_bible", {}))
            screenplay_json["events"] = _normalize_events(story_assets.get("events", []))
            screenplay_json["causal_graph"] = _normalize_causal_graph(story_assets.get("causal_graph", {}))
            screenplay_json["foreshadowing"] = _normalize_foreshadowing(
                story_assets.get("foreshadowing", []), screenplay_json["events"]
            )
            screenplay_json["adaptation_plan"] = _normalize_adaptation_plan(adaptation_plan)
            # 归一化 scenes：LLM 可能输出不完全匹配 schema 的格式
            screenplay_json["scenes"] = _normalize_scenes(
                screenplay_json.get("scenes", []), chapters, screenplay_json["source"]
            )
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
            if char_lookup or event_lookup:
                screenplay_json = _normalize_all_references(screenplay_json, char_lookup, event_lookup)
            # 最终安全网：确保 minItems ≥ 1 的数组不为空
            screenplay_json = _ensure_non_empty_arrays(screenplay_json)
            findings = self.validation_service.validate_screenplay(screenplay_json)
            audit_report = self.validation_service.audit_report_for(findings).model_dump()
            screenplay_json["audit_report"] = audit_report
            yaml_text = self.yaml_service.export_validated(screenplay_json)
            self.artifact_service.save_artifact(project_id, "screenplay_json", screenplay_json, active_job.id)
            self.artifact_service.save_artifact(project_id, "screenplay_yaml", yaml_text, active_job.id)
            self.artifact_service.save_artifact(project_id, "audit_report", audit_report, active_job.id)
            return self.job_service.mark_step(active_job, "succeeded", "complete")
        except Exception as exc:
            return self.job_service.mark_step(active_job, "failed", active_job.current_step, str(exc))
