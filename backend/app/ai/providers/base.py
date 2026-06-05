from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class StructuredGenerationRequest(BaseModel):
    skill_name: str
    prompt_name: str
    input_data: dict[str, Any]
    schema_name: str | None = None
    temperature: float = 0.0
    max_tokens: int | None = None


class StructuredGenerationResult(BaseModel):
    provider: str
    raw_output: str | None = None
    parsed_output: dict[str, Any] = Field(default_factory=dict)


class AiProvider(ABC):
    name: str

    @abstractmethod
    def generate_structured(self, request: StructuredGenerationRequest) -> StructuredGenerationResult:
        raise NotImplementedError

    @abstractmethod
    def generate_text(self, prompt: str, temperature: float = 0.0, max_tokens: int | None = None) -> str:
        raise NotImplementedError

