from __future__ import annotations

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
#   ├── story_bible: StoryBible      ← 角色/关系/知情状态
#   ├── events: [Event]              ← 叙事事件列表
#   ├── causal_graph: CausalGraph    ← 因果图
#   ├── foreshadowing: [Foreshadowing] ← 伏笔追踪
#   ├── adaptation_plan              ← 改编操作计划
#   ├── scenes: [Scene]              ← 最终剧本场景
#   │   ├── location, characters, dramatic_purpose
#   │   ├── action: [str]            ← 动作描写
#   │   └── dialogue: [DialogueLine] ← 对白（含潜台词、情感状态）
#   └── audit_report: AuditReport    ← 内嵌校验报告
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


class Scene(BaseModel):
    id: str
    title: str
    source_refs: list[SourceRef] = Field(default_factory=list)
    dramatic_purpose: list[str] = Field(default_factory=list)
    location: Location
    characters: list[str] = Field(default_factory=list)
    related_events: list[str] = Field(default_factory=list)
    foreshadowing: SceneForeshadowingRefs | None = None
    action: list[str] = Field(default_factory=list)
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
    story_bible: StoryBible
    events: list[Event] = Field(default_factory=list)
    causal_graph: CausalGraph
    foreshadowing: list[Foreshadowing] = Field(default_factory=list)
    adaptation_plan: AdaptationPlan
    scenes: list[Scene] = Field(default_factory=list)
    audit_report: AuditReport

