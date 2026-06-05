from __future__ import annotations

import copy
from typing import Any

from app.ai.providers.base import AiProvider, StructuredGenerationRequest, StructuredGenerationResult


class FakeProvider(AiProvider):
    name = "fake"

    def __init__(self, fixtures: dict[str, dict[str, Any]] | None = None) -> None:
        self.fixtures = fixtures or {}

    def generate_structured(self, request: StructuredGenerationRequest) -> StructuredGenerationResult:
        payload = copy.deepcopy(self.fixtures.get(request.skill_name, {}))
        return StructuredGenerationResult(
            provider=self.name,
            raw_output=None,
            parsed_output=payload,
        )

    def generate_text(self, prompt: str, temperature: float = 0.0, max_tokens: int | None = None) -> str:
        return "fake-provider-text-output"

