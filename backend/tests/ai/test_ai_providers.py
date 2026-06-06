from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest import mock

from app.ai.providers.base import (
    AiProviderConfigurationError,
    AiProviderResponseError,
    StructuredGenerationRequest,
)
from app.ai.providers.deepseek_provider import DeepSeekProvider
from app.ai.providers.factory import build_ai_provider
from app.core.settings import AiSettings, load_ai_settings
from app.services.generation_orchestrator import GenerationOrchestrator


class _ChatCompletions:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self.output_text)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class _Chat:
    def __init__(self, output_text: str) -> None:
        self.completions = _ChatCompletions(output_text)


class _DeepSeekClient:
    def __init__(self, output_text: str) -> None:
        self.chat = _Chat(output_text)


class AiProviderTest(unittest.TestCase):
    def test_provider_factory_rejects_unknown_provider(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            build_ai_provider(AiSettings(provider="fake"))
        self.assertIn("Unsupported AI provider", str(ctx.exception))

    def test_provider_factory_rejects_empty_provider(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            build_ai_provider(AiSettings(provider=""))
        self.assertIn("Unsupported AI provider", str(ctx.exception))

    def test_provider_factory_builds_deepseek_with_injected_client(self) -> None:
        client = _DeepSeekClient("{}")
        provider = build_ai_provider(
            AiSettings(provider="deepseek", deepseek_model="deepseek-test"),
            client=client,
        )

        self.assertIsInstance(provider, DeepSeekProvider)
        self.assertIs(provider.client, client)
        self.assertEqual(provider.model, "deepseek-test")

    def test_orchestrator_factory_composes_configured_provider(self) -> None:
        client = _DeepSeekClient('{"ok": true}')
        orchestrator = GenerationOrchestrator.from_provider_settings(
            AiSettings(provider="deepseek", deepseek_model="deepseek-test"),
            client=client,
        )

        result = orchestrator.novel_reader.run({})
        self.assertEqual(result, {"ok": True})

    def test_orchestrator_rejects_non_deepseek_provider(self) -> None:
        fake = mock.Mock()
        fake.name = "fake"
        with mock.patch(
            "app.services.generation_orchestrator.build_ai_provider",
            return_value=fake,
        ):
            with self.assertRaises(AiProviderConfigurationError) as ctx:
                GenerationOrchestrator.from_provider_settings()
        self.assertIn("deepseek", str(ctx.exception).lower())

    def test_run_v1_save_intermediates_defaults_to_false(self) -> None:
        import inspect
        sig = inspect.signature(GenerationOrchestrator.run_v1)
        param = sig.parameters.get("save_intermediates")
        self.assertIsNotNone(param, "run_v1 should accept save_intermediates")
        self.assertFalse(param.default, "save_intermediates should default to False")

    def test_deepseek_provider_parses_structured_response(self) -> None:
        client = _DeepSeekClient('{"characters": [], "events": []}')
        provider = DeepSeekProvider(model="deepseek-test", client=client)

        result = provider.generate_structured(
            StructuredGenerationRequest(
                skill_name="novel_reader",
                prompt_name="novel_reader.md",
                input_data={"chapters": []},
            )
        )

        self.assertEqual(result.provider, "deepseek")
        self.assertEqual(result.parsed_output, {"characters": [], "events": []})
        call = client.chat.completions.calls[0]
        self.assertEqual(call["model"], "deepseek-test")
        self.assertEqual(call["response_format"], {"type": "json_object"})
        self.assertIn("Runtime Input", call["messages"][1]["content"])

    def test_deepseek_provider_rejects_placeholder_key_without_injected_client(self) -> None:
        with self.assertRaises(AiProviderConfigurationError):
            DeepSeekProvider(model="deepseek-test", api_key="PASTE_YOUR_DEEPSEEK_API_KEY_HERE")

    def test_deepseek_provider_rejects_non_object_json(self) -> None:
        provider = DeepSeekProvider(model="deepseek-test", client=_DeepSeekClient('["not", "an", "object"]'))

        with self.assertRaises(AiProviderResponseError):
            provider.generate_structured(
                StructuredGenerationRequest(
                    skill_name="novel_reader",
                    prompt_name="novel_reader.md",
                    input_data={},
                )
            )


if __name__ == "__main__":
    unittest.main()
