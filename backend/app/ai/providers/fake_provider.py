from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from app.ai.providers.base import AiProvider, StructuredGenerationRequest, StructuredGenerationResult


class FakeProvider(AiProvider):
    name = "fake"

    def __init__(self, fixtures: dict[str, dict[str, Any]] | None = None) -> None:
        self.fixtures = fixtures or {}

    def generate_structured(self, request: StructuredGenerationRequest) -> StructuredGenerationResult:
        payload = copy.deepcopy(self.fixtures.get(request.skill_name) or self._default_payload(request))
        return StructuredGenerationResult(
            provider=self.name,
            raw_output=None,
            parsed_output=payload,
        )

    def generate_text(self, prompt: str, temperature: float = 0.0, max_tokens: int | None = None) -> str:
        return "fake-provider-text-output"

    def _default_payload(self, request: StructuredGenerationRequest) -> dict[str, Any]:
        screenplay = self._load_json_fixture("demo_screenplay.json")
        story_assets = self._load_json_fixture("demo_story_bible.json")
        if request.skill_name == "novel_reader":
            return {
                "chapters": request.input_data.get("chapters", []),
                "events": story_assets.get("events", []),
                "source_refs": ["chapter_001", "chapter_002", "chapter_003"],
            }
        if request.skill_name == "story_ontology":
            return story_assets
        if request.skill_name == "adaptation_planner":
            return screenplay["adaptation_plan"]
        if request.skill_name == "screenplay_writer":
            payload = copy.deepcopy(screenplay)
            # The fake writer keeps V1 inputs inspectable in the exported asset,
            # proving the orchestrator passes config and plan through the writer step.
            if "adaptation_config" in request.input_data:
                payload["adaptation_config"] = request.input_data["adaptation_config"]
            if "adaptation_plan" in request.input_data:
                payload["adaptation_plan"] = request.input_data["adaptation_plan"]
            return payload
        return {}

    def _load_json_fixture(self, name: str) -> dict[str, Any]:
        path = Path(__file__).resolve().parents[4] / "fixtures" / name
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
