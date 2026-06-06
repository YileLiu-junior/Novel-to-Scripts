from __future__ import annotations

from app.domain.audit import AuditReport, AuditTarget, AuditWarning
from app.domain.common import ValidationFinding
from app.core.ids import warning_id

# 这个类负责把验证结果（ValidationFinding）转换成审计报告（AuditReport），以便前端展示给用户。
# 审计报告分为两类警告：schema_warnings（结构相关的警告）和continuity_warnings（连贯性相关的警告）。每个警告都包含一个唯一ID、严重程度、目标信息、消息内容，以及是否需要人工审核的标志。
#     结构相关的警告通常是指输入数据不符合预期的格式或规则，而连贯性相关的警告则可能涉及故事情节、角色发展等方面的问题。通过这种分类，前端可以更清晰地向用户展示不同类型的问题，并指导他们进行相应的修改。
#     连贯性相关的警告通常是指故事情节、角色发展等方面的问题，而结构相关的警告则可能涉及输入数据不符合预期的格式或规则。通过这种分类，前端可以更清晰地向用户展示不同类型的问题，并指导他们进行相应的修改。
class AuditValidator:
    def findings_to_audit_report(self, findings: list[ValidationFinding]) -> AuditReport:
        schema_warnings: list[AuditWarning] = []
        continuity_warnings: list[AuditWarning] = []
        for index, finding in enumerate(findings, start=1):
            warning = AuditWarning(
                id=warning_id(index),
                severity=finding.severity,
                target=AuditTarget(type=finding.target_type or "screenplay", id=finding.target_id or "root"),
                message=finding.message,
                needs_human_review=finding.severity != "info",
            )
            if finding.code.startswith("schema."):
                schema_warnings.append(warning)
            else:
                continuity_warnings.append(warning)
        return AuditReport(
            continuity_warnings=continuity_warnings,
            schema_warnings=schema_warnings,
        )

