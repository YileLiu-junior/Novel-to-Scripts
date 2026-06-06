from __future__ import annotations

from typing import Any

from app.domain.common import ValidationFinding
from app.validators.audit_validator import AuditValidator
from app.validators.reference_validator import ReferenceValidator
from app.validators.schema_validator import SchemaValidator


class ValidationService:
    def __init__(
        self,
        schema_validator: SchemaValidator | None = None,
        reference_validator: ReferenceValidator | None = None,
        audit_validator: AuditValidator | None = None,
    ) -> None:
        self.schema_validator = schema_validator or SchemaValidator()
        self.reference_validator = reference_validator or ReferenceValidator()
        self.audit_validator = audit_validator or AuditValidator()

    def validate_screenplay(self, screenplay: dict[str, Any]) -> list[ValidationFinding]:
        return [
            *self.schema_validator.validate(screenplay),
            *self.reference_validator.validate_screenplay(screenplay),
        ]

    def audit_report_for(self, findings: list[ValidationFinding]):
        return self.audit_validator.findings_to_audit_report(findings)

