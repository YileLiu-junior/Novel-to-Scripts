from __future__ import annotations

from app.ai.providers.base import AiProvider, StructuredGenerationRequest, StructuredGenerationResult


class OpenAIProvider(AiProvider):
    name = "openai"

    def generate_structured(self, request: StructuredGenerationRequest) -> StructuredGenerationResult:
        raise NotImplementedError("OpenAIProvider is reserved for after the fake pipeline is stable.")

    def generate_text(self, prompt: str, temperature: float = 0.0, max_tokens: int | None = None) -> str:
        raise NotImplementedError("OpenAIProvider is reserved for after the fake pipeline is stable.")

