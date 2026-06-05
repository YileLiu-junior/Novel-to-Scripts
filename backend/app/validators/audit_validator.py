from __future__ import annotations

from app.domain.audit import AuditReport, AuditTarget, AuditWarning
from app.domain.common import ValidationFinding
from app.core.ids import warning_id


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

