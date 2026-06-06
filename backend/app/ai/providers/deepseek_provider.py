from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.ai.providers.base import (
    AiProvider,
    AiProviderConfigurationError,
    AiProviderResponseError,
    StructuredGenerationRequest,
    StructuredGenerationResult,
)


class DeepSeekProvider(AiProvider):
    name = "deepseek"

    def __init__(
        self,
        *,
        model: str = "deepseek-v4-flash",
        api_key: str | None = None,
        base_url: str = "https://api.deepseek.com",
        timeout_seconds: float = 60.0,
        client: Any | None = None,
        prompts_dir: Path | None = None,
    ) -> None:
        self.model = model
        self.prompts_dir = prompts_dir or Path(__file__).resolve().parents[1] / "prompts"
        self.client = client or self._build_client(api_key, base_url, timeout_seconds)

    def generate_structured(self, request: StructuredGenerationRequest) -> StructuredGenerationResult:
        response = self._create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are one step in a structured novel-to-screenplay backend. "
                        "Return only a valid JSON object. Do not return Markdown."
                    ),
                },
                {"role": "user", "content": self._render_structured_prompt(request)},
            ],
            response_format={"type": "json_object"},
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        raw_output = self._extract_message_content(response)
        parsed_output = self._parse_json_object(raw_output)
        return StructuredGenerationResult(
            provider=self.name,
            raw_output=raw_output,
            parsed_output=parsed_output,
        )

    def generate_text(self, prompt: str, temperature: float = 0.0, max_tokens: int | None = None) -> str:
        response = self._create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return self._extract_message_content(response)

    def _build_client(self, api_key: str | None, base_url: str, timeout_seconds: float):
        if not api_key or api_key == "PASTE_YOUR_DEEPSEEK_API_KEY_HERE":
            raise AiProviderConfigurationError(
                "DEEPSEEK_API_KEY is required when XENGINEER_AI_PROVIDER=deepseek"
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise AiProviderConfigurationError(
                "The OpenAI-compatible SDK transport is required for DeepSeekProvider. "
                "Install the DeepSeek extra with `pip install -e backend[deepseek]`."
            ) from exc
        return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_seconds)

    def _create_chat_completion(self, **kwargs: Any):
        try:
            return self.client.chat.completions.create(model=self.model, stream=False, **kwargs)
        except Exception as exc:
            raise AiProviderResponseError(f"DeepSeek request failed: {exc}") from exc

    def _render_structured_prompt(self, request: StructuredGenerationRequest) -> str:
        prompt_path = self.prompts_dir / request.prompt_name
        if not prompt_path.is_file():
            raise AiProviderConfigurationError(f"Prompt file not found: {request.prompt_name}")
        prompt_text = prompt_path.read_text(encoding="utf-8")
        return "\n\n".join(
            [
                prompt_text,
                "## Runtime Input",
                json.dumps(request.input_data, ensure_ascii=False, indent=2),
                "## JSON Output Requirement",
                "Return a single valid JSON object. Example JSON output: {}",
            ]
        )

    def _extract_message_content(self, response: Any) -> str:
        choices = getattr(response, "choices", None) or []
        if not choices:
            raise AiProviderResponseError("DeepSeek response did not include choices")
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            return content
        raise AiProviderResponseError("DeepSeek response did not include message content")

    def _parse_json_object(self, raw_output: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise AiProviderResponseError("DeepSeek response was not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise AiProviderResponseError("DeepSeek structured response must be a JSON object")
        return parsed
