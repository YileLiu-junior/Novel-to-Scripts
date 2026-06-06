from __future__ import annotations

from typing import Any

from app.ai.providers.base import AiProvider, StructuredGenerationRequest


class SkillWrapper:
    skill_name: str
    prompt_name: str
    schema_name: str | None = None

    def __init__(self, provider: AiProvider) -> None:
        self.provider = provider

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        request = StructuredGenerationRequest(
            skill_name=self.skill_name,
            prompt_name=self.prompt_name,
            input_data=input_data,
            schema_name=self.schema_name,
        )
        result = self.provider.generate_structured(request)
        return result.parsed_output
