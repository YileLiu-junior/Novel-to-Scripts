from __future__ import annotations

from typing import Any

from app.ai.providers.base import AiProvider
from app.ai.providers.deepseek_provider import DeepSeekProvider
from app.ai.providers.fake_provider import FakeProvider
from app.core.settings import AiSettings, load_ai_settings


def build_ai_provider(
    settings: AiSettings | None = None,
    *,
    fixtures: dict[str, dict[str, Any]] | None = None,
    client: Any | None = None,
) -> AiProvider:
    active_settings = settings or load_ai_settings()
    if active_settings.provider == "fake":
        return FakeProvider(fixtures=fixtures)
    if active_settings.provider == "deepseek":
        return DeepSeekProvider(
            model=active_settings.deepseek_model,
            api_key=active_settings.deepseek_api_key,
            base_url=active_settings.deepseek_base_url,
            timeout_seconds=active_settings.llm_timeout_seconds,
            client=client,
        )
    raise ValueError(f"Unsupported AI provider: {active_settings.provider}")
