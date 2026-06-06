from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

# 产物元数据
# Artifact 对应 db/tables.py 的 artifacts 表，记录每一步产物的类型和版本。支持 6 种类型：
# novel_analysis → story_bible → adaptation_plan → screenplay_json → screenplay_yaml → audit_report，
# 这正好是整个工作流的流水线阶段。每个阶段的产物都可以存储在这个表里，方便追踪和回溯。data 字段可以是 JSON（dict）或者 YAML（str），根据 type 来区分。

ArtifactType = Literal[
    "novel_analysis",
    "story_bible",
    "adaptation_plan",
    "screenplay_json",
    "screenplay_yaml",
    "screenplay_rendered",
    "audit_report",
]


class Artifact(BaseModel):
    id: str
    project_id: str
    job_id: str | None = None
    type: ArtifactType
    version: int
    data: dict[str, Any] | str

