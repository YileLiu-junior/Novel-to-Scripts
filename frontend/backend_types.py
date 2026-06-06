"""
backend_types.py
前端侧的轻量类型别名与数据归一化工具。

后端 schema 是真实契约；这里不重新定义业务规则，只把可能缺失或不同
artifact 包装层的数据整理成 Streamlit 页面容易消费的结构。
"""

from __future__ import annotations

from typing import Any, TypeAlias, TypedDict


Project: TypeAlias = dict[str, Any]
Chapter: TypeAlias = dict[str, Any]
Job: TypeAlias = dict[str, Any]
Artifact: TypeAlias = dict[str, Any]
ScreenplayData: TypeAlias = dict[str, Any]
Scene: TypeAlias = dict[str, Any]
Character: TypeAlias = dict[str, Any]
DialogueLine: TypeAlias = dict[str, Any]
Event: TypeAlias = dict[str, Any]
CausalEdge: TypeAlias = dict[str, Any]
ForeshadowingItem: TypeAlias = dict[str, Any]
AdaptationPlan: TypeAlias = dict[str, Any]
AuditReport: TypeAlias = dict[str, Any]


class FrontendProjectState(TypedDict, total=False):
    """Streamlit session/local project 需要持有的后端联调状态。"""

    backend_project_id: str
    backend_chapters: list[Chapter]
    backend_job_id: str
    backend_job_status: str
    backend_current_step: str | None
    backend_error: str | None
    backend_artifacts: list[Artifact]
    screenplay_data: ScreenplayData
    screenplay_yaml: str
    rendered_markdown: str
    selected_scene: str | None
    selected_character: str | None


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def artifact_data(artifact: Artifact | None) -> Any:
    if not artifact:
        return None
    return artifact.get("data")


def screenplay_from_artifacts(project: Project) -> ScreenplayData:
    """从本地项目缓存中取出后端 screenplay_json.data。"""
    data = project.get("screenplay_data")
    return data if isinstance(data, dict) else {}


def character_name_map(screenplay: ScreenplayData) -> dict[str, str]:
    characters = screenplay.get("story_bible", {}).get("characters", [])
    return {item.get("id", ""): item.get("name", item.get("id", "")) for item in characters if item.get("id")}


def event_title_map(screenplay: ScreenplayData) -> dict[str, str]:
    return {item.get("id", ""): item.get("title", item.get("id", "")) for item in screenplay.get("events", []) if item.get("id")}


def events_by_id(screenplay: ScreenplayData) -> dict[str, Event]:
    return {item.get("id", ""): item for item in screenplay.get("events", []) if isinstance(item, dict) and item.get("id")}


def story_bible_data(screenplay: ScreenplayData, story_bible_artifact: Artifact | None = None) -> dict[str, Any]:
    """优先使用 story_bible artifact，缺失时退回 screenplay_json.story_bible。"""
    artifact_payload = artifact_data(story_bible_artifact)
    if isinstance(artifact_payload, dict) and isinstance(artifact_payload.get("story_bible"), dict):
        return artifact_payload.get("story_bible", {})
    bible = screenplay.get("story_bible")
    return bible if isinstance(bible, dict) else {}


def dramatic_assets(screenplay: ScreenplayData) -> dict[str, Any]:
    assets = screenplay.get("story_bible", {}).get("dramatic_assets", {})
    return assets if isinstance(assets, dict) else {}


def conflict_pool(screenplay: ScreenplayData) -> list[dict[str, Any]]:
    return [item for item in as_list(dramatic_assets(screenplay).get("conflict_pool")) if isinstance(item, dict)]


def continuity_anchors(screenplay: ScreenplayData) -> list[dict[str, Any]]:
    bible = screenplay.get("story_bible", {})
    return [item for item in as_list(bible.get("continuity_anchors")) if isinstance(item, dict)] if isinstance(bible, dict) else []


def filmic_constraints(screenplay: ScreenplayData) -> list[dict[str, Any]]:
    return [item for item in as_list(dramatic_assets(screenplay).get("filmic_constraints")) if isinstance(item, dict)]


def event_planner_status(event: Event, adaptation_plan: AdaptationPlan) -> str:
    """把 planner 对完整事件的消费情况转为用户可读状态。"""
    event_id = event.get("id")
    count = 0
    for item in as_list(adaptation_plan.get("scene_plan")):
        if isinstance(item, dict) and event_id in as_list(item.get("source_events")):
            count += 1
    if count == 0:
        return "未关联场景"
    if count > 1 and event.get("must_keep_together"):
        return "被拆分需说明"
    return "已保护"


def scene_evidence_trace(scene: Scene, screenplay: ScreenplayData) -> dict[str, Any]:
    """从当前 scene 派生首版 scene-to-evidence trace，不创建跨场景索引。"""
    related_ids = {item for item in as_list(scene.get("related_events")) if isinstance(item, str)}
    by_id = events_by_id(screenplay)
    related_events = [by_id[event_id] for event_id in related_ids if event_id in by_id]
    scene_chapters = {
        ref.get("chapter_id")
        for ref in as_list(scene.get("source_refs"))
        if isinstance(ref, dict) and ref.get("chapter_id")
    }
    conflicts = [
        item
        for item in conflict_pool(screenplay)
        if related_ids.intersection(set(as_list(item.get("related_events"))))
    ]
    anchors = [
        item
        for item in continuity_anchors(screenplay)
        if scene_chapters.intersection(
            {
                ref.get("chapter_id")
                for ref in as_list(item.get("source_refs"))
                if isinstance(ref, dict) and ref.get("chapter_id")
            }
        )
    ]
    return {
        "events": related_events,
        "conflicts": conflicts,
        "continuity_anchors": anchors,
        "source_refs": as_list(scene.get("source_refs")),
        "source_refs_text": ref_text(scene.get("source_refs")),
    }


def ref_text(source_refs: list[dict[str, Any]] | None) -> str:
    """把 source_refs 压缩成卡片中可读的一行来源信息。"""
    refs = []
    for ref in as_list(source_refs):
        if not isinstance(ref, dict):
            continue
        chapter_id = ref.get("chapter_id", "")
        paragraph_range = ref.get("paragraph_range", "")
        refs.append(" ".join(part for part in (chapter_id, paragraph_range) if part))
    return "；".join(refs) if refs else "暂无来源"


def warning_count(audit_report: AuditReport) -> int:
    keys = ["schema_warnings", "continuity_warnings", "dialogue_warnings", "unresolved_foreshadowing"]
    return sum(len(as_list(audit_report.get(key))) for key in keys)
