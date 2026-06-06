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

        # --- source_refs: 字符串 → 对象 ---
        raw_refs = scene.get("source_refs", [])
        if raw_refs and isinstance(raw_refs[0], str):
            scene["source_refs"] = [
                {"chapter_id": default_chapter_id, "event_ids": raw_refs}
            ]

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
    """确保 story_bible 含 schema 要求的必填字段。"""
    story_bible.setdefault("relationship_edges", [])
    story_bible.setdefault("knowledge_states", [])
    # 补全角色必填字段
    characters = story_bible.get("characters", [])
    for char in characters:
        if isinstance(char, dict):
            char.setdefault("name", char.get("id", "unknown"))
    return story_bible


def _normalize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """确保事件列表含 schema 要求的必填字段。"""
    for evt in events:
        if isinstance(evt, dict):
            evt.setdefault("event_type", "narrative")
            evt.setdefault("participants", [])
            evt.setdefault("summary", evt.get("description", evt.get("title", "")))
    return events


def _normalize_causal_graph(causal_graph: dict[str, Any]) -> dict[str, Any]:
    """确保因果图的边含 schema 要求的 relation 和 explanation。"""
    causal_graph.setdefault("edges", [])
    for edge in causal_graph.get("edges", []):
        if isinstance(edge, dict):
            edge.setdefault("relation", "leads_to")
            edge.setdefault("explanation", f"Event {edge.get('from', '?')} leads to {edge.get('to', '?')}")
    return causal_graph


def _normalize_foreshadowing(foreshadowing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """确保伏笔列表含 schema 要求的必填字段。"""
    for item in foreshadowing:
        if isinstance(item, dict):
            item.setdefault("id", f"foreshadow_{len(foreshadowing):03d}")
            item.setdefault("setup_event_id", "")
            item.setdefault("status", "open")
            item.setdefault("description", "")
    return foreshadowing


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
            screenplay_json["foreshadowing"] = _normalize_foreshadowing(story_assets.get("foreshadowing", []))
            screenplay_json["adaptation_plan"] = adaptation_plan
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
