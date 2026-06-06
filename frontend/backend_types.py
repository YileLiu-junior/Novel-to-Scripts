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
