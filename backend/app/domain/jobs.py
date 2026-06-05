from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
# 生成任务与状态跟踪
# 异步任务
# GenerationJob 对应 db/tables.py 的 generation_jobs 表，状态机：queued → running → succeeded/failed。
JobStatus = Literal["queued", "running", "succeeded", "failed"]


class GenerationJob(BaseModel):
    id: str
    project_id: str
    status: JobStatus = "queued"
    current_step: str | None = None
    error: str | None = None
    artifact_ids: list[str] = Field(default_factory=list)

