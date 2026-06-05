from __future__ import annotations

from typing import Any

from app.exporters.yaml_exporter import YamlExporter
from app.services.validation_service import ValidationService


class YamlService:
    def __init__(
        self,
        exporter: YamlExporter | None = None,
        validation_service: ValidationService | None = None,
    ) -> None:
        self.exporter = exporter or YamlExporter()
        self.validation_service = validation_service or ValidationService()

    def export_validated(self, screenplay: dict[str, Any]) -> str:
        findings = self.validation_service.validate_screenplay(screenplay)
        errors = [finding for finding in findings if finding.severity == "error"]
        if errors:
            raise ValueError(f"Cannot export invalid screenplay: {errors[0].message}")
        return self.exporter.export(screenplay)

    def validate_yaml(self, yaml_text: str):
        data = self.exporter.parse(yaml_text)
        return self.validation_service.validate_screenplay(data)

