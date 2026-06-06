from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.domain.adaptation import AdaptationConfig, AdaptationPlan
from app.domain.audit import AuditReport
from app.domain.common import Location, SourceRef
from app.domain.story_bible import CausalGraph, Event, Foreshadowing, StoryBible

# 剧本（最终产物）也是顶层聚合根：一个对象把所有分析、改编、场景、校验结果全部串起来

#  Screenplay（顶层聚合根）
#   ├── project: ScreenplayProject
#   ├── source: SourceBlock          ← 源素材摘要
#   ├── adaptation_config            ← 改编配置
#   ├── script_structure             ← 故事梗概/大纲/文学剧本格式声明
#   ├── story_bible: StoryBible      ← 角色/关系/知情状态
#   ├── core_elements                ← 动作/情节/情境/主题/主人公/人物关系索引
#   ├── events: [Event]              ← 叙事事件列表
#   ├── causal_graph: CausalGraph    ← 因果图
#   ├── foreshadowing: [Foreshadowing] ← 伏笔追踪
#   ├── adaptation_plan              ← 改编操作计划
#   ├── scenes: [Scene]              ← 最终剧本场景
#   │   ├── scene_heading            ← 单独成行的文学剧本场景标题
#   │   ├── location, characters, dramatic_purpose
#   │   ├── action: [str]            ← 动作描写
#   │   ├── content_blocks           ← 标题下方自然段正文
#   │   └── dialogue: [DialogueLine] ← 对白（含潜台词、情感状态）
#   └── audit_report: AuditReport    ← 内嵌校验报告


# 这些结构把“故事梗概 -> 故事大纲 -> 文学剧本”的训练链路固化在最终资产里，
# 方便前端和评审看到生成结果不是只由 scene 文本孤立组成。
class StoryOutlineItem(BaseModel):
    id: str
    summary: str
    related_events: list[str] = Field(default_factory=list)
    target_scenes: list[str] = Field(default_factory=list)


class LiteraryScreenplayStructure(BaseModel):
    unit: Literal["scene"] = "scene"
    format_note: str
    scene_ids: list[str] = Field(default_factory=list)


class ScriptStructure(BaseModel):
    story_synopsis: str
    story_outline: list[StoryOutlineItem] = Field(default_factory=list)
    literary_screenplay: LiteraryScreenplayStructure


# CoreElements 是对文学剧本核心要素的索引层；它引用既有角色、关系、事件和场景，
# 不替代 story_bible 或 scene 正文，只让“动作/情节/情境/主题/主人公/人物关系”可检查。
class CoreAction(BaseModel):
    id: str
    description: str
    scene_id: str
    related_event_id: str | None = None


class PlotBeat(BaseModel):
    event_id: str
    function: str


class Situation(BaseModel):
    id: str
    scene_id: str
    description: str
    pressure: str | None = None


class CoreElements(BaseModel):
    actions: list[CoreAction] = Field(default_factory=list)
    plot: list[PlotBeat] = Field(default_factory=list)
    situations: list[Situation] = Field(default_factory=list)
    theme: str
    protagonists: list[str] = Field(default_factory=list)
    character_relationships: list[str] = Field(default_factory=list)


class DialogueLine(BaseModel):
    id: str
    character_id: str
    line: str
    surface_intent: str | None = None
    subtext: str | None = None
    emotional_state: str | None = None
    action_hint: str | None = None


class SceneForeshadowingRefs(BaseModel):
    setups: list[str] = Field(default_factory=list)
    payoffs: list[str] = Field(default_factory=list)


# SceneHeading 和 SceneContentBlock 显式承接文学剧本格式：
# heading 可单独成行展示，content_blocks 是标题下方按自然段排列的正文。
class SceneHeading(BaseModel):
    sequence: int
    location: str
    interior_exterior: Literal["INT", "EXT", "INT/EXT"]
    time_of_day: Literal["day", "night", "morning", "dusk"]
    text: str


class SceneContentBlock(BaseModel):
    id: str
    block_type: Literal["action", "dialogue", "transition"]
    text: str
    character_id: str | None = None
    dialogue_line_id: str | None = None


class Scene(BaseModel):
    id: str
    title: str
    scene_heading: SceneHeading
    source_refs: list[SourceRef] = Field(default_factory=list)
    dramatic_purpose: list[str] = Field(default_factory=list)
    location: Location
    characters: list[str] = Field(default_factory=list)
    related_events: list[str] = Field(default_factory=list)
    foreshadowing: SceneForeshadowingRefs | None = None
    action: list[str] = Field(default_factory=list)
    content_blocks: list[SceneContentBlock] = Field(default_factory=list)
    dialogue: list[DialogueLine] = Field(default_factory=list)


class SourceChapterSummary(BaseModel):
    id: str
    title: str
    order: int


class SourceBlock(BaseModel):
    case_id: str | None = None
    novel_source_file: str | None = None
    screenplay_reference_file: str | None = None
    chapters: list[SourceChapterSummary] = Field(default_factory=list)


class ScreenplayProject(BaseModel):
    id: str
    title: str
    logline: str | None = None
    target_format: str


class Screenplay(BaseModel):
    schema_version: str
    project: ScreenplayProject
    source: SourceBlock
    adaptation_config: AdaptationConfig
    script_structure: ScriptStructure
    story_bible: StoryBible
    core_elements: CoreElements
    events: list[Event] = Field(default_factory=list)
    causal_graph: CausalGraph
    foreshadowing: list[Foreshadowing] = Field(default_factory=list)
    adaptation_plan: AdaptationPlan
    scenes: list[Scene] = Field(default_factory=list)
    audit_report: AuditReport
