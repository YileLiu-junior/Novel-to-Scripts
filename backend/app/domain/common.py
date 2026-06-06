from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

#跨域共享的小类型
#  SourceRef（引用溯源：章节+段落范围）、Location（场景地点+内/外景）、VoiceProfile（角色语态）、ValidationFinding（通用校验发现）、IdList
class SourceRef(BaseModel):
    chapter_id: str
    paragraph_range: str | None = None


class Location(BaseModel):
    name: str
    time: Literal["day", "night", "morning", "dusk"] = "day"
    interior_exterior: Literal["INT", "EXT", "INT/EXT"] = "INT"


class VoiceProfile(BaseModel):
    rhythm: str | None = None
    defense_mechanism: str | None = None


class ValidationFinding(BaseModel):
    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    target_type: str | None = None
    target_id: str | None = None
    path: str | None = None
    schema_path: str | None = None


class IdList(BaseModel):
    values: list[str] = Field(default_factory=list)
