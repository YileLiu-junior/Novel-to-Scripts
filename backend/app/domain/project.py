from __future__ import annotations

from pydantic import BaseModel, Field

### 项目主体：最顶层实体，一个项目 = 一部要改编的作品。

class Project(BaseModel):
    id: str
    title: str
    logline: str | None = None
    target_format: str = "web_series"
    metadata: dict[str, str] = Field(default_factory=dict)

