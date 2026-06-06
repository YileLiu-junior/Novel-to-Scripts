from __future__ import annotations

from typing import Any

from app.exporters.yaml_exporter import YamlExporter
from app.services.artifact_service import ArtifactService
from app.services.validation_service import ValidationService
from app.validators.screenplay_normalizer import normalize_screenplay_for_export


class YamlService:
    def __init__(
        self,
        exporter: YamlExporter | None = None,
        validation_service: ValidationService | None = None,
        artifact_service: ArtifactService | None = None,
    ) -> None:
        self.exporter = exporter or YamlExporter()
        self.validation_service = validation_service or ValidationService()
        self.artifact_service = artifact_service or ArtifactService()

    def export_validated(self, screenplay: dict[str, Any]) -> str:
        screenplay = normalize_screenplay_for_export(screenplay)
        findings = self.validation_service.validate_screenplay(screenplay)
        errors = [finding for finding in findings if finding.severity == "error"]
        if errors:
            first = errors[0]
            raise ValueError(
                "Cannot export invalid screenplay: "
                f"{first.message}; path={first.path or '<root>'}; "
                f"schema_path={first.schema_path or '<schema-root>'}"
            )
        return self.exporter.export(screenplay)

    def validate_yaml(self, yaml_text: str):
        data = self.exporter.parse(yaml_text)
        return self.validation_service.validate_screenplay(data)

    def download_latest_for_project(self, project_id: str) -> str | None:
        artifact = self.artifact_service.latest_for_project(project_id, "screenplay_yaml")
        if artifact is None or not isinstance(artifact.data, str):
            return None
        return artifact.data
