from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# 校验与审计
# AuditWarning(id, severity, target, message, needs_human_review)
# AuditReport(continuity_warnings, unresolved_foreshadowing, dialogue_warnings, schema_warnings)
# 按类别分桶的校验警告，needs_human_review 标记哪些需要人工介入。

class AuditTarget(BaseModel):
    type: str
    id: str


class AuditWarning(BaseModel):
    id: str
    severity: Literal["info", "warning", "error"]
    target: AuditTarget
    message: str
    needs_human_review: bool = False


class AuditReport(BaseModel):
    continuity_warnings: list[AuditWarning] = Field(default_factory=list)
    unresolved_foreshadowing: list[AuditWarning] = Field(default_factory=list)
    dialogue_warnings: list[AuditWarning] = Field(default_factory=list)
    schema_warnings: list[AuditWarning] = Field(default_factory=list)

