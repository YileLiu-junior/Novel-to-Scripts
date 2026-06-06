from __future__ import annotations

from dataclasses import dataclass
from os import environ
from typing import Mapping


@dataclass(frozen=True)
class AiSettings:
    provider: str = "fake"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    llm_timeout_seconds: float = 60.0


def load_ai_settings(env: Mapping[str, str] | None = None) -> AiSettings:
    values = env or environ
    timeout_value = values.get("XENGINEER_LLM_TIMEOUT_SECONDS", "60")
    try:
        timeout_seconds = float(timeout_value)
    except ValueError as exc:
        raise ValueError("XENGINEER_LLM_TIMEOUT_SECONDS must be a number") from exc

    return AiSettings(
        provider=values.get("XENGINEER_AI_PROVIDER", "fake").strip().lower(),
        deepseek_model=values.get("XENGINEER_DEEPSEEK_MODEL") or values.get("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        deepseek_api_key=values.get("DEEPSEEK_API_KEY"),
        deepseek_base_url=values.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        llm_timeout_seconds=timeout_seconds,
    )
