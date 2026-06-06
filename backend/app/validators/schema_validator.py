from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.domain.common import ValidationFinding

_APP_ROOT = Path(__file__).resolve().parents[3]  # backend/app/validators -> project root

# 这个类负责验证输入数据是否符合预定义的JSON Schema规范。它使用jsonschema库来进行验证，如果输入数据不符合规范，就会返回一个包含所有验证错误的列表，前端可以根据这些错误信息向用户展示相应的提示，帮助他们修正输入数据。
class SchemaValidator:
    def __init__(self, schema_path: Path | None = None) -> None:
        self.schema_path = schema_path or (_APP_ROOT / "schemas" / "screenplay.schema.json")

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

