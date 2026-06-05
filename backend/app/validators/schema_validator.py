from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.domain.common import ValidationFinding


class SchemaValidator:
    def __init__(self, schema_path: Path | None = None) -> None:
        self.schema_path = schema_path or Path("schemas/screenplay.schema.json")

    def validate(self, data: dict[str, Any]) -> list[ValidationFinding]:
        try:
            import jsonschema
        except ImportError:
            return [
                ValidationFinding(
                    code="schema_validator.unavailable",
                    severity="warning",
                    message="jsonschema is not installed; schema validation was skipped.",
                )
            ]

        schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        findings: list[ValidationFinding] = []
        for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
            findings.append(
                ValidationFinding(
                    code="schema.invalid",
                    severity="error",
                    message=error.message,
                    path=".".join(str(part) for part in error.path),
                )
            )
        return findings

