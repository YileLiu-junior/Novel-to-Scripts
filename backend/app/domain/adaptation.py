from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# adaptation.py — 改编配置与计划

#- AdaptationConfig：改编参数（忠实度 high/medium/low、对话风格等）
class AdaptationConfig(BaseModel):
    target_format: str = "web_series"
    fidelity_level: Literal["low", "medium", "high"] = "high"
    preserve_priorities: list[str] = Field(default_factory=list)
    dialogue_style: str = "restrained_with_subtext"
    adaptation_evidence_mode: Literal["enabled", "minimal"] = "enabled"


class MergedEvent(BaseModel):
    from_events: list[str] = Field(alias="from")
    into: str
    reason: str


class DeferredEvent(BaseModel):
    event_id: str
    reason: str


class ScenePlanItem(BaseModel):
    scene_id: str
    purpose: str
    source_events: list[str] = Field(default_factory=list)

# - AdaptationPlan：具体操作——保留/合并/删除/推迟哪些事件，以及场景规划
class AdaptationPlan(BaseModel):
    retained_events: list[str] = Field(default_factory=list)
    merged_events: list[MergedEvent] = Field(default_factory=list)
    deleted_or_deferred_events: list[DeferredEvent] = Field(default_factory=list)
    protected_elements: list[str] = Field(default_factory=list)
    scene_plan: list[ScenePlanItem] = Field(default_factory=list)
