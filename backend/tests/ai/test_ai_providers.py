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

    def test_story_ontology_prompt_references_upstream_characters(self) -> None:
        """D5: story_ontology prompt must instruct LLM to preserve upstream characters."""
        from pathlib import Path
        prompt = (Path(__file__).resolve().parents[2] / "app" / "ai" / "prompts" / "story_ontology.md").read_text(encoding="utf-8")
        self.assertIn("upstream_characters", prompt,
                       "story_ontology.md must reference upstream_characters for D5 contract")

    def test_screenplay_writer_prompt_references_canonical_characters(self) -> None:
        """D5: screenplay_writer prompt must instruct LLM to use canonical characters only."""
        from pathlib import Path
        prompt = (Path(__file__).resolve().parents[2] / "app" / "ai" / "prompts" / "screenplay_writer.md").read_text(encoding="utf-8")
        self.assertIn("canonical_characters", prompt,
                       "screenplay_writer.md must reference canonical_characters for D5 contract")

    def test_placeholder_scene_function_removed(self) -> None:
        """D6: _make_placeholder_scene must not exist — placeholder injection is removed."""
        from app.services import generation_orchestrator as go
        self.assertFalse(
            hasattr(go, "_make_placeholder_scene"),
            "_make_placeholder_scene should be deleted per D6"
        )

    def test_ensure_non_empty_arrays_does_not_inject_placeholders(self) -> None:
        """D6: _ensure_non_empty_arrays must not exist — silent patching is removed."""
        from app.services import generation_orchestrator as go
        self.assertFalse(
            hasattr(go, "_ensure_non_empty_arrays"),
            "_ensure_non_empty_arrays should be deleted per D6"
        )

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

    # ── JSON extraction fallback tests ──────────────────────────────────

    def test_json_extraction_from_markdown_code_block(self) -> None:
        """LLM returns JSON wrapped in ```json ... ``` — extract it."""
        provider = DeepSeekProvider(
            model="deepseek-test",
            client=_DeepSeekClient('```json\n{"scenes": [{"id": "scene_001"}]}\n```'),
        )
        result = provider.generate_structured(
            StructuredGenerationRequest(
                skill_name="screenplay_writer",
                prompt_name="screenplay_writer.md",
                input_data={},
            )
        )
        self.assertEqual(result.parsed_output, {"scenes": [{"id": "scene_001"}]})

    def test_json_extraction_via_brace_matching(self) -> None:
        """LLM returns prose with embedded JSON — extract via brace matching."""
        provider = DeepSeekProvider(
            model="deepseek-test",
            client=_DeepSeekClient('Here is the output:\n\n{"events": [{"id": "event_001"}]}\n\nHope this helps.'),
        )
        result = provider.generate_structured(
            StructuredGenerationRequest(
                skill_name="story_ontology",
                prompt_name="story_ontology.md",
                input_data={},
            )
        )
        self.assertEqual(result.parsed_output, {"events": [{"id": "event_001"}]})

    def test_json_fallback_rejects_garbled_output(self) -> None:
        """Completely garbled output should still raise AiProviderResponseError."""
        provider = DeepSeekProvider(
            model="deepseek-test",
            client=_DeepSeekClient("I'm sorry, I cannot do that."),
        )
        with self.assertRaises(AiProviderResponseError):
            provider.generate_structured(
                StructuredGenerationRequest(
                    skill_name="novel_reader",
                    prompt_name="novel_reader.md",
                    input_data={},
                )
            )

    # ── Retry behavior tests ────────────────────────────────────────────
    # DeepSeekProvider uses the OpenAI-compatible SDK under the hood.
    # The retry logic catches specific network-layer exceptions by type.
    # Tests below patch _RETRYABLE_EXCEPTIONS to include a local stub rather
    # than importing from openai directly — keeping test deps on the provider
    # module only.

    class _StubNetworkError(OSError):
        """Stub for connection/timeout/rate-limit exceptions."""

    def test_retry_on_network_error(self) -> None:
        """Network errors in _RETRYABLE_EXCEPTIONS should be retried up to 3x."""
        import app.ai.providers.deepseek_provider as dp
        client = mock.MagicMock()
        client.chat.completions.create.side_effect = self._StubNetworkError("boom")
        provider = DeepSeekProvider(model="deepseek-test", client=client)

        with mock.patch.object(dp, "_RETRYABLE_EXCEPTIONS", (self._StubNetworkError,)):
            with self.assertRaises(AiProviderResponseError) as ctx:
                provider.generate_text("test")
        self.assertIn("after 3 attempts", str(ctx.exception))
        self.assertEqual(client.chat.completions.create.call_count, 3)

    def test_no_retry_on_unknown_error(self) -> None:
        """Exceptions not in _RETRYABLE_EXCEPTIONS should fail immediately."""
        client = mock.MagicMock()
        client.chat.completions.create.side_effect = ValueError("bad request")
        provider = DeepSeekProvider(model="deepseek-test", client=client)

        with self.assertRaises(AiProviderResponseError):
            provider.generate_text("test")
        self.assertEqual(client.chat.completions.create.call_count, 1)


if __name__ == "__main__":
    unittest.main()
